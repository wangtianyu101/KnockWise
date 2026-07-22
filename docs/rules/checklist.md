# 6 步工作流阶段交付物清单

> **版本**：v2 · 2026-07-21
>
> **权威完成定义**：[`../DOD.md`](../DOD.md)。本文件只回答“每一步要交什么”，不再保留旧 5/7 步阶段编号。

## 0 调研

| 项目 | 要求 |
|---|---|
| 产物 | `docs/tasks/<date>-<type>-<topic>/research.md` |
| 路径模式 | new-feature=`full-6`；bug=`fix-mini`；refactor=`refactor-6`；P0=`timebox` |
| 基线 | `docs/issues.md` + `git log -10` + `git status` + 至少 3 个相关文件 |
| 内容 | 任务理解、现状、依赖、风险、建议路径 |
| 人工 gate | 用户确认复述、scope 和路径模式 |

## 1 规格：业务契约与三脑交汇

| 文档 | 触发条件 | 主导 | 内容边界 |
|---|---|---|---|
| `product-doc.md` | 仅新功能 | 人 | 为什么做、给谁、MVP、成功指标 |
| `design-spec.md` | 涉及 UI/UX | 人/设计 | 用户旅程、页面、交互、视觉，不写组件实现 |
| `spec.md` | full-6/refactor-6 | AI 起草、人验收 | Requirement+Scenario、边界、数据契约、测试场景 |

### 规格阶段必须遵守

- 业务决策由人做，AI 只能提炼、补缺和列选项。
- `spec.md` 是机器可读业务契约，不放 ORM、迁移工具、UI 库等技术选型。
- 涉及 UI 时，先按 [`design-mockup-workflow.md`](design-mockup-workflow.md) 完成可审阅设计，再进入技术组件定义。
- 用户明确验收后才能进入步骤 2。

## 2 计划与技术详细化

| 文档 | 触发条件 | 必需内容 |
|---|---|---|
| `plan.md` | full-6/refactor-6 | ≥2 方案、单一推荐、风险、决策记录、估时 |
| `db-design.md` | schema/索引/迁移变化 | ER、字段约束、索引、forward/rollback、数据影响 |
| `api-spec.md` | 新增/修改 API | 接口清单、Request/Response、错误码、认证、测试 |
| `component-spec.md` | 新增/重构组件 | Props/State/Events、复用、边界、测试；引用已验收 mockup |

### 计划阶段必须遵守

- `plan.md` 先给方案，再由用户拍板；不得直接实施推荐方案。
- 技术文档只在触发条件满足时创建，不用空模板凑齐四份。
- UI 技术详细化必须继承步骤 1 已验收的页面与视觉系统，不重新设计产品。

## 3 拆分

产物：`tasks.md`。

- 每个任务 ≤1h AI 工作量。
- 每个任务一个 commit 边界。
- 每个任务映射 Requirement/Scenario 和测试。
- 写清依赖、实施顺序、文件范围、估时。
- 用户验收粒度后才能开始步骤 4。

## 4 实现

产物：代码、自动化测试、commits、`test-cases.md`、持续更新的 `tasks.md`。

### 每个 task 循环

1. 先写失败测试并确认红灯。
2. 写最小实现并确认绿灯。
3. refactor，跑相关测试与类型检查。
4. 回写 `tasks.md` 状态、实际耗时和 commit 历史。
5. 一个 task 一个 commit。
6. 启动独立 verifier，对照 spec/plan、跑测试并实测行为。
7. FAIL 则修复并重新验证；不收敛时报告用户。

### 分布式质量活动

- L1：类型检查。
- L2：单元测试与覆盖率。
- L4：用户 review + 独立 verifier。

## 5 验证

产物：`verify.md`。

- 引用步骤 4 的 L1/L2/L4 证据。
- L3：整合测试、API contract、关键 E2E。
- L5：在 staging 或本机完整服务上跑真实用户路径。
- 每个场景记录期望、实际、日志/截图和结论。
- 用户明确说验证完成后，自动起草步骤 6 的 retro。

## 6 复盘

产物：`retro.md` + 至少一处长期规则更新。

- 量化计划/实际耗时、任务、commit、返工。
- 记录做对、做错、根因和影响。
- 修正 research 阶段的事实偏差。
- 改进项写负责人、截止日期、沉淀位置。
- 更新 `CLAUDE.md` / `AGENTS.md` / DOD / 模板 / skill / `docs/issues.md`。
- 用户确认改进项后任务闭环。

## 非完整路径

| 类型 | 默认路径 | 关键约束 |
|---|---|---|
| Bug | 0 `fix-mini` → 4 回归修复 → 6 | 大型/跨模块 Bug 升级 full-6 |
| 重构 | 0→1→2→3→4→5→6 | 不写 product-doc，默认不写 design-spec；不改业务行为 |
| P0 | timebox | 先止血，24h 内补 `docs/issues.md` 和回归测试 |
| 遗留项关闭 | 收尾核验，不是实施路径 | 按 [`../templates/issue-closure-template.md`](../templates/issue-closure-template.md)；需改代码则重新分类 |

## 通用禁止项

- 未经用户明确指令跨步骤。
- 为了“文档齐全”生成不适用的空文件。
- 在步骤 1 提前锁定技术库、SQL 或具体实现。
- 把测试无法运行写成通过。
- 完成 task 后不更新 `tasks.md`。
- 只在 task/retro/TODO 记录长期问题而不登记 `docs/issues.md`。
