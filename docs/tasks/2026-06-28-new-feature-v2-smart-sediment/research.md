# 🔍 调研报告 · 新功能：V2 智能沉淀层

> 日期：2026-06-28 · 调研人：Claude (MiniMax-M3)
> 议題编号：T-2026-06-28-01
> 路径模式: full-7（V2 跨 3 service + 6 端点 + 3 UI 改造，走完整 7 步流程）
> 上游：V1 收尾报告 [`docs/tasks/2026-06-27-v1-closure/closure.md`](../2026-06-27-v1-closure/closure.md)

---

## 1. 任务理解（必填）

- **用户原话**: "你列一下V2都需要做什么" / "调研 新功能 先整理V2调研文档吧"
- **AI 复述**: 实现 V2 智能沉淀层 = 3 个 service（SummaryService / ProfileSettlementService / ObsidianSedimentService），让用户答完题/面完试后画像自动更新、AI 摘要生成、Obsidian 自动写笔记，**跑通"输入→沉淀→回流"闭环**。
- **涉及模块**:
  - `interview`（触发画像更新）
  - `learn`（触发画像更新 + 触发摘要生成）
  - `obsidian`（沉淀文件写入）
  - `profile`（被 3 个 service 更新）
  - `dashboard`（展示新数据）
- **估时**: ~6-8h
  - 后端 3 service: 4-5h
  - 前端 UI 改造: 1-2h
  - 测试 + 文档: 1h

---

## 2. 现状扫描（必填）

### 2.1 相关文件

| 文件 | 当前状态 | V2 改动 |
|---|---|---|
| `backend/services/profile_settlement_service.py` | ❌ 不存在 | 🆕 新建（4 方法） |
| `backend/services/summary_service.py` | ❌ 不存在 | 🆕 新建（5 方法） |
| `backend/services/obsidian_sediment_service.py` | ❌ 不存在 | 🆕 新建（5 方法） |
| `backend/services/learning_progress_service.py` | ✅ 在 | 改 `upsert_progress` 末尾加 settlement 触发 |
| `backend/api/interview.py` | ✅ 在（803 行） | 改 `complete` 端点末尾加 settlement 触发 |
| `backend/api/learn.py` | ✅ 在 | 改 `answer` 端点末尾加 settlement 触发 + 加 6 个新端点 |
| `backend/models/__init__.py` Profile | ✅ 字段已扩 | 不动（`weak_topics` / `mastered_topics` / `learning_trajectory` / `last_active_at` 已在） |
| `backend/models/__init__.py` MonthlyReport | ✅ 表已建 | 不动 |
| `backend/services/obsidian_service.py` | ✅ 94% 覆盖 | 改：增加 `learning/` 路径写入支持 |
| `frontend/pages/profile.tsx` | ✅ 在 | 改：接 `weak_topics` / `mastered_topics` 数据 |
| `frontend/pages/dashboard.tsx` | ✅ 在 | 改：顶部加"今日学习总结"卡片 |
| `frontend/pages/knowledge.tsx` | ✅ 在 | 改：加"最近学习沉淀"卡片 |
| `docs/tasks/2026-06-22-new-feature-question-bank/technical-spec.md` | ✅ 在（1535 行） | 改：标 V2 service ✅，更新状态 |

### 2.2 相关议題（来自 `docs/issues.md`）

- **议题 A**（LangGraph StateGraph 未用）— 与 V2 无关，不影响
- **议题 B**（`interview.py` 803 行拆分）— V2 会让 interview.py 加 1-2 个触发点，可顺手拆；但不阻塞
- **议题 C**（语音架构 3 套并存）— 与 V2 无关
- **议题 D**（Schema 扩字段）— V2 不需要新字段（Profile 4 字段已扩）
- **议题 E**（AI 推送模块）— V2 不动
- **议题 F**（实时语音实施）— V2 不动
- ⚠️ 议題 B 沉积超过 30 天，建议 V2 实施时一起拆 interview.py

### 2.3 最近相关改动（git log -10）

```
395a2d9 docs(templates): 7 步流程配套模板
70e8816 docs(v1-closure): 收尾 V1
5c2fe38 docs+infra: 补遗漏文件（README / DOD / 4 个新模板 / check-step.py）
ffbe581 docs: 补测试调研报告 + 复盘
6222a36 test(services): obsidian/news/seed/archive 测试覆盖 70% → 100%
fd95a31 test(services): 6 核心 service 测试覆盖 12% → 99%
7bc67ff test(infra): 共享 conftest.py + pytest-asyncio + pre-commit 升级
e4bcdaa fix(services): study_plan_service.py 缺 Question import
2311eba infra: 一键启停脚本 + CLAUDE.md § 七
be7ba47 docs: 4 层分类重构为按任务 + 全局汇总
```

V2 实施会用到：
- ✅ `conftest.py`（已有 `mock_db` / `mock_cache` / `mock_llm` 共享 fixture）
- ✅ `mock_llm` fixture（SummaryService 调 LLM 用）
- ✅ `services/obsidian_service.py` 测试模式（ObsidianSedimentService 沿用）
- ✅ `pytest-asyncio` 已配 auto 模式

### 2.4 类似功能怎么实现的（找 1-2 个参考）

- **参考 A: `services/learning_progress_service.py:upsert_progress`** — 已经是"调 SM-2 + 写 log + invalidate cache"的多步编排。V2 的 `settle_after_practice` 沿用此模式：调计算 + 更新 + 触发下游。
- **参考 B: `services/qa_service.py:chat_qa`** — "DB 查询 + LLM 调用 + 状态写入"的模式。V2 的 SummaryService.daily 沿用此模式：DB 聚合数据 + LLM 生成 narrative + 落库。

---

## 3. 依赖发现（必填）

### 3.1 改这些文件会影响

| 文件 | 影响 |
|---|---|
| `backend/api/interview.py:complete` | 加 1 行 settlement 触发；不影响现有 803 行业务（议題 B 的 1 个补充点） |
| `backend/api/learn.py:answer` | 加 1 行 settlement 触发；不影响现有 20+ 端点 |
| `backend/services/learning_progress_service.py:upsert_progress` | 末尾加 settlement；现有 SM-2 逻辑不变 |
| `frontend/pages/profile.tsx` | 接数据 + 改样式；不影响其他 profile 端点 |
| `frontend/pages/dashboard.tsx` | 加 1 卡片；不影响 dashboard 现有数据 |

### 3.2 需要先改的

- 无（所有 schema 已就位：Profile 4 字段、monthly_reports 表、questions 等已建）
- 无需 Alembic 迁移（V1 没用 Alembic，V2 也不引入）
- 无需新增依赖包（`langchain_openai` / `httpx` / `pydantic-settings` 已在）

### 3.3 调用方清单（改之前必查）

- `api/interview.py` complete 端点 — 改前查：是否有 E2E 测试依赖此端点状态？答：是（11 步 e2e），但只测状态码，不影响
- `api/learn.py` answer 端点 — 改前查：被 `learning_progress_service.upsert_progress` 调；需循环检查防 recursion。答：不会，settlement 写在 service 内，service 自己调 service 是允许的
- `obsidian_service.VAULT_ROOT = Path.home() / "Obsidian" / "coding"` — V2 沿用同一路径；无需新设
- `models.MonthlyReport.summary_stats` 字段 — JSON 格式；新 service 写入需对齐 schema

---

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| **LLM 调用成本不可控**（每次 settlement 触发都调） | 🔴 | 加 Redis 缓存（profile:{user_id} TTL 1h）+ 批量触发（同一用户 1h 内多次答题只算 1 次） |
| **Obsidian vault 不存在**（开发机没 Obsidian） | 🟡 | `_write` 写失败返回 None + log warning，不抛异常；`is_vault_exists()` 启动时检查 |
| **3 个 service 循环依赖**（summary → settlement → obsidian → summary） | 🟡 | 用 `triggered_by` 参数明确方向；最多 1 层嵌套（summary 调 obsidian，obsidian 不调 summary） |
| **已有未提交改动** | 🟢 | git status 干净（最近 10 commit 都已落地） |
| **议題 B（interview.py 803 行）影响判断** | 🟡 | 顺手拆 1-2 个触发函数到 `interview_settlement.py`，不阻塞但减小风险 |
| **估时偏差 > 50%**（6-8h 估时偏乐观） | 🟡 | 拆 5 个子任务（V2.1-V2.5），每阶段 1-2h，可中断 |
| **触发 settlement 失败导致用户行为不可见** | 🟡 | settlement 失败时 return 错误 + 写 log，但**不**阻塞原业务（答完题照样返回结果） |
| **Profile 字段被并发更新覆盖** | 🟡 | 用 `SELECT FOR UPDATE` 或乐观锁（updated_at 比对） |

---

## 5. 输出建议（必填）

### 5.1 推荐路径（按 6 步流程 + 7 步 DOD）

```
0 调研（本文件）✅
→ 1 规格（spec.md）        — 1-2h
→ 2 计划（plan.md）        — 0.5h
→ 3 拆分（tasks.md）       — 0.5h
→ 4 实现（V2.1-V2.5）      — 4-5h
→ 5 验证（5 层 gate）       — 1h
→ 6 发布（V2 整体完成报告） — 0.5h
→ 7 复盘（retro.md）        — 0.5h
```

### 5.2 实施分批（V2.1-V2.5）

| 子任务 | 内容 | 工时 | 完成标志 |
|---|---|---|---|
| **V2.1** | ProfileSettlementService + 触发点 | 2-3h | 答完题 → `weak_topics` 出现新项 |
| **V2.2** | ObsidianSedimentService | 1-2h | 答完题 → `~/Obsidian/coding/learning/YYYY-MM-DD.md` 出现 |
| **V2.3** | SummaryService + LLM 模板 | 2-3h | Dashboard 顶部"今日学习总结"卡片出现 |
| **V2.4** | 前端 UI 改造（3 处） | 1-2h | 用户能看到所有"沉淀"成果 |
| **V2.5** | 测试 + 文档收尾 | 1h | pytest 全绿，DOD ✅ |

### 5.3 关键决策点（≥ 1）

- **决策 1: LLM 调用策略** → A. **缓存 + 批量触发**（省成本） B. 每次都调（新鲜） → **推荐 A**
- **决策 2: Obsidian 写回时机** → A. **立即写**（用户答完题 1s 内看到 Obsidian 变化） B. 批量（每小时） → **推荐 A**（与"沉淀"语义对齐）
- **决策 3: 触发点位置** → A. **在 service 内调 settlement**（集中） B. 在 API endpoint 调（分散） → **推荐 A**（与现有 `upsert_from_interview` 模式一致）
- **决策 4: 是否拆 `interview.py` 803 行** → A. 顺手拆 B. 留给议題 B → **推荐 A**（V2 加触发点会再加 ~30 行）
- **决策 5: V2 是单 PR 还是分 PR** → A. **分 PR**（V2.1 / V2.2 / V2.3 各 1 PR） B. 1 PR → **推荐 A**（回滚粒度小）

### 5.4 元信息

- 是否需要外部评审: 否（3 个 service 内部功能）
- 是否涉及 schema 变更: 否（Profile 4 字段 + monthly_reports 表 V1 已就位）
- 是否需要 AB 测试: 否（无对照组需求）
- 是否需要用户确认: **是**（决策 1-5 需用户拍板再实施）

---

## 6. 自检清单（AI 调研完必过）

- [x] 任务理解段已写且用户复述对（V1 收尾报告已确认 V2 范围）
- [x] 现状扫描覆盖 ≥ 3 个相关文件（12 个文件已列）
- [x] 依赖发现列出 ≥ 3 个影响点（5 个调用方已查）
- [x] 风险评估 ≥ 3 条带等级（8 条）
- [x] 输出建议给完整 7 步路径
- [x] 关键决策点 ≥ 1（给了 5 个）
- [x] 已读 `docs/issues.md`（议題 A-F 全过）
- [x] 已跑 `git log -10` + `git status`（working tree clean）

---

## 📎 证据清单

- [V1 收尾报告 `docs/tasks/2026-06-27-v1-closure/closure.md`](../2026-06-27-v1-closure/closure.md) — V1 状态 + 3 个缺失 service
- [Technical Spec § 5.4/5.5/5.6 `docs/tasks/2026-06-22-new-feature-question-bank/technical-spec.md`](../2026-06-22-new-feature-question-bank/technical-spec.md) — 3 个 service 方法签名
- [Profile 模型 `backend/models/__init__.py:Profile`] — 4 字段已扩
- [MonthlyReport 模型 `backend/models/__init__.py:MonthlyReport`] — summary_stats 字段已建
- [`backend/services/obsidian_service.py`] — VAULT_ROOT 路径（`Path.home() / "Obsidian" / "coding"`）
- [`backend/services/learning_progress_service.py:upsert_progress`] — 参考 A：settlement 编排模式
- [`backend/services/qa_service.py:chat_qa`] — 参考 B：DB 聚合 + LLM 调用 + 落库
- [`tests/conftest.py`] — mock_db / mock_cache / mock_llm 共享 fixture
- [`docs/issues.md`] — 议題 A-F 状态
- [git log 10 个 commit] — V1 + 测试 + 文档 全部落地

---

## 7. 立即行动（等用户确认后）

1. **等用户拍板决策 1-5**（特别是 1 LLM 缓存策略、5 分 PR 节奏）
2. **建 spec.md**（按 spec-template 模板）
3. **建 plan.md**（按 plan-template 模板）
4. **建 tasks.md**（5 个子任务，按 tasks-template 模板）
5. **写代码 + 测试**（V2.1 优先）

---

## 8. 给用户的简短提示

调研完成。建议下一步：
- 你说"V2 进" → 我建 spec/plan/tasks
- 你有不同想法（比如"只做 V2.1 不做 V2.3"）→ 改调研结论再进
- 你想看更细节的某一块（比如 LLM prompt 模板设计）→ 我加详细段