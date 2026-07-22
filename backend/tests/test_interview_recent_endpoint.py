"""
/api/interviews/recent 端点测试 — V3.8 P3a (V1 mock_db 风格)

9 测试：
- test_recent_empty
- test_recent_one
- test_recent_three
- test_recent_truncate
- test_recent_excludes_in_progress
- test_recent_excludes_no_score
- test_recent_user_isolation
- test_recent_limit_validation
- test_recent_unauthenticated

策略：mock_db + dependency_overrides（V1 风格）
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from uuid import uuid4
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from main import app
from core.dependencies import get_current_user


def _user(user_id: str | None = None):
    return SimpleNamespace(id=user_id or str(uuid4()))


def _interview(
    user_id: str,
    status: str = "completed",
    overall_score: float | None = 78.5,
    round: str = "字节·后端",
    started_at: datetime | None = None,
) -> dict:
    """Mock Interview 返回 dict（Pydantic v2 需要 dict 或 BaseModel 实例）"""
    return {
        "id": str(uuid4()),
        "round": round,
        "style": "tech",
        "status": status,
        "total_questions": 8,
        "overall_score": overall_score,
        "radar_data": {
            "algorithm": 78, "system_design": 75,
            "network": 65, "frontend": 50, "ai": 40,
        },
        "started_at": started_at or datetime.now(timezone.utc),
        "ended_at": None,
    }


class TestRecentInterviewsEndpoint:
    """V3.8 新增 /api/interviews/recent"""

    def test_recent_empty(self):
        """#1: 0 面试 → 空数组"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=[])) as MockSvc:
                client = TestClient(app)
                response = client.get("/api/interviews/recent")
                assert response.status_code == 200
                data = response.json()
                assert data == {"items": [], "total": 0}
                MockSvc.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_recent_one(self):
        """#2: 1 条 → total=1"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            iv = _interview(user.id, overall_score=78.5, round="字节·后端")
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=[iv])):
                client = TestClient(app)
                response = client.get("/api/interviews/recent")
                assert response.status_code == 200
                data = response.json()
                assert data["total"] == 1
                assert data["items"][0]["overall_score"] == 78.5
                assert data["items"][0]["round"] == "字节·后端"
        finally:
            app.dependency_overrides.clear()

    def test_recent_three(self):
        """#3: 3 条 → total=3 + 倒序"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            interviews = [
                _interview(user.id, overall_score=score, started_at=datetime(2026, 7, 8 - i, tzinfo=timezone.utc))
                for i, score in enumerate([78.5, 68.0, 62.0])
            ]
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=interviews)):
                client = TestClient(app)
                response = client.get("/api/interviews/recent")
                data = response.json()
                assert data["total"] == 3
                assert data["items"][0]["overall_score"] == 78.5
                assert data["items"][1]["overall_score"] == 68.0
                assert data["items"][2]["overall_score"] == 62.0
        finally:
            app.dependency_overrides.clear()

    def test_recent_truncate(self):
        """#4: 5 条 + limit=3 → 返回 3 条"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            interviews = [_interview(user.id, overall_score=70.0 + i) for i in range(5)]
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=interviews[:3])):
                client = TestClient(app)
                response = client.get("/api/interviews/recent?limit=3")
                data = response.json()
                assert len(data["items"]) == 3
                assert data["total"] == 3
        finally:
            app.dependency_overrides.clear()

    def test_recent_excludes_in_progress(self):
        """#5: service 负责过滤 in_progress（mock 返回已过滤结果）"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            # 假设 service 已过滤 in_progress，返回 2 条 completed
            filtered = [
                _interview(user.id, overall_score=78.0),
                _interview(user.id, overall_score=68.0),
            ]
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=filtered)):
                client = TestClient(app)
                response = client.get("/api/interviews/recent")
                data = response.json()
                assert data["total"] == 2
        finally:
            app.dependency_overrides.clear()

    def test_recent_excludes_no_score(self):
        """#6: service 过滤 overall_score IS NULL"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            filtered = [_interview(user.id, overall_score=78.0)]
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=filtered)):
                client = TestClient(app)
                response = client.get("/api/interviews/recent")
                data = response.json()
                assert data["total"] == 1
                assert data["items"][0]["overall_score"] == 78.0
        finally:
            app.dependency_overrides.clear()

    def test_recent_user_isolation(self):
        """#7: service 接收 user.id 参数（不同用户不同结果）"""
        user_a = _user()
        user_b = _user()
        app.dependency_overrides[get_current_user] = lambda: user_a
        try:
            # service 接收 user.id 返回对应用户的数据
            async def mock_service(db, user_id, limit=3):
                if user_id == user_a.id:
                    return [_interview(user_id, overall_score=70.0) for _ in range(3)]
                elif user_id == user_b.id:
                    return [_interview(user_id, overall_score=80.0) for _ in range(3)]
                return []
            with patch("api.interview.list_recent_interviews", side_effect=mock_service):
                client = TestClient(app)
                response = client.get("/api/interviews/recent")
                data = response.json()
                assert data["total"] == 3
                assert all(item["overall_score"] == 70.0 for item in data["items"])
        finally:
            app.dependency_overrides.clear()

    def test_recent_limit_validation(self):
        """#8: limit=0 / limit=11 → 422 (FastAPI 自动校验)"""
        user = _user()
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            with patch("api.interview.list_recent_interviews", new=AsyncMock(return_value=[])):
                client = TestClient(app)
                for bad_limit in ["0", "11", "100"]:
                    response = client.get(f"/api/interviews/recent?limit={bad_limit}")
                    assert response.status_code == 422, f"limit={bad_limit} 应返回 422"
        finally:
            app.dependency_overrides.clear()

    def test_recent_unauthenticated(self):
        """#9: 无 token → 401"""
        # 不 override get_current_user
        client = TestClient(app)
        response = client.get("/api/interviews/recent")
        assert response.status_code in (401, 403)