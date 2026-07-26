---
title: P0 任务治理 Gate · 决策主账
type: meta
step: 0
date: 2026-07-26
status: approved
tags: [decisions, p0, governance]
related: [research.md, task.yaml]
---

# P0 任务治理 Gate · 决策主账

本文件是本任务决策最权威详细主账。调研证据见 [research.md](research.md)，项目状态镜像见 [docs/issues.md](../../issues.md)；其他文档只引用。

## 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-26 | P0-1 修复边界 | checker + manifest Gate + 版本化 Hook + CI；Ruleset 单列 | ✅ 已确认 | research § 2/8 |

## 决策详细记录

### 决策 1 · 代码侧治理 Gate 四点闭环

- **日期**：2026-07-26
- **决策项**：只修日期正则，还是修复完整本地与 CI 失效链。
- **选项**：只修正则；四点闭环；立即回填全部历史 manifest。
- **选择**：四点闭环；历史迁移与 GitHub Ruleset 分别跟踪。
- **用户原话**：「确认」
- **理由**：
  1. 单修正则不能阻止缺失 `task.yaml`。
  2. 手工复制 Hook 已出现实际漂移。
  3. 本地 Hook 可绕过，CI 必须独立执行。
- **影响文件**：checker、Hook、CI、测试和任务主账。
- **关联决策**：任务状态语义 P0-5、任务产物契约 P0-7、Required Checks P0-4。

## 决策落地追踪

| 决策 | 落地点 | 状态 |
|---|---|---|
| 1 | checker / Hook / CI / tests | ✅ 已落地 · commit `f1cf815` · verifier PASS |
| 1 | GitHub Ruleset | ⛔ 外部 BLOCKED |

## 元信息

- **位置**：`docs/tasks/2026-07-26-p0-governance-gate-enforcement/decisions.md`
- **创建日期**：2026-07-26
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：1
- **负责人**：Codex / 用户
- **状态**：代码侧完成 · 外部 Ruleset BLOCKED
