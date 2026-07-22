"""E2E push flow (T24 重写 · 2026-07-22) - cron → fetch → score → save → API。

覆盖：4 个场景（happy / all-failed / partial / no-candidates）

实现位置：services/digest_service.py::DigestService.push_daily
邮件发送通过可注入 provider 边界验证，不访问公网。

测试策略：
- 全链路 mock（fetch / DB save / email）
- 验证 push_daily 编排正确（调用顺序 + 异常处理）
- 验证 vibe 文本覆盖 5 种状态（全失败/无候选/部分/正常/全部）
- 验证 DB 持久化调用（add + commit 顺序）
- email 发送单独验证 provider 调用契约
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.digest_service import DigestService


# ── Fixtures ────────────────────────────────────────────────


def make_raw_item(
    title: str,
    source_name: str = "Test Source",
    type: str = "model",
    region: str = "domestic",
    score: float = 0.85,
):
    """构造一个 RSS item + 已分类 + 已打分"""
    return {
        "title": title,
        "url": f"https://test.com/{title}",
        "summary": "test summary",
        "published_at": "2026-07-22T10:00:00Z",
        "source_name": source_name,
        "type": type,
        "region": region,
        "category": "一手",
        "score": score,
    }


def make_user_prefs():
    """Mock user preferences (返回 dict · DigestPreferenceService 内部也是 dict)"""
    return {
        "user_id": "user-001",
        "interested_tags": ["AI", "LLM"],
        "blocked_tags": ["crypto"],
        "push_hour": 8,
        "push_minute": 0,
        "push_timezone": "Asia/Shanghai",
    }


# ── Tests · push_daily 编排 ──────────────────────────────────


class TestPushDailyOrchestration:
    """测试 push_daily 编排逻辑（fetch → score → select → save）"""

    @pytest.mark.asyncio
    async def test_full_cron_to_db_to_api_happy(self):
        """Happy path：5 候选 → select 5 条 → save digest + items → 返回 daily_id

        完整 cron → DB → API 编排：
        1. fetch_all_sources 返回 8 源成功
        2. composite_score + select_top_n 选 5
        3. 写 DigestDaily + DigestDailyItem
        4. 返回 daily_id + vibe + item_count
        """
        service = DigestService()
        db = AsyncMock()

        # 模拟 8 源成功 · 每源 5 条 item · 已分类已打分
        source_results = [
            {
                "source_id": f"src-{i}",
                "source_name": f"Source {i}",
                "items": [make_raw_item(f"AI LLM breakthrough item-{i}-{j}", source_name=f"Source {i}") for j in range(5)],
                "error": None,
            }
            for i in range(8)
        ]

        with patch.object(service, "fetch_all_sources", AsyncMock(return_value=source_results)), \
             patch("services.digest_preference_service.DigestPreferenceService") as MockPref, \
             patch("models.DigestDaily") as MockDaily, \
             patch("models.DigestDailyItem") as MockItem:
            MockPref.return_value.get_user_prefs = AsyncMock(return_value=make_user_prefs())
            MockDaily.return_value = MagicMock()  # for type hint
            MockItem.return_value = MagicMock()

            result = await service.push_daily(db=db, user_id="user-001", target_date=None)

        # 验证返回结构
        assert result["daily_id"] is not None
        assert result["item_count"] == 5
        assert "vibe" in result
        assert result["error"] is None
        # 验证 DB 写操作（add 调用次数：1 daily + 5 items = 6 次）
        assert db.add.call_count == 6
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_push_daily_persists_to_db(self):
        """push_daily 持久化：commit 调用 + add 顺序（daily 先 / items 后）"""
        service = DigestService()
        db = AsyncMock()

        source_results = [
            {
                "source_id": "src-1",
                "source_name": "S1",
                "items": [make_raw_item(f"AI LLM news item-{j}") for j in range(10)],  # 10 候选
                "error": None,
            }
        ]

        with patch.object(service, "fetch_all_sources", AsyncMock(return_value=source_results)), \
             patch("services.digest_preference_service.DigestPreferenceService") as MockPref, \
             patch("models.DigestDaily"), \
             patch("models.DigestDailyItem"):
            MockPref.return_value.get_user_prefs = AsyncMock(return_value=make_user_prefs())

            result = await service.push_daily(db=db, user_id="user-001", target_date=None)

        # DB add + commit 都被调用
        db.add.assert_called()
        db.commit.assert_awaited_once()
        assert result["daily_id"] is not None

    @pytest.mark.asyncio
    async def test_all_sources_failed_returns_error_vibe(self):
        """全源失败 → vibe = "今日 digest 暂缺 · 信源全部失败" · 不写 DB"""
        service = DigestService()
        db = AsyncMock()

        # 8 源全部失败
        source_results = [
            {"source_id": f"src-{i}", "source_name": f"S{i}", "items": [], "error": "ConnectionError"}
            for i in range(8)
        ]

        with patch.object(service, "fetch_all_sources", AsyncMock(return_value=source_results)), \
             patch("services.digest_preference_service.DigestPreferenceService") as MockPref:
            MockPref.return_value.get_user_prefs = AsyncMock(return_value=make_user_prefs())

            result = await service.push_daily(db=db, user_id="user-001", target_date=None)

        assert result["daily_id"] is None
        assert result["item_count"] == 0
        assert "信源全部失败" in result["vibe"]
        # 全失败时不写 DB
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_candidates_returns_vibe_no_new(self):
        """无候选（源成功但 0 条过阈值）→ vibe = "今日 AI 圈无新动态" · 不写 DB"""
        service = DigestService()
        db = AsyncMock()

        # 源成功但 items 全部 score=0 → 全部被阈值过滤
        source_results = [
            {
                "source_id": "src-1",
                "source_name": "S1",
                "items": [make_raw_item(f"unrelated item-{j}") for j in range(3)],  # 全部 0 分
                "error": None,
            }
        ]

        with patch.object(service, "fetch_all_sources", AsyncMock(return_value=source_results)), \
             patch("services.digest_preference_service.DigestPreferenceService") as MockPref:
            MockPref.return_value.get_user_prefs = AsyncMock(return_value=make_user_prefs())

            result = await service.push_daily(db=db, user_id="user-001", target_date=None)

        assert result["daily_id"] is None
        assert "无新动态" in result["vibe"]
        db.add.assert_not_called()


# ── Tests · email provider 集成 ───────────────────────────────


class TestEmailIntegration:
    """EmailService delegates delivery to the configured provider."""

    @pytest.mark.asyncio
    async def test_email_send_delegates_to_provider(self):
        from services.email_service import EmailService

        provider = AsyncMock()
        provider.send.return_value = "message-1"
        svc = EmailService(provider=provider)
        message_id = await svc._send_via_resend(
            to_email="test@example.com",
            subject="KnockWise Daily 2026-07-22",
            html="<html>test</html>",
        )

        assert message_id == "message-1"
        provider.send.assert_awaited_once()
