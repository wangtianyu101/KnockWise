---
name: research-ai-workflow-engine
description: 0 步调研 · 新功能：把 6 步工作流 + 动态组件做成可复用工程化产品
date: 2026-07-06
status: 调研中
trigger: "调研 新功能：AI 协作工作流引擎"
type: new-feature
path-mode: full-6
---

# 🔍 调研报告 · 新功能：AI 协作工作流引擎

> 日期：2026-07-06 · 调研人：Claude (MiniMax-M3)
> 路径模式：**full-6**（跨 ≥ 3 文件，影响后端 + 协议层 + Skill + docs）

---

## 1. 任务理解（必填）

- **用户原话**：
  - "百度 AI coding 打算建立工作流，之后可以动态扩展组件，来完成 AI coding"
  - "比如 claude 或者 codex 我搭建完了一个工作流 怎么接入这些 agent 呢"
  - "那这个要变成可服用的工程化的怎么用呢？"
  - "我觉的你可以考虑考虑 先规划好 调研一下"

- **AI 复述**：
  把 Intervue 项目自身的 **6 步 AI 协作工作流**（0 调研 → 1 规格 → 2 计划 → 3 拆分 → 4 实现 → 5 验证 → 6 复盘）从「个人 SOP」**工程化**为一个**可复用产品**：
  - **核心能力**：工作流调度引擎 + 动态组件注册（运行时扩展）
  - **接入方式**：以 **MCP Server**（主）+ **Claude Code Skill**（辅）+ **Hooks**（守护）三层协议，让 Claude Code / Codex CLI / Cursor 等 agent 都能调用
  - **产品形态**：L1-L3 渐进式交付（个人模板 → CLI → 平台）
  - **差异化**：vs Dify/Coze（封闭 SaaS）做 **本地优先 + 协议开放**；vs LangGraph（执行引擎）做 **人机协作流程**

  ⚠️ **复述不对请打断**。

- **涉及模块**：
  - 后端：新增 `backend/workflow/` 目录（工作流引擎 + 组件注册中心 + MCP server）
  - 协议层：新增 `.claude/skills/ai-workflow/SKILL.md` + 改 `settings.json`（Hooks）
  - 文档：新增 `docs/workflow/`（架构 + 协议 + 组件开发指南）
  - 集成：复用 `backend/agents/interview_graph.py`（LangGraph）+ `backend/services/*`（组件化）

- **估时**：
  - L1 个人模板：1 天（8h）
  - L2 CLI 骨架 + 1 个示例：1 周（40h）
  - L3 动态组件 + 完整工程化：2-3 周（80-120h）

---

## 2. 现状扫描（必填）

### 2.1 相关文件（核心 ≥ 3）

| 文件 | 作用 | 状态 |
|---|---|---|
| `backend/agents/interview_graph.py` | LangGraph StateGraph 完整定义（select_question / ask / receive / evaluate_route / followup / report） | ✅ 已实现，但**未被 service 走**（见 Issue A）|
| `backend/services/interview_service.py` | InterviewSessionManager，**直接调 LLM**绕开 graph | 🟡 已经是"假 LangGraph" |
| `.claude/skills/intervue-dev/SKILL.md` | 项目级 Skill（介绍 + 关键文件路径） | ✅ 已有，**但只描述项目，不驱动工作流** |
| `docs/issues.md` 议题 A | graph 写了但没用上 | 📋 待讨论 |
| `docs/issues.md` 议题 E | 现在的"假 LangGraph"要不要换 | 📋 待讨论 |
| `docs/issues.md` 议题 F | 零 trace / metrics / structured log | 📋 待讨论 |
| `~/Obsidian/coding/AI代码工具使用心得/7步工作流最终版/全局流程.md` | 6 步工作流完整定义（v2 已精简） | ✅ 已沉淀 |
| `docs/CODE-MOCK.md` | 项目完整架构文档 | ✅ 参考 |
| `docs/api/README.md` | 1047 行 API 全量定义 | ✅ 后续组件化参考 |
| `backend/services/profile_settlement_service.py` | 22k 行服务 — **最大服务**，可作为"组件化抽离"参考 | 🟡 候选 |
| `backend/services/summary_service.py` | 20k 行服务 — 同上 | 🟡 候选 |
| `backend/core/limiter.py` | 新增的 slowapi 限流器（git status untracked） | 🟢 模式参考 |

### 2.2 相关议題（来自 `docs/issues.md`）

- **A** — LangGraph StateGraph 写了但没用上 🔥 **直接相关**
- **E** — AI Agent 框架是"假 LangGraph" 🔥 **直接相关**
- **F** — 零可观测性 🔥 **直接相关**（工作流引擎必须自带 observability）
- D — 跨模块数据流，部分相关（工作流组件化能促进跨模块打通）
- B — `interview.py` 803 行拆分，无关
- C — 语音架构 3 套并存，无关

**议題沉积情况**：
- A 沉积约 1 个月（从 V1 闭环后就在）⚠️
- E 沉积约 1 个月 ⚠️
- F 沉积约 1 个月 ⚠️
- **本次调研**正是同时解决 A + E + F 的契机（用工作流引擎统一抽象 + 自带可观测 + 真用 LangGraph）

### 2.3 最近相关改动

```bash
git log --oneline -15
```

| commit | 摘要 | 日期 |
|---|---|---|
| `fc49243` | feat(review): V2 L4 review 报告（11 commits + 14 已推 + 风险点）| 7-03 |
| `e009891` | fix(retro): 标改进项 #7 完成（antd 装好 + 16 V2 测试通过）| 7-03 |
| `9631d2d` | fix(ui): 装 antd 6.5 + icons + recharts + 16 V2 组件测试 | 7-03 |
| `ef8923f` | feat(docs): V2 完整 0-3 步文档 | 7-02 |
| `dca9def` | feat(retro): V2.5 复盘 + CLAUDE.md + api README | 7-02 |
| `a3db146` | feat(verify): V2.4 验证文档（5 层 gate · L1-L3 全过）| 7-02 |
| `cb19140` | feat(ui): V2.3-T25 新建 /profile 页 + nav 加画像入口 | 7-02 |
| `6d9c2e1` | feat(ui): V2.3-T24 RecentSedimentsCard + 嵌入 knowledge.tsx | 7-02 |
| `0e455a3` | feat(api): V2.3-T20-T22 6 端点 + 14 测试 | 7-02 |
| `e424d58` | feat(services): V2.3-T19 weekly/monthly/sync_daily_to_obsidian 实施 | 7-02 |

**相关路径 grep**：
```bash
git log --oneline -10 -- backend/agents/ backend/services/ .claude/
```
最近 5 个 commit 都在做 V2 沉淀层（services + api + ui），**和本调研不重叠**，可以独立推进。

### 2.4 类似功能怎么实现的（必填，找 1-2 个）

- **参考 A**：`backend/services/interview_service.py` — `InterviewSessionManager` 类
  - **用了什么模式**：state machine + MemorySaver checkpointing + JSON snapshot 持久化
  - **可借鉴**：状态机 + checkpoint 模式
  - **缺陷**：状态字段手维护、不可观测、没有动态扩展

- **参考 B**：`backend/agents/interview_graph.py` — `build_interview_graph()`
  - **用了什么模式**：LangGraph StateGraph + 节点 + 边 + 条件路由
  - **可借鉴**：声明式 workflow 定义
  - **缺陷**：被 service 绕开，没真用上

- **参考 C（外部）**：Dify / Coze / n8n / Mastra（公开产品）
  - **Dify**：YAML DSL + 可视化拖拽 + 插件市场
  - **Mastra**：TypeScript 原生，工具动态注册
  - **MCP 协议**：Anthropic 推动的工具 USB-C 事实标准
  - **可借鉴**：DSL + 插件 + 标准化协议

---

## 3. 依赖发现（必填）

### 3.1 改这些文件会影响

| 文件 | 影响 |
|---|---|
| `backend/agents/interview_graph.py` | 工作流引擎可能复用其 LangGraph 定义 — 需改 | 
| `backend/services/interview_service.py` | 工作流引擎可能接管 session 管理 — 需改（但**不破坏**现有行为，向后兼容）|
| `.claude/skills/intervue-dev/SKILL.md` | 可能要更新（项目 Skill 描述）|
| `CLAUDE.md` | 6 步流程已经在 § 一定义，**不动**（工作流引擎是 6 步的工程化实现）|
| `docs/DOD.md` | 新增工作流引擎的 DOD 项 |
| `docs/README.md` | 文档地图加新目录 |
| `backend/requirements.txt` | 加 `mcp[cli]>=0.5`（如用 MCP server）|
| `backend/main.py` | **不动**（MCP server 独立进程，不走 FastAPI）|

### 3.2 需要先改的

| 文件 | 为什么 |
|---|---|
| **无硬依赖** | 全新模块，不阻塞其他工作 |
| `docs/issues.md` 议题 A/E | 建议**同步解决**（工作流引擎正好是真用 LangGraph + 解决假 LangGraph）|
| `docs/issues.md` 议题 F | **必须解决**（工作流引擎自带可观测）|

### 3.3 调用方清单（改之前必查）

- `backend/api/interview.py:80-150` — 当前直接调 LLM，**改造前**必须确认不破坏 API
- `backend/api/v2_settlement.py` — 调 SummaryService / ProfileSettlementService / ObsidianSedimentService，**暂不涉及**
- `frontend/pages/interview.tsx` — 用户界面，**不动**
- `.claude/skills/intervue-dev/SKILL.md` — 项目级 Skill 描述，**不破坏性更新**

---

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| **重复造轮**：项目已有 LangGraph 0.3.18 + session manager，自己搞工作流引擎可能与现有架构冲突 | 🔴 | 调研阶段先做 **小 POC 验证 LangGraph 复用可行性**；不破坏现有 `interview_graph.py`，新模块独立 `backend/workflow/` |
| **V2 沉淀层未稳定**：`git status` 有 3 个 modified + 1 个 untracked（限流器），主线 V2 还在推进 | 🔴 | **新功能独立分支**（`feat/ai-workflow-engine`），不在 V2 主线打转；要求 V2 5 验证完成后再合入 |
| **议題 A/E/F 沉积**：3 个相关议題都沉积 1 月，本质是同一类问题 | 🟡 | 本次新功能**同时解决**这三个议題（工作流引擎 = 真用 LangGraph = 自带可观测）|
| **协议标准化难**：MCP / Skill / Hooks 三层协议在不同 agent 上支持度不同 | 🟡 | 调研阶段先**实测 1 个完整 demo**（如 Claude Code + MCP server），验证协议可行性 |
| **动态组件协议设计难**：Pydantic schema 设计错了后期重构痛苦 | 🟡 | 1 步 spec 阶段**重点 spec 协议**，找 2-3 个参考实现（LangGraph tool / MCP tool / Mastra tool）对比 |
| **范围蔓延**：从 L1 个人模板一直做到 L4 SaaS 平台 | 🟡 | **明确 MVP 边界**（L2 即可发版），后续版本增量扩展；L4 留作下个 0 步 |
| **估时偏差**：新架构 + 新协议 + 新测试，估时可能偏差 > 50% | 🟡 | 3 步拆分时**强制 ≤ 1h 原子任务**，单 task 估时偏差不会爆 |
| **教育成本**：MCP / Skill 概念对用户新 | 🟢 | 1 步 product-doc 写清楚用户价值；6 步 retro 沉淀到 CLAUDE.md |
| **本地优先 vs 云端**：L3 平台化需要后端，**单人项目**难维护 | 🟢 | **强烈推荐 L1-L2 收手**，L3 留待团队化 |

---

## 5. 输出建议（必填）

### 5.1 推荐路径

```
0 调研（本步完成 → 等用户确认）
→ 1 规格（product-doc.md + design-spec.md + spec.md · 三脑交汇）
→ 2 计划（plan.md + api-spec.md + component-spec.md · ≥ 2 方案）
→ 3 拆分（tasks.md · ≤ 1h 原子任务）
→ 4 实现（TDD 循环 + test-cases.md 整合）
→ 5 验证（verify.md · L3 整合 + L5 staging）
→ 6 复盘（retro.md · 更新 CLAUDE.md / DOD.md）
```

**路径模式**：`full-6`（跨 ≥ 3 文件，新功能标准流程）

**总时间预算**：30-60 min 调研 + 完整 6 步 ≈ **3-4 周**（L1-L2 = 1 周 / L3 = 2-3 周）

### 5.2 关键决策点（必填 ≥ 1）

| 决策 | 选项 | 推荐 | 理由 |
|---|---|---|---|
| **决策 1：协议层选型** | A. 纯 MCP · B. 纯 Claude Code Skill · C. **MCP + Skill 双层** · D. 自定义协议 | **C** | MCP 通用（Claude/Codex/Cursor）/ Skill 深度集成 Claude Code / Hooks 守护违规；C 兼容性最好 |
| **决策 2：工作流引擎** | A. **复用 LangGraph 0.3.18** · B. 自研状态机 · C. 包装 LangChain AgentExecutor | **A** | 已装好、有图可视化、能解决 Issue A；同时验证 Issue A 的"假 LangGraph"是否可激活 |
| **决策 3：组件协议** | A. Pydantic BaseModel · B. JSON Schema 字符串 · C. 两者结合 | **A** | 已装 pydantic 2.10.4，类型安全 + 自动校验 + OpenAPI 文档 |
| **决策 4：状态持久化** | A. SQLite · B. JSON 文件 · C. Redis | **A** | 轻量、单文件、易调试、事务支持；与现有 interview_settlement 一致 |
| **决策 5：MVP 边界** | A. L1-L2（个人+CLI）· B. L1-L3（加动态组件）· C. L1-L4（含生态）| **B** | 1 人项目 L4 太重；L3 动态组件是核心价值 |
| **决策 6：是否同时解决 Issue A/E/F** | A. 一并解决 · B. 只做新功能 | **A** | 一次调研解决 3 个沉积议題，效率最高 |
| **决策 7：发布形式** | A. PyPI 包（`pip install intervue-workflow`）· B. Git 模板仓库 · C. 内置到 Intervue 仓库 | **C** | 单人项目，包发布成本高；内置到 Intervue 做子模块最实际 |

### 5.3 元信息

- **是否需要外部评审**：否（单人项目，用户主导）
- **是否涉及 schema 变更**：是（新增 `backend/workflow/` 目录 + 新增 SQLite 表存工作流状态 + `.claude/skills/ai-workflow/SKILL.md`）
- **是否需要 AB 测试**：否
- **是否同步解决议題 A/E/F**：是

---

## 6. POC 验证清单（建议在 1 步规格前做）

> ⚠️ **强烈建议**：不要直接进 1 步规格，先做 30 分钟 POC 验证可行性。

- [ ] **POC-1**：写一个最小 MCP server（10 行代码），调通 Claude Code 端的 `tool_use`
- [ ] **POC-2**：把 `interview_graph.py` 的 StateGraph 真跑通一次（不绕过 service）
- [ ] **POC-3**：写一个示例组件（Pydantic schema + execute 方法），验证动态注册可行
- [ ] **POC-4**：实测 6 步流程在 Claude Code + MCP 下能否跑通最小 demo

**POC 通过标准**：
- Claude Code 能成功调用 MCP 工具
- LangGraph StateGraph 真用上
- 组件动态注册 demo 跑通
- 总耗时 ≤ 1h

**POC 失败** → 回到 0 步重做，不进 1 步。

---

## 7. 防御清单（自检）

- [x] 任务理解段已写且**待用户复述确认**
- [x] 现状扫描覆盖 ≥ 3 个相关文件（实际 12 个）
- [x] 依赖发现列出 ≥ 3 个影响点（实际 8 个）
- [x] 风险评估 ≥ 3 条带等级（实际 9 条，🔴 2 / 🟡 5 / 🟢 2）
- [x] 输出建议给完整 6 步路径
- [x] 关键决策点 ≥ 1（实际 7 个）
- [x] 已读 `docs/issues.md`
- [x] 已跑 `git log -10` + `git status`

---

## 📌 下一步

**等用户确认**：
- [ ] 复述对吗？
- [ ] POC 清单可接受吗？
- [ ] 关键决策点（特别是 决策 1/2/5/7）有异议吗？
- [ ] 确认后是否进 **1 步规格**（写 product-doc.md + design-spec.md + spec.md）？

---

**相关文档**：
- [[全局流程]]（6 步工作流 v2 定义）— `~/Obsidian/coding/AI代码工具使用心得/7步工作流最终版/全局流程.md`
- `docs/issues.md` — Issue A / E / F
- `.claude/skills/intervue-dev/SKILL.md` — 现有项目 Skill
- `docs/CODE-MOCK.md` — 项目架构
