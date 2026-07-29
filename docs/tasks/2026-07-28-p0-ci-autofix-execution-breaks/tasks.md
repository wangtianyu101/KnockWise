---
title: CI auto-fix 三项执行断链 · 实施任务
type: tasks
step: 4
layer: L0
date: 2026-07-28
status: completed
tags: [p0, github-actions, agent, tdd]
related: [research.md, decisions.md, test-cases.md]
---

# CI auto-fix 三项执行断链 · 实施任务

> 路径模式：`timebox`。步骤 0 已验收；一个原子 commit 同时关闭同一 workflow 的三条执行链。

## 1. 任务清单

### T1: 修复 prompt、branch output 与精确 staging

- [x] T1: commit `8fb65bf` · 三项失败回归先红，再完成最小安全修复
  - **文件**: `.github/workflows/auto-fix-ci.yml`, `scripts/ci/check_auto_fix_diff.py`
  - **测试**: `backend/tests/test_auto_fix_workflow.py`, `scripts/ci/test_check_auto_fix_diff.py`, `scripts/ci/test_auto_fix_e2e.sh`, `scripts/ci/test_security_e2e.sh`
  - **依赖**: 步骤 0 `research.md` 的 prompt 安全边界；当前工作区 P0 provenance 改动必须保留
  - **估时**: 1 h
  - **对应 commit**: `8fb65bf`
  - **产出**: 一个 implementation commit + 独立 verifier

## 2. 依赖图

```text
prompt context → Claude patch.diff
                         |
step id → branch output  +→ git apply --index → cached diff policy → tests → commit → push/PR
```

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | implementation | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | workflow contract + temp Git subprocess + Shell E2E | prompt / branch output / 精确 staging | REQ-AF-01～03 | SCN-AF-01～03 | TC-001～TC-010 | L1/L3/L5 | `8fb65bf` | GREEN | PASS | ACCEPTED |

## 4. 实施顺序

1. 新增 workflow contract/真实 Git index 回归，确认旧实现失败。
2. 让 prompt 只消费 allowlisted `failed_job/error_code` 的单行 JSON；禁止 `key_string`。
3. 增加 `id: create-branch` 与非空输出契约。
4. 使用 `git apply --index`，删除 patch 文件，diff checker 改查 cached diff，commit 不再全量 add。
5. 跑定向、治理、安全、provenance 和 YAML 解析回归。
6. 回写本文件，再形成白名单 commit，并由独立 verifier 固定 commit 校验。

## 5. DOD

| 条件 | 状态 |
|---|---|
| T1 ≤ 1h | PASS |
| 三项先红后绿 | PASS（初始 7 FAIL；修复后 8 PASS） |
| 真实 subprocess / Git index 证据 | PASS |
| 原治理与安全回归全绿 | PASS（31 pytest + 7 checker + 2 Shell E2E） |
| implementation commit 白名单无并行文件 | PASS（`8fb65bf`，10 个任务白名单文件） |
| 独立 verifier PASS | PASS（固定 commit `8fb65bf`，无偏差） |
| 用户已验收步骤 0 | PASS |

**总估时**：1h。

## 6. 验证轮次

| 轮次 | 范围 | 结果 | 偏差与修复 |
|---|---|---|---|
| baseline | 三项静态复现 + 现有测试 | FAIL（生产断链；现有测试假绿） | 新增真实行为 oracle |
| RED | 新增 workflow 行为测试 | FAIL（7 failed） | 精确命中 prompt / step id / staging / cached diff |
| GREEN | 定向 + 扩展回归 | PASS | 补充 commit 后复用 pre-commit `needs_review` output |
| verifier | 固定 commit `8fb65bf` 独立快照 | PASS | 8 workflow + 7 checker + 8 Shell E2E + 安全四关全绿 |

## 7. Commit 历史

| commit | 日期 | 范围 | 测试 | 偏差 |
|---|---|---|---|---|
| `8fb65bf` | 2026-07-29 | T1 | 866 full pytest + 8 workflow + 7 checker + Shell E2E PASS | 估时 1h；实际跨并发 gate 收敛约 2h |
