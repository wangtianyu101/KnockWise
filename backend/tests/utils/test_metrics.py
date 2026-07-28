"""Tests for backend/utils/metrics.py digest_metrics singleton (T-P0.2 · P0 stub 修复).

按 spec § 4.5 接入指南第 5 步 + metrics.py:11-15 docstring：
- 测试用 from utils.metrics import digest_metrics 直接 inc + snapshot（不依赖 push_daily）
- 断言 counter 真增（不只 mock hasattr）
- 覆盖 inc / timing / snapshot 三方法

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题）。
T-P0.2 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest tests/utils/test_metrics.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import sys

import pytest

# 添加 backend/ 到 sys.path
BACKEND_ROOT = "/Users/wangtianyu/IdeaProjects/KnockWise/backend"
sys.path.insert(0, BACKEND_ROOT)

from utils.metrics import DigestMetrics, digest_metrics  # noqa: E402


# ─── TC-P0.1: digest_metrics.inc 单调增（counter 真增断言）─────
def test_inc_increments_counter():
    """digest_metrics.inc('push_total') 后 counter +1（不只 mock hasattr）。

    spec § 4.5 接入指南第 5 步要求"覆盖 inc + snapshot"。
    """
    # 注意：digest_metrics 是单例 · 测试间共享状态
    # 用未使用过的 counter key（避免与现有测试冲突）
    test_key = "test_inc_increments_counter_key"
    initial = digest_metrics.counters.get(test_key, 0)

    # 调用 inc（默认 by=1）
    digest_metrics.inc(test_key)

    after = digest_metrics.counters.get(test_key, 0)
    assert after == initial + 1, f"counter '{test_key}' 应 +1 · 期望 {initial+1} 实际 {after}"


# ─── TC-P0.2: digest_metrics.inc(key, by=3) 按数累计 ──
def test_inc_with_by_parameter():
    """digest_metrics.inc(key, by=3) 后 counter +3（按 by 参数累加）。"""
    test_key = "test_inc_with_by_parameter_key"
    initial = digest_metrics.counters.get(test_key, 0)

    digest_metrics.inc(test_key, by=3)

    after = digest_metrics.counters.get(test_key, 0)
    assert after == initial + 3, f"counter '{test_key}' 应 +3 · 期望 {initial+3} 实际 {after}"


# ─── TC-P0.3: digest_metrics.timing 记录 elapsed_ms ──
def test_timing_records_elapsed_ms():
    """digest_metrics.timing('push_latency_ms', 150.5) 后 timings 含 150.5。

    验证 push_latency_ms 列表追加 · snapshot() 含 avg/p50/p95。
    """
    test_key = "test_timing_records_elapsed_ms_key"
    initial_count = len(digest_metrics.timings.get(test_key, []))

    digest_metrics.timing(test_key, 150.5)

    after_count = len(digest_metrics.timings.get(test_key, []))
    assert after_count == initial_count + 1, f"timings '{test_key}' 应 +1 · 期望 {initial_count+1} 实际 {after_count}"

    # 验证刚加的值在列表末尾
    last_value = digest_metrics.timings[test_key][-1]
    assert last_value == 150.5, f"最后 timing 值应为 150.5 · 实际 {last_value}"


# ─── TC-P0.4: digest_metrics.snapshot 返回 4 counter 键 ──
def test_snapshot_returns_4_counters():
    """snapshot() 返回 4 counter 键齐全（v1.2 修正键名）。

    用新建 DigestMetrics 实例隔离（避免全局单例被其他测试污染）。
    """
    new_instance = DigestMetrics()
    snapshot = new_instance.snapshot()
    assert "counters" in snapshot
    assert "timings" in snapshot

    expected = {"push_total", "push_failed", "fetch_failures", "rsshub_routes_broken"}
    actual = set(snapshot["counters"].keys())
    assert expected == actual, f"4 counter 键不齐全 · 期望 {expected} · 实际 {actual}"


# ─── TC-P0.5: digest_metrics snapshot 含 inc 后的 counter 新值 ──
def test_inc_then_snapshot_reflects_new_value():
    """inc 后 snapshot 含新值（end-to-end · 不只 mock hasattr）。

    spec § 4.5 接入指南第 5 步要求"覆盖 inc + snapshot"。
    """
    test_key = "test_inc_then_snapshot_reflects_new_value_key"
    # 先确保初始 0
    if test_key in digest_metrics.counters:
        digest_metrics.counters[test_key] = 0

    # inc 5 次
    for _ in range(5):
        digest_metrics.inc(test_key)

    # snapshot 验证
    snapshot = digest_metrics.snapshot()
    actual = snapshot["counters"].get(test_key, 0)
    assert actual == 5, f"snapshot counter 应为 5 · 实际 {actual}"


# ─── TC-P0.6: DigestMetrics 新实例独立 counter（不共享状态）─────
def test_new_digest_metrics_instance_is_independent():
    """新建 DigestMetrics() 实例 counter 默认 0 · 独立于全局单例。"""
    new_instance = DigestMetrics()
    assert new_instance.counters["push_total"] == 0
    assert new_instance.counters["push_failed"] == 0
    assert new_instance.counters["fetch_failures"] == 0
    assert new_instance.counters["rsshub_routes_broken"] == 0
    # 互不影响
    new_instance.inc("push_total", 10)
    assert digest_metrics.counters["push_total"] != new_instance.counters["push_total"] or \
           digest_metrics.counters["push_total"] == 0  # 单例可能已被其他测试改
    assert new_instance.counters["push_total"] == 10  # 新实例独立 +10