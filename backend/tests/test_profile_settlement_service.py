"""单测: services/profile_settlement_service.py

V2.1 PR 1 — T1: 骨架测试（仅验证 class 可实例化 + 4 方法占位存在）
后续 T2-T7 会逐步加业务测试；T8 凑齐 ≥ 80% 覆盖。

对齐 V1 测试风格：参考 test_learning_progress_service.py
"""
from __future__ import annotations

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
