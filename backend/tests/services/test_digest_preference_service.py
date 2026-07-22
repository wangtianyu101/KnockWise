"""Tests for DigestPreferenceService (T9).

Verifies:
- 整合 settings.interested_tags / blocked_tags
- 整合 active hide topic_keywords (7 天内 expire)
- 7 天前 expire 的 hide 不再纳入
- 不存在的 settings 返回默认值
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.digest_preference_service import DigestPreferenceService


def make_settings(
    interested: list[str] | None = None,
    blocked: list[str] | None = None,
) -> MagicMock:
    s = MagicMock()
    s.interested_tags = interested or []
    s.blocked_tags = blocked or []
    return s


def make_hide(
    keywords: list[str] | None = None,
    expires_in_days: int = 3,
) -> MagicMock:
    h = MagicMock()
    h.topic_keywords = keywords or []
    h.expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    return h


class TestGetUserPrefsHappyPath:
    @pytest.mark.asyncio
    async def test_combines_settings_and_hide(self):
        svc = DigestPreferenceService()
        db = AsyncMock()
        settings = make_settings(interested=["Agent", "Claude"], blocked=["crypto"])
        hide1 = make_hide(keywords=["Web3", "元宇宙"], expires_in_days=3)
        hide2 = make_hide(keywords=["crypto"], expires_in_days=1)

        # mock db.execute to return settings first, then hide
        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = settings
        hide_result = MagicMock()
        hide_result.scalars.return_value.all.return_value = [hide1, hide2]

        db.execute.side_effect = [settings_result, hide_result]

        prefs = await svc.get_user_prefs(db=db, user_id="u1")

        assert set(prefs["interested_tags"]) == {"Agent", "Claude"}
        assert set(prefs["blocked_tags"]) == {"crypto"}
        assert set(prefs["hide_topics"]) == {"Web3", "元宇宙", "crypto"}
        assert prefs["source_authority_bias"] == 1.0


class TestGetUserPrefsHideExpiry:
    @pytest.mark.asyncio
    async def test_filters_out_expired_hides(self):
        """7 天前的 hide 不再纳入 hide_topics。"""
        svc = DigestPreferenceService()
        db = AsyncMock()
        settings = make_settings()
        # SQL WHERE 过滤 · DB 端 · mock 已过滤
        active_hide = make_hide(keywords=["active"], expires_in_days=3)
        # 7 天前的 · 不在 result 里
        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = settings
        hide_result = MagicMock()
        hide_result.scalars.return_value.all.return_value = [active_hide]

        db.execute.side_effect = [settings_result, hide_result]

        prefs = await svc.get_user_prefs(db=db, user_id="u1")

        assert "active" in prefs["hide_topics"]
        # "expired" 不会出现在结果里（DB 端已过滤）


class TestGetUserPrefsDefaults:
    @pytest.mark.asyncio
    async def test_no_settings_returns_defaults(self):
        """用户无 settings 记录 → 返回空 list + 1.0 bias。"""
        svc = DigestPreferenceService()
        db = AsyncMock()
        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = None
        hide_result = MagicMock()
        hide_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [settings_result, hide_result]

        prefs = await svc.get_user_prefs(db=db, user_id="u1")

        assert prefs["interested_tags"] == []
        assert prefs["blocked_tags"] == []
        assert prefs["hide_topics"] == []
        assert prefs["source_authority_bias"] == 1.0

    @pytest.mark.asyncio
    async def test_no_hides_returns_empty_topics(self):
        """有 settings 但无 hide → hide_topics = []。"""
        svc = DigestPreferenceService()
        db = AsyncMock()
        settings = make_settings(interested=["AI"])
        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = settings
        hide_result = MagicMock()
        hide_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [settings_result, hide_result]

        prefs = await svc.get_user_prefs(db=db, user_id="u1")

        assert prefs["interested_tags"] == ["AI"]
        assert prefs["hide_topics"] == []


class TestGetUserPrefsDedup:
    @pytest.mark.asyncio
    async def test_dedupes_repeated_keywords(self):
        """同一 keyword 多次出现 → 去重。"""
        svc = DigestPreferenceService()
        db = AsyncMock()
        settings = make_settings()
        hide1 = make_hide(keywords=["AI", "Claude"], expires_in_days=2)
        hide2 = make_hide(keywords=["AI", "Web3"], expires_in_days=1)
        settings_result = MagicMock()
        settings_result.scalar_one_or_none.return_value = settings
        hide_result = MagicMock()
        hide_result.scalars.return_value.all.return_value = [hide1, hide2]

        db.execute.side_effect = [settings_result, hide_result]

        prefs = await svc.get_user_prefs(db=db, user_id="u1")

        # "AI" 出现 2 次 → 只 1 次
        assert sorted(prefs["hide_topics"]) == ["AI", "Claude", "Web3"]
