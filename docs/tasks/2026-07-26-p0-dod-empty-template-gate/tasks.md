---
title: P0 空模板 DOD Gate · 实施任务
type: tasks
step: 4
date: 2026-07-26
status: implemented_verifier_pass_acceptance_pending
tags: [p0, dod, regression]
related: [research.md, decisions.md, test-cases.md]
---

# P0 空模板 DOD Gate · 实施任务

> 路径模式：`timebox`。用户未要求 commit，产出先保留在 worktree。

## 1. 任务清单

- [ ] T1: 增加共享模板残留 Gate 和回归测试
  - **文件**: `scripts/check-step.py`, `backend/tests/test_check_step.py`
  - **测试**: `backend/tests/test_check_step.py`
  - **依赖**: —
  - **估时**: 45 min
  - **实际**: 34 min
  - **产出**: 1 个实施边界；不擅自 commit

## 2. 任务依赖

T1 为单一原子任务，无前置依赖、无环。

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| 任务 T1 | `test_check_step.py::TestTemplateResidueGate` | 空模板非零、合法边界不误伤 | REQ-001 | SCN-001 | TC-001~005 | L2 | worktree | PASS | PASS | PENDING |

## 4. 总估时

- T1：45 min
- **总估时**：45 min
- **实际耗时**：34 min
- **偏差**：-24.4%

## 5. 实施顺序

1. 增加真实模板负例，确认 RED。
2. 增加共享前置 Gate，确认 GREEN。
3. 跑 checker、Hook 相关回归、测试质量。
4. 独立 verifier 复验并回写状态。

## 6. TDD 与验证记录

| 轮次 | 命令 / 范围 | 结果 | 说明 |
|---|---|---|---|
| RED | `pytest tests/test_check_step.py::TestTemplateResidueGate -q` | 7 failed, 6 passed | 五类模板、改名模板、CLI 原因均假绿 |
| GREEN | 同一目标 | 13 passed | 首版共享 Gate 生效 |
| 边界 RED | `test_document_about_empty_templates_is_not_itself_a_template` | 1 failed | “空模板问题”标题被宽泛误伤 |
| 边界 GREEN | `TestTemplateResidueGate` | 14 passed | 标题识别收紧为标准模板标题 |
| 回归 | 7 个治理测试文件 | 77 passed | checker/Hook/CI 契约全绿 |
| Harness | `check_test_quality.py` | 68 tests, 0 violations | 新测试有真实 oracle |
| verifier-1 | 独立上下文：测试 + CLI + 2 个对抗样本 + 安全审查 | PASS | 77/77；模板 rc=1，合法 angle bracket rc=0 |

## 7. 任务状态

- implementation：worktree（未 commit）
- test：PASS（77/77）
- verifier：PASS
- acceptance：PENDING
