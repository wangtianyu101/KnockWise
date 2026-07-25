---
title: 任务状态语义与传播链 · 计划
type: plan
step: 2
date: 2026-07-24
status: draft
tags: [refactor, task-status, plan]
related:
  - research.md
  - spec.md
  - decisions.md
---

# 计划 · 任务状态语义与传播链（P0-5）

> 路径模式：refactor-6
> 1 步 spec 已落地 → [`spec.md`](spec.md)

---

## 1. ≥ 2 方案对比

### 方案 A · 模板 + checker 双改（推荐）

- `docs/templates/tasks-template.md` § 4 改 5 列表头
- `docs/templates/verify-template.md` L5 加 phase_acceptance 字段
- 新建 `scripts/check_task_state.py` 校验 5 条不变量
- pre-commit 加 1 行 case

**优**：复用 check-step.py 风格，单一职责
**缺**：3 文件改动 + 新脚本

### 方案 B · 集成到 check-step.py

- check-step.py tasks step 加 5 条新不变量

**优**：单一脚本
**缺**：check-step.py 已 600+ 行；加更多职责混淆边界

### 单一推荐：方案 A

**推荐**: 方案 A

**理由**：
1. check-step.py 已是 6 step 校验，新增状态检查会与现有 tasks 校验混淆
2. 单独脚本 `check_task_state.py` 可独立演进
3. 模板改动是文档层（不改 behavior）
4. pre-commit 1 行 case 集成成本低

**决策点**（用户已确认）：
- 决策 1：选 A 还是 B？→ A（独立脚本）
- 决策 2：12 老任务是否迁移？→ 豁免（标 legacy）
- 决策 3：templates 改 4 列还是 5 列？→ 5 列（任务级三事实 + 阶段 acceptance）

**适用性说明**：
- `product-doc.md`：**不适用**（本任务是流程治理重构，无用户产品层改动）
- `design-spec.md`：**不适用**（本任务不改 UI）

---

## 2. 单一推荐方案详细

### 2.1 文件改动总览

| # | 文件 | 类型 | 增量 |
|---|---|---|---|
| 1 | `docs/templates/tasks-template.md` § 4 | 修改 | +15 行 |
| 2 | `docs/templates/verify-template.md` L5 | 修改 | +10 行 |
| 3 | `scripts/check_task_state.py` | 新建 | ~150 行 |
| 4 | `scripts/pre-commit` | 修改 | +5 行 |
| **合计** | | | **~180 行** |

**估时**：~45 min

---

## 3. 实施步骤

### T1 · 模板改动
1. `tasks-template.md` § 4 改 5 列表头 (任务 | 实施 commit | test | verifier | acceptance)
2. `verify-template.md` L5 段加 phase_acceptance 字段说明

### T2 · check_task_state.py 实现
1. 创建 `scripts/check_task_state.py` 5 条不变量
2. 跑 → 全绿

### T3 · pre-commit 集成
1. `scripts/pre-commit` 加 1 行 case 调用 check_task_state.py

### T4 · 全套回归 + verify + retro
1. 跑 check-step.py tasks step（不破）
2. 跑 check_task_state.py（5 不变量通过）
3. 12 老任务标 legacy，豁免新规
4. 写 verify.md + retro.md

---

## 4. 依赖影响

| 改 A | 影响 B |
|---|---|
| tasks-template.md § 4 改 5 列 | 新任务用 5 列；老任务用 4 列（兼容）|
| verify-template.md L5 加字段 | 未来新任务 verify.md 必填 |
| check_task_state.py 新建 | 独立脚本，与 check-task.py 各自负责 |
| pre-commit +1 行 case | 仅调用，不影响现有 5 自动化 |

---

## 5. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 12 老任务违反新规 | 🟡 | 标 legacy 豁免 |
| check-step.py tasks step 冲突 | 🟢 | 独立 check_task_state.py |
| 模板改动影响未来新任务 | 🟢 | 加段，不删旧 |
| 状态机漏写 | 🟡 | 5 条不变量在 7 个场景测试覆盖 |

---

## 6. 测试矩阵

| Case | 输入 | 期望 |
|---|---|---|
| T1.three_facts_required | 缺任一字段 | violation |
| T1.failed_blocks_x_checkbox | verifier=FAIL + [x] | violation |
| T1.no_naked_done_marker | 含 `✅ DONE` | violation |
| T1.phase_acceptance_required_for_L5 | L5 缺 phase_acceptance | violation |
| T1.legacy_12_tasks_exempt | 12 老任务 | EXEMPT |
| T1.propagation_in_retro | retro 标完成含 FAIL | violation |
| T1.propagation_in_milestones | milestones 用任务计数 | violation |

---

## 7. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 决策：[decisions.md](decisions.md)
- 主账：`docs/issues.md` 决策 #25 · 债务 #13
- 现有：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md` · `check-task.py` (P0-7) · `check-step.py` (P1-2)
