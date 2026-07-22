---
title: Spec 规格模板（技术脑）
date: 2026-06-27
status: v1
tags: [spec, 1步, 技术脑, 模板]
related:
  - [product-doc-template.md](product-doc-template.md) — 配套产品脑
  - [test-cases-template.md](test-cases-template.md) — 4 步产出
---

# Spec 规格模板（技术脑）

> **一句话**：把"产品意图"翻译成"机器可读的契约"——AI 实施的依据，QA 验收的标准。
>
> **产出时机**：1 步规格阶段（new-feature 必填，bug/refactor 可选）。
>
> **对应 DOD**：见 `docs/DOD.md` §三.3。
>
> **上游**：research.md（0 步）+ product-doc.md（人主导的产品脑）
>
> **下游**：tasks.md（3 步）+ test-cases.md（4 步后整合）+ verify.md（5 步）

---

## 0. 上游引用（必填）

- **调研报告**：`docs/tasks/<date>-<type>-<topic>/research.md`
- **产品文档**：`docs/tasks/<date>-<type>-<topic>/product-doc.md`（new-feature 必填）
- **调研版本**：v1（调研更新后 spec 同步标 v2）
- **关键决策**（从 product-doc §3 抄）：<从产品文档抄>
- **关键风险**（从 research §4 抄，标 🔴 的）：<从调研抄>

---

## 1. 用户故事（产品意图，必填）

```markdown
作为 <角色>，我想要 <能力>，以便 <价值>
```

**示例**：
作为 25-35 岁职场人，我想要根据兴趣订阅 AI 推送，以便通勤时获得高质量内容（不用花时间筛选）。

**要求**：
- ≤ 3 条用户故事（多了 = 范围太大，应该拆成多个 spec）
- 每条必须可独立验收
- 引用 product-doc §2 目标用户（角色要具体）

---

## 2. 验收标准 / Requirement + Scenario（机器可验证，必填）

> **升级说明（2026-07-17）**：从纯 GWT 升级为 **Requirement (SHALL) + Scenario (GWT)** 双层结构。
> - **Requirement 层** 写"系统承诺"——强制 SHALL，禁 should/may
> - **Scenario 层** 写"验收用例"——沿用 GWT（Given/When/Then），向后兼容
> - 既有 GWT 用法继续生效，只是包在 Requirement 下面
> - 来源：借鉴 [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) 的 SDD 写法（我们不装 OpenSpec，只白嫖写法）

### 2.1 Requirement（系统承诺 · 必填 ≥ 1）

```markdown
### Requirement: <功能名（动词 + 名词）>
The system SHALL <单一可验证的承诺>.
```

**要求**：
- 必填 `SHALL`（强制承诺；`should` / `may` 一律视为不通过）
- 每个 Requirement 单一职责（不要把多个承诺写一起）
- Requirement 数量与下方 Scenario 数量不强制 1:1，但**至少 1 个 Requirement + ≥ 3 个 Scenario**

### 2.2 Scenario（验收用例 · 必填 ≥ 3 · 沿用 GWT）

```markdown
#### Scenario: <场景名（happy / invalid / edge / failure）>
- **Given** <前置条件>
- **When** <动作>
- **Then** <期望结果 1>
- **And** <期望结果 2>（可选）
```

**完整示例**：

```markdown
### Requirement: User Authentication
The system SHALL validate user credentials and return a JWT token on success.

#### Scenario: Successful login
- **Given** a registered user with username "alice@example.com"
- **When** user submits valid username and password
- **Then** system returns HTTP 200
- **And** response body contains a JWT token
- **And** token expires in 24 hours

#### Scenario: Invalid credentials
- **Given** a registered user with username "alice@example.com"
- **When** user submits an incorrect password
- **Then** system returns HTTP 401
- **And** error code is "AUTH_INVALID"

#### Scenario: Empty fields
- **Given** the login form is empty
- **When** user clicks submit
- **Then** system returns HTTP 422
- **And** error code is "VALIDATION_REQUIRED_FIELD"

#### Scenario: Rate limit exceeded
- **Given** user has submitted credentials 5 times in 1 minute
- **When** user submits credentials a 6th time
- **Then** system returns HTTP 429
- **And** response includes Retry-After header
```

**要求**：
- **Scenario ≥ 3 条**（happy + invalid + edge/failure 各 ≥ 1）
- 每条 Scenario 必须能直接转成测试用例
- failure Scenario 必须存在（AI 写 Scenario 容易偏向 happy）
- 4 类场景覆盖参考 §3.7

### 2.3 与单测的对接

- 每个 Scenario 的 When/Then → **对应 1 个 pytest 用例**（happy / invalid / edge / failure 各 1 个起步）
- spec.md 写完后 → 步 4 实施时**直接照 Scenario 写测试**（红→绿），不必再设计测试
- 改 spec.md → 必须同步改测试（双向同步，防 drift）

---

## 3. 边界条件（防御性，必填）

```markdown
### 3.1 空值 / 异常 / 并发（基础）
- 空值: <输入为空时>
- 异常: <网络失败、DB 断连时>
- 并发: <同时 N 个请求时>

### 3.2 时序（顺序依赖）
- 操作 A 必须先于 B：<为什么>

### 3.3 安全 / 权限
- 权限校验：<谁能做什么>
- 注入防护：<SQL/XSS/CMD 注入>

### 3.4 性能 / QPS
- 响应时间：<P95 < 200ms>
- QPS 上限：<QPS > 1000 时>

### 3.5 兼容性 / 版本
- 向后兼容：<旧 API 还能用>
- 前向兼容：<未来改动不影响>

### 3.6 国际化
- 时区：<用户 profile 自动适配>
- 多语言：<文案 i18n>
```

**要求**：
- 8 类必填：空值/异常/并发/时序/安全/性能/兼容/国际化
- 不适用 = 显式标注"不适用 + 理由"

### 3.7 Scenario 4 类场景覆盖（与 §2.2 联动）

| 场景类型 | 必填 | 写什么 | 例子 |
|---|---|---|---|
| **Happy path** | ✅ | 正常输入 → 正常输出 | 登录成功 → 200 + JWT |
| **Invalid input** | ✅ | 错误/空/越界 → 错误码 | 错误密码 → 401 + AUTH_INVALID |
| **Edge / 边界值** | 🟡 推荐 | 最小/最大/临界值 | 24h 内 token → 正好过期 |
| **Failure / 异常路径** | 🟡 推荐 | 网络/超时/并发/权限/限流 | 网络失败 → 重试 3 次后放弃 |

**联动规则**：
- §2.2 至少要有 **happy + invalid** 两类
- §3 边界条件段里涉及的边界 → 在 §2.2 至少有 1 个对应 Scenario

---

## 4. 数据契约（接口定义，必填）

```python
# Pydantic / TypeScript interface

class <RequestName>(BaseModel):
    <field>: <type>  # 业务：<业务规则>
    <field>: <type> = Field(<constraint>)  # 业务：<业务规则>

class <ResponseName>(BaseModel):
    <field>: <type>

# 副作用（DB 变更 / 缓存 / 事件）
- DB: <哪些表变更>
- Cache: <哪些 key 失效>
- Event: <发哪些事件>
```

**示例**：
```python
class PushSubscription(BaseModel):
    user_id: int
    tags: List[str] = Field(min_items=0, max_items=5)  # 业务：最多 5 个标签
    time_window: TimeWindow  # 业务：用户本地时区

class PushNotification(BaseModel):
    subscription_id: int
    title: str = Field(max_length=50)  # 业务：title 不超 50 字
    content: str = Field(max_length=200)
    tag: str

# 副作用
- DB: subscription / push_history 2 张表
- Cache: user_subscription:{user_id} 失效
- Event: PushDeliveredEvent 上报
```

**要求**：
- ≥ 1 schema（输入或输出）
- 业务不变量必须写（`age: int = Field(ge=0)`，不是 `age: int`）
- 副作用明确（DB / Cache / Event）

---

## 5. 测试场景（验收测试，必填）

```markdown
- [ ] TC-1: <happy path 1>  ← 对应 GWT happy
- [ ] TC-2: <edge case 1>  ← 对应 GWT edge
- [ ] TC-3: <failure case 1> ← 对应 GWT failure
```

**要求**：
- **测试场景 ≥ 3 条**（happy + edge + failure 各 ≥ 1）
- 每个 TC 必须对应一个 GWT（追溯关系）
- 4 步实现时，test-cases.md §1 验收测试从这里提炼

---

## AI vs 人分工

| AI 适合做 | 人适合做 |
|---|---|
| 填 §4 数据契约（schema 是结构化） | 写 §1 用户故事（产品意图） |
| 列 §3 边界（checklist） | 验收 §2 GWT（业务判断） |
| 列 §5 测试场景（从 GWT 提炼） | 签字"已验收"（决策） |
| 检查 5 段齐全（自动） | 决定优先级 |

**核心原则**：**人填空白（业务决策），AI 校验完整性（缺什么提醒）**。

---

## 🎯 硬性 DOD（spec.md 完成必须全过）

- [ ] 5 段齐全（用户故事 / Requirement + Scenario / 边界 / 数据契约 / 测试场景）
- [ ] Requirement ≥ 1（每个用 SHALL 强约束）
- [ ] Scenario ≥ 3 条（happy + invalid + edge/failure 各 ≥ 1）
- [ ] 数据契约 ≥ 1 schema（Pydantic / Zod / TypeScript interface）
- [ ] 测试场景 ≥ 3 条（happy + edge + failure 各 ≥ 1）
- [ ] §0 上游引用齐全（调研 + 产品文档）
- [ ] 用户故事已验收（人签字 / 写在文档里 "已验收：<name> <date>"）

> ⚠️ 任何 1 条未满足 → spec.md 不算完成，不能进 2 步
> ⚠️ 工具校验：`python3 scripts/check-step.py spec <file>`

---

## 📚 相关文档（spec.md 是"业务契约浓缩版"，详细技术层见 2 步产物）

- `product-doc-template.md` — 上游：产品脑（人主导）
- `db-design-template.md` — **2 步技术层**：表结构 + 迁移 SQL
- `api-spec-template.md` — **2 步技术层**：接口清单 + Request/Response
- `component-spec-template.md` — **2 步技术层**：组件 Props/State 实现
- `plan-template.md` — 2 步：多方案对比 + 推荐
- `test-cases-template.md` — 4 步整合产出
- `docs/DOD.md` §三.3 — 1 步规格 DOD 完整定义

---

## 5.5 跨文档引用（必填 · 指向 2 步技术详细化）

```markdown
- 涉及 schema 变更？ → 2 步产出 db-design.md（§1-5 业务表结构 + §6-8 技术实现）
- 涉及新/改 API？   → 2 步产出 api-spec.md（§1-5 业务接口 + §6-8 技术实现）
- 涉及新组件？      → 2 步产出 component-spec.md（§1-5 业务 Props + §6-8 技术实现）
- 都不涉及？       → 2 步只产出 plan.md
```

**核心原则**：spec.md 是"业务契约"层，技术实现层（schema / API / 组件库选型）归 2 步详细化文档。
