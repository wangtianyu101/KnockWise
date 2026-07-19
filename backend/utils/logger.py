"""Logger + Observability (T19: 2026-07-17 实施).

结构化日志 + trace_id + 关键 metrics
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any


# Trace ID 上下文 (简化)
_trace_id: str | None = None


def get_trace_id() -> str:
    """当前请求的 trace_id · 没设则生成。"""
    global _trace_id
    if not _trace_id:
        _trace_id = str(uuid.uuid4())[:8]
    return _trace_id


def set_trace_id(tid: str) -> None:
    _trace_id = tid


class TraceFilter(logging.Filter):
    """为每条 log 加 trace_id。"""
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def setup_logger(name: str = "knockwise") -> logging.Logger:
    """配置结构化 JSON logger。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(TraceFilter())

    def fmt(record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "trace_id": getattr(record, "trace_id", "-"),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self_format_exc(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

    handler.setFormatter(logging.Formatter())
    handler.format = lambda r: fmt(r)  # type: ignore
    logger.addHandler(handler)
    return logger


def self_format_exc(exc_info) -> str:
    import traceback
    return "".join(traceback.format_exception(*exc_info))


# Metrics 简易实现 (T19 关键指标)
class DigestMetrics:
    """关键指标 (failure_rate / push_latency / rsshub_health)。"""

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
        import statistics
        snapshot = {"counters": dict(self.counters)}
        snapshot["timings"] = {}
        for k, vs in self.timings.items():
            if vs:
                snapshot["timings"][k] = {
                    "count": len(vs), "avg": statistics.mean(vs),
                    "p50": statistics.median(vs), "p95": sorted(vs)[int(len(vs) * 0.95)] if len(vs) > 1 else vs[0],
                }
        return snapshot


# 模块级
digest_metrics = DigestMetrics()
digest_logger = setup_logger("knockwise.digest")
