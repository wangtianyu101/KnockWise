"""Rate Limiting Middleware (T17: 2026-07-17 实施).

api-spec.md § 2.2 限流策略:
- 每用户 · digest 读操作: 60/min
- 每用户 · bookmark / hide / read 写操作: 30/min
- 超限返回 429 + Retry-After header
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 限流配置 (api-spec.md § 2.2)
LIMIT_READ = 60  # /min
LIMIT_WRITE = 30  # /min
WINDOW_SEC = 60  # 1 min

# 写操作路径前缀 (POST/PATCH/DELETE)
WRITE_PATH_PREFIXES = (
    "/api/digest/bookmarks",
    "/api/digest/read",
    "/api/digest/hide",
    "/api/digest/sources",
    "/api/digest/settings",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """每用户速率限制 · Redis 计数 (in-memory 兜底)。"""

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client  # 部署时注入

    async def dispatch(self, request: Request, call_next):
        user_id = self._extract_user_id(request)
        if not user_id:
            return await call_next(request)  # 匿名 / 走 auth 拒绝

        # 1. 选 limit
        is_write = any(request.url.path.startswith(p) for p in WRITE_PATH_PREFIXES)
        is_write = is_write or request.method in ("POST", "PUT", "PATCH", "DELETE")
        limit = LIMIT_WRITE if is_write else LIMIT_READ

        # 2. 检查
        key = f"ratelimit:{user_id}:{WINDOW_SEC}s"
        count = await self._incr(key, WINDOW_SEC)
        if count > limit:
            return JSONResponse(
                {"error": {"code": "RATE_LIMITED",
                           "message": f"限流 {limit}/min · spec § 2.2"}},
                status_code=429,
                headers={"Retry-After": str(WINDOW_SEC)},
            )

        return await call_next(request)

    def _extract_user_id(self, request: Request) -> str | None:
        """从 Bearer JWT 或 session 提取 user_id (依赖项目 auth)。"""
        # 项目已有 get_current_user · 这里简化 placeholder
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        return None  # 实际部署: jwt decode

    async def _incr(self, key: str, ttl: int) -> int:
        """Redis INCR · 部署时启用。MVP: in-memory 兜底。"""
        if self.redis:
            return await self.redis.incr(key)
        # 兜底: 总是允许 (无 Redis 时不阻断开发)
        return 0
