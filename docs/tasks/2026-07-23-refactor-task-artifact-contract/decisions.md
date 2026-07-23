---
title: 任务路径、阶段与条件产物契约 · 决策主账
date: 2026-07-23
status: 1/1 自动决策 · 待步骤 1 规格
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · 任务路径、阶段与条件产物契约

> 📌 **本文件是本任务决策最权威详细主账**。用户已授权剩余 P0 无需逐项确认，由对抗调研后采用单一推荐，并在最后提供汇总报告。

## ① 顶部权威定位

关联：[`research.md`](research.md) · [`docs/issues.md`](../../issues.md) · [`check-step.py`](../../../scripts/check-step.py)

## ② 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | P0-7 完整性契约 | 最小 task.yaml + check-task.py；测试证据可多落点；pre-commit 检查 INDEX | ✅ 自动决策 · 待规格 | research § 3-8 |

## ③ 决策详细记录

### 决策 1 · 采用最小任务契约

- **日期**：2026-07-23
- **决策项**：如何发现当前路径/阶段真正缺失的产物与测试证据，而不强制空 `test-cases.md`。
- **选项**：固定文件列表；强制 test-cases；多处复制 mode/status；大型 manifest；最小 task.yaml。
- **选择**：✅ 最小 `task.yaml` + 目录级 `check-task.py`。
- **授权原话**：“循环把上面哪些问题都处理一遍…不需要我确认了”；补充“最后给我一个汇总报告”。
- **理由**：
  1. 文件存在不等于测试真实，机械强制会复制空模板。
  2. 当前阶段是避免误报后续文件缺失的必要事实。
  3. 条件产物需要 UI/API/DB 触发声明。
  4. INDEX/WORKTREE 错位会让 checker 检查与提交不同内容。
  5. 最小 manifest 只保存阶段契约，不复制 P0-5 的 task 状态。
- **核心规则**：
  - `task.yaml` 保存 mode/current_step/step_state/triggers/test_evidence。
  - 测试证据允许 code、tasks-inline、standalone；不强制 `test-cases.md`。
  - check-step 保持单文件 validator；check-task 负责目录闭包。
  - pre-commit 固定 `--view index`。
  - 新任务严格；旧任务 `LEGACY_UNVERIFIED`，无永久白名单。
- **明确排除**：全量历史迁移、时间调度器、事件账本、证据哈希、自动 Agent/mutation test、完整 diff trigger 推断。
- **影响文件**：后续 spec/plan 决定，预计涉及 task 模板、DOD、`check-task.py`、pre-commit 和测试。

## ④ 落地追踪 + 元信息

| # | 决策 | 落地状态 | 落地位置 |
|---|---|---|---|
| 1 | 最小任务契约 | 🟡 待步骤 1 规格 | spec.md → plan/tasks → implementation |

- **位置**：`docs/tasks/2026-07-23-refactor-task-artifact-contract/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0（用户授权自动决策）
- **暂缓数**：0
- **路径模式**：refactor-6
- **下一步**：剩余 P0 调研完成后统一汇总；实施仍未授权。
