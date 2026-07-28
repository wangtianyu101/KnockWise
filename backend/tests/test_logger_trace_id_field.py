"""Tests for backend/utils/logger.py trace_id field (T10 · P1-9 L1 平台层 · v1.1 修正).

覆盖 SCN：
- TC-5: logger trace_id 字段在并发请求下不串（SCN-P1.9.1 v1.1）
- TC-5b: logger trace_id 字段跨请求不串（SCN-P1.9.2 v1.1）

测试策略：
- asyncio.gather 100 个并发 task 真跑（不 mock · 真实并发）
- 收集每个 task 的 logger.info 输出 trace_id
- 验证 100 个 trace_id 与各任务的 i 一一对应（无串）
- 验证跨请求切换 trace_id 不泄漏

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题）。
T10 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest backend/tests/test_logger_trace_id_field.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import asyncio
import logging
import sys
from io import StringIO

import pytest

# 添加 backend/ 到 sys.path 以便 import logger.py
BACKEND_ROOT = "/Users/wangtianyu/IdeaProjects/KnockWise/backend"
sys.path.insert(0, BACKEND_ROOT)

from utils.logger import trace_id_var, set_trace_id, get_trace_id, TraceFilter  # noqa: E402


# ─── TC-5: logger trace_id 100 并发隔离（SCN-P1.9.1 v1.1）─────
@pytest.mark.asyncio
async def test_logger_trace_id_concurrent_isolation():
    """100 个并发 async 任务 · 每个设自己的 trace_id · logger 输出应隔离。

    v1.1 修正：原 T19 global _trace_id 在并发下会 race（所有 task 共享同一变量）。
    T9 改用 contextvars.ContextVar 后，asyncio.Task 自动隔离 context。
    """
    # 用 StringIO 捕获所有 logger 输出
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    # 用 TraceFilter 让 logger 输出含 trace_id 字段
    handler.addFilter(TraceFilter())
    # 自定义 formatter 输出 trace_id（用 logger name 替代避免 trace_id 已被 set）
    handler.setFormatter(logging.Formatter("%(trace_id)s|%(message)s"))

    test_logger = logging.getLogger("test_logger_trace_id")
    test_logger.handlers = [handler]
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False

    async def task(i: int) -> tuple[int, str]:
        """每个并发 task 设自己的 trace_id + logger.info"""
        trace_id_var.set(f"req-{i}")
        # 给 asyncio 调度机会让其他 task 也设 trace_id
        await asyncio.sleep(0)
        # 再设一次确保覆盖（如果 race 会被其他 task 覆盖）
        trace_id_var.set(f"req-{i}")
        await asyncio.sleep(0)
        test_logger.info(f"task-{i}")
        return (i, get_trace_id())

    # 100 个并发任务
    results = await asyncio.gather(*[task(i) for i in range(100)])

    # 验证 1：每个 task 自己读回的 trace_id 应是自己设的（无 race）
    for i, returned_tid in results:
        assert returned_tid == f"req-{i}", (
            f"task {i} 读回的 trace_id 错了：期望 'req-{i}' 实际 '{returned_tid}'"
        )

    # 验证 2：logger 输出 trace_id 字段与各 task 一一对应
    log_output = log_stream.getvalue()
    log_lines = [line for line in log_output.strip().split("\n") if line]
    assert len(log_lines) == 100, f"期望 100 行日志，实际 {len(log_lines)} 行"

    for i in range(100):
        # 期望每行："req-{i}|task-{i}"
        expected = f"req-{i}|task-{i}"
        assert expected in log_output, (
            f"日志中缺 'req-{i}|task-{i}' · 可能 trace_id race · 实际日志:\n{log_output[:500]}"
        )


# ─── TC-5b: logger trace_id 跨请求不串（SCN-P1.9.2 v1.1）────
@pytest.mark.asyncio
async def test_logger_trace_id_cross_request_no_leak():
    """request A 设 trace_id='A' · request B 异步插入设 'B' · A 中途 await 后 logger 输出 trace_id 应是 'A'。

    v1.1 修正：原 T19 global _trace_id 在跨 await 切换时会被覆盖。
    T9 改用 ContextVar 后，asyncio.Task 各自有独立 context。
    """
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.addFilter(TraceFilter())
    handler.setFormatter(logging.Formatter("%(trace_id)s|%(message)s"))

    test_logger = logging.getLogger("test_logger_cross_request")
    test_logger.handlers = [handler]
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False

    async def request_a():
        trace_id_var.set("A")
        await asyncio.sleep(0.05)  # 给 request_b 机会插入
        # A 中途 await 后 logger · 应输出 trace_id='A'（不是 'B'）
        test_logger.info("A-step1")
        await asyncio.sleep(0.05)
        test_logger.info("A-step2")
        return get_trace_id()

    async def request_b():
        await asyncio.sleep(0.025)  # A 设 trace_id 之后 · B 启动
        trace_id_var.set("B")
        await asyncio.sleep(0.05)
        test_logger.info("B-step")
        return get_trace_id()

    # 并发跑 A 和 B
    a_tid, b_tid = await asyncio.gather(request_a(), request_b())

    # 验证 A 和 B 各自读回的 trace_id 不串
    assert a_tid == "A", f"request_a 读回 '{a_tid}' · 期望 'A'"
    assert b_tid == "B", f"request_b 读回 '{b_tid}' · 期望 'B'"

    # 验证 logger 输出 trace_id 字段正确（无串）
    log_output = log_stream.getvalue()
    # A 输出应当是 A · B 输出应当是 B
    assert "A|A-step1" in log_output, f"日志缺 'A|A-step1' · 实际:\n{log_output}"
    assert "A|A-step2" in log_output, f"日志缺 'A|A-step2' · 实际:\n{log_output}"
    assert "B|B-step" in log_output, f"日志缺 'B|B-step' · 实际:\n{log_output}"

    # 关键断言：A 的两条日志 trace_id 都是 'A'（不被 B 覆盖）
    a_step1_line = [line for line in log_output.split("\n") if "A-step1" in line][0]
    a_step2_line = [line for line in log_output.split("\n") if "A-step2" in line][0]
    assert a_step1_line.startswith("A|"), f"A-step1 trace_id 错了：{a_step1_line}"
    assert a_step2_line.startswith("A|"), f"A-step2 trace_id 错了：{a_step2_line}"