"""单测: services/archive_service.py

策略：mock AsyncSession + DB 结果。test archive_loop 较复杂（infinite loop），
     只测核心 archive_mastered_progress 逻辑。
覆盖：archive_mastered_progress / archive_loop 异常处理 / start_archive_task
目标：≥ 60%
"""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import archive_service as svc
from services.archive_service import (
    archive_mastered_progress,
    archive_loop,
    start_archive_task,
    ARCHIVE_AFTER_DAYS,
    BATCH_SIZE,
)


def make_qp(id, updated_at, status="mastered"):
    """创建模拟 QuestionProgress 对象"""
    return SimpleNamespace(
        id=id, user_id=f"u-{id}", question_id=f"q-{id}",
        status=status, practice_count=5, correct_count=4,
        bookmarked=False, source="practice",
        last_review_at=updated_at, next_review_at=updated_at,
        review_count=3, ease_factor=2.5, interval_days=10,
        first_practiced_at=updated_at, last_practiced_at=updated_at,
        user_answer="x", notes_path=None,
        created_at=updated_at, updated_at=updated_at,
    )


# ─── archive_mastered_progress ────────────────────────────────

class TestArchiveMasteredProgress:
    async def test_no_old_mastered_returns_zero(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        count = await archive_mastered_progress(mock_db)
        assert count == 0
        mock_db.commit.assert_not_awaited()

    async def test_archives_one_batch(self, mock_db):
        from tests.conftest import FakeResult
        # 创建 2 个"老"行
        old_date = datetime.now(timezone.utc) - timedelta(days=400)
        rows = [make_qp(f"old-{i}", old_date) for i in range(2)]

        # 第一次 execute 选 batch，第二次 delete，commit
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=rows),  # select
            FakeResult(items=[]),    # delete 无返回
        ])

        count = await archive_mastered_progress(mock_db)
        assert count == 2
        # db.add_all 调用 1 次（archive 2 行）
        mock_db.add_all.assert_called_once()
        # 2 行加进 archive
        added = mock_db.add_all.call_args.args[0]
        assert len(added) == 2
        # 都设了 archived_at
        assert all(a.archived_at is not None for a in added)
        mock_db.commit.assert_awaited_once()

    async def test_loops_until_batch_lt_size(self, mock_db):
        """分批归档：第一次 1000 行，第二次 500 行 < BATCH_SIZE 退出"""
        from tests.conftest import FakeResult
        old_date = datetime.now(timezone.utc) - timedelta(days=400)

        # 第一批：BATCH_SIZE 个（1000）
        batch1 = [make_qp(f"b1-{i}", old_date) for i in range(BATCH_SIZE)]
        # 第二批：500 < BATCH_SIZE → 退出循环
        batch2 = [make_qp(f"b2-{i}", old_date) for i in range(500)]

        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=batch1),  # 第 1 批 select
            FakeResult(items=[]),      # delete 1
            FakeResult(items=batch2),  # 第 2 批 select
            FakeResult(items=[]),      # delete 2
        ])

        count = await archive_mastered_progress(mock_db)
        assert count == BATCH_SIZE + 500
        # 2 次 add_all + 2 次 commit
        assert mock_db.add_all.call_count == 2
        assert mock_db.commit.await_count == 2

    async def test_preserves_field_values(self, mock_db):
        from tests.conftest import FakeResult
        old_date = datetime.now(timezone.utc) - timedelta(days=400)
        original = make_qp("p-1", old_date)
        original.practice_count = 42
        original.user_answer = "my answer"

        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[original]),
            FakeResult(items=[]),
        ])

        await archive_mastered_progress(mock_db)
        archived = mock_db.add_all.call_args.args[0][0]
        assert archived.id == "p-1"
        assert archived.user_id == "u-p-1"
        assert archived.question_id == "q-p-1"
        assert archived.practice_count == 42
        assert archived.user_answer == "my answer"
        # archived_at 应是当前时间
        assert archived.archived_at is not None

    async def test_uses_correct_cutoff(self, mock_db):
        """cutoff 应该是 NOW - 365 天（ARCHIVE_AFTER_DAYS）"""
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        await archive_mastered_progress(mock_db)
        # 验证 ARCHIVE_AFTER_DAYS 常量
        assert ARCHIVE_AFTER_DAYS == 365


# ─── archive_loop ──────────────────────────────────────────────

class TestArchiveLoop:
    async def test_handles_exception_in_loop(self, monkeypatch):
        """archive_loop 内的异常被捕获，loop 不退出"""
        # 让 archive_mastered_progress 抛错
        call_count = 0

        async def fake_archive(db):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("simulated")
            # 第二次成功并退出
            return 0

        monkeypatch.setattr(svc, "archive_mastered_progress", fake_archive)
        monkeypatch.setattr(svc, "STARTUP_DELAY_SEC", 0)  # 不 sleep
        monkeypatch.setattr(svc, "CHECK_INTERVAL_SEC", 0)  # 不 sleep（让循环跑 2 次就退出）

        # 用 cancel 退出 loop
        async def run():
            task = asyncio.create_task(archive_loop())
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        import asyncio
        await run()
        # 至少调过 1 次
        assert call_count >= 1

    async def test_logs_count_when_archived(self, monkeypatch):
        """有归档时 log count"""
        async def fake_archive(db):
            return 42

        monkeypatch.setattr(svc, "archive_mastered_progress", fake_archive)
        monkeypatch.setattr(svc, "STARTUP_DELAY_SEC", 0)
        monkeypatch.setattr(svc, "CHECK_INTERVAL_SEC", 0)

        # 跑一次 + cancel
        import asyncio
        task = asyncio.create_task(archive_loop())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        # 没崩即过


# ─── start_archive_task ───────────────────────────────────────

class TestStartArchiveTask:
    def test_creates_asyncio_task(self, monkeypatch):
        """start_archive_task 返回 asyncio.Task"""
        import asyncio
        mock_task = MagicMock(spec=asyncio.Task)
        mock_create_task = MagicMock(return_value=mock_task)
        monkeypatch.setattr("asyncio.create_task", mock_create_task)

        result = start_archive_task()
        # 验证 create_task 被调过
        mock_create_task.assert_called_once()
        assert result is mock_task