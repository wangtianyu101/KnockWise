"""单测: services/learning_progress_service.py

覆盖 14 个函数 / helper，目标 ≥ 80%。
SM-2 部分 test_sm2.py 已覆盖大部分，这里补 service 集成部分。
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import learning_progress_service as svc


# ─── SM-2 补充边界（test_sm2.py 已覆盖大部分）─────────────

class TestCalcNextReviewAt:
    def test_zero_interval_means_now(self):
        from datetime import timezone as tz
        before = datetime.now(tz.utc)
        result = svc.calc_next_review_at(0)
        after = datetime.now(tz.utc)
        assert before <= result <= after + timedelta(seconds=1)

    def test_interval_adds_days(self):
        result = svc.calc_next_review_at(7)
        expected = datetime.now(timezone.utc) + timedelta(days=7)
        # 允许 1s 误差
        assert abs((result - expected).total_seconds()) < 1


# ─── get_user_progress ────────────────────────────────────────

class TestGetUserProgress:
    async def test_returns_none_when_not_found(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))
        result = await svc.get_user_progress(mock_db, "u-1", "q-1")
        assert result is None

    async def test_returns_progress(self, mock_db):
        from tests.conftest import FakeResult
        progress = SimpleNamespace(id="p-1", user_id="u-1", question_id="q-1")
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=progress))
        result = await svc.get_user_progress(mock_db, "u-1", "q-1")
        assert result is progress


# ─── list_my_progress ─────────────────────────────────────────

class TestListMyProgress:
    async def test_returns_dict_with_items_and_total(self, mock_db):
        from tests.conftest import FakeResult
        p1 = SimpleNamespace(
            question_id="q-1", status="learning",
            practice_count=5, correct_count=4,
            bookmarked=False, ease_factor=2.5, interval_days=6,
            next_review_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_practiced_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        p2 = SimpleNamespace(
            question_id="q-2", status="new",
            practice_count=0, correct_count=0,
            bookmarked=True, ease_factor=2.5, interval_days=0,
            next_review_at=None, last_practiced_at=None,
        )
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[p1, p2]),  # main query
            FakeResult(scalar=2),         # count
        ])
        result = await svc.list_my_progress(mock_db, "u-1")
        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == "q-1"  # alias question_id → id
        assert result["items"][0]["status"] == "learning"
        assert result["items"][1]["next_review_at"] is None  # None 处理
        assert result["total"] == 2

    async def test_with_status_filter(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),
            FakeResult(scalar=0),
        ])
        await svc.list_my_progress(mock_db, "u-1", status="mastered")
        assert mock_db.execute.await_count == 2

    async def test_with_bookmarked_filter(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),
            FakeResult(scalar=0),
        ])
        await svc.list_my_progress(mock_db, "u-1", bookmarked=True)
        assert mock_db.execute.await_count == 2

    async def test_pagination(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),
            FakeResult(scalar=0),
        ])
        result = await svc.list_my_progress(mock_db, "u-1", page=3, size=10)
        assert result["page"] == 3
        assert result["size"] == 10


# ─── upsert_progress ──────────────────────────────────────────

class TestUpsertProgress:
    async def test_creates_new_progress_for_first_attempt(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        # get_user_progress 返回 None → 新建
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        result = await svc.upsert_progress(
            mock_db, "u-1", "q-1", score=4, blind_spots=["x"], user_answer="my answer",
        )
        # db.add 被调 2 次：progress + log
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()
        mock_cache.delete.assert_awaited()

    async def test_updates_existing_progress(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        existing = SimpleNamespace(
            user_id="u-1", question_id="q-1",
            status="learning", practice_count=3, correct_count=2,
            bookmarked=False, ease_factor=2.5, interval_days=6,
            review_count=2, last_review_at=None,
        )
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=existing))

        result = await svc.upsert_progress(mock_db, "u-1", "q-1", score=5)
        # 答对 +1
        assert existing.correct_count == 3
        assert existing.practice_count == 4
        # status 升级（review_count=3 还是 learning，>=5 才是 mastered）
        mock_db.commit.assert_awaited()

    async def test_score_below_3_resets_review(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        existing = SimpleNamespace(
            user_id="u-1", question_id="q-1",
            status="mastered", practice_count=10, correct_count=8,
            bookmarked=False, ease_factor=2.5, interval_days=20,
            review_count=5, last_review_at=None,
        )
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=existing))

        await svc.upsert_progress(mock_db, "u-1", "q-1", score=1)
        # 答错 → correct_count 不增，status 应改回 learning
        assert existing.correct_count == 8  # 没加
        assert existing.practice_count == 11
        assert existing.status == "learning"

    async def test_invalidates_review_queue_cache(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))
        await svc.upsert_progress(mock_db, "u-1", "q-1", score=3)
        mock_cache.delete.assert_awaited_with("review_queue:u-1")

    async def test_triggers_settlement_after_practice(self, mock_db, mock_cache):
        """T6: 答题后触发 ProfileSettlementService.settle_after_practice（决策 3A）。

        验证：upsert_progress 末尾调 settlement.best-effort，**不阻塞**主业务。
        """
        from tests.conftest import FakeResult
        from unittest.mock import patch
        from uuid import UUID
        import uuid as _uuid

        user_uuid = str(_uuid.uuid4())
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        with patch(
            "services.profile_settlement_service.ProfileSettlementService"
        ) as MockSettle:
            mock_instance = MockSettle.return_value
            mock_instance.settle_after_practice = AsyncMock(return_value=None)

            result = await svc.upsert_progress(mock_db, user_uuid, "q-1", score=4)

            # 关键：settlement 被调
            mock_instance.settle_after_practice.assert_awaited_once()
            call_kwargs = mock_instance.settle_after_practice.await_args.kwargs
            assert call_kwargs["qid"] == "q-1"
            assert call_kwargs["score"] == 4
            assert call_kwargs["user_id"] == UUID(user_uuid)  # str → UUID 转换
            # 主业务不阻塞（返回 result）
            assert result is not None

    async def test_settlement_failure_does_not_block_main_business(self, mock_db, mock_cache):
        """T6: settlement 抛异常 → upsert_progress 仍正常返回（决策 7A 不阻塞）。"""
        from tests.conftest import FakeResult
        from unittest.mock import patch
        import uuid as _uuid

        user_uuid = str(_uuid.uuid4())
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        with patch(
            "services.profile_settlement_service.ProfileSettlementService"
        ) as MockSettle:
            mock_instance = MockSettle.return_value
            mock_instance.settle_after_practice = AsyncMock(
                side_effect=Exception("settlement crashed")
            )

            # 关键：upsert_progress 不抛
            result = await svc.upsert_progress(mock_db, user_uuid, "q-1", score=4)
            assert result is not None


# ─── upsert_from_interview ────────────────────────────────────

class TestUpsertFromInterview:
    async def test_correct_maps_to_score_4(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        result = await svc.upsert_from_interview(
            mock_db, "u-1", "q-1", correct=True, interview_id="iv-1"
        )
        # 通过查 source=mock_interview 验证（间接）
        assert mock_db.add.call_count >= 1  # 创建 progress
        mock_cache.delete.assert_awaited()

    async def test_incorrect_maps_to_score_2(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        existing = SimpleNamespace(
            user_id="u-1", question_id="q-1",
            status="mastered", practice_count=5, correct_count=5,
            bookmarked=False, ease_factor=2.5, interval_days=10,
            review_count=5, last_review_at=None,
        )
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=existing))

        await svc.upsert_from_interview(
            mock_db, "u-1", "q-1", correct=False, interview_id="iv-1"
        )
        # score=2 → 答错 → status 应改
        assert existing.status == "learning"  # score=2 < 3 → learning
        assert existing.correct_count == 5  # 没 +1

    async def test_returns_none_on_exception(self, mock_db):
        # 让 upsert_progress 抛错
        with patch.object(svc, "upsert_progress", side_effect=RuntimeError("boom")):
            result = await svc.upsert_from_interview(
                mock_db, "u-1", "q-1", correct=True, interview_id="iv-1"
            )
        assert result is None
        mock_db.rollback.assert_awaited()


# ─── get_review_queue ─────────────────────────────────────────

class TestGetReviewQueue:
    async def test_returns_cached_when_hit(self, mock_db, mock_cache):
        cached = [{"question_id": "q-1"}, {"question_id": "q-2"}]
        mock_cache.get = AsyncMock(return_value=cached)
        result = await svc.get_review_queue(mock_db, "u-1")
        assert result == cached
        mock_db.execute.assert_not_called()

    async def test_db_query_when_cache_miss(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        p1 = SimpleNamespace(
            question_id="q-1", status="learning", ease_factor=2.5,
            interval_days=6, next_review_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        mock_cache.get = AsyncMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[p1]))

        result = await svc.get_review_queue(mock_db, "u-1")
        assert len(result) == 1
        assert result[0]["question_id"] == "q-1"
        # cache 被写入
        mock_cache.set.assert_awaited()

    async def test_respects_limit(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        mock_cache.get = AsyncMock(return_value=None)
        # 60 个 item 但 limit=10
        items = [
            SimpleNamespace(
                question_id=f"q-{i}", status="learning", ease_factor=2.5,
                interval_days=1, next_review_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ) for i in range(60)
        ]
        mock_db.execute = AsyncMock(return_value=FakeResult(items=items))

        result = await svc.get_review_queue(mock_db, "u-1", limit=10)
        assert len(result) == 10

    async def test_handles_none_next_review_at(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        p1 = SimpleNamespace(
            question_id="q-1", status="new", ease_factor=2.5,
            interval_days=0, next_review_at=None,
        )
        mock_cache.get = AsyncMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[p1]))

        result = await svc.get_review_queue(mock_db, "u-1")
        assert result[0]["next_review_at"] is None


# ─── get_recommend ────────────────────────────────────────────

class TestGetRecommend:
    async def test_no_profile_returns_empty(self, mock_db):
        from tests.conftest import FakeResult
        # 1) Profile query → None
        # 2) new 题 query → 空
        # 3) learning 题 query → 空
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=None),
            FakeResult(items=[]),
            FakeResult(items=[]),
        ])
        result = await svc.get_recommend(mock_db, "u-1", n=3)
        assert result == []

    async def test_with_weak_topics_recommends(self, mock_db):
        from tests.conftest import FakeResult
        prof = SimpleNamespace(weak_topics=["agent"])
        # 1) Profile → 有 weak_topics
        # 2) weak_topics → Question where topic='agent'
        # 3) new 题
        # 4) learning 题
        # 5) q_row lookup（db.get）
        q1 = SimpleNamespace(id="q-1", topic="agent", sub_topic="react",
                             difficulty=3, question_text="Q1?")
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=prof),
            FakeResult(items=[q1]),  # weak_topics Questions
            FakeResult(items=[]),     # new
            FakeResult(items=[]),     # learning
        ])
        mock_db.get = AsyncMock(return_value=q1)

        result = await svc.get_recommend(mock_db, "u-1", n=3)
        assert len(result) >= 1
        assert result[0]["id"] == "q-1"

    async def test_falls_back_to_user_question(self, mock_db):
        """db.get(Question) 返回 None 时试 db.get(UserQuestion)"""
        from tests.conftest import FakeResult
        prof = SimpleNamespace(weak_topics=[])
        u_q = SimpleNamespace(id="u-q-1", topic="custom", sub_topic=None,
                              difficulty=2, question_text="User Q?", source="user_note")
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=prof),       # Profile query
            FakeResult(items=[]),          # new 题
            FakeResult(items=["u-q-1"]),   # learning 题（返回 qid）
        ])
        # db.get 第一次 Question 返回 None，第二次 UserQuestion 返回 u_q
        mock_db.get = AsyncMock(side_effect=[None, u_q])

        result = await svc.get_recommend(mock_db, "u-1", n=3)
        assert len(result) >= 1
        assert result[0]["source"] == "user_note"

    async def test_handles_null_topic(self, mock_db):
        """profile.weak_topics 为 None 时不 crash"""
        from tests.conftest import FakeResult
        prof = SimpleNamespace(weak_topics=None)
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=prof),
            FakeResult(items=[]),
            FakeResult(items=[]),
        ])
        result = await svc.get_recommend(mock_db, "u-1", n=3)
        assert isinstance(result, list)


# ─── LearningSession CRUD ─────────────────────────────────────

class TestStartSession:
    async def test_creates_session(self, mock_db):
        result = await svc.start_session(mock_db, "u-1", "review")
        added = mock_db.add.call_args.args[0]
        assert added.user_id == "u-1"
        assert added.type == "review"
        assert added.items == []
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()

    async def test_default_type_is_practice(self, mock_db):
        await svc.start_session(mock_db, "u-1")
        added = mock_db.add.call_args.args[0]
        assert added.type == "practice"


class TestEndSession:
    async def test_returns_none_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.end_session(mock_db, "u-1", "s-1", []) is None

    async def test_returns_none_when_owner_mismatch(self, mock_db):
        s = SimpleNamespace(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=s)
        assert await svc.end_session(mock_db, "u-1", "s-1", []) is None

    async def test_updates_session(self, mock_db):
        started = datetime.now(timezone.utc) - timedelta(seconds=30)
        s = SimpleNamespace(
            id="s-1", user_id="u-1",
            started_at=started, ended_at=None, duration_sec=None, items=None,
        )
        mock_db.get = AsyncMock(return_value=s)
        items = [{"qid": "q-1", "score": 4}]

        result = await svc.end_session(mock_db, "u-1", "s-1", items)
        assert s.ended_at is not None
        assert s.duration_sec >= 30
        assert s.items == items
        mock_db.commit.assert_awaited()

    async def test_handles_none_started_at(self, mock_db):
        s = SimpleNamespace(
            id="s-1", user_id="u-1",
            started_at=None, ended_at=None, duration_sec=None, items=None,
        )
        mock_db.get = AsyncMock(return_value=s)
        result = await svc.end_session(mock_db, "u-1", "s-1", [])
        # started_at 为 None 时跳过 duration_sec 计算
        assert s.duration_sec is None
        assert result is s


class TestGetRecentSessions:
    async def test_returns_recent_sessions(self, mock_db):
        from tests.conftest import FakeResult
        s1 = SimpleNamespace(
            id="s-1", type="review",
            started_at=datetime.now(timezone.utc) - timedelta(days=1),
            ended_at=datetime.now(timezone.utc),
            duration_sec=600,
            items=[{"x": 1}, {"y": 2}],
        )
        s2 = SimpleNamespace(
            id="s-2", type="practice",
            started_at=datetime.now(timezone.utc) - timedelta(days=2),
            ended_at=None, duration_sec=None, items=None,
        )
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[s1, s2]))

        result = await svc.get_recent_sessions(mock_db, "u-1")
        assert len(result["items"]) == 2
        assert result["items"][0]["duration_sec"] == 600
        assert result["items"][0]["item_count"] == 2
        assert result["items"][1]["item_count"] == 0  # None items
        assert result["items"][1]["ended_at"] is None

    async def test_empty(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        result = await svc.get_recent_sessions(mock_db, "u-1")
        assert result["items"] == []


# ─── get_learn_stats ──────────────────────────────────────────

class TestGetLearnStats:
    async def test_returns_cached_when_hit(self, mock_db, mock_cache):
        cached = {"total_practice": 10, "accuracy": 80.0}
        mock_cache.get = AsyncMock(return_value=cached)
        result = await svc.get_learn_stats(mock_db, "u-1")
        assert result == cached
        mock_db.execute.assert_not_called()

    async def test_aggregates_stats(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        # status rows: [(status, count)]
        s1 = SimpleNamespace(status="new", cnt=5)
        s2 = SimpleNamespace(status="mastered", cnt=3)
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[s1, s2]),    # status group
            FakeResult(items=[(20, 16)]), # total / correct
            FakeResult(scalar=2),         # bookmarked count
            FakeResult(scalar=600),       # week session sum
        ])
        result = await svc.get_learn_stats(mock_db, "u-1")
        assert result["total_practice"] == 20
        assert result["total_correct"] == 16
        assert result["accuracy"] == 80.0  # 16/20 * 100
        assert result["by_status"]["new"] == 5
        assert result["by_status"]["mastered"] == 3
        assert result["bookmarked"] == 2
        assert result["week_session_sec"] == 600

    async def test_zero_practice_no_division_error(self, mock_db, mock_cache):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),         # 0 status
            FakeResult(items=[(0, 0)]),   # 0 total
            FakeResult(scalar=0),         # 0 bookmarked
            FakeResult(scalar=0),         # 0 week
        ])
        result = await svc.get_learn_stats(mock_db, "u-1")
        assert result["accuracy"] == 0  # 0 练习时不除
        assert result["total_practice"] == 0


# ─── cache invalidation helpers ───────────────────────────────

class TestInvalidateTopicStats:
    def test_schedules_delete_task(self, mock_cache, monkeypatch):
        """invalidate_topic_stats 用 asyncio.create_task 触发 cache.delete。

        pytest 同步上下文没有 event loop，patch create_task 验证它被调用过。
        """
        mock_create_task = MagicMock()
        monkeypatch.setattr("asyncio.create_task", mock_create_task)
        svc.invalidate_topic_stats("u-1")
        assert mock_create_task.call_count == 1


class TestInvalidateReviewQueue:
    def test_schedules_delete_task(self, mock_cache, monkeypatch):
        mock_create_task = MagicMock()
        monkeypatch.setattr("asyncio.create_task", mock_create_task)
        svc.invalidate_review_queue("u-1")
        assert mock_create_task.call_count == 1