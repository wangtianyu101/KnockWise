---
title: Spec · AI 协作工作流引擎
date: 2026-07-06
updated: 2026-07-09
status: draft-v1 (待人确认)
author: Claude（AI 主导）
type: spec
related:
  - [research.md](research.md) — 上游：调研
  - [product-doc.md](product-doc.md) — 上游：产品脑
  - [design-spec.md](design-spec.md) — 上游：设计脑
---

# Spec · AI 协作工作流引擎（技术脑）

> **作者分工**：本文件 AI 主导填写（spec.md 是机器可读契约，AI 最擅长结构化）。
>
> **上游**：research.md + product-doc.md + design-spec.md
>
> **下游**：2 步 plan.md / api-spec.md / component-spec.md + 4 步 test-cases.md

---

## 0. 上游引用（必填）

- **调研报告**：[research.md](research.md) v1
- **产品文档**：[product-doc.md](product-doc.md) v1（待人拍板 4 个 TODO）
- **设计文档**：[design-spec.md](design-spec.md) v1（待人拍板 3 个 TODO）
- **POC 报告**：[poc/POC-REPORT.md](poc/POC-REPORT.md) — 4 项 POC 全过

### 关键决策（从 product-doc §4 抄）
- **MVP 范围**：6 步状态机 + 组件协议 + MCP server + Claude Skill + 1 个真实组件 + 可观测性 + 80% 覆盖率
- **不包含**：PyPI 发布 / 可视化 UI / 插件市场 / 远程 MCP / 多租户

### 关键风险（从 research §4 抄，标 🔴）
- 🔴 **重复造轮**：已有 LangGraph 1.2.4 + 现有 `interview_graph.py` 可能冲突 → POC-2 已验证可复用
- 🔴 **V2 未稳定**：git status 有 4 个未提交改动 → 新功能独立分支 `feat/ai-workflow-engine`
- 🟡 **议題 A/E/F 沉积**：3 个议題一并解决

### 关键技术发现（从 POC）
- langgraph **实际版本 1.2.4**（requirements.txt 写的 0.3.18 已升级）
- `build_interview_graph()` 1.x 直接返回 `CompiledStateGraph`，无需 `.compile()`
- mcp **1.28.1** 已装，30 行能跑通 stdio server
- Pydantic **2.13.4** 用 ConfigDict 替代 class Config

---

## 1. 用户故事（产品意图 · 必填 · ≤ 3 条）

### US-1：作为独立开发者，我想要把 6 步工作流封装成 CLI 命令
**以便** 我每次新功能 / 修 bug / 重构时，一行命令启动，不用每次重新 prompt AI。

### US-2：作为 Claude Code / Codex 用户，我想要通过 MCP 协议让 AI 自动按 6 步推进
**以便** AI 不需要我每步手动指挥，能自己识别"现在该走哪一步"，我只需在关键决策点批准。

### US-3：作为想扩展能力的开发者，我想要写一个 Python 类就能注册成新能力（动态组件）
**以便** 加新功能（如 PDF 简历解析）不用改主程序、不用重启服务，**热插拔**。

---

## 2. 验收标准 / Requirement + Scenario（机器可验证 · 必填 · ≥ 3 条）

> 升级说明（2026-07-17）：从纯 GWT 升级为 Requirement (SHALL) + Scenario (GWT) 双层结构。

### Requirement: AI Workflow Engine
The system SHALL provide a CLI-driven, resumable, 6-step workflow engine for AI-assisted development with state persistence and MCP server support.

#### Scenario: Happy Path — CLI start
- **Given** 用户在 Intervue 项目根目录
- **When** 运行 `intervue workflow start "V3 实时评分"`
- **Then** CLI 输出 `✅ Started run: <uuid8>` 并在 `~/.intervue/state.db` 创建一条新 run 记录

#### Scenario: Happy Path — workflow research step
- **Given** 已有 run a1b2c3d4 在 step 0_research
- **When** 运行 `intervue workflow research a1b2c3d4 --topic "..."`
- **Then** 生成 `docs/tasks/<date>-<topic>/research.md` 且 run 状态变为 step 1_spec

#### Scenario: Edge — missing handler field
- **Given** 用户配置的 workflow.yaml 缺 `handler` 字段
- **When** 启动 CLI
- **Then** **fail-fast** 报错 `ConfigError: workflow.steps[3] missing required field 'handler'`，exit code 1

#### Scenario: Edge — invalid Component manifest
- **Given** 用户注册的 Component manifest.id 不符合正则 `^[a-z][a-z0-9_]*$`
- **When** 注册
- **Then** 报错 `ValidationError` 不入库

#### Scenario: Failure — corrupted SQLite
- **Given** SQLite 文件被外部损坏
- **When** 运行 `intervue workflow status`
- **Then** 报错 `DatabaseError: ... Try 'intervue workflow repair'` 且 exit code 1

#### Scenario: Failure — MCP port conflict
- **Given** MCP server 启动时端口冲突
- **When** 启动
- **Then** **优雅退出** + 报错含修复建议（`port 8000 in use, try --port 8001`）

#### Scenario: Failure — resume after kill
- **Given** 工作流跑到 step 4 突然中断（kill -9）
- **When** 重启后运行 `intervue workflow resume <run_id>`
- **Then** **从 step 4 继续**，不重跑已完成的 step 0-3

---

## 3. 边界条件（防御性 · 必填）

### 3.1 空值 / 异常 / 并发
- **空值**：
  - `topic` 为空字符串 → 启动失败，提示"topic 不能为空"
  - `run_id` 不存在 → 报错"Run <id> not found"
  - workflow.yaml 为空 → 报错"配置文件为空"
- **异常**：
  - SQLite 锁等待 > 5s → 重试 3 次后失败
  - Component 执行抛异常 → 标记 step failed，**不污染** 其他 step 的状态
  - MCP stdio 通信断开 → 优雅退出 + 清理资源
- **并发**：
  - 同一 run 同时被两个 CLI 命令 advance → **SQLite 事务 + 行锁** 串行化
  - 多 CLI 进程同时启动 → 不冲突（SQLite WAL 模式）

### 3.2 时序（顺序依赖）
- 启动 → 必须先校验配置 → 再启动 MCP server
- advance → 必须先 load run state → 再执行 handler → 再 update state
- retro → 必须先完成 verify → 才能执行 retro

### 3.3 安全 / 权限
- **权限校验**：
  - CLI 启动时不要求权限（本地工具）
  - MCP server 仅暴露给本地（stdio）
  - **v2 远程场景**才需要 token 鉴权
- **注入防护**：
  - workflow.yaml 用 Pydantic 强类型校验（防 YAML 注入）
  - Component.execute() 的 input 必须先过 manifest.input_schema 校验
  - 所有 SQL 用 SQLAlchemy ORM（防 SQL 注入）
- **路径遍历防护**：
  - run topic 不能含 `..` 或 `/`（防路径遍历）
  - 文档路径用 Pydantic Literal 限定

### 3.4 性能 / QPS
- **响应时间**：
  - `intervue workflow status` P95 < 50ms（纯 SQLite 查询）
  - `intervue workflow start` P95 < 200ms
  - Component execute P95 < 30s（含 LLM 调用，**不卡 UI**）
- **QPS 上限**：
  - SQLite 写并发 ≤ 100 QPS（够本地用）
  - LLM 调用限流：**复用 V2 已加的 slowapi limiter**

### 3.5 兼容性 / 版本
- **向后兼容**：
  - workflow.yaml schema_version 字段必填
  - 旧版本 workflow.yaml 启动时 warn 但不 fail
- **前向兼容**：
  - 组件 manifest 缺字段时 warn 但不 fail（除非 required）
- **依赖版本**：
  - langgraph 锁定到 1.2.x（避免大版本 breaking）
  - mcp 锁定到 1.28.x

### 3.6 国际化
- **时区**：所有 timestamp 用 UTC 存储，**显示时**转用户时区
- **多语言**：MVP **不做** i18n（v2 再考虑）
- **日期格式**：ISO 8601（`2026-07-09T14:32:15Z`）

---

## 4. 数据契约（接口定义 · 必填）

### 4.1 Component Manifest（Pydantic）

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class ComponentManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")  # 业务：组件唯一标识
    name: str = Field(..., min_length=1, max_length=50)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")  # 业务：semver
    description: str = Field(..., min_length=1, max_length=500)
    author: str = Field(default="intervue")
    input_schema: dict  # 业务：JSON Schema，约束 input
    output_schema: dict  # 业务：JSON Schema，约束 output
    permissions: list[Literal["read_files", "write_files", "network", "git", "llm"]] = []
    dependencies: list[str] = []  # 业务：依赖的其他组件 id
```

### 4.2 Component Interface（Protocol）

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Component(Protocol):
    manifest: ComponentManifest

    def execute(self, input: dict) -> dict:
        """同步执行；异步组件请用 AsyncComponent"""
        ...

    async def aexecute(self, input: dict) -> dict:
        """异步执行（可选；不实现则同步执行）"""
        ...
```

### 4.3 Workflow Step Config（Pydantic）

```python
class WorkflowStepConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^[0-6]_[a-z_]+$")  # 业务：0_research / 1_spec / ...
    handler: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")  # 业务：组件 id
    requires_approval: bool = True  # 业务：是否需要人批准才能推进
    timeout: int = Field(default=1800, ge=10, le=7200)  # 业务：超时秒数
```

### 4.4 Workflow Config（Pydantic）

```python
class WorkflowConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    project_name: str = Field(..., min_length=1)
    steps: list[WorkflowStepConfig] = Field(..., min_length=1, max_length=20)
    components_dir: str = "./components"
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
```

### 4.5 Run State（SQLite Schema）

```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,                    -- 8 字符 uuid
    topic TEXT NOT NULL,
    current_step TEXT,                       -- 0_research / 1_spec / ... / NULL（完成）
    state TEXT NOT NULL,                     -- pending / running / approved / failed / completed
    context TEXT NOT NULL DEFAULT '{}',     -- JSON：步间传递的上下文
    history TEXT NOT NULL DEFAULT '[]',     -- JSON：所有步的执行历史
    config_snapshot TEXT NOT NULL,          -- JSON：启动时的配置快照
    created_at TEXT NOT NULL,               -- ISO 8601
    updated_at TEXT NOT NULL                -- ISO 8601
);

CREATE INDEX idx_runs_state ON runs(state);
CREATE INDEX idx_runs_updated ON runs(updated_at);

CREATE TABLE components (
    id TEXT NOT NULL,                        -- 组件 id
    version TEXT NOT NULL,                   -- 组件版本
    loaded_at TEXT NOT NULL,                 -- ISO 8601
    PRIMARY KEY (id, version)
);
```

### 4.6 MCP Tool Schemas（暴露给 agent）

```python
# start_research
{
    "name": "start_research",
    "description": "0 步调研：根据任务类型生成 research.md 模板",
    "inputSchema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "minLength": 1, "maxLength": 200},
            "task_type": {"enum": ["new-feature", "bug", "refactor", "p0"]}
        },
        "required": ["topic", "task_type"]
    }
}

# submit_spec
{
    "name": "submit_spec",
    "description": "1 步规格：保存三脑交汇产物",
    "inputSchema": {
        "type": "object",
        "properties": {
            "run_id": {"type": "string", "pattern": "^[a-z0-9]{8}$"},
            "product_doc": {"type": "string"},
            "design_spec": {"type": "string"},
            "spec": {"type": "string"}
        },
        "required": ["run_id", "spec"]
    }
}

# advance_workflow
{
    "name": "advance_workflow",
    "description": "推进工作流到下一步（每步完成后调用）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "approved": {"type": "boolean", "default": true}
        },
        "required": ["run_id"]
    }
}

# get_workflow_status
{
    "name": "get_workflow_status",
    "description": "查询 run 状态",
    "inputSchema": {
        "type": "object",
        "properties": {"run_id": {"type": "string"}},
        "required": ["run_id"]
    }
}

# list_components
{
    "name": "list_components",
    "description": "列出所有已注册组件",
    "inputSchema": {"type": "object", "properties": {}}
}

# list_runs
{
    "name": "list_runs",
    "description": "列出所有 run（最近 50 条）",
    "inputSchema": {
        "type": "object",
        "properties": {
            "state": {"enum": ["pending", "running", "approved", "failed", "completed"]}
        }
    }
}

# retro_workflow
{
    "name": "retro_workflow",
    "description": "6 步复盘：沉淀经验到 CLAUDE.md / DOD.md",
    "inputSchema": {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "lessons_learned": {"type": "string"}
        },
        "required": ["run_id", "lessons_learned"]
    }
}
```

### 4.7 副作用（Side Effects）

| 操作 | 副作用 |
|---|---|
| `start` | DB: `INSERT INTO runs`  ·  FS: 无  ·  Event: `WorkflowStarted` |
| `advance` | DB: `UPDATE runs SET current_step, state, history, updated_at`  ·  FS: 产物落盘到 `docs/tasks/<date>-<topic>/`  ·  Event: `StepCompleted` |
| `retro` | DB: `UPDATE runs SET state='completed'`  ·  FS: 追加到 `CLAUDE.md` / `DOD.md`  ·  Event: `WorkflowCompleted` |
| `register_component` | DB: `INSERT INTO components`  ·  FS: 无  ·  Event: `ComponentRegistered` |

---

## 5. 测试场景（验收测试 · 必填 · ≥ 3 条）

| TC | 对应 GWT | 描述 | 类型 |
|---|---|---|---|
| **TC-1** | GWT-H1 | `start` 命令生成 uuid8 + 创建 run 记录 | happy |
| **TC-2** | GWT-H2 | `research` 命令生成 research.md + 推进到 step 1 | happy |
| **TC-3** | GWT-H1 + H2 | 端到端：start → research → spec → plan → tasks → implement → verify → retro 全跑通 | happy |
| **TC-4** | GWT-E1 | workflow.yaml 缺 `handler` 字段 → fail-fast | edge |
| **TC-5** | GWT-E2 | Component id 不符合正则 → ValidationError | edge |
| **TC-6** | GWT-F1 | SQLite 损坏 → DatabaseError + 提示 repair | failure |
| **TC-7** | GWT-F3 | kill -9 中断后 resume → 从断点继续，不重跑 | failure |
| **TC-8** | GWT-H2 | 并发：2 个 CLI 同时 advance 同一 run → 串行化（不丢步） | edge |
| **TC-9** | GWT-H1 | 空 topic → 启动失败 | edge |
| **TC-10** | GWT-H1 | topic 含 `..` → 拒绝（防路径遍历） | failure |

**覆盖率目标**：
- `engine.py` ≥ 90%
- `registry.py` ≥ 85%
- `cli.py` ≥ 75%（CLI 难测，覆盖率放宽）
- 至少 1 个真实 Component（如 `obsidian_research`）≥ 70%

---

## 5.5 跨文档引用（指向 2 步技术详细化）

- ✅ 涉及 schema 变更？→ 2 步产出 **db-design.md**（§4.5 runs/components 表已草拟）
- ✅ 涉及新/改 API？→ 2 步产出 **api-spec.md**（§4.6 MCP tool schemas 已列）
- ✅ 涉及新组件？→ 2 步产出 **component-spec.md**（§4.1-4.2 manifest + protocol 已草拟）
- 都不涉及？→ ❌（本 feature 涉及 3 个全产出）

---

## 🤖 AI vs 人分工（1 步本步内）

| 段 | AI 已填 | 人需拍板 |
|---|---|---|
| §0 上游引用 | ✅ | — |
| §1 用户故事 | ✅ | 验收 US 措辞是否准确 |
| §2 GWT | ✅ 7 条 | 验收 GWT 是否覆盖关键路径 |
| §3 边界 | ✅ 6 类 | 验收是否有遗漏 |
| §4 数据契约 | ✅ 7 块 schema | 验收 schema 字段是否符合业务 |
| §5 测试场景 | ✅ 10 条 | 验收是否覆盖核心场景 |
| §5.5 跨文档引用 | ✅ | — |

---

## 🎯 DOD 自检清单

- [x] 5 段齐全（用户故事 / GWT / 边界 / 数据契约 / 测试场景）
- [x] GWT ≥ 3 条（实际 7 条：H×2 / E×2 / F×3）
- [x] 数据契约 ≥ 1 schema（实际 7 块）
- [x] 测试场景 ≥ 3 条（实际 10 条：happy×3 / edge×4 / failure×3）
- [x] §0 上游引用齐全（research + product-doc + design-spec + POC）
- [ ] 用户故事已验收（**待人签字**）

---

## ⚠️ 待用户拍板的 3 个关键点

1. **§1 用户故事 3 条**：覆盖核心场景吗？要不要加（如"团队 lead 协作"）或减？
2. **§2 GWT 7 条**：H/E/F 比例合理吗？failure case 够不够？
3. **§4.5 SQLite Schema**：`runs` / `components` 两张表够不够？要不要加 `approvals`（人批准记录）表？

---

## 📚 下游（2 步会展开）

- → [plan.md](plan.md)（2 步）— ≥ 2 方案对比 + 推荐 + 技术选型
- → [db-design.md](db-design.md)（2 步）— §4.5 schema 详细化（字段类型 + 索引 + 迁移）
- → [api-spec.md](api-spec.md)（2 步）— §4.6 MCP tool 详细化（Request/Response 样例 + 错误码）
- → [component-spec.md](component-spec.md)（2 步）— §4.1-4.2 详细化（如何开发 + 调试 + 测试组件）