---
title: 开发规范政策单一真源与一致性规格
type: spec
step: 1
date: 2026-08-09
status: approved
tags: [refactor, governance, policy, single-source]
related:
  - research.md
  - decisions.md
  - ../../issues.md
---

# 开发规范政策单一真源与一致性规格

> 路径模式：`fix-mini`（D-003 由 `refactor-6` 降级）
>
> 本文件只定义 R-01 的系统承诺和可验收行为。政策载体、生成语言、文件布局和分发方式留到步骤 2；本步骤不修改 Hook、Checker、CI 或现有状态控制面。

> **2026-08-09 最简修订（D-003）**：用户选择快速消除现有冲突，不建设 policy registry。本轮冻结的最小语义为：`[x]` 仅表示 implementation 已落 commit，可与 test/verifier FAIL 共存；裸 `✅ DONE` 仍禁止。其他单一真源、adapter、consumer lifecycle Requirement 暂缓，不作为本轮关闭条件。

## 0. 上游引用

- **调研报告**：[`research.md`](research.md)，重点是 R-01、§ 2.6 根因、§ 3.5 范围决策和 § 6 关闭条件。
- **决策主账**：[`decisions.md`](decisions.md) D-001。
- **议题主账**：[`docs/issues.md` 债务 25](../../issues.md)。
- **既有状态语义**：[`任务状态语义 spec`](../2026-07-23-refactor-task-status-semantics/spec.md)，复用 `[x]` 只表示 implementation、删除裸 `DONE` 的既有决策。
- **既有状态控制面**：[`AI Coding 控制面 v2 spec`](../2026-07-28-refactor-ai-coding-workflow-audit/spec.md)，继续作为运行状态与证据真源。
- **product-doc.md**：不适用；本任务是内部开发治理重构，不新增终端用户产品能力。
- **design-spec.md**：不适用；本任务不涉及 UI/UX。
- **用户确认**：用户已于 2026-08-09 回复「验收步骤 1，出方案」，验收本规格并授权进入步骤 2；技术方案仍待步骤 2 拍板。

### 0.1 规格范围

**包含**：

- 强制政策的唯一机器权威定义；
- 通用政策与项目 overlay 的优先级；
- 人读 adapter、模板提示、Checker、Hook/CI consumer 的派生或一致性验证；
- 重复规则、语义冲突、缺失接线和手改漂移的 fail-closed 行为；
- policy 版本、兼容、迁移和退役生命周期；
- 修复当前 `[x]` / `✅ DONE` 直接矛盾作为首个验收样例。

**不包含**：

- implementation/test/verifier/acceptance 等运行状态存储；
- 新建事件流、状态分支或替代 `workflow_state`；
- R-02～R-12 的独立整改；
- 创建或安装跨项目 Skill；
- 自动 push/merge、secrets 或远端 ruleset 配置；
- 全量改写历史任务文档。

## 1. 用户故事

### US-1 · 规范维护者修改一次

作为规范维护者，我希望一条强制政策只修改一个权威定义，以便 AGENTS、模板、Checker 和 Hook 不再依靠人工复制保持一致。

### US-2 · Writer 获得无冲突指令

作为 Writer Agent，我希望人读规则和 Gate 报错使用相同语义，以便遵守一条规则不会同时违反另一条规则。

### US-3 · Reviewer 识别真实接线

作为 Reviewer，我希望每条强制政策能列出并验证其 consumer，以便“文档声明已强制”不再冒充 Hook/CI 已接线。

**已验收**：用户已于 2026-08-09 指定修复 R-01，并以「验收步骤 1，出方案」冻结以上用户故事。

## 2. 验收标准

### Requirement: 政策唯一权威定义

The system SHALL identify exactly one authoritative machine definition for every active mandatory policy rule.

#### Scenario: 同一 rule id 只存在一个权威定义

- **Given** 一个 active 强制规则已有权威定义
- **When** 校验器扫描政策集合
- **Then** 该 rule id 只能解析到一个 authority
- **And** AGENTS、DOD 和模板中的同义文本不得被识别为第二个 authority

#### Scenario: 重复 rule id 冲突

- **Given** 通用内核和项目 overlay 声明同一 rule id
- **When** overlay 未显式声明允许覆盖关系或兼容版本
- **Then** 校验失败
- **And** 错误同时指出两个来源，不进行静默“后写覆盖前写”

### Requirement: 派生视图语义一致

The system SHALL derive or validate every registered adapter against the same canonical policy semantics.

#### Scenario: 修复 DONE 直接矛盾

- **Given** 既有权威语义规定 `[x]` 只表示 implementation 且禁止裸 `✅ DONE`
- **When** 生成或验证 AGENTS、tasks template、Checker 错误和 Hook 提示
- **Then** 所有 consumer 使用同一语义
- **And** 不再出现要求用户写入 `✅ DONE` 的指令

#### Scenario: 手工修改派生 adapter

- **Given** 一个派生区域包含 policy version 和 source digest
- **When** 内容被手改但权威 policy 未变化
- **Then** drift 校验失败
- **And** 输出 rule id、consumer、期望 digest 与实际 digest

### Requirement: 强制 consumer 可发现

The system SHALL register every mandatory policy consumer and report whether it is enforced, advisory, generated, or not applicable.

#### Scenario: 声明强制但 Hook 未接线

- **Given** 一条规则声明 local-hook consumer 为 enforced
- **When** consumer registry 无法证明 Hook 调用了对应 deterministic check
- **Then** governance 校验失败
- **And** 不得把 Markdown 中出现规则文字视为已接线

#### Scenario: consumer 明确不适用

- **Given** 项目没有 frontend 或远端 CI
- **When** 对应 consumer 被项目 overlay 标记 not_applicable 并提供理由
- **Then** coverage 校验通过
- **And** 结果保留明确的 N/A 证据，而不是静默忽略

### Requirement: 政策与运行状态分离

The system SHALL keep policy definitions separate from workflow execution state and evidence.

#### Scenario: policy 不接受运行事实

- **Given** implementation commit、test PASS 或 acceptance 事件已经产生
- **When** 系统更新任务当前状态
- **Then** 状态继续由既有 workflow-state 事件与投影计算
- **And** policy authority 不保存或覆盖这些运行事实

#### Scenario: 状态语义作为政策引用

- **Given** policy 需要解释 `[x]` 的合法含义
- **When** adapter 生成相关人读说明
- **Then** 它引用既有状态语义契约
- **And** 不复制一套新的 task 状态枚举

### Requirement: 政策生命周期可审计

The system SHALL version every policy change and require explicit compatibility, migration, test, and retirement metadata before activation.

#### Scenario: 破坏性政策变更

- **Given** 新版本改变既有 rule 的语义或 consumer
- **When** 变更未提供迁移策略和回归测试
- **Then** 激活被阻断
- **And** 旧版本保持 active 或任务标记 BLOCKED

#### Scenario: 规则退役

- **Given** 一条规则满足退役条件
- **When** 维护者提交 retirement metadata
- **Then** consumer 停止把它当 active 强制规则
- **And** 历史版本、替代规则和退役理由仍可审计

## 3. 边界条件

### 3.1 空值

- rule id、authority、statement、version 或 consumer 为空：校验失败，不生成 adapter。
- consumer 列表为空：强制规则失败；纯 advisory 规则必须显式声明无强制 consumer。

### 3.2 异常

- 权威 policy 无法解析、adapter 无法生成或 consumer 无法探测时：结果为 FAIL/BLOCKED，不沿用陈旧 PASS。
- 单个 consumer 错误不得吞掉其他诊断；最终退出码仍为非零。

### 3.3 并发

- 两个进程同时验证相同版本应产生相同结果。
- 两个变更并发修改同一 rule id 时不得静默覆盖；合并后的重复/版本冲突必须失败。

### 3.4 时序

- 先验证 canonical policy，再生成 adapter，最后验证 consumer wiring。
- 新政策只有在 schema、adapter、consumer 和回归测试同一变更通过后才 active。

### 3.5 安全

- 仓库 Markdown、Issue、日志和模型输出是待校验数据，不能自我升级为 authority。
- policy 工具默认只读；写 adapter 前必须显示 diff，禁止写 secrets、执行外部文本或自动 push。
- 路径必须归一化并限制在仓库允许目录，命令使用 argv，不拼接 shell 字符串。

### 3.6 性能

- 对当前仓库的 policy + adapter + consumer 静态校验目标为本地 P95 小于 2 秒。
- 不得为了静态政策校验启动 MySQL、Redis、LiveKit、backend 或 frontend。

### 3.7 兼容性

- 既有债务 13 状态语义保持不变；当前错误提示和文档迁移到该语义。
- 债务 23 的事件 schema、state ref 和投影不由本任务修改。
- 历史非生成文档允许 legacy 标记，但 active adapter 不允许无期限豁免。

### 3.8 国际化

- rule id、枚举和机器错误码保持稳定英文标识。
- 人读 adapter 可使用中文；翻译不得改变 SHALL、状态枚举或错误码语义。

## 4. 数据契约

> 以下是逻辑 Schema，不指定 YAML、JSON 或 Python 作为步骤 2 的最终技术载体。

```text
interface PolicyRule {
  rule_id: StableIdentifier
  version: SemanticVersion
  status: DRAFT | ACTIVE | DEPRECATED | RETIRED
  scope: UNIVERSAL | PROJECT
  authority: CanonicalSource
  statement: MandatoryStatement
  semantics: Map<StableKey, StableValue>
  consumers: ConsumerContract[]
  compatibility: CompatibilityContract
  migration: MigrationContract | N_A
  retirement: RetirementContract | N_A
}

interface ConsumerContract {
  consumer_id: StableIdentifier
  kind: HUMAN_ADAPTER | TEMPLATE | CHECKER | LOCAL_HOOK | CI
  mode: GENERATED | VALIDATED | ENFORCED | ADVISORY | NOT_APPLICABLE
  target: RepositoryRelativePath | StableCommand
  evidence: DeterministicEvidenceContract
}
```

### 4.1 权威与覆盖规则

1. `rule_id + version` 唯一。
2. PROJECT overlay 只能覆盖明确标记为 configurable 的字段，不能改写通用安全不变量。
3. consumer 未注册不能声称 enforced。
4. generated adapter 必须携带 source version/digest；validated adapter 必须有等价性测试。
5. policy 只描述规则，不持有 workflow event 或当前 task state。

## 5. 测试场景

- TC-001：单一 rule id + 多个派生 consumer，validate PASS。
- TC-002：重复 rule id 且无合法 overlay，validate rc 非零并报告两个来源。
- TC-003：AGENTS 要求 `✅ DONE`、canonical 禁止时，语义冲突被捕获。
- TC-004：pre-commit 提示要求被 canonical 禁止的写法时，consumer drift 被捕获。
- TC-005：强制 checker 已声明但 Hook/CI 未接线时，coverage FAIL。
- TC-006：无 frontend 项目显式 `NOT_APPLICABLE + reason` 时，coverage PASS。
- TC-007：手改 generated adapter 后 source digest 不匹配，validate FAIL。
- TC-008：policy 文档中出现 implementation/test PASS，不改变 workflow-state projection。
- TC-009：破坏性 policy 变更缺 migration/test 时，activation BLOCKED。
- TC-010：同一输入连续验证两次，输出与退出码完全一致。

## 6. 追溯与验收

| Requirement | Scenarios | Tests | 关闭条件 |
|---|---|---|---|
| 政策唯一权威定义 | 单一/重复 rule id | TC-001/002 | research § 6.1 |
| 派生视图语义一致 | DONE 冲突/手改 adapter | TC-003/004/007 | research § 6.2/6.4 |
| 强制 consumer 可发现 | 未接线/N/A | TC-005/006 | research § 6.3 |
| 政策与运行状态分离 | 不接受运行事实/引用状态语义 | TC-008 | research § 6.5 |
| 政策生命周期可审计 | 破坏性变更/退役 | TC-009/010 | research § 6.6 |

### 6.1 步骤 1 Gate

- **规格状态**：`APPROVED`。
- **验收人**：用户。
- **验收日期**：2026-08-09。
- **验收原话**：「验收步骤 1，出方案」。
- **当前限制**：已授权进入步骤 2；技术方案未验收前不得拆任务或实施，不得修改现有政策、Hook、Checker、CI 或安装 Skill。
