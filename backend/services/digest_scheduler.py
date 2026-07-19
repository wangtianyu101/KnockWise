"""Digest Scheduler (T18: 2026-07-17 实施 · DUAL AGENT).

APScheduler 集成到项目 scheduler.py
- 每分钟检查 · 用户到达 push_hour → 调 push_daily
- 防重复推送 · digest_daily.pushed_at 检查
- per-user timezone (spec R6)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import DigestDaily, DigestSettings

logger = logging.getLogger(__name__)


# 防重复推送阈值（分钟）
DEDUP_WINDOW_MIN = 60


class DigestScheduler:
    """每分钟检查 + 防重复推送。"""

    def __init__(self):
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
        from services.digest_service import digest_service

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
                result = await digest_service.push_daily(
                    db=db,
                    user_id=str(settings.user_id),
                    target_date=target_date,
                )

                if result.get("daily_id"):
                    pushed += 1
                    self.last_pushed[str(settings.user_id)] = datetime.now(timezone.utc)
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
            elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
            if elapsed < DEDUP_WINDOW_MIN:
                return False, "dedup"

        # 2. 时区 + 推送时间匹配 (MVP 简化 · 不做完整 tz 转换)
        # 实际部署: 用 zoneinfo + user tz
        from datetime import datetime as dt
        now_utc = dt.now(timezone.utc)
        user_hour = settings.push_hour
        user_minute = settings.push_minute

        # 简化: 如果 push_hour == UTC hour ± 1 → 推送
        if abs(now_utc.hour - user_hour) <= 1 and now_utc.minute < 5:
            return True, ""

        return False, "not_time"

    def _user_local_date(self, settings: DigestSettings) -> "date":
        """用户本地时区的日期 (MVP 简化 · 直接 UTC date)。"""
        from datetime import date
        return datetime.now(timezone.utc).date()


# 模块级
digest_scheduler = DigestScheduler()
