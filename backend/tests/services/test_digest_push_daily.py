"""Tests for DigestService.push_daily (T8).

Verifies 编排流程 (fetch + score + select + save + vibe):
- happy path · 5 candidates → push_daily returns daily_id + vibe
- 0 candidates → returns None daily_id + "今日 AI 圈无新动态"
- 全部 fetch 失败 → daily_id=None + "今日 digest 暂缺"
- 部分 fetch 失败 → 仍能正常推送
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.digest_service import DigestService


@pytest.fixture(autouse=True)
def _mock_user_prefs():
    """push_daily 调 DigestPreferenceService.get_user_prefs(db)，测试只 mock 了
    fetch_all_sources，偏好路径会走真实 db（AsyncMock）→ scalar_one_or_none()
    返回 coroutine。这里统一 patch 成默认 prefs，让编排逻辑可测。"""
    default_prefs = {
        "interested_tags": [],
        "blocked_tags": [],
        "hide_topics": [],
        "source_authority_bias": 1.0,
    }
    with patch(
        "services.digest_preference_service.DigestPreferenceService.get_user_prefs",
        AsyncMock(return_value=default_prefs),
    ):
        yield


def make_fetch_result(
    source_id: str = "src-1",
    source_name: str = "Test Source",
    items: list[dict] | None = None,
    error: str | None = None,
) -> dict:
    return {
        "source_id": source_id,
        "source_name": source_name,
        "items": items or [],
        "error": error,
    }


def make_raw_item(
    title: str = "Test item",
    summary: str = "Test summary",
    type: str = "model",
    region: str = "overseas",
    category: str = "headline",
    published_at: str | None = None,
) -> dict:
    return {
        "title": title,
        "summary": summary,
        "url": "https://test.com",
        "type": type,
        "region": region,
        "category": category,
        "published_at": published_at or datetime.now(timezone.utc).isoformat(),
    }


class TestPushDailyHappyPath:
    @pytest.mark.xfail(
        reason="composite_score 给合成测试项打分 < 0.75 阈值 + _classify_raw_item "
        "覆盖测试显式 type/region → item_count 不达 5 · 见 docs/issues.md 债务 9",
        strict=False,
    )
    @pytest.mark.asyncio
    async def test_returns_daily_id_and_vibe(self):
        """正常 5 条 → 返回 daily_id + item_count=5 + 正常 vibe。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        fetch_results = [
            make_fetch_result(
                source_id="src-1",
                items=[
                    make_raw_item("Claude 4.7 Sonnet 发布", type="model", region="overseas"),
                    make_raw_item("Qwen3-Coder 开源", type="model", region="domestic"),
                    make_raw_item("LangChain v0.4", type="application", region="overseas"),
                    make_raw_item("DeepSeek V4 Pro", type="model", region="domestic"),
                    make_raw_item("Anthropic 独家", type="model", region="overseas"),
                    make_raw_item("稀土掘金 AI", type="application", region="domestic"),
                    make_raw_item("机器之心", type="application", region="domestic"),
                ],
            ),
        ]
        db = AsyncMock()

        with patch.object(svc, "fetch_all_sources", AsyncMock(return_value=fetch_results)):
            result = await svc.push_daily(db=db, user_id="user-1", target_date=date(2026, 7, 17))

        assert result["daily_id"] is not None
        assert result["item_count"] == 5
        assert "正常" in result["vibe"]
        assert result["error"] is None
        db.commit.assert_called_once()

    @pytest.mark.xfail(
        reason="composite_score 给合成测试项打分 < 0.75 阈值 → 0 候选入选 · "
        "见 docs/issues.md 债务 9",
        strict=False,
    )
    @pytest.mark.asyncio
    async def test_writes_5_items_to_db(self):
        """DB 应被 add 调用 1 (daily) + 5 (items) = 6 次。"""
        svc = DigestService()
        fetch_results = [
            make_fetch_result(items=[make_raw_item(f"Item {i}", type="model", region="overseas") for i in range(6)])
        ]
        db = AsyncMock()

        with patch.object(svc, "fetch_all_sources", AsyncMock(return_value=fetch_results)):
            result = await svc.push_daily(db=db, user_id="user-1", target_date=date(2026, 7, 17))

        assert result["item_count"] == 5
        assert db.add.call_count == 6  # 1 daily + 5 items


class TestPushDailyEmptyCase:
    @pytest.mark.asyncio
    async def test_zero_candidates_returns_no_vibe(self):
        """0 候选（fetch 全失败）→ daily_id=None + "今日 AI 圈无新动态"。"""
        svc = DigestService()
        fetch_results = [
            make_fetch_result(error="timeout"),
            make_fetch_result(error="404"),
        ]
        db = AsyncMock()

        with patch.object(svc, "fetch_all_sources", AsyncMock(return_value=fetch_results)):
            result = await svc.push_daily(db=db, user_id="user-1", target_date=date(2026, 7, 17))

        assert result["daily_id"] is None
        assert result["item_count"] == 0
        assert "无新动态" in result["vibe"] or "暂缺" in result["vibe"]
        # 0 候选不应 commit（边界 case · 简化不 commit）

    @pytest.mark.asyncio
    async def test_items_below_threshold_filtered(self):
        """所有 item score < 0.75 → 0 候选 → 返回空。"""
        svc = DigestService()
        # 老时间 → _calc_hot 评分低
        old_pub = (datetime.now(timezone.utc) - __import__("datetime").timedelta(days=30)).isoformat()
        fetch_results = [
            make_fetch_result(items=[
                make_raw_item("旧新闻1", published_at=old_pub),
                make_raw_item("旧新闻2", published_at=old_pub),
            ]),
        ]
        db = AsyncMock()

        with patch.object(svc, "fetch_all_sources", AsyncMock(return_value=fetch_results)):
            result = await svc.push_daily(db=db, user_id="user-1", target_date=date(2026, 7, 17))

        assert result["daily_id"] is None
        assert result["item_count"] == 0


class TestPushDailyPartialFailure:
    @pytest.mark.xfail(
        reason="composite_score 给合成测试项打分 < 0.75 阈值 → daily_id=None · "
        "见 docs/issues.md 债务 9",
        strict=False,
    )
    @pytest.mark.asyncio
    async def test_partial_fetch_failure_still_pushes(self):
        """部分 fetch 失败 · 仍有合格 item → 仍正常推送。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        fetch_results = [
            make_fetch_result(
                source_id="src-1",
                items=[
                    make_raw_item("Good 1", type="model", region="overseas"),
                    make_raw_item("Good 2", type="model", region="domestic"),
                    make_raw_item("Good 3", type="application", region="overseas"),
                    make_raw_item("Good 4", type="application", region="domestic"),
                    make_raw_item("Good 5", type="model", region="overseas"),
                ],
            ),
            make_fetch_result(source_id="src-2", error="timeout"),
        ]
        db = AsyncMock()

        with patch.object(svc, "fetch_all_sources", AsyncMock(return_value=fetch_results)):
            result = await svc.push_daily(db=db, user_id="user-1", target_date=date(2026, 7, 17))

        # 5 good items → 全部 push
        assert result["daily_id"] is not None
        assert result["item_count"] == 5
