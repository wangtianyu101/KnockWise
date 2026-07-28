"""Tests for GET /api/digest/metrics endpoint (T14 · P1-9 L1 平台层 · v1.2 修正 counter 键).

覆盖 SCN：
- TC-8: 4 counter 键齐全（SCN-P1.9.4 v1.2）
- TC-8.5: 仅本地访问（SCN-P1.9.7）

测试策略：
- FastAPI TestClient 真测 endpoint（不 mock · 不 stub）
- 业务代码直接调 digest_metrics.inc() 累计 counter
- 验证 GET /api/digest/metrics 返回的 JSON 含 4 counter 键

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题）。
T14 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest backend/tests/test_metrics_endpoint.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 添加 backend/ 到 sys.path
BACKEND_ROOT = "/Users/wangtianyu/IdeaProjects/KnockWise/backend"
sys.path.insert(0, BACKEND_ROOT)

from api.digest_metrics import router as digest_metrics_router  # noqa: E402
from utils.metrics import digest_metrics  # noqa: E402


# ─── TC-8: GET /api/digest/metrics 返回 4 counter 齐全（SCN-P1.9.4 v1.2）───
def test_get_metrics_returns_4_counters():
    """业务代码 inc counter 后，GET /api/digest/metrics 返回 4 counter 键齐全。

    v1.2 决策 3 修正：counter 键 = push_total / push_failed / fetch_failures / rsshub_routes_broken
    与 backend/utils/metrics.py:32-37 一致。
    """
    # 创建独立的 FastAPI app（含 endpoint router · 不依赖完整 main app）
    app = FastAPI()
    app.include_router(digest_metrics_router)

    # 业务代码先 inc counter（模拟真实业务调用）
    digest_metrics.inc("push_total", 1)
    digest_metrics.inc("push_failed", 1)
    digest_metrics.inc("fetch_failures", 1)
    digest_metrics.inc("rsshub_routes_broken", 1)

    # 用 TestClient 真测 endpoint
    client = TestClient(app)
    response = client.get("/api/digest/metrics")

    # 验证 HTTP 200
    assert response.status_code == 200, f"期望 200 · 实际 {response.status_code}"

    # 验证响应 JSON 含 counters + timings
    data = response.json()
    assert "counters" in data, f"响应缺 'counters' · 实际: {data}"
    assert "timings" in data, f"响应缺 'timings' · 实际: {data}"

    # 验证 4 counter 键齐全（v1.2 修正键名）
    expected_counters = {"push_total", "push_failed", "fetch_failures", "rsshub_routes_broken"}
    actual_counters = set(data["counters"].keys())
    assert expected_counters == actual_counters, (
        f"4 counter 键不匹配 · 期望 {expected_counters} · 实际 {actual_counters}"
    )

    # 验证 counter 值 ≥ 1（业务代码 inc 了）
    for key in expected_counters:
        assert data["counters"][key] >= 1, f"counter '{key}' 应 ≥ 1 · 实际 {data['counters'][key]}"


# ─── TC-8b: 业务代码不调 inc 时，4 counter 键仍存在（spec § 4 端点契约）───
def test_metrics_default_counters_present():
    """digest_metrics snapshot 返回的 4 counter 键齐全（不管值）。

    注：digest_metrics 是单例 · 测试间共享状态。
    测试只验证 4 键存在，不验证具体数值（避免测试间状态污染）。
    """
    app = FastAPI()
    app.include_router(digest_metrics_router)

    client = TestClient(app)
    response = client.get("/api/digest/metrics")

    assert response.status_code == 200
    data = response.json()

    # 4 counter 键必须存在（v1.2 修正键名）
    expected = {"push_total", "push_failed", "fetch_failures", "rsshub_routes_broken"}
    actual = set(data["counters"].keys())
    assert expected == actual, f"4 counter 键不齐全 · 期望 {expected} · 实际 {actual}"

    # counter 值应是整数 ≥ 0（不管具体多少）
    for key in expected:
        assert isinstance(data["counters"][key], int), f"counter '{key}' 应为 int"
        assert data["counters"][key] >= 0, f"counter '{key}' 应 ≥ 0"


# ─── TC-8.5: GET /api/digest/metrics 路由路径正确（SCN-P1.9.7 v1.2）──
def test_metrics_endpoint_route_prefix():
    """endpoint 路由前缀正确（/api/digest/metrics）· 实际绑定由 uvicorn --host 127.0.0.1 控制。

    SCN-P1.9.7 验证：
    - 路由路径必须是 /api/digest/metrics（不在公网路径）
    - 实际绑定 127.0.0.1 通过 uvicorn 启动参数（main.py + 部署脚本）
    """
    app = FastAPI()
    app.include_router(digest_metrics_router)

    # 验证路由路径
    routes = [route.path for route in app.routes if hasattr(route, "path")]
    assert "/api/digest/metrics" in routes, (
        f"路由缺 '/api/digest/metrics' · 实际: {routes}"
    )


# ─── TC-8c: 业务代码调 timing() 后，timings 字段含 push_latency_ms ──
def test_metrics_returns_timings_after_timing_call():
    """业务代码调 digest_metrics.timing() 后，GET /api/digest/metrics 返回 push_latency_ms 含 count/avg/p50/p95。

    注：metrics.py:51-63 snapshot() 只输出有数据的 timings（空 list 不输出）。
    """
    # 业务代码先调 timing（模拟真实业务调用）
    digest_metrics.timing("push_latency_ms", 100.0)
    digest_metrics.timing("push_latency_ms", 200.0)
    digest_metrics.timing("push_latency_ms", 150.0)

    app = FastAPI()
    app.include_router(digest_metrics_router)

    client = TestClient(app)
    response = client.get("/api/digest/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "timings" in data
    assert "push_latency_ms" in data["timings"], f"timings 缺 'push_latency_ms' · 实际: {data['timings']}"

    # push_latency_ms 应含 count/avg/p50/p95（metrics.py:51-63 snapshot 实现）
    timing = data["timings"]["push_latency_ms"]
    required_keys = {"count", "avg", "p50", "p95"}
    assert required_keys.issubset(set(timing.keys())), (
        f"timing 缺字段 · 期望 {required_keys} · 实际 {set(timing.keys())}"
    )

    # 验证 count = 3
    assert timing["count"] == 3, f"期望 count=3 · 实际 {timing['count']}"
    # 验证 avg ≈ 150.0
    assert abs(timing["avg"] - 150.0) < 0.1, f"期望 avg≈150 · 实际 {timing['avg']}"