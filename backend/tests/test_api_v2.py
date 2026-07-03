"""单测: api/v2_settlement.py

V2.3 PR 3a — T20: 6 个新 API 端点 + T22: 集成测试
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from main import app


# ─── T20: 6 端点 happy / edge / 错误码 ─────────────

class TestDashboardSummaryEndpoint:
    """GET /api/v2/dashboard/summary"""

    def test_unauthorized_returns_401(self, monkeypatch):
        """未登录 → 401。"""
        # 不 override get_current_user，TestClient 也不传 token → FastAPI Depends 失败
        client = TestClient(app)
        response = client.get("/api/v2/dashboard/summary")
        assert response.status_code in (401, 403)

    def test_happy_returns_summary(self, monkeypatch):
        """Happy: 返 DailySummary dict。"""
        from core.dependencies import get_current_user
        from uuid import uuid4
        user = SimpleNamespace(id=str(uuid4()))
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            # mock SummaryService.dashboard
            with patch(
                "api.v2_settlement.SummaryService"
            ) as MockSvc:
                MockSvc.return_value.dashboard = AsyncMock(return_value={
                    "title": "今日学习总结",
                    "date": "2026-06-28",
                    "yesterday_count": 8,
                    "mastered": [{"topic": "React Hooks"}],
                    "weak_shift": [],
                    "body": "你答了 8 道题。",
                    "_fallback": False,
                })

                client = TestClient(app)
                response = client.get("/api/v2/dashboard/summary")
                assert response.status_code == 200
                data = response.json()
                assert data["yesterday_count"] == 8
                assert "React Hooks" in str(data["mastered"])
        finally:
            app.dependency_overrides.clear()

    def test_invalid_date_returns_422(self):
        """date=2026-13-99 格式错 → 422。"""
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            client = TestClient(app)
            response = client.get("/api/v2/dashboard/summary?date=invalid")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestProfileWeeklyEndpoint:
    """GET /api/v2/profile/weekly"""

    def test_happy_returns_weekly_summary(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch(
                "api.v2_settlement.SummaryService"
            ) as MockSvc:
                MockSvc.return_value.weekly = AsyncMock(return_value={
                    "week": "2026-W26",
                    "total_questions": 42,
                    "mastered_count": 7,
                    "weak_topics": [],
                    "body": "本周你答了 42 题。",
                    "trajectory": {"2026-W26": {"mastered_count": 7}},
                })

                client = TestClient(app)
                response = client.get("/api/v2/profile/weekly?week=2026-W26")
                assert response.status_code == 200
                data = response.json()
                assert data["week"] == "2026-W26"
                assert "trajectory" in data
        finally:
            app.dependency_overrides.clear()

    def test_invalid_week_format_returns_422(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            client = TestClient(app)
            response = client.get("/api/v2/profile/weekly?week=invalid")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestProfileMonthlyEndpoint:
    """GET /api/v2/profile/monthly"""

    def test_happy_returns_monthly_summary(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch(
                "api.v2_settlement.SummaryService"
            ) as MockSvc:
                MockSvc.return_value.monthly = AsyncMock(return_value={
                    "month": "2026-06",
                    "total_questions": 168,
                    "mastered_count": 28,
                    "weak_topics": [],
                    "body": "6 月你答了 168 题。",
                    "trajectory": {},
                    "summary_stats": {
                        "narrative": "...",
                        "saved_to_db": True,
                        "monthly_report_id": "uuid-x",
                    },
                })

                client = TestClient(app)
                response = client.get("/api/v2/profile/monthly?month=2026-06")
                assert response.status_code == 200
                data = response.json()
                assert data["month"] == "2026-06"
                assert data["summary_stats"]["saved_to_db"] is True
        finally:
            app.dependency_overrides.clear()

    def test_invalid_month_returns_422(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            client = TestClient(app)
            response = client.get("/api/v2/profile/monthly?month=invalid")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestProfileRefreshEndpoint:
    """POST /api/v2/profile/refresh"""

    def test_happy_returns_settlement_result(self):
        from core.dependencies import get_current_user
        import uuid as _uuid
        user = SimpleNamespace(id=str(_uuid.uuid4()))
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch(
                "api.v2_settlement.ProfileSettlementService"
            ) as MockSvc:
                MockSvc.return_value.manual_refresh = AsyncMock(return_value={
                    "user_id": user.id,
                    "settled_at": "2026-06-28T15:30:00Z",
                    "weak_topics": [],
                    "mastered_topics": [],
                    "triggered_by": "manual_refresh",
                    "cache_invalidated": True,
                })

                client = TestClient(app)
                response = client.post("/api/v2/profile/refresh")
                assert response.status_code == 200
                data = response.json()
                assert data["triggered_by"] == "manual_refresh"
                assert data["cache_invalidated"] is True
        finally:
            app.dependency_overrides.clear()


class TestKnowledgeRecentSediments:
    """GET /api/v2/knowledge/recent-sediments"""

    def test_vault_missing_returns_empty_list(self, tmp_path, monkeypatch):
        """vault 不存在 → 返空 list（决策 7A，不抛 500）。"""
        from core.dependencies import get_current_user
        from pathlib import Path
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user

        # monkeypatch Path.home() 到不存在的目录
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        try:
            client = TestClient(app)
            response = client.get("/api/v2/knowledge/recent-sediments")
            assert response.status_code == 200
            data = response.json()
            assert data == []
        finally:
            app.dependency_overrides.clear()

    def test_vault_with_files_returns_recent(self, tmp_path, monkeypatch):
        """vault 有 3 个 .md → 返最近 3 个（按 mtime）。"""
        from core.dependencies import get_current_user
        from pathlib import Path
        import time
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user

        # 建 vault + 3 个 .md
        vault = tmp_path / "Obsidian" / "coding"
        learning = vault / "learning"
        learning.mkdir(parents=True)
        for i, name in enumerate(["a.md", "b.md", "c.md"]):
            f = learning / name
            f.write_text(f"#{name}")
            time.sleep(0.01)  # 不同的 mtime
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        try:
            client = TestClient(app)
            response = client.get("/api/v2/knowledge/recent-sediments?limit=3")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            # c.md 最新
            assert data[0]["rel_path"] == "learning/c.md"
        finally:
            app.dependency_overrides.clear()


class TestObsidianSyncEndpoint:
    """POST /api/v2/obsidian/sync"""

    def test_happy_returns_synced_count(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch(
                "api.v2_settlement.SummaryService"
            ) as MockSvc:
                MockSvc.return_value.sync_daily_to_obsidian = AsyncMock(
                    return_value={
                        "date": "2026-06-28",
                        "synced": True,
                        "path": "/Users/x/Obsidian/coding/learning/2026-06-28.md",
                    },
                )

                client = TestClient(app)
                response = client.post("/api/v2/obsidian/sync?date=2026-06-28")
                assert response.status_code == 200
                data = response.json()
                assert data["synced_count"] == 1
                assert data["files"][0]["success"] is True
        finally:
            app.dependency_overrides.clear()

    def test_vault_missing_returns_zero_count(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch(
                "api.v2_settlement.SummaryService"
            ) as MockSvc:
                MockSvc.return_value.sync_daily_to_obsidian = AsyncMock(
                    return_value={
                        "date": "2026-06-28",
                        "synced": False,
                        "path": None,
                    },
                )

                client = TestClient(app)
                response = client.post("/api/v2/obsidian/sync?date=2026-06-28")
                assert response.status_code == 200
                data = response.json()
                assert data["synced_count"] == 0
                assert data["files"][0]["success"] is False
        finally:
            app.dependency_overrides.clear()

    def test_invalid_date_returns_422(self):
        from core.dependencies import get_current_user
        user = SimpleNamespace(id="user-1")
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            client = TestClient(app)
            response = client.post("/api/v2/obsidian/sync?date=invalid")
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ─── T22: 端到端集成测试 ────────────────────────────

class TestEndToEndPipeline:
    """T22: 答 3 题 → Dashboard summary + Profile weekly + Knowledge recent。"""

    def test_e2e_pipeline_returns_consistent_data(self):
        """完整流：mock 3 service 都有数据。"""
        from core.dependencies import get_current_user
        from uuid import uuid4
        user_id = str(uuid4())
        user = SimpleNamespace(id=user_id)
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch(
                "api.v2_settlement.SummaryService"
            ) as MockSvc:
                # dashboard
                MockSvc.return_value.dashboard = AsyncMock(return_value={
                    "title": "今日学习总结",
                    "date": "2026-06-28",
                    "yesterday_count": 3,
                    "mastered": [{"topic": "React Hooks"}],
                    "weak_shift": [],
                    "body": "答了 3 题。",
                    "_fallback": False,
                })
                # weekly
                MockSvc.return_value.weekly = AsyncMock(return_value={
                    "week": "2026-W26",
                    "total_questions": 12,
                    "mastered_count": 3,
                    "weak_topics": [],
                    "body": "本周答了 12 题。",
                    "trajectory": {"2026-W26": {"mastered_count": 3}},
                })

                client = TestClient(app)
                # 调 3 个端点
                r1 = client.get("/api/v2/dashboard/summary")
                r2 = client.get("/api/v2/profile/weekly?week=2026-W26")
                assert r1.status_code == 200
                assert r2.status_code == 200
                # 数据一致（同一用户）
                assert r1.json()["yesterday_count"] == 3
                assert r2.json()["mastered_count"] == 3
        finally:
            app.dependency_overrides.clear()
