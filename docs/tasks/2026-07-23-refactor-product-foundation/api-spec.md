---
title: API Spec · P1-9 L1 metrics endpoint
date: 2026-07-27
status: v1.1
type: api-spec
related:
  - [spec.md](spec.md) — 业务契约 v1.1
  - [plan.md](plan.md) — 方案 v1.1
  - [tasks.md](tasks.md) — 任务拆分 v1.1
  - [api-spec-template.md](../../templates/api-spec-template.md) — 上游模板
---

# API Spec · GET /api/digest/metrics（L1 平台层基础设施）

> **范围**：决策 1 P1-9 L1 平台层 · 1 个 endpoint
> **路径模式**：refactor-6 · 2 步技术详细化
> **对应 spec SCN**：SCN-P1.9.4（4 counter 齐全）+ SCN-P1.9.7（仅本地访问）

---

## 1. 接口清单

| Method | Path | 作用 | 认证 | 暴露范围 |
|---|---|---|---|---|
| `GET` | `/api/digest/metrics` | 返回 `digest_metrics.snapshot()` 当前状态（counters + timings） | ❌ 无（本地基础设施）| ✅ 仅 `127.0.0.1`（SCN-P1.9.7）|

---

## 2. 详细定义

### GET /api/digest/metrics

#### Request

**Headers**：
```
Host: 127.0.0.1:<port>
```

**Query / Body**：无

**认证**：❌ 无（本地基础设施 · 决策 5 · spec SCN-P1.9.7）

**绑定**：`127.0.0.1:<port>`（**不**绑 `0.0.0.0` · 外部访问 connection refused）

#### Response

**成功 (200)**：
```json
{
  "counters": {
    "push_total": 0,
    "push_failed": 0,
    "fetch_failures": 0,
    "rsshub_routes_broken": 0
  },
  "timings": {
    "push_latency_ms": {
      "count": 0,
      "avg": 0.0,
      "p50": 0.0,
      "p95": 0.0
    }
  }
}
```

**Schema**：
```python
class MetricsResponse(BaseModel):
    counters: dict[str, int] = Field(
        description="4 counter 键（push_total / push_failed / fetch_failures / rsshub_routes_broken）"
    )
    timings: dict[str, TimingStats] = Field(default_factory=dict)

class TimingStats(BaseModel):
    count: int = Field(ge=0)
    avg: float
    p50: float
    p95: float
```

**错误码**：
- 不适用（本地 endpoint · 无认证 · 无业务错误）

#### 实现要点

1. **直接调用** `digest_metrics.snapshot()`（[`backend/utils/metrics.py:51-63`](../../../backend/utils/metrics.py)）
2. **绑定** `uvicorn` 启动参数 `--host 127.0.0.1`（**不** `0.0.0.0`）
3. **路由注册**：`backend/main.py` `app.include_router(metrics_router)` 在 startup 期间
4. **测试**：`tests/test_metrics_endpoint.py::test_get_metrics_returns_4_counters`（TC-8）+ `test_metrics_endpoint_localhost_only`（TC-8.5）
5. **数据来源**：`DigestMetrics` 类实例（`metrics.py:13-49`）— 业务代码调 `digest_metrics.inc(key)` / `timing(key, ms)` 累计

#### 副作用

- **DB**：无
- **Cache**：无
- **Event**：无（只读 endpoint · 不修改状态）
- **副作用路径**：业务代码调 `digest_metrics.inc("push_total")` → `counters["push_total"] += 1` → 下次 `GET /api/digest/metrics` 看到新值

---

## 3. 边界

### 3.1 失败模式

| 场景 | 行为 | 测试 |
|---|---|---|
| 外部访问（`0.0.0.0`）| connection refused（端口未绑定）| TC-8.5 |
| 进程未启动 | connection refused | 集成测试 |
| `digest_metrics` 未初始化 | 500 Internal Server Error（防御性 fallback 返回 0）| — |
| 并发 100 请求 | 全部 200（counter snapshot 是原子读）| 性能测试（非必填）|

### 3.2 时序

- `digest_metrics` 必须在 `app.include_router(metrics_router)` **之前** 初始化（单例）
- T13（endpoint 实施）依赖 T9（logger trace_id 字段 · 跨请求隔离，间接影响 endpoint 日志注入 trace_id）

### 3.3 安全

- ✅ 不暴露公网（`127.0.0.1` only）
- ✅ 无认证（本地基础设施）
- ✅ 无 CORS 配置（浏览器不可达）
- ✅ 无 secrets 暴露
- ⚠️ 不放任何 PII（counter 键是业务名 · 数值是累计计数 · 无用户标识）

### 3.4 性能

- P95 < 50ms（不阻塞主路径）
- `digest_metrics.snapshot()` 是 dict 复制 · O(n) · n = counter 键数（4）+ timing 键数（1）= 5

### 3.5 兼容性

- v1 暂不锁版本号（`/api/digest/metrics` 稳定）
- 后续可加 `/api/v1/digest/metrics` 不破坏兼容

### 3.6 国际化

- N/A（数值接口 · 无文案）

---

## 4. 实施检查清单

- [x] 路径定义（`/api/digest/metrics`）
- [x] 方法定义（`GET`）
- [x] 请求 schema（无 body · 无 query）
- [x] 响应 schema（`MetricsResponse` 含 counters + timings）
- [x] 错误码（N/A · 本地 endpoint）
- [x] 认证（N/A · 本地）
- [x] 暴露范围（`127.0.0.1` only · SCN-P1.9.7）
- [x] 副作用（无）
- [x] 测试映射（TC-8 + TC-8.5）
- [ ] 实施：T13（endpoint 代码）+ T14（测试）

---

## 落地追踪

| 决策/Requirement | api-spec 状态 | 下一步 |
|---|---|---|
| 决策 1 P1-9 L1 metrics endpoint | ✅ api-spec v1.1 写完 | 4 步 T13 实施 + T14 测试 |
| spec SCN-P1.9.4（4 counter 齐全）| Response schema 已含 4 counter | T14 test_get_metrics_returns_4_counters |
| spec SCN-P1.9.7（仅本地）| § 2 绑定 `127.0.0.1` 明确 | T13 uvicorn --host 127.0.0.1 + T14 test_localhost_only |
| spec SCN-P1.9.5（counter 真增断言）| § 2 副作用路径 | T6 实施后业务代码调 inc → T14 端到端断言 |
