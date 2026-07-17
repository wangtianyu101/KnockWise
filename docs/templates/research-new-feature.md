# 调研模板 · 新功能

> 触发词：`调研 新功能：<topic>` 或 `调研 设计：<topic>` 或 `调研 feature：<topic>`
> 时间预算：30-60 min
> 必填段：1, 2, 3, 4, 5（全部必填）

---

# 🔍 调研报告 · 新功能：<名字>

> 日期：YYYY-MM-DD · 调研人：<AI 名>

## 1. 任务理解（必填）

- **用户原话**: "<原话>"
- **AI 复述**: <用自己的话讲要做啥，1-2 句；如果复述不对，立刻停下等用户确认>
- **涉及模块**: [interview / learn / qa / news / obsidian / ai-push / ...]
- **估时**: ~Xh（后端 / 前端 / 测试 分开估）

## 2. 现状扫描（必填）

### 2.1 相关文件
- `backend/api/<...>.py` — <作用>
- `backend/services/<...>.py` — <作用>
- `frontend/pages/<...>.tsx` — <作用>
- `frontend/components/<...>.tsx` — <作用>

### 2.2 相关议題（来自 `docs/40-追踪/目前缺陷.md`）
- [A-1, F-3 ...]（无则写"无"）
- 如议題沉积超过 30 天未推进 → 标注 ⚠️

### 2.3 最近相关改动
```bash
git log --oneline -10 -- <相关路径>
```
- commit `abc1234`: <摘要>（日期）
- commit `def5678`: <摘要>（日期）

### 2.4 类似功能怎么实现的（必填，找 1-2 个）
- **参考 A**: `<已有功能>` — 用了什么模式 / 组件 / endpoint
- **参考 B**: `<已有功能>` — 用了什么模式 / 组件 / endpoint

## 3. 依赖发现（必填）

### 3.1 改这些文件会影响
- `<file>`: <影响什么>
- `<test>`: <影响什么>

### 3.2 需要先改的
- `<file>`: <为什么>
- `<migration>`: <为什么>

### 3.3 调用方清单（改之前必查）
- `<file>:line` — <怎么调用>
- `<file>:line` — <怎么调用>

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 已有未提交改动（`git status`） | 🟡/🔴 | 确认是不是冲突，协调其他 session |
| 类似功能已有但不一致 | 🟡 | 决定是统一还是并存 |
| 涉及 schema 变更 | 🔴 | 必走迁移流程 + 备份 |
| 涉及多个 agent / branch | 🟡 | 强调研 + 走 1.7 分支 |
| 议題沉积影响判断 | 🟡 | 必读 `目前缺陷.md` |
| 估时偏差 > 50% | 🟡 | 拆更小的 task |

## 5. 输出建议（必填）

### 5.1 推荐路径
```
0 调研（本步完成）
→ 1 规格（spec.md · 三脑交汇）
→ 2 计划（plan.md + db/api/component spec）
→ 3 拆分（tasks.md · ≤ 1h 原子任务）
→ 4 实现（TDD 循环 · 红→绿→refactor）
→ 5 验证（L3 整合 + L5 staging）
→ 6 复盘（retro.md）
```

> ⚠️ v2 变更（2026-07-02）：砍掉原"6 发布"（灰度 + 监控 + 回滚）—— PR/commit 即交付。
> v2 验证精简：原 5 层 gate → 2 段（L3 整合测试 + L5 staging 实地）· L1/L2 由 pre-commit hook 兜底 · L4 review 是活动不是步骤。
> 详见 CLAUDE.md § 一 v1 → v2 变化。

### 5.2 关键决策点（必填 ≥ 1）
- 决策 1: <用什么组件 / 库 / 模式>
- 决策 2: <要不要缓存 / 限流 / 重试>

### 5.3 元信息
- 是否需要外部评审: 是 / 否
- 是否涉及 schema 变更: 是 / 否
- 是否需要 AB 测试: 是 / 否

---

## 6. spec.md 规格写法（参考 OpenSpec · 强约束可验证）

> ⚠️ 这是给 **下一步（步 1 写 spec.md）** 用的格式。**禁止**在 spec.md 里写空话、感觉流描述。
> 强约束：每个 Requirement 必须配 ≥ 1 个 Scenario，每个 Scenario 必须能直接转为测试用例。

### 6.1 结构骨架

```markdown
### Requirement: <功能名（动词 + 名词）>
The system SHALL <单一可验证的承诺>.

#### Scenario: <场景名（happy path / 边界 / 失败）>
- **WHEN** <触发条件>
- **THEN** <预期结果 1>
- **AND** <预期结果 2>（可选）

#### Scenario: <另一场景>
- **WHEN** ...
- **THEN** ...
```

### 6.2 关键字用法

| 关键字 | 用途 | 示例 |
|---|---|---|
| **SHALL** | 强制承诺（不能用 should / may）| The system SHALL validate credentials |
| **WHEN** | 触发条件（输入/动作）| WHEN user submits valid username AND password |
| **THEN** | 预期结果（输出/状态）| THEN system returns 200 with JWT token |
| **AND** | 同一层级的并列条件或结果 | AND token expires in 24 hours |

### 6.3 正反例对比

**❌ 反例（感觉流，禁止）**：

```markdown
## 需求：用户登录
- 用户能输入用户名密码
- 失败要提示
- 成功跳到首页
```

**✅ 正例（SHALL/WHEN/THEN，可验证）**：

```markdown
### Requirement: User Authentication
The system SHALL validate user credentials and return a JWT token on success.

#### Scenario: Successful login
- **WHEN** user submits valid username AND password
- **THEN** system returns HTTP 200
- **AND** response body contains a JWT token
- **AND** token expires in 24 hours

#### Scenario: Invalid credentials
- **WHEN** user submits invalid username OR password
- **THEN** system returns HTTP 401
- **AND** error code is "AUTH_INVALID"

#### Scenario: Empty fields
- **WHEN** username OR password is empty
- **THEN** system returns HTTP 422
- **AND** error code is "VALIDATION_REQUIRED_FIELD"

#### Scenario: Rate limit exceeded
- **WHEN** user submits credentials more than 5 times in 1 minute
- **THEN** system returns HTTP 429
- **AND** response includes Retry-After header
```

### 6.4 场景覆盖清单（每个 Requirement 至少覆盖 4 类）

| 场景类型 | 必填 | 写什么 |
|---|---|---|
| Happy path | ✅ | 正常输入 → 正常输出 |
| Invalid input | ✅ | 错误/空/越界 → 错误码 |
| 边界值 | 🟡 推荐 | 最小/最大/临界值 |
| 异常路径 | 🟡 推荐 | 网络/超时/并发/权限 |

### 6.5 与 CLAUDE.md § 六 单测的对接

- 每个 Scenario 的 WHEN/THEN → **对应 1 个 pytest 用例**（happy / invalid / edge 各 1 个）
- spec.md 写完后 → 步 4 实施时**直接照 Scenario 写测试**（红→绿），不必再设计测试
- 改 spec.md → 必须同步改测试（双向同步，防止 drift）

### 6.6 来源

- 借鉴自 [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) 的 SDD（Spec-Driven Development）写法
- 原文链接：https://juejin.cn/post/7662638440001388578（Harness 企业级落地三）
- ⚠️ 我们**不装 OpenSpec**，只**白嫖写法**（避免双源真理，详见 § 0 调研决策）

---

## 自检清单（AI 调研完必过）

- [ ] 任务理解段已写且用户复述对
- [ ] 现状扫描覆盖 ≥ 3 个相关文件
- [ ] 依赖发现列出 ≥ 3 个影响点
- [ ] 风险评估 ≥ 3 条带等级
- [ ] 输出建议给完整 6 步路径
- [ ] 关键决策点 ≥ 1
- [ ] 已读 `docs/40-追踪/目前缺陷.md`
- [ ] 已跑 `git log -10` + `git status`
- [ ] 步 1 写 spec.md 时按 § 6 强制用 SHALL/WHEN/THEN 结构
