"""Email delivery boundary backed by the Resend HTTP API."""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    async def send(
        self,
        to_email: str,
        subject: str,
        html: str,
        *,
        idempotency_key: str,
    ) -> str: ...


class ResendEmailProvider:
    """Minimal Resend adapter; callers can inject a deterministic test provider."""

    API_URL = "https://api.resend.com/emails"

    async def send(
        self,
        to_email: str,
        subject: str,
        html: str,
        *,
        idempotency_key: str,
    ) -> str:
        from core.config import settings

        if not settings.resend_api_key or not settings.resend_from_email:
            raise RuntimeError("Resend is not configured")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json={
                    "from": settings.resend_from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
            )
            response.raise_for_status()
            message_id = response.json().get("id")
            if not message_id:
                raise RuntimeError("Resend response did not include a message id")
            return str(message_id)


class EmailService:
    """邮件发送服务 · Resend API + HTML 模板 + 重试。"""

    # 重试配置 (spec § 7.2)
    MAX_RETRIES = 3
    RETRY_DELAYS = [5 * 60, 15 * 60, 60 * 60]

    def __init__(self, provider: EmailProvider | None = None) -> None:
        self.provider = provider or ResendEmailProvider()
        self._sent_results: dict[str, dict[str, Any]] = {}
        self._delivery_locks: dict[str, asyncio.Lock] = {}

    async def send_daily_digest(
        self,
        user_email: str,
        digest_date: str,
        items: list[dict],
        vibe: str | None = None,
    ) -> dict[str, Any]:
        """发送每日 digest 邮件 (spec § 7.2)。

        Args:
            user_email: 收件人
            digest_date: 日期 'YYYY-MM-DD'
            items: 5 条 digest 卡片
            vibe: 顶部 vibe 标签 (如 "今日 5 条 · 正常")

        Returns:
            {
                "message_id": str,
                "sent_at": str (ISO 8601),
                "error": str | None
            }
        """
        if not user_email:
            return {"message_id": None, "sent_at": None, "error": "no user email"}

        idempotency_key = self._idempotency_key(user_email, digest_date)
        if idempotency_key in self._sent_results:
            return dict(self._sent_results[idempotency_key])

        # 1. 渲染 HTML 模板
        html = self._render_html(digest_date, items, vibe)

        # Serialize identical in-process attempts; Resend's idempotency header
        # provides the same guarantee across worker restarts.
        delivery_lock = self._delivery_locks.setdefault(idempotency_key, asyncio.Lock())
        async with delivery_lock:
            if idempotency_key in self._sent_results:
                return dict(self._sent_results[idempotency_key])
            for attempt in range(self.MAX_RETRIES + 1):
                try:
                    message_id = await self._send_via_resend(
                        user_email,
                        "KnockWise · 今日 5 条 AI 推送",
                        html,
                        idempotency_key=idempotency_key,
                    )
                    logger.info(
                        "email sent: user=%s message_id=%s", user_email, message_id
                    )
                    sent_result = {
                        "message_id": message_id,
                        "sent_at": __import__("datetime").datetime.now(
                            __import__("datetime").timezone.utc
                        ).isoformat(),
                        "error": None,
                    }
                    self._sent_results[idempotency_key] = sent_result
                    return dict(sent_result)
                except Exception as e:
                    logger.warning("email send failed (attempt %s): %s", attempt + 1, e)
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_DELAYS[attempt])

        return {
            "message_id": None,
            "sent_at": None,
            "error": "max retries exceeded",
        }

    def _render_html(
        self, digest_date: str, items: list[dict], vibe: str | None
    ) -> str:
        """渲染每日 digest HTML 邮件 (模板)。"""
        items_html = ""
        for i, item in enumerate(items, 1):
            type_color = "#3b82f6" if item.get("type") == "model" else "#8b5cf6"
            region_color = "#f59e0b" if item.get("region") == "domestic" else "#10b981"
            items_html += f"""
            <div style="border-left: 3px solid {type_color}; padding: 12px; margin-bottom: 12px;">
                <div style="font-size: 12px; color: #6b7280;">
                    <span style="background: {type_color}; color: white; padding: 2px 6px; border-radius: 3px;">{item.get('type', '')}</span>
                    <span style="background: {region_color}; color: white; padding: 2px 6px; border-radius: 3px;">{item.get('region', '')}</span>
                    · {item.get('source_name', '')} · {item.get('estimated_minutes', 3)} 分钟
                </div>
                <h3 style="margin: 8px 0;">{i}. {item.get('title', '')}</h3>
                <p style="color: #4b5563;">{item.get('summary', '')}</p>
                <a href="{item.get('source_url', '#')}" style="color: #6366f1;">查看原文 →</a>
            </div>
            """

        from core.config import settings

        digest_url = f"{settings.app_base_url.rstrip('/')}/ai/today?date={digest_date}"
        return f"""
        <!DOCTYPE html>
        <html><body style="font-family: -apple-system, sans-serif; max-width: 768px; margin: 0 auto; padding: 24px;">
            <h1>KnockWise · AI 推送 · {digest_date}</h1>
            <p style="color: #6b7280; font-size: 14px;">{vibe or ''}</p>
            <hr/>
            {items_html}
            <p><a href="{digest_url}" style="color: #6366f1; font-weight: 600;">在 KnockWise 查看今日 Digest →</a></p>
            <hr/>
            <p style="color: #9ca3af; font-size: 12px;">KnockWise · AI for AI developers</p>
        </body></html>
        """

    async def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        html: str,
        *,
        idempotency_key: str,
    ) -> str:
        """Delegate delivery to the configured provider boundary."""
        return await self.provider.send(
            to_email,
            subject,
            html,
            idempotency_key=idempotency_key,
        )

    def _idempotency_key(self, user_email: str, digest_date: str) -> str:
        digest = hashlib.sha256(
            f"digest-email:{user_email.casefold()}:{digest_date}".encode()
        ).hexdigest()
        return f"digest-{digest}"


# 模块级 singleton
email_service = EmailService()
