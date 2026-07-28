"""Logger + Trace ID (T19: 2026-07-17 实施 · T9 v1.1 修正 2026-07-27).

结构化日志 + trace_id 上下文（contextvars 隔离 · 避免并发 race）

⚠️ **2026-07-22 audit（T31 路径核验）**：
- `DigestMetrics` 类已从本文件搬出至 `utils/metrics.py`（拆分关注点）
- logger.py 专做 logging + trace_id · metrics.py 专做指标采集
- 无向后兼容 shim — 当前零调用方，搬出无破坏

⚠️ **2026-07-27 T9 v1.1 调研偏差修正**：
- 原 `global _trace_id: str | None = None` 全局变量在 asyncio 并发请求下会 race
- 改用 `contextvars.ContextVar[str]` 实现跨请求隔离（spec § 4.4 v1.1 修订）
- 保留 `get_trace_id()` / `set_trace_id()` 函数接口（向后兼容 · 内部用 ContextVar 实现）
- TraceFilter.filter 内部仍调 `get_trace_id()` · 但 `get_trace_id()` 现在从 ContextVar 读
"""
from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


# Trace ID 上下文（contextvars 隔离 · v1.1 修正）
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)


def get_trace_id() -> str:
    """当前请求/任务的 trace_id · 未设则返回空字符串（v1.1 改用 ContextVar）。"""
    return trace_id_var.get()


def set_trace_id(tid: str) -> None:
    """设置当前请求/任务的 trace_id（v1.1 改用 ContextVar）。"""
    trace_id_var.set(tid)


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


# 模块级 logger 实例
digest_logger = setup_logger("knockwise.digest")
