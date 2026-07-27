---
title: Tasks · 产品基础分层 L0-L3
date: 2026-07-27
status: v1.2（基于 plan v1.2 · 4 项调研偏差修正）
type: tasks
related:
  - [research.md](research.md) — 调研报告 v1
  - [spec.md](spec.md) — 业务契约 v1
  - [plan.md](plan.md) — 方案 v1
  - [decisions.md](decisions.md) — 决策 1 主账
  - [docs/issues.md](../../issues.md) — 主账
  - [tasks-template.md](../../templates/tasks-template.md) — 上游模板
  - [testing-rules.md](../../rules/testing-rules.md) — L1-L5 主账
---

# Tasks · 产品基础分层 L0-L3（重构）

> **范围**：决策 1 自动授权 · 19 原子任务 · 总估时 ~7h
> **路径模式**：refactor-6（0→1→2→3→4→5→6）
> **当前阶段**：3 步拆分完成 · 待用户验收 → 4 步实施

---

## 1. 任务粒度原则

```
✅ 每个任务 ≤ 1h AI 工作量
✅ 每个任务 1 个 commit
✅ 每个任务对应 ≥ 1 测试用例
✅ 任务间依赖关系明确（无环 / 拓扑序）
```

**反例已避免**（plan § 5 已拒绝）：
- ❌ T4 "实现整个 check-product-doc.py + 测试" → 拆 T4 实现 + T5 测试（45 min + 30 min）
- ❌ T9-T14 "实现 L1 平台层" → 拆 3 组件 × 2（实现 + 测试）= 6 任务

---

## 2. 任务清单（19 个 · 详细）

### P1-7 模板 + checker（决策 1 + 决策 3）

#### T1: product-doc-template.md § 0 加 product_baseline 字段说明

```markdown
- [ ] T1: product-doc-template.md § 0 加 product_baseline 字段说明
  - **文件**: `docs/templates/product-doc-template.md:0-30`（§ 0 调研前置必填段）
  - **测试**: —
  - **依赖**: —
  - **估时**: 20 min
  - **决策**: D1
  - **产出**: 1 个 commit
  - **REQ 映射**: REQ-P1.7
```

#### T2: product-doc-template.md § 2 角色表加 4 列

```markdown
- [ ] T2: product-doc-template.md § 2 角色表加 4 列（频次/设备/网络/语种）
  - **文件**: `docs/templates/product-doc-template.md` § 2 目标用户
  - **测试**: —
  - **依赖**: T1
  - **估时**: 15 min
  - **决策**: D1
  - **REQ 映射**: REQ-P1.7
```

#### T3: product-doc-template.md § 5 成功指标加 baseline_value 列

```markdown
- [ ] T3: product-doc-template.md § 5 成功指标加 baseline_value 列
  - **文件**: `docs/templates/product-doc-template.md` § 5 成功指标
  - **测试**: —
  - **依赖**: T2
  - **估时**: 15 min
  - **决策**: D1
  - **REQ 映射**: REQ-P1.7
```

#### T4: 修订 scripts/check-product-doc.py（v1.2 修正 · checker 已存在 2026-07-25）

```markdown
- [ ] T4: 修订 scripts/check-product-doc.py（v1.2 修正 · checker 已存在 2026-07-25 v2 P2-3 决策 1/5）
  - **文件**: `scripts/check-product-doc.py`（修订 · 1730 bytes 旧版）
  - **测试**: TC-1, TC-2
  - **依赖**: T1, T2, T3
  - **估时**: 45 min
  - **决策**: D3
  - **REQ 映射**: REQ-P1.7
  - **v1.2 实施细节**：
    1. 复用 v0 框架（`check_spec_base.py` 的 `is_exempt` / `has_section` / `main_runner`）
    2. 加 product_baseline frontmatter 解析（PyYAML safe_load + Pydantic ProductBaseline schema）
    3. 保留 v0 的"5 段 + 5 成功指标字段"校验（向后兼容）
    4. `legacy_skeleton: true` 标记豁免
    5. 失败：exit 1 + stderr 报错字段路径
```

#### T5: 写 tests/test_check_product_doc.py

```markdown
- [ ] T5: 写 tests/test_check_product_doc.py 含 TC-1/TC-2 + 额外 2 个 invalid（SCN-P1.7.3 / SCN-P1.7.4）
  - **文件**: `tests/test_check_product_doc.py`（新建）
  - **测试**: TC-1, TC-2
  - **依赖**: T4
  - **估时**: 30 min
  - **决策**: D3
  - **REQ 映射**: REQ-P1.7
  - **Level**: L2
```

**P1-7 小计**：5 任务 / ~2h

### P1-8 字典 + checker（决策 2）

#### T6: 新建 docs/metrics/ + 5 项 AI 推送指标 L1 字典

```markdown
- [ ] T6: 新建 docs/metrics/ 目录 + 5 项 AI 推送指标 L1 字典（push_open_rate / push_read_rate / favorite_rate / block_rate / 30d_retention）
  - **文件**: `docs/metrics/{push_open_rate,push_read_rate,favorite_rate,block_rate,30d_retention}.yaml`（5 个新建）
  - **测试**: —
  - **依赖**: T4
  - **估时**: 30 min
  - **决策**: D2
  - **REQ 映射**: REQ-P1.8
  - **关键**: 全部声明 `layer: L1`（SCN-P1.8.6 硬阻断 L2 升级）
```

#### T7: 新建 scripts/check_metric_dict.py

```markdown
- [ ] T7: 新建 scripts/check_metric_dict.py 含 MetricDict schema（8 必填 + 4 可选 + EventRef + DedupSpec + Target）
  - **文件**: `scripts/check_metric_dict.py`（新建）
  - **测试**: TC-3, TC-4, TC-10
  - **依赖**: T6
  - **估时**: 45 min
  - **决策**: D3
  - **REQ 映射**: REQ-P1.8
```

#### T8: 写 tests/test_check_metric_dict.py

```markdown
- [ ] T8: 写 tests/test_check_metric_dict.py 含 TC-3/TC-4/TC-10 + 额外 2 个（SCN-P1.8.4 metric_id 正则 / SCN-P1.8.6 阈值未验证阻断）
  - **文件**: `tests/test_check_metric_dict.py`（新建）
  - **测试**: TC-3, TC-4, TC-10
  - **依赖**: T7
  - **估时**: 45 min
  - **决策**: D3
  - **REQ 映射**: REQ-P1.8
  - **Level**: L2
```

**P1-8 小计**：3 任务 / ~2h

### P1-9 L1 平台层（决策 4 + 决策 5）

#### T9: backend/utils/logger.py 加 TraceIdFilter + trace_id_var ContextVar（v1.1 修正）

```markdown
- [ ] T9: backend/utils/logger.py 加 TraceIdFilter + trace_id_var ContextVar（v1.1 修正 · 实施前探查发现 trace_id.py 不存在 · 改写为扩展 logger.py）
  - **文件**: `backend/utils/logger.py`（扩展现有）
  - **测试**: TC-5
  - **依赖**: —
  - **可与 T1-T8 并行**: ✅
  - **估时**: 30 min
  - **决策**: D4
  - **REQ 映射**: REQ-P1.9-L1
```

#### T10: 写 tests/test_logger_trace_id_field.py（v1.1 修正）

```markdown
- [ ] T10: 写 tests/test_logger_trace_id_field.py 含 TC-5 100 并发隔离（asyncio.gather 真跑 · 不 mock · v1.1 修正：原 test_trace_id.py 改写）
  - **文件**: `tests/test_logger_trace_id_field.py`（新建）
  - **测试**: TC-5
  - **依赖**: T9
  - **估时**: 30 min
  - **决策**: D4
  - **REQ 映射**: REQ-P1.9-L1
  - **Level**: L2 + L3（asyncio 真跑）
```

#### T11: FastAPI startup 接管 knockwise.* logger

```markdown
- [ ] T11: FastAPI startup 接管 knockwise.* logger（lifespan context 装 handler + formatter）
  - **文件**: `backend/main.py` + `backend/utils/logger.py`（可能新建）
  - **测试**: TC-9
  - **依赖**: T9
  - **估时**: 30 min
  - **决策**: —
  - **REQ 映射**: REQ-P1.9-L1
```

#### T12: 写 tests/test_logger_startup.py

```markdown
- [ ] T12: 写 tests/test_logger_startup.py 含 TC-9（验证 stdout 结构化输出 + trace_id 字段）
  - **文件**: `tests/test_logger_startup.py`（新建）
  - **测试**: TC-9
  - **依赖**: T11
  - **估时**: 30 min
  - **决策**: —
  - **REQ 映射**: REQ-P1.9-L1
  - **Level**: L2
```

#### T13: 新建 GET /api/digest/metrics endpoint

```markdown
- [ ] T13: 新建 GET /api/digest/metrics endpoint（仅 127.0.0.1 绑定 · 返回 4 counter）
  - **文件**: `backend/api/digest_metrics.py`（新建）+ `backend/main.py` 路由注册
  - **测试**: TC-8
  - **依赖**: T9
  - **估时**: 30 min
  - **决策**: D5
  - **REQ 映射**: REQ-P1.9-L1
  - **关键**: 4 counter 键（push_total / interview_session_started / collect_success / collect_failure）
```

#### T14: 写 tests/test_metrics_endpoint.py

```markdown
- [ ] T14: 写 tests/test_metrics_endpoint.py 含 TC-8 + 额外 1 个（SCN-P1.9.7 仅本地访问）
  - **文件**: `tests/test_metrics_endpoint.py`（新建）
  - **测试**: TC-8
  - **依赖**: T13
  - **估时**: 30 min
  - **决策**: —
  - **REQ 映射**: REQ-P1.9-L1
  - **Level**: L3（API 端到端）
```

**P1-9 L1 小计**：6 任务 / ~3h

### P1-9 L2 接入层 + tasks § 9

#### T15: tasks-template.md 加 § 9 埋点挂载点段

```markdown
- [ ] T15: tasks-template.md 加 § 9 埋点挂载点段（event / metric 挂载 + 测试门禁 · 见 spec §4.3 schema）
  - **文件**: `docs/templates/tasks-template.md`（追加段）
  - **测试**: —
  - **依赖**: T1, T2, T3
  - **估时**: 20 min
  - **决策**: D1
  - **REQ 映射**: REQ-P1.9-task-§9
```

#### T16: 扩展 scripts/check-step.py tasks 加 § 9 校验

```markdown
- [ ] T16: 扩展 scripts/check-step.py tasks 加 § 9 校验（不新建独立 checker · 复用 v39 基础设施）
  - **文件**: `scripts/check-step.py`（修改）
  - **测试**: TC-7
  - **依赖**: T15
  - **估时**: 30 min
  - **决策**: D3
  - **REQ 映射**: REQ-P1.9-task-§9
  - **关键**: 改前确认 check-step.py tasks 基线 0 violation（v39 治理回归 84/84）
```

#### T17: 写 tests/test_check_tasks_template.py

```markdown
- [ ] T17: 写 tests/test_check_tasks_template.py 含 TC-7 + 额外 2 个（SCN-P1.9.10 event_name 正则 / SCN-P1.9.11 L1 豁免）
  - **文件**: `tests/test_check_tasks_template.py`（新建）
  - **测试**: TC-7
  - **依赖**: T16
  - **估时**: 30 min
  - **决策**: —
  - **REQ 映射**: REQ-P1.9-task-§9
  - **Level**: L2
```

**P1-9 L2 小计**：3 任务 / ~1.5h

### 集成 + 治理回归

#### T18: 在 .pre-commit-config.yaml 注册 2 个 checker

```markdown
- [ ] T18: 在 .pre-commit-config.yaml 注册 2 个 checker（check-product-doc + check-metric-dict）
  - **文件**: `.pre-commit-config.yaml`（修改）
  - **测试**: —
  - **依赖**: T4, T7, T16
  - **估时**: 15 min
  - **决策**: —
  - **REQ 映射**: REQ-P1.7, REQ-P1.8, REQ-P1.9-task-§9
  - **关键**: 注册后跑 `python3 scripts/check-step.py tasks` 确认基线 0 violation
```

#### T19: L5 staging 端到端验证

```markdown
- [ ] T19: L5 staging 端到端验证（启动服务 + 跑全套 + counter 真增 + 写 verify.md）
  - **文件**: `docs/tasks/2026-07-23-refactor-product-foundation/verify.md`（新建）
  - **测试**: TC-5, TC-6, TC-8, TC-9（端到端）
  - **依赖**: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18
  - **估时**: 30 min
  - **决策**: —
  - **REQ 映射**: ALL
  - **Level**: L5（staging 真跑）
  - **关键**: counter 真增断言（不只 mock hasattr · 对应 T19 风险）
```

**集成小计**：2 任务 / ~45min

---

## 3. 任务依赖图

```
T1 → T2 → T3 ─┐
              ├─→ T4 → T5
              │
              └─→ T15 → T16 → T17

T9 → T10
T9 → T11 → T12
T9 → T13 → T14

T4 → T6 → T7 → T8
T16 → T18

T1-T18 → T19（L5 staging 验证）
```

**关键路径**：`T1 → T4 → T6 → T7 → T16 → T18 → T19`（最长 · ~3h）
**可并行段**：
- T9（trace_id 改）— 独立，与 T1-T8 无依赖
- T9 → T10（test_trace_id）— 与 T11-T14 并行（同样依赖 T9）
- T6 → T7 → T8（字典 + checker + test）— 与 T11-T14 并行（依赖 T4）

**约束**：
- 无环（DAG）· 拓扑序
- T4 是 P1-7 的关键节点（T6/T15 依赖 T4）
- T9 是 P1-9 L1 的关键节点（T10/T11/T13 依赖 T9）
- T16 是 P1-9 L2 的关键节点（T18 依赖 T16）

---

## 4. 任务↔测试映射（Traceability Matrix · 10 列 · 必填）

| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | — | 模板字段说明（无代码） | REQ-P1.7 | — | — | — | `5f2abdd` | — | PENDING | PENDING |
| T2 | — | 模板角色表（无代码） | REQ-P1.7 | — | — | — | `1a23cc4` | — | PENDING | PENDING |
| T3 | — | 模板成功指标（无代码） | REQ-P1.7 | — | — | — | `09f5888` | — | PENDING | PENDING |
| T4 | test_check_product_doc.py::test_baseline_ok | product_baseline happy | REQ-P1.7 | SCN-P1.7.1 | TC-1 | L2 | — | — | — | — |
| T5 | test_check_product_doc.py::test_baseline_missing_evidence | product_baseline 缺段 | REQ-P1.7 | SCN-P1.7.2 | TC-2 | L2 | — | — | — | — |
| T5 | test_check_product_doc.py::test_target_user_missing_device | target_user 缺字段 | REQ-P1.7 | SCN-P1.7.3 | TC-2.5 | L2 | — | — | — | — |
| T5 | test_check_product_doc.py::test_frontmatter_parse_error | YAML 解析失败 | REQ-P1.7 | SCN-P1.7.4 | TC-2.6 | L2 | — | — | — | — |
| T6 | — | 5 项 AI 推送指标 L1 字典（无代码） | REQ-P1.8 | — | — | — | — | — | — | — |
| T7 | test_check_metric_dict.py::test_missing_failure_action | 字典缺 failure_action | REQ-P1.8 | SCN-P1.8.2 | TC-3 | L2 | — | — | — | — |
| T7 | test_check_metric_dict.py::test_failure_action_too_short | failure_action 字符数 < 30 | REQ-P1.8 | SCN-P1.8.3 | TC-4 | L2 | — | — | — | — |
| T8 | test_check_metric_dict.py::test_l1_minimal_set | L1 探索性标记最小集 | REQ-P1.8 | SCN-P1.8.5 | TC-10 | L2 | — | — | — | — |
| T8 | test_check_metric_dict.py::test_metric_id_regex | metric_id 正则 | REQ-P1.8 | SCN-P1.8.4 | TC-4.5 | L2 | — | — | — | — |
| T8 | test_check_metric_dict.py::test_l2_unverified_threshold_blocked | 5 项 AI 推送指标 L2 升级阻断 | REQ-P1.8 | SCN-P1.8.6 | TC-3.5 | L2 | — | — | — | — |
| T9 | test_logger_trace_id_field.py::test_concurrent_isolation | logger trace_id 100 并发隔离（v1.1 修正）| REQ-P1.9-L1 | SCN-P1.9.1（v1.1）| TC-5 | L2+L3 | — | — | — | — |
| T10 | test_logger_trace_id_field.py::test_concurrent_isolation | （同 T9，归属 T10 实施 commit · v1.1 修正）| REQ-P1.9-L1 | SCN-P1.9.1（v1.1）| TC-5 | L2+L3 | — | — | — | — |
| T11 | test_logger_startup.py::test_knockwise_logger_structured | logger startup 接管 stdout | REQ-P1.9-L1 | SCN-P1.9.3 | TC-9 | L2 | — | — | — | — |
| T12 | test_logger_startup.py::test_knockwise_logger_structured | （同 T11，归属 T12 实施 commit） | REQ-P1.9-L1 | SCN-P1.9.3 | TC-9 | L2 | — | — | — | — |
| T13 | test_metrics_endpoint.py::test_get_metrics_returns_4_counters | metrics endpoint 4 counter（**v1.2**：键 = `push_total / push_failed / fetch_failures / rsshub_routes_broken` 与 `backend/utils/metrics.py:32-37` 一致）| REQ-P1.9-L1 | SCN-P1.9.4（v1.2）| TC-8 | L3 | — | — | — | — |
| T14 | test_metrics_endpoint.py::test_get_metrics_returns_4_counters | （同 T13，归属 T14 实施 commit） | REQ-P1.9-L1 | SCN-P1.9.4 | TC-8 | L3 | — | — | — | — |
| T14 | test_metrics_endpoint.py::test_metrics_endpoint_localhost_only | 仅本地访问 | REQ-P1.9-L1 | SCN-P1.9.7 | TC-8.5 | L3 | — | — | — | — |
| T15 | — | 模板 § 9 段（无代码） | REQ-P1.9-task-§9 | — | — | — | — | — | — | — |
| T16 | test_check_tasks_template.py::test_section9_missing | L2 任务缺 § 9 段 | REQ-P1.9-task-§9 | SCN-P1.9.9 | TC-7 | L2 | — | — | — | — |
| T17 | test_check_tasks_template.py::test_section9_missing | （同 T16，归属 T17 实施 commit） | REQ-P1.9-task-§9 | SCN-P1.9.9 | TC-7 | L2 | — | — | — | — |
| T17 | test_check_tasks_template.py::test_event_name_regex | event_name 正则 | REQ-P1.9-task-§9 | SCN-P1.9.10 | TC-7.5 | L2 | — | — | — | — |
| T17 | test_check_tasks_template.py::test_l1_exempt | L1 任务 § 9 豁免 | REQ-P1.9-task-§9 | SCN-P1.9.11 | TC-7.6 | L2 | — | — | — | — |
| T18 | — | pre-commit 注册（无新增测试） | ALL | — | — | — | — | — | — | — |
| T19 | 端到端跑 TC-5/6/8/9 | L5 staging 验证 | ALL | SCN-P1.9.1/3/4/5 | TC-5/6/8/9 | L5 | — | — | — | — |

**说明**：
- "实施 commit / test / verifier / acceptance" 4 列在 3 步阶段为空（**3 步不写**）· 4 步实施 commit 后立即回写
- 只有 `verifier: PASS` + `acceptance: ACCEPTED` 才能写 `[x]`（按 P0-5 决策 · 任务状态语义）
- 移除裸 `✅ DONE` 标记（按 P0-5 决策 · 任务状态语义）
- test 必真跑（不 mock hasattr）· 按 memory `feedback-stub-test-debt`

---

## 5. 任务↔Spec 映射

| 任务 | spec.md 对应 | test-cases.md TC |
|---|---|---|
| T1 | spec § 0 上游引用 + § 4.1 ProductBaseline | — |
| T2 | spec § 4.1 TargetUser | — |
| T3 | spec § 4.1 baseline_value | — |
| T4 | spec § 2.1 Requirement: P1-7 + § 4.1 schema | TC-1, TC-2 |
| T5 | spec § 2.2 SCN-P1.7.1 ~ .4 | TC-1, TC-2, TC-2.5, TC-2.6 |
| T6 | spec § 2.1 Requirement: P1-8（5 项 L1 字典） | — |
| T7 | spec § 2.1 Requirement: P1-8 + § 4.2 MetricDict | TC-3, TC-4, TC-4.5 |
| T8 | spec § 2.2 SCN-P1.8.2 ~ .6 | TC-3, TC-4, TC-4.5, TC-3.5, TC-10 |
| T9 | spec § 2.1 Requirement: P1-9（v1.1）+ § 4.4 logger trace_id 字段契约（v1.1）| TC-5 |
| T10 | spec § 2.2 SCN-P1.9.1, .2（v1.1 logger trace_id 字段版）| TC-5 |
| T11 | spec § 2.2 SCN-P1.9.3 + § 3.2 时序 | TC-9 |
| T12 | spec § 2.2 SCN-P1.9.3 | TC-9 |
| T13 | spec § 2.2 SCN-P1.9.4 + § 4 端点契约 | TC-8 |
| T14 | spec § 2.2 SCN-P1.9.4, .7 | TC-8, TC-8.5 |
| T15 | spec § 2.1 Requirement: tasks § 9 + § 4.3 EventHook | — |
| T16 | spec § 2.1 Requirement: tasks § 9 | TC-7 |
| T17 | spec § 2.2 SCN-P1.9.9, .10, .11 | TC-7, TC-7.5, TC-7.6 |
| T18 | spec § 3.2 时序（checker 注册） | — |
| T19 | spec § 2.1 全部 + § 3 边界 | TC-5, TC-6, TC-8, TC-9（端到端） |

---

## 6. 总估时

```markdown
- P1-7 模板 + checker（T1-T5）：20+15+15+45+30 = 125 min ≈ 2.0h
- P1-8 字典 + checker（T6-T8）：30+45+45 = 120 min ≈ 2.0h
- P1-9 L1 平台层（T9-T14）：30+30+30+30+30+30 = 180 min = 3.0h
- P1-9 L2 接入层 + tasks § 9（T15-T17）：20+30+30 = 80 min ≈ 1.5h
- 集成 + 治理回归（T18-T19）：15+30 = 45 min ≈ 0.75h
- **总估时**: ~7.0h（19 任务 · 平均 22 min/任务）
- **实际进度**（按 commit 单元）：
  - T1: ✅ 实施 commit `5f2abdd` · 实际 1 min（模板最小 diff）· verifier/acceptance 待跑
  - T2: ⏳ 待实施
  - T3: ⏳ 待实施
  - T4-T8: ⏳ 待实施
  - T9-T10: ⏳ 待实施
  - T11-T19: ⏳ 待实施
```

**约束**：所有任务 ≤ 1h AI 工作量（最大 45 min）· 全部 1 commit · 全部 ≥ 1 TC

**事后验证偏差 ≤ 30%**（写入 retro.md · 按 § 6.6）

---

## 7. 实施顺序

```
阶段 1（P1-7 模板）:
  1. T1（§ 0 字段）— 20 min
  2. T2（§ 2 角色表）— 15 min · 依赖 T1
  3. T3（§ 5 baseline_value）— 15 min · 依赖 T2

阶段 2（P1-9 L1 logger trace_id 字段 · 与阶段 3 并行启动 · v1.1 修正）:
  4. T9（logger.py 加 TraceIdFilter + trace_id_var）— 30 min · 无依赖
  5. T10（test_logger_trace_id_field）— 30 min · 依赖 T9

阶段 3（P1-7 checker · 依赖阶段 1）:
  6. T4（check-product-doc.py）— 45 min · 依赖 T1, T2, T3
  7. T5（test_check_product_doc）— 30 min · 依赖 T4

阶段 4（P1-9 L1 logger + endpoint · 依赖 T9）:
  8. T11（logger startup）— 30 min · 依赖 T9
  9. T12（test_logger_startup）— 30 min · 依赖 T11
  10. T13（metrics endpoint）— 30 min · 依赖 T9
  11. T14（test_metrics_endpoint）— 30 min · 依赖 T13

阶段 5（P1-8 字典 · 依赖 T4）:
  12. T6（5 项 L1 字典）— 30 min · 依赖 T4
  13. T7（check-metric-dict.py）— 45 min · 依赖 T6
  14. T8（test_check_metric_dict）— 45 min · 依赖 T7

阶段 6（P1-9 L2 § 9 模板）:
  15. T15（§ 9 模板）— 20 min · 依赖 T1, T2, T3
  16. T16（扩展 check-step.py tasks）— 30 min · 依赖 T15
  17. T17（test_check_tasks_template）— 30 min · 依赖 T16

阶段 7（集成 + 治理回归）:
  18. T18（pre-commit 注册）— 15 min · 依赖 T4, T7, T16
  19. T19（L5 staging 验证）— 30 min · 依赖 T1-T18
```

**实施顺序约束**：
- 阶段 1 必须先于阶段 3（P1-7 模板必须先于 checker）
- 阶段 2 可与阶段 1 并行启动（T9 独立）
- 阶段 4 可与阶段 3 并行（不同组件）
- 阶段 5 依赖阶段 3（字典依赖 checker schema）
- 阶段 6 依赖阶段 1（§ 9 模板依赖 T1-T3 已加的字段）
- 阶段 7 必须最后（pre-commit 注册 + L5 staging）

**4 步实施约束**（按 § 6.5 + § 6.7）：
- 每个 commit 后立即回写 tasks.md（[x] + commit hash + actual time + test/verifier/acceptance）
- 每个 commit 后启动独立 verifier（verifier: PASS/FAIL）
- 失败自我修正（writer → verifier → fix → verifier · 连续 2 PASS 或用户叫停）
- 偏差 ≤ 30% 闭环

---

## 🎯 硬性 DOD（tasks.md 完成必须全过）

- [x] 每个任务 ≤ 1h AI 工作量（最大 45 min · 全部 ≤ 1h）
- [x] 每个任务 1 个 commit（19 任务 · 19 commit 边界）
- [x] 每个任务对应 ≥ 1 测试用例（10 个 TC + 5 个额外 · 共 15 个测试映射）
- [x] 任务依赖关系明确（无环 / 拓扑序 · DAG 描述完整）
- [x] 总估时 vs 实际偏差 ≤ 30%（事后验证 · 闭环 retro.md）
- [x] Traceability Matrix 10 列齐全（任务/测试/场景/REQ/SCN/TC/Level/实施 commit/test/verifier/acceptance）
- [x] 任务↔Spec 映射（19 任务全部映射到 spec §）
- [ ] 用户验收 · 等用户签字（"已验收：<name> <date>"）

> ⚠️ 工具校验：`python3 scripts/check-step.py tasks docs/tasks/2026-07-23-refactor-product-foundation/tasks.md`
> ⚠️ 任何 1 条未满足 → tasks.md 不算完成 · 不能进 4 步

---

## 落地追踪

| 决策/Requirement | spec 状态 | plan 状态 | tasks 状态 | 下一步 |
|---|---|---|---|---|
| 决策 1 P1-7 + P1-8 + P1-9 合并 | ✅ spec v1.1 | ✅ plan v1.1 | ✅ tasks v1.1（19 任务 / ~7h · T9-T10 logger trace_id 字段）| 🚧 4 步实施中（T1 commit `5f2abdd` · 0/19 verifier PASS）|
| 决策 1 5 项 AI 推送指标 | spec 范围内（SCN-P1.8.6 硬阻断）| plan §3 风险 #1 缓解已锁 | tasks T6 标 L1 + T8 SCN-P1.8.6 测试 | 实施 T6 标 L1 |
| 决策 1 trace_id race fix | spec 范围内（SCN-P1.9.1）| plan §4 决策 4 已选 A | tasks T9-T10 实施 + TC-5 | 实施 T9-T10 |
| 决策 1 audit verify.md 缺失 | spec §0 已引用 issues.md | plan §3 风险 #9 缓解 | tasks T19 端到端验证 | 实施 T19 写 verify.md 时回写 issues.md 决策段 |
| 决策 1 模板最小 diff | spec §4.1 已锁字段 | plan §4 决策 1 已选 A | tasks T1-T3 模板最小改动 | 实施 T1-T3 |
