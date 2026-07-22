@AGENTS.md

# Claude Code 工具适配

> 公共项目规则的唯一主账是 `AGENTS.md`。本文件只补充 Claude Code 的具体工具映射。

- § 6.7 的独立 verifier 使用 Claude Code 当前环境实际提供的 `Agent` tool，并创建全新 prompt；不得复用 writer 上下文。
- 只有当前环境明确暴露下述 Workflow 能力时，才应用本节；未暴露时遵循 `AGENTS.md` § 6.7.1 的通用路径。

### 6.7.1 进阶路径：Workflow tool（≥ 3 verify cycle 或 ≥ 5 phase 时升级 · 2026-07-17 整合）

Claude Code 已实现 **`Workflow` tool**（确定性 orchestration）。与 § 6.7 默认 `Agent` tool 对比：

| 维度 | `Agent` tool（默认） | `Workflow` tool（进阶） |
|---|---|---|
| 控制方 | Claude 每轮决策 | **脚本决定**（确定性）|
| 中间状态 | context window（50 轮后 100K+ tokens）| **脚本变量**（不污染 context）|
| 可重复 | 弱（重启 turn 即丢）| **强**（`resumeFromRunId` 同会话恢复）|
| 规模 | 数个 / turn | **数十到数百 agents** |
| 适用 | 单 commit verify · 偶发 fix | **≥ 3 cycle** · ≥ 5 phase · 对抗式 verify |

**升级阈值**（推荐）：

| 场景 | 工具 |
|---|---|
| 1-2 verify cycle · 单 phase | 保持 `Agent` tool（§ 6.7 默认）|
| **≥ 3 verify cycle** 或 ≥ 5 phase 任务 | 升级 **`Workflow`** |
| 关键 commit / 涉及安全 / 性能 | **直接 `Workflow` + 对抗式 verify** |

**完整脚本骨架**（含 workflow 主循环 + 对抗式 verify 变体 · 复制改名即可用）：

→ **[`.claude/workflows/verify-loop-example.js`](.claude/workflows/verify-loop-example.js)**

文件含：`meta` 声明 · `WRITER_RESULT_SCHEMA` / `VERIFIER_SCHEMA` · 主循环（writer → verifier → fix）· **对抗式 verify 注释块**（`parallel()` 屏障 + 2/3 共识）

**关键工具速查**：

- `Agent` tool:
  - `subagent_type: "general-purpose"` — 默认
  - `subagent_type: "Plan"` — verifier 用于"对照 architecture"
  - `subagent_type: "Explore"` — verifier 用于"查 reference / 文件搜索"
  - `isolation: "worktree"` — writer + fixer 同时改文件时避免冲突（贵 ~300ms · 仅高冲突场景）
  - `run_in_background: true` — verifier 跑时 writer 可继续（仅 verifier 只读不写时用）
- `Workflow` tool:
  - `pipeline(items, stage1, stage2, ...)` — 默认 stage 串行无屏障
  - `parallel(thunks)` — 屏障（等所有完成）· **对抗式 verify 用这个**
  - `phase(title)` — 进度分组
  - `agent(prompt, {schema})` — `schema` 强制结构化输出，避免自由格式 FAIL 清单模糊
  - `resumeFromRunId` — 中断后同会话恢复
- `ScheduleWakeup` tool — verifier 等外部状态（CI / deploy 完成）时用，**cache-aware 60-3600s**
- `SendMessage` tool — 队友 agent 间发消息（verifier 给 writer 反馈）· 替代"反复开新 Agent"

**资源**：[Dynamic Workflows 深度解析](https://www.cnblogs.com/ai-old-six/p/20245238) · [Workflow 功能实战教程](https://blog.csdn.net/2601_96073073/article/details/161488327) · [Subagent vs Workflow 对比](https://www.cnblogs.com/softlin/p/20231222)
