"""Digest Scheduler (T18: 2026-07-17 实施 · DUAL AGENT).

APScheduler 集成到项目 scheduler.py
- 每分钟检查 · 用户到达 push_hour → 调 push_daily
- 防重复推送 · digest_daily.pushed_at 检查
- per-user timezone (spec R6)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import DigestDaily, DigestSettings

logger = logging.getLogger(__name__)


# 防重复推送阈值（分钟）
DEDUP_WINDOW_MIN = 60


class DigestScheduler:
    """每分钟检查 + 防重复推送。"""

    def __init__(
        self,
        service: Any | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ):
        self.service = service
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self.last_pushed: dict[str, datetime] = {}  # user_id → last_pushed_at

    async def check_and_push(self, db: AsyncSession) -> dict[str, Any]:
        """每分钟调用 (cron) · 检查所有 enabled 用户 → 调 push_daily。

        Returns:
            {
                "checked": int,        # 检查的用户数
                "pushed": int,          # 实际推送数
                "skipped": int,         # 防重复跳过数
                "errors": int,          # 错误数
            }
        """
        if self.service is None:
            from services.digest_service import digest_service

            service = digest_service
        else:
            service = self.service

        # 1. 查所有 enabled 的 settings
        stmt = select(DigestSettings).where(
            DigestSettings.email_enabled.is_(True),
        )
        result = await db.execute(stmt)
        settings_list = list(result.scalars().all())

        checked = len(settings_list)
        pushed = 0
        skipped = 0
        errors = 0

        for settings in settings_list:
            try:
                should_push, reason = self._should_push_now(settings)
                if not should_push:
                    if reason == "dedup":
                        skipped += 1
                    continue

                # 2. 调 push_daily
                target_date = self._user_local_date(settings)
                existing_result = await db.execute(
                    select(DigestDaily.id).where(
                        DigestDaily.user_id == str(settings.user_id),
                        DigestDaily.date == target_date,
                    )
                )
                if existing_result.scalar_one_or_none() is not None:
                    skipped += 1
                    continue

                result = await service.push_daily(
                    db=db,
                    user_id=str(settings.user_id),
                    target_date=target_date,
                )

                if result.get("daily_id"):
                    pushed += 1
                    self.last_pushed[str(settings.user_id)] = self._now_provider()
                else:
                    # 没选出 item
                    pass

            except Exception as e:
                logger.exception(f"push failed for user={settings.user_id}: {e}")
                errors += 1

        return {
            "checked": checked,
            "pushed": pushed,
            "skipped": skipped,
            "errors": errors,
        }

    def _should_push_now(self, settings: DigestSettings) -> tuple[bool, str]:
        """判断当前是否应推送 + 原因。"""
        # 1. 防重复 · 上次推送 < DEDUP_WINDOW_MIN
        last = self.last_pushed.get(str(settings.user_id))
        if last:
            elapsed = (self._now_provider() - last).total_seconds() / 60
            if elapsed < DEDUP_WINDOW_MIN:
                return False, "dedup"

        # 2. Convert the injected UTC clock to the user's IANA timezone.
        try:
            user_now = self._now_provider().astimezone(ZoneInfo(settings.push_timezone))
        except (ZoneInfoNotFoundError, ValueError):
            logger.warning("invalid digest timezone: %s", settings.push_timezone)
            return False, "invalid_timezone"
        if user_now.hour == settings.push_hour and user_now.minute == settings.push_minute:
            return True, ""

        return False, "not_time"

    def _user_local_date(self, settings: DigestSettings) -> "date":
        """用户本地时区的日期 (MVP 简化 · 直接 UTC date)。"""
        try:
            timezone_info = ZoneInfo(settings.push_timezone)
        except (ZoneInfoNotFoundError, ValueError):
            timezone_info = timezone.utc
        return self._now_provider().astimezone(timezone_info).date()


# 模块级
digest_scheduler = DigestScheduler()
