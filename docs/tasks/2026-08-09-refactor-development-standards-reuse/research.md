---
title: KnockWise 开发规范体系审计与复用化调研
type: research
step: 0
date: 2026-08-09
status: approved
tags: [research, governance, workflow, reuse]
related:
  - ../../issues.md
  - ../../DOD.md
  - ../2026-07-28-refactor-ai-coding-workflow-audit/research.md
---

# 🔧 调研报告 · 重构：开发规范体系审计与复用化

> 日期：2026-08-09 · 调研人：Codex · 议题：债务 22、债务 23 · 路径模式：`refactor-6`
>
> 本报告只完成步骤 0：核对事实、识别核心问题、比较复用方向。未修改现有规则、Hook、CI、业务代码或进行 Skill 安装。

## 1. 任务理解

- **用户原话**：「你查一下整体项目的开发规范 看看哪里存在问题 分析下是否存在核心问题 可以直接搞出一个复用的吗？」
- **用户确认**：2026-08-09 回复「对」，确认审计范围是整个开发规范体系，并且本轮先调研、不直接实施。
- **步骤 0 验收与范围决策**：2026-08-09 用户回复「我觉的那你可以把1 修复下」，验收调研结论并将后续范围收敛到 R-01；按 `refactor-6` 进入步骤 1 规格，不越级实施。
- **任务复述**：审计 `AGENTS.md`、DOD、rules、templates、Skill、Hook、CI、治理 checker、任务目录和在建工作流状态控制面，判断它们是否一致、可执行、可验证；识别表象问题背后的结构性根因；评估能否抽成跨项目可复用的治理资产。
- **重构目标**：
  - [x] 可维护性：降低规则散落和人工同步成本
  - [x] 一致性：统一政策、状态、证据和 Gate 语义
  - [x] 可测试性：让机器校验事实，不只校验 Markdown 形状
  - [x] 可复用性：拆开通用治理内核与 KnockWise 项目配置
  - [x] 安全性：保留最小权限、不可绕过 Gate 和人工审批边界
- **明确不做**：本轮不修现有冲突、不重写 6 步流程、不安装个人 Skill、不迁移历史任务、不碰并行工作区文件。
- **不重构会怎样**：事件状态控制面即使完成，也只能解决“机器执行状态”问题；规范正文仍可能在 `AGENTS.md`、DOD、模板、Hook 和 Skill 之间互相矛盾。规则越加越多，会继续提高上下文、维护和绕过成本，并把 KnockWise 专用约束错误传播到其他项目。

## 2. 现状分析

### 2.1 调研基线与证据

| 证据 | 当前结果 | 说明 |
|---|---|---|
| `docs/issues.md` | 已完整读取，共 1006 行 / 83,983 bytes | 债务 13、14、18、20、22、23 与本审计直接相关 |
| `git log -10` | HEAD `809fe41`，最近 10 个 commit 均围绕债务 23 控制面与状态记录 | 当前正在实施单一事件真源，不能另造竞争状态机 |
| `git status` | 分支 `feature/v40-product-foundation`，领先远端 3；存在用户及并行 Agent 的 modified/untracked 文件 | 本报告仅新增独立 task 目录，未碰已有改动 |
| `./scripts/start.sh` | rc=0，五个服务已运行 | 也证明“纯规范审计必须启动全栈”是路径触发过宽的实际例子 |
| 治理回归 | 已跟踪基线 278 passed / 0 failed | 测试绿不等于规范语义一致，现有套件没有覆盖跨文件政策冲突 |
| 并行 WIP | 未跟踪的 migration 实现/测试在审计期间出现 | 合并运行时为 279 passed / 4 failed；4 个失败全部来自并行 WIP，已排除出已提交基线判断 |

### 2.2 重构对象与规模

| 对象 | 规模 / 状态 | 当前职责 |
|---|---:|---|
| `AGENTS.md` | 474 行 / 27,335 bytes | 流程、测试、安全、状态、决策同步、退役规则 |
| `docs/issues.md` | 1006 行 / 83,983 bytes | 议题主账、历史结论、决策镜像、动态状态 |
| `docs/DOD.md` | 166 行 | 步骤完成定义与自动校验入口 |
| `docs/rules/` + templates + checker / Hook / taskctl | 已跟踪约 9559 行 | 交付物、模板、文本 checker、状态控制面、CI 接线 |
| `docs/tasks/` | 已跟踪 220 个文件、约 50,573 行 / 2.36 MB | 调研、决策、规格、计划、任务、验证、复盘与历史证据 |
| 强制启动上下文 | 1920 行 / 134,271 bytes | `AGENTS` + issues + DOD + checklist + testing rules + 项目 Skill |
| task 产物分布 | research 33、tasks 25、retro 22、verify 14、test-cases 7、task.yaml 12 | 路径、阶段和历史版本不统一，不能靠文件存在推断真实状态 |

### 2.3 调用方清单

1. **Codex / Claude Writer**：读取根规则、项目 Skill、task 文档并修改代码与状态。
2. **独立 Verifier**：读取 spec/plan/commit，运行测试并产生 PASS / FAIL 证据。
3. **本地 Hook**：按 staged path 运行测试、文档 checker、manifest 和状态检查。
4. **GitHub CI**：运行治理、测试质量、backend、frontend 等 job。
5. **`taskctl` / workflow-state**：记录事件、计算投影、绑定 commit 与测试证据。
6. **后续 Agent / 用户**：从 issues、task.yaml、tasks、verify、retro、Git/CI 恢复真实进度。
7. **模板与 Skill 使用者**：复制流程到新任务或其他项目，是复用错误传播的主要入口。

### 2.4 已确认的优点

1. “先复述、再调研、再实施”的方向正确，能减少需求误解和越级执行。
2. TDD、真实退出码、Harness oracle、Mock 边界和故意破坏反证，比只看测试数量成熟。
3. Agent 安全四关方向正确：不可信输入、最小权限、供应链 pin、人工 approval。
4. 本地 Hook 与 CI 复用同一 checker 的意图正确；INDEX 视图和 subprocess 回归是可靠实践。
5. 债务 23 已把状态问题推进到 append-only 事件、Actor 权限、CAS 和可重建投影，这部分有明确复用价值。
6. 已跟踪治理测试 278/278 通过，说明现有脚本具备继续演进的测试底座。

### 2.5 核心问题清单

| ID | 等级 | 问题 | 当前证据 | 是否被债务 23 覆盖 |
|---|---|---|---|---|
| R-01 | 🔴 核心 | **政策没有单一可编译真源** | `AGENTS.md` 要求 `- [x] ... ✅ DONE`；tasks 模板和 `check_task_state.py` 又禁止裸 DONE；Hook 的报错提示仍要求写被 checker 禁止的格式 | ❌ 状态事件源不能自动消除政策正文冲突 |
| R-02 | 🟠 核心 | **状态、证据、正文和视图仍混在一起** | `task.yaml`、tasks、verify、issues、milestones 各自手改；已知 completed task 的 manifest 仍可为 step 0/in_progress 且两个 checker 同时 PASS | ✅ 正在解决机器状态；尚未完成迁移/退役 |
| R-03 | 🟠 核心 | **流程图不闭合，阶段边界泄漏** | `fix-mini=0→4→6` 跳过 verify，但 retro 规则要求 verify 后才起草；重构 research 已要求两方案和推荐，plan 又重复同一职责；当前控制面任务在 step 4 已写阶段性 retro | ❌ 需要重新定义流程 profile 与条件 Gate |
| R-04 | 🟠 高 | **机器多校验文本形状，少校验证据语义** | `check_verify()` 只寻找 L3/L5 段与 PASS 词；`check_research()` 只找字符串；特殊 checker 未形成统一调度 | 🟡 部分可由事件证据模型承接 |
| R-05 | 🟠 高 | **声明的 Gate 与实际接线不一致** | Hook 对 backend 跑 pytest、对 frontend 只跑 tsc；注释称 `scripts/` 需要同步 tasks，条件却只含 backend/frontend；design/api/db/component checker 均未接 Hook/CI | ❌ 属于政策编译与能力探测问题 |
| R-06 | 🟠 高 | **治理写放大和上下文税过高** | 每次任务基线需读约 134 KB；每次决策最多人工同步六处；task 文档已约 5 万行；规则退役目录从未建立 | ❌ 单一状态只减少状态副本，不减少政策和文档副本 |
| R-07 | 🟠 高 | **通用内核与项目配置没有分层** | Hook 硬编码 backend/frontend；tasks checker 默认 L2 并强制产品埋点 §9；本地启动、seed 保护、MySQL/LiveKit 都写进根规则 | ❌ 这是复用化的主问题 |
| R-08 | 🔴 安全 | **跨工具 Skill 适配存在失效和陈旧指令** | `.claude/skills/intervue-dev` 指向不存在的相对目标，警告后仍保留 Docker、种子写入和旧架构命令；`.agents` 下的兼容 alias 才是精简版本 | ❌ 需要 adapter 生成与一致性 Gate |
| R-09 | 🟡 中 | **文档入口和权威指针漂移** | README 把完整启动说明指向 issues；docs/README 仍把 CLAUDE 当完整流程主账；实际 CLAUDE 又声明 AGENTS 是唯一主账 | ❌ 属于导航和生成视图 |
| R-10 | 🟡 中 | **规则退役机制只存在于文字** | `AGENTS.md` 已定义 §6.11，但没有 `docs/archive/rules-deprecated/`，也没有实际退役记录 | ❌ 需要可执行 policy lifecycle |
| R-11 | 🟡 中 | **流程治理强、基础工程规范弱** | 后端没有 Ruff/Black/Mypy gate；前端 package 无 lint/format script；同时流程与任务文档规模持续增长 | ❌ 应由项目 profile 声明基础质量命令 |
| R-12 | 🟡 中 | **模板/schema/checker 未闭环** | 12 个已跟踪 template/schema 文件未通过 frontmatter checker；frontmatter checker 未接 Hook/CI；5 个模板仍写“TODO 接入”，其中只有 product-doc 已实际接入 | ❌ 需要从 schema 生成或统一注册 checker |

### 2.6 核心根因

以上不是十二个互不相关的小问题，最终收敛到四个根因：

1. **职责混合**：政策（应该怎样）、状态（现在到哪）、证据（事实是什么）、视图（给人看什么）没有清晰分层。
2. **复制协议代替编译**：同一规则靠人工写进 AGENTS、DOD、模板、Hook、CI 和 Skill；没有机器可读 policy schema 生成各端 adapter。
3. **按文档数量治理，而非按风险治理**：默认完整 6 步和全栈启动覆盖过宽；Bug/P0 的短路径又不闭合，导致 Agent 只能临场解释。
4. **复用边界缺失**：KnockWise 的端口、目录、指标、种子保护和工具命令，与通用的 TDD、证据、权限和审批规则混在同一份政策里。

**核心判断**：项目确实存在核心问题。债务 23 正在修“状态控制面”，但还缺一个“政策控制面”；如果直接复制当前 `AGENTS.md` 做 Skill，只会把现有冲突、项目耦合和上下文成本一起复用。

### 2.7 当前测试覆盖与反例

| 检查 | 结果 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| 18 组已跟踪治理/状态测试 | 278 passed | 单个 checker、Hook 场景和 T1-T10 控制面行为符合各自测试 | 跨文件政策是否互相一致 |
| `check-task.py` 对已完成 CI auto-fix task | PASS | manifest 字段和局部 artifact 条件满足 | manifest 的 step 0/in_progress 与 tasks completed 是否冲突 |
| `check_task_state.py` 对同一 task | PASS | tasks 表局部状态符合格式 | task.yaml、verify、Git/CI 是否同一事实 |
| `check-frontmatter.py` 扫 templates | 12 个已跟踪文件失败 | schema 与历史模板存在断层 | 因未接 Hook/CI，不能阻断大部分模板漂移 |
| `check-step.py research/tasks` 对债务 23 | PASS | Markdown 包含要求的段落/关键词 | 事件控制面是否完成、远端 Gate 是否生效 |

### 2.8 依赖关系与改动影响

```text
通用政策 schema
  ├─→ 风险 profile / artifact matrix
  ├─→ Codex Skill / Claude adapter / AGENTS 入口
  ├─→ 模板与文档导航
  └─→ checker registry → local Hook → CI required checks

机器事件真源（债务 23）
  ├─→ task / test / verifier / acceptance / merge facts
  └─→ 可重建状态视图

KnockWise project profile
  ├─→ backend/frontend 命令与路径
  ├─→ protected seed / env / MySQL 数据
  ├─→ local-dev 五服务
  └─→ 产品指标与 UI 子流程
```

改通用政策会影响 `AGENTS.md`、DOD、rules、templates、checker、Hook、CI 和工具 adapter；改状态 schema 会影响现有 `taskctl/workflow_state`、迁移器和投影。两者必须通过接口对接，不能合并成一个巨大 YAML，也不能另建第二套事件真源。

### 2.9 安全审查

#### 官方安全依据

- GitHub Actions Secure use：最小权限、不可信输入隔离、第三方 Action 使用完整且来自原仓库的 commit SHA。
- GitHub Actions Script injections：PR、branch、commit、label 等 metadata 均可能成为不可信输入。
- OWASP LLM01 Prompt Injection：仓库文本、日志、Issue、网页内容不能因被模型读取就升级为控制指令。
- OWASP LLM06 Excessive Agency：减少 Agent 的功能、权限和自治范围，高影响动作保留人工批准。

#### 威胁模型

| 场景 | 攻击者能力 / 输入 | 攻击向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|---|
| T-01 复用 Skill 被仓库内容劫持 | 可修改 README、注释、Issue 或日志 | 间接 prompt injection 改写 policy 解释 | 越权改文件、跳过测试、泄露信息 | 🔴 | 根级受信 policy 与业务数据分离；Skill 只接受 schema 字段；外部文本只作证据 |
| T-02 初始化器过度写入 | 用户运行可复用 scaffold | 脚本覆盖现有 Hook、CI、AGENTS 或 secrets 配置 | 破坏项目、扩大权限 | 🔴 | 默认 dry-run；逐文件 diff；冲突 fail closed；写 Hook/CI 前人工确认；可回滚 |
| T-03 通用 profile 权限过大 | 新项目直接启用 high-risk 能力 | Skill 获得网络、secrets、push/merge 权限 | Excessive Agency 与供应链风险 | 🔴 | 默认只读 audit；执行 profile 最小权限；secrets 与非可信 checkout 分 job；高影响动作 approval |
| T-04 policy/config 被篡改 | 可提交 `.governance.yaml` | 降低测试或审批要求后让 CI 接受 | Gate 静默降级 | 🟠 | policy 变更走独立 review/required check；记录 schema/version/hash；禁止 Writer 自签 |
| T-05 第三方 Action 来源伪造 | 可编辑 workflow | 任意 40 位 hex 冒充合法 pin | CI 中断或执行错误供应链代码 | 🔴 | 校验 owner/repo/SHA provenance；网络失败为 BLOCKED；升级需审阅 |

#### 权限边界

```text
不可信：repo 正文 / PR / issue / CI log / 网页
                    │ 仅结构化数据与证据
                    v
┌──────────────────────────────┐
│ reusable Skill: audit/read   │  默认无 secrets、无 push、无网络写
└──────────────┬───────────────┘
               │ dry-run proposal
               v
        用户确认 scaffold / policy 变更
               │
               v
┌──────────────────────────────┐
│ deterministic local CLI      │  只写明确 repo 路径，可回滚
└──────────────┬───────────────┘
               │ commit
               v
┌──────────────────────────────┐
│ CI diagnostic / verifier     │  read-only、固定 commit、无 secrets
└──────────────┬───────────────┘
               │ verified evidence
               v
        protected merge / action job
        需要 required check 或人工 approval
```

#### 外部依赖与不可信输入

- 本步骤未新增第三方依赖、Action、网络写入或高权限配置。
- 复用实现优先使用 Python 标准库和现有 PyYAML；如引入 Action，必须固定完整 SHA 并核验来源。
- 不可信输入包括仓库 Markdown、源码注释、任务文档、PR/Issue metadata、commit message、CI 日志、测试输出、网页和模型输出。
- 净化策略：字段 allowlist、类型校验、长度限制、路径归一化、命令 argv 禁止 shell 拼接、输出只作为 evidence，不直接执行。

## 3. 重构方案

| 维度 | 方案 A：复制现有规范为大 Skill | 方案 B：分层治理 Skill + Repo Kit | 方案 C：独立治理平台 / Plugin |
|---|---|---|---|
| **思路** | 把 `AGENTS.md`、模板和脚本整体打包 | 通用 policy kernel + 风险 profile + 项目配置 + adapter + deterministic scripts | 把状态、策略、证据、UI 和多仓库管理做成独立服务或完整 Plugin |
| **改动范围** | 小 | 中；先抽 schema 与只读 audit，再接现有 taskctl | 大；需要独立产品、权限和部署 |
| **风险等级** | 🔴 高 | 🟠 中 | 🔴 高 |
| **兼容性** | 表面最高，实际复制所有耦合 | 可保留 KnockWise `refactor-6` 作为兼容 profile | 需要迁移和运维 |
| **测试影响** | 只能测 Skill 格式，难证语义 | schema/golden/subprocess/forward-test 可分层验证 | 需端到端、多租户和权限测试 |
| **复用质量** | ❌ 伪复用 | ✅ 真复用 | ✅ 但当前过度设计 |
| **工作量粗估** | 2-4h | 2-4 天做 MVP；状态控制面复用现有债务 23 | 2-4 周以上 |

### 3.1 方案 A：大 Skill

优点是快，可以立即复制；缺点是把 134 KB 启动上下文、KnockWise 端口/seed/指标、过时 adapter 和互相矛盾的状态规则一起带走。它只能“提醒 Agent”，不能让 Hook、CI 和远端 required checks 真正执行，因此不推荐。

### 3.2 方案 B：分层治理 Skill + Repo Kit（推荐）

建议复用资产暂命名为 `govern-ai-development`，不是一份巨型 Markdown，而是一个可审计、可脚手架化的 Skill：

```text
govern-ai-development/
  SKILL.md                    # 精简路由：何时 audit / init / validate / migrate
  agents/openai.yaml          # Codex UI 元数据
  scripts/
    governance.py             # audit / init --dry-run / validate / doctor
  references/
    policy-kernel.md          # 五个通用不变量
    risk-profiles.md          # tiny / standard / high-risk
    evidence-and-security.md  # Actor、证据、权限、供应链
  assets/
    repo-kit/
      governance.example.yaml
      AGENTS.adapter.md
      templates/
      ci-governance.yml
```

每个项目只维护一份机器配置，例如 `.governance.yaml`，声明技术栈命令、路径、受保护对象、风险 profile 和可选产物。Skill 负责理解与脚手架；deterministic CLI 负责校验；Hook/CI 负责强制；债务 23 的事件真源负责状态和证据。四层各自只有一个职责。

**建议的五个通用不变量**：

1. 任务先确认 scope、风险和授权边界，再产生写操作。
2. 状态只有一个机器真源，其他状态视图可重建。
3. 测试、verifier、用户验收、merge Gate 是不同 Actor 的正交事实，并绑定固定 commit。
4. 强制规则必须有 deterministic checker 和不可绕过的远端 Gate；Skill 文本不是安全边界。
5. policy 变化必须有版本、测试、迁移和退役记录，不能只增不减。

### 3.3 方案 C：独立平台 / Plugin

长期可把 Skill、状态服务、GitHub 集成和跨仓库 dashboard 做成 Plugin 或独立项目。它适合团队和多仓库，但当前只有单仓库、事件控制面仍在实施，立即平台化会把尚未稳定的 schema 固化，暂不推荐。

### 3.4 可直接复用与必须剥离的内容

| 可直接抽取 | 需要配置化 | 不应复用 |
|---|---|---|
| 任务理解确认、TDD、oracle、真实 rc、固定 commit verifier、安全四关 | 测试/type/lint/build 命令、风险 profile、产物矩阵、受保护路径、本地服务 | 50 题 seed 细节、固定端口、MySQL 真数据规则、KnockWise backlog |
| workflow-state 的 models/canonical/reducer/projector/actor policy | state ref 名、默认分支、task root、CI provider | `.claude/intervue-dev` 陈旧架构与 Docker/灌种命令 |
| subprocess/INDEX/CAS/golden test 模式 | Codex/Claude adapter、GitHub/GitLab CI adapter | 每次强制完整读取 1000 行 issues、人工同步六处 |
| fail closed、BLOCKED 不冒充 PASS | full-6/fix-mini/refactor/timebox 作为兼容 profiles | 所有项目默认 L2 埋点 §9、所有任务默认启动五服务 |

### 3.5 2026-08-09 范围决策

- ✅ **本轮只修 R-01**：建立政策单一真源及其 adapter / consumer 一致性契约。
- ✅ **步骤 1 已验收**：2026-08-09 用户回复「验收步骤 1，出方案」，规格边界冻结并进入步骤 2。
- ✅ **最简快速修复**：2026-08-09 用户回复「按照最简版 快速修复下冲突」，拒绝本轮建设 policy registry，将路径从 `refactor-6` 降级为 `fix-mini`，只统一既有 task 状态语义与直接 consumer。
- ✅ **复用既有状态语义**：债务 13 已确定 `[x]` 与裸 `DONE` 的语义，本任务不重新投票。
- ✅ **复用债务 23 状态控制面**：本任务不创建事件流、状态分支或第二套 task state。
- ⏸ **R-02～R-12 暂不夹带**：除非它们是验证 R-01 的最小必要反例，否则只保留为调研发现。
- ⏸ **技术载体待步骤 2 决策**：本步骤不提前锁定 YAML、Python DSL、生成器布局或 Skill 安装位置。

## 4. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 与债务 23 另建第二套状态机 | 🔴 | 复用现有事件 schema/CLI；新资产只定义 policy 接口，不复制 state store |
| 过早抽象未稳定实现 | 🔴 | 先做只读 audit + config schema + dry-run scaffold；enforce 等债务 23 Shadow 验证 |
| 大 Skill 再次挤占上下文 | 🟠 | `SKILL.md` 保持短；细节放 references；脚本无需加载全文即可运行 |
| 一个 profile 套所有项目 | 🟠 | tiny/standard/high-risk + project overlay；按风险触发，不按文件数量触发 |
| 自动脚手架覆盖用户现有文件 | 🔴 | 默认 dry-run、冲突拒绝、逐文件 diff、备份/回滚、写入前人工确认 |
| policy schema 与 adapter 漂移 | 🟠 | adapter 由 schema 生成；golden tests；禁止手改 generated 区 |
| Skill 只提示、远端仍可绕过 | 🔴 | 明确 Skill 非安全边界；必须配 Hook/CI/required checks，缺失写 BLOCKED |
| 跨工具能力不同 | 🟠 | 核心 policy 不写工具名；Codex、Claude 仅做薄 adapter；能力探测后选择路径 |
| 历史任务迁移污染事实 | 🔴 | legacy 一律 `LEGACY_UNVERIFIED`，不把历史 PASS 自动升级为可信事实 |
| 当前工作区并行冲突 | 🟠 | 新 task 目录隔离；实施前重新跑 git status；不读取/修改并行 WIP 的结论 |
| R-01 与债务 13/23 职责重叠 | 🔴 | policy 只定义规则与 consumer；状态事实继续由 workflow-state 管理；既有状态语义作为输入契约 |
| 为消除一个矛盾而全量重写规范 | 🟠 | 关闭条件限定为政策真源、生成/校验链和直接矛盾；R-02～R-12 不夹带 |

## 5. 输出建议

### 5.1 推荐方案

- **推荐：方案 B，做“可复用 Skill + Repo Kit”，不要直接复制当前整套规范。**
- **理由 1**：Skill Creator 的渐进加载模型适合把路由、references、scripts 和 assets 分层，能避免巨型 `AGENTS.md` 常驻上下文。
- **理由 2**：现有 `workflow_state` 已提供可抽取的机器状态底座，复用它比另建平台成本低。
- **理由 3**：真正的强制来自 deterministic checker、Hook、CI 和 protected merge，不来自提示词；Repo Kit 能把这些一起装配。
- **理由 4**：项目专用内容放 `.governance.yaml`，才能让同一 Skill 用于 Python、Node、单体仓库或其他项目，而不继承 KnockWise 的端口、seed 和指标规则。

### 5.2 推荐路径

```text
0 调研（本报告，2026-08-09 已验收）
→ 1 规格（当前）：冻结 R-01 的政策真源、consumer、adapter 与状态控制面边界
→ 2 计划：比较“个人 Skill / 独立源码仓 / Plugin”分发方式并拍板安装位置
→ 3 拆分：audit、init --dry-run、validate、adapter generation、迁移五组原子任务
→ 4 实现：TDD；先只读 audit，再 scaffold；每个 commit 独立 verifier
→ 5 验证：至少用 tiny Python、前后端 monorepo、高风险 Agent/CI 三类样例 forward-test
→ 6 复盘：删除被生成器覆盖的重复规则，真正执行规则退役
```

### 5.3 MVP 边界

**MVP 包含**：

- 精简 `SKILL.md` 与 `agents/openai.yaml`；
- `.governance.yaml` schema；
- `audit`、`init --dry-run`、`validate`、`doctor` 四个命令；
- risk profile 与 artifact matrix；
- Codex `AGENTS` adapter + 通用 CI template；
- 与现有 `taskctl` 的只读接口，不复制状态存储；
- golden、subprocess、exit-code 和三类 forward-test。

**MVP 不包含**：

- 多租户 Web 平台、dashboard、数据库服务；
- 自动 push/merge、自动写 secrets、自动启用远端 ruleset；
- 全量迁移 KnockWise 历史任务；
- Claude/Cursor/GitLab 等所有 adapter 同时首发；
- 把 KnockWise 业务 backlog、端口、指标和 seed 规则塞进通用内核。

### 5.4 需要用户拍板的决策点

1. **复用形态**：方案 B（Skill + Repo Kit）还是方案 C（独立 Plugin/平台）。推荐 B。
2. **源码与安装位置**：个人 `~/.codex/skills`、独立 Git 仓库，或先放 KnockWise 内孵化。推荐独立源码仓 + 个人 Skill 安装副本。
3. **兼容策略**：新项目继续默认 full-6，还是默认 risk profile，KnockWise 保留 full-6 兼容层。推荐后者。
4. **与债务 23 的时序**：现在先做只读 audit/schema，还是等 T11-T20 全完成再开工。推荐现在做只读层，enforce/迁移等待 Shadow 稳定。
5. **首发工具范围**：只做 Codex，还是同时做 Claude adapter。推荐 Codex 首发，adapter schema 从第一天保持工具无关。

### 5.5 本步骤结论

- **存在核心问题**：是。核心不是“规则少”，而是政策、状态、证据、视图未分层，且规则靠人工复制而非编译。
- **能否直接复用**：能复用原则、事件控制面、测试模式和安全边界；不能直接复用当前整份 `AGENTS.md`。
- **能否搞出一个可复用资产**：能，推荐 `govern-ai-development` Skill + Repo Kit；先做只读 audit 和 schema，再逐步接 enforce。
- **当前 Gate**：步骤 0 已验收；用户授权只修 R-01，当前进入步骤 1 规格。规格未验收前不进入技术方案或实施。

## 6. R-01 关闭条件

- [ ] 每条强制政策只有一个机器权威定义，其他文本是引用、生成视图或明确的项目 overlay。
- [ ] `AGENTS.md`、DOD、模板、Hook 提示和 Checker 对 `[x]` / `DONE` 的语义一致。
- [ ] 所有声明为强制的 consumer 均在注册表中可发现，并能验证已接线或明确不适用。
- [ ] 手改生成区域、重复 rule id、未知 consumer、adapter 漂移均能被确定性测试阻断。
- [ ] policy 不保存 implementation/test/verifier/acceptance 等运行状态，不与债务 23 竞争真源。
- [ ] 变更具有版本、兼容/迁移策略、回归测试和退役入口。
- [ ] 步骤 4 独立 verifier 对照固定 spec/commit 给出 PASS，步骤 5 完成 Hook/CI 整合证据。

## 7. 决策后风险同步

| 风险 | 2026-08-09 决策后的缓解 | 状态 |
|---|---|---|
| 一次性修十二项导致范围失控 | 只修 R-01；其余发现不夹带 | ✅ 已收敛 |
| 与债务 23 形成双状态源 | policy 只描述规则和 consumer，运行状态继续读取既有事件投影 | ✅ 规格约束 |
| 直接按方案 B 实施而跳过 Gate | 当前只写 `spec.md`，技术载体留给步骤 2 | ✅ 已阻断 |
| 只改 `✅ DONE` 文案而未修根因 | 关闭条件同时要求单一政策定义、adapter 和 consumer coverage | ✅ 已纳入 |
| 步骤 2 把政策层误做成状态服务 | 已验收 spec 明确 policy 不持有运行事实；方案必须复用现有 governance 入口 | ✅ 已冻结 |
| 最简修复被误报为完整 R-01 关闭 | 本轮只关闭直接语义冲突；policy 单一真源与复用资产明确暂缓 | ✅ 已限界 |

## 8. 用户决策清单

| # | 决策项 | 2026-08-09 决策 | 状态 | 权威记录 |
|---|---|---|---|---|
| D-001 | 调研是否验收、后续修什么 | 「我觉的那你可以把1 修复下」→ 只修 R-01，进入步骤 1 规格 | ✅ 已决策 | [`decisions.md`](decisions.md) |
| D-002 | 步骤 1 是否验收 | 「验收步骤 1，出方案」→ 冻结 spec，进入步骤 2 | ✅ 已决策 | [`decisions.md`](decisions.md) |
| D-003 | 具体实施范围 | 「按照最简版 快速修复下冲突」→ 不做 registry；降级 `fix-mini`，直接 TDD 修四个 active consumer | ✅ 已决策 | [`decisions.md`](decisions.md) |

## 自检清单

- [x] 重构目标明确，不是笼统“让规范更好”
- [x] 不重构的具体后果已说明
- [x] 调用方清单不少于 3 个，并用全局搜索核对
- [x] 当前治理测试覆盖已查：已跟踪基线 278 passed
- [x] 方案对比不少于 2 个，含范围、风险、兼容、测试和工作量
- [x] 推荐方案引用了仓库证据与 Skill 分层原则
- [x] 已读 `docs/issues.md`、`git log -10`、`git status`
- [x] 已列依赖影响和不少于 2 个风险点
- [x] 涉及 Agent/CI/网络/文件系统，已完成官方安全资料、威胁模型、权限边界、外部依赖和不可信输入审查
- [x] 已给出完整 `refactor-6` 路径建议
