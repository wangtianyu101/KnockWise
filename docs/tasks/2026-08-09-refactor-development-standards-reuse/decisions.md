---
title: 开发规范政策单一真源 · 决策主账
type: meta
step: 1
date: 2026-08-09
status: in-review
tags: [decisions, governance, policy, single-source]
related:
  - research.md
  - spec.md
  - ../../issues.md
---

# 开发规范政策单一真源 · 决策主账

## 1. 权威定位

本文件是本任务的决策最权威详细主账。

- 调研事实与方案证据：[`research.md`](research.md)
- 当前规格：[`spec.md`](spec.md)
- 长期议题状态：[`docs/issues.md`](../../issues.md)
- `research.md` § 8 与 `docs/issues.md` 只保留简表和链接，不重复完整理由。

## 2. 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| D-003 | 2026-08-09 | 步骤 2 方案取舍与实施范围 | 不做 policy registry；最简 `fix-mini` 直接修语义冲突 | ✅ 已决策 · 已提交 | research § 3.5/§ 8；spec 修订；commit `99dde16` |
| D-002 | 2026-08-09 | 步骤 1 规格验收与步骤 2 授权 | 验收 spec；进入技术方案比选，不实施 | ✅ 已决策 | spec.md / plan.md / task.yaml |
| D-001 | 2026-08-09 | 调研验收与修复范围 | 只修 R-01 政策单一真源；进入步骤 1 规格 | ✅ 已决策 | research § 3.5 / § 8；spec.md |

## 3. 决策详细记录

### D-001 · 只修 R-01 并进入步骤 1

- **日期**：2026-08-09
- **决策项**：整体规范审计完成后，是不处理、只修核心问题 1，还是一次处理全部十二项发现。
- **选项列表**：
  1. 保持现状，只保留审计报告。
  2. **只修 R-01：建立政策单一真源与 adapter / consumer 一致性。**
  3. 一次性处理 R-01～R-12 并制作完整复用 Skill。
- **选择**：✅ 选项 2；验收步骤 0，按 `refactor-6` 进入步骤 1 规格，不越级实施。
- **用户原话**：「我觉的那你可以把1 修复下」。
- **理由**：
  1. R-01 是多个文档和 Gate 互相矛盾的上游根因，优先修复能减少继续扩散。
  2. 只改 `✅ DONE` 文案只能消除一个症状，必须同时建立权威政策定义和 consumer coverage。
  3. R-02 已由债务 23 的事件控制面实施，不应在本任务创建竞争状态机。
  4. 一次处理十二项会混入基础工程、流程路径、Skill 适配和文档导航，无法形成可验收的原子范围。
- **影响文件**：本任务 `research.md`、`spec.md`、后续 `plan.md/tasks.md`；实施阶段预计影响政策定义、adapter、Checker/Hook 提示及其测试。
- **关联决策**：债务 13 的状态语义决策、债务 23 的事件真源决策；均复用、不重开。

### D-002 · 验收步骤 1 并进入技术方案比选

- **日期**：2026-08-09
- **决策项**：是否接受政策唯一权威、adapter 一致性、consumer coverage、状态边界和生命周期规格，并进入步骤 2。
- **选项列表**：
  1. 退回步骤 1 修改规格。
  2. **验收步骤 1，进入步骤 2 比较技术方案。**
  3. 跳过方案与拆分，直接修改 Hook/Checker。
- **选择**：✅ 选项 2；冻结 `spec.md`，授权起草 `plan.md`，不授权实施。
- **用户原话**：「验收步骤 1，出方案」。
- **理由**：
  1. Spec 已覆盖唯一 authority、派生 adapter、consumer 接线、状态分离与政策生命周期。
  2. YAML、Markdown 或 Python code-first 均可能满足行为契约，需要在步骤 2 比较兼容性和测试代价。
  3. 债务 23 正在实施 T18/T19，先确定技术边界才能避免并行文件冲突和双真源。
- **影响文件**：`spec.md`、本文件、`research.md`、`docs/issues.md`、`task.yaml`、新增 `plan.md`。
- **关联决策**：D-001。

### D-003 · 采用最简版快速修复直接冲突

- **日期**：2026-08-09
- **决策项**：采用完整 policy registry，还是只修当前已确认的 task 状态语义冲突。
- **选项列表**：
  1. 按 plan 推荐实施 YAML registry + adapter + consumer coverage。
  2. **最简修复：统一现有权威语义、Checker、模板和 Hook 提示。**
  3. 不做任何修改。
- **选择**：✅ 选项 2；路径由 `refactor-6` 降级为 `fix-mini`，用户原话同时授权直接实施。
- **用户原话**：「按照最简版 快速修复下冲突」。
- **冻结语义**：
  - `[x]` 只表示 implementation 已落入 commit。
  - `[x]` 可与 test/verifier FAIL 共存，失败不否定实施事实。
  - 裸 `✅ DONE` 禁止，因为它会混合 implementation、test、verifier 和 acceptance。
  - 阶段是否完成继续由 acceptance / workflow-state 决定。
- **理由**：
  1. 用户明确优先速度和最小改动，不要求本轮制作复用资产。
  2. 债务 13 的决策主账与 research 已给出正交事实语义，无需另建配置层。
  3. 债务 23 T19 已提交，最小修复可直接基于新 HEAD 完成，不再与并行 T19 冲突。
  4. 同时修 Checker、模板、AGENTS 和 Hook 提示，才能避免只改文案后的残余冲突。
- **影响文件**：`AGENTS.md`、`docs/templates/tasks-template.md`、`scripts/pre-commit`、`scripts/check_task_state.py`、治理回归测试、旧状态 spec 的勘误、本任务文档。
- **关联决策**：D-001/D-002；取代 `plan.md` 推荐组合，但不撤销已验收的事实调研。

## 4. 决策落地追踪与元信息

| 决策 | 落地点 | 状态 | 证据 |
|---|---|---|---|
| D-001 | `research.md` § 3.5 / § 7 / § 8 | ✅ 已同步 | 2026-08-09 用户原话 |
| D-001 | `docs/issues.md` 债务 25 | ✅ 已同步 | 议题主账链接本文件 |
| D-001 | `spec.md` | ✅ 已验收 | 2026-08-09「验收步骤 1，出方案」 |
| D-002 | research/spec/issues/task 状态镜像 | ✅ 已同步 | 当前步骤 2 `in_progress` |
| D-002 | `plan.md` | 🟡 已起草，待步骤 2 验收 | 三方案、单一推荐、风险和决策点 |
| D-003 | `plan.md` | ⏸ 已归档 | 完整 registry 方案不在本轮实施 |
| D-003 | 最小 TDD 修复 | ✅ commit `99dde16` | 3 focused + 36 governance PASS；pre-commit 全量后端 1081 PASS |
| D-003 | 固定 commit 独立验证 | ✅ 第二轮 PASS | `99dde16` 首轮仅文档漂移 FAIL；`818f08f` 修正后 36 tests + 全部治理检查 PASS |

- **位置**：`docs/tasks/2026-08-09-refactor-development-standards-reuse/decisions.md`
- **创建日期**：2026-08-09
- **决策总数**：3
- **已决策数**：3
- **待确认数**：0
- **暂缓数**：0
- **取消数**：0
- **当前阶段**：最简修复已提交 `99dde16`，证据修正 `818f08f` 经第二轮固定 commit verifier PASS；用户 acceptance 待确认。
