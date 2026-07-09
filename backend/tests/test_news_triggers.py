"""单测: news 触发 / 历史端点（V1 closure 🟡 #7）"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from core.dependencies import get_current_user, get_db
from tests.conftest import FakeResult


class TestNewsTriggerAndHistory:
    """POST /trigger/daily + POST /trigger/weekly + GET /history（V1 closure 🟡 #7）。"""

    def setup_method(self):
        app.dependency_overrides.clear()

    def test_trigger_daily_writes_marker(self, tmp_path, monkeypatch):
        """POST /trigger/daily → 写 marker 文件 + 返回状态。"""
        from api import news as news_api

        monkeypatch.setattr(news_api, "TRIGGER_LOG_DIR", tmp_path)
        user = SimpleNamespace(id="u-test")
        app.dependency_overrides[get_current_user] = lambda: user

        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.post("/api/news/trigger/daily")
        assert response.status_code == 200
        body = response.json()
        assert body["queued"] is True
        assert "marker_path" in body
        assert "queued_at" in body
        # marker 文件确实写入了
        markers = list(tmp_path.glob("daily_*.trigger"))
        assert len(markers) == 1

    def test_trigger_weekly_writes_marker(self, tmp_path, monkeypatch):
        from api import news as news_api
        monkeypatch.setattr(news_api, "TRIGGER_LOG_DIR", tmp_path)

        user = SimpleNamespace(id="u-test")
        app.dependency_overrides[get_current_user] = lambda: user

        client = TestClient(app)
        response = client.post("/api/news/trigger/weekly")
        assert response.status_code == 200
        body = response.json()
        assert body["queued"] is True

    def test_history_returns_combined_list(self):
        """GET /history → 日报+周报聚合按日期降序。"""
        user = SimpleNamespace(id="u-1")
        app.dependency_overrides[get_current_user] = lambda: user
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        # patch service.list_dailies + list_weeklies
        from unittest.mock import patch

        dailies = [
            {"date": "2026-06-28", "name": "AI 日报 2026-06-28.md", "size": 1024},
            {"date": "2026-06-27", "name": "AI 日报 2026-06-27.md", "size": 900},
        ]
        weeklies = [
            {"week": "2026-W26", "name": "AI 周报 2026-W26.md", "size": 2048},
        ]

        with patch.object(
            __import__('services.news_service', fromlist=['news_service']).news_service,
            'list_dailies', return_value=dailies,
        ), patch.object(
            __import__('services.news_service', fromlist=['news_service']).news_service,
            'list_weeklies', return_value=weeklies,
        ):
            client = TestClient(app)
            response = client.get("/api/news/history?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert data["total"] == 3
            # 按 name 降序
            names = [item["name"] for item in data["items"]]
            assert names == sorted(names, reverse=True)
