---
title: 6 步工作流 DOD 完成定义总表
date: 2026-06-27
updated: 2026-07-21
status: v2
tags: [DOD, 6步流程, 完成定义]
---

# 6 步工作流 DOD 完成定义总表

> 每一步必须同时满足：**文档 DOD 全过 + 用户明确验收**，才能进入下一步。
>
> 0 是调研前置，正式步骤为 1–6；旧“6 发布”已取消，PR/commit 即交付。
>
> L1 类型检查、L2 单元测试、L4 review 分布在步骤 4；步骤 5 只汇总 L3 整合与 L5 staging。

## 一、路径与产物总览

| 类型 | 路径模式 | 默认路径 | 条件产物 |
|---|---|---|---|
| 新功能 | `full-6` | 0→1→2→3→4→5→6 | product-doc 必填；UI 时 design/component；schema/API 按变更填写 |
| Bug | `fix-mini` | 0→4→6 | 回归测试必填；大型或跨模块 Bug 可升级 full-6 |
| 重构 | `refactor-6` | 0→1→2→3→4→5→6 | product-doc/design-spec 默认不写；不得改变业务行为 |
| P0 | `timebox` | T+30m→T+2h→T+24h→T+48h→T+72h | 先止血，24h 内补主账与回归测试 |

| 步骤 | 核心产物 | 进入下一步的人工 gate |
|---|---|---|
| 0 调研 | `research.md` | 用户确认任务理解、范围和路径模式 |
| 1 规格 | `product-doc.md` / `design-spec.md` / `spec.md` | 用户验收产品与设计决策 |
| 2 计划 | `plan.md` + 条件技术文档 | 用户选择推荐方案并拍板决策点 |
| 3 拆分 | `tasks.md` | 用户确认粒度、依赖和实施顺序 |
| 4 实现 | commits + tests + `test-cases.md` | 用户 review；每个 commit 通过 verifier |
| 5 验证 | `verify.md` | 用户确认 L3 + L5 证据 |
| 6 复盘 | `retro.md` + 规则沉淀 | 用户确认改进项和沉淀位置 |

## 二、0 步调研 DOD

- [ ] 路径模式明确且为 `full-6` / `fix-mini` / `refactor-6` / `timebox`
- [ ] 用自己的话复述任务，用户确认理解正确
- [ ] 已读 `docs/issues.md`、`git log -10`、`git status`
- [ ] 找到至少 3 个相关文件；P0 可先止血、T+2h 内补齐
- [ ] 依赖影响和至少 2 个风险点均有证据与缓解措施
- [ ] 产物落在 `docs/tasks/<date>-<type>-<topic>/research.md`

## 三、1 步规格 DOD

### 3.1 product-doc.md（仅新功能必填）

- [ ] 问题、目标用户、价值、MVP、成功指标五段齐全
- [ ] MVP 同时写“包含”和“不包含”
- [ ] 至少一个可量化成功指标和合格线
- [ ] 用户价值与项目价值均明确，关键产品决策由人确认

### 3.2 design-spec.md（涉及 UI/UX 时必填）

- [ ] 用户旅程、页面地图、线框、交互状态、视觉规范齐全
- [ ] 默认、hover、loading、success、error 状态均覆盖
- [ ] 继承现有项目视觉 token、导航、组件与图标体系
- [ ] 用户已审阅页面结构和关键交互

### 3.3 spec.md（full-6 / refactor-6 必填）

- [ ] 用户故事、Requirement+Scenario、边界、数据契约、测试场景齐全
- [ ] Requirement ≥1 且使用 SHALL
- [ ] Scenario ≥3，覆盖 happy、invalid、edge/failure
- [ ] 八类边界：空值、异常、并发、时序、安全、性能、兼容、国际化
- [ ] 引用 research；新功能同时引用 product-doc/design-spec 的适用项
- [ ] 文档写有用户验收人和日期

## 四、2 步计划与技术详细化 DOD

### 4.1 plan.md

- [ ] 至少两个真实可选方案，包含优缺点、兼容性、工作量和测试影响
- [ ] 明确推荐一个方案及证据，不写模糊二选一
- [ ] 风险带等级和缓解动作
- [ ] 至少一个需要用户拍板的决策点，并记录最终选择
- [ ] 引用 research/spec；product/design 文档按适用性引用或标注不适用

### 4.2 条件技术文档

| 文件 | 触发条件 | 最低要求 |
|---|---|---|
| `db-design.md` | schema/索引/迁移变化 | ER 图、字段约束、索引、forward/rollback、数据影响 |
| `api-spec.md` | 新增或修改 API | 接口清单、Request/Response、错误码、认证、测试要点 |
| `component-spec.md` | 新增或重构 UI 组件 | Props/State/Events、复用关系、边界、测试、页面 wireframe |

涉及 UI 时还必须完成 [`rules/design-mockup-workflow.md`](rules/design-mockup-workflow.md) 的三层设计产物；具体时机见该规则。

## 五、3 步拆分 DOD

- [ ] 每个任务 ≤1h AI 工作量，可独立验收
- [ ] 每个任务对应一个 commit 边界
- [ ] 每个任务映射到 spec Requirement/Scenario 和至少一个测试
- [ ] 依赖关系无环且实施顺序明确
- [ ] 有总估时；实施后记录实际耗时、commit 和偏差

## 六、4 步实现 DOD

- [ ] 每个代码任务按红→绿→refactor 执行，并保留失败/通过证据
- [ ] 新函数有 happy path，异常与边界有测试；Bug 有回归测试
- [ ] L1 类型检查和 L2 单元测试通过；核心 service 覆盖率目标 ≥80%
- [ ] 一个 task 对应一个 commit，commit message 包含任务编号
- [ ] commit 前先回写 `tasks.md` 的状态、实际耗时和 commit 历史
- [ ] 每个 commit 按 `CLAUDE.md §6.7` 运行独立 verifier；FAIL 必须修正或上报
- [ ] 阶段结束整合 `test-cases.md`
- [ ] 新增/修改测试通过 AST Harness Gate；无 `pass` / `...` / 无理由 skip / 占位标记
- [ ] 每条测试能指出需求失败时会变红的 oracle，不以“收集到/未抛异常”代替验证
- [ ] E2E 已列 Mock 边界；内部 Scheduler / Service / ORM / DB / API 不得被 Mock 后仍称真实 E2E
- [ ] 前端测试不位于 Next.js `pages/` / `app/` 路由树

## 七、5 步验证 DOD

- [ ] 引用步骤 4 已完成的 L1/L2/L4 证据，不重复把它们当独立 gate
- [ ] **L3 整合测试**：关键 API contract / E2E / 跨模块路径通过
- [ ] **L5 staging**：真实运行路径通过，有命令、日志、截图或浏览器证据
- [ ] 期望与实际逐场景记录；失败项不得写成通过
- [ ] 每条证据含 commit、命令、cwd、环境、时间、退出码及 passed/failed/skipped/xfail 分类计数
- [ ] 需求追踪矩阵能从 requirement 追到生产代码、测试和失败 oracle
- [ ] API/E2E 有 Mock 边界账本、真实数据库最终状态、重复执行和进程重启幂等证据
- [ ] 核心逻辑有一次“故意破坏后测试变红”的反证；启动、关闭路径均实测
- [ ] Vitest、typecheck、build、Playwright 分开记录，不用其中一个绿推导另一个绿
- [ ] workflow 与 GitHub required checks 分开核验；未配置 ruleset 不得声称能阻断合并
- [ ] `tasks.md`、`verify.md`、`retro.md`、issues/milestones 已完成事实对账
- [ ] 用户明确确认验证完成

> 任何一项未满足，`verify.md` 不算完成，不能进入复盘。

## 八、6 步复盘 DOD

- [ ] 数据完整：计划/实际耗时、任务数、commit 数、返工次数
- [ ] 做对与做错各至少一条，做错包含现象、根因和影响
- [ ] 调研偏差逐条修正
- [ ] 改进项有负责人、截止日期和沉淀位置
- [ ] 经验已写入 `CLAUDE.md` / `AGENTS.md` / DOD / 模板 / skill / `docs/issues.md` 至少一处
- [ ] 严重问题已按“Writer → oracle → Verifier → CI → 文档”写完整失效链
- [ ] 每个改进项注明机器约束位置和“已验证/待验证”，不把规则文件存在等同于生效

## 九、遗留项关闭 DOD（收尾动作，不是步骤）

- [ ] 用户明确要求关闭，而非仅提到“议题 / issue”
- [ ] 按 [`templates/issue-closure-template.md`](templates/issue-closure-template.md) 逐条核验
- [ ] 有可复现的代码、测试、文档或数据证据
- [ ] 仍需改代码时已重新分类，不强行关闭
- [ ] `docs/issues.md` 与相关 tasks/retro 状态同步

## 十、自动校验

```bash
python3 scripts/check-step.py research <research.md>
python3 scripts/check-step.py spec <spec.md>
python3 scripts/check-step.py plan <plan.md>
python3 scripts/check-step.py tasks <tasks.md>
python3 scripts/check-step.py implement <test-cases.md>
python3 scripts/check-step.py verify <verify.md>
python3 scripts/check-step.py retro <retro.md>
```

`ship` 已从 v2 删除；生产部署项目应另建部署 runbook，不得重新塞回本工作流。

## 十一、演进规则

- 新增 DOD：必须有真实失败案例
- 删除 DOD：必须证明已被其他 gate 稳定覆盖
- 修改量化指标：必须记录原因和影响
- 规则、模板、`check-step.py`、pre-commit 必须在同一变更中同步
