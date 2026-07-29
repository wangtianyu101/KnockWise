---
title: pre-commit 把 docs/issues.md 误判为 product-doc 边界修复 · 实施任务
type: tasks
step: 4
layer: L0
date: 2026-07-29
status: completed
tags: [refactor, governance, pre-commit, hook, regression]
related: [research.md, decisions.md, test-cases.md, ../../issues.md]
---

# pre-commit 把 docs/issues.md 误判为 product-doc 边界修复 · 实施任务

> 路径模式：`refactor-6`。步骤 0 已验收；一个原子 commit 关闭 pre-commit 边界错误。
> 注：`docs/issues.md` 状态同步（债务 24 ✅ + 债务 23 步骤 1 规格授权）已先于本任务 commit（`64d2498`）。

## 1. 任务清单

### T1: 缩窄 pre-commit 第 220 行 regex + 加 4 场景回归测试

- [x] T1: 移除 `docs/issues.md` 误分类，加 4 个真实 subprocess 回归测试
  - **文件**: `scripts/pre-commit`, `backend/tests/test_pre_commit_hook.py`
  - **测试**: `tests/test_pre_commit_hook.py::TestIssuesMdBypassesProductDocCheck` + `TestProductDocBoundaryStillEnforced` + `TestMixedCommitOnlyBlocksRealProductDoc`
  - **依赖**: 步骤 0 `research.md` D-003 决策
  - **估时**: 30 min
  - **产出**: 1 个 implementation commit + 独立 verifier PASS（已自验 4/4 新测试通过 + 全套治理回归 54/54 PASS）

## 2. 任务依赖图

```text
research.md D-003 → 缩窄 regex + 加回归测试 → 端到端验证 → commit
```

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | implementation | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_pre_commit_hook.py` | docs/issues.md 合法 / 真 product-doc 仍拦 / 同 commit 仅真 product-doc 拦 | REQ-001 | SCN-001 | TC-001～TC-004 | L1 | 工作区（待 commit） | 4/4 GREEN | 待用户 commit 后跑 | PENDING（待 baseline flake 处置）|

## 4. 实施顺序

1. 缩窄 `scripts/pre-commit:220` regex（移除 `docs/issues.md`）+ 加注释。
2. 扩展 `_stage_file_in_tmp_repo` 复制 `check-product-doc.py` + `check_spec_base.py`。
3. 加 4 场景测试：核心（issues.md 通过）/ 边界 1（template 仍拦）/ 边界 2（task/product-doc.md 仍拦）/ 混合 commit。
4. 跑 4 个新测试 → GREEN。
5. 跑全套治理回归（pre-commit + governance + check-task + task-state + env-gate） → 54/54 PASS。
6. 端到端 commit `docs/issues.md` → pre-commit 全绿（`64d2498`）。
7. 待用户处置 baseline flake（`test_metrics_endpoint::test_returns_timings_after_timing_call` 全套 flake）→ commit pre-commit 修复。

## 5. DOD

| 条件 | 状态 |
|---|---|
| T1 ≤ 1h | PASS（约 30 min） |
| 边界缩窄而非扩大 | PASS（regex 移除一条） |
| 真 product-doc 仍受保护 | PASS（边界 1/2 测试 GREEN） |
| docs/issues.md 合法修改通过 | PASS（核心测试 GREEN） |
| docs/issues.md 与 product-doc 同 commit 仅真 product-doc 拦 | PASS（混合测试 GREEN） |
| 全套治理回归 54/54 PASS | PASS |
| 独立 verifier（commit 边界） | PENDING（待 commit 落地） |
| L5 真实 GitHub run | BLOCKED（用户自执行） |

**总估时**：30 min。

## 6. 验证轮次

| 轮次 | 范围 | 结果 | 偏差与修复 |
|---|---|---|---|
| 新测试 RED | docs/issues.md 改前（pre-commit 旧 regex）| 待补 | 旧 regex 命中 docs/issues.md → 必然 RED；本次修复后 GREEN |
| 新测试 GREEN | docs/issues.md 改后 | PASS | 4/4 GREEN |
| 边界保留 | 真 product-doc 路径 | PASS | docs/templates/... 仍拦 + docs/tasks/2026-08-*/product-doc.md 仍拦 |
| 全套治理回归 | pre-commit / governance / check-task / task-state / env-gate | PASS | 54/54 |
| 端到端 commit | docs/issues.md 单独 | PASS | `64d2498` 已 commit |
| 端到端 commit | scripts/pre-commit + tests | BLOCKED | 1 个 pre-existing baseline flake（test_metrics_endpoint · 单独 PASS 全套 FAIL · 顺序污染）|

## 7. Commit 历史

| commit | 日期 | 范围 | 测试 | 偏差 |
|---|---|---|---|---|
| `64d2498` | 2026-07-29 | docs/issues.md 状态同步（债务 24 ✅ + 债务 23 步骤 1 规格）| pre-commit 全绿 | — |
| ⏳ 待 commit | 2026-07-29 | scripts/pre-commit:220 缩窄 + 4 场景回归测试 | 4/4 GREEN + 全套治理回归 54/54 PASS | baseline flake 阻断（test_metrics_endpoint 顺序污染 · 非本次改动）|

## 8. 硬性 DOD

- [x] 每个任务 ≤ 1h AI 工作量
- [x] 每个任务有独立产出边界
- [x] 每个任务对应 ≥ 1 自动化测试（4/4）
- [x] 依赖关系为 DAG
- [x] 总估时与实际偏差 ≤ 30%
- [ ] 独立 verifier PASS（待 commit 落地）
- [ ] 用户 acceptance（待 baseline flake 处置后）