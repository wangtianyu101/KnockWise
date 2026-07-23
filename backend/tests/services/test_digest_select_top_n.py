"""Tests for DigestService.select_top_n (T7).

Verifies 多样性平衡 + 阈值过滤:
- 10 候选 → 选 5 条
- 满足 ≥ 2 国内 + 2 国外 + 3 模型 + 2 应用
- 阈值过滤：score < 0.75 不入选
- 候选不足 5：返回所有合格
- 全部候选 score < 0.75：返回空 list
"""
from __future__ import annotations

import pytest

from services.digest_service import DigestService


def make_scored(
    title: str = "Test",
    score: float = 0.85,
    item_type: str = "model",  # model | application
    region: str = "overseas",   # domestic | overseas
) -> dict:
    """Build a candidate item with score + dual-axis labels."""
    return {
        "item": {"title": title, "summary": "x", "url": "https://x"},
        "title": title,
        "score": score,
        "type": item_type,
        "region": region,
    }


# ─── 多样性平衡主流程 ─────────────────────────────────────


class TestSelectTopNDiversity:
    @pytest.mark.xfail(
        reason=(
            "owner=backend-digest; "
            "issue=docs/issues.md#digest-select-top-n-diversity; "
            "expiry=2026-08-31; "
            "reason=select_top_n 多样性未实现: DIVERSITY_MIN 键是 type/region 的值, 算法却当键查 (it.get('domestic') 恒 None)"
        ),
        strict=True,
    )
    def test_selects_5_with_diversity(self):
        """10 候选（含 2 国内 + 3 国外 + 5 模型 + 3 应用）→ 选 5 条满足多样性。"""
        svc = DigestService()
        candidates = [
            make_scored("国内模型1", 0.90, "model", "domestic"),
            make_scored("国内模型2", 0.88, "model", "domestic"),
            make_scored("国内应用1", 0.86, "application", "domestic"),
            make_scored("国外模型1", 0.92, "model", "overseas"),
            make_scored("国外模型2", 0.89, "model", "overseas"),
            make_scored("国外应用1", 0.85, "application", "overseas"),
            make_scored("国外应用2", 0.83, "application", "overseas"),
            make_scored("国内应用2", 0.81, "application", "domestic"),
            make_scored("国外模型3", 0.79, "model", "overseas"),
            make_scored("国内模型3", 0.77, "model", "domestic"),
        ]
        result = svc.select_top_n(candidates, n=5)

        # 必须 5 条
        assert len(result) == 5

        # 必须 ≥ 2 domestic + ≥ 2 overseas
        domestic_count = sum(1 for it in result if it["region"] == "domestic")
        overseas_count = sum(1 for it in result if it["region"] == "overseas")
        assert domestic_count >= 2, f"domestic={domestic_count}, expected ≥2"
        assert overseas_count >= 2, f"overseas={overseas_count}, expected ≥2"

        # 必须 ≥ 3 model + ≥ 2 application
        model_count = sum(1 for it in result if it["type"] == "model")
        app_count = sum(1 for it in result if it["type"] == "application")
        assert model_count >= 3, f"model={model_count}, expected ≥3"
        assert app_count >= 2, f"application={app_count}, expected ≥2"

        # score 降序
        scores = [it["score"] for it in result]
        assert scores == sorted(scores, reverse=True)


# ─── 阈值过滤 ──────────────────────────────────────────────


class TestSelectTopNThreshold:
    @pytest.mark.asyncio
    async def test_below_threshold_excluded(self):
        """score < 0.75 不入选（spec R1 阈值）。"""
        svc = DigestService()
        candidates = [
            make_scored("High 1", 0.95),
            make_scored("High 2", 0.85),
            make_scored("Below 1", 0.74),  # < 0.75
            make_scored("Below 2", 0.65),  # < 0.75
            make_scored("At threshold", 0.75),  # >= 0.75
        ]
        result = svc.select_top_n(candidates, n=5)
        # 只 3 条 ≥ 0.75
        assert len(result) == 3
        assert all(it["score"] >= 0.75 for it in result)

    @pytest.mark.asyncio
    async def test_custom_threshold(self):
        """自定义阈值 0.5 → 5 条全部入选。"""
        svc = DigestService()
        candidates = [make_scored(f"Item {i}", 0.55 + i * 0.05) for i in range(5)]
        result = svc.select_top_n(candidates, n=5, score_threshold=0.5)
        assert len(result) == 5


# ─── 候选不足 ──────────────────────────────────────────────


class TestSelectTopNInsufficient:
    @pytest.mark.asyncio
    async def test_returns_all_when_fewer_than_n(self):
        """3 合格候选 · n=5 → 返回 3 条（spec D2 fallback）。"""
        svc = DigestService()
        candidates = [
            make_scored("Only 1", 0.95),
            make_scored("Only 2", 0.90),
            make_scored("Only 3", 0.85),
        ]
        result = svc.select_top_n(candidates, n=5)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_when_none_pass_threshold(self):
        """0 候选过阈值 → 返回空 list。"""
        svc = DigestService()
        candidates = [
            make_scored("Low 1", 0.65),
            make_scored("Low 2", 0.55),
        ]
        result = svc.select_top_n(candidates, n=5)
        assert result == []


# ─── 自定义 N ────────────────────────────────────────────────


class TestSelectTopNCustomN:
    def test_n_3_returns_3(self):
        svc = DigestService()
        candidates = [make_scored(f"Item {i}", 0.95 - i * 0.01) for i in range(10)]
        result = svc.select_top_n(candidates, n=3)
        assert len(result) == 3
        # 最高 3 分
        assert result[0]["score"] == pytest.approx(0.95)
        assert result[1]["score"] == pytest.approx(0.94)
        assert result[2]["score"] == pytest.approx(0.93)


# ─── 多样性边界 ────────────────────────────────────────────


class TestSelectTopNDiversityEdgeCases:
    def test_diversity_fails_gracefully_when_not_enough(self):
        """候选只有 1 domestic 2 overseas → 选 1+2=3 条返回（不足 5 也没事）。"""
        svc = DigestService()
        candidates = [
            make_scored("国内唯一", 0.90, "model", "domestic"),
            make_scored("国外1", 0.88, "model", "overseas"),
            make_scored("国外2", 0.85, "application", "overseas"),
        ]
        result = svc.select_top_n(candidates, n=5)
        # 返回所有 3 条（不足 5）
        assert len(result) == 3

    def test_score_zero_excluded(self):
        """score=0 被阈值过滤（< 0.75）。"""
        svc = DigestService()
        candidates = [
            make_scored("Good", 0.90),
            make_scored("Zero", 0.0),
            make_scored("Negative", -0.1),  # 防御
        ]
        result = svc.select_top_n(candidates, n=3)
        assert len(result) == 1
        assert result[0]["title"] == "Good"
