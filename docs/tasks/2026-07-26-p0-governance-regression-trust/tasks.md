---
title: P0 治理回归可信度 · 实施任务
type: tasks
step: 4
date: 2026-07-26
status: implementation_complete_acceptance_pending
tags: [p0, governance, regression]
related: [research.md, decisions.md, test-cases.md]
---

# P0 治理回归可信度 · 实施任务

> 路径模式：`timebox`。用户于 2026-07-27 要求提交，实施已落入 commit `f1cf815`。

## 任务清单

- [x] T1: 建立 `check-task.py` 黑盒 CLI/退出码回归
  - **文件**: `backend/tests/test_check_task.py`
  - **测试**: 合法 rc=0、校验失败 rc=1、缺 manifest rc=2、错误调用 rc=3
  - **依赖**: —
  - **估时**: 25 min
  - **实际**: 12 min
  - **产出**: commit `f1cf815` · 6/6 CLI 专项 PASS

- [x] T2: 建立 Git INDEX/worktree 对抗回归
  - **文件**: `backend/tests/test_check_task.py`, `backend/tests/test_task_governance_gate.py`
  - **测试**: staged 合法不受 worktree 非法影响；staged 缺失不被 worktree 文件救活
  - **依赖**: T1
  - **估时**: 20 min
  - **实际**: 8 min
  - **产出**: commit `f1cf815` · staged/worktree 对抗 PASS

- [x] T3: 明确 CI 静态接线与共享 CLI 行为证据边界
  - **文件**: `backend/tests/test_ci_workflow.py`, `backend/tests/test_check_governance.py`
  - **测试**: workflow 只验证权限/接线；好坏 commit 由真实 CLI E2E 验证
  - **依赖**: T1
  - **估时**: 20 min
  - **实际**: 7 min
  - **产出**: commit `f1cf815` · 真实 commit/CLI E2E PASS

## 任务↔测试映射

| 任务 | 自动化测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_check_task.py` | CLI rc 分类 | REQ-001 | SCN-001 | TC-001~004 | L2 | `f1cf815` | PASS | PASS | PENDING |
| T2 | `test_check_task.py` | INDEX 对抗 | REQ-002 | SCN-002 | TC-005~006 | L2 | `f1cf815` | PASS | PASS | PENDING |
| T3 | `test_check_governance.py` | CI 共享入口行为 | REQ-003 | SCN-003 | TC-007~008 | L3 | `f1cf815` | PASS | PASS | PENDING |

## 依赖与估时

```text
T1 ──→ T2
 └──→ T3
```

- 总估时：65 min。
- 实际：27 min；比估时少 38 min（复用已有临时 Git 基座）。

## 验证轮次

| 轮次 | 范围 | 结果 | 偏差与修复 |
|---|---|---|---|
| writer-1 | 新增 CLI rc 0/1/2/3 + INDEX 对抗 | FAIL（3） | 缺 manifest 实际 rc=1、调用错误实际 rc=2，与公开契约 2/3 不符 |
| writer-2 | CLI 专项 | PASS（6/6） | 自定义 argparse error rc=3；缺 manifest rc=2 |
| writer-3 | 治理七文件 + 测试质量 | PASS（84/84；75 tests / 0 violations） | 无 |
| verifier-1 | 独立选择集 + CLI 对抗 | PASS（81 tests） | rc 0/1/2/3 与 INDEX 0/1 均符合 |

## 硬性 DOD

- [x] 每个任务 ≤ 1h
- [x] 每个任务对应自动化测试
- [x] 依赖为 DAG
- [x] TDD 红→绿证据已记录
- [x] 治理专项全绿
- [x] 独立 verifier PASS
- [ ] 用户 acceptance

## Commit 历史

| commit | 日期 | 范围 | 测试 | 备注 |
|---|---|---|---|---|
| `f1cf815` | 2026-07-27 | P0-1 执行链 + P0-3 可信回归 | 84/84 PASS；75 tests / 0 violations；verifier PASS | 使用已授权 `PRE_COMMIT_SKIP=1`；未带入 Auth/Eval/AI Push 改动 |
