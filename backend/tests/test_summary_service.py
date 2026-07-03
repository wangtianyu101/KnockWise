"""单测: services/summary_service.py

V2.3 PR 3 — T16: 骨架测试（class 可实例化 + 5 方法占位 + LLM 模板）
后续 T17-T20 实施业务，T21 凑齐 ≥ 80% 覆盖。
"""
from __future__ import annotations

import pytest

from services import summary_service as svc


# ─── T16: 骨架 ────────────────────────────────

class TestSummaryServiceSkeleton:
    """T16: SummaryService 骨架测试。"""

    def test_class_importable(self):
        service = svc.SummaryService()
        assert service is not None

    def test_class_has_daily(self):
        assert hasattr(svc.SummaryService, "daily")

    def test_class_has_weekly(self):
        assert hasattr(svc.SummaryService, "weekly")

    def test_class_has_monthly(self):
        assert hasattr(svc.SummaryService, "monthly")

    def test_class_has_sync_daily_to_obsidian(self):
        assert hasattr(svc.SummaryService, "sync_daily_to_obsidian")

    def test_class_has_dashboard(self):
        assert hasattr(svc.SummaryService, "dashboard")

    def test_class_has_generate_narrative(self):
        assert hasattr(svc.SummaryService, "_generate_narrative")

    def test_logger_initialized(self):
        assert hasattr(svc, "log")
        assert svc.log.name == "codemock.summary"

    def test_cache_ttl_constant(self):
        """决策 2A: cache TTL = 3600s (1h)"""
        assert svc.CACHE_TTL == 3600

    def test_cache_key_prefixes(self):
        """Redis key 前缀：summary:dashboard:{user_id} + summary:profile:{user_id}"""
        assert svc.DASHBOARD_CACHE_PREFIX == "summary:dashboard:"
        assert svc.PROFILE_CACHE_PREFIX == "summary:profile:"

    def test_init_reads_llm_provider_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        service = svc.SummaryService()
        assert service.llm_provider == "openai"
