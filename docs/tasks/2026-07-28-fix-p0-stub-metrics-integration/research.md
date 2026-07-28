---
title: Research · P0 stub 修复 · digest_metrics 业务代码接入
date: 2026-07-28
status: v1.0（fix-mini 0 步调研完成 · 等用户确认进入 4 步实施）
type: research
related:
  - [P1-9 retro.md](../../tasks/2026-07-23-refactor-product-foundation/retro.md) — 5 段沉淀（含本任务触发）
  - [P1-9 verify.md](../../tasks/2026-07-23-refactor-product-foundation/verify.md) — L5 staging 端到端验证
  - [metrics.py 接入指南](../../../backend/utils/metrics.py:1-15) — 实现已含接入指南
---

# Research · P0 stub 修复 · digest_metrics 业务代码接入

> **任务理解（用户授权）**：P0 stub 修复 · 把业务代码接入 `digest_metrics.inc()` · 让 L5 staging counter 增量真增
> **路径模式**：fix-mini（0→4→6）· bug 修复类型 · 不写 spec/plan/tasks
> **当前阶段**：0 调研完成 · 等用户确认进入 4 步实施

---

## 0. 任务理解（用户授权确认）

- **用户授权**：用户说"继续 P0 stub 修复"+ 选 "1" = 现在做
- **范围**：4 步接入（业务代码 + 测试 + pytest 真验证 counter 增量）
- **目标**：消除 L5 staging counter 默认 0（业务代码没接 inc）· 让 v1 决策 4「P0 stub 修复」落地

---

## 1. 复现路径

### 1.1 当前状态（dead code）

按 `backend/utils/metrics.py:1-15` docstring：
- `DigestMetrics` 类已实现 `inc()` / `timing()` / `snapshot()`
- **全代码库零调用方**（无 service / handler 触发）
- `tests/utils/test_metrics.py::test_metrics_emits_digest_failure_rate` 在 audit 标"DONE" 但实际**不存在**
- 模块从 `utils/logger.py` 搬出至本文件（T31 决策 1 · commit `acca478` 后续）
- 真实指标集成属决策 4「P0 stub 修复」之后阶段 ← **本任务**

### 1.2 L5 staging 验证（验证不通过）

按 v40-product-foundation verify.md § 4：
- uvicorn 启动后 GET /api/digest/metrics 返回 `{counters: {push_total: 0, push_failed: 0, fetch_failures: 0, rsshub_routes_broken: 0}}`
- 业务代码未调 inc · counter 永远为 0
- L5 staging counter 增量真增无法验证 ⚠️

---

## 2. 影响范围（≥ 3 相关文件）

| 文件 | 当前状态 | 接入方式 |
|---|---|---|
| `backend/utils/metrics.py` | ✅ 已实现 inc / timing / snapshot | 不需要改（已含接入指南） |
| `backend/services/digest_service.py` push_daily() | ❌ 未接 inc | **改**：成功路径 + 失败路径 + fetch 失败累计 |
| `backend/tests/utils/test_metrics.py` | ❌ 不存在 | **新建**：counter 真增断言测试 |

辅助依赖（间接）：
- `backend/api/digest_metrics.py` — 已存在 endpoint（GET /api/digest/metrics · 已测 4/4 PASS）
- `backend/main.py` on_startup — 不需要改（endpoint 已注册）

---

## 3. 根因假设

**根因**：决策 4「P0 stub 修复」未在原始 V4 AI 推送任务中实施 · T19 实施时只建脚手架（commit `96566d8`）· 后续没真正接进 call site

**触发**：v40-product-foundation 任务 T19 L5 staging 端到端验证发现 counter 默认 0（retro § 3.3 记录）

---

## 4. 最近相关改动

按 `git log --oneline backend/utils/metrics.py`：
- T31 决策 1 · commit `acca478`：从 `utils/logger.py` 搬出至 `utils/metrics.py`
- T19 决策（v40-product-foundation 第 19 任务）· commit `374b208` + `aa95de2`：GET /api/digest/metrics endpoint + 4/4 PASS 测试
- v1.2 决策 3（v40-product-foundation 调研偏差修正）：counter 键与 metrics.py:32-37 一致

按 `backend/services/digest_service.py`：
- 主体 push_daily() 在 L918-1096
- L933-941：fetch 阶段 + fetch_failures 累计
- L993-1002：early return（无 selected · 全失败 / 无新动态）
- L1063：await db.commit() 成功
- L1090-1096：成功 return

---

## 5. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 改 push_daily() 影响 digest 推送业务逻辑 | 🔴 P0 | 加 try/except 包住 inc + timing · 失败不影响主流程 |
| 新增测试与现有 stub 测试冲突（41 个 stub · 决策 9） | 🟡 P1 | 先跑 baseline pytest 看基线 · 新测试用 `from utils.metrics import digest_metrics` 直接测不依赖 push_daily |
| timing 调用缺 elapsed_ms 计算 | 🟢 P2 | 在 push_daily 入口记 `start = time.monotonic()` · 出口算 elapsed |
| fetch_failures 累计 vs 1 次 inc | 🟢 P2 | 按 `fetch_failures` 列表长度 inc(by=len) 而非 inc(by=1) |
| conftest.py reset_limiter v40 预存阻断 | 🔴 P0 | 用 `--noconftest` 跑新测试（已验证模式 · T5/T8/T10/T12/T14/T17 都用） |

---

## 6. 6 步路径建议（fix-mini）

按 AGENTS.md § 0.1 fix-mini 路径（0→4→6）：

### 6.1 0 步调研（当前 · 已完成）

- ✅ 任务理解（用户授权）
- ✅ 复现路径（counter 默认 0）
- ✅ 影响范围（push_daily + test_metrics.py）
- ✅ 根因假设（决策 4 未实施）
- ✅ 最近相关改动（metrics.py:1-15 + digest_service.py:918-1096）
- ✅ 风险评估 + 缓解（5 项）
- ✅ 6 步路径建议（本节）

### 6.2 4 步实施（等用户确认 · 估时 30-45 min）

**核心改动**：
1. **改 `backend/services/digest_service.py`**：
   - push_daily() 入口：`start = time.monotonic()`
   - 成功路径（L1090 return 前）：`digest_metrics.inc("push_total")` + `digest_metrics.timing("push_latency_ms", (time.monotonic() - start) * 1000)`
   - 失败路径（L993-1002 early return · 含 fetch_failures）：`digest_metrics.inc("push_failed")`
   - fetch 阶段（L939-941）：`digest_metrics.inc("fetch_failures", by=len(fetch_failures))` 累计
   - try/except 包住所有 inc/timing 调用（不影响主流程）

2. **新建 `backend/tests/utils/test_metrics.py`**：
   - `test_metrics_emits_digest_failure_rate`（按 spec § 4.5 接入指南第 5 步）
   - 测试用 `from utils.metrics import digest_metrics` 直接 inc + snapshot（不依赖 push_daily）
   - 断言 `digest_metrics.inc("push_total", 1)` 后 `digest_metrics.snapshot()["counters"]["push_total"] >= 1`
   - 断言 `digest_metrics.inc("fetch_failures", by=3)` 后 counter +3

3. **跑 pytest 真验证**（counter 真增）：
   ```bash
   cd /Users/wangtianyu/IdeaProjects/KnockWise/backend
   ./.venv/bin/python -m pytest tests/utils/test_metrics.py -v --noconftest --tb=short
   # 期望：测试 PASS + counter 真增断言成立
   ```

4. **跑全量 pytest 看基线**（确认未引入回归）：
   ```bash
   cd /Users/wangtianyu/IdeaProjects/KnockWise/backend
   ./.venv/bin/python -m pytest tests/utils/test_metrics.py -v --tb=short --noconftest
   ```
   - 期望：新测试 PASS · 现有测试不受影响

### 6.3 6 步复盘（估时 15 min · 5 段 retro）

按 § 6.6 retro 5 段：
- 1. 数据（commit / 测试 / 时间）
- 2. 做对（最小 diff · try/except 包住 · 不影响主流程）
- 3. 做错（如果有）
- 4. 改进（实施前探查教训 · 5 次调研偏差沉淀）
- 5. 沉淀（memory feedback）

---

## 7. 决策点（待用户确认）

按 § 一 双 gate · 0 步调研完成 + 等用户确认进入 4 步：

- **D1**：按上述路径直接进入 4 步实施（最小 diff · try/except 包住）
- **D2**：先跑 baseline pytest 看基线（确认无回归风险）再实施
- **D3**：调整接入范围（只接 push_total / push_failed · 不接 timing）

按 § 6.7 实施自校验：writer + verifier 双 agent · 4 步实施后启动 verifier

按 § 6.10 AI Agent Security 4 关：本任务不涉及（无 CI/CD / 密钥 / 网络 / 高权限 · 仅业务代码改动）

---

## 8. 落地追踪

| 维度 | 状态 |
|---|---|
| 0 调研 | ✅ 已完成（research.md v1.0） |
| 4 实施 | 🟡 等用户确认 |
| 6 复盘 | 🟡 4 步后启动 |
| v40 议题状态 | 🔴 已登记 · 仍独立 P0（修复不阻塞） |
| docs/issues.md 同步 | 🟡 实施完更新 |

---

**调研产物已 commit · 等用户确认进入 4 步实施**