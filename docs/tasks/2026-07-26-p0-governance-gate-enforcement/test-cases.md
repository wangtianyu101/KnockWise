---
title: P0 任务治理 Gate · 测试用例
type: test-cases
step: 4
date: 2026-07-26
status: executed
tags: [p0, regression, hook, ci]
related: [tasks.md, verify.md]
---

# P0 任务治理 Gate · 测试用例

> 实施 commit：`f1cf815`（2026-07-27）。

## 0. 测试策略

- **自动化覆盖率目标**: ≥ 80%；本任务 15/15 关键风险场景自动化，场景覆盖率 100%。
- **手测场景**: 1 个，本仓库实际 `core.hooksPath` 配置检查。
- **E2E 场景**: 4 个临时 Git 仓库真实 subprocess 场景。
- **回归测试**: 既有 DOD Hook、task contract、CI workflow 静态契约和测试质量 checker。

## 1. 验收测试

| TC | 场景 | 类型 | 自动化 | 手测脚本 | 实际结果 |
|---|---|---|---|---|---|
| TC-001 | 2026-07-24 后任务不再 legacy exempt | happy | `test_task_governance_gate.py::test_post_cutoff_task_is_not_legacy_exempt` | — | PASS |
| TC-002 | 新目录缺 task.yaml 时 Hook 非零 | failure | `test_task_governance_gate.py::test_new_task_without_manifest_blocks_hook` | — | PASS |
| TC-003 | 新目录缺 task.yaml 时 CI 非零 | failure | `test_check_governance.py::test_ci_blocks_new_task_without_manifest` | — | PASS |
| TC-004 | INDEX 读取 staged 内容而非 worktree | edge | `test_task_governance_gate.py::test_state_checker_index_view_reads_staged_content` | — | PASS |
| TC-005 | 只改 verify.md 仍校验 sibling tasks.md | edge | `test_task_governance_gate.py::test_verify_only_change_validates_sibling_tasks_from_index` | — | PASS |
| TC-006 | 合法 task.yaml 的 Hook 返回零 | happy | `test_task_governance_gate.py::test_new_task_with_valid_manifest_passes_hook` | — | PASS |
| TC-007 | checker 缺失时 Hook fail closed | failure | `test_task_governance_gate.py::test_missing_task_checker_fails_closed` | — | PASS |
| TC-008 | CI governance job 只读、无 secrets | security | `test_ci_workflow.py::test_governance_gate_is_read_only_secretless_and_runs_shared_checker` | — | PASS |
| TC-009 | 既有历史任务新增文件不强制回填 manifest | edge | `test_task_governance_gate.py::test_existing_legacy_task_can_add_file_without_manifest` | — | PASS |
| TC-010 | CI 同样区分既有 root 与新增 root | edge | `test_check_governance.py::test_ci_does_not_require_manifest_when_existing_task_adds_file` | — | PASS |
| TC-011 | INDEX manifest 已 staged、worktree 后删仍按 INDEX 校验 | edge | `test_check_task.py::TestIndexView::test_index_validation_ignores_unstaged_worktree_deletion` | — | PASS |
| TC-012 | task root R100 rename 且无 manifest 时 Hook 非零 | failure | `test_task_governance_gate.py::test_renamed_task_root_without_manifest_blocks_hook` | — | PASS |
| TC-013 | 删除既有 task.yaml 时 CI 非零 | failure | `test_check_governance.py::test_ci_blocks_deleting_existing_task_manifest` | — | PASS |
| TC-014 | task root rename 且无 manifest 时 CI 非零 | failure | `test_check_governance.py::test_ci_blocks_renamed_task_root_without_manifest` | — | PASS |
| TC-015 | 后续 Markdown 表不覆盖最后一条 T 三事实 | regression | `test_task_governance_gate.py::test_state_checker_does_not_overwrite_task_with_later_table` | — | PASS |

## 2. 自动化测试

| 自动化测试 | 对应 TC | 覆盖范围 |
|---|---|---|
| `backend/tests/test_task_governance_gate.py` | TC-001/002/004/005/006/007/009/012/015 | Hook、INDEX、legacy、rename、状态表解析、hooksPath |
| `backend/tests/test_check_governance.py` | TC-003/006/010/013/014 | CI changed-files/delete/rename Gate |
| `backend/tests/test_ci_workflow.py` | TC-008 | workflow 权限与命令 |
| `backend/tests/test_check_task.py` | TC-004/006/011 | manifest schema 与纯 INDEX |
| `backend/tests/test_pre_commit_hook.py` | TC-006/007 | DOD Hook 退出码回归 |

**覆盖率**：关键风险场景 15/15 = 100%，达到 ≥80% 目标。

## 3. 手测场景

- [x] **实际仓库使用版本化 Hook**
  - 步骤：运行 `sh scripts/install-hooks.sh`；读取 `git config --local --get core.hooksPath`。
  - 期望：输出 `scripts`。
  - 实际：PASS，当前仓库返回 `scripts`。

## 4. 回归测试

| 旧功能 | 自动化测试 | 验证点 |
|---|---|---|
| DOD 合法/非法文档退出码 | `backend/tests/test_pre_commit_hook.py` | 合法 0、非法非零 |
| task.yaml schema/path mode | `backend/tests/test_check_task.py` | 既有契约仍通过 |
| 环境 Gate | `backend/tests/test_pre_commit_env_gate.py` | venv/pytest/tsc fail closed |
| 测试质量 Gate | `backend/tests/test_check_test_quality.py` | 空壳/xfail 规则不回归 |

## 5. 边界 case

- [x] worktree 与 INDEX 内容不同：checker 只看 staged 版本。
- [x] 现有任务目录新增 verify.md：不误判为无需校验，定位 sibling tasks.md。
- [x] checker 文件丢失：禁止通过。
- [x] 历史 task root 新增文件：不强制伪造历史 manifest。
- [x] R100 task root rename：新 root 仍必须带合法 manifest。
- [x] INDEX 已 staged、worktree 后续删除：只读 INDEX，不回退。
- [x] 删除既有 task.yaml：CI fail closed。
- [x] tasks.md 后续表格：不污染三事实表解析。
- [x] CI base SHA 不可用：回退 default branch、HEAD^ 或 empty tree。

## 6. Bug 回归测试

- [x] 日期正则误豁免：TC-001。
- [x] 仅在 task.yaml 已 staged 时才触发：TC-002/003。
- [x] `.git/hooks/pre-commit` 复制漂移：installer 测试 + 实际 hooksPath。
- [x] verify-only 改动错误地把 verify.md 当 tasks.md：TC-005。
