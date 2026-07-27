---
title: Plan · 产品基础分层 L0-L3
date: 2026-07-27
status: v1.2（基于 spec v1.2 · 4 项调研偏差修正）
type: plan
related:
  - [research.md](research.md) — 调研报告 v1
  - [spec.md](spec.md) — 业务契约 v1
  - [decisions.md](decisions.md) — 决策 1 主账
  - [docs/issues.md](../../issues.md) — 主账
  - [api-spec-template.md](../../templates/api-spec-template.md) — 2 步 API 详细化
  - [plan-template.md](../../templates/plan-template.md) — 上游模板
---

# Plan · 产品基础分层 L0-L3（重构）

> **范围**：决策 1 自动授权 · 3 子项合并（P1-7 + P1-8 + P1-9）
> **路径模式**：refactor-6（0→1→2→3→4→5→6）
> **实施阶段产物**：19 个原子任务 · 总估时 ~7h · 平均 22 min/任务
> **适用性说明**：
> - `product-doc.md`：**N/A**（refactor-6 路径不写 product-doc · 按 product-doc-template § 触发条件）
> - `design-spec.md`：**N/A**（无 UI 组件 · P1-9 L1 平台层 = 后端基础设施 + 模板 checker · 不涉及页面 / 组件）

---

## 1. 推荐方案

**推荐**: 方案 A · 模板加段 + 独立字典文件 + 扩展 check-tasks

```markdown
### 推荐方案
- **方案**：A · 模板加段 + 独立字典文件 + 扩展 check-tasks
- **理由**：
  1. 决策 1 明确"模板最小 diff" → 方案 A 改 3 个模板段 / 方案 B 改 5+ 段
  2. 独立字典文件 `docs/metrics/<id>.yaml` 易维护 + 易 git diff + 不污染 product-doc frontmatter
  3. 复用 v39 pre-commit DOD checker 基础设施（`scripts/check-step.py tasks` 已存在）· 避免新建独立 § 9 checker
  4. 风险等级 🟡（与方案 B 同级）· 工作量比 B 少 2h
- **工作量**：~7 小时（19 个原子任务）
- **风险**：🟡（中风险 · 已通过 SCN-P1.8.6 + TC-6 等硬阻断）
```

---

## 2. 方案对比（3 个）

### 方案 A：原模板加段 + 独立字典文件 + 扩展 check-tasks（推荐）

```markdown
- **思路**：
  - product-doc-template.md § 0/§ 2/§ 5 加 4 段（决策 1 已锁定）
  - 新建 `docs/metrics/<metric_id>.yaml` 独立文件
  - 扩展 `scripts/check-step.py tasks` 加 § 9 校验（不新建独立 checker）
  - 复用 v39 pre-commit 基础设施
- **优点**：
  - 模板最小 diff（决策 1 强约束）
  - 字典独立文件 · 8 必填字段易扩展
  - 复用现有 checker · 不引入新基础设施
- **缺点**：
  - 3 个文件改动跨模板/字典存储/checker
- **风险等级**：🟡
- **工作量**：~7h（19 任务）
- **兼容性**：✅ v1 → v2 兼容（`legacy_skeleton: true`）
- **测试影响**：扩展现有 `tests/test_check_*.py` · 不需新建测试基础设施
```

### 方案 B：独立 schema 文件 + 独立字典文件 + 独立 § 9 checker

```markdown
- **思路**：
  - 新建 `docs/schemas/product-baseline.schema.json` 独立 JSON Schema
  - 新建 `docs/schemas/metric-dict.schema.json` 独立 JSON Schema
  - 新建 `scripts/check-section9.py` 独立 § 9 checker
  - product-doc / tasks 模板只引用 schema 不内嵌
- **优点**：
  - 完全独立 · 不污染模板
  - JSON Schema 标准化
- **缺点**：
  - 3 个新文件 · 跨治理面广
  - 模板"只引用"形式 = 维护双份（模板 + schema）
  - 回归测试覆盖 3 个新文件 + 2 个修改模板
- **风险等级**：🟡
- **工作量**：~9h（22 任务）
- **兼容性**：⚠️ 需迁移（v1 → v2）
- **测试影响**：新建 3 个测试文件 + 2 个新 schema 验证测试
```

### 方案 C：JSON Schema 外部 + 内嵌字典 + 嵌入 check-tasks 子模块

```markdown
- **思路**：
  - 字典内嵌在 product-doc frontmatter（不独立文件）
  - check-tasks 拆子模块 `scripts/check_tasks/section9.py`
  - JSON Schema 校验 product_baseline
- **优点**：
  - 字典与 product-doc 同步（无漂移）
- **缺点**：
  - JSON Schema 表达 Pydantic 复杂模型（Union / Literal / 嵌套）能力弱
  - 需写自定义 validator 补足
  - 字典与 product-doc 强耦合 · 大字典导致 frontmatter 臃肿
- **风险等级**：🔴
- **工作量**：~10h（25 任务）
- **兼容性**：⚠️ 需迁移 + 工具链变化
- **测试影响**：JSON Schema + 自定义 validator 双重测试
```

---

## 3. 风险评估

| # | 风险 | 等级 | 缓解措施 | 关联 SCN/TC |
|---|---|---|---|---|
| 1 | 5 项 AI 推送产品指标（40%/60%/10%/5%/30%）阈值未验证锁死 | 🔴 P0 | SCN-P1.8.6 硬阻断 L2 升级；5 项标 L1 探索性 | SCN-P1.8.6 |
| 2 | T19 dead code 复制（counter.inc 调了但不真增） | 🟡 | TC-6 counter 真增断言（不只 mock hasattr）+ TC-7 § 9 缺段报错 | TC-6, TC-7 |
| 3 | 单人项目承担过重（所有功能都要 baseline 字段） | 🟡 | L0 不要求 · L1 最小 · L2/L3 才强制 8 必填 | SCN-P1.8.5 |
| 4 | trace_id race fix 引入新 bug | 🟡 | TC-5 100 并发隔离（asyncio.gather 真跑）+ L5 staging 实测 | TC-5 |
| 5 | product-doc 旧实例 v1 → v2 迁移混乱 | 🟡 | `legacy_skeleton: true` 标记豁免（spec §4.1） | spec §4.1 |
| 6 | metrics endpoint 暴露公网泄露内部 counter | 🟡 | SCN-P1.9.7 验证仅 127.0.0.1 | SCN-P1.9.7 |
| 7 | check-tasks 扩展破坏现有 0 violations（v39 治理回归 84/84） | 🟡 | 改前跑 `python3 scripts/check-step.py tasks` 确认基线 0 violation · 改后必须仍 0 violation | v39 决策 25/26 |
| 8 | Goodhart 风险（指标被优化而非真实价值） | 🟡 | 配定性证据 · 指标变更需决策日志（spec §3.6） | spec §3.6 |
| 9 | audit 9 任务 verify.md 缺失未补登记 | 🟡 | 实施时回写 issues.md 决策段（spec §0 引用） | spec §0 |

**风险等级定义**：
- 🔴 高风险：可能导致延期 / 数据丢失 / 用户影响
- 🟡 中风险：可控，但需要关注

---

## 4. 决策点（5 个）

### 决策 1：product-doc 模板扩展形态

- **选择**：✅ 方案 A · 原模板加 4 段（§ 0 / § 2 / § 5 + 新建 schema 段）
- **理由**：
  1. 决策 1 明确"模板最小 diff" · 方案 B 改 5+ 段违背
  2. 旧 product-doc 实例加 `legacy_skeleton: true` 标记豁免（spec §4.1）
  3. 模板直接可见 · AI 写 spec 时不会漏字段
- **替代方案**：
  - 方案 B（独立 schema 文件）：改动面大，违背最小 diff · ❌
  - 方案 C（JSON Schema 外部）：表达 Pydantic 复杂模型能力弱 · ❌

### 决策 2：指标字典存储

- **选择**：✅ 方案 A · 独立 `docs/metrics/<metric_id>.yaml` 文件
- **理由**：
  1. 8 必填 + 4 可选字段多 · 内嵌 product-doc frontmatter 臃肿
  2. 独立文件 = 易维护 + 易 git diff + 易追溯
  3. 跨 product-doc 复用（一个 metric 可能被多个 product-doc 引用）
- **替代方案**：
  - 内嵌 product-doc frontmatter：污染 + 臃肿 · ❌
  - 单一 `index.json`：不易追溯 + 不易 git diff · ❌

### 决策 3：tasks § 9 校验集成

- **选择**：✅ 方案 A · 扩展 `scripts/check-step.py tasks`
- **理由**：
  1. 复用 v39 pre-commit DOD checker 基础设施（commit `d91fdef`+`ee6da13`+`9841c38`）
  2. 不引入新脚本 = 治理面不增加
  3. 现有 `check-step.py tasks` 已支持多规则扩展
- **替代方案**：
  - 新建独立 `check-section9.py`：重复基础设施 · ❌
  - 嵌入子模块 `check_tasks/section9.py`：过度抽象 · ❌

### 决策 4：logger trace_id 字段实现（v1.1 修正 · 调研偏差）

- **选择**：✅ `contextvars.ContextVar` + `logging.Filter` 注入 `backend/utils/logger.py`（v1.1 修正：实施对象为 `logger.py` 扩展而非新建 `trace_id.py`）
- **理由**：
  1. 实施前探查发现 `trace_id.py` 不存在（4 Agent 调研盲点）· 修正为扩展现有 `logger.py`
  2. Python stdlib · 无第三方依赖
  3. asyncio 天然隔离（asyncio.Task 各自 context）· 同步代码也支持
  4. `logging.Filter` 是 stdlib 标准做法 · 与 logger startup 接管天然集成
- **替代方案**：
  - 新建 `backend/utils/trace_id.py`：v1.0 调研假设 · v1.1 探查发现文件不存在 · ❌
  - `asyncio.current_task().get_name()`：不跨同步代码 · ❌
  - middleware 注入：不够灵活 · ❌

### 决策 5：metrics endpoint 暴露范围（spec 已锁）

- **选择**：✅ 仅 127.0.0.1（spec SCN-P1.9.7）
- **理由**：
  1. 内部基础设施 · 不暴露公网
  2. 减少攻击面 · 无需 token 复杂度
- **替代方案**：
  - 内部 token：增加复杂度 · ❌
  - 不暴露（仅日志）：失去观察口 · ❌

---

## 5. 任务拆分建议（19 个原子任务 · 总估时 ~7h）

> 任务粒度约束：每个 ≤ 1h AI 工作量 · 每个 1 commit · 每个 ≥ 1 TC

### P1-7 模板 + checker（决策 1 + 决策 3）

| T# | 任务 | 文件 | 测试 | 依赖 | 估时 | 决策 |
|---|---|---|---|---|---|---|
| T1 | product-doc-template.md § 0 加 product_baseline 字段说明 | `docs/templates/product-doc-template.md` | — | — | 20 min | D1 |
| T2 | product-doc-template.md § 2 角色表加 4 列（频次/设备/网络/语种） | 同上 | — | T1 | 15 min | D1 |
| T3 | product-doc-template.md § 5 成功指标加 baseline_value 列 | 同上 | — | T2 | 15 min | D1 |
| T4 | 新建 `scripts/check-product-doc.py` 含 4 schema | `scripts/check-product-doc.py` | TC-1, TC-2 | T1-T3 | 45 min | D3 |
| T5 | 写 `tests/test_check_product_doc.py` 含 TC-1/TC-2 | `tests/test_check_product_doc.py` | TC-1, TC-2 | T4 | 30 min | D3 |

**P1-7 小计**：~2h（5 任务）

### P1-8 字典 + checker（决策 2）

| T# | 任务 | 文件 | 测试 | 依赖 | 估时 | 决策 |
|---|---|---|---|---|---|---|
| T6 | 新建 `docs/metrics/` 目录 + 5 项 AI 推送指标 L1 字典 | `docs/metrics/{push_open_rate,push_read_rate,...}.yaml` | — | T4 | 30 min | D2 |
| T7 | 新建 `scripts/check_metric_dict.py` 含 MetricDict schema | `scripts/check_metric_dict.py` | TC-3, TC-4, TC-10 | T6 | 45 min | D3 |
| T8 | 写 `tests/test_check_metric_dict.py` 含 TC-3/TC-4/TC-10 | `tests/test_check_metric_dict.py` | TC-3, TC-4, TC-10 | T7 | 45 min | D3 |

**P1-8 小计**：~2h（3 任务）

### P1-9 L1 平台层（决策 4 + 决策 5）

| T# | 任务 | 文件 | 测试 | 依赖 | 估时 | 决策 |
|---|---|---|---|---|---|---|
| T9 | `backend/utils/logger.py` 加 `TraceIdFilter` + `trace_id_var` ContextVar（v1.1 修正） | `backend/utils/logger.py` | TC-5 | — | 30 min | D4 |
| T10 | 写 `tests/test_logger_trace_id_field.py` 含 TC-5 100 并发（v1.1 修正） | `tests/test_logger_trace_id_field.py` | TC-5 | T9 | 30 min | D4 |
| T11 | FastAPI startup 接管 `knockwise.*` logger | `backend/main.py` + `backend/utils/logger.py` | TC-9 | T9 | 30 min | — |
| T12 | 写 `tests/test_logger_startup.py` 含 TC-9 | `tests/test_logger_startup.py` | TC-9 | T11 | 30 min | — |
| T13 | 新建 `GET /api/digest/metrics` endpoint（仅 127.0.0.1） | `backend/api/digest_metrics.py` | TC-8 | T9 | 30 min | D5 |（**v1.2 修正**：4 counter 键 = `push_total / push_failed / fetch_failures / rsshub_routes_broken` · 与 `backend/utils/metrics.py:32-37` 一致）|
| T14 | 写 `tests/test_metrics_endpoint.py` 含 TC-8 | `tests/test_metrics_endpoint.py` | TC-8 | T13 | 30 min | — |

**P1-9 L1 小计**：~3h（6 任务）

### P1-9 L2 接入层 + tasks § 9

| T# | 任务 | 文件 | 测试 | 依赖 | 估时 | 决策 |
|---|---|---|---|---|---|---|
| T15 | 在 `tasks-template.md` 加 § 9 埋点挂载点段 | `docs/templates/tasks-template.md` | — | T1-T3 | 20 min | D1 |
| T16 | 扩展 `scripts/check-step.py tasks` 加 § 9 校验 | `scripts/check-step.py` | TC-7 | T15 | 30 min | D3 |
| T17 | 写 `tests/test_check_tasks_template.py` 含 TC-7 | `tests/test_check_tasks_template.py` | TC-7 | T16 | 30 min | — |

**P1-9 L2 小计**：~1.5h（3 任务）

### 集成 + 治理回归

| T# | 任务 | 文件 | 测试 | 依赖 | 估时 | 决策 |
|---|---|---|---|---|---|---|
| T18 | 在 `.pre-commit-config.yaml` 注册 2 个 checker（check-product-doc + check-metric-dict） | `.pre-commit-config.yaml` | — | T4, T7, T16 | 15 min | — |
| T19 | L5 staging 端到端验证（启动服务 + 跑全套 + counter 真增） | `docs/tasks/.../verify.md` | TC-5/6/8/9 | T1-T18 | 30 min | — |

**集成小计**：~45min（2 任务）

### 总估时

- T1-T5: ~2h
- T6-T8: ~2h
- T9-T14: ~3h
- T15-T17: ~1.5h
- T18-T19: ~45min
- **总估时**: ~7h
- **任务数**: 19
- **平均**: 22 min/任务
- **约束**: 全部 ≤ 1h · 全部 1 commit · 全部 ≥ 1 TC

---

## 6. 依赖图

```
T1 → T2 → T3 ─┐
              ├─→ T4 → T5
              │
              └─→ T15 → T16 → T17

T9 → T10
T9 → T11 → T12
T9 → T13 → T14

T4 → T6 → T7 → T8
T16 → T18

T1-T18 → T19（L5 staging 验证）
```

**关键路径**：`T1 → T4 → T6 → T7 → T16 → T18 → T19`（最长 · ~3h）
**可并行段**：T9-T14（trace_id + logger + metrics endpoint 三个组件互不依赖 · 但需串行 commit）

---

## 7. 路径建议

```
0 调研 ✅ → 1 规格 ✅（spec v1）→ 2 计划 ✅（plan v1 · 本步）→ 3 拆分（tasks.md）
                                                                    ↓
                                                          4 实现（TDD + L1/L2/L4 + commit）
                                                                    ↓
                                                          5 验证（L3 整合 + L5 staging · verify.md）
                                                                    ↓
                                                          6 复盘（retro.md + AGENTS/模板/memory 更新）
```

**下一步**：3 步写 `tasks.md`（按 plan §5 拆 19 任务 + 添加 traceability matrix + 实施顺序 · 估时偏差 ≤ 30% 闭环）。

---

## 🎯 硬性 DOD（plan.md 完成必须全过）

- [x] 方案 ≥ 2 个（A / B / C）
- [x] 推荐方案明确（A · 单一推荐 · 给出 4 条具体理由）
- [x] 风险点带等级（🔴 × 1 + 🟡 × 8）+ 缓解措施
- [x] 决策点 ≥ 1（5 个 · 决策 4/5 spec 已锁）
- [x] 引用完整（research.md v1 + spec.md v1 + decisions.md 决策 1 + issues.md 主账）
- [ ] 用户验收 · 等用户签字（"已验收：<name> <date>"）

> ⚠️ 工具校验：`python3 scripts/check-step.py plan docs/tasks/2026-07-23-refactor-product-foundation/plan.md`
> ⚠️ 任何 1 条未满足 → plan.md 不算完成 · 不能进 3 步

---

## 落地追踪

| 决策/Requirement | spec 状态 | plan 状态 | 下一步 |
|---|---|---|---|
| 决策 1 P1-7 + P1-8 + P1-9 合并 | ✅ spec v1.1 完成 | ✅ plan v1.1 完成 | 用户验收 → 3 步 tasks.md |
| 决策 1 5 项 AI 推送指标 | spec 范围内（SCN-P1.8.6 硬阻断）| plan §3 风险 #1 缓解已锁 | 实施时 T6 标 L1 |
| 决策 1 logger trace_id 字段（v1.1 修正）| spec § 4.4 v1.1（logger trace_id 字段契约）| plan §4 决策 4 v1.1 | 实施 T9-T10（扩展 logger.py 而非新建 trace_id.py）|
| 决策 1 audit verify.md 缺失 | spec §0 已引用 issues.md | plan §3 风险 #9 缓解 | 实施时回写 issues.md 决策段 |
| 决策 1 模板最小 diff | spec §4.1 已锁字段 | plan §4 决策 1 已选 A | 实施 T1-T3 |
