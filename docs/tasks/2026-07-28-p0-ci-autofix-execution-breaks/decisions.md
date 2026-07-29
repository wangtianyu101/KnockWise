---
title: CI auto-fix 三项执行断链 · 决策主账
type: meta
step: 0
date: 2026-07-28
status: approved_implementation_in_progress
tags: [decisions, p0, github-actions, agent]
related: [research.md, task.yaml, ../../issues.md]
---

# CI auto-fix 三项执行断链 · 决策主账

## ① 顶部权威定位

本文件是本任务决策最权威详细主账。

- 事实、复现、风险和关闭条件：[`research.md`](research.md)
- 长期议题状态：[`docs/issues.md` 债务 24](../../issues.md)
- 既有 auto-fix v4 安全债：[`2026-07-23 task`](../2026-07-23-bug-ci-autofix-safety-drift/decisions.md)
- 其他文件只保留链接与状态镜像，不重复完整理由。

## ② 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| D-002 | 2026-07-28 | 实施路径与 prompt 安全边界 | timebox；仅传 allowlisted fields；精确 staging | ✅ 用户已验收 | research § 六/七 |
| D-001 | 2026-07-28 | 本次范围 | 只修三项及必要测试 | ✅ 用户已确认 | research § 一 |

## ③ 决策详细记录

### D-001 · 本次只处理三项执行断链

- **日期**：2026-07-28
- **决策项**：本次是否同时处理全部 auto-fix v4 安全债
- **选项**：只处理三项；合并既有七项 v4；永久停用 auto-fix。
- **选择**：✅ 只处理 prompt 字面 `$(jq ...)`、缺 step id、`git add -A` 过度 staging，以及必要回归测试。
- **用户原话**：「Claude prompt 里的 `$(jq ...)` 不会执行；`create-branch` 缺少 step id，后续分支输出为空；`git add -A` 可能把 `patch.diff` 一并提交。是这三项，可以。」
- **理由**：
  1. 三项都能独立稳定复现。
  2. 两项确定性阻断每个 auto-fix run，第三项破坏提交边界。
  3. 限定 scope 避免把既有 v4 七项安全债混入一个不可审阅提交。
- **影响文件**：workflow、diff checker、auto-fix E2E/安全测试、workflow contract test。
- **关联决策**：既有 v4 决策继续有效但不在本任务实施。

### D-002 · 最小安全修复与 timebox 路径

- **日期**：2026-07-28
- **决策项**：如何在不扩展 scope 的前提下修通 prompt、branch output 和 staging。
- **选项**：
  - A：结构化 step output + id + `git apply --index` + cached diff。
  - B：连同 sanitizer/key_string 等 v4 七项安全债全部重写。
  - C：永久关闭 auto-fix。
- **选择**：✅ 方案 A：`timebox` + 结构化 step output + `id: create-branch` + `git apply --index` + cached diff。
- **用户原话**：「验收步骤 0，开始实施。」
- **理由**：
  1. 固定版本 Action 的 `prompt` 输入不会执行 shell，必须显式生成 step output。
  2. 当前 `key_string` 是 raw log 前 200 字符；修通它会激活间接 prompt injection，因此本任务只传 allowlisted `failed_job/error_code`。
  3. `git apply --index` 直接把 patch 指定的变更写入 index，可兼容新增/修改/删除文件并隔离无关 workspace 文件。
- **影响文件**：`.github/workflows/auto-fix-ci.yml`、`scripts/ci/check_auto_fix_diff.py` 及测试。
- **关联决策**：D-001。

## ④ 决策落地追踪 + 元信息

| 决策 | 落地点 | 状态 | 证据 |
|---|---|---|---|
| D-001 | research § 一/三/八、issues 债务 24 | ✅ 已同步 | 2026-07-28 |
| D-002 | research § 六/七/八 | ✅ 已验收，实施中 | 2026-07-28 用户确认 |

- **位置**：`docs/tasks/2026-07-28-p0-ci-autofix-execution-breaks/decisions.md`
- **创建日期**：2026-07-28
- **决策总数**：2
- **已决策数**：2
- **待确认数**：0
- **暂缓数**：0
- **取消数**：0
- **路径模式**：`timebox`
- **当前阶段**：步骤 4 TDD 实施中
