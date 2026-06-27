"""单测: services/recommendations_service.py

覆盖 5 个函数 + obsidian / news mock，目标 ≥ 80%。
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import recommendations_service as svc


@pytest.fixture
def mock_obsidian(monkeypatch):
    """Mock obsidian.search()。"""
    fake_obsidian = MagicMock()
    fake_obsidian.search = MagicMock(return_value=[])
    monkeypatch.setattr(svc, "obsidian", fake_obsidian)
    return fake_obsidian


@pytest.fixture
def mock_news(monkeypatch):
    """Mock news_service.get_code_stats()。"""
    fake_news = MagicMock()
    fake_news.get_code_stats = MagicMock(return_value={
        "summary": {"total_tokens": 100_000, "total_days": 21, "total_code": 1000}
    })
    monkeypatch.setattr(svc, "news_service", fake_news)
    return fake_news


@pytest.fixture
def fake_user():
    u = SimpleNamespace(id="u-1")
    return u


# ─── _get_weak_spots ──────────────────────────────────────────

class TestGetWeakSpots:
    async def test_no_interviews_returns_empty(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        result = await svc._get_weak_spots(fake_user, mock_db)
        assert result == []

    async def test_counts_blind_spots_from_records(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        # 1 次 execute: 查 Interview（completed）
        interview = SimpleNamespace(id="iv-1", status="completed")
        # 2 次 execute: 查 QuestionRecord
        records = [
            SimpleNamespace(blind_spots=["Memory", "Tool Use"]),
            SimpleNamespace(blind_spots=["Memory"]),
            SimpleNamespace(blind_spots=["Agent 流式输出"]),
        ]
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[interview]),
            FakeResult(items=records),
        ])

        result = await svc._get_weak_spots(fake_user, mock_db)
        assert "Memory" in result
        assert result[0] == "Memory"  # 出现 2 次排第一

    async def test_handles_none_blind_spots(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        interview = SimpleNamespace(id="iv-1", status="completed")
        records = [
            SimpleNamespace(blind_spots=None),
            SimpleNamespace(blind_spots=[]),
        ]
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[interview]),
            FakeResult(items=records),
        ])
        result = await svc._get_weak_spots(fake_user, mock_db)
        assert result == []

    async def test_returns_at_most_5_spots(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        interview = SimpleNamespace(id="iv-1", status="completed")
        records = [
            SimpleNamespace(blind_spots=[f"spot-{i}"]) for i in range(10)
        ]
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[interview]),
            FakeResult(items=records),
        ])
        result = await svc._get_weak_spots(fake_user, mock_db)
        assert len(result) == 5


# ─── _match_knowledge ─────────────────────────────────────────

class TestMatchKnowledge:
    def test_empty_weak_spots_returns_empty(self, mock_obsidian):
        result = svc._match_knowledge([])
        assert result == []

    def test_obsidian_results_become_recs(self, mock_obsidian):
        mock_obsidian.search.return_value = [
            {"name": "agent.md", "path": "/notes/agent.md"},
            {"name": "rag.md", "path": "/notes/rag.md"},
        ]
        result = svc._match_knowledge(["Agent 架构"])
        assert len(result) == 2
        assert all(r["type"] == "knowledge" for r in result)
        assert all(r["priority"] == "high" for r in result)

    def test_deduplicates_by_path(self, mock_obsidian):
        mock_obsidian.search.return_value = [
            {"name": "agent.md", "path": "/notes/agent.md"},
            {"name": "agent.md", "path": "/notes/agent.md"},  # 同 path
        ]
        result = svc._match_knowledge(["Agent 架构"])
        assert len(result) == 1

    def test_fallback_when_obsidian_empty(self, mock_obsidian):
        mock_obsidian.search.return_value = []
        result = svc._match_knowledge(["未知主题"])
        assert len(result) == 1
        assert result[0]["title"].startswith("补充学习")
        assert result[0]["priority"] == "medium"

    def test_limits_to_3_weak_spots(self, mock_obsidian):
        mock_obsidian.search = MagicMock(return_value=[])
        svc._match_knowledge(["a", "b", "c", "d", "e"])
        # 只前 3 个 weak_spots 触发 search
        assert mock_obsidian.search.call_count == 3


# ─── _interview_recs ──────────────────────────────────────────

class TestInterviewRecs:
    async def test_no_completed_interview_suggests_first(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        # 所有 interview 都不是 completed
        mock_db.execute = AsyncMock(return_value=FakeResult(items=[]))
        result = await svc._interview_recs(fake_user, mock_db)
        assert len(result) == 1
        assert result[0]["title"] == "开始第一次面试"
        assert result[0]["priority"] == "high"
        assert result[0]["link"] == "/interview/setup"

    async def test_few_completed_suggests_continue(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        interviews = [
            SimpleNamespace(id=f"iv-{i}", status="completed") for i in range(2)
        ]
        mock_db.execute = AsyncMock(return_value=FakeResult(items=interviews))
        result = await svc._interview_recs(fake_user, mock_db)
        assert result[0]["title"].startswith("继续练习")
        assert "已完成 2 次" in result[0]["title"]
        assert result[0]["priority"] == "medium"

    async def test_three_plus_completed_returns_empty(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        interviews = [
            SimpleNamespace(id=f"iv-{i}", status="completed") for i in range(4)
        ]
        mock_db.execute = AsyncMock(return_value=FakeResult(items=interviews))
        result = await svc._interview_recs(fake_user, mock_db)
        assert result == []

    async def test_in_progress_interviews_not_counted(self, mock_db, fake_user):
        from tests.conftest import FakeResult
        # 3 个 interview，但都是 in_progress
        interviews = [
            SimpleNamespace(id=f"iv-{i}", status="in_progress") for i in range(3)
        ]
        mock_db.execute = AsyncMock(return_value=FakeResult(items=interviews))
        result = await svc._interview_recs(fake_user, mock_db)
        # completed = 0 → 走 "no_completed" 分支
        assert result[0]["title"] == "开始第一次面试"


# ─── _stats_context ───────────────────────────────────────────

class TestStatsContext:
    def test_returns_empty_on_exception(self, mock_news, monkeypatch):
        mock_news.get_code_stats = MagicMock(side_effect=RuntimeError("boom"))
        assert svc._stats_context() == []

    def test_low_tokens_returns_basic_rec(self, mock_news):
        mock_news.get_code_stats = MagicMock(return_value={
            "summary": {"total_tokens": 50_000, "total_days": 5, "total_code": 100}
        })
        result = svc._stats_context()
        assert len(result) == 1
        assert result[0]["title"] == "代码统计已就绪"
        assert result[0]["priority"] == "low"
        assert "5 天" in result[0]["detail"]

    def test_high_tokens_returns_warning_rec(self, mock_news):
        mock_news.get_code_stats = MagicMock(return_value={
            "summary": {"total_tokens": 600_000, "total_days": 7, "total_code": 5000}
        })
        result = svc._stats_context()
        assert len(result) == 1
        assert "Token 消耗" in result[0]["title"]
        assert "600K" in result[0]["title"]
        assert result[0]["priority"] == "low"

    def test_handles_empty_summary(self, mock_news):
        mock_news.get_code_stats = MagicMock(return_value={})
        result = svc._stats_context()
        # total_tokens 不存在 → 0 → 走 basic 分支
        assert result[0]["title"] == "代码统计已就绪"


# ─── get_recommendations（顶层）─────────────────────────────

class TestGetRecommendations:
    async def test_combines_all_sources_and_dedupes(
        self, mock_db, mock_obsidian, mock_news, fake_user
    ):
        from tests.conftest import FakeResult

        # weak_spots: 1 个 interview 但有 records → ["Memory"]
        interview = SimpleNamespace(id="iv-1", status="completed")
        records = [SimpleNamespace(blind_spots=["Memory"])]
        # interview_recs: < 3 completed → "继续练习"
        interview_for_recs = SimpleNamespace(id="iv-1", status="completed")

        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[interview]),    # _get_weak_spots: Interview query
            FakeResult(items=records),        # _get_weak_spots: QuestionRecord query
            FakeResult(items=[interview_for_recs]),  # _interview_recs: Interview query
        ])
        mock_obsidian.search.return_value = [
            {"name": "memory.md", "path": "/notes/memory.md"},
        ]

        result = await svc.get_recommendations(fake_user, mock_db)

        # 至少有 knowledge + interview + stats 3 条
        types = {r["type"] for r in result}
        assert "knowledge" in types
        assert "interview" in types
        assert "stats" in types
        assert len(result) <= 6  # 截到 6 条

    async def test_limits_to_six_recommendations(
        self, mock_db, mock_obsidian, mock_news, fake_user
    ):
        from tests.conftest import FakeResult

        # 让 weak_spots 返回 5 个不同主题
        interview = SimpleNamespace(id="iv-1", status="completed")
        records = [
            SimpleNamespace(blind_spots=[f"spot-{i}"]) for i in range(5)
        ]
        # interview_recs 走 <3 completed 分支
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[interview]),
            FakeResult(items=records),
            FakeResult(items=[SimpleNamespace(status="completed")]),
        ])
        # obsidian 返回 5 个不同笔记
        mock_obsidian.search.return_value = [
            {"name": f"note-{i}.md", "path": f"/notes/note-{i}.md"} for i in range(5)
        ]

        result = await svc.get_recommendations(fake_user, mock_db)
        assert len(result) <= 6

    async def test_dedupes_by_title(
        self, mock_db, mock_obsidian, mock_news, fake_user
    ):
        """如果两个分支产生相同 title，应去重"""
        from tests.conftest import FakeResult

        interview = SimpleNamespace(id="iv-1", status="completed")
        records = [SimpleNamespace(blind_spots=["x"])]
        mock_db.execute = AsyncMock(side_effect=[
            FakeResult(items=[interview]),
            FakeResult(items=records),
            FakeResult(items=[SimpleNamespace(status="completed")]),
        ])

        result = await svc.get_recommendations(fake_user, mock_db)
        titles = [r["title"] for r in result]
        assert len(titles) == len(set(titles))  # 无重复 title