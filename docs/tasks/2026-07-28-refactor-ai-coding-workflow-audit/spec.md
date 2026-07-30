---
title: AI Coding 控制面 v2 · 单一事件真源与自动投影规格
type: spec
step: 1
date: 2026-07-29
status: approved
tags: [refactor, governance, event-source, projection, ai-coding]
related:
  - research.md
  - decisions.md
  - plan.md
  - tasks.md
  - task.yaml
  - ../../issues.md
---

# AI Coding 控制面 v2 · 单一事件真源与自动投影规格

> 路径模式：`refactor-6`
>
> 本文件只定义系统承诺和验收行为。事件介质选 Git ref、状态分支还是外部存储，
> CLI 命令与文件布局等实现选择留到步骤 2。

## 0. 上游引用

- **调研报告**：[`research.md`](research.md)，特别是 §2 F-03/F-04/F-09 与 §6 专项核验。
- **决策主账**：[`decisions.md`](decisions.md) D-002、D-004。
- **长期议题**：[`docs/issues.md` 债务 23](../../issues.md)。
- **product-doc.md**：不适用；本任务是治理控制面重构，不新增面向终端用户的产品功能。
- **design-spec.md**：不适用；本任务不涉及页面或 UI/UX。
- **调研版本**：2026-07-29 专项核验版。
- **已确认方向**：用户已选择方案 B，并于 2026-07-29 授权「那你修复下」。
- **规格验收状态**：✅ 用户已于 2026-07-29 验收；原话：「验收步骤 1，出方案」。
- **技术方案镜像**：✅ 用户已于 2026-07-30 验收 [`plan.md`](plan.md)；
  选择独立受保护 `workflow-state` branch + 不可变事件文件 + CAS，并按推荐拍板
  Actor 信任、投影位置、迁移范围和 Shadow→Enforce 节奏。权威详细记录见
  [`decisions.md` D-006](decisions.md)。

### 0.1 关键事实

1. 11 个带 `task.yaml` 的任务中，6 个存在明显 manifest/tasks 状态漂移。
2. 最近 100 个 commit 中有 16 个 tasks 状态或 commit evidence 回写。
3. 当前 checker 可放行 `accepted`、缺步骤产物且 evidence path 不存在的隔离探针。
4. 当前没有事件日志、投影器、重建命令或跨视图一致性 Gate。

### 0.2 规格边界

**包含**：

- 唯一机器事件真源；
- 正交状态语义；
- actor 写权限；
- 状态转移；
- 自动投影视图；
- commit/test/verifier/acceptance/merge evidence 绑定；
- 并发、幂等、损坏恢复；
- 活跃旧任务迁移边界。

**不包含**：

- 事件存储介质和 CLI 技术选型；
- GitHub 远端 ruleset 的实际配置；
- 全量历史任务回填；
- 业务 research/spec/plan/decision 正文自动生成；
- 本步骤直接修改 checker、Hook、CI 或模板。

## 1. 用户故事

### US-1 · 后续 Agent 恢复任务

作为接手任务的 Writer 或 Verifier Agent，我想从一个机器真源读取任务状态，
以便不用猜测 `task.yaml/tasks/verify/issues` 哪一份更新。

### US-2 · 用户判断真实进度

作为验收人，我想看到 implementation、test、verifier、acceptance 和 merge Gate
分别处于什么状态，以便一个 PASS 不会冒充整个任务已完成。

### US-3 · 治理维护者重建状态

作为治理维护者，我想删除所有生成视图后从事件重新投影，以便检测漂移、恢复损坏，
并停止人工六处同步。

**方向已确认**：用户已选择方案 B 并授权开始修复；以上用户故事的具体契约待本步骤验收。

## 2. 验收标准

### Requirement: 唯一机器事件真源

The system SHALL treat one append-only task event stream as the sole authority for machine execution state.

#### Scenario: 从事件恢复当前状态

- **Given** 一个任务已有创建、scope、implementation、test 和 verifier 事件
- **When** 任意 Agent 查询任务当前状态
- **Then** 系统从事件流确定状态
- **And** 不读取 Markdown 中的手写 PASS 作为权威事实

#### Scenario: 试图覆盖历史事件

- **Given** 事件流已有序号 1～20
- **When** Writer 尝试修改或删除序号 10
- **Then** 写入被拒绝
- **And** 当前状态保持不变

### Requirement: 正交状态语义

The system SHALL project workflow, implementation, test, verifier, acceptance, and merge-gate states as independent facts.

#### Scenario: 测试通过但未验收

- **Given** implementation commit 已观察且测试 PASS
- **When** verifier 或用户验收事件尚不存在
- **Then** test state 为 PASS
- **And** verifier state 为 NOT_RUN
- **And** acceptance state 为 PENDING
- **And**任务不得投影为 completed

#### Scenario: verifier 失败

- **Given** implementation 和 test 已通过
- **When** 固定 commit 的 verifier 结果为 FAIL
- **Then** verifier state 为 FAIL
- **And** implementation state 不被回写成未实施
- **And** acceptance state 不得自动变为 ACCEPTED

### Requirement: 受信 Actor 写入

The system SHALL authorize each event type to one explicit actor class and reject self-attestation across actor boundaries.

#### Scenario: Writer 伪造用户验收

- **Given** Writer 拥有代码和文档写权限
- **When** Writer 提交 `phase_accepted` 或 `step_accepted` 事件
- **Then** 系统拒绝该事件
- **And** 记录 actor authorization failure

#### Scenario: Writer 伪造 verifier PASS

- **Given** Writer 完成 implementation commit
- **When** Writer 尝试写入 `verifier_observed(result=PASS)`
- **Then** 系统拒绝该事件
- **And** verifier state 保持 NOT_RUN

### Requirement: Commit 后置观察

The system SHALL record an implementation commit only after an observer has resolved its immutable full commit SHA.

#### Scenario: 实施 commit 产生真实 SHA

- **Given** staged patch 尚未形成 commit
- **When** Git 成功创建 implementation commit
- **Then** observer 以 40 字符 commit SHA 写入 `implementation_committed`
- **And** feature commit 本身不包含对自己 SHA 的回填

#### Scenario: Commit 不存在

- **Given** 一个 `implementation_committed` 事件引用某 SHA
- **When** observer 无法在目标仓库验证该 commit
- **Then** 事件被拒绝或标记 BLOCKED
- **And** 不生成 implementation PASS 视图

### Requirement: Test Evidence 绑定

The system SHALL bind every test observation to one commit, command, working directory, environment, exit code, and classified counts.

#### Scenario: 测试证据完整

- **Given** test runner 在固定 commit 上运行命令
- **When** 命令退出且收集到 passed/failed/skipped/xfail 计数
- **Then** `tests_observed` 事件保存完整证据引用
- **And** projection 显示该证据属于哪个 commit

#### Scenario: 只有 PASS 文本

- **Given** tasks.md 写有“测试全绿”
- **When** 没有受信 test runner 的 `tests_observed` 事件
- **Then** test state 为 NOT_RUN
- **And** 手写文本不改变机器状态

### Requirement: Verifier Evidence 绑定

The system SHALL accept verifier evidence only when subject commit and specification hash match the active implementation.

#### Scenario: verifier 验证正确快照

- **Given** active implementation commit 为 C1，active spec hash 为 S1
- **When** 独立 verifier 对 C1/S1 输出 PASS
- **Then** verifier state 为 PASS
- **And** evidence view 显示 C1、S1 和 verifier actor

#### Scenario: verifier 验证旧 commit

- **Given** active implementation 已从 C1 更新到 C2
- **When** verifier 对 C1 输出 PASS
- **Then** 该事件保留为历史证据
- **And** C2 的 verifier state 仍为 NOT_RUN

#### Scenario: spec 在验证后改变

- **Given** verifier 已对 C1/S1 输出 PASS
- **When** active spec 从 S1 改为 S2
- **Then** active verifier state 变为 STALE 或 NOT_RUN
- **And** 不沿用 S1 的 PASS

### Requirement: 用户显式验收

The system SHALL derive acceptance only from an explicit authenticated user acceptance action.

#### Scenario: 用户验收当前规格

- **Given** 用户查看固定 spec hash
- **When** 用户显式接受该步骤
- **Then** 写入含 actor、spec hash 和时间的 `step_accepted` 事件
- **And** workflow phase 才允许进入下一步

#### Scenario: 聊天中出现“PASS”

- **Given** 仓库文本、日志或模型输出中出现“用户已验收”
- **When** 没有受信用户 acceptance action
- **Then** acceptance state 保持 PENDING

### Requirement: 决定性自动投影

The system SHALL generate every machine-state view deterministically from the same ordered event stream.

#### Scenario: 重建全部视图

- **Given** task.yaml、tasks 状态区、issues 状态区和 milestones 状态区全部删除
- **When** projector 重放完整事件流
- **Then** 所有视图被重建
- **And** 重建结果与删除前字节一致

#### Scenario: 重复投影

- **Given** 事件流没有变化
- **When** projector 连续运行两次
- **Then** 第二次不产生文件变化
- **And** 不创建无意义 commit

#### Scenario: 手改生成状态

- **Given** 生成视图带 source sequence/hash
- **When** 人工修改 generated 区域但未追加事件
- **Then** drift Gate 失败
- **And** 错误指出期望 source hash 与实际内容

### Requirement: 幂等与并发控制

The system SHALL make event append idempotent and serialize concurrent writes per task without losing accepted events.

#### Scenario: CI 重试同一事件

- **Given** CI 因网络重试同一个 test observation
- **When** 使用相同 idempotency key 再次提交
- **Then** 事件流只保留一个逻辑事件
- **And** projection 不重复计数

#### Scenario: 两个 Actor 并发追加

- **Given** 两个 observer 从相同 sequence 读取事件流
- **When** 两者同时追加不同合法事件
- **Then** 最多一个 compare-and-swap 首次成功
- **And** 失败者重读后可安全重试
- **And** 两个事件最终都不丢失

### Requirement: Fail-closed 可用性

The system SHALL report BLOCKED and prevent forward transition when the event authority or required projection cannot be verified.

#### Scenario: 事件真源不可用

- **Given** Writer 已产生代码 commit
- **When** observer 无法连接或写入事件真源
- **Then** implementation observation 标记 BLOCKED
- **And** 系统不得把任务投影为已同步或已完成

#### Scenario: 投影器遇到未知 schema

- **Given** 事件流含不支持的 schema version
- **When** projector 重放
- **Then** 投影失败并返回非零
- **And** 保留上一个已验证 snapshot

### Requirement: 兼容迁移

The system SHALL migrate new and active tasks without converting unverified legacy text into trusted machine evidence.

#### Scenario: 新任务使用 v2

- **Given** 创建控制面 v2 生效后的新任务
- **When** task creation 完成
- **Then** 首个事实为受 schema 校验的 `task_created`
- **And** 状态视图由事件投影生成

#### Scenario: 导入活跃旧任务

- **Given** 旧任务只有 task.yaml/tasks.md/verify.md 文本
- **When** 迁移器导入当前 snapshot
- **Then** 只写一个 `legacy_snapshot_imported`
- **And** evidence trust 标记为 LEGACY_UNVERIFIED
- **And** 不伪造历史 test/verifier/acceptance 事件

#### Scenario: 历史任务保持只读

- **Given** 已归档且不再活跃的旧任务
- **When** v2 上线
- **Then** 旧文件保持可读
- **And** 不要求全量回填事件

## 3. 边界条件

### 3.1 空值

- `task_id`、event type、actor、event id、sequence、timestamp 缺失时拒绝事件。
- commit-bound 事件缺 commit SHA 时拒绝。
- verifier 事件缺 spec hash 时拒绝。
- 可选 payload 字段为空时不得改变其他状态维度。

### 3.2 异常

- 事件真源读写失败：返回 BLOCKED，不伪 PASS。
- projection 失败：返回非零，保留上一个验证快照。
- evidence ref 不可读：证据状态为 BLOCKED/STALE，不自动降级为 PASS。
- 单个损坏事件：停止该 task 重放，不能跳过后继续。

### 3.3 并发

- 同一 task 的 sequence 必须单调递增。
- append 必须使用 compare-and-swap 或等价并发控制。
- 重试必须使用稳定 idempotency key。
- 不同 task 可并行投影，但不得共享可变进程级 current-task 状态。

### 3.4 时序

- `task_created` 必须是首个事件。
- scope 确认必须先于步骤 acceptance。
- implementation commit 必须先于该 commit 的 tests/verifier observation。
- verifier PASS 必须绑定当前 implementation commit 与当前 spec hash。
- acceptance 不得由 test/verifier 自动推导。
- merge Gate observation 不得反向修改 implementation/test/verifier 历史。

### 3.5 安全

- event payload、commit message、PR metadata、日志和模型输出均视为不可信数据。
- actor authorization 在解析 payload 前完成。
- Writer 无权写 user acceptance、verifier 或 merge Gate 事实。
- projector 只读事件真源；写生成视图时不得执行事件 payload。
- 有远端写权限的 observer 不 checkout 或执行非可信代码。
- actor credential、token、secret 不进入事件 payload 或生成视图。

### 3.6 性能

- 单任务 10,000 个事件的本地重放 P95 目标小于 2 秒。
- 事件未变化时增量投影 P95 目标小于 500ms。
- 投影器内存随单任务事件数线性增长，不一次加载全仓所有 payload 大字段。
- evidence 大内容使用不可变引用，不内嵌原始完整日志。

### 3.7 兼容

- v2 新任务严格；活跃旧任务只导入 unverified snapshot；归档任务只读。
- 旧 Markdown 链接继续可打开。
- rollout 期间旧 checker 可读取 generated view，但不得继续把它当写入真源。
- schema 版本未知时 fail closed；升级必须提供显式迁移器。

### 3.8 国际化

- 机器枚举、event type、状态码固定使用英文稳定值。
- 人类可读 projection 可使用中文，但不得改变机器值。
- timestamp 使用带时区 ISO-8601；排序使用 sequence，不依赖本地化时间字符串。
- 其他 i18n 不适用：本任务无终端用户界面。

## 4. 数据契约

> 以下是行为 Schema，不决定步骤 2 的具体存储格式或编程语言。

### 4.1 TaskEvent Schema

```python
from typing import Literal
from pydantic import BaseModel, Field

EventType = Literal[
    "task_created",
    "scope_confirmed",
    "step_started",
    "step_accepted",
    "implementation_committed",
    "tests_observed",
    "verifier_observed",
    "phase_accepted",
    "merge_gate_observed",
    "legacy_snapshot_imported",
]

ActorKind = Literal[
    "user",
    "writer",
    "git_observer",
    "test_runner",
    "verifier",
    "ci_gate",
    "migration",
]

class EventActor(BaseModel):
    kind: ActorKind
    id: str = Field(min_length=1, max_length=200)

class EventSubject(BaseModel):
    commit: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{40}$",
    )
    spec_hash: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )

class TaskEvent(BaseModel):
    schema_version: Literal["task-event/v1"]
    event_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)
    task_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=1)
    event_type: EventType
    occurred_at: str
    actor: EventActor
    subject: EventSubject
    payload: dict
    previous_event_hash: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
```

业务不变量：

- `(task_id, sequence)` 唯一。
- `(task_id, idempotency_key)` 唯一。
- sequence > 1 时 `previous_event_hash` 必填且匹配上一事件。
- actor.kind 必须被授权写对应 event_type。
- commit-bound event 必须提供合法 commit SHA。
- verifier event 必须提供 commit + spec hash。

### 4.2 TaskProjection Schema

```python
WorkflowPhase = Literal[
    "research",
    "spec",
    "plan",
    "tasks",
    "implementation",
    "verification",
    "retro",
]

EvidenceState = Literal[
    "NOT_RUN",
    "PASS",
    "FAIL",
    "BLOCKED",
    "STALE",
]

AcceptanceState = Literal[
    "PENDING",
    "ACCEPTED",
    "REJECTED",
]

class TaskProjection(BaseModel):
    schema_version: Literal["task-projection/v1"]
    task_id: str
    source_sequence: int = Field(ge=1)
    source_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    workflow_phase: WorkflowPhase
    implementation_state: EvidenceState
    test_state: EvidenceState
    verifier_state: EvidenceState
    acceptance_state: AcceptanceState
    merge_gate_state: EvidenceState
    active_commit: str | None
    active_spec_hash: str | None
    legacy_trust: Literal["NATIVE", "LEGACY_UNVERIFIED"]
```

业务不变量：

- projection 只能由 ordered events 计算，不能独立编辑。
- active commit 改变后，旧 test/verifier evidence 不得自动沿用。
- active spec hash 改变后，旧 verifier PASS 变为 STALE。
- overall “completed” 只能是 projection 展示值，不是独立可写状态。

### 4.3 Actor 权限矩阵

| Event | user | writer | git observer | test runner | verifier | CI gate | migration |
|---|---:|---:|---:|---:|---:|---:|---:|
| task_created | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| scope_confirmed | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| step_started | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| step_accepted | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| implementation_committed | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| tests_observed | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| verifier_observed | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| phase_accepted | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| merge_gate_observed | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| legacy_snapshot_imported | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

Migration actor 写入的历史事实必须统一带 `LEGACY_UNVERIFIED`，不能获得 native trust。

### 4.4 自动投影视图

| View | 人工正文 | generated 区域 | 权威性 |
|---|---|---|---|
| `task.yaml` v2 snapshot | 无 | 全文件 | 只读 cache |
| `tasks.md` | task 描述、依赖、估时 | implementation/test/verifier/acceptance/commit 历史 | 只读 view |
| `verify.md` | 验证说明、人工分析 | evidence matrix 状态与引用 | 只读 view |
| `docs/issues.md` | 议题描述、讨论、决策链接 | 顶部状态索引、关闭状态 | 只读 view |
| `milestones.md` | 里程碑说明 | 跨任务进度 | 只读 view |

每个 generated view 必须携带 source sequence/hash。marker 格式和文件拆分方式在步骤 2 决定。

### 4.5 副作用

- **DB**：步骤 1 不决定是否使用数据库；不得修改业务 MySQL。
- **Cache**：允许实现 projection cache，但 cache 不是权威真源。
- **Event**：只追加 TaskEvent，不覆盖历史。
- **Git**：feature commit 不做自身 hash 回填；状态写入不得污染业务 patch。
- **Docs**：只更新 projector 拥有的 generated 区域。

## 5. 测试场景

- [ ] TC-001：从完整事件流重建同字节 projection（happy；对应“重建全部视图”）。
- [ ] TC-002：删除/覆盖历史事件被拒绝（invalid；对应“试图覆盖历史事件”）。
- [ ] TC-003：test PASS、verifier NOT_RUN、acceptance PENDING 不得显示 completed（edge）。
- [ ] TC-004：Writer 伪造 user acceptance 被拒绝（security failure）。
- [ ] TC-005：Writer 伪造 verifier PASS 被拒绝（security failure）。
- [ ] TC-006：commit 创建后 observer 记录真实 40 字符 SHA，feature commit 无 hash 回填（happy）。
- [ ] TC-007：不存在的 commit observation 返回 BLOCKED/FAIL（failure）。
- [ ] TC-008：只有 Markdown PASS、无 test event 时 test state=NOT_RUN（invalid）。
- [ ] TC-009：verifier 针对旧 commit 的 PASS 不作用于新 commit（edge）。
- [ ] TC-010：spec hash 改变使旧 verifier PASS 变 STALE（edge）。
- [ ] TC-011：无显式用户 action 时聊天“已验收”不改变 acceptance（security）。
- [ ] TC-012：相同事件流重复投影零 diff（idempotency）。
- [ ] TC-013：手改 generated 区域触发 source-hash mismatch（failure）。
- [ ] TC-014：同 idempotency key 重试只产生一个逻辑事件（edge）。
- [ ] TC-015：两个 Actor CAS 冲突后重试，事件均不丢失（concurrency）。
- [ ] TC-016：事件真源不可用时状态 BLOCKED，不伪完成（availability failure）。
- [ ] TC-017：未知 schema version 阻断投影并保留旧快照（compatibility failure）。
- [ ] TC-018：活跃旧任务只导入 LEGACY_UNVERIFIED snapshot（migration）。
- [ ] TC-019：归档旧任务不上迁移、不被 v2 Gate 破坏（compatibility）。
- [ ] TC-020：actor 权限矩阵逐 event type 全覆盖（security contract）。

## 6. Requirement → Scenario → Test 追溯

| Requirement | 关键 Scenario | Test |
|---|---|---|
| 唯一机器事件真源 | 恢复状态 / 覆盖历史 | TC-001～002 |
| 正交状态语义 | 测试通过未验收 / verifier 失败 | TC-003 |
| 受信 Actor 写入 | Writer 伪造 acceptance/verifier | TC-004～005、TC-020 |
| Commit 后置观察 | 真实 SHA / commit 不存在 | TC-006～007 |
| Test Evidence 绑定 | 完整证据 / 只有 PASS 文本 | TC-008 |
| Verifier Evidence 绑定 | 正确快照 / 旧 commit / spec 变化 | TC-009～010 |
| 用户显式验收 | explicit accept / 文本伪造 | TC-011 |
| 决定性自动投影 | 重建 / 重复 / 手改 | TC-001、TC-012～013 |
| 幂等与并发控制 | 重试 / CAS 冲突 | TC-014～015 |
| Fail-closed 可用性 | 真源不可用 / 未知 schema | TC-016～017 |
| 兼容迁移 | active legacy / archive | TC-018～019 |

## 7. 人与 AI 职责

| 事项 | AI | 用户 |
|---|---|---|
| 从 research 提炼系统契约 | 负责 | review |
| 定义测试场景与不变量 | 负责 | review |
| 选择事件存储/投影技术方案 | 步骤 2 给至少两案与推荐 | 拍板 |
| 接受本规格 | 不得自签 | 明确验收 |
| 实施和测试 | 步骤 4 执行 | review diff |
| 用户 acceptance 事件 | 不得代写 | 显式触发 |

## 8. 步骤 1 DOD

- [x] 用户故事 3 条，方向已确认，规格内容待用户验收。
- [x] Requirement 使用 SHALL。
- [x] Scenario 覆盖 happy、invalid、edge、failure、安全和并发。
- [x] 八类边界齐全。
- [x] TaskEvent 与 TaskProjection Schema 齐全。
- [x] 测试场景 20 条并有追溯矩阵。
- [x] 引用 research.md、decisions.md 与 issues 债务 23。
- [x] product-doc/design-spec 明确不适用。
- [x] 用户于 2026-07-29 验收本规格；原话：「验收步骤 1，出方案」。

> 当前 Gate：**ACCEPTED**。步骤 1～3 均已获用户验收；用户于 2026-07-30
> 明确「验收步骤 3，开始实施」，当前按本规格进入步骤 4。
