---
title: P0 AI Coding containment 决策主账
type: meta
step: 0
date: 2026-07-28
status: approved
tags: [decisions, p0, governance, supply-chain]
related: [research.md, tasks.md, ../../issues.md]
---

# P0 AI Coding containment · 决策主账

## 1. 权威定位

本文件是本 P0 任务的决策最权威详细主账。

- 事实、威胁与关闭条件：[`research.md`](research.md)
- 长期状态：[`docs/issues.md` 债务 23](../../issues.md)
- 父任务方案决策：[`AI Coding 流程审计 decisions`](../2026-07-28-refactor-ai-coding-workflow-audit/decisions.md)
- 其他文档只镜像状态，不重复理由。

## 2. 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| D-002 | 2026-07-28 | P0 止血实现 | release SHA + CI provenance + active ruleset | ✅ 已决策 | research § 2 |
| D-001 | 2026-07-28 | 顺序 | 先两个 P0，再方案 B 规格 | ✅ 已决策 | 父任务 D-003 |

## 3. 决策详细记录

### D-001 · 顺序

- **日期**：2026-07-28
- **决策项**：先恢复底线还是先写控制面 v2 规格
- **选项**：先规格 / 先 P0 / 只 P0
- **选择**：先两个 P0，再方案 B 规格
- **用户原话**：「验收步骤 0，先修两个 P0，再按方案 B 做规格。」
- **理由**：
  1. 失效 Gate 不能保护后续规格与实现。
  2. Action ref 不存在是可独立止血的阻断。
  3. 独立 P0 task 避免与 P1 重构混成一个不可回滚提交。
- **影响文件**：本目录、父任务、`docs/issues.md`
- **关联决策**：父任务 D-003

### D-002 · P0 止血实现

- **日期**：2026-07-28
- **决策项**：如何关闭格式假绿与远端 Gate 绕过
- **选项**：只换 SHA / release SHA + 在线 provenance + active ruleset / 暂停 workflow
- **选择**：release SHA + 在线 provenance + active ruleset
- **用户原话**：「先修两个 P0」
- **理由**：
  1. 只换 SHA 不能阻止同类缺陷复发。
  2. provenance 必须由目标 repo 的 API 事实证明。
  3. Hook 不是安全边界，远端 ruleset 才是最终裁决。
- **影响文件**：`.github/workflows/*.yml`、`scripts/ci/check_action_sha.py`、测试、GitHub ruleset
- **关联决策**：D-001

## 4. 决策落地追踪与元信息

| 决策 | 落地点 | 状态 | 证据 |
|---|---|---|---|
| D-001 | 父 `research.md` / `decisions.md` / `docs/issues.md` | ✅ 已落地 | 2026-07-28 同步 |
| D-002 | Action provenance | ✅ 已落地 | commit `c2965e6` + 独立 verifier PASS |
| D-002 | active ruleset | ⏸ 用户操作 | Codex 不操控远端；tasks T2 保留待回读 |

- **位置**：`docs/tasks/2026-07-28-p0-ai-coding-containment/decisions.md`
- **创建日期**：2026-07-28
- **决策总数**：2
- **已决策数**：2
- **待确认数**：0
- **暂缓数**：0
- **取消数**：0
- **当前阶段**：P0 timebox 实施中
