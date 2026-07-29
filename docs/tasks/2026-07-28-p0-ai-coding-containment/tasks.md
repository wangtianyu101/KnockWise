---
title: P0 AI Coding containment · 实施任务
type: tasks
step: 4
layer: L0
date: 2026-07-28
status: in-progress
tags: [p0, governance, github-actions, ruleset]
related: [research.md, decisions.md, test-cases.md]
---

# P0 AI Coding containment · 实施任务

> 路径模式：`timebox`。用户已授权先修两个 P0；每个任务小于 1 小时。

## 1. 任务清单

### T1: Action provenance fail-closed

- [ ] T1: 替换无效 Action ref，并让 governance 在线验证 repo + SHA
  - **文件**: `.github/workflows/auto-fix-ci.yml`, `.github/workflows/ci.yml`, `scripts/ci/check_action_sha.py`
  - **测试**: `scripts/ci/test_check_action_sha.py`, `scripts/ci/test_security_e2e.sh`
  - **依赖**: —
  - **估时**: 45 min
  - **产出**: 独立 implementation commit

### T2: 远端 required ruleset

- [ ] T2: 启用 ruleset 19763447，设置四个 required checks 且无常规 bypass
  - **对象**: GitHub repository ruleset `合并保护`
  - **测试**: GitHub API 回读 enforcement/rules/bypass actors
  - **依赖**: T1 的 governance check 名称保持稳定
  - **估时**: 30 min
  - **产出**: 远端设置证据 + verify.md

## 2. 依赖图

```text
T1 Action provenance ──→ T2 active ruleset
```

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | implementation | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_check_action_sha.py` | 伪 40 位 SHA / 404 / 网络失败均被拒绝 | REQ-P0-1 | SCN-P0-1 | TC-P0-1 | L1/L3 | READY | GREEN | PENDING | ACCEPTED |
| T2 | GitHub API readback | ruleset active + 四 required checks + no bypass | REQ-P0-2 | SCN-P0-2 | TC-P0-2 | L5 | EXTERNAL | PENDING | PENDING | ACCEPTED |

## 4. 实施顺序

1. 先写 provenance 负例并确认旧 checker 假绿。
2. 实现远端校验与 CI 接线，替换三个官方 release SHA。
3. 跑单元、Shell E2E、真实 API smoke。
4. 只提交 T1 白名单文件并开独立 verifier。
5. verifier PASS 后启用 ruleset，API 回读并记录 T2。

## 5. DOD

| 条件 | 状态 |
|---|---|
| 每个任务 ≤ 1h | PASS（T1 约 45 min） |
| 每个任务有自动化或远端事实证据 | T1 PASS；T2 PENDING |
| T1 代码 commit 配套单测 | PASS（11 checker + security E2E） |
| T1 独立 verifier PASS | PENDING |
| T2 远端 API 回读 PASS | PENDING |
| 用户已授权 P0 实施与后续顺序 | PASS |

**总估时**：75 min（T1 45 min + T2 30 min）。

## 6. 验证轮次

| 轮次 | 范围 | 结果 | 偏差与修复 |
|---|---|---|---|
| baseline | 当前 checker + 伪造 SHA | FAIL（oracle 假绿） | 待 T1 修复 |
| T1 GREEN | provenance 单元 + workflow contract + security E2E + 官方 API smoke | PASS | 40 位格式检查升级为 owner/repo+SHA 在线证据 |

## 7. Commit 历史

| commit | 日期 | 范围 | 测试 | 偏差 |
|---|---|---|---|---|
| PENDING | 2026-07-28 | T1 | PENDING | PENDING |
