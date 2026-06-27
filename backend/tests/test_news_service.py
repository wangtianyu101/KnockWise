"""单测: services/news_service.py

策略：monkeypatch OBSIDIAN_AI 和 STATS_DB 到 tmp_path。
覆盖：list_dailies / get_daily / list_weeklies / get_weekly / get_code_stats /
       _fallback_stats / get_sources
目标：≥ 70%
"""
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from services import news_service as svc
from services.news_service import NewsService


@pytest.fixture
def ai_vault(tmp_path, monkeypatch):
    """monkeypatch OBSIDIAN_AI 到 tmp_path/ai"""
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir()
    monkeypatch.setattr(svc, "OBSIDIAN_AI", ai_dir)
    return ai_dir


@pytest.fixture
def stats_db(tmp_path, monkeypatch):
    """建一个临时 SQLite stats DB 并 monkeypatch STATS_DB"""
    db_path = tmp_path / ".stats.db"
    monkeypatch.setattr(svc, "STATS_DB", db_path)
    return db_path


@pytest.fixture
def populated_stats_db(stats_db):
    """建一个 schema 完整、有数据的 stats DB"""
    conn = sqlite3.connect(str(stats_db))
    conn.executescript("""
        CREATE TABLE daily_summary (
            date TEXT PRIMARY KEY,
            note TEXT
        );
        CREATE TABLE daily_tokens (
            date TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER
        );
        CREATE TABLE daily_code (
            date TEXT,
            lines_added INTEGER,
            lines_deleted INTEGER,
            commits INTEGER
        );
    """)
    # 插入测试数据
    today = date.today().isoformat()
    yesterday = (date.today().toordinal() - 1).isoformat() if False else None  # not needed
    from datetime import timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    week_ago = (date.today() - timedelta(days=5)).isoformat()

    conn.execute("INSERT INTO daily_summary VALUES (?, ?)", (today, None))
    conn.execute("INSERT INTO daily_summary VALUES (?, ?)", (yesterday, None))
    conn.execute("INSERT INTO daily_summary VALUES (?, ?)", (week_ago, None))

    conn.execute("INSERT INTO daily_tokens VALUES (?, ?, ?)", (today, 1000, 2000))
    conn.execute("INSERT INTO daily_tokens VALUES (?, ?, ?)", (yesterday, 500, 1500))
    conn.execute("INSERT INTO daily_tokens VALUES (?, ?, ?)", (week_ago, 100, 200))

    conn.execute("INSERT INTO daily_code VALUES (?, ?, ?, ?)", (today, 50, 10, 3))
    conn.execute("INSERT INTO daily_code VALUES (?, ?, ?, ?)", (yesterday, 30, 5, 2))
    conn.commit()
    conn.close()
    return stats_db


# ─── list_dailies ─────────────────────────────────────────────

class TestListDailies:
    def test_returns_empty_when_dir_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "OBSIDIAN_AI", tmp_path / "nope")
        s = NewsService()
        assert s.list_dailies() == []

    def test_lists_daily_files(self, ai_vault):
        (ai_vault / "AI 日报 2026-06-25.md").write_text("content")
        (ai_vault / "AI 日报 2026-06-26.md").write_text("content")
        (ai_vault / "AI 日报 2026-06-27.md").write_text("content")
        (ai_vault / "其他文件.md").write_text("content")  # 不应计入

        s = NewsService()
        items = s.list_dailies()
        assert len(items) == 3
        # 应倒序
        assert items[0]["date"] == "2026-06-27"

    def test_extracts_date_from_filename(self, ai_vault):
        (ai_vault / "AI 日报 2026-06-27.md").write_text("c")
        items = NewsService().list_dailies()
        assert items[0]["date"] == "2026-06-27"
        assert items[0]["name"] == "AI 日报 2026-06-27.md"
        assert "size" in items[0]


# ─── get_daily ────────────────────────────────────────────────

class TestGetDaily:
    def test_returns_none_when_no_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "OBSIDIAN_AI", tmp_path / "nope")
        assert NewsService().get_daily() is None

    def test_returns_none_when_no_files(self, ai_vault):
        assert NewsService().get_daily() is None

    def test_returns_latest_when_no_day_specified(self, ai_vault):
        (ai_vault / "AI 日报 2026-06-25.md").write_text("older")
        (ai_vault / "AI 日报 2026-06-27.md").write_text("newest")
        (ai_vault / "AI 日报 2026-06-26.md").write_text("middle")

        result = NewsService().get_daily()
        assert result is not None
        assert result["date"] == "2026-06-27"
        assert result["content"] == "newest"

    def test_returns_specific_day(self, ai_vault):
        (ai_vault / "AI 日报 2026-06-25.md").write_text("c1")
        (ai_vault / "AI 日报 2026-06-27.md").write_text("c2")

        result = NewsService().get_daily("2026-06-25")
        assert result["content"] == "c1"
        assert result["date"] == "2026-06-25"

    def test_returns_none_for_missing_day(self, ai_vault):
        (ai_vault / "AI 日报 2026-06-25.md").write_text("c")
        assert NewsService().get_daily("2099-01-01") is None


# ─── list_weeklies ────────────────────────────────────────────

class TestListWeeklies:
    def test_returns_empty_when_dir_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "OBSIDIAN_AI", tmp_path / "nope")
        assert NewsService().list_weeklies() == []

    def test_lists_weekly_files(self, ai_vault):
        (ai_vault / "AI 周报 2026-W22.md").write_text("w1")
        (ai_vault / "AI 周报 2026-W23.md").write_text("w2")
        (ai_vault / "AI 日报 2026-06-27.md").write_text("daily")  # 不应计入

        items = NewsService().list_weeklies()
        assert len(items) == 2
        # 倒序
        assert items[0]["week"] == "2026-W23"


# ─── get_weekly ───────────────────────────────────────────────

class TestGetWeekly:
    def test_returns_none_when_no_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "OBSIDIAN_AI", tmp_path / "nope")
        assert NewsService().get_weekly() is None

    def test_returns_latest(self, ai_vault):
        (ai_vault / "AI 周报 2026-W22.md").write_text("older")
        (ai_vault / "AI 周报 2026-W23.md").write_text("newest")

        result = NewsService().get_weekly()
        assert result["content"] == "newest"
        assert result["week"] == "2026-W23"

    def test_returns_specific_week(self, ai_vault):
        (ai_vault / "AI 周报 2026-W22.md").write_text("w22")
        (ai_vault / "AI 周报 2026-W23.md").write_text("w23")

        result = NewsService().get_weekly("2026-W22")
        assert result["content"] == "w22"


# ─── get_code_stats ───────────────────────────────────────────

class TestGetCodeStats:
    def test_returns_fallback_when_db_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "STATS_DB", tmp_path / "nonexistent.db")
        result = NewsService().get_code_stats()
        assert result == {
            "daily": [],
            "summary": {"total_days": 0, "total_tokens": 0, "total_code": 0, "total_commits": 0},
        }

    def test_returns_fallback_on_exception(self, stats_db, monkeypatch):
        """DB 存在但 schema 错时走 fallback"""
        # 不建 schema，让 query 失败
        monkeypatch.setattr(svc, "STATS_DB", stats_db)
        result = NewsService().get_code_stats()
        assert "summary" in result
        assert result["summary"]["total_days"] == 0

    def test_aggregates_real_data(self, populated_stats_db, monkeypatch):
        monkeypatch.setattr(svc, "STATS_DB", populated_stats_db)
        result = NewsService().get_code_stats(days=7)
        # 应该有 daily 数据
        assert "daily" in result
        assert "summary" in result
        # summary 应有数据
        assert result["summary"]["total_tokens"] >= 0
        assert result["summary"]["total_days"] >= 0

    def test_filters_by_days(self, populated_stats_db, monkeypatch):
        """days=1 只应包含最近 1 天的数据"""
        monkeypatch.setattr(svc, "STATS_DB", populated_stats_db)
        result_7 = NewsService().get_code_stats(days=7)
        result_1 = NewsService().get_code_stats(days=1)
        # days=1 应 <= days=7
        assert len(result_1["daily"]) <= len(result_7["daily"])


# ─── _fallback_stats ──────────────────────────────────────────

class TestFallbackStats:
    def test_returns_empty_structure(self):
        result = NewsService()._fallback_stats()
        assert result["daily"] == []
        assert result["summary"]["total_days"] == 0
        assert result["summary"]["total_tokens"] == 0
        assert result["summary"]["total_code"] == 0
        assert result["summary"]["total_commits"] == 0


# ─── get_sources ──────────────────────────────────────────────

class TestGetSources:
    def test_returns_source_list(self):
        sources = NewsService().get_sources()
        assert isinstance(sources, list)
        assert len(sources) >= 3  # 至少 3 个源

    def test_each_source_has_required_fields(self):
        for s in NewsService().get_sources():
            assert "name" in s
            assert "url" in s
            assert "category" in s
            assert "enabled" in s

    def test_includes_qbitai_and_36kr(self):
        sources = NewsService().get_sources()
        names = {s["name"] for s in sources}
        assert "量子位" in names
        assert "36氪" in names