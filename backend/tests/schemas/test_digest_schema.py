"""Tests for AI push Pydantic schemas (T2: 2026-07-17 实施).

Verifies:
- All required schemas can be instantiated with valid data
- Field validation rejects invalid data (range, length, enum)
- Read/Create/Update variants work as expected
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from schemas.digest import (
    # A · Daily
    DigestDailyItem,
    DigestDailyItemCreate,
    DigestTodayResponse,
    DigestDailiesListItem,
    DigestDailiesListResponse,
    # B · Bookmarks
    BookmarkCreate,
    BookmarkListItem,
    BookmarkListResponse,
    # C · Behavior
    ReadCreate,
    HideCreate,
    HideResponse,
    # D · Sources
    DigestSource,
    DigestSourceCreate,
    DigestSourceUpdate,
    DigestSourceListResponse,
    # E · Settings
    DigestSettings,
    DigestSettingsUpdate,
)


# ═══════════════════════════════════════════════════════════════════
# A · Daily schemas
# ═══════════════════════════════════════════════════════════════════


class TestDigestDailyItemCreate:
    def test_valid_minimal(self):
        item = DigestDailyItemCreate(
            title="Claude 4.7 Sonnet 发布",
            quality_score=0.98,
            type="model",
            region="overseas",
            category="headline",
            source_name="Anthropic News",
            source_url="https://www.anthropic.com/news/...",
        )
        assert item.title == "Claude 4.7 Sonnet 发布"
        assert item.quality_score == 0.98
        assert item.type == "model"
        assert item.summary is None
        assert item.estimated_minutes == 3  # default

    def test_quality_score_must_be_0_to_1(self):
        with pytest.raises(ValidationError):
            DigestDailyItemCreate(
                title="x", quality_score=1.5, type="model",
                region="overseas", category="headline",
                source_name="x", source_url="https://x.com",
            )

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            DigestDailyItemCreate(
                title="x", quality_score=0.5, type="video",  # not in enum
                region="overseas", category="headline",
                source_name="x", source_url="https://x.com",
            )

    def test_estimated_minutes_max_5(self):
        with pytest.raises(ValidationError):
            DigestDailyItemCreate(
                title="x", quality_score=0.5, type="model",
                region="overseas", category="headline",
                source_name="x", source_url="https://x.com",
                estimated_minutes=10,
            )


class TestDigestDailyItem:
    def test_valid_with_all_fields(self):
        item = DigestDailyItem(
            id="uuid-1",
            rank=1,
            title="Test",
            summary="Test summary",
            quality_score=0.9,
            type="application",
            region="domestic",
            category="engineering",
            source_name="Test Source",
            source_url="https://test.com",
            published_at=datetime(2026, 7, 17, tzinfo=timezone.utc),
            estimated_minutes=4,
            is_read=False,
            is_bookmarked=True,
            related_item_ids=["uuid-old-1", "uuid-old-2"],
        )
        assert item.is_bookmarked is True
        assert len(item.related_item_ids) == 2

    def test_rank_must_be_1_to_5(self):
        with pytest.raises(ValidationError):
            DigestDailyItem(
                id="uuid", rank=6, title="x", quality_score=0.5,
                type="model", region="overseas", category="headline",
                source_name="x", source_url="https://x.com",
            )


class TestDigestTodayResponse:
    def test_with_5_items(self):
        items = [
            DigestDailyItem(
                id=f"uuid-{i}", rank=i + 1, title=f"Title {i}",
                quality_score=0.8, type="model", region="overseas",
                category="headline", source_name="x",
                source_url="https://x.com", estimated_minutes=3,
            )
            for i in range(5)
        ]
        resp = DigestTodayResponse(
            date=date(2026, 7, 17),
            vibe="今日 5 条 · 正常",
            item_count=5,
            items=items,
        )
        assert resp.item_count == 5
        assert len(resp.items) == 5

    def test_max_5_items_enforced(self):
        items = [
            DigestDailyItem(
                id=f"uuid-{i}", rank=1, title=f"t{i}",
                quality_score=0.5, type="model", region="overseas",
                category="headline", source_name="x", source_url="https://x.com",
                estimated_minutes=3,
            )
            for i in range(6)  # 6 items
        ]
        with pytest.raises(ValidationError):
            DigestTodayResponse(date=date(2026, 7, 17), items=items)


# ═══════════════════════════════════════════════════════════════════
# B · Bookmark schemas
# ═══════════════════════════════════════════════════════════════════


class TestBookmarkCreate:
    def test_valid(self):
        bc = BookmarkCreate(item_id="12345678-1234-1234-1234-123456789012")
        assert bc.item_id.startswith("1234")

    def test_item_id_must_be_36_chars(self):
        with pytest.raises(ValidationError):
            BookmarkCreate(item_id="short-uuid")


class TestBookmarkListItem:
    def test_valid(self):
        item = BookmarkListItem(
            item_id="12345678-1234-1234-1234-123456789012",
            title="Test", summary="s", type="model", region="overseas",
            source_name="x", source_url="https://x.com",
            quality_score=4.5,
            bookmarked_at=datetime(2026, 7, 17, tzinfo=timezone.utc),
            published_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
        )
        assert item.type == "model"


# ═══════════════════════════════════════════════════════════════════
# C · Behavior schemas
# ═══════════════════════════════════════════════════════════════════


class TestReadCreate:
    def test_valid(self):
        r = ReadCreate(
            item_id="12345678-1234-1234-1234-123456789012",
            duration_sec=120,
        )
        assert r.duration_sec == 120

    def test_duration_max_86400(self):
        with pytest.raises(ValidationError):
            ReadCreate(
                item_id="12345678-1234-1234-1234-123456789012",
                duration_sec=100000,
            )

    def test_duration_negative_rejected(self):
        with pytest.raises(ValidationError):
            ReadCreate(
                item_id="12345678-1234-1234-1234-123456789012",
                duration_sec=-1,
            )


class TestHideCreate:
    def test_valid(self):
        h = HideCreate(
            item_id="12345678-1234-1234-1234-123456789012",
            reason="not_interested",
            topic_keywords=["Claude", "Anthropic"],
        )
        assert h.reason == "not_interested"
        assert len(h.topic_keywords) == 2

    def test_reason_must_be_valid_enum(self):
        with pytest.raises(ValidationError):
            HideCreate(
                item_id="12345678-1234-1234-1234-123456789012",
                reason="spam",  # not in enum
                topic_keywords=[],
            )

    def test_topic_keywords_max_5(self):
        with pytest.raises(ValidationError):
            HideCreate(
                item_id="12345678-1234-1234-1234-123456789012",
                reason="low_quality",
                topic_keywords=["a", "b", "c", "d", "e", "f"],  # 6
            )


# ═══════════════════════════════════════════════════════════════════
# D · Source schemas
# ═══════════════════════════════════════════════════════════════════


class TestDigestSourceCreate:
    def test_valid(self):
        s = DigestSourceCreate(
            name="稀土掘金 LLM",
            url="https://rsshub.app/juejin/tag/LLM",
            category="model",
            type="model",
            region="domestic",
        )
        assert s.name == "稀土掘金 LLM"

    def test_url_must_be_valid_http(self):
        with pytest.raises(ValidationError):
            DigestSourceCreate(
                name="x", url="not-a-url",
                category="model", type="model", region="domestic",
            )


class TestDigestSourceUpdate:
    def test_partial_update_enabled_only(self):
        u = DigestSourceUpdate(enabled=False)
        assert u.enabled is False
        assert u.name is None

    def test_partial_update_name_only(self):
        u = DigestSourceUpdate(name="New name")
        assert u.name == "New name"
        assert u.enabled is None


class TestDigestSource:
    def test_system_source_user_id_null(self):
        s = DigestSource(
            id="uuid-1", user_id=None, name="Anthropic News",
            url="https://anthropic.com/news", category="一手",
            type="model", region="overseas",
            enabled=True, is_default=True,
        )
        assert s.user_id is None
        assert s.is_default is True


# ═══════════════════════════════════════════════════════════════════
# E · Settings schemas
# ═══════════════════════════════════════════════════════════════════


class TestDigestSettings:
    def test_defaults(self):
        s = DigestSettings(user_id="uuid-1")
        assert s.push_hour == 8
        assert s.push_minute == 0
        assert s.push_timezone == "Asia/Shanghai"
        assert s.email_enabled is True
        assert s.daily_count == 5

    def test_invalid_hour_rejected(self):
        with pytest.raises(ValidationError):
            DigestSettings(user_id="uuid-1", push_hour=24)

    def test_daily_count_only_3_or_5(self):
        with pytest.raises(ValidationError):
            DigestSettings(user_id="uuid-1", daily_count=4)

    def test_max_10_tags(self):
        with pytest.raises(ValidationError):
            DigestSettings(
                user_id="uuid-1",
                interested_tags=[f"t{i}" for i in range(11)],
            )


class TestDigestSettingsUpdate:
    def test_empty_update_valid(self):
        u = DigestSettingsUpdate()
        assert u.push_hour is None
        assert u.email_enabled is None

    def test_partial_update(self):
        u = DigestSettingsUpdate(
            push_hour=7, push_minute=30, interested_tags=["Agent", "LLM"]
        )
        assert u.push_hour == 7
        assert u.push_minute == 30
        assert u.interested_tags == ["Agent", "LLM"]
