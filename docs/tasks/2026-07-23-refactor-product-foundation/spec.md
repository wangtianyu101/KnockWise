---
title: Spec · 产品基础分层 L0-L3
date: 2026-07-27
status: v1.2（v1.1 + 4 项调研偏差修正：counter 键 / T4 checker 已存在 / logger 已有 trace_id / pytest 基线）
type: spec
related:
  - [research.md](research.md) — 调研报告（v1）
  - [decisions.md](decisions.md) — 决策 1 主账
  - [docs/issues.md](../../issues.md) — 主账
  - [product-doc-template.md](../../templates/product-doc-template.md) — P1-7 扩展对象
  - [tasks-template.md](../../templates/tasks-template.md) — P1-9 §9 扩展对象
  - [spec-template.md](../../templates/spec-template.md) — 上游模板
---

# Spec · 产品基础分层 L0-L3（重构）

> **范围**：决策 1 自动授权 · 分层 L0-L3 治理 + 模板最小 diff + 埋点按层强制
> **路径模式**：refactor-6（0→1→2→3→4→5→6）· 不写 product-doc（refactor 不写）
> **不实施代码**（spec 阶段止于业务契约）

## 0. 上游引用（必填）

- **调研报告**：[`research.md`](research.md) v1
- **决策主账**：[`decisions.md`](decisions.md) 决策 1
- **产品文档**：N/A（refactor 路径不写 product-doc）
- **关键决策**（从 decisions §1 抄）：分层 L0-L3 治理 + 模板最小 diff + 埋点按层强制 · P1-7/8/9 合并方案
- **关键风险**（🔴 从 research §6 抄）：5 项 AI 推送产品指标（40%/60%/10%/5%/30%）阈值未验证 → 列入 L1 探索性 · 未验证前不固化

---

## 1. 用户故事（产品意图 · ≤ 3 条）

```markdown
作为 KnockWise 维护者，我想要"分层 L0-L3"产品基础治理规则，以便新功能/重构按风险与成熟度匹配测量深度、避免单人项目承担过重的形式主义。

作为 KnockWise 维护者，我想要 product-doc 模板 + tasks 模板 + 2 个 Python checker，以便在 commit 前自动校验 problem_evidence / 指标字典 / 埋点挂载，强制 baseline 与埋点"先存在后实施"。

作为 KnockWise AI 协作者，我想要 trace_id race-free + logger startup + metrics endpoint，以便业务代码可安全地调用 `digest_metrics.inc(name)`，且不与其它请求串 trace。
```

**验收**：3 条故事可独立 commit + 配套单测；与决策 1 落地追踪表 §1 严格对齐。

---

## 2. 验收标准 / Requirement + Scenario（机器可验证）

### 2.1 Requirement（系统承诺 · SHALL）

### Requirement: P1-7 Product Baseline Frontmatter
The system SHALL provide `product_baseline` frontmatter schema for `product-doc.md` and a `scripts/check-product-doc.py` pre-commit checker that fails when baseline 字段缺失或不符.

#### Scenario: 合规 product-doc 通过校验
- **Given** product-doc.md 含 `product_baseline.problem_evidence` (3-5 条) + `target_user` (5 字段) + `kill_criteria` (1-3 条) + `dangerous_assumptions` (≥ 0)
- **When** `python3 scripts/check-product-doc.py <file>` 跑
- **Then** exit code 0
- **And** stdout 仅输出 "OK" 或空

#### Scenario: 缺 problem_evidence 段被拒
- **Given** product-doc.md frontmatter 缺 `product_baseline.problem_evidence` 字段
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 包含 "product_baseline.problem_evidence" + "missing" 关键词

#### Scenario: target_user 缺 device 字段被拒
- **Given** target_user 缺 `device` 字段
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 定位到 "target_user.device"

#### Scenario: frontmatter YAML 解析失败被拒
- **Given** frontmatter 含非法 YAML（缩进错 / Tab 字符）
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 包含 "frontmatter parse error" + 行号

### Requirement: P1-8 指标字典 8 必填 + 4 可选 + L0-L3 分层
The system SHALL provide 8 必填 + 4 可选指标字典 schema with L0-L3 分层校验严格度, and `scripts/check_metric_dict.py` that fails on 必填缺失.

#### Scenario: L2 字典 8 必填齐全通过校验
- **Given** 字典文件声明 `layer: L2` 且 8 必填字段齐全（含 `failure_action` ≥ 1 条 ≥ 30 字符）
- **When** checker 跑
- **Then** exit code 0

#### Scenario: 缺 failure_action 被拒
- **Given** 字典声明 L2 但缺 `failure_action`
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 定位到 "failure_action"

#### Scenario: failure_action 字符数 < 30 被拒
- **Given** failure_action 某条字符串长度 = 25
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 包含 "min_length 30" + 当前字符数

#### Scenario: metric_id 不符合正则被拒
- **Given** `metric_id = "1push_total"` （首字符为数字）或 `"x"` （< 3 字符）
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 包含 regex `^[a-z][a-z0-9_]{2,40}$`

#### Scenario: L1 探索性标记仅校验最小集
- **Given** 字典声明 `layer: L1` 且含 1 句话问题假设 + 1 核心成功信号 + ≤ 3 事件
- **When** checker 跑
- **Then** exit code 0（跳过 8 必填 / 4 可选校验）

#### Scenario: 5 项 AI 推送产品指标未验证被标 L1
- **Given** 5 项产品指标（打开率 40% / 读完率 60% / 收藏率 10% / 屏蔽率 5% / 30 天留存 30%）未做实测
- **When** 在字典中声明为 L2
- **Then** checker 警告 "阈值未验证 · L1 探索性标记"
- **And** exit code 1（阻断 L2 升级）

### Requirement: P1-9 L1 平台层 logger / metrics（v1.1 修正）
The system SHALL provide 2 个 L1 平台层基础组件：logger trace_id 字段注入（`backend/utils/logger.py` 扩展 · 含 `TraceIdFilter` + `trace_id_var` ContextVar）+ `knockwise.*` logger startup 接管 + `GET /api/digest/metrics` endpoint，且各组件有 ≥ 1 单测断言行为正确.

#### Scenario: logger trace_id 字段在并发请求下不串（v1.1 修正）
- **Given** 100 个并发 async 任务，每个设 `trace_id_var.set("req-{i}")`
- **When** 收集所有任务中 `logger.info("ok")` 输出（每条日志含 trace_id 字段）
- **Then** 100 条日志的 trace_id 字段与各任务的 i 一一对应（无串）
- **And** 用 `asyncio.gather` 真跑（不是 mock）

#### Scenario: logger trace_id 字段跨请求不串（v1.1 修正）
- **Given** request A 调 `trace_id_var.set("A")`，request B 异步插入设 "B"
- **When** request A 中途 await 后调 `logger.info("A-step")`
- **Then** 输出日志 trace_id = "A"（不是 B 的值）

#### Scenario: knockwise.* logger 在 startup 接管 stdout
- **Given** FastAPI startup 跑
- **When** 业务代码 `logging.getLogger("knockwise.digest").info("ok")`
- **Then** stdout 出现结构化日志（含 timestamp / level / logger / trace_id）
- **And** 不出现未接管前的 bare print 格式

#### Scenario: GET /api/digest/metrics 返回 4 counter 当前值
- **Given** 服务在 127.0.0.1 + 业务代码曾 `digest_metrics.inc("push_total", 1)` + `digest_metrics.inc("push_failed", 1)`
- **When** `curl http://127.0.0.1:PORT/api/digest/metrics`
- **Then** HTTP 200 + JSON `{"counters": {"push_total": 1, "push_failed": 1, ...}}`
- **And** 4 counter 键（**v1.2 修正**：push_total / push_failed / fetch_failures / rsshub_routes_broken — 与 `backend/utils/metrics.py:32-37` 一致）齐全

#### Scenario: counter 真增断言（不是"方法存在"）
- **Given** `digest_metrics` 初始值 `inc("push_total") == 0`
- **When** 业务代码调 `digest_metrics.inc("push_total")`
- **Then** `digest_metrics.inc("push_total") == 1`（真增断言 · 不只 mock `hasattr`）

#### Scenario: 无 inc 调用的业务代码不被伪造真增
- **Given** 测试桩不调 `digest_metrics.inc`
- **When** 单测断言 `digest_metrics.inc("push_total") == 1`
- **Then** 测试 fail（防 dead code 复制 · 对应 T19 风险）

#### Scenario: metrics endpoint 仅本地访问
- **Given** 服务绑定 127.0.0.1
- **When** `curl http://0.0.0.0:PORT/api/digest/metrics`（外部访问）
- **Then** HTTP 403 或 connection refused（不暴露公网）

### Requirement: tasks-template § 9 埋点挂载点段
The system SHALL extend `tasks-template.md` with mandatory § 9 段 (event / metric 挂载 + 测试门禁), and `check-task-tasks.py`（或现有 tasks checker 扩展）fail L2 任务缺 § 9.

#### Scenario: L2 任务含 § 9 段 + 3 字段通过
- **Given** tasks.md 声明 `layer: L2` 且 § 9.1 event_name / trigger_location / data_fields 3 字段齐全
- **When** checker 跑
- **Then** exit code 0

#### Scenario: L2 任务缺 § 9 段被拒
- **Given** tasks.md L2 任务但无 § 9 段
- **When** checker 跑
- **Then** exit code 1
- **And** stderr 定位到 "§ 9 埋点挂载点缺失"

#### Scenario: event_name 不符合命名被拒
- **Given** event_name = "PushTotal" （含大写）或 "x" （< 3 字符）
- **When** checker 跑
- **Then** exit code 1 + regex 报错

#### Scenario: L1 探索性任务无埋点要求被豁免
- **Given** tasks.md 声明 `layer: L1`
- **When** checker 跑
- **Then** exit code 0（§ 9 可缺）

---

## 3. 边界条件（防御性 · 8 类必填）

### 3.1 空值 / 异常 / 并发
- **空值**：frontmatter 完全缺失 → checker exit 1 + "no frontmatter"
- **异常**：业务代码未注册 logger → logger startup 兜底为 NullHandler，不抛
- **并发**：100 个并发任务 trace_id 不串（见 SCN-P1.9.1）

### 3.2 时序（顺序依赖）
- `check-product-doc.py` 必在 commit 前（pre-commit hook 注册）
- trace_id race fix 必先于 logger startup（logger 依赖 trace_id 字段）
- metrics endpoint 必先于 L2 任务验收（无 endpoint → counter 无观察口）
- `check_metric_dict.py` 必在 L2 任务实施前注册

### 3.3 安全 / 权限
- `GET /api/digest/metrics` 仅 127.0.0.1 绑定（不暴露公网）
- 失败认证：N/A（本地基础设施，不需 token）
- 注入防护：frontmatter 用 PyYAML safe_load（不执行任意对象）
- trace_id 输入校验：UUID v4 格式（防日志注入）

### 3.4 性能 / QPS
- `check-product-doc.py` 跑 < 100ms（commit gate 不阻塞）
- `GET /api/digest/metrics` P95 < 50ms（不阻塞主路径）
- `digest_metrics.inc` 调 < 1μs（counter 单调，无锁）

### 3.5 兼容性 / 版本
- product-doc 模板 v1 → v2：旧实例可保留 `legacy_skeleton: true` 标记豁免校验
- tasks-template v1 → v2：旧任务豁免（仅新任务强制 § 9）
- API `/api/digest/metrics` v1：暂不锁版本号

### 3.6 国际化
- 不适用（指标字典 / event_name 英文命名 · 不本地化）
- 日志 message 暂不 i18n（单人项目 · 工具型日志）

### 3.7 Scenario 4 类覆盖（与 §2 联动）
| Requirement | happy | invalid | edge | failure |
|---|---|---|---|---|
| P1-7 | SCN-P1.7.1 | SCN-P1.7.2, .3, .4 | — | — |
| P1-8 | SCN-P1.8.1, .5 | SCN-P1.8.2, .3, .4 | SCN-P1.8.5 | SCN-P1.8.6 |
| P1-9 | SCN-P1.9.3, .4 | SCN-P1.9.2, .7 | SCN-P1.9.1, .5 | SCN-P1.9.6 |
| tasks § 9 | SCN-P1.9.8 | SCN-P1.9.9, .10 | SCN-P1.9.11 | — |

---

## 4. 数据契约（接口定义 · ≥ 1 schema）

### 4.1 Product Baseline Frontmatter（product-doc 扩展）

```python
# scripts/check-product-doc.py 内嵌 Pydantic schema
from pydantic import BaseModel, Field
from typing import List, Literal, Union

class ProblemEvidence(BaseModel):
    file: str  # 绝对路径
    line: int = Field(ge=1)
    quote: str = Field(max_length=80)
    baseline_value: Union[str, int, float, None]
    baseline_source: Literal["git_commit", "实测命令", "估算"]

class TargetUser(BaseModel):
    role: str = Field(min_length=2, max_length=50)
    persona_count: int = Field(ge=1, le=10)
    frequency_per_week: int = Field(ge=0, le=1000)
    device: Literal["桌面", "移动", "混合"]
    network: Literal["高带宽", "低带宽", "N-A"]

class KillCriterion(BaseModel):
    name: str = Field(max_length=30)
    trigger: str = Field(min_length=10, max_length=200)
    evidence: str = Field(min_length=10, max_length=200)

class DangerousAssumption(BaseModel):
    hypothesis: str = Field(min_length=20, max_length=200)
    falsification: str = Field(min_length=20, max_length=200)
    risk_level: Literal["🔴", "🟡", "🟢"]

class ProductBaseline(BaseModel):
    problem_evidence: List[ProblemEvidence] = Field(min_items=3, max_items=5)
    target_user: TargetUser
    kill_criteria: List[KillCriterion] = Field(min_items=1, max_items=3)
    dangerous_assumptions: List[DangerousAssumption] = Field(default_factory=list)
    legacy_skeleton: bool = False  # v1 → v2 兼容旧实例
```

### 4.2 Metric Dictionary（8 必填 + 4 可选）

```python
class EventRef(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_.]{2,50}$")
    file: str  # 业务代码绝对路径
    line: int = Field(ge=1)

class DedupSpec(BaseModel):
    primary_key: str  # e.g. "user_id" / "session_id"
    window: str = Field(pattern=r"^\d+[hd]$")  # e.g. "1h" / "7d" / "30d"

class Target(BaseModel):
    value: float = Field(ge=0)
    deadline: str  # ISO date
    source: str = Field(min_length=5)  # 数字来源

class MetricDict(BaseModel):
    metric_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,40}$")
    metric_name: str = Field(min_length=3, max_length=50)
    formula: str = Field(min_length=10, max_length=200)
    num_event: EventRef
    den_event: EventRef
    dedup: DedupSpec
    target: Target
    failure_action: List[str] = Field(min_items=1)  # 每条 ≥ 30 字符
    # 4 可选（L3 触发）
    current_baseline: Union[str, float, None] = None
    instrumentation_site: str = None
    owner: str = None
    observed_at: str = None
    layer: Literal["L0", "L1", "L2", "L3"]

# 副作用
- DB: 无变更（指标字典 = 独立文件 · `docs/metrics/<metric_id>.yaml`）
- Cache: 无
- Event: 无（埋点层决策 · 4.3 定义）
```

### 4.3 Event Hook（tasks § 9 段）

```python
class EventHook(BaseModel):
    task_id: str = Field(pattern=r"^T\d+$")
    event_name: str = Field(pattern=r"^[a-z][a-z0-9_.]{2,50}$")
    trigger_location: str  # file:line
    data_fields: List[str] = Field(min_items=1, max_items=10)
    counter_name: str = Field(pattern=r"^[a-z][a-z0-9_]{2,40}$")
    assertion: Literal["counter_increments", "no_change"]

# 副作用
- DB: 无
- Cache: 无
- Event: 业务代码触发时调 `digest_metrics.inc(counter_name)`
```

### 4.4 logger trace_id 字段契约（v1.1 修正 · 替代原 §4.4 trace_id ContextVar · 2026-07-27 调研偏差修正）

```python
# backend/utils/logger.py（扩展现有 logger · 2026-07-27）
import contextvars
import logging

trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)

class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = trace_id_var.get("")
        return True

# 业务代码
trace_id_var.set("req-uuid-v4")
logger = logging.getLogger("knockwise.digest")
logger.info("ok")  # 自动注入 trace_id 字段
```

**关键修正**：
- 实施对象：`backend/utils/logger.py`（已存在 · 调研偏差修正前误以为有 `trace_id.py`）
- 仍用 `contextvars.ContextVar`（满足 asyncio 隔离需求）
- 通过 `logging.Filter` 注入 trace_id 字段到所有日志记录
- 无新文件 · T9 改写为扩展 `logger.py` 而非新建 `trace_id.py`

---

## 5. 测试场景（验收测试 · ≥ 3）

> **DOD 校验友好列表**（check-step.py spec 校验找 `- [ ] TC-N` 格式）：

- [ ] **TC-1**: product_baseline happy path → `tests/test_check_product_doc.py::test_baseline_ok`（对应 SCN-P1.7.1 · L2）
- [ ] **TC-2**: product_baseline 缺段报错 → `tests/test_check_product_doc.py::test_baseline_missing_evidence`（对应 SCN-P1.7.2 · L2）
- [ ] **TC-3**: metric_dict 缺 failure_action 报错 → `tests/test_check_metric_dict.py::test_missing_failure_action`（对应 SCN-P1.8.2 · L2）
- [ ] **TC-4**: metric_dict failure_action 字符数 < 30 报错 → `tests/test_check_metric_dict.py::test_failure_action_too_short`（对应 SCN-P1.8.3 · L2）
- [ ] **TC-5**: logger trace_id 100 并发隔离 → `tests/test_logger_trace_id_field.py::test_concurrent_isolation`（对应 SCN-P1.9.1 v1.1 · L2+L3 · asyncio.gather 真跑）
- [ ] **TC-6**: counter 真增断言 → `tests/test_digest_metrics.py::test_counter_increments`（对应 SCN-P1.9.5 · L2 · 不只 mock hasattr）
- [ ] **TC-7**: tasks § 9 缺段报错 → `tests/test_check_tasks_template.py::test_section9_missing`（对应 SCN-P1.9.9 · L2）
- [ ] **TC-8**: metrics endpoint 4 counter 齐全 → `tests/test_metrics_endpoint.py::test_get_metrics_returns_4_counters`（对应 SCN-P1.9.4 · L3）
- [ ] **TC-9**: logger startup 接管 stdout → `tests/test_logger_startup.py::test_knockwise_logger_structured`（对应 SCN-P1.9.3 · L2）
- [ ] **TC-10**: L1 字典最小集豁免校验 → `tests/test_check_metric_dict.py::test_l1_minimal_set`（对应 SCN-P1.8.5 · L2）

**详细映射表**（含实施 commit / test / verifier / acceptance 4 列 · 4 步实施后回写）：

| TC | 名称 | 对应 SCN | Level | 实施位置 |
|---|---|---|---|---|
| TC-1 | product_baseline happy path | SCN-P1.7.1 | L2 | `tests/test_check_product_doc.py::test_baseline_ok` |
| TC-2 | product_baseline 缺段报错 | SCN-P1.7.2 | L2 | `tests/test_check_product_doc.py::test_baseline_missing_evidence` |
| TC-3 | metric_dict 缺 failure_action 报错 | SCN-P1.8.2 | L2 | `tests/test_check_metric_dict.py::test_missing_failure_action` |
| TC-4 | metric_dict failure_action 字符数 < 30 报错 | SCN-P1.8.3 | L2 | `tests/test_check_metric_dict.py::test_failure_action_too_short` |
| TC-5 | trace_id 100 并发隔离 | SCN-P1.9.1 | L3 | `tests/test_trace_id.py::test_concurrent_isolation` (asyncio.gather) |
| TC-6 | counter 真增断言 | SCN-P1.9.5 | L2 | `tests/test_digest_metrics.py::test_counter_increments` |
| TC-7 | tasks § 9 缺段报错 | SCN-P1.9.9 | L2 | `tests/test_check_tasks_template.py::test_section9_missing` |
| TC-8 | metrics endpoint 4 counter 齐全 | SCN-P1.9.4 | L3 | `tests/test_metrics_endpoint.py::test_get_metrics_returns_4_counters` |
| TC-9 | logger startup 接管 stdout | SCN-P1.9.3 | L2 | `tests/test_logger_startup.py::test_knockwise_logger_structured` |
| TC-10 | L1 字典最小集豁免校验 | SCN-P1.8.5 | L2 | `tests/test_check_metric_dict.py::test_l1_minimal_set` |

**关键**：TC-5 / TC-6 / TC-9 / TC-10 是**核心创新**（counter 真增 · 不只 mock `hasattr`）· 对应 research §2.3 风险 T19 dead code。

---

## 5.5 跨文档引用（必填 · 2 步产物）

| 文档 | 是否涉及 | 理由 |
|---|---|---|
| `plan.md` | ✅ **必出** | 多方案对比（template 加段 vs 新建独立 schema 文件）+ 实施顺序 + 估时 |
| `db-design.md` | ❌ 不涉及 | 决策明排除业务表 schema 强埋点 |
| `api-spec.md` | 🟡 1 个 | `GET /api/digest/metrics`（基础设施 · 仅本地 · 4 counter 键） |
| `component-spec.md` | ❌ 不涉及 | 无 UI 组件 |

**核心原则**：spec.md 是"业务契约"层 · 技术实现层（logger 库选型 / YAML 解析库 / ContextVar 性能 / endpoint 路由）归 2 步 plan.md + api-spec.md。

---

## 🎯 硬性 DOD（spec.md 完成必须全过）

- [x] 5 段齐全（§1 用户故事 · §2 Req+SCN · §3 边界 · §4 数据契约 · §5 测试场景）
- [x] Requirement = 4（P1-7 · P1-8 · P1-9 · tasks § 9）· SHALL 强约束
- [x] Scenario = 25（happy + invalid + edge + failure 4 类均覆盖 · 见 §3.7 表）
- [x] 数据契约 = 4 schema（ProductBaseline · MetricDict · EventHook · trace_id ContextVar）
- [x] 测试场景 = 10（TC-1 ~ TC-10 · 跨 L2/L3）
- [x] §0 上游引用齐全（research v1 + decisions 决策 1 + issues 主账）
- [ ] 用户故事已验收 · 待用户签字（"已验收：<name> <date>"）

> ⚠️ 工具校验：`python3 scripts/check-step.py spec docs/tasks/2026-07-23-refactor-product-foundation/spec.md`
> ⚠️ 任何 1 条未满足 → spec.md 不算完成 · 不能进 2 步

---

## 落地追踪

| 决策/Requirement | spec 状态 | 下一步 |
|---|---|---|
| 决策 1 P1-7 + P1-8 + P1-9 合并 | ✅ spec v1.1 写完（实施前调研偏差修正） | 用户验收 → 2 步 plan.md |
| 决策 1 audit verify.md 缺失补登记 | spec 范围内（§0 引用 issues.md）| 实施时回写 issues.md 决策段 |
| 决策 1 trace_id race fix | spec 范围内（P1-9 L1 平台层）| 2 步 plan + 3 步 tasks |
| 决策 1 模板最小 diff | spec 范围内（§ 4.1 / 4.3 锁定字段）| 2 步 plan 决定 template 加段 vs 新建 schema |
