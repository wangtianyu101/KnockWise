---
title: P0 任务治理 Gate · 实施任务
type: tasks
step: 4
date: 2026-07-26
status: completed
tags: [p0, governance, hook, ci]
related: [research.md, decisions.md, test-cases.md, verify.md]
acceptance: ACCEPTED (2026-07-29 · 代码侧 · 用户拍板)
acceptance_external: PENDING (GitHub Ruleset / Required Check · 用户自执行)
---

# P0 任务治理 Gate · 实施任务

> 路径模式：`timebox`。每个任务均小于 1 小时；用户于 2026-07-27 要求提交，实施已落入 commit `f1cf815`。

## 1. 任务清单

### T1: 修正 checker 的 INDEX 与 legacy 边界

- [x] T1: 修正 INDEX 读取、日期误豁免与 verify→tasks 状态校验
  - **文件**: `scripts/check-task.py`, `scripts/check_task_state.py`
  - **测试**: `backend/tests/test_check_task.py`, `backend/tests/test_task_governance_gate.py`
  - **依赖**: —
  - **估时**: 30 min
  - **实际**: 28 min
  - **产出**: commit `f1cf815`

### T2: 关闭本地 Hook 逃逸链

- [x] T2: 新任务缺 manifest 时 fail closed，并切换版本化 hooksPath
  - **文件**: `scripts/pre-commit`, `scripts/install-hooks.sh`
  - **测试**: `backend/tests/test_pre_commit_hook.py`, `backend/tests/test_task_governance_gate.py`
  - **依赖**: T1
  - **估时**: 30 min
  - **实际**: 34 min
  - **产出**: commit `f1cf815`

### T3: 建立只读 CI 治理 Gate

- [x] T3: CI 对 changed task artifacts 执行同一组 checker
  - **文件**: `.github/workflows/ci.yml`, `scripts/check-governance.py`, `scripts/requirements-governance.txt`
  - **测试**: `backend/tests/test_check_governance.py`, `backend/tests/test_ci_workflow.py`
  - **依赖**: T1
  - **估时**: 45 min
  - **实际**: 41 min
  - **产出**: commit `f1cf815`

## 2. 任务依赖图

```text
T1 ──→ T2
 └──→ T3
```

无环；T2 与 T3 在 T1 后可并行。

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_task_governance_gate.py::test_post_cutoff_task_is_not_legacy_exempt` | 新任务不再误豁免 | REQ-001 | SCN-001 | TC-001 | L1 | `f1cf815` | PASS | PASS | PENDING |
| T2 | `test_task_governance_gate.py::test_new_task_without_manifest_blocks_hook` | Hook 缺 manifest 非零 | REQ-002 | SCN-002 | TC-002 | L2 | `f1cf815` | PASS | PASS | PENDING |
| T3 | `test_check_governance.py::test_ci_blocks_new_task_without_manifest` | CI 缺 manifest 非零 | REQ-003 | SCN-003 | TC-003 | L3 | `f1cf815` | PASS | PASS | PENDING |

## 4. 任务↔调研映射

| 任务 | 调研关闭条件 | test-cases.md |
|---|---|---|
| 任务 T1 | research § 3.2 条件 1/3 | TC-001, TC-004 |
| 任务 T2 | research § 3.2 条件 2/4 | TC-002, TC-005, TC-006 |
| 任务 T3 | research § 3.2 条件 2/6/7 | TC-003, TC-007, TC-008 |

## 5. 总估时与实际

- T1: 30 min → 28 min
- T2: 30 min → 34 min
- T3: 45 min → 41 min
- **总估时**: 1h45m
- **实际**: 1h43m
- **偏差**: -1.9%

## 6. 实施顺序

1. T1 checker 边界与 INDEX 读取。
2. T2 Hook fail-closed 与 hooksPath。
3. T3 CI diff Gate 与只读安全契约。
4. 运行相关测试、全套测试并交独立 verifier。

## 7. 验证轮次

| 轮次 | 范围 | 结果 | 偏差与修复 |
|---|---|---|---|
| writer-1 | 5 个治理测试文件 | FAIL（3） | POSIX `sh` 对嵌套 case 命令替换解析失败；改为 `if` |
| writer-2 | 5 个治理测试文件 | PASS（35/35） | 无 |
| writer-3 | 7 个治理测试文件 | PASS（69/69） | 新增“既有 root 不误判成新增目录”的 Hook + CI 回归 |
| verifier-1 | 对抗式独立检查 | FAIL（3 项） | INDEX 被 worktree 影响；rename 绕过 Hook；CI 删除 manifest 绕过 |
| writer-4 | 7 个治理测试文件 | PASS（73/73） | 修复 3 项并补 INDEX / Hook rename / CI delete + rename 4 条回归 |
| verifier-2 | 独立复验 | PASS | 73/73；INDEX-only / Hook rename / CI manifest delete 对抗实测均符合预期 |
| writer-5 | 状态主账自检 | PASS（74/74） | 修复后续 Markdown 表覆盖最后一条 T 三事实 |
| verifier-3 | 最终独立复验 | PASS | 74/74；新增回归与此前 4 个对抗场景定向 5/5 |

## 硬性 DOD

- [x] 每个任务 ≤ 1h AI 工作量
- [x] 每个任务有独立产出边界并已落入 commit `f1cf815`
- [x] 每个任务对应 ≥ 1 自动化测试
- [x] 依赖关系为 DAG
- [x] 总估时与实际偏差 ≤ 30%
- [x] 独立 verifier PASS
- [x] 用户 acceptance（代码侧 · 2026-07-29 · GitHub Ruleset 仍 PENDING 外部 BLOCKED · 用户自执行）

## 8. Commit 历史

| commit | 日期 | 范围 | 测试 | 备注 |
|---|---|---|---|---|
| `f1cf815` | 2026-07-27 | P0-1 执行链 + P0-3 可信回归 | 84/84 PASS；独立 verifier PASS | 使用已授权 `PRE_COMMIT_SKIP=1`；全后端存在范围外 Auth/Digest/MySQL 失败 |
