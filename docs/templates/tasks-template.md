---
title: 任务拆分模板（tasks / 实施文档·细化）
date: 2026-06-30
status: v1
tags: [tasks, 3步, 实施, 模板]
related:
  - [plan-template.md](plan-template.md) — 上游：方案
  - [test-cases-template.md](test-cases-template.md) — 下游：测试
---

# 任务拆分模板（tasks.md / 实施文档·细化）

> **一句话**：把 plan 拆成原子任务，每个 ≤ 1h AI 工作量，1 个 commit——**实施指南**。
>
> **产出时机**：3 步拆分阶段（任何实现都必填）。
>
> **作者**：**AI 主导**（人 review 粒度）。
>
> **对应 DOD**：见 `docs/DOD.md` §五（5 条）。

---

## 1. 任务粒度原则（必填）

```
✅ 每个任务 ≤ 1h AI 工作量
✅ 每个任务 1 个 commit
✅ 每个任务对应 ≥ 1 测试用例
✅ 任务间依赖关系明确（无环 / 拓扑序）
```

**反例**（粒度太粗）：
- ❌ T1: 实现整个订阅功能（4h）
- ❌ T2: 写所有测试（2h）

**正例**（粒度细）：
- ✅ T1: 建 users_push_subscription 表（30min）
- ✅ T2: 写 SubscribeRequest schema（30min）
- ✅ T3: 写 POST /subscribe endpoint（45min）
- ✅ T4: 写 test_subscribe.py happy path（30min）

---

## 2. 任务清单（必填）

### T1: <具体动作>

```markdown
- [ ] T1: <具体动作>
  - **文件**: `<file>:<line>` 或 `<file>.py`
  - **测试**: `<test_file>.py::test_<name>`
  - **依赖**: —
  - **估时**: 30 min
  - **产出**: 1 个 commit
```

### T2: <具体动作>

```markdown
- [ ] T2: <具体动作>
  - **文件**: `<file>:<line>`
  - **测试**: `<test>.py::test_<name>`
  - **依赖**: T1
  - **估时**: 30 min
```

### T3: <具体动作>

（同上结构）

---

## 3. 任务依赖图（必填）

```
T1 ──→ T2 ──→ T3
              ↓
              T4
```

或更复杂：

```
T1 ──→ T2 ──→ T4 ──→ T5
T1 ──→ T3 ──→ T4

T1 是起点，必须先做
T4 依赖 T2 和 T3
T5 依赖 T4
```

**约束**：
- 无环（DAG）
- 拓扑序（依赖关系明确）
- 并行任务标"可并行"

---

## 4. 任务↔测试映射（必填 · 含 Traceability ID per P1-2）

```markdown
| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|
| T1 | test_db.py::test_create_table | 建表成功 | REQ-001 | SCN-001 | TC-001 | L1 | `abc1234` | PASS | PASS | ACCEPTED |
| T2 | test_schema.py::test_subscribe_request | schema 校验 | REQ-002 | SCN-002 | TC-002 | L1 | `def5678` | PASS | PENDING | PENDING |
| T3 | test_api.py::test_post_subscribe | POST /subscribe happy | REQ-003 | SCN-003 | TC-003 | L3 | — | FAIL | FAIL | REJECTED |
| T4 | test_api.py::test_post_subscribe_error | POST /subscribe error | REQ-003 | SCN-004 | TC-004 | L3 | — | NOT_RUN | NOT_RUN | PENDING |
```

**每个任务至少 1 个测试**（TDD 强制）。**Level 列必填**，与 `docs/rules/testing-rules.md` § 6.5.1 L1-L5 主账对齐。**REQ/SCN/TC 列必填**，与 verify.md § 0.4 Traceability Matrix 10 列对齐。**最后 4 列（实施 commit / test / verifier / acceptance）按 P0-5 决策**：三事实（implementation / test / verifier）+ phase_acceptance 必填；`[x]` 只表示 implementation 已落入 commit，可与 test/verifier `FAIL` 共存，test/verifier/acceptance 分别记录独立事实。**禁止裸 `✅ DONE` 标记**；阶段是否完成只由 phase acceptance 与 workflow-state 投影决定。

---

## 5. 任务↔Spec 映射（必填）

```markdown
| 任务 | spec.md 对应 | test-cases.md TC |
|---|---|---|
| T1 | db-design §2 users_push_subscription | — |
| T2 | spec.md §4 SubscribeRequest | TC-1 |
| T3 | api-spec §2 POST /subscribe | TC-1, TC-2 |
| T4 | spec.md §3 边界 + api-spec §2 错误码 | TC-3 |
```

---

## 6. 总估时（必填）

```markdown
- T1: 30 min
- T2: 30 min
- T3: 45 min
- T4: 30 min
- ...
- **总估时**: <X> 小时

（事后验证偏差 ≤ 30%，写入 retro.md）
```

---

## 7. 实施顺序（必填）

```
1. T1（建表）
2. T2（schema）— 必须先于 T3
3. T3（endpoint）— 可与 T2 并行做了一半
4. T4（错误处理）
5. T5（端到端测试）
```

---

## 🎯 硬性 DOD（tasks.md 完成必须全过）

- [ ] 每个任务 ≤ 1h AI 工作量（粒度约束）
- [ ] 每个任务 1 个 commit（不混合多任务）
- [ ] 每个任务对应 ≥ 1 测试用例（来自 spec §5）
- [ ] 任务依赖关系明确（无环 / 拓扑序）
- [ ] 总估时 vs 实际偏差 ≤ 30%（事后验证，闭环）

> ⚠️ 任何 1 条未满足 → tasks.md 不算完成
> ⚠️ 工具校验：`python3 scripts/check-step.py tasks <file>`

---

## 9. 埋点挂载点（涉及事件 / 指标时必填 · P1-9 L2 § 9 治理）

> **用途**：把"产品功能任务"与"埋点事件 / 指标"绑定，避免审计 9 任务全无埋点（research § 2.3）。
>
> **触发条件**：L1 / L2 / L3 任务（产品功能任务）· L0 内部任务豁免
>
> **关联 Spec**：[`spec.md § 2.2 SCN-P1.9.9 ~ SCN-P1.9.11`](../tasks/) + [`spec.md § 4.3 EventHook schema`](../tasks/)
>
> **校验**：`scripts/check-step.py tasks <file>` · L2 任务缺 § 9 → exit 1

### 9.1 事件挂载（event / trigger / data fields）

| 任务 | event_name | trigger 位置（file:line） | data fields |
|---|---|---|---|
| T1 | interview.session_started | services/interview_service.py start() | session_id, user_id, round |
| T6 | push.delivered | backend/services/digest_service.py push_daily() | user_id, push_id, content_type |
| T7 | push.opened | frontend/components/AIRecommendationCard.tsx onClick | user_id, push_id, open_source |

### 9.2 指标挂载（metric / counter）

| 任务 | counter_name | inc 调用位置 | 关联 digest_metrics |
|---|---|---|---|
| T6 | push_total | backend/services/digest_service.py push_daily() success path | backend/utils/metrics.py:21-25 |
| T7 | push_opened_total | frontend/components/AIRecommendationCard.tsx onClick handler | backend/utils/metrics.py:21-25 |
| T6 | push_failed | backend/services/digest_service.py push_daily() failure path | backend/utils/metrics.py:21-25 |
| T6 | fetch_failures | backend/services/rss_service.py fetch() exception handler | backend/utils/metrics.py:21-25 |

### 9.3 测试门禁（counter 真增断言）

- [ ] 单测断言 `digest_metrics.inc("push_total") == 1`（不只 mock `hasattr`）
- [ ] L5 staging 启动服务真跑 + counter 增量真断言
- [ ] tasks.md § 6.5 commit 后回写 + events 表格同步

**事件命名规范**：`[domain].[action]` 小写 + 下划线 + 点分隔（regex `^[a-z][a-z0-9_.]{2,50}$`）
**L1 豁免**：纯内部 / 一次性任务（如重构 / 文档）豁免 § 9

---

## 📚 相关文档

- [plan-template.md](plan-template.md) — 上游：方案文档
- [test-cases-template.md](test-cases-template.md) — 下游：4 步整合
- `docs/DOD.md` §五 — 3 步拆分 DOD 完整定义
