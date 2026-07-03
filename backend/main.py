import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="CodeMock", version="0.1.0")

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
