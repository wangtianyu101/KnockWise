---
title: 最小状态语义冲突修复 · 实施追踪
type: tasks
step: 4
date: 2026-08-09
status: in-review
tags: [fix-mini, governance, task-state]
related:
  - research.md
  - spec.md
  - decisions.md
  - test-cases.md
---

# 最小状态语义冲突修复 · 实施追踪

layer: L1

> 路径：`fix-mini`。用户选择最简快速修复，跳过完整 policy registry；本文件只追踪一个原子工作区修复。

## 1. 上游与范围

- 决策：[`decisions.md`](decisions.md) D-003。
- 规格修订：[`spec.md`](spec.md) 2026-08-09 最简修订。
- 不实施：`.governance/policies.yaml`、policyctl、adapter 生成器、CI 新 job、债务 23 状态机修改。

## 2. 原子任务

- [x] T1: 统一 `[x]` / FAIL / 裸 DONE 的 active consumer 语义（实现已进入 commit）
  - **估时**: 1h
  - **依赖**: 无；基于债务 23 T19 commit `14df732`
  - **对应 commit**: `99dde16cc24ae3e41687b01d383e839e9d77165c`
  - **对应测试**: `backend/tests/test_task_governance_gate.py` 三个回归 + 治理相关 36 项回归
  - **文件**: `AGENTS.md`、tasks template、pre-commit、state checker、旧状态 spec 勘误、回归测试

## 3. 任务状态事实

| 任务 | 自动化测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_task_governance_gate.py` | 正交状态语义与 active guidance | REQ-MIN-1 | SCN-MIN-1 | TC-001/003 | L1 | `99dde16` | PASS | PASS（`818f08f`） | PENDING |

## 4. 实施证据

- TDD 红灯：`test_failed_verifier_keeps_implemented_checkbox` 在旧 Checker 下 `1 failed, 1 passed`，错误码 `task-state-failed-blocks-x`。
- 最小绿灯：新增三个聚焦回归 `3 passed`。
- 治理回归：`test_task_governance_gate.py + test_check_governance.py + test_workflow_state_reducer.py` 共 `36 passed`。
- 测试质量：13 tests，0 violations。
- 独立 verifier：固定 commit `99dde16` 首轮实现语义与 36 项测试 PASS，但因主账文档漂移整体 FAIL；修复提交 `818f08f` 经第二轮固定 commit verifier PASS，偏差 0，36 项测试 PASS。

## 5. 总估时与实际

- **总估时**：1h。
- **当前实际耗时**：约 35 min。
- **偏差**：首次 fixture 位于 EOF，撞到既有 checker 边界导致假绿；补尾行后正确复现红灯。EOF 边界不夹带修复。

## 6. Commit 历史

| Task | commit | 状态 | 说明 |
|---|---|---|---|
| Task T1 | `99dde16` | ✅ 已实施 | 最小语义修复；pre-commit 全量后端 `1081 passed` |
| Task T1 evidence fix | `818f08f` | ✅ 已验证 | 首轮主账漂移修正；第二轮固定 commit verifier PASS |

## 7. 当前 Gate

- implementation worktree：✅ 已完成。
- implementation commit：✅ `99dde16cc24ae3e41687b01d383e839e9d77165c`。
- test：✅ PASS。
- independent verifier：✅ `818f08f` 第二轮固定 commit PASS；36 passed，13 tests / 0 violations，tasks/implement/state checks PASS。
- user acceptance：⏳ PENDING。
