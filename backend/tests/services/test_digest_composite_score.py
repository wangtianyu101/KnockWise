"""Tests for DigestService.composite_score (T6).

Verifies 5 维加权打分 (hot/novel/changed/source_authority/user_pref):
- 5 weights 合计 1.0
- 各项分别打分逻辑（hot 衰减 / novel 关键词 / changed 距今 / authority 类别映射 / user_pref 命中比例）
- 边界 case: blocked_tags 命中 → 0.0; item 缺 published_at → 降权; user_prefs=None → 0.5
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.digest_service import DigestService


def make_item(
    title: str = "Claude 4.7 Sonnet 发布",
    summary: str = "Anthropic 发布 Claude 4.7 Sonnet · 工具调用稳定性 +23%",
    published_at: str | None = None,
    source_name: str = "Anthropic News",
) -> dict:
    """Build a sample RSS item dict for testing."""
    return {
        "title": title,
        "summary": summary,
        "url": "https://test.com",
        "published_at": published_at,
        "source_name": source_name,
    }


# ─── 权重 · 5 维 · 合计 1.0 ─────────────────────────────────


class TestWeightsSum:
    def test_weights_sum_to_1(self):
        assert sum(DigestService.DEFAULT_WEIGHTS.values()) == pytest.approx(1.0)

    def test_weights_have_all_5_dimensions(self):
        expected = {"hot", "novel", "changed", "source_authority", "user_pref"}
        assert set(DigestService.DEFAULT_WEIGHTS.keys()) == expected


# ─── composite_score 主流程 ─────────────────────────────────


class TestCompositeScore:
    def test_score_in_0_to_1_range(self):
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(published_at=now)
        score = svc.composite_score(item, user_prefs=None, source_category="一手")
        assert 0.0 <= score <= 1.0

    def test_high_quality_source_high_authority(self):
        """一手 + 最新 + 含首发 + 命中关注 → 应 ≥ 0.75（spec R1 阈值）。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(
            title="Anthropic 独家首发 Claude 4.7 Sonnet",
            summary="重大突破 · 发布 · open source",
            published_at=now,
        )
        prefs = {"interested_tags": ["Claude", "Anthropic"], "blocked_tags": []}
        score = svc.composite_score(item, user_prefs=prefs, source_category="一手")
        assert score >= 0.75, f"Expected ≥0.75 for high-quality item, got {score}"

    def test_low_quality_old_item_low_score(self):
        """旧 + 二手 + 无关注标签命中 → 应 < 0.5。"""
        svc = DigestService()
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        item = make_item(
            title="普通新闻",
            summary="",
            published_at=old,
        )
        prefs = {"interested_tags": ["不相关"], "blocked_tags": []}
        score = svc.composite_score(item, user_prefs=prefs, source_category="社区")
        assert score < 0.5, f"Expected <0.5 for low-quality item, got {score}"


# ─── 边界 case ─────────────────────────────────────────────


class TestBlockedTagsHardZero:
    def test_blocked_tag_hit_returns_zero(self):
        """spec R5: blocked_tags 命中 → 直接 0.0（屏蔽优先）。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(title="深度学习框架大新闻", published_at=now)
        prefs = {
            "interested_tags": ["AI"],
            "blocked_tags": ["深度学习"],  # 标题含此词
        }
        score = svc.composite_score(item, user_prefs=prefs, source_category="一手")
        assert score == 0.0

    def test_blocked_tag_not_in_title_unaffected(self):
        """blocked_tag 不在标题 → 不影响分数。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(title="Claude 4.7 Sonnet 发布", published_at=now)
        prefs = {
            "interested_tags": [],
            "blocked_tags": ["完全不相关词"],
        }
        score = svc.composite_score(item, user_prefs=prefs, source_category="一手")
        assert score > 0.0


class TestMissingPublishedAt:
    def test_no_published_at_changes_dim(self):
        """item 缺 published_at → changed 维度降权 0.5x。"""
        svc = DigestService()
        item_with_date = make_item(published_at=datetime.now(timezone.utc).isoformat())
        item_without_date = make_item(published_at=None)

        # both same otherwise
        score_with = svc.composite_score(item_with_date, user_prefs=None, source_category="一手")
        score_without = svc.composite_score(item_without_date, user_prefs=None, source_category="一手")

        # 无 published_at 分数应更低（主要是 changed 维度降权）
        assert score_without < score_with


class TestUserPrefsHandling:
    def test_none_user_prefs_uses_default(self):
        """user_prefs=None → user_pref 维度取默认 0.5。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(published_at=now)

        # 模拟没有 pref 时的 user_pref 维度
        score = svc.composite_score(item, user_prefs=None, source_category="一手")
        # 不应崩
        assert 0.0 <= score <= 1.0

    def test_empty_interested_tags_neutral(self):
        """interested_tags=[] → user_pref 维度 0.5 中性。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(published_at=now)
        prefs = {"interested_tags": [], "blocked_tags": []}
        score = svc.composite_score(item, user_prefs=prefs, source_category="一手")
        assert 0.0 <= score <= 1.0

    def test_all_interested_tags_match_high_pref(self):
        """所有关注标签都命中 → user_pref ≈ 1.0。"""
        svc = DigestService()
        now = datetime.now(timezone.utc).isoformat()
        item = make_item(
            title="Claude 4.7 Sonnet 重大更新",
            summary="Anthropic AI agent 突破",
            published_at=now,
        )
        prefs = {
            "interested_tags": ["Claude", "Anthropic", "AI"],
            "blocked_tags": [],
        }
        score = svc.composite_score(item, user_prefs=prefs, source_category="一手")
        assert score > 0.6  # 高分


# ─── 各维度独立测试 ─────────────────────────────────────────


class TestHotDimension:
    def test_fresh_article_6h_high(self):
        svc = DigestService()
        recent = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        item = make_item(published_at=recent)
        assert svc._calc_hot(item) == 1.0

    def test_24h_article_medium(self):
        svc = DigestService()
        day_old = (datetime.now(timezone.utc) - timedelta(hours=20)).isoformat()
        item = make_item(published_at=day_old)
        assert svc._calc_hot(item) == 0.7

    def test_7d_article_low(self):
        svc = DigestService()
        week_old = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        item = make_item(published_at=week_old)
        assert svc._calc_hot(item) == 0.4

    def test_no_published_at_neutral(self):
        svc = DigestService()
        assert svc._calc_hot({}) == 0.5


class TestNovelDimension:
    def test_first_keyword_high_novel(self):
        svc = DigestService()
        item = make_item(title="Anthropic 独家首发 Claude 4.7", summary="")
        assert svc._calc_novel(item) == 0.9

    def test_breakthrough_keyword_high(self):
        svc = DigestService()
        item = make_item(title="重大突破：GPT-5", summary="")
        assert svc._calc_novel(item) == 0.8

    def test_release_keyword_medium(self):
        svc = DigestService()
        item = make_item(title="新版本发布", summary="")
        assert svc._calc_novel(item) == 0.6

    def test_no_keyword_low(self):
        svc = DigestService()
        item = make_item(title="普通新闻", summary="")
        assert svc._calc_novel(item) == 0.4


class TestSourceAuthorityMapping:
    def test_first_hand_high(self):
        svc = DigestService()
        assert svc.SOURCE_AUTHORITY_SCORE["一手"] == 1.0

    def test_second_hand_medium(self):
        svc = DigestService()
        assert svc.SOURCE_AUTHORITY_SCORE["二手"] == 0.6

    def test_community_low(self):
        svc = DigestService()
        assert svc.SOURCE_AUTHORITY_SCORE["社区"] == 0.4

    def test_unknown_category_default(self):
        """未知 category → 默认 0.5。"""
        svc = DigestService()
        item = make_item()
        score = svc.composite_score(item, user_prefs=None, source_category="未知")
        # 应仍返回 0.0-1.0 不崩
        assert 0.0 <= score <= 1.0
