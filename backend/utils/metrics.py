"""Metrics 简易实现 · 关键指标采集

⚠️ **状态（2026-07-22 audit）**：
- 当前 **dead code** — DigestMetrics 类已定义 + digest_metrics 实例已创建
- 全代码库零调用（无 service / handler 触发 inc() / timing() / snapshot()）
- 无对应单测（`test_metrics_emits_digest_failure_rate` 在 audit 中标"DONE" 但实际不存在）
- 模块从 `utils/logger.py` 搬出至本文件（T31 决策 1 · commit `acca478` 后续）
- 真实指标集成属决策 4「P0 stub 修复」之后阶段

**接入指南**（未来实施）：
1. 在 `services/digest_service.py` push_daily() 成功路径调用 `digest_metrics.inc("push_total")` + `timing("push_latency_ms", ...)`
2. 失败路径 `digest_metrics.inc("push_failed")`
3. RSSHub 抓取失败时 `digest_metrics.inc("fetch_failures")` 或 `inc("rsshub_routes_broken", by=count)`
4. 在 `api/digest.py` GET /api/digest/metrics 返回 `digest_metrics.snapshot()`
5. 加测试：`tests/utils/test_metrics.py::test_metrics_emits_digest_failure_rate`（覆盖 inc + snapshot）

来源：T19 实施时建的脚手架（T19 commit `96566d8`）· 后续没真正接进 call site
"""
from __future__ import annotations

import statistics
from typing import Any


class DigestMetrics:
    """关键指标 (failure_rate / push_latency / rsshub_health)。

    简易内存实现 · 重启清零 · 后续可接 Prometheus / OTel exporter
    """

    def __init__(self):
        self.counters: dict[str, int] = {
            "push_total": 0,
            "push_failed": 0,
            "fetch_failures": 0,
            "rsshub_routes_broken": 0,
        }
        self.timings: dict[str, list[float]] = {
            "push_latency_ms": [],
        }

    def inc(self, key: str, by: int = 1):
        self.counters[key] = self.counters.get(key, 0) + by

    def timing(self, key: str, ms: float):
        self.timings.setdefault(key, []).append(ms)

    def snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {"counters": dict(self.counters), "timings": {}}
        for k, vs in self.timings.items():
            if vs:
                snapshot["timings"][k] = {
                    "count": len(vs),
                    "avg": statistics.mean(vs),
                    "p50": statistics.median(vs),
                    "p95": sorted(vs)[int(len(vs) * 0.95)] if len(vs) > 1 else vs[0],
                }
        return snapshot


# 模块级单例
digest_metrics = DigestMetrics()
