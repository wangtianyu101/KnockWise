"""
PR 3 · V3.7 定时任务调度器（asyncio · 每 6 小时跑一次题目同步）

仿 V1 archive_service.py 模式：loop + start_task + cancel
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from core.database import async_session
from services.question_sync_service import sync_questions, build_default_sources

log = logging.getLogger("codemock.scheduler")

# 默认每 6 小时跑一次（可通过 env 覆盖）
DEFAULT_INTERVAL_SEC = 6 * 3600  # 6h
STARTUP_DELAY_SEC = 60  # 启动 1min 后首次跑（等 DB / cache 就绪）


async def question_sync_loop():
    """后台 loop：每 N 小时拉取外部题库 → 同步到 DB。

    异常处理：单次失败不中断 loop（避免一个数据源挂掉就停）。
    """
    interval = int(os.environ.get("QUESTION_SYNC_INTERVAL_SEC", DEFAULT_INTERVAL_SEC))
    log.info(f"question_sync loop started (interval={interval}s)")

    # 启动 delay
    await asyncio.sleep(STARTUP_DELAY_SEC)

    while True:
        try:
            sources = build_default_sources()
            log.info(f"question_sync cycle: {len(sources)} sources configured")

            async with async_session() as db:
                stats = await sync_questions(
                    db,
                    sources,
                    collection_id=os.environ.get("QUESTION_SYNC_COLLECTION_ID"),  # 可选：agent_foundation
                )
            log.info(f"question_sync cycle: {stats}")
        except Exception as e:
            log.warning(f"question_sync cycle failed: {e}")

        await asyncio.sleep(interval)


def start_question_sync_task() -> asyncio.Task:
    """在 FastAPI startup 阶段调用，fire-and-forget。"""
    return asyncio.create_task(question_sync_loop())


# 持全局 reference（避免 asyncio.create_task 的 task 被 GC）
_task_ref: Optional[asyncio.Task] = None


def init_question_sync_task():
    """main.py startup 调用入口。"""
    global _task_ref
    if os.environ.get("QUESTION_SYNC_DISABLED", "").lower() == "true":
        log.info("question_sync task disabled by env")
        return
    try:
        _task_ref = start_question_sync_task()
        log.info("question_sync task started")
    except Exception as e:
        log.warning(f"question_sync task skipped: {e}")


def cancel_question_sync_task():
    """main.py shutdown 调用。"""
    global _task_ref
    if _task_ref and not _task_ref.done():
        _task_ref.cancel()
        log.info("question_sync task cancelled")
