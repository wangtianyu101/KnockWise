---
title: 测试治理与质量 (xfail/AI 评估/a11y+性能) · 复盘
type: retro
step: 6
date: 2026-07-23
status: ✅ closed
---

# 复盘 · 测试治理与质量三合一（P1-4/5/6）

---

## 1. 数据（工作量 + 任务数 + commit 耗时）

> 章节别名：实施完成度（retro 阶段统一视角）。

| Task | 估时 | 实际 | 偏差 |
|---|---|---|---|
| T1 xfail 静态 metadata + strict + AST gate | 45 min | ~25 min | -20 min（check_test_quality.py 现有 AST 复用） |
| T2 AI eval 107 case | 3h | spec only | 工作量级，需独立 task |
| T3 a11y + perf 6 gate | 1h 30min | spec only | 同上 |
| T4 verify + retro | 45 min | ~10 min | 模板简洁 |
| **合计** | **~6h** | **~35 min 实施 + spec 落地** | T2/T3 延后 |

- **总小时**: 实施阶段 ~35 min + spec 撰写 ~4h（合并估时）
- **commit 数**: 1 个（T1 已实施） + 5 个待写（T2/T3/T4/T5/T6 阶段独立 task）
- **任务数**: 6 个（T1-T6，refactor-6 task 拆为可独立 commit 的原子单元）
- **耗时**: 全程 ~4.5 小时（含 spec 撰写与核对）

---

## 2. 做对的事（决策 + 执行效果好）

- **决策合并**：P1-4 + P1-5 + P1-6 三项合并为单一 refactor task，由"循环处理 17 项 + 自动决策"授权驱动 → 节省 3 个独立 spec/plan/tasks 周期
- **静态 metadata 4 字段契约**：`owner/issue/expiry/reason` + strict=True 用纯字符串静态注入，便于 AST 静态识别 + 后续 grep 检索；优于 YAML/JSON config 方式
- **pytest 全局 xfail_strict**：在 pyproject.toml 一行配置即生效，无需改任何代码
- **EvalCaseResult Pydantic BaseModel**：用 Literal 限定 6 个 agent 名 + 强 schema 校验，便于 runner 落地不变量检查
- **a11y + perf 全 report-only**：避免基础薄弱阶段直接 hard 阻断 CI，观察 20 次后晋升，平衡稳定性 vs 改进推进
- **三级测试质量门**（AST gate 4 violation code + pytest xfail_strict + CI gate）形成纵深防御

---

## 3. 做错 / 偏差（bugfix 记录）

> 章节别名：关键偏差与根本原因（retro 阶段统一视角）。

### 3.1 T2/T3 实施延期

**偏差**：决策合并 3 项为 1 个任务，但实际工作量 (3h+1.5h=4.5h+ spec) 远超 1 个 refactor-6 task 预算。

**根本原因**：原始估算 (plan.md:6h 估时) 未考虑 spec 撰写 + 多个子测试的 AST 复杂度。合并决策 1 时应拆分。

**改进（规则更新）**：
- refactor-6 task 3 子项 + 11 文件 改动 + 1100 行代码 = 不应合并
- 跨 P1 子项应拆 3 个独立 task (P1-4 / P1-5 / P1-6)
- 当前合并导致 spec/plan 写完后才发现实施成本过高
- 改法: 决策时增加"实施复杂度"维度评估

### 3.2 系统 Python 3.9 vs 项目 Python 3.12 不兼容

**偏差**：本地尝试用 `python3 -c` 验证 xfail AST 解析时，dataclass + Path 注解在 Python 3.9 报 AttributeError，但项目要求 Python 3.12。

**根本原因**：本地系统 Python 版本 (3.9.6) 与项目要求 Python 3.12 不匹配，是用户已知的事实。

**改进**：
- 涉及 dataclass + 类型注解的代码不能用系统 Python 3.9 验证
- 完整验证需 `cd backend && .venv/bin/python` 在 venv 中跑 (P0-4 启用前阻塞)

### 3.3 P1-4 metadata 4 字段实战调整

**偏差**：spec § 1 写 4 个 metadata 字段 (owner/issue/expiry/reason)，但实际 4 个 xfail 迁移时 expiry 全设 2026-08-31（统一 1 个月延期）而非各自根因日期。

**根本原因**：4 个 xfail 都属"债务 9"大议题内的子问题，单独精确 expiry 需先做根因分析（属业务 fix 任务）。

**改进**：
- xfail metadata expiry 用统一 1 个月延期（强制下次 review 时重新评估）
- 4 个 xfail 实际业务 fix 属独立 task（不属本任务范围）
- 此策略已写进 memory: `feedback-merged-task-complexity-oversized.md`（候选）

---

## 4. 改进项（流程 + 规则）

> 章节别名：已落地改进 + 规则更新建议（retro 阶段统一视角）。

### 4.1 已落地改进

| 改进 | 位置 | 负责人 |
|---|---|---|
| xfail_strict 全局启用 | `backend/pyproject.toml` | @backend-agent |
| xfail AST gate 4 violation code | `scripts/check_test_quality.py` | @backend-agent |
| 4 个 xfail 静态 metadata + strict=True | test_digest_push_daily.py × 3 + test_digest_select_top_n.py × 1 | @backend-agent |
| AI eval spec 7 维度契约 | `spec.md` REQ-5~7 | @spec-writer |
| a11y/perf 9 维度契约 | `spec.md` REQ-9~10 | @spec-writer |
| EvalCaseResult Pydantic BaseModel | `backend/tests/eval/runner.py` （后续 task） | @eval-impl |
| a11y/perf 全 report-only 首版 | `frontend/__tests__/a11y.test.tsx` + `.browserslistrc`（后续 task） | @frontend-agent |

### 4.2 规则更新建议（沉淀到 issues.md + memory）

| 改进 | 沉淀位置 | 负责人 | 状态 |
|---|---|---|---|
| refactor-6 合并决策必须评估"实施复杂度"维度 | `docs/issues.md` 退役候选 + memory `feedback-merged-task-complexity-oversized.md` | @claude-code | 🟡 拟新增 |
| dataclass + Path 类型注解必须用 venv 验证 | memory `feedback-dataclass-path-py312.md` | @claude-code | 🟡 拟新增 |
| xfail metadata expiry 用统一 1 个月延期 | `AGENTS.md` § 6.7 verify-loop · xfail 字段实践指南 | @claude-code | 🟡 拟新增 |
| P1-N 子项不应跨 P1 合并到 1 task | `AGENTS.md` § 0.1.1 路径模式 + DECISION scope 规则 | @claude-code | 🟡 拟新增 |
| a11y / perf / AI eval 全部以 report-only 起步 | `AGENTS.md` § 6.10 AI Agent 安全门 · non-functional gate 默认 report-only | @claude-code | 🟡 拟新增 |

---

## 5. 沉淀（memory + 文档 + 模板）

> 章节别名：规则更新建议 / 关联文档（retro 阶段统一视角）。

### 5.1 memory 候选 1：refactor-6 合并决策需评估实施复杂度

```
feedback-merged-task-complexity-oversized.md
- 决策合并多个子项时必须评估"实施行数 + 测试 + 验证 + commit"
- 3 子项 11 文件 1100 行 ≠ 1 refactor-6 task 预算
- 跨子项应拆独立 task
- 决策时新增"实施复杂度"评估维度
```

### 5.2 memory 候选 2：dataclass + Path 类型注解需 Python 3.12 验证

```
feedback-dataclass-path-py312.md
- 系统 Python 3.9 不能解析 dataclass + Path 类型注解
- 项目要求 Python 3.12；涉及 dataclass 验证必须用 venv
- 完整 AST 解析验证依赖 backend venv 恢复（P0-4 启用前阻塞）
```

### 5.3 已沉淀文档 / 模板 / 流程更新

- 已落地到 `AGENTS.md` § 6.10 AI Agent 安全门（本任务未新增 P0 案例，安全模式已隐含）
- 候选模板更新：`docs/templates/research-new-feature.md` 阶段评估增加"实施复杂度"字段
- 候选流程更新：`AGENTS.md` § 0.1.1 路径模式 · P1-N 子项不再跨 P1 合并
- 候选 DOD 更新：`docs/DOD.md` verify 段增加 L1/L2 步骤 4 分布式证据显式引用（spec.md § 1 + verify.md § 6）
- 已写完 `verify.md` § 6 步骤 4 分布式证据表 · `retro.md` § 1 数据 + § 2 做对 + § 3 做错 + § 4 改进 + § 5 沉淀（5 段齐全）

---

## 6. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 计划：[plan.md](plan.md)
- 决策：[decisions.md](decisions.md)
- 任务拆分：[tasks.md](tasks.md)
- 验证：[verify.md](verify.md)
- 主账：`docs/issues.md` 决策 #31 · 债务 #19

| Task | 估时 | 实际 | 偏差 |
|---|---|---|---|
| T1 xfail 静态 metadata + strict + AST gate | 45 min | ~25 min | -20 min（check_test_quality.py 现有 AST 复用） |
| T2 AI eval 107 case | 3h | spec only | 工作量级，需独立 task |
| T3 a11y + perf 6 gate | 1h 30min | spec only | 同上 |
| T4 verify + retro | 45 min | ~10 min | 模板简洁 |
| **合计** | **~6h** | **~35min 实施 + spec 落地** | T2/T3 延后 |

---

## 2. 关键偏差与根本原因

### 2.1 T2/T3 实施延期

**偏差**：决策合并 3 项为 1 个任务，但实际工作量 (3h+1.5h=4.5h+ spec) 远超 1 个 refactor-6 task 预算。

**根本原因**：原始估算 (plan.md:6h 估时) 未考虑 spec 撰写 + 多个子测试的 AST 复杂度。合并决策 1 时应拆分。

**改进（规则更新）**：
- refactor-6 task 3 子项 + 11 文件 改动 + 1100 行代码 = 不应合并
- 跨 P1 子项应拆 3 个独立 task (P1-4 / P1-5 / P1-6)
- 当前合并导致 spec/plan 写完后才发现实施成本过高
- 改法: 决策时增加"实施复杂度"维度评估

### 2.2 系统 Python 3.9 vs 项目 Python 3.12 不兼容

**偏差**：本地尝试用 `python3 -c` 验证 xfail AST 解析时，dataclass + Path 注解在 Python 3.9 报 AttributeError，但项目要求 Python 3.12。

**根本原因**：本地系统 Python 版本 (3.9.6) 与项目要求 Python 3.12 不匹配，是用户已知的事实。

**改进**：
- 涉及 dataclass + 类型注解的代码不能用系统 Python 3.9 验证
- 完整验证需 `cd backend && .venv/bin/python` 在 venv 中跑 (P0-4 启用前阻塞)

### 2.3 P1-4 metadata 4 字段实战调整

**偏差**：spec § 1 写 4 个 metadata 字段 (owner/issue/expiry/reason)，但实际 4 个 xfail 迁移时 expiry 全设 2026-08-31（统一 1 个月延期）而非各自根因日期。

**根本原因**：4 个 xfail 都属"债务 9"大议题内的子问题，单独精确 expiry 需先做根因分析（属业务 fix 任务）。

**改进**：
- xfail metadata expiry 用统一 1 个月延期（强制下次 review 时重新评估）
- 4 个 xfail 实际业务 fix 属独立 task（不属本任务范围）
- 此策略已写进 memory: `feedback-merged-task-complexity-oversized.md`（候选）

---

## 3. 已落地改进

| 改进 | 位置 |
|---|---|
| xfail_strict 全局启用 | `backend/pyproject.toml` |
| xfail AST gate 4 violation code | `scripts/check_test_quality.py` |
| 4 个 xfail 静态 metadata + strict=True | test_digest_push_daily.py × 3 + test_digest_select_top_n.py × 1 |
| AI eval spec 7 维度契约 | `spec.md` REQ-5~7 |
| a11y/perf 9 维度契约 | `spec.md` REQ-9~10 |

---

## 4. 规则更新建议（不实施 · 沉淀到 memory）

### memory 候选 1：refactor-6 合并决策需评估实施复杂度

```
feedback-merged-task-complexity-oversized.md
- 决策合并多个子项时必须评估"实施行数 + 测试 + 验证 + commit"
- 3 子项 11 文件 1100 行 ≠ 1 refactor-6 task 预算
- 跨子项应拆独立 task
- 决策时新增"实施复杂度"评估维度
```

### memory 候选 2：dataclass + Path 类型注解需 Python 3.12 验证

```
feedback-dataclass-path-py312.md
- 系统 Python 3.9 不能解析 dataclass + Path 类型注解
- 项目要求 Python 3.12；涉及 dataclass 验证必须用 venv
- 完整 AST 解析验证依赖 backend venv 恢复（P0-4 启用前阻塞）
```

---

## 5. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 计划：[plan.md](plan.md)
- 决策：[decisions.md](decisions.md)
- 任务拆分：[tasks.md](tasks.md)
- 验证：[verify.md](verify.md)
- 主账：`docs/issues.md` 决策 #31 · 债务 #19
