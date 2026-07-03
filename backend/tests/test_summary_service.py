"""单测: services/summary_service.py

V2.3 PR 3 — T16: 骨架测试（class 可实例化 + 5 方法占位 + LLM 模板）
后续 T17-T20 实施业务，T21 凑齐 ≥ 80% 覆盖。
"""
from __future__ import annotations

from unittest.mock import AsyncMock

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

    async def test_class_has_generate_narrative_async(self):
        import inspect
        assert inspect.iscoroutinefunction(svc.SummaryService._generate_narrative)

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


# ─── T17: _generate_narrative (LLM + 降级) ──────────────

class TestGenerateNarrative:
    """T17: LLM narrative 生成 — happy / 降级 / strip markdown。"""

    def test_strip_markdown_removes_code_blocks(self):
        """移除 ```...``` 代码块。"""
        s = svc.SummaryService._strip_markdown("```python\nprint('hi')\n```")
        assert "```" not in s
        assert "print" not in s  # 代码块内容被移除

    def test_strip_markdown_removes_links(self):
        s = svc.SummaryService._strip_markdown("[click](http://x.com)")
        assert "http" not in s
        assert "click" in s

    def test_strip_markdown_removes_emphasis(self):
        s = svc.SummaryService._strip_markdown("**bold** and *italic*")
        # * 移除，保留文字
        assert "bold" in s
        assert "italic" in s
        assert "**" not in s

    def test_fallback_narrative_basic(self):
        """LLM 降级 → 规则生成叙述。"""
        result = svc.SummaryService._fallback_narrative({
            "yesterday_count": 8,
            "mastered": [{"topic": "React Hooks"}],
            "weak_shift": [{"from_topic": "网络层", "to_topic": "状态管理"}],
        })
        assert "8" in result
        assert "React Hooks" in result
        assert "网络层" in result
        assert "状态管理" in result

    def test_fallback_narrative_empty(self):
        """0 题 + 无 master → 简单叙述（spec GWT-7）。"""
        result = svc.SummaryService._fallback_narrative({
            "yesterday_count": 0,
            "mastered": [],
            "weak_shift": [],
        })
        assert "0 道题" in result

    async def test_generate_narrative_returns_fallback_on_llm_failure(self, monkeypatch):
        """LLM 调失败 → 降级到规则生成（**不抛**，决策 7A）。"""
        # 让 _get_llm 抛错 → 触发 fallback
        def boom_llm():
            raise RuntimeError("LLM down")

        monkeypatch.setattr(svc.SummaryService, "_get_llm", boom_llm)
        service = svc.SummaryService()

        text, llm_success = await service._generate_narrative(
            stats={"yesterday_count": 5},
            template="今天答了 {yesterday_count} 题。",
        )
        # 关键：返回降级版（不抛），flag=False
        assert text is not None
        assert "5" in text
        assert llm_success is False

    async def test_generate_narrative_returns_success_flag(self, monkeypatch):
        """LLM 调成功 → (text, True) tuple。"""
        from langchain_core.messages import AIMessage

        # mock 完整 LLM chain
        class FakeLLM:
            async def ainvoke(self, messages):
                return AIMessage(content="这是 LLM 生成的总结。")

        monkeypatch.setattr(svc.SummaryService, "_get_llm", lambda self: FakeLLM())
        service = svc.SummaryService()

        text, llm_success = await service._generate_narrative(
            stats={"yesterday_count": 3},
            template="x {yesterday_count} y",
        )
        assert llm_success is True
        assert "LLM 生成的总结" in text


# ─── T18: daily + dashboard（含 Redis 缓存）────────────────

class TestDailyDashboard:
    """T18: daily/dashboard — Redis 缓存 + DB 聚合 + LLM + 降级。"""

    async def test_daily_cache_hit_returns_cached(self, mock_db, mock_cache):
        """Redis 命中 → 直接返回缓存，不调 DB/LLM（spec GWT-8）。"""
        import datetime as _dt

        cached_value = {
            "title": "今日学习总结",
            "date": "2026-06-28",
            "yesterday_count": 5,
            "mastered": [],
            "weak_shift": [],
            "body": "cached body",
            "_fallback": False,
        }
        # cache.get 直接返回 cached_value（不需要序列化）
        async def fake_get(key):
            return cached_value
        mock_cache.get = fake_get

        service = svc.SummaryService()
        result = await service.daily(
            "user-1", date=_dt.date(2026, 6, 28), db=mock_db,
        )

        assert result == cached_value
        # DB 没被查（cache 命中短路）
        assert not mock_db.execute.await_count

    async def test_daily_cache_miss_queries_db_and_sets_cache(self, mock_db, mock_cache):
        """Redis miss → DB 聚合 + LLM + cache.set（happy path）。"""
        from tests.conftest import FakeResult
        from types import SimpleNamespace
        import datetime as _dt
        from unittest.mock import patch

        today = _dt.date(2026, 6, 28)

        # cache miss → return None
        async def fake_get(key):
            return None

        mock_cache.get = fake_get
        mock_cache.set = AsyncMock()

        # DB 1st: count question_answer_logs → 5
        # DB 2nd: select Profile
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(scalar=5),  # yesterday_count
            FakeResult(scalar=SimpleNamespace(  # profile
                mastered_topics=[{"topic": "React Hooks"}],
                weak_topics=[{"topic": "网络层"}],
            )),
        ])

        # mock LLM：返回已知 narrative + llm_success=True（tuple）
        with patch.object(
            svc.SummaryService, "_generate_narrative",
            new_callable=AsyncMock,
            return_value=("昨天你答了 5 道题，掌握了 1 个新 topic。", True),
        ):
            service = svc.SummaryService()
            result = await service.daily("user-1", date=today, db=mock_db)

        assert result is not None
        assert result["yesterday_count"] == 5
        assert result["_fallback"] is False
        # cache.set 被调（写入 1h TTL）
        mock_cache.set.assert_awaited_once()

    async def test_daily_db_failure_falls_back(self, mock_db, mock_cache):
        """DB 不可达 → 降级返回（_fallback=True，**不抛**）。"""
        import datetime as _dt

        async def fake_get(key):
            return None

        mock_cache.get = fake_get
        mock_cache.set = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB down"))

        service = svc.SummaryService()
        result = await service.daily(
            "user-1", date=_dt.date(2026, 6, 28), db=mock_db,
        )
        assert result is not None
        assert result["_fallback"] is True
        assert result["yesterday_count"] == 0

    async def test_dashboard_calls_daily(self, mock_db, mock_cache):
        """dashboard 是 daily(today) 的简写。"""
        import datetime as _dt

        async def fake_get(key):
            return None

        mock_cache.get = fake_get
        mock_cache.set = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB down"))

        service = svc.SummaryService()
        result = await service.dashboard("user-1", db=mock_db)
        # dashboard 走 daily fallback
        assert result is not None
        assert result["_fallback"] is True
        assert result["date"] == _dt.date.today().isoformat()
