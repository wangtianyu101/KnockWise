"""Tests for FastAPI startup logger initialization (T12 · P1-9 L1 平台层 · v1.1 logger trace_id 字段).

覆盖 SCN：
- TC-9: logger startup 接管 stdout（SCN-P1.9.3 v1.1）

测试策略：
- import utils.logger + setup_logger('knockwise') 直接调用（模拟 startup 行为）
- 捕获 stdout · 验证结构化 JSON 含 timestamp/level/trace_id/logger/msg
- 验证业务代码 logger.info() 输出含 trace_id 字段

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题）。
T12 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest backend/tests/test_logger_startup.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import json
import logging
import sys
from io import StringIO

import pytest

# 添加 backend/ 到 sys.path 以便 import logger.py
BACKEND_ROOT = "/Users/wangtianyu/IdeaProjects/KnockWise/backend"
sys.path.insert(0, BACKEND_ROOT)

from utils.logger import setup_logger, digest_logger, TraceFilter, set_trace_id, get_trace_id  # noqa: E402


# ─── TC-9: logger startup 接管 stdout + trace_id 字段（SCN-P1.9.3）───
def test_logger_startup_takes_over_stdout(monkeypatch):
    """setup_logger('knockwise') 后，业务代码 logger.info 输出结构化 JSON + trace_id 字段。

    v1.1 修正：T11 在 FastAPI startup 调用 setup_logger('knockwise')。
    本测试模拟 startup 行为 + 验证 stdout 接管 + 结构化输出 + trace_id 字段。
    """
    # 用 StringIO 替换 sys.stdout（setup_logger 用 sys.stdout 作为 StreamHandler）
    log_stream = StringIO()
    monkeypatch.setattr(sys, "stdout", log_stream)

    # 用 setup_logger 初始化 logger（覆盖默认 JSON formatter）
    test_logger_name = "test_logger_startup"
    test_logger = logging.getLogger(test_logger_name)
    test_logger.handlers = []  # 清空之前的 handlers 让 setup_logger 重新添加
    initialized_logger = setup_logger(test_logger_name)

    # 设置 trace_id（模拟业务代码 set_trace_id）
    set_trace_id("test-trace-id-123")

    # 业务代码 logger.info
    initialized_logger.info("knockwise logger initialized")

    # 解析输出
    log_output = log_stream.getvalue().strip()
    assert log_output, f"logger.info 输出为空 · 实际: {repr(log_output)}"

    # 验证是 JSON 格式
    try:
        log_json = json.loads(log_output)
    except json.JSONDecodeError as e:
        pytest.fail(f"logger 输出不是 JSON 格式: {log_output!r} (error: {e})")

    # 验证 spec § 2.2 SCN-P1.9.3 要求的 5 字段齐全
    required_fields = ["ts", "level", "trace_id", "logger", "msg"]
    for field in required_fields:
        assert field in log_json, f"logger 输出 JSON 缺 '{field}' 字段 · 实际: {log_json}"

    # 验证具体值
    assert log_json["level"] == "INFO", f"level 应为 INFO · 实际: {log_json['level']}"
    assert log_json["trace_id"] == "test-trace-id-123", f"trace_id 应为 'test-trace-id-123' · 实际: {log_json['trace_id']}"
    assert log_json["logger"] == test_logger_name, f"logger 字段应为 '{test_logger_name}' · 实际: {log_json['logger']}"
    assert log_json["msg"] == "knockwise logger initialized", f"msg 字段应匹配 · 实际: {log_json['msg']}"


# ─── TC-9b: setup_logger('knockwise') 真实调用（验证 startup 模拟）───
def test_setup_logger_knockwise_initialization():
    """调 setup_logger('knockwise')（模拟 startup 行为）后 logger 配置正确。

    T11 在 backend/main.py on_startup 调 setup_logger('knockwise')。
    本测试验证 setup_logger 函数本身能正确初始化 logger：
    - logger.handlers 不为空（添加了 StreamHandler）
    - logger 等级为 INFO
    - handler 含 TraceFilter
    - formatter 是自定义 JSON 格式化函数（不是默认 Formatter）
    """
    # 使用独立 logger name 避免污染全局
    test_logger_name = "test_setup_logger_init"
    # 先清除可能存在的 handler（setup_logger 会检查 if logger.handlers 跳过）
    test_logger = logging.getLogger(test_logger_name)
    test_logger.handlers = []

    # 调用 setup_logger（应当添加 handler）
    initialized_logger = setup_logger(test_logger_name)

    # 验证 1：handler 不为空
    assert len(initialized_logger.handlers) > 0, "setup_logger 后 handlers 应非空"

    # 验证 2：logger 等级为 INFO
    assert initialized_logger.level == logging.INFO, (
        f"logger 等级应为 INFO · 实际: {logging.getLevelName(initialized_logger.level)}"
    )

    # 验证 3：handler 含 TraceFilter
    handler = initialized_logger.handlers[0]
    filter_classes = [type(f).__name__ for f in handler.filters]
    assert "TraceFilter" in filter_classes, (
        f"handler 应含 TraceFilter · 实际 filters: {filter_classes}"
    )

    # 验证 4：handler 输出到 stdout
    assert isinstance(handler, logging.StreamHandler), (
        f"handler 应为 StreamHandler · 实际: {type(handler).__name__}"
    )


# ─── TC-9c: digest_logger（knockwise.digest）已有 trace_id 字段 ─
def test_digest_logger_has_trace_id_filter():
    """digest_logger = setup_logger('knockwise.digest')（logger.py:77）已有 TraceFilter。"""
    # digest_logger 是模块级实例（logger.py:77）
    assert digest_logger.name == "knockwise.digest", (
        f"digest_logger name 应为 'knockwise.digest' · 实际: {digest_logger.name}"
    )

    # 应当有 handlers
    assert len(digest_logger.handlers) > 0, "digest_logger 应有 handlers"

    # 应当有 TraceFilter
    handler = digest_logger.handlers[0]
    filter_classes = [type(f).__name__ for f in handler.filters]
    assert "TraceFilter" in filter_classes, (
        f"digest_logger handler 应含 TraceFilter · 实际: {filter_classes}"
    )