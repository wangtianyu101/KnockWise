"""Logger + Trace ID (T19: 2026-07-17 实施).

结构化日志 + trace_id 上下文

⚠️ **2026-07-22 audit（T31 路径核验）**：
- `DigestMetrics` 类已从本文件搬出至 `utils/metrics.py`（拆分关注点）
- logger.py 专做 logging + trace_id · metrics.py 专做指标采集
- 无向后兼容 shim — 当前零调用方，搬出无破坏
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


# 模块级 logger 实例
digest_logger = setup_logger("knockwise.digest")
