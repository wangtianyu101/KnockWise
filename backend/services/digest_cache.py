"""Digest Cache (T16: 2026-07-17 实施).

Redis TTL 多级缓存 + invalidation
- L1 /api/digest/today 5min (spec § 3.4 P95 < 200ms)
- L2 /api/digest/weekly 1h
- L3 /api/digest/monthly 1h
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


# TTL 配置 (spec § 3.4)
TTL_TODAY_SEC = 300  # 5 min
TTL_WEEKLY_SEC = 3600  # 1 h
TTL_MONTHLY_SEC = 3600


class DigestCache:
    """Redis TTL 多级缓存 · 写入时失效。"""

    # 缓存键命名 (与 API 路由对齐)
    KEY_TODAY = "digest:today:{user_id}:{date}"  # 5min
    KEY_WEEKLY = "digest:weekly:{user_id}:{year}:{week}"  # 1h
    KEY_MONTHLY = "digest:monthly:{user_id}:{year}:{month}"  # 1h

    # 用户级 invalidate key
    KEY_USER_PATTERN = "digest:user:{user_id}:*"  # SCAN for invalidation

    def __init__(self):
        # 部署时: from core.cache import cache; self.cache = cache
        # MVP: 抽象接口
        self.cache = None

    async def get_today(self, user_id: str, date: str) -> dict | None:
        """GET /api/digest/today · 5min TTL。"""
        if not self.cache:
            return None
        key = self.KEY_TODAY.format(user_id=user_id, date=date)
        return await self.cache.get(key)

    async def set_today(
        self, user_id: str, date: str, value: dict, ttl: int = TTL_TODAY_SEC
    ) -> None:
        """SET /api/digest/today response · 5min TTL。"""
        if not self.cache:
            return
        key = self.KEY_TODAY.format(user_id=user_id, date=date)
        await self.cache.set(key, value, ttl=ttl)

    async def invalidate_today(self, user_id: str, date: str) -> None:
        """push_daily 后失效 · 强制下次重新 fetch。"""
        if not self.cache:
            return
        key = self.KEY_TODAY.format(user_id=user_id, date=date)
        await self.cache.delete(key)

    async def invalidate_user(self, user_id: str) -> None:
        """失效该用户所有缓存 (settings change 时用)。"""
        if not self.cache:
            return
        # SCAN + DEL · MVP 简化: 列出已知 key
        pattern = self.KEY_USER_PATTERN.format(user_id=user_id)
        await self.cache.delete_pattern(pattern)


# 模块级 singleton
digest_cache = DigestCache()
