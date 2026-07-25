---
title: 任务状态语义与传播链 · 决策主账
date: 2026-07-23
status: 1/1 已决策 · 待步骤 1 规格
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · 任务状态语义与传播链

> 📌 **本文件是本任务决策最权威详细主账**。
> `research.md` § 8 与 `docs/issues.md` 只保存简表和链接；规格、计划、实施和验证的落地状态统一回写本文件。

## ① 顶部权威定位

本文件记录任务状态模型、checkbox 语义、测试/verifier 事实与阶段验收的用户决策。

关联文档：

- 调研：[`research.md`](research.md)
- 议题主账：[`docs/issues.md`](../../issues.md)
- 公共流程主账：[`AGENTS.md`](../../../AGENTS.md)

## ② 决策总览表

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | P0-5 任务状态模型 | 任务级三事实 + 阶段级验收；`[x]` 仅表示 implemented；删除裸 DONE | ✅ 已决策 · 待规格 | research.md § 3-8 |

## ③ 决策详细记录

### 决策 1 · 采用最小正交事实模型

- **日期**：2026-07-23
- **决策项**：如何避免 `[x] DONE` 同时表达实施、测试、验证和用户验收，并阻止 FAILED 继续传播为完成。
- **选项列表**：
  1. 保持现有 `[x] + DONE`，依赖现有文档和 verifier。
  2. 单一五级线性状态机：Planned → Implemented → Tested → Verified → Accepted。
  3. frontmatter + checkbox + table 三份状态副本。
  4. **最小正交事实模型**：task 记录 implementation/test/verifier，阶段记录 acceptance。
- **选择**：✅ **选项 4**。
- **用户原话**："确认"。
- **具体语义**：
  - `[x]` 只表示 implementation 已落入 commit。
  - `test`：NOT_RUN / PASS / FAIL / N/A。
  - `verifier`：NOT_RUN / PASS / FAIL / BLOCKED / N/A。
  - `acceptance`：PENDING / ACCEPTED / REJECTED，只放阶段级。
  - 删除新任务格式中的裸 `DONE`。
  - `[x] + FAIL` 合法；`FAIL + DONE/VERIFIED/阶段完成` 非法。
- **理由**：
  1. V4 T29 已证明“已实施但验证失败”是常见且必须表达的复合事实。
  2. 单一线性状态会丢失事实；多份 frontmatter/正文/表格会制造重复主账。
  3. Checkbox 保持 commit 边界语义，与 AGENTS.md § 6.5 的即时回写习惯最接近。
  4. 用户通常验收 phase/step，而不是每个内部原子 task。
  5. 新规则仅约束新任务，避免全量历史迁移。
- **影响文件**：`AGENTS.md`、`docs/DOD.md`、tasks/verify/retro 模板、`scripts/check-step.py`、相关测试、`docs/rules/milestones.md`。
- **明确排除**：全量历史迁移、任务状态数据库、事件账本、三份状态副本、在本轮直接实施。
- **关联决策**：无。

## ④ 决策落地追踪 + 元信息

### 4.1 落地追踪

| # | 决策 | 落地状态 | 落地位置 | 落地日期 |
|---|---|---|---|---|
| 1 | 最小正交事实模型 | 🟡 已决策 · 待步骤 1 规格 | spec.md + 后续 plan/tasks/implementation | 待落地 |

### 4.2 元信息

- **位置**：`docs/tasks/2026-07-23-refactor-task-status-semantics/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：`refactor-6`
- **下一步**：等待用户明确要求“做设计”后进入步骤 1，编写状态与传播契约 `spec.md`。
