"""单测: services/profile_settlement_service.py

V2.1 PR 1 — T1: 骨架测试（仅验证 class 可实例化 + 4 方法占位存在）
后续 T2-T7 会逐步加业务测试；T8 凑齐 ≥ 80% 覆盖。

对齐 V1 测试风格：参考 test_learning_progress_service.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services import profile_settlement_service as svc


# ─── T1: 骨架（class 可导入 / 4 方法占位）────────────────

class TestSettlementServiceSkeleton:
    """T1: 骨架测试 — 验证 class 导入 + 实例化 + 4 方法签名占位。

    后续 T2-T7 会替换这些占位为业务实现。
    """

    def test_class_importable(self):
        """T1: class 可被 import + 实例化。"""
        service = svc.ProfileSettlementService()
        assert service is not None

    def test_class_has_settle_after_practice(self):
        """T1: 必有 settle_after_practice 方法。"""
        assert hasattr(svc.ProfileSettlementService, "settle_after_practice")
        assert callable(svc.ProfileSettlementService.settle_after_practice)

    def test_class_has_settle_after_interview(self):
        """T1: 必有 settle_after_interview 方法。"""
        assert hasattr(svc.ProfileSettlementService, "settle_after_interview")
        assert callable(svc.ProfileSettlementService.settle_after_interview)

    def test_class_has_weekly_full_refresh(self):
        """T1: 必有 weekly_full_refresh 方法。"""
        assert hasattr(svc.ProfileSettlementService, "weekly_full_refresh")
        assert callable(svc.ProfileSettlementService.weekly_full_refresh)

    def test_class_has_manual_refresh(self):
        """T1: 必有 manual_refresh 方法。"""
        assert hasattr(svc.ProfileSettlementService, "manual_refresh")
        assert callable(svc.ProfileSettlementService.manual_refresh)

    def test_logger_initialized(self):
        """T1: 模块级 logger 用 codemock.profile_settlement 命名（V1 风格）。"""
        assert hasattr(svc, "log")
        assert svc.log.name == "codemock.profile_settlement"


# ─── T1 后续补充：schema 导入（spec.md §4 数据契约）────────

class TestSettlementSchemasImportable:
    """T1: 验证 SettlementResult / TopicSettlement schema 可被 import。"""

    def test_topic_settlement_importable(self):
        from schemas.settlement import TopicSettlement
        assert TopicSettlement is not None

    def test_settlement_result_importable(self):
        from schemas.settlement import SettlementResult
        assert SettlementResult is not None

    def test_settlement_result_required_fields(self):
        """T1: SettlementResult 必有 user_id/settled_at/triggered_by。"""
        from schemas.settlement import SettlementResult
        fields = SettlementResult.model_fields
        assert "user_id" in fields
        assert "settled_at" in fields
        assert "triggered_by" in fields

    def test_topic_settlement_required_fields(self):
        """T1: TopicSettlement 必有 topic/error_rate/practice_count。"""
        from schemas.settlement import TopicSettlement
        fields = TopicSettlement.model_fields
        assert "topic" in fields
        assert "error_rate" in fields
        assert "practice_count" in fields


# ─── T2: settle_after_practice 业务实现 ─────────────────────

class TestSettleAfterPractice:
    """T2: 答题后触发的画像沉淀 — 4 个测试覆盖 GWT-1/2/3/9。"""

    async def test_happy_path_adds_to_weak_topics(self, mock_db):
        """GWT-1: score=4, error_rate=0.75 → weak_topics 出现新项 + last_active_at 更新。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        # 1st execute: Question.topic
        topic_result = FakeResult(scalar="网络层")
        # 2nd execute: QuestionProgress（practice=4, correct=1 → error_rate=0.75）
        progress = SimpleNamespace(
            practice_count=4,
            correct_count=1,
            last_practiced_at=now,
        )
        progress_result = FakeResult(scalar=progress)
        # 3rd execute: Profile with FOR UPDATE
        profile = SimpleNamespace(
            user_id=str(user_id),
            weak_topics=[],
            mastered_topics=[],
            last_active_at=None,
            updated_at=now,
        )
        profile_result = FakeResult(scalar=profile)

        mock_db.execute = AsyncMock(side_effect=[
            topic_result, progress_result, profile_result,
        ])

        result = await svc.ProfileSettlementService().settle_after_practice(
            user_id, "q-1", score=4, db=mock_db,
        )

        assert result is not None
        assert result.triggered_by == "practice"
        assert any(t.topic == "网络层" for t in result.weak_topics)
        # last_active_at 被设了
        assert profile.last_active_at is not None
        # commit 被调
        assert mock_db.commit.await_count == 1

    async def test_edge_moves_to_mastered_on_second_correct(self, mock_db):
        """GWT-2: practice>=2 + score>=4 + 已在 weak → 移到 mastered_topics。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        topic_result = FakeResult(scalar="React Hooks")
        # practice=2, correct=2 → error_rate=0 → 不会进 weak，但满足"答对第 2 次"
        progress = SimpleNamespace(
            practice_count=2, correct_count=2, last_practiced_at=now,
        )
        progress_result = FakeResult(scalar=progress)
        # 已在 weak 中有这个 topic
        profile = SimpleNamespace(
            user_id=str(user_id),
            weak_topics=[{
                "topic": "React Hooks",
                "error_rate": 0.5,
                "practice_count": 1,
                "last_practiced_at": "2026-06-27T00:00:00+00:00",
                "related_question_ids": ["q-1"],
            }],
            mastered_topics=[],
            last_active_at=None,
            updated_at=now,
        )
        profile_result = FakeResult(scalar=profile)

        mock_db.execute = AsyncMock(side_effect=[
            topic_result, progress_result, profile_result,
        ])

        result = await svc.ProfileSettlementService().settle_after_practice(
            user_id, "q-1", score=4, db=mock_db,
        )

        assert result is not None
        # weak 应该清空（topic 被移走）
        assert all(t.topic != "React Hooks" for t in result.weak_topics)
        # mastered 应该有 React Hooks
        assert any(t.topic == "React Hooks" for t in result.mastered_topics)

    async def test_failure_concurrent_lock_retries_once(self, mock_db):
        """GWT-3: 乐观锁 — commit 第 1 次失败重试 1 次，第 2 次成功。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar="网络层"),         # Question.topic
            FakeResult(scalar=SimpleNamespace(  # QuestionProgress
                practice_count=4, correct_count=1, last_practiced_at=now,
            )),
            FakeResult(scalar=SimpleNamespace(  # Profile with FOR UPDATE
                user_id=str(user_id),
                weak_topics=[],
                mastered_topics=[],
                last_active_at=None,
                updated_at=now,
            )),
        ])
        # commit 第 1 次失败（乐观锁冲突），第 2 次成功
        mock_db.commit = AsyncMock(side_effect=[Exception("Lock conflict"), None])
        mock_db.rollback = AsyncMock()

        result = await svc.ProfileSettlementService().settle_after_practice(
            user_id, "q-1", score=4, db=mock_db,
        )

        # commit 调了 2 次（第 1 次失败 + 第 2 次成功）
        assert mock_db.commit.await_count == 2
        # rollback 至少 1 次
        assert mock_db.rollback.await_count >= 1
        # 第 2 次成功 → 返回 SettlementResult
        assert result is not None
        assert result.triggered_by == "practice"

    async def test_failure_db_exception_returns_none_no_throw(self, mock_db):
        """GWT-9: DB 失败 → log warning + return None，**不抛异常**（决策 7A）。"""
        from uuid import uuid4

        user_id = uuid4()
        # execute 直接抛错
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection lost"))
        mock_db.rollback = AsyncMock()

        # 关键：调用不抛异常
        result = await svc.ProfileSettlementService().settle_after_practice(
            user_id, "q-1", score=4, db=mock_db,
        )

        assert result is None
        # rollback 被尝试
        assert mock_db.rollback.await_count >= 1

    async def test_failure_question_not_found_returns_none(self, mock_db):
        """T2 边界: qid 不存在 → log warning + return None。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        result = await svc.ProfileSettlementService().settle_after_practice(
            user_id, "nonexistent-qid", score=4, db=mock_db,
        )
        assert result is None


# ─── T3: settle_after_interview 业务实现 ─────────────────────

class TestSettleAfterInterview:
    """T3: 面试后触发的画像沉淀 — 4 个测试覆盖 happy/edge/no_report/db_failure。"""

    async def test_happy_path_aggregates_blind_spots_into_weak(self, mock_db):
        """Happy: Report.top_blind_spots 3 项 → 合并进 Profile.weak_topics。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        interview_id = uuid4()
        now = datetime.now(timezone.utc)

        # 1st execute: Report
        report = SimpleNamespace(
            interview_id=str(interview_id),
            top_blind_spots=[
                {"topic": "分布式锁", "error_rate": 0.7, "related_question_ids": ["q-1"]},
                {"topic": "消息队列", "error_rate": 0.6, "related_question_ids": ["q-2"]},
                {"topic": "索引优化", "error_rate": 0.5, "related_question_ids": ["q-3"]},
            ],
        )
        report_result = FakeResult(scalar=report)
        # 2nd execute: Profile
        profile = SimpleNamespace(
            user_id=str(user_id),
            weak_topics=[],
            mastered_topics=[],
            last_active_at=None,
            updated_at=now,
        )
        profile_result = FakeResult(scalar=profile)

        mock_db.execute = AsyncMock(side_effect=[report_result, profile_result])

        result = await svc.ProfileSettlementService().settle_after_interview(
            user_id, interview_id, db=mock_db,
        )

        assert result is not None
        assert result.triggered_by == "interview"
        topics = {t.topic for t in result.weak_topics}
        assert "分布式锁" in topics
        assert "消息队列" in topics
        assert "索引优化" in topics
        # 3 项都进 weak
        assert len(result.weak_topics) == 3
        # last_active_at 被设
        assert profile.last_active_at is not None

    async def test_edge_dedup_no_duplicate_topics(self, mock_db):
        """Edge: top_blind_spots 包含已在 weak 的 topic → 不重复添加。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        interview_id = uuid4()
        now = datetime.now(timezone.utc)

        report = SimpleNamespace(
            interview_id=str(interview_id),
            top_blind_spots=[
                {"topic": "分布式锁", "error_rate": 0.8},  # 已在 weak
                {"topic": "消息队列", "error_rate": 0.6},  # 新的
            ],
        )
        report_result = FakeResult(scalar=report)
        profile = SimpleNamespace(
            user_id=str(user_id),
            weak_topics=[{
                "topic": "分布式锁",
                "error_rate": 0.5,
                "practice_count": 1,
                "last_practiced_at": "2026-06-27T00:00:00+00:00",
                "related_question_ids": [],
            }],
            mastered_topics=[],
            last_active_at=None,
            updated_at=now,
        )
        profile_result = FakeResult(scalar=profile)

        mock_db.execute = AsyncMock(side_effect=[report_result, profile_result])

        result = await svc.ProfileSettlementService().settle_after_interview(
            user_id, interview_id, db=mock_db,
        )

        assert result is not None
        topics = [t.topic for t in result.weak_topics]
        # 分布式锁 不重复
        assert topics.count("分布式锁") == 1
        # 消息队列 新增
        assert "消息队列" in topics
        # 总共 2 项
        assert len(result.weak_topics) == 2

    async def test_failure_no_report_returns_none(self, mock_db):
        """T3 边界: interview 没 Report → log warning + return None。"""
        from tests.conftest import FakeResult
        from uuid import uuid4

        user_id = uuid4()
        interview_id = uuid4()
        mock_db.execute = AsyncMock(return_value=FakeResult(scalar=None))

        result = await svc.ProfileSettlementService().settle_after_interview(
            user_id, interview_id, db=mock_db,
        )
        assert result is None

    async def test_failure_db_exception_returns_none_no_throw(self, mock_db):
        """T3 边界: DB 失败 → log + return None，**不抛**（决策 7A）。"""
        from uuid import uuid4

        user_id = uuid4()
        interview_id = uuid4()
        mock_db.execute = AsyncMock(side_effect=Exception("DB down"))
        mock_db.rollback = AsyncMock()

        # 关键：不抛
        result = await svc.ProfileSettlementService().settle_after_interview(
            user_id, interview_id, db=mock_db,
        )

        assert result is None
        assert mock_db.rollback.await_count >= 1

