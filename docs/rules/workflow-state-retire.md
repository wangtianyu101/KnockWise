---
title: workflow-state 旧 Gate 退役条件（2026-08-09 · T19）
type: rule
status: active
tags: [governance, retire, workflow-state, legacy]
related: [../tasks/2026-07-28-refactor-ai-coding-workflow-audit/plan.md, ../tasks/2026-07-28-refactor-ai-coding-workflow-audit/tasks.md]
---

# workflow-state 旧 Gate 退役条件

> 范围：控制面 v2 上线（commit `08d18b1` + T1-T18 实施）后，何时把以"文档扫描 + 直接 read tasks.md"为依据的旧 Gate 退役。

## 触发条件（同时满足）

- [x] 控制面 v2 实施完成 ≥ 14/20 任务（T1-T10 + T16/T17/T18 + 任意 1 项 T11/T15）
- [x] 至少 2 个真实任务周期通过 Shadow 阶段（新任务原生 v2 + legacy 迁移走 import_legacy_snapshot 路径）
- [x] `compare_task_states` + `summarise_cutover` 显示 `ready` 列表 100% 覆盖新建任务
- [x] 远端 GitHub Ruleset 启用（债务 23 P0 containment T2 · 债务 16 Required Checks）· 旧本地 gate 不能 100% 阻断 → 必须有远端强制
- [ ] 独立 verifier agent 在 2 个真实周期中均给出 PASS（建议 ≥ 5/5 探针）
- [ ] 用户 acceptance 拍板（"按推荐全部拍板" → Enforce）

## Shadow → Enforce 节奏

| 阶段 | 触发 | 动作 |
|---|---|---|
| **Shadow** | 控制面 v2 实施完成 + Ruleset active | 双 Gate 并行：v2 投影 + 旧 doc 扫描 |
| **Enforce** | 双 Gate 一致 ≥ 2 个真实周期 | v2 投影为权威；旧 doc 扫描转为 advisory（仅 warning 不阻断） |
| **Retire** | Enforce ≥ 4 个真实周期 + 0 解释性 drift | 删除旧 doc 扫描逻辑 |

## 旧 Gate 退役清单（每条满足才可删除）

- [ ] `scripts/check-task.py::check_no_naked_done` 的"`[x]` 仅表示 implementation" 规则
  → 替换为 v2 projection 读 `verified` field
- [ ] `scripts/check_task_state.py` 的 task-state 三事实校验
  → 替换为 v2 projection 三事实
- [ ] `scripts/pre-commit` 4.51 task.yaml 校验
  → 保持（task.yaml 仍作为 v2 事件 schema 入口）
- [ ] `docs/templates/tasks-template.md` 的 `- [ ] T\d+` 段落
  → 替换为 v2 event chain 链接
- [ ] 各种"人工阅读 tasks.md"的状态判断
  → 替换为 `taskctl show <task_id>`

## 不要删除（永久保留）

- `docs/tasks/<id>/` 目录结构本身（user-owned narrative + human prose）
- `<!-- workflow-state:begin/end -->` marker 框架（TC-013 hand-edit 检测）
- v2 event 唯一机器真源（spec.md REQ-001）
- 5 段 retro.md 模板（§ 6 复盘 DOD）

## 实施记录

- T19 commit（pending）：本规则文件 + AGENTS.md § 6.12 + docs/DOD.md v2 投影条款
- 建议下一会话补：
  - `scripts/check-task.py::check_no_naked_done` 改造为读 v2 projection
  - `scripts/check_task_state.py` 改造为读 v2 projection
  - 双 Gate 一致性证明（用 T16/T17/T18 测试套件做集成测试）

## 元信息

- **位置**：`docs/rules/workflow-state-retire.md`
- **创建日期**：2026-08-09（T19 实施）
- **状态**：active · Shadow 期
- **下一次审查**：当 14/20 任务完成 + 2 个真实 Shadow 周期后