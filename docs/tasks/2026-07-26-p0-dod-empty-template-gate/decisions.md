---
title: P0 空模板 DOD Gate · 决策主账
type: meta
step: 0
date: 2026-07-26
status: approved
tags: [decisions, p0, dod]
related: [research.md, task.yaml]
---

# P0 空模板 DOD Gate · 决策主账

本文件是本任务决策最权威详细主账。调研证据见 [research.md](research.md)，项目状态镜像见 [docs/issues.md](../../issues.md)；其他文件只引用。

## 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-26 | 空模板阻断方式 | 共享模板残留 Gate，不做路径特判 | ✅ 已确认 | research § 2/8 |

## 决策详细记录

### 决策 1 · 共享模板残留 Gate

- **日期**：2026-07-26
- **决策项**：只拒绝模板路径，还是检查实际提交内容。
- **选项**：路径特判；共享模板残留 Gate；完整 Markdown AST/schema。
- **选择**：共享 Gate 检查模板身份、draft 与高置信度占位，再运行原阶段 checker。
- **用户原话**：「P0-2：空模板可以被判定为 DOD 通过 我们直接来解决这个问题吧」
- **理由**：
  1. 路径特判不能阻止复制模板到任务目录。
  2. 完整 AST/schema 超出 P0 时间盒。
  3. 共享 Gate 能同时保护本地 Hook 与 CI，且无需扩权限。
- **影响文件**：`scripts/check-step.py`、`backend/tests/test_check_step.py`、本任务主账。
- **关联决策**：P0-1 DOD 退出码传播、P0 任务治理 Gate。

## 决策落地追踪

| 决策 | 落地点 | 状态 |
|---|---|---|
| 1 | checker + regression tests | ✅ 已实施 · 77/77 PASS |
| 1 | 本地 Hook / CI 调用链 | ✅ 相关回归 PASS · 独立 verifier PASS |

## 元信息

- **位置**：`docs/tasks/2026-07-26-p0-dod-empty-template-gate/decisions.md`
- **创建日期**：2026-07-26
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **负责人**：Codex / 用户
- **状态**：已实现并独立验证 · 用户验收待完成
