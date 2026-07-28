import asyncio
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

logger = logging.getLogger("knockwise")

# V2.3 限流（L4 review 改进项 · spec §3.2 表格）
app = FastAPI(title="KnockWise", version="0.1.0")
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

from api.admin import router as admin_router
# 2026-07-22 audit 修复：5 个 digest router 之前没挂载
from api.digest.daily import router as digest_daily_router
from api.digest.bookmarks import router as digest_bookmarks_router
from api.digest.behavior import router as digest_behavior_router
from api.digest.sources import router as digest_sources_router
from api.digest.settings import router as digest_settings_router
from api.digest_metrics import router as digest_metrics_router  # T13 v1.2 4 counter 键
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(interview_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)
app.include_router(knowledge_router)
app.include_router(news_router)
app.include_router(voice_ws_router)
app.include_router(admin_router)  # V3.7 · PR 3 手动同步 API
app.include_router(learn_router)  # Phase 1c
app.include_router(v2_settlement_router)  # V2.3 智能沉淀层 6 端点
# V4 AI 推送模块 13 endpoint
app.include_router(digest_daily_router)     # /api/digest/{today,daily/{date},dailies}
app.include_router(digest_bookmarks_router)  # /api/digest/bookmarks CRUD
app.include_router(digest_behavior_router)   # /api/digest/{read,hide}
app.include_router(digest_sources_router)    # /api/digest/sources CRUD
app.include_router(digest_settings_router)   # /api/digest/settings GET/PATCH
app.include_router(digest_metrics_router)    # /api/digest/metrics（仅本地 · T13 v1.2 4 counter 键 = push_total/push_failed/fetch_failures/rsshub_routes_broken）


@app.on_event("startup")
async def on_startup():
    # T11 v1.1 · FastAPI startup 接管 knockwise.* logger（确保 TraceFilter 生效 + contextvars 隔离）
    # 注：digest_logger 已在 utils/logger.py 模块导入时初始化（line 77）
    # 这里显式调用确保 startup 阶段 logger 已配置 + 打印确认
    try:
        from utils.logger import setup_logger, digest_logger
        setup_logger("knockwise")  # 确保 stdout 结构化 + TraceFilter 注入
        logger.info("knockwise.* logger initialized with TraceFilter (contextvars isolation · T9 v1.1)")
    except Exception as e:
        logger.warning(f"knockwise.* logger setup skipped: {e}")

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

    # V3.1-PR2-T10: 预填精选题单（5 官方题单 + 关联题目）
    try:
        from core.database import SessionLocal
        from services.collection_service import seed_collections_system
        async with SessionLocal() as db:
            cnt = await seed_collections_system(db)
            logger.info(f"V3.1 seeded {cnt} system collections")
    except Exception as e:
        logger.warning(f"V3.1 collection seed skipped: {e}")

    # V2 AI 推送: seed 8 默认 digest_sources（幂等 · stub 修复）
    try:
        from core.database import async_session
        from services.seed_service import seed_default_digest_sources
        async with async_session() as _db:
            cnt = await seed_default_digest_sources(_db)
            logger.info(f"digest default sources: {cnt} newly seeded (idempotent)")
    except Exception as e:
        logger.warning(f"digest sources seed skipped: {e}")

    # V3.7 · PR 3 定时任务调度器启动（混合拉取 · 每 6h 跑一次）
    try:
        from services.scheduler import init_question_sync_task
        init_question_sync_task()
    except Exception as e:
        logger.warning(f"V3.7 question sync scheduler skipped: {e}")

    # V2 AI 推送: DigestScheduler（每分钟检查 · 到点推 push_daily · stub 修复）
    try:
        import asyncio as _asyncio
        # 2026-07-25 FIX: dev 环境禁用 scheduler（60s 跑 + LLM rate limit 触发）· env 控开关
        import os as _os
        if _os.getenv("DISABLE_DIGEST_SCHEDULER", "0") == "1":
            logger.info("digest scheduler DISABLED (DISABLE_DIGEST_SCHEDULER=1)")
        else:
            globals()["_digest_task"] = _asyncio.create_task(_digest_loop())
            logger.info("digest scheduler started (60s loop)")
    except Exception as e:
        logger.warning(f"digest scheduler skipped: {e}")


async def _digest_loop():
    """DigestScheduler 主循环 · 每 60s 调一次 check_and_push。

    与 services/archive_service.py:start_archive_task 模式一致。
    """
    import asyncio
    from core.database import async_session
    from services.digest_scheduler import digest_scheduler

    while True:
        try:
            async with async_session() as db:
                result = await digest_scheduler.check_and_push(db)
                if result["pushed"] > 0 or result["errors"] > 0:
                    logger.info(
                        f"digest scheduler: checked={result['checked']} "
                        f"pushed={result['pushed']} skipped={result['skipped']} "
                        f"errors={result['errors']}"
                    )
        except Exception as e:
            logger.exception(f"digest scheduler loop error: {e}")
        await asyncio.sleep(60)


@app.on_event("shutdown")
async def on_shutdown():
    """Phase 1a · 关 Redis 连接池 + 取消 archive task + V3.7 取消 question_sync task + digest task."""
    # V3.7 · PR 3 取消定时任务
    try:
        from services.scheduler import cancel_question_sync_task
        cancel_question_sync_task()
    except Exception as e:
        logger.warning(f"V3.7 question sync cancel skipped: {e}")

    # V2 AI 推送: 取消 digest loop task
    digest_task = globals().get("_digest_task")
    if digest_task is not None and not digest_task.done():
        digest_task.cancel()
        try:
            await digest_task
        except (asyncio.CancelledError, Exception):
            pass

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
    return {"status": "ok", "service": "knockwise"}
