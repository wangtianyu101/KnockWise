"""Redis cache wrapper with graceful degradation.

设计原则 (Phase 1a):
- 所有 cache.* 调用在 Redis 不可用时 silently 返回 None / 不报错
- 主流程不能因缓存层失败而失败 → DB fallback 是 single source of truth
- 连接池懒初始化: 第一次调用时才 connect
- 用 redis.asyncio (redis-py >= 4.2) 原生 async 支持

典型用法:
    from core.cache import cache

    # 读
    val = await cache.get("review_queue:user_123")
    if val is None:
        val = await db_query_expensive()
        await cache.set("review_queue:user_123", val, ttl=300)

    # 写后失效
    await cache.delete("review_queue:user_123")

    # 批量失效 (e.g. 一组 review queue key)
    await cache.delete_pattern("review_queue:*")
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from core.config import settings

log = logging.getLogger("knockwise.cache")


class RedisCache:
    """Thin async wrapper around redis.asyncio.Redis.

    所有方法都包 try/except → RedisConnectionError / TimeoutError 时返回 None
    (或对 set/delete: silent return)。**绝不抛异常**给业务层。
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._lock = asyncio.Lock()
        self._healthy: bool = False  # 上次连接是否成功

    async def init(self) -> bool:
        """Public init: 应用启动时调用一次, 早发现连接问题, 健康日志早出现。

        失败时返回 False, 主流程继续 (cache 仍然 lazy 兜底)。
        """
        client = await self._ensure_client()
        return client is not None

    async def _ensure_client(self) -> Any:
        """Lazy init Redis client. Idempotent + concurrency-safe.

        Private: 业务层不要直接调, 用 cache.get/set/delete 或 cache.init()
        """
        if not settings.redis_enabled:
            return None
        if self._client is not None:
            return self._client
        async with self._lock:
            if self._client is not None:  # double-check after lock
                return self._client
            try:
                import redis.asyncio as aioredis

                self._client = aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    health_check_interval=30,
                )
                # 验证连接
                await self._client.ping()
                self._healthy = True
                log.info(f"Redis connected: {settings.redis_url}")
            except Exception as e:
                self._healthy = False
                log.warning(f"Redis connection failed ({type(e).__name__}): {e}. Cache disabled.")
                self._client = None
            return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Read JSON-serialised value. Returns None on miss / error."""
        client = await self._ensure_client()
        if client is None:
            return None
        try:
            raw = await client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            log.debug(f"cache.get({key}) failed: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Write JSON-serialised value. ttl seconds, default from settings."""
        client = await self._ensure_client()
        if client is None:
            return False
        try:
            ttl = ttl or settings.redis_cache_ttl_default
            await client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
            return True
        except Exception as e:
            log.debug(f"cache.set({key}) failed: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete single key."""
        client = await self._ensure_client()
        if client is None:
            return False
        try:
            await client.delete(key)
            return True
        except Exception as e:
            log.debug(f"cache.delete({key}) failed: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern. Returns count deleted."""
        client = await self._ensure_client()
        if client is None:
            return 0
        try:
            # SCAN cursor-based iteration (safe for large keyspaces)
            deleted = 0
            async for key in client.scan_iter(match=pattern, count=200):
                await client.delete(key)
                deleted += 1
            return deleted
        except Exception as e:
            log.debug(f"cache.delete_pattern({pattern}) failed: {e}")
            return 0

    async def incr(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
        """Atomic increment. Sets ttl on first increment. Returns new value or None."""
        client = await self._ensure_client()
        if client is None:
            return None
        try:
            new_val = await client.incr(key, amount)
            if ttl and new_val == amount:  # first increment → set TTL
                await client.expire(key, ttl)
            return new_val
        except Exception as e:
            log.debug(f"cache.incr({key}) failed: {e}")
            return None

    @property
    def healthy(self) -> bool:
        """Whether last connection attempt succeeded. Cheap; doesn't reconnect."""
        return self._healthy

    async def close(self) -> None:
        """Close connection pool. Call on shutdown."""
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
            self._healthy = False


# Module-level singleton
cache = RedisCache()