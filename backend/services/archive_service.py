"""冷数据归档 service (Phase 1a · 优化 2)。

设计:
- question_progress 表按 user_id HASH 分区, 16 个 partition
- 当 mastered > 1Y 的行冷掉, 月度 cron 迁到 question_progress_archive
- 归档表无 FK 无分区, 单表纯 append-only
- 跑法: 启动时注册 asyncio task, 每 24h 检查一次
  (生产环境应该走系统 cron, 这里用 asyncio 简化)

迁移逻辑:
  SELECT * FROM question_progress
   WHERE status = 'mastered'
     AND updated_at < NOW() - INTERVAL 1 YEAR
   LIMIT 1000;
  → 拷贝到 archive 表 → DELETE from question_progress
  → 分批跑 (LIMIT 1000), 直到没有满足条件的行

不阻塞启动: 启动 5s 后才开始第一次检查 (避免拖慢启动)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session
from models import QuestionProgress, QuestionProgressArchive

log = logging.getLogger("codemock.archive")

ARCHIVE_AFTER_DAYS = 365  # mastered > 1Y 视为冷
BATCH_SIZE = 1000
CHECK_INTERVAL_SEC = 24 * 60 * 60  # 24h
STARTUP_DELAY_SEC = 5  # 启动后 5s 才第一次跑


async def archive_mastered_progress(db: AsyncSession) -> int:
    """把 status='mastered' AND updated_at < NOW() - 365d 的行迁到 archive 表。

    Returns: archived count.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=ARCHIVE_AFTER_DAYS)
    total = 0

    while True:
        # 1) 选一批
        stmt = (
            select(QuestionProgress)
            .where(
                QuestionProgress.status == "mastered",
                QuestionProgress.updated_at < cutoff,
            )
            .limit(BATCH_SIZE)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        if not rows:
            break

        # 2) 拷贝到 archive
        archive_rows = [
            QuestionProgressArchive(
                id=r.id,
                user_id=r.user_id,
                question_id=r.question_id,
                status=r.status,
                practice_count=r.practice_count,
                correct_count=r.correct_count,
                bookmarked=r.bookmarked,
                source=r.source,
                last_review_at=r.last_review_at,
                next_review_at=r.next_review_at,
                review_count=r.review_count,
                ease_factor=r.ease_factor,
                interval_days=r.interval_days,
                first_practiced_at=r.first_practiced_at,
                last_practiced_at=r.last_practiced_at,
                user_answer=r.user_answer,
                notes_path=r.notes_path,
                archived_at=datetime.now(timezone.utc),
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rows
        ]
        db.add_all(archive_rows)

        # 3) 从 question_progress 删 (用 id 列表, 比 ORM delete 快)
        ids = [r.id for r in rows]
        await db.execute(
            delete(QuestionProgress).where(QuestionProgress.id.in_(ids))
        )

        await db.commit()
        total += len(rows)
        log.info(f"archive batch: +{len(rows)} (total {total})")

        if len(rows) < BATCH_SIZE:
            break  # 没有更多

    return total


async def archive_loop():
    """后台 loop: 每 24h 跑一次 archive_mastered_progress。"""
    await asyncio.sleep(STARTUP_DELAY_SEC)
    log.info("archive loop started")
    while True:
        try:
            async with async_session() as db:
                count = await archive_mastered_progress(db)
                if count > 0:
                    log.info(f"archive cycle: {count} rows migrated to archive")
        except Exception as e:
            log.warning(f"archive cycle failed: {e}")
        await asyncio.sleep(CHECK_INTERVAL_SEC)


def start_archive_task() -> asyncio.Task:
    """在 FastAPI startup 阶段调用, fire-and-forget。"""
    return asyncio.create_task(archive_loop())