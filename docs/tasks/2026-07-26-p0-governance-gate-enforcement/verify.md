---
title: P0 任务治理 Gate · 验证报告
type: verify
step: 5
date: 2026-07-26
status: partial_external_blocked
tags: [p0, governance, verification]
related: [research.md, tasks.md, test-cases.md, decisions.md]
---

# P0 任务治理 Gate · 验证报告

> 结论边界：代码侧 Gate 已通过专项验证；GitHub Required Check / Ruleset 尚未配置，因此不能宣称“合并不可绕过”。
> 实施 commit：`f1cf815`（2026-07-27）。本文如实保留全后端与 L5 未闭环结果，不将专项 PASS 扩大为完整交付 PASS。

## L1 单元测试证据

- 治理专项 7 个测试文件：**74 passed**。
- 测试质量：60 files / 752 tests / 0 violations。
- Python AST、Shell syntax、workflow YAML：PASS。

## L2 接口与 subprocess 证据

- 真实临时 Git 仓库运行 `sh scripts/pre-commit`：
  - 缺 `task.yaml` → 非零；
  - 合法 manifest → 零；
  - checker 缺失 → 非零；
  - 仅新增 `verify.md` → 校验 INDEX 中 sibling `tasks.md`；
  - 既有历史 task root 新增文件 → 不误要求回填 manifest。
  - R100 task root rename → 新 root 缺 manifest 时非零；
  - INDEX 已 staged 后 worktree 删除 manifest → 仍按 INDEX 校验。
- 当前仓库 `git config --local --get core.hooksPath` → `scripts`。

## L3 整合测试

**任务范围结果：PASSED**

- `74 passed in 4.29s`：task contract、task state、Hook、CI Gate、workflow、安全静态契约与既有测试质量 Gate。
- `git diff --check`：PASS。
- `scripts/ci/check_action_sha.py`：全部第三方 Action 完整 SHA pin。

**仓库全套结果：FAILED / 已知外部基线阻塞**

- `22 failed, 754 passed, 2 skipped, 4 xfailed`。
- 失败集中在既有 Digest API mock / 本地 MySQL 连接限制、eval JSONL 中 Python `None` 非法 JSON、Digest LLM contract；本次治理 diff 未修改这些模块。
- 因全套未绿，本报告不把仓库总体状态标成 PASS。

## L4 独立 review

- verifier 第 1 轮：FAIL（3 项）—— INDEX/worktree 混读、rename 绕过 Hook、CI 删除 manifest 绕过。
- 三项均已修复并增加 4 条回归。
- verifier 第 2 轮：**PASS**；对抗实测 `INDEX_ONLY_RC=0`、`RENAME_HOOK_RC=1`、`DELETE_MANIFEST_CI_RC=1`。
- 主账自检又发现后续 Markdown 表覆盖最后一条 T 三事实；补回归并修复 parser。
- verifier 第 3 轮：**PASS**；最终治理专项 74/74，关键对抗场景定向 5/5。

## L5 staging 运行时验证

**结果：FAILED / BLOCKED**

- 本地 Hook 激活：PASS（`core.hooksPath=scripts`）。
- GitHub CI workflow 代码已添加，但尚未在真实 PR 上执行。
- GitHub Repository Ruleset / Required Check 尚未配置；这是外部仓库设置，当前代码修改不能完成。

**phase_acceptance**: PENDING

## 剩余项

1. 在 GitHub 上跑一次真实 PR，确认实际 emitted check name（预期 job 名为 `Workflow governance`）。
2. 将该 check 加入目标 branch 的 required checks / ruleset。
3. 单独修复仓库全套的 22 个既有失败；不与本次 P0-1 混成假绿。
