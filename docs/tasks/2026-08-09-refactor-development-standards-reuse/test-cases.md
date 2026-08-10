---
title: 最小状态语义冲突修复 · 测试用例
type: test-cases
step: 4
date: 2026-08-09
status: in-review
tags: [test-cases, fix-mini, governance]
related:
  - spec.md
  - tasks.md
  - decisions.md
---

# 最小状态语义冲突修复 · 测试用例

## 0. 测试策略

- **自动化覆盖率目标**：本次三个冲突场景 100% 自动化覆盖；未宣称全文件行覆盖率。
- **手测场景**：0；纯静态治理逻辑无 UI。
- **E2E 场景**：1 个生产 CLI subprocess 路径，由聚焦测试真实执行 `check_task_state.py`。
- **回归测试**：治理 Hook/CI、workflow-state reducer 和任务状态 Checker 共 36 项。

## 1. 验收测试

| TC | 场景 | 类型 | 自动化 | 实际结果 |
|---|---|---|---|---|
| TC-001 | `[x] + verifier=FAIL` 保留 implementation 事实 | edge | `test_task_governance_gate.py::test_failed_verifier_keeps_implemented_checkbox` | ✅ PASS |
| TC-002 | 裸 `✅ DONE` 继续被 Checker 阻断 | invalid | `test_task_governance_gate.py::test_naked_done_still_blocks_implemented_checkbox` | ✅ PASS |
| TC-003 | AGENTS/template/Hook 不再给出互相冲突的 active guidance | regression | `test_task_governance_gate.py::test_active_task_status_guidance_uses_orthogonal_facts` | ✅ PASS |

## 2. 自动化测试

| 自动化测试 | 对应 TC | Oracle |
|---|---|---|
| `backend/tests/test_task_governance_gate.py::test_failed_verifier_keeps_implemented_checkbox` | TC-001 | 生产 CLI rc=0；旧实现真实红灯 rc=1 |
| `backend/tests/test_task_governance_gate.py::test_naked_done_still_blocks_implemented_checkbox` | TC-002 | 生产 CLI rc=1 且输出 `task-state-naked-done` |
| `backend/tests/test_task_governance_gate.py::test_active_task_status_guidance_uses_orthogonal_facts` | TC-003 | 三个 active consumer 无旧冲突短语且包含统一语义 |

**场景自动化覆盖率**：3/3 = 100%（目标 ≥80%）。

## 3. 手测场景

- 不适用：无页面、API、数据库或外部服务行为。

## 4. 回归测试

| 旧功能 | 自动化测试 | 结果 |
|---|---|---|
| task state Hook/INDEX/manifest | `backend/tests/test_task_governance_gate.py` | ✅ PASS |
| CI governance diff gate | `backend/tests/test_check_governance.py` | ✅ PASS |
| workflow-state 正交投影 | `backend/tests/test_workflow_state_reducer.py` | ✅ PASS |

合计：`36 passed in 2.49s`；测试质量 `13 tests / 0 violations`。

## 5. 边界 case

- [x] verifier FAIL 不抹掉 implementation checkbox。
- [x] 裸 DONE 仍严格阻断。
- [x] staged/worktree 与 manifest 的既有回归保持通过。
- [ ] EOF checkbox 探测边界：调研中发现，但已明确不在本次最简修复范围。

## 6. Bug 回归测试

- [x] 回归：AGENTS/Hook 要求写被 Checker 禁止的裸 DONE。
- [x] 回归：模板同时声称 `[x]` 依赖 acceptance、又声称只代表 implementation。
- [x] 回归：Checker 把 verifier FAIL 错误解释成 implementation 未发生。

## 7. 当前结论

- L1/L2 工作区测试：✅ PASS。
- 独立 verifier：✅ worktree PASS、偏差 0；⛔ commit identity BLOCKED。
- 固定 implementation commit：尚未创建，因此不能宣称 commit 级验证完成。
