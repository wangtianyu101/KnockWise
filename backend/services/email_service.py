"""EmailService (T15: 2026-07-17 实施).

Resend API 邮件发送 + HTML 模板 + 重试 3 次
配套 docs/tasks/2026-07-17-new-feature-ai-push/spec.md § 7.2

注: resend SDK 未装,这里写为接口预留;实际部署时 `pip install resend`
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务 · Resend API + HTML 模板 + 重试。"""

    # 重试配置 (spec § 7.2)
    MAX_RETRIES = 3
    RETRY_DELAYS = [5, 15, 60]  # 秒 · spec § 7.2 错误码重试间隔

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

        # 1. 渲染 HTML 模板
        html = self._render_html(digest_date, items, vibe)

        # 2. 重试 3 次 (spec § 7.2 错误码重试)
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await self._send_via_resend(user_email, digest_date, html)
                logger.info(f"email sent: user={user_email} message_id={result}")
                return {
                    "message_id": result,
                    "sent_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                    "error": None,
                }
            except Exception as e:
                logger.warning(f"email send failed (attempt {attempt+1}): {e}")
                if attempt < self.MAX_RETRIES - 1:
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

        return f"""
        <!DOCTYPE html>
        <html><body style="font-family: -apple-system, sans-serif; max-width: 768px; margin: 0 auto; padding: 24px;">
            <h1>KnockWise · AI 推送 · {digest_date}</h1>
            <p style="color: #6b7280; font-size: 14px;">{vibe or ''}</p>
            <hr/>
            {items_html}
            <hr/>
            <p style="color: #9ca3af; font-size: 12px;">KnockWise · AI for AI developers</p>
        </body></html>
        """

    async def _send_via_resend(
        self, to_email: str, subject: str, html: str
    ) -> str:
        """Resend API 调用 (实际部署时启用)。"""
        # 部署时: import resend; resend.api_key = settings.resend_api_key
        # params = {"from": "...", "to": [to_email], "subject": subject, "html": html}
        # resend.Emails.send(params)
        # return params['message_id']
        #
        # MVP 简化: raise NotImplementedError · 部署时启用
        raise NotImplementedError("Resend SDK 未装 · 部署时 `pip install resend` 启用")


# 模块级 singleton
email_service = EmailService()
