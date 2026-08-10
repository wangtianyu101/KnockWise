---
title: 任务状态语义与传播链 · 规格
type: spec
step: 1
date: 2026-07-24
status: approved
tags: [refactor, task-status, state-machine, propagation]
related:
  - research.md
  - decisions.md
  - ../../templates/tasks-template.md
  - ../../templates/verify-template.md
  - ../../../scripts/check-task.py
---

# 规格 · 任务状态语义与传播链（P0-5）

> 路径模式：refactor-6
> 调研 0 步已落地 → [`research.md`](research.md)
> 决策已拍板 → [`decisions.md`](decisions.md)

---

## 0. 用户故事

**核心目标**：解决 `[x] DONE` 混合实施/测试/验证/用户验收语义问题；建立任务级三事实 + 阶段级 acceptance 状态机；防止 FAILED 任务被标记 DONE 传播。

**用户故事**：作为 KnockWise 维护者，我希望任务追踪能区分"实施 / 测试 / 验证 / 验收"四个独立事实，避免 V4 那种 41 个空壳 + 整体"完成"的传播失真。

**已验收 ✅**：经 4 个独立对抗 Agent 调研 + 用户确认 [research.md 决策 1](research.md#8-用户决策清单)

**边界**：
- 不改业务代码
- 不改 `check-task.py` 任务元数据契
- 不动 P0-7 task.yaml 已落地状态
- 12 个老任务标 `legacy` 不迁移

---

## 1. 验收标准

### Requirement: 任务级三事实 SHALL 必填

每个任务 SHALL 必含 3 个独立事实字段：

```yaml
implementation:
  commit: <hash | null>            # 实际落地 commit
  test: PASS | FAIL | NOT_RUN | N/A  # L1/L2 测试结果
  verifier: PASS | FAIL | NOT_RUN | BLOCKED  # 独立 verifier 结果
```

中间状态保留（`[ ]` + 三事实 NOT_RUN/PASS/FAIL）。
只有 `verifier: PASS` 才能写 `[x]`。

### Requirement: 阶段级 acceptance SHALL 走 PENDING/ACCEPTED/REJECTED

```yaml
phase_acceptance: PENDING | ACCEPTED | REJECTED
```

只有 `phase_acceptance: ACCEPTED` 才能进 verify.md 的 L5 段。

### Requirement: `[x]` SHALL 与裸 DONE 标记互斥

- 移除 `✅ DONE` 标记（曾用：`- [x] T1: ✅ DONE — commit hash`）
- `[x]` 仅表示 implementation 已落 commit
- `[x]` 可与 test=FAIL 或 verifier=FAIL 共存；失败不否认 implementation 已发生
- checker 只阻断裸 `✅ DONE` 及错误的阶段完成传播，不把 implementation checkbox 当测试或验收事实

### Requirement: tasks.md § 4 任务↔测试映射 SHALL 三事实表

按实施时三事实更新 § 4 表：

```markdown
| 任务 | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|
| T1 | `abc1234` | PASS | PASS | ACCEPTED |
| T2 | `def5678` | FAIL | PENDING | PENDING |
```

### Requirement: verify.md L5 段 SHALL 含 phase_acceptance

verify.md L5 staging 段必含：
- phase_acceptance 状态
- 失败任务必含 `failure_action`（下一步动作）
- 不能"🟢 可进入 6 步"但 verifier: FAIL

### Requirement: 传播链 SHALL 阻断 FAILED → 完成

- retro.md SHALL NOT 把 `phase_acceptance: PENDING` 任务标 "实施完成"
- milestones.md SHALL NOT 以"任务计数"判断完成
- issues.md 决策段 SHALL NOT 关闭含 FAIL 任务的议题

### Requirement: 模板 SHALL 升级

`docs/templates/tasks-template.md` § 4 SHALL 改为三事实表。
`docs/templates/verify-template.md` L5 段 SHALL 加 acceptance 字段。

### Requirement: 12 老任务 SHALL 豁免

12 个 2026-07 老任务标 `legacy` 状态，豁免新规。
新规只对 2026-07-24 起新任务生效。

---

## 2. 边界条件

#### Scenario: 任务级三事实 happy path
**Given** 实施完一个任务，commit hash 已知
**When** 写 tasks.md
**Then** 必含 implementation.commit + test + verifier 3 字段

#### Scenario: FAILED 保留 implementation checkbox (edge)
**Given** 一个任务 verifier=FAIL
**When** 写 tasks.md
**Then** 已有 implementation commit 时仍可写 `[x]`
**And** verifier 独立保留 `FAIL`
**And** phase_acceptance 保持 `PENDING` 或 `REJECTED`

#### Scenario: 裸 DONE 移除 (edge)
**Given** 任意 tasks.md
**When** 含 `✅ DONE` 标记
**Then** 报 violation

#### Scenario: phase_acceptance 必填 (happy)
**Given** 任务全部 PASS verifier
**When** 写 verify.md L5
**Then** phase_acceptance 必含 ACCEPTED 才标 "🟢 可进入 6 步"

#### Scenario: FAILED 阻断里程碑 (failure)
**Given** verifier=FAIL 任务
**When** 写 retro.md
**Then** 不得标 "实施完成"
**When** 写 milestones.md
**Then** 不得以"任务计数"判断完成
**When** 写 issues.md
**Then** 不得关闭含 FAIL 任务的议题

#### Scenario: 老任务豁免 (legacy)
**Given** 12 个 2026-07 老任务目录
**When** checker 跑
**Then** 豁免新规（标 legacy 兼容）

#### Scenario: 不破现有契 (regression)
**Given** P0-7 task.yaml schema 已落地
**When** 实施新规
**Then** task.yaml schema 不变
**And** 12 个老任务的 current 状态不动
**And** check-task.py 6 step validator 不破

---

## 3. 数据契约

### 3.1 任务级三事实 Pydantic Schema

```python
from pydantic import BaseModel
from typing import Optional, Literal

class TaskThreeFacts(BaseModel):
    commit: Optional[str] = None
    test: Literal["PASS", "FAIL", "NOT_RUN", "N/A"] = "NOT_RUN"
    verifier: Literal["PASS", "FAIL", "NOT_RUN", "BLOCKED"] = "NOT_RUN"

class PhaseAcceptance(BaseModel):
    phase_acceptance: Literal["PENDING", "ACCEPTED", "REJECTED"] = "PENDING"
    failure_action: Optional[str] = None
```

```yaml
implementation:
  commit: <hash | null>
  test: PASS | FAIL | NOT_RUN | N/A
  verifier: PASS | FAIL | NOT_RUN | BLOCKED
phase_acceptance: PENDING | ACCEPTED | REJECTED
failure_action: <next-step> | null
```

### 3.2 任务↔测试映射表（§ 4）

```markdown
| 任务 | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|
| T1 | `abc1234` | PASS | PASS | ACCEPTED |
```

---

## 4. 边界与非目标

- 不动 P0-7 task.yaml schema
- 不迁移 12 个老任务
- 不改业务代码
- 不引入新工具
- 不改 `check-task.py` 已落地的 8 error code

---

## 5. 与现有机制关系

| 文件 | 角色 | 关系 |
|---|---|---|
| tasks-template.md § 4 | 现有任务↔测试映射 | 改 4 列表头为 5 列 |
| verify-template.md L5 | 现有 L5 staging 段 | 加 phase_acceptance 字段 |
| check-task.py | 任务元数据契 | 不重叠 · 三事实在 tasks.md 内部，不在 task.yaml |
| check-step.py tasks | 任务清单校验 | 兼容 · 三事实为额外 metadata，不替代 checklist |

---

## 5. 测试用例 / 测试场景

- TC-1: `test_three_facts_required` — 任务级三事实 schema 必填
- TC-2: `test_failed_verifier_keeps_implemented_checkbox` — FAILED 不抹掉 implementation [x]
- TC-3: `test_no_naked_done_marker` — 裸 DONE 标记移除
- TC-4: `test_phase_acceptance_required_for_L5` — L5 段必含 phase_acceptance
- TC-5: `test_legacy_12_tasks_exempt` — 12 老任务豁免
- TC-6: `test_propagation_constraints_in_retro_milestones` — 传播链约束

```python
# backend/tests/test_task_state_checker.py
def test_three_facts_required(): ...
def test_failed_verifier_keeps_implemented_checkbox(): ...
def test_no_naked_done_marker(): ...
def test_phase_acceptance_required_for_L5(): ...
def test_legacy_12_tasks_exempt(): ...
def test_propagation_constraints_in_retro_milestones(): ...
```

---

## 7. 实施约束

1. 先写失败 pytest → 红
2. 写实现 → 绿
3. 老 12 个任务标 `legacy_status: pre-p0-5` 不迁移
4. 模板改动加段，不删旧字段

---

## 8. 关联文档

- 调研：[research.md](research.md)
- 决策：[decisions.md](decisions.md)
- 主账：`docs/issues.md` 决策 #25 · 债务 #13
- 公共规则：`AGENTS.md` § 6.5
- 现有机制：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md` · `check-task.py` (P0-7)
