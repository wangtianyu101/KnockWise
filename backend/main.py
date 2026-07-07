import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from core.limiter import limiter

from api.auth import router as auth_router
from api.profile import router as profile_router
from api.interview import router as interview_router
from api.report import router as report_router
from api.dashboard import router as dashboard_router
from api.analytics import router as analytics_router
from api.knowledge import router as knowledge_router
from api.news import router as news_router
from api.voice_ws import router as voice_ws_router
from api.learn import router as learn_router  # Phase 1c
from api.v2_settlement import router as v2_settlement_router  # V2.3 智能沉淀层 6 端点

logger = logging.getLogger("codemock")

# V2.3 限流（L4 review 改进项 · spec §3.2 表格）
app = FastAPI(title="CodeMock", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda req, exc: JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMITED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "details": {"limit": str(exc.detail)},
            }
        },
    ),
)


# V2.3 错误响应统一（spec §3.4）：所有 4xx 走 {error: {code, message, details}}
# - RequestValidationError（Pydantic 自动校验失败）→ 422 with field/constraint/all_errors
# - HTTPException（手动 raise 的 401/403/404/422/500）→ wrap detail
# - RateLimitExceeded（slowapi）→ 429 with limit
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 统一 spec §3.4 格式（Pydantic 自动校验失败）。"""
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(p) for p in first.get("loc", [])) if first else "unknown"
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": first.get("msg", "Validation failed"),
                "details": {
                    "field": field,
                    "constraint": first.get("type", "unknown"),
                    "input": str(first.get("input", ""))[:200],  # 截断防泄漏
                    "all_errors": [
                        {
                            "field": ".".join(str(p) for p in e.get("loc", [])),
                            "constraint": e.get("type", "unknown"),
                        }
                        for e in errors
                    ],
                },
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """通用 HTTPException 包装：401/403/404/500 等都走 spec §3.4。

    V2.5 优化项提前（之前 FastAPI 默认 {detail: ...}）。
    """
    # code 映射（按 HTTP status 选最贴近的 spec code）
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    # detail 可能是 dict 或 str（兼容历史调用）
    if isinstance(exc.detail, dict):
        details = exc.detail
        message = str(details.get("message", exc.detail))
    else:
        details = {"detail": str(exc.detail)}
        message = str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(interview_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)
app.include_router(knowledge_router)
app.include_router(news_router)
app.include_router(voice_ws_router)
app.include_router(learn_router)  # Phase 1c
app.include_router(v2_settlement_router)  # V2.3 智能沉淀层 6 端点


@app.on_event("startup")
async def on_startup():
    try:
        from core.database import init_db
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database unavailable, running without persistence: {e}")

    # Phase 1a · 月度归档 cron (冷数据 mastered > 1Y → archive 表)
    try:
        from services.archive_service import start_archive_task
        # 必须持有 reference, 否则 asyncio.create_task 的 task 可能被 GC
        globals()["_archive_task"] = start_archive_task()
        logger.info("Archive cron task started")
    except Exception as e:
        logger.warning(f"Archive cron task skipped: {e}")

    # Phase 1a · Redis cache (懒初始化, 第一次调用时 connect)
    try:
        from core.cache import cache
        await cache.init()
        logger.info(f"Redis cache: {'connected' if cache.healthy else 'disabled (fallback to DB)'}")
    except Exception as e:
        logger.warning(f"Redis init skipped: {e}")

    # Pre-warm STT model so first request doesn't time out
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _warm_stt)
    except Exception as e:
        logger.warning(f"STT pre-warm skipped: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    """Phase 1a · 关 Redis 连接池 + 取消 archive task."""
    # 取消 archive task
    task = globals().get("_archive_task")
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
    # 关 Redis 连接
    try:
        from core.cache import cache
        await cache.close()
    except Exception:
        pass


def _warm_stt():
    from voice.stt import SimpleSTT
    stt = SimpleSTT()
    stt.warm_up()


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "codemock"}
