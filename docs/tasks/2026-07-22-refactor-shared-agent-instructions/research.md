# 🔧 调研报告 · 重构：统一 Codex / Claude 项目指令

> 日期：2026-07-22 · 调研人：Codex · 议题编号：N/A（项目规则文档去重，不登记为产品遗留议题）
> 路径模式：`refactor-6`

## 1. 任务理解（必填）

- **用户原话**：
  - “那你搞一个公共的吧 一起引用它”
  - “可以的 你调研下网上很多公司都怎么用的”
- **目标**：让 Codex 与 Claude Code 读取同一套项目规则，只维护一个权威来源，同时保留必要的工具专属说明。
- **重构目标**：
  - [x] 可维护性（消除两份大文件的重复维护）
  - [x] 一致性（避免 Codex 与 Claude 得到不同规则）
  - [x] 可读性（明确公共规则与工具专属规则的边界）
  - [x] 可验证性（能确认两个工具实际加载了同一主账）
- **不重构会怎样**：当前两份入口已经发生实质漂移。`CLAUDE.md` 有 493 行、27,723 bytes，`AGENTS.md` 有 317 行、15,999 bytes；前者新增的安全审查、决策同步、决策主账和 AI Agent 安全四道关没有同步到后者。继续双写会让同一任务因使用的工具不同而走不同流程。

## 2. 现状分析（必填）

### 2.1 重构对象

| 文件 | 状态 | 规模 | 关键事实 |
|---|---|---:|---|
| `AGENTS.md` | 未跟踪 | 317 行 / 15,999 bytes | Codex 当前入口；内容落后于 `CLAUDE.md` |
| `CLAUDE.md` | 已跟踪且有未提交修改 | 493 行 / 27,723 bytes | 相对 HEAD 为 `+69/-1`；不能直接覆盖 |
| `docs/rules/testing-rules.md` | 已跟踪 | 规则子文档 | 同时出现“CLAUDE.md 中保留”和“AGENTS.md 中保留”，已产生主账歧义 |
| `docs/DOD.md` | 已跟踪 | DOD 主文档 | 仍以 `CLAUDE.md §6.7` 作为主要规则来源 |
| `scripts/pre-commit` | 已跟踪 | 强制检查 | 注释和错误提示绑定 `CLAUDE.md §6.5` |

### 2.2 调用方 / 引用方清单

活跃 Markdown（排除 `docs/archive/**`）中，约 55 个文件提到 `CLAUDE.md`，只有 4 个文件提到 `AGENTS.md`。主要规范性调用方包括：

- `README.md:55` — 安全设计引用 `CLAUDE.md §6.10`
- `docs/DOD.md:105` — verifier gate 引用 `CLAUDE.md §6.7`
- `docs/README.md:108,121` — 把 `CLAUDE.md` 描述为完整流程入口
- `docs/rules/testing-rules.md:1-3,83` — 规则来源在两种入口名之间混用
- `docs/rules/design-mockup-workflow.md:225` — UI 工作流引用 `CLAUDE.md`
- `docs/templates/research-new-feature.md:69,94` — 新功能调研模板引用 Claude 专属入口名
- `scripts/pre-commit:121-134` — hook 提示绑定 `CLAUDE.md §6.5`
- `scripts/check-step.py:314` — 同时接受 `CLAUDE.md` / `AGENTS.md`

历史任务和归档文档里的 `CLAUDE.md` 是当时事实，不应为了表面统一而批量重写；应只迁移当前规范性入口和仍会执行的脚本提示。

### 2.3 当前测试覆盖

- 本次是文档配置重构，没有业务代码覆盖率指标。
- 当前没有自动检查两份入口是否同源，也没有验证 Claude 导入或 Codex 指令发现的测试。
- 实施后的替代验证应包括：
  1. 静态检查入口结构与引用目标存在；
  2. Claude Code 用 `/context` 确认加载；
  3. Codex 从仓库根启动并要求列出已加载指令源；
  4. 检查当前规范性文件不再把 `CLAUDE.md` 当成公共规则主账。

### 2.4 当前差异

`CLAUDE.md` 比 `AGENTS.md` 多出的公共规则主要包括：

- §0.2.1 安全审查清单；
- §6.8 调研文档决策同步；
- §6.9 决策记录规则；
- §6.10 AI Agent 安全四道关；
- §6.3 的安全提交自检。

工具专属差异主要包括：

- `AGENTS.md` 使用 Codex 的 `spawn_agent` 描述；
- `CLAUDE.md` 使用 Claude Code 的 `Agent` / `Workflow` / `ScheduleWakeup` / `SendMessage` 描述；
- `CLAUDE.md` 的 Workflow 章节不应原样进入跨工具公共规则，因为并非每个运行环境都有这些工具。

### 2.5 依赖关系

- **外部依赖**：Codex 的 `AGENTS.md` 发现规则、Claude Code 的 `@path` 导入语法、Git 对符号链接的支持。
- **内部依赖**：README、DOD、规则文档、调研模板、pre-commit hook、step checker 以及大量历史任务文档。
- **循环依赖**：当前无文件级循环；若入口互相引用（`AGENTS.md → CLAUDE.md → AGENTS.md`）则会形成逻辑循环，必须禁止。

## 3. 外部调研：主流项目如何处理

### 3.1 官方能力边界

| 来源 | 已确认行为 | 对 KnockWise 的含义 |
|---|---|---|
| [OpenAI Codex：AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Codex 原生读取 `AGENTS.md`，从仓库根到当前目录合并；默认组合上限 32 KiB | `AGENTS.md` 应保留为原生公共入口，不宜只留一个依赖模型主动二次读取的普通 Markdown 链接 |
| [Anthropic Claude Code：memory / CLAUDE.md](https://code.claude.com/docs/en/memory) | Claude Code 读取 `CLAUDE.md`，支持 `@path` 原生导入；官方明确建议已有 `AGENTS.md` 时在 `CLAUDE.md` 中写 `@AGENTS.md`；也允许符号链接 | `CLAUDE.md` 可以成为很薄的兼容入口，无需复制公共正文 |
| [VS Code 自定义指令](https://code.visualstudio.com/docs/agent-customization/custom-instructions) | 官方建议多 AI 工具场景使用根目录 `AGENTS.md` 作为共同指令 | 把 `AGENTS.md` 作为跨工具主账具有更好的生态兼容性 |

Anthropic 还建议每个 `CLAUDE.md` 目标控制在 200 行以内；当前 493 行明显过长。Codex 默认组合上限是 32 KiB；当前 `CLAUDE.md` 的公共内容若整体迁入 `AGENTS.md`，会接近该上限，因此不能只做机械拼接。

### 3.2 公开公司 / 大型项目样例

| 项目 | 做法 | 评价 |
|---|---|---|
| [Apache Superset](https://github.com/apache/superset/blob/master/CLAUDE.md) | `CLAUDE.md` 是指向 `AGENTS.md` 的符号链接 | 真正零漂移，但不能追加 Claude 专属规则；Windows 开发者创建/检出 symlink 可能有额外要求 |
| [Microsoft skills](https://github.com/microsoft/skills/blob/main/.github/plugins/deep-wiki/skills/wiki-agents-md/SKILL.md) | 生成权威 `AGENTS.md`，同时生成极薄的 `CLAUDE.md`，要求先读 `AGENTS.md` | 跨平台简单，但纯自然语言“请读取”弱于 Claude 官方的 `@AGENTS.md` 原生导入 |
| [AGENTS.md 开放约定](https://agents.md/) | 把 `AGENTS.md` 作为面向多种编码 Agent 的仓库级说明 | 支持将公共规则放在中立入口，而不是以某一家供应商命名的文件作为总主账 |

可归纳为三种企业实践：

1. **开放入口为主账，供应商文件做适配器**：最常见，也最适合多工具团队。
2. **符号链接到同一文件**：最强的一致性，适合不需要供应商专属说明、开发环境统一的团队。
3. **生成多份镜像并由 CI 防漂移**：适合工具不支持导入/链接的大型组织，但维护脚本和 CI 的成本最高。

## 4. 重构方案（必填，≥2 个）

| 维度 | 方案 A：`AGENTS.md` 为公共主账，`CLAUDE.md` 原生导入 | 方案 B：`CLAUDE.md` symlink 到 `AGENTS.md` | 方案 C：第三份公共文件 + 两个薄入口 | 方案 D：生成两份镜像 + CI 防漂移 |
|---|---|---|---|---|
| 思路 | 公共规则只写 `AGENTS.md`；`CLAUDE.md` 顶部 `@AGENTS.md`，下方仅放 Claude 专属内容 | 两个文件物理上是同一内容 | 新建 `AI_ASSISTANT_RULES.md`；两个入口都指向它 | 维护模板源，脚本生成 `AGENTS.md` / `CLAUDE.md` |
| 原生加载 | Codex ✅；Claude ✅（官方 `@` 导入） | Codex ✅；Claude ✅ | Claude ✅；Codex ⚠️ 没有 Markdown 原生 import，只能依赖自然语言再次读取或 symlink | 两者 ✅ |
| 单一主账 | ✅ | ✅ 最强 | ✅ | ⚠️ 生成产物仍有两份 |
| 工具专属规则 | ✅ 可在 `CLAUDE.md` 导入后追加 | ❌ | ✅ | ✅ |
| Windows / Git 兼容 | ✅ | 🟡 symlink 有限制 | ✅（若不用 symlink） | ✅ |
| 维护成本 | 低 | 最低 | 中 | 高 |
| 风险 | 🟢 低 | 🟡 中 | 🟡 中偏高 | 🟡 中 |
| 业界证据 | Anthropic 官方推荐；VS Code 多 Agent 建议 | Apache Superset | 通用但 Codex 缺原生导入支持 | 大型平台常见的兼容层思路 |

## 5. 风险评估（必填）

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| 覆盖当前未提交的 `CLAUDE.md` 69 行新增规则 | 🔴 | 实施时以当前工作树为源做语义合并，不从 HEAD 重建，不使用覆盖式写入 |
| 把 Claude 专属 Workflow 工具写入公共规则，导致 Codex 虚构工具 | 🔴 | 公共规则改为“使用当前环境实际暴露的独立 verifier 工具”；Claude 专属语法只保留在导入后的 Claude 段 |
| 机械合并后 `AGENTS.md` 接近 Codex 32 KiB 上限、Claude 上下文过长 | 🟡 | 删除重复解释与长反例；把教程/历史/memory 清单迁到 `docs/rules/`，入口只保留强制 gate 与路由 |
| symlink 在 Windows 或部分 Git 配置下退化成普通文本 | 🟡 | 推荐方案不用 symlink；若选方案 B，增加跨平台检出验证 |
| 55 个活跃引用仍把 `CLAUDE.md` 当公共主账 | 🟡 | 只更新规范性活跃文件；历史任务与 archive 保留原始事实 |
| `@AGENTS.md` 被误写进代码块而不触发导入 | 🟢 | 放在 `CLAUDE.md` 首个非注释内容处，并用 Claude `/context` 验证 |
| 两个入口互相引用产生循环 | 🔴 | 固定单向关系：`CLAUDE.md → AGENTS.md`，禁止反向引用 |

## 6. 输出建议（推荐方案）

### 6.1 单一推荐

推荐 **方案 A：`AGENTS.md` 作为公共权威主账，`CLAUDE.md` 使用官方 `@AGENTS.md` 导入，并只追加 Claude 专属内容**。

理由：

1. 同时走 Codex 与 Claude 的原生加载路径，不依赖 Agent 看见普通 Markdown 链接后“记得再读一次”。
2. Anthropic 官方文档直接推荐这种兼容方式，风险最可控。
3. 比 Apache Superset 的 symlink 更适合 KnockWise，因为现有 `CLAUDE.md` 确实包含 Claude 专属 `Agent` / `Workflow` 说明。
4. 不需要第三份公共文件；`AGENTS.md` 本身就是生态中立的公共文件，结构更少、主账更清楚。

### 6.2 推荐目标结构

```text
KnockWise/
├── AGENTS.md              # 公共规则唯一主账；Codex 原生读取
├── CLAUDE.md              # @AGENTS.md + 最小 Claude 专属适配
├── docs/rules/            # 被入口按任务路由读取的详细规则
│   ├── checklist.md
│   ├── testing-rules.md
│   ├── local-dev.md
│   └── agent-tooling.md    # 可选：长篇工具说明，不塞进入口
└── .agents/skills/         # Codex/通用项目技能
```

建议 `CLAUDE.md` 最终形态：

```md
@AGENTS.md

# Claude Code 专属补充

- 仅保留当前 Claude Code 环境真实支持、且无法用能力中立语言表达的规则。
```

### 6.3 内容迁移边界

- **迁入公共 `AGENTS.md`**：6 步流程、调研 gate、安全审查、TDD、tasks/decisions 同步、禁止修改区域、验证要求。
- **留在 `CLAUDE.md` 专属段**：Claude Code 的具体工具名与调用语法；但任何未经当前环境确认的 Workflow 能力不能作为公共硬约束。
- **迁到 `docs/rules/`**：长示例、反例全集、工具教程、memory 索引和历史缘由。
- **更新当前规范性引用**：README、DOD、规则文档、模板与 hook 提示统一引用 `AGENTS.md` 或中立的 `docs/rules/*`。
- **不批量修改**：`docs/archive/**` 与已完成任务文档中的历史 `CLAUDE.md` 引用。

## 7. 推荐路径

本任务按 `refactor-6`：

```text
0 调研（本报告）
→ 1 规格（定义公共/Claude 专属边界与加载契约）
→ 2 计划（列迁移文件、引用更新和验证命令）
→ 3 拆分（入口迁移 / 活跃引用迁移 / 加载验证）
→ 4 实现（文档重构；不涉及业务代码）
→ 5 验证（Codex + Claude 加载验证、静态引用检查）
→ 6 复盘（确认是否真正消除漂移）
```

这是文档去重任务，步骤 4 不需要业务单测，但仍需保留双 gate。若用户希望按“文档整理可即时做”例外缩短流程，应明确批准降级为 `0 → 4 → 5 → 6`。

## 8. 关键决策点（待用户确认）

| # | 决策 | 推荐 | 状态 |
|---|---|---|---|
| 1 | 公共主账是否直接使用 `AGENTS.md`，不再新建第三份文件 | 是 | ✅ 2026-07-22 用户：“按你说的来” |
| 2 | `CLAUDE.md` 使用 `@AGENTS.md` 还是 symlink | `@AGENTS.md` | ✅ 2026-07-22 用户：“按你说的来” |
| 3 | 是否同步压缩入口长度，把教程/长反例迁到 `docs/rules/` | 本轮不做，只提取公共规则 | ✅ 2026-07-22 用户缩小范围：“直接改吧，提取就行” |
| 4 | 是否更新所有历史任务里的 `CLAUDE.md` 引用 | 否，本轮也不扩散修改活跃引用 | ✅ 2026-07-22 用户缩小范围：“提取就行” |
| 5 | 是否按文档整理例外走短路径 | 是，`0 → 4 → 5 → 6` | ✅ 2026-07-22 用户：“来吧……继续” |

## 9. 调研 DOD 自检

- [x] 任务理解已经由用户确认
- [x] 已读 `docs/issues.md`
- [x] 已跑 `git log -10`
- [x] 已跑 `git status`
- [x] 已找到至少 3 个相关文件
- [x] 已列出主要引用方与依赖影响
- [x] 已核对当前测试 / 验证缺口
- [x] 已给出 4 个方案并作横向比较
- [x] 已给出单一推荐
- [x] 已列出至少 2 个风险及缓解方案
- [x] 已给出完整流程和建议缩短路径
