---
title: 任务状态语义与传播链 · 任务拆分
type: tasks
step: 3
date: 2026-07-24
status: ✅ closed
tags: [refactor, task-status, tasks]
related:
  - research.md
  - spec.md
  - plan.md
  - decisions.md
---

# 任务拆分 · 任务状态语义与传播链（P0-5）

> refactor-6 · 1 步 spec + 2 步 plan 已落地

---

## 任务总览

- [ ] T1: 模板改动（tasks-template.md § 4 改 5 列 + verify-template.md L5 加 phase_acceptance）— **测试**: 模板渲染 smoke test
- [ ] T2: check_task_state.py 实现（5 不变量 + 12 老任务 legacy 豁免）— **测试**: test_task_state_checker.py 6 场景
- [ ] T3: pre-commit § 4.6 集成（文档改动 + check_task_state.py 串联）— **测试**: pre-commit hook dry-run 4 场景
- [ ] T4: 回归 + verify + retro（check-step.py 不破 + 5 步 verify + 6 步 retro）— **测试**: check-step.py tasks step 全绿 + verify 矩阵 7 场景

**总估时**：~55 min

**依赖关系**：
- T1 依赖：无
- T2 依赖：无
- T3 依赖：T2
- T4 依赖：T1, T2, T3

| ID | 任务 | 估时 | 状态 | 依赖 |
|---|---|---|---|---|
| T1 | 模板改动 (tasks § 4 + verify L5) | 15 min | ✅ DONE | 无 |
| T2 | check_task_state.py 实现 | 20 min | ✅ DONE | 无 |
| T3 | pre-commit 集成 | 5 min | ✅ DONE | T2 |
| T4 | 回归 + verify + retro | 15 min | ✅ DONE | T1-T3 |
| **合计** | | **~55 min** | | |

---

## T1 · 模板改动

### 描述
改 `tasks-template.md` § 4 任务↔测试映射为 5 列表头；改 `verify-template.md` L5 加 phase_acceptance 字段。

### 步骤
1. `docs/templates/tasks-template.md` § 4 改表头 (任务 | 实施 commit | test | verifier | acceptance)
2. `docs/templates/verify-template.md` L5 段加 phase_acceptance 必填

### 估时
15 min

---

## T2 · check_task_state.py 实现

### 描述
新建 `scripts/check_task_state.py` 验证 5 条不变量：
- 三事实必填 (commit + test + verifier)
- FAILED 状态禁止 [x]
- 无 `✅ DONE` 标记
- L5 段必含 phase_acceptance
- 12 老任务豁免 (标 legacy)

### 步骤
1. 创建 `scripts/check_task_state.py` (~150 行)
2. 读 tasks.md 解析
3. 校验 5 条不变量
4. 输出 violation list + exit 0/1

### 估时
20 min

---

## T3 · pre-commit 集成

### 描述
改 `scripts/pre-commit` 加 1 行 case 调用 check_task_state.py。

### 步骤
1. `scripts/pre-commit` 加 case: `*.md → check_task_state.py`
2. 跑 pre-commit → 全绿

### 估时
5 min

---

## T4 · 回归 + verify + retro

### 描述
5 步 verify + 6 步 retro 落地。

### 步骤
1. 跑 `scripts/check-step.py tasks`（不破）
2. 跑 `scripts/check_task_state.py`（5 不变量通过）
3. 12 老任务标 legacy 豁免
4. 写 verify.md
5. 写 retro.md

### 估时
15 min

---

## 任务状态跟踪

| # | 任务 | 状态 | 实施 commit | 实际耗时 | 偏差分析 |
|---|---|---|---|---|---|
| T1 | 模板改动 | ✅ DONE | `ceb3d0a` | ~20 min | +5 min (Edit 失败 1 次, 拆为 3 次 Edit) |
| T2 | check_task_state.py | ✅ DONE | `ceb3d0a` | ~20 min | OK |
| T3 | pre-commit 集成 | ✅ DONE | `8fa464d` | ~5 min | OK |
| T4 | 回归 + verify + retro | ✅ DONE | `8fa464d` | ~10 min | 模板简洁 |
