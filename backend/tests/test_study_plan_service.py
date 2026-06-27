"""单测: services/study_plan_service.py

覆盖 5 个函数 + 边界条件，目标 ≥ 80%。
"""
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import study_plan_service as svc


# ─── list_plans ───────────────────────────────────────────────

class TestListPlans:
    async def test_returns_plan_dicts(self, mock_db):
        from tests.conftest import FakeResult
        p1 = SimpleNamespace(
            id="plan-1", name="Q1 plan", description="d", goal="g",
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            status="active", weekly_target=[{"week_idx": 0, "target_count": 5}],
            progress={"done_count": 3},
        )
        p2 = SimpleNamespace(
            id="plan-2", name="Q2 plan", description=None, goal=None,
            start_date=None, end_date=None,
            status="completed", weekly_target=None, progress=None,
        )
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[p1, p2]))

        result = await svc.list_plans(mock_db, "u-1")
        assert len(result["items"]) == 2
        assert result["items"][0]["id"] == "plan-1"
        assert result["items"][0]["weekly_target"] == [{"week_idx": 0, "target_count": 5}]
        # None 字段处理
        assert result["items"][1]["start_date"] is None
        assert result["items"][1]["weekly_target"] == []
        assert result["items"][1]["progress"] == {}

    async def test_empty_list(self, mock_db):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        result = await svc.list_plans(mock_db, "u-1")
        assert result["items"] == []


# ─── get_plan ────────────────────────────────────────────────

class TestGetPlan:
    async def test_returns_none_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.get_plan(mock_db, "u-1", "plan-1") is None

    async def test_returns_none_when_owner_mismatch(self, mock_db):
        p = SimpleNamespace(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=p)
        assert await svc.get_plan(mock_db, "u-1", "plan-1") is None

    async def test_returns_plan(self, mock_db):
        p = SimpleNamespace(id="plan-1", user_id="u-1", name="my plan")
        mock_db.get = AsyncMock(return_value=p)
        result = await svc.get_plan(mock_db, "u-1", "plan-1")
        assert result is p


# ─── create_plan ──────────────────────────────────────────────

class TestCreatePlan:
    async def test_minimal_data(self, mock_db):
        data = {"name": "Q1 plan"}
        await svc.create_plan(mock_db, "u-1", data)
        added = mock_db.add.call_args.args[0]
        assert added.name == "Q1 plan"
        assert added.user_id == "u-1"
        assert added.status == "active"
        assert added.weekly_target == []
        assert added.progress == {}
        mock_db.commit.assert_awaited()
        mock_db.refresh.assert_awaited()

    async def test_full_data_with_iso_dates(self, mock_db):
        data = {
            "name": "Q1 plan",
            "description": "learn agent",
            "goal": "interview ready",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "active",
            "weekly_target": [{"week_idx": 0, "target_count": 5}],
            "progress": {"done": 0},
        }
        await svc.create_plan(mock_db, "u-1", data)
        added = mock_db.add.call_args.args[0]
        assert added.start_date == date(2026, 1, 1)
        assert added.end_date == date(2026, 3, 31)
        assert added.weekly_target == [{"week_idx": 0, "target_count": 5}]

    async def test_passes_through_date_objects(self, mock_db):
        """start_date 是 date 对象而非字符串时，直接传过去"""
        data = {
            "name": "p",
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 6, 30),
        }
        await svc.create_plan(mock_db, "u-1", data)
        added = mock_db.add.call_args.args[0]
        assert added.start_date == date(2026, 1, 1)


# ─── update_plan ──────────────────────────────────────────────

class TestUpdatePlan:
    async def test_returns_none_when_plan_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        result = await svc.update_plan(mock_db, "u-1", "plan-1", {"name": "new"})
        assert result is None

    async def test_returns_none_when_owner_mismatch(self, mock_db):
        p = SimpleNamespace(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=p)
        result = await svc.update_plan(mock_db, "u-1", "plan-1", {"name": "new"})
        assert result is None

    async def test_updates_specified_fields(self, mock_db):
        p = SimpleNamespace(
            user_id="u-1", name="old", description="d", goal="g",
            status="active", weekly_target=[], progress={},
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            updated_at=None,
        )
        mock_db.get = AsyncMock(return_value=p)
        await svc.update_plan(mock_db, "u-1", "plan-1", {
            "name": "new", "weekly_target": [{"target_count": 10}]
        })
        assert p.name == "new"
        assert p.weekly_target == [{"target_count": 10}]
        # 没传的字段不动
        assert p.description == "d"
        assert p.updated_at is not None
        mock_db.commit.assert_awaited()

    async def test_converts_iso_string_to_date(self, mock_db):
        p = SimpleNamespace(
            user_id="u-1", name="p", description=None, goal=None,
            status="active", weekly_target=[], progress={},
            start_date=None, end_date=None, updated_at=None,
        )
        mock_db.get = AsyncMock(return_value=p)
        await svc.update_plan(mock_db, "u-1", "plan-1", {"start_date": "2026-02-01"})
        assert p.start_date == date(2026, 2, 1)


# ─── delete_plan ──────────────────────────────────────────────

class TestDeletePlan:
    async def test_returns_false_when_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.delete_plan(mock_db, "u-1", "plan-1") is False

    async def test_returns_false_when_owner_mismatch(self, mock_db):
        p = SimpleNamespace(user_id="OTHER")
        mock_db.get = AsyncMock(return_value=p)
        assert await svc.delete_plan(mock_db, "u-1", "plan-1") is False

    async def test_deletes_plan(self, mock_db):
        p = SimpleNamespace(user_id="u-1", id="plan-1")
        mock_db.get = AsyncMock(return_value=p)
        result = await svc.delete_plan(mock_db, "u-1", "plan-1")
        assert result is True
        mock_db.delete.assert_awaited_with(p)
        mock_db.commit.assert_awaited()


# ─── get_plan_progress（聚合逻辑）────────────────────────────

class TestGetPlanProgress:
    async def test_returns_none_when_plan_not_found(self, mock_db):
        mock_db.get = AsyncMock(return_value=None)
        assert await svc.get_plan_progress(mock_db, "u-1", "plan-1") is None

    async def test_basic_progress_aggregation(self, mock_db):
        from tests.conftest import FakeResult
        # plan with weekly_target total = 10
        p = SimpleNamespace(
            id="plan-1", user_id="u-1",
            weekly_target=[
                {"week_idx": 0, "target_count": 5, "target_topics": ["agent"]},
                {"week_idx": 1, "target_count": 5, "target_topics": ["rag"]},
            ],
            progress={},
        )
        mock_db.get = AsyncMock(return_value=p)

        # status_rows aggregate query
        # 2 个 topic 各调 2 次 (total + mastered) = 4 次 weak_remaining 循环
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[("mastered", 3), ("learning", 2), ("new", 5)]),
            FakeResult(items=[(5,)]),  # agent total
            FakeResult(items=[(3,)]),  # agent mastered
            FakeResult(items=[(2,)]),  # rag total
            FakeResult(items=[(1,)]),  # rag mastered
        ])

        result = await svc.get_plan_progress(mock_db, "u-1", "plan-1")
        assert result["total_target"] == 10
        assert result["mastered"] == 3
        assert result["learning"] == 2
        assert result["new_count"] == 5
        assert result["completion_rate"] == 0.3  # 3/10

    async def test_empty_weekly_target_no_division_error(self, mock_db):
        from tests.conftest import FakeResult
        p = SimpleNamespace(
            id="plan-1", user_id="u-1",
            weekly_target=None,  # 空
            progress={},
        )
        mock_db.get = AsyncMock(return_value=p)
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))

        result = await svc.get_plan_progress(mock_db, "u-1", "plan-1")
        assert result["total_target"] == 0
        assert result["completion_rate"] == 0  # 没 target 时 0% 不报错
        assert result["weak_topics_remaining"] == []

    async def test_topic_with_50_percent_mastery_not_weak(self, mock_db):
        """mastered/total >= 50% 不算 weak"""
        from tests.conftest import FakeResult
        p = SimpleNamespace(
            id="plan-1", user_id="u-1",
            weekly_target=[{"week_idx": 0, "target_count": 5, "target_topics": ["agent"]}],
            progress={},
        )
        mock_db.get = AsyncMock(return_value=p)
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),  # status_rows（空）
            FakeResult(items=[(2,)]),  # topic total
            FakeResult(items=[(1,)]),  # topic mastered → 50%
        ])

        result = await svc.get_plan_progress(mock_db, "u-1", "plan-1")
        # 50% 不算 weak（strictly < 0.5）
        assert "agent" not in result["weak_topics_remaining"]

    async def test_topic_with_low_mastery_is_weak(self, mock_db):
        from tests.conftest import FakeResult
        p = SimpleNamespace(
            id="plan-1", user_id="u-1",
            weekly_target=[{"week_idx": 0, "target_count": 5, "target_topics": ["agent"]}],
            progress={},
        )
        mock_db.get = AsyncMock(return_value=p)
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),
            FakeResult(items=[(10,)]),  # total = 10
            FakeResult(items=[(2,)]),   # mastered = 2 → 20% < 50%
        ])

        result = await svc.get_plan_progress(mock_db, "u-1", "plan-1")
        assert "agent" in result["weak_topics_remaining"]

    async def test_topic_with_zero_total_not_weak(self, mock_db):
        """total=0 时不计入 weak（避免除零）"""
        from tests.conftest import FakeResult
        p = SimpleNamespace(
            id="plan-1", user_id="u-1",
            weekly_target=[{"week_idx": 0, "target_count": 5, "target_topics": ["agent"]}],
            progress={},
        )
        mock_db.get = AsyncMock(return_value=p)
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[]),
            FakeResult(items=[(0,)]),  # total = 0
            FakeResult(items=[(0,)]),
        ])

        result = await svc.get_plan_progress(mock_db, "u-1", "plan-1")
        assert "agent" not in result["weak_topics_remaining"]

    async def test_handles_none_scalar_from_db(self, mock_db):
        """scalar() 返回 None 时不 crash"""
        from tests.conftest import FakeResult
        p = SimpleNamespace(
            id="plan-1", user_id="u-1",
            weekly_target=[{"week_idx": 0, "target_count": 5, "target_topics": ["agent"]}],
            progress={},
        )
        mock_db.get = AsyncMock(return_value=p)
        # 注意：FakeResult.scalar 默认 None，scalar_one_or_none 也是 None
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        result = await svc.get_plan_progress(mock_db, "u-1", "plan-1")
        # 不 crash 即可
        assert "agent" not in result["weak_topics_remaining"]