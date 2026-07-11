---
title: Design Spec · AI 协作工作流引擎（CLI 体验设计）
date: 2026-07-06
status: draft-v1 (待人确认)
author: Claude（AI 起草）+ 用户（拍板）
type: design-spec
related:
  - [product-doc.md](product-doc.md) — 上游：产品脑
  - [spec.md](spec.md) — 下游：技术脑
---

# Design Spec · AI 协作工作流引擎（CLI 体验设计）

> **本文件定位**：本 feature 是 **CLI 工具 + 协议层**，**无 GUI 改动**。所以"设计脑"翻译成 **CLI 体验设计**：命令结构、输出格式、交互流、错误提示、配置文件格式。
>
> **作者分工**：AI 起草骨架，关键 UX 决策标 `<!-- TODO: 人填 -->`，需用户拍板。

---

## 1. 用户旅程（CLI 版本）

### 完整流程（从用户视角）

#### 场景 A：本地起新功能

```
1. 用户在终端: cd /path/to/Intervue
2. 用户: $ intervue workflow start "V3 实时面试评分"
3. CLI 输出:
   ✅ Started run: a1b2c3d4
   📋 Step 0/6: 调研 (research)
   💡 提示: 在 Claude Code 里继续，或运行 `intervue workflow status a1b2c3d4`
4. 用户: $ intervue workflow research a1b2c3d4 --topic "V3 实时面试评分" --type new-feature
5. CLI 输出: 生成 docs/tasks/2026-07-06-new-feature-v3-realtime-score/research.md
   → 等待人审核 → 用户输入 y 批准
6. CLI: 📋 Step 1/6: 规格 (spec)
   → 用户调 MCP 工具 submit_spec / 或在 Claude Code 里继续
7. ... 重复 6 步 ...
8. CLI: ✅ 6 步完成，retro 沉淀到 CLAUDE.md
```

#### 场景 B：在 Claude Code 里走流程

```
1. 用户: 我要做个新功能，V3 实时面试评分
2. Claude Code (识别 Skill 触发): 我先调 start_research 走 0 步调研
   → 调用 MCP 工具
   → 生成 research.md
3. Claude Code: 调研完成，调用 submit_spec 走 1 步规格
4. ... Claude Code 按 6 步推进，每步调对应 MCP 工具 ...
5. Claude Code: 6 步完成，retro 沉淀
```

#### 场景 C：工作流中断恢复

```
1. 某次跑 4 步实现时电脑死机
2. 重启: $ intervue workflow list
3. CLI 输出:
   - a1b2c3d4 (V3 实时面试评分) — Step 4/6: 实现 — ⏸️ 暂停（2026-07-06 14:32）
4. 用户: $ intervue workflow resume a1b2c3d4
5. CLI: ✅ 从 Step 4 继续
```

### 关键决策点

- **决策点 1**：用户在哪一步可以"批准 / 驳回"？→ **每步完成后**（核心 6 步都需人批准）
- **决策点 2**：AI 怎么知道"现在该走哪一步"？→ **状态机**（context 里有 current_step）
- **决策点 3**：工作流跑挂怎么办？→ **自动回滚到上一个 approved 状态 + 提示**

### 异常路径

| 异常 | 用户应对 |
|---|---|
| 网络断开（调 LLM 失败） | CLI 显示"重试 (y/n)?"，用户可输入 n 暂停 |
| Component 不存在 | CLI 提示 "Component 'xxx' not registered. 检查 components/ 目录" |
| 配置文件错误 | CLI fail-fast：启动时校验，报具体哪个字段错 |
| SQLite 损坏 | CLI 提示"DB 损坏，请运行 `intervue workflow repair`" |

---

## 2. 命令地图（CLI Surface）

```bash
intervue
├── workflow
│   ├── start <topic>           # 启动新工作流
│   ├── research <run_id>       # 0 步：调研（生成 research.md）
│   ├── spec <run_id>           # 1 步：规格
│   ├── plan <run_id>           # 2 步：计划
│   ├── tasks <run_id>          # 3 步：拆分
│   ├── implement <run_id>      # 4 步：实现
│   ├── verify <run_id>         # 5 步：验证
│   ├── retro <run_id>          # 6 步：复盘
│   ├── status <run_id>         # 查看状态
│   ├── list                    # 列出所有 run
│   ├── resume <run_id>         # 恢复中断的 run
│   └── repair                  # 修复 DB
├── component
│   ├── list                    # 列出已注册组件
│   ├── info <component_id>     # 查组件详情
│   └── validate <path>         # 验证组件 manifest
├── mcp
│   └── serve                   # 启动 MCP server（stdio 模式）
└── config
    ├── show                    # 查当前配置
    └── validate                # 校验配置
```

### 命令设计原则

| 原则 | 说明 |
|---|---|
| **动词优先** | `start` / `resume` / `repair` 都是动词，一眼懂 |
| **run_id 显式传** | 不用全局状态，避免多 session 冲突 |
| **短选项 + 长选项** | `-t` / `--topic`，遵循 GNU 风格 |
| **错误信息含修复建议** | 不只说"错"，还说"怎么修" |

---

## 3. CLI 输出规范

### 3.1 状态输出（status 命令）

```
$ intervue workflow status a1b2c3d4

📋 Run: a1b2c3d4
   Topic: V3 实时面试评分
   Created: 2026-07-06 14:32:15
   Updated: 2026-07-06 15:10:22

📊 Progress: ████████░░ 4/6 (66%)

✅ 0_research       completed  (14:32 → 14:45, 13min)
✅ 1_spec           completed  (14:45 → 15:02, 17min)
✅ 2_plan           completed  (15:02 → 15:08, 6min)
🔄 3_tasks          running    (15:08 → ...)
⏸️  4_implement      pending
⏸️  5_verify         pending
⏸️  6_retro          pending

💡 Next: `intervue workflow tasks a1b2c3d4` to continue
```

### 3.2 进度输出（推进时）

```
$ intervue workflow implement a1b2c3d4

🚀 Starting 4_implement...
   [1/3] Running test_research_component.py...     ✅ pass (1.2s)
   [2/3] Running test_workflow_engine.py...         ✅ pass (3.4s)
   [3/3] Running test_e2e_workflow.py...            ❌ FAIL (line 42)

💥 Test failed. Run details:
   /path/to/test_e2e_workflow.py:42: AssertionError
   expected: 'completed'
   actual:   'failed'

🔧 Options:
   y  - retry
   n  - pause (save state, can resume later)
   d  - debug (show full traceback)
```

### 3.3 错误输出规范

| 错误类型 | 输出格式 | 示例 |
|---|---|---|
| **配置错误** | `❌ ConfigError: <字段> <错在哪>` | `❌ ConfigError: workflow.steps[3] missing required field 'handler'` |
| **组件未注册** | `❌ ComponentNotFound: <id>. Run 'intervue component list' to see available.` | — |
| **状态机错误** | `❌ InvalidState: cannot advance from <from> to <to>` | — |
| **DB 错误** | `❌ DatabaseError: <msg>. Try 'intervue workflow repair'` | — |
| **MCP 错误** | `❌ MCPError: <tool> failed: <reason>` | — |

### 3.4 颜色与符号规范

| 元素 | 颜色 | 符号 |
|---|---|---|
| 成功 | 🟢 green | ✅ |
| 失败 | 🔴 red | ❌ |
| 警告 | 🟡 yellow | ⚠️ |
| 进行中 | 🔵 blue | 🔄 |
| 暂停 | ⚪ gray | ⏸️ |
| 提示 | 🟣 purple | 💡 |

---

## 4. 配置文件格式（workflow.yaml）

```yaml
# ~/.intervue/workflow.yaml
project:
  name: intervue
  version: 1.0.0

workflow:
  steps:
    - id: research
      handler: obsidian_research
      requires_approval: true
      timeout: 1800
    - id: spec
      handler: spec_writer
      requires_approval: true
      timeout: 1800
    # ... 其他 5 步

components:
  registry_path: ./components
  auto_discover: true
  sandbox: subprocess

logging:
  level: INFO
  format: json
  output: ~/.intervue/logs/{date}.log

mcp:
  transport: stdio  # 未来支持 sse / http
```

**校验规则**（启动时 fail-fast）：
- YAML 语法
- Pydantic schema 严格匹配（`extra: forbid`）
- 必填字段齐全
- handler 引用的 component 已注册

---

## 5. 视觉规范（CLI 特有）

### 5.1 终端颜色
- **库**：[rich](https://rich.readthedocs.io/)（Python 生态最成熟的终端美化库）
- **主色**：cyan（信息）/ green（成功）/ red（失败）/ yellow（警告）
- **不依赖颜色**：所有状态用 emoji + 文字双标识（色盲友好）

### 5.2 进度展示
- **进度条**：[tqdm](https://tqdm.github.io/) 风格
- **实时刷新**：用 `rich.live`
- **可中断**：`Ctrl+C` 优雅暂停（保存状态）

### 5.3 表格输出
- **库**：rich.table
- **对齐**：左对齐（中文）+ 右对齐（数字）
- **边框**：`box.ROUNDED`

### 5.4 字体与编码
- **等宽字体**（用户终端决定）
- **UTF-8** 全支持（emoji / 中文）
- **跨平台**：macOS / Linux / Windows Terminal

---

## 6. 错误信息规范（重点）

### 6.1 三段式错误信息

```
❌ <错误类型>: <一句话说明>
   Cause: <为什么发生>
   Fix:   <怎么修>
```

**示例**：

```
❌ ComponentNotFound: obsidian_research not registered.
   Cause: components/obsidian_research/ 目录不存在或 __init__.py 缺失
   Fix:   1. 创建 components/obsidian_research/__init__.py
          2. 实现 ObsidianResearchComponent 类（含 manifest）
          3. 重启 MCP server
```

### 6.2 错误等级

| 等级 | 处理 | 示例 |
|---|---|---|
| **FATAL** | 立即退出，exit code 1 | 配置错误 / DB 损坏 |
| **ERROR** | 提示用户决定（重试 / 跳过 / 暂停）| 组件执行失败 |
| **WARN** | 继续运行 + log warn | 重试成功 / 性能降级 |
| **INFO** | 正常输出 | 步骤完成 |

---

## 🎯 DOD 自检清单（人审核时必过）

- [x] 5 段齐全（用户旅程 / 命令地图 / 输出规范 / 配置格式 / 视觉规范）
- [x] ≥ 1 个完整用户旅程（场景 A/B/C）
- [x] ≥ 1 个页面（命令）线框图（`status` 输出示例）
- [x] 交互细节 ≥ 5 种状态（默认 / 成功 / 失败 / 暂停 / 进行中）
- [x] 视觉规范 5 方面齐全（颜色 / 进度 / 表格 / 字体 / 错误）

---

## ⚠️ 待用户拍板的 3 个关键问题

1. **CLI 库选型**（§3.1 / §5）— 用 [rich](https://github.com/Textualize/rich) 还是 [click + colorama]？
   - 推荐 **rich**（生态成熟，progress / table / color 全有）
2. **命令分组**（§2）— `intervue workflow start` vs `intervue start workflow`？前缀 vs 动词在前？
   - 推荐 `intervue workflow start`（group 清晰，子命令统一）
3. **配置文件位置**（§4）— `~/.intervue/workflow.yaml` vs `./workflow.yaml`（项目内）？
   - 推荐 **项目内**（每项目独立配置）+ **全局 fallback**（`~/.intervue/`）

---

## 📚 下游

- → [spec.md](spec.md) — 技术契约（CLI 命令签名 + MCP tool schema）
- → [api-spec.md](api-spec.md)（2 步）— MCP tool 详细定义
- → [component-spec.md](component-spec.md)（2 步）— 组件 manifest 详细定义
