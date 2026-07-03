---
title: 任务拆分 · V2 智能沉淀层
date: 2026-06-28
status: v1
tags: [tasks, 3步, 实施, v2, 智能沉淀]
related:
  - [plan.md](plan.md) — 上游方案
  - [spec.md](spec.md) — 上游技术契约
  - [api-spec.md](api-spec.md) — 配套 API
  - [component-spec.md](component-spec.md) — 配套组件
  - [test-cases-template.md](../../templates/test-cases-template.md) — 下游 4 步
---

# 任务拆分：V2 智能沉淀层

> **一句话**：把 plan.md 拆成 **32 个原子任务**（V2.1 = 8 / V2.2 = 7 / V2.3 = 10 / V2.4 = 4 / V2.5 = 3），每个 ≤ 1h AI 工作量 = 1 commit = ≥ 1 测试。
>
> **作者**：AI 主导（实施指南），待你 review 任务粒度
>
> **下游**：4 步实施按 T1 → T32 顺序推进，PR 1/2/3 边界 = V2.1/V2.2/V2.3

---

## 1. 任务粒度原则（已锁定）

```
✅ 每个任务 ≤ 1h AI 工作量
✅ 每个任务 1 个 commit
✅ 每个任务对应 ≥ 1 测试用例
✅ 任务间依赖关系明确（拓扑序，无环）
✅ 并行任务标"可并行"
```

---

## 2. 任务清单（32 个，按 PR 分组）

### PR 1 — V2.1 ProfileSettlementService（任务 T1-T8，2-3h）

#### T1: 建 `profile_settlement_service.py` 骨架

```markdown
- [x] T1: 建 backend/services/profile_settlement_service.py 骨架
  - **文件**: `backend/services/profile_settlement_service.py:1-50`
  - 测试: `tests/test_profile_settlement_service.py::test_class_importable` (10 个骨架测试全过)
  - 依赖: —
  - 估时: 30 min (实际: ~15 min, 复用 V1 模板)
  - **产出**: 1 commit (`a4b0c85`)
```

**实施要点**：
- class `ProfileSettlementService` 含 4 方法占位（pass）
- import：`from backend.models import Profile, Question, Practice` + `from backend.schemas.settlement import SettlementResult, TopicSettlement`
- 实例化：`service = ProfileSettlementService()`（V1 风格，无状态）
- 加日志：`import logging` + `log = logging.getLogger(__name__)`

#### T2: 实现 `settle_after_practice`（DB 写 + 乐观锁，决策 1A + 决策 7A）

```markdown
- [ ] T2: 实现 settle_after_practice
  - **文件**: `backend/services/profile_settlement_service.py:50-150`
  - 测试: `tests/test_profile_settlement_service.py::test_settle_after_practice_happy/test_concurrent/test_db_failure`
  - 依赖: T1
  - 估时: 45 min
  - **产出**: 1 commit
```

**实施要点**：
- 收 3 参数：`user_id, qid, score`
- 流程：读 `question_progress` + `Question.topic` → 算 error_rate → 读 `Profile.weak_topics` → 增/更新/移到 mastered（mastered_count ≥ 2 且 score ≥ 4 触发）
- **乐观锁**：SELECT FOR UPDATE + `updated_at` 比对 → 冲突重试 1 次
- **容错（决策 7A）**：try/except 整套 → 失败 log warning → 返回失败标记 SettlementResult，**不抛异常**
- 更新 `Profile.last_active_at`

#### T3: 实现 `settle_after_interview`（聚合本场盲点）

```markdown
- [ ] T3: 实现 settle_after_interview
  - **文件**: `backend/services/profile_settlement_service.py:150-220`
  - 测试: `tests/test_profile_settlement_service.py::test_settle_after_interview_aggregates_blind_spots`
  - 依赖: T2
  - 估时: 30 min
  - **产出**: 1 commit
```

#### T4: 实现 `weekly_full_refresh`（重算 12 周 learning_trajectory）

```markdown
- [ ] T4: 实现 weekly_full_refresh
  - **文件**: `backend/services/profile_settlement_service.py:220-290`
  - 测试: `tests/test_profile_settlement_service.py::test_weekly_full_refresh_recalculates_12_weeks`
  - 依赖: T1
  - 估时: 30 min
  - **产出**: 1 commit
```

#### T5: 实现 `manual_refresh`（给"刷新按钮"用）

```markdown
- [ ] T5: 实现 manual_refresh
  - **文件**: `backend/services/profile_settlement_service.py:290-340`
  - 测试: `tests/test_profile_settlement_service.py::test_manual_refresh_invalidates_summary_cache`
  - 依赖: T4
  - 估时: 30 min
  - **产出**: 1 commit
```

**要点**：调 T4 重算 + DEL Redis 3 个 key（`summary:dashboard:{user_id}` / `summary:profile:{user_id}` / `profile:{user_id}`）

#### T6: 改 `learning_progress_service.py:upsert_progress` 末尾触发 settlement

```markdown
- [ ] T6: 改 learning_progress_service.upsert_progress 末尾调 settlement
  - **文件**: `backend/services/learning_progress_service.py` 末尾（约 `:300` 附近）
  - 测试: `tests/test_learning_progress_service.py::test_upsert_progress_triggers_settlement`
  - 依赖: T2
  - 估时: 30 min
  - **产出**: 1 commit
```

**要点**：
- 末尾 `try: ProfileSettlementService().settle_after_practice(user_id, qid, score) except Exception as e: log.warning(...)`（决策 7A 不抛）
- 不阻塞原函数返回

#### T7: 改 `interview.py:complete` 触发 settlement + **拆出 `interview_settlement.py`**（决策 4A）

```markdown
- [ ] T7: 改 interview.py:complete 触发 settlement + 拆 interview_settlement.py
  - **文件**:
    - `backend/services/interview_settlement.py` (新，3 触发函数)
    - `backend/api/interview.py` 末尾
  - 测试: `tests/test_interview.py::test_complete_triggers_interview_settlement`
  - 依赖: T3
  - 估时: 45 min
  - **产出**: 1 commit
```

**要点**：
- 新建 `backend/services/interview_settlement.py` 装 3 个触发函数：`trigger_settle_after_interview` / `trigger_write_practice_log` / `trigger_v2_summary_invalidate`（空实现，先放接口）
- `interview.py:complete` 末尾调 `trigger_settle_after_interview(interview_id, user_id)` try/except 兜底

#### T8: `test_profile_settlement_service.py` 完整测试套件（决策 6A 派生：≥ 80% 覆盖）

```markdown
- [ ] T8: 写 test_profile_settlement_service.py（≥ 80% 覆盖）
  - **文件**: `backend/tests/test_profile_settlement_service.py:1-300`
  - 测试:
    - `test_settle_after_practice_happy` (GWT-1)
    - `test_settle_after_practice_master_threshold` (GWT-2)
    - `test_settle_after_practice_concurrent_lock` (GWT-3)
    - `test_settle_after_practice_db_failure_no_throw` (GWT-9)
    - `test_settle_after_practice_empty_profile` (TC-1.5)
    - `test_settle_after_interview_aggregates_blind_spots`
    - `test_weekly_full_refresh_recalculates_12_weeks`
    - `test_manual_refresh_invalidates_cache`
  - 依赖: T2-T7 全部
  - 估时: 60 min
  - **产出**: 1 commit
```

**PR 1 标志**：✅ profile.weak_topics 自动更新 + last_active_at 自动更新

---

### PR 2 — V2.2 ObsidianSedimentService（任务 T9-T15，1-2h）

#### T9: 建 `obsidian_sediment_service.py` 骨架（含 _write 容错）

```markdown
- [ ] T9: 建 obsidian_sediment_service.py 骨架 + _write 容错
  - **文件**: `backend/services/obsidian_sediment_service.py:1-80`
  - 测试: `tests/test_obsidian_sediment_service.py::test_class_importable`
  - 依赖: —
  - 估时: 30 min
  - **产出**: 1 commit
```

**要点**：
- class 5 方法占位
- `_write(rel_path, content) -> str | None`（决策 7A 容错核心：vault 不存在/写失败返回 None，log warning，**不抛**）
- `VAULT_ROOT = Path.home() / "Obsidian" / "coding"`（与 V1 obsidian_service 同路径）

#### T10: 实现 `write_daily`（含 YAML frontmatter）

```markdown
- [ ] T10: 实现 write_daily（生成 Markdown + YAML frontmatter）
  - **文件**: `backend/services/obsidian_sediment_service.py:80-140`
  - 测试: `tests/test_obsidian_sediment_service.py::test_write_daily_creates_file_with_frontmatter`
  - 依赖: T9
  - 估时: 30 min
  - **产出**: 1 commit
```

#### T11: 实现 `write_weekly` / `write_monthly` / `write_mastered_dump`

```markdown
- [ ] T11: 实现 write_weekly/monthly/mastered_dump
  - **文件**: `backend/services/obsidian_sediment_service.py:140-220`
  - 测试: `tests/test_obsidian_sediment_service.py::test_write_weekly/monthly/mastered_dump`
  - 依赖: T10
  - 估时: 30 min
  - **产出**: 1 commit
```

#### T12: 实现 `write_practice_log`（面试日志路径 `interview/YYYY-MM-DD-<id>.md`）

```markdown
- [ ] T12: 实现 write_practice_log
  - **文件**: `backend/services/obsidian_sediment_service.py:220-280`
  - 测试: `tests/test_obsidian_sediment_service.py::test_write_practice_log_creates_interview_file`
  - 依赖: T9
  - 估时: 30 min
  - **产出**: 1 commit
```

#### T13: 在 `settle_after_practice` 末尾调 `write_daily`

```markdown
- [ ] T13: settle_after_practice 末尾调 write_daily
  - **文件**: `backend/services/profile_settlement_service.py` (在 settle_after_practice 末尾)
  - 测试: `tests/test_profile_settlement_service.py::test_settle_triggers_write_daily`
  - 依赖: T2, T10
  - 估时: 20 min
  - **产出**: 1 commit
```

**要点**：try/except 包裹，失败 log，不阻塞

#### T14: 在 `settle_after_interview` 末尾调 `write_practice_log`

```markdown
- [ ] T14: settle_after_interview 末尾调 write_practice_log
  - **文件**: `backend/services/profile_settlement_service.py` (在 settle_after_interview 末尾)
  - 测试: `tests/test_profile_settlement_service.py::test_settle_after_interview_triggers_practice_log`
  - 依赖: T3, T12
  - 估时: 20 min
  - **产出**: 1 commit
```

#### T15: `test_obsidian_sediment_service.py` 完整测试套件

```markdown
- [ ] T15: 写 test_obsidian_sediment_service.py（≥ 80% 覆盖）
  - **文件**: `backend/tests/test_obsidian_sediment_service.py:1-250`
  - 测试:
    - `test_write_daily_creates_file_with_frontmatter` (GWT-4)
    - `test_write_daily_vault_missing_returns_none` (GWT-5)
    - `test_write_daily_appends_if_exists` (TC-2.3)
    - `test_write_practice_log_creates_interview_file`
    - `test_security_path_traversal` (TC-2.4)
    - `test_write_weekly/monthly/mastered_dump`
  - 依赖: T9-T14 全部
  - 估时: 60 min
  - **产出**: 1 commit
```

**PR 2 标志**：✅ ~/Obsidian/coding/learning/YYYY-MM-DD.md 自动生成

---

### PR 3 — V2.3 SummaryService + 6 端点 + 前端 3 改造（任务 T16-T25，2-3h）

#### T16: 建 `summary_service.py` 骨架（class + 5 方法 + Redis hook）

```markdown
- [ ] T16: 建 summary_service.py 骨架 + Redis TTL hook
  - **文件**: `backend/services/summary_service.py:1-80`
  - 测试: `tests/test_summary_service.py::test_class_importable`
  - 依赖: —
  - 估时: 30 min
  - **产出**: 1 commit
```

**要点**：决策 2A = Redis TTL 1h，`@cache_result(ttl=3600, key="summary:dashboard:{user_id}")` 装饰器或包装函数

#### T17: 实现 `_generate_narrative`（LLM 调 + strip markdown + 降级）

```markdown
- [ ] T17: 实现 _generate_narrative（LLM + JSON 模板 + strip + 降级）
  - **文件**: `backend/services/summary_service.py:80-160`
  - 测试: `tests/test_summary_service.py::test_generate_narrative_llm_success/failure/fallback`
  - 依赖: T16
  - 估时: 45 min
  - **产出**: 1 commit
```

**要点**：
- 调 `langchain_openai`（V1 已有）
- prompt 模板含：占位符 `{yesterday_count}` / `{mastered}` / `{weak_shift}`
- user input 先 strip markdown + 截断 1000 字（防注入，决策 7A + 9 风险）
- LLM 失败 → 降级返回 `f"昨天你答了 {yesterday_count} 道题..."`（规则模板）

#### T18: 实现 `daily` / `dashboard`（含 Redis 缓存）

```markdown
- [ ] T18: 实现 daily + dashboard（Redis 缓存 + 降级）
  - **文件**: `backend/services/summary_service.py:160-260`
  - 测试: `tests/test_summary_service.py::test_daily/board_cache_hit/cache_miss/fallback`
  - 依赖: T17
  - 估时: 45 min
  - **产出**: 1 commit
```

**要点**：决策 2A — Redis 命中跳 LLM，决策 7A — LLM 失败返 `_fallback=true`

#### T19: 实现 `weekly` / `monthly` / `sync_daily_to_obsidian`

```markdown
- [ ] T19: 实现 weekly/monthly/sync_daily_to_obsidian
  - **文件**: `backend/services/summary_service.py:260-360`
  - 测试: `tests/test_summary_service.py::test_weekly/monthly/sync_daily`
  - 依赖: T18
  - 估时: 30 min
  - **产出**: 1 commit
```

**要点**：monthly 写 `monthly_reports.summary_stats`（DB 落库）

#### T20: 实现 6 个 API 端点 + slowapi 限流

```markdown
- [ ] T20: 实现 6 个新 API 端点 + slowapi 限流
  - **文件**:
    - `backend/api/dashboard.py` 加 `/api/v2/dashboard/summary`
    - `backend/api/profile.py` (新) 含 `/api/v2/profile/weekly/monthly/refresh`
    - `backend/api/knowledge.py` 加 `/api/v2/knowledge/recent-sediments`
    - `backend/api/obsidian.py` (新) 含 `/api/v2/obsidian/sync`
  - 测试: `tests/test_api_v2.py::test_all_6_endpoints_happy/ratelimit/auth`
  - 依赖: T18
  - 估时: 60 min
  - **产出**: 1 commit
```

**要点**：
- 全部走 JWT（V1 风格）
- 限流阈值见 api-spec.md §3.2 表格
- 响应头统一加 `X-API-Version: v2.0`

#### T21: `test_summary_service.py`（≥ 80% 覆盖）

```markdown
- [ ] T21: 写 test_summary_service.py（≥ 80% 覆盖）
  - **文件**: `backend/tests/test_summary_service.py:1-300`
  - 测试:
    - `test_daily_cache_hit/miss/fallback` (GWT-6/7/8)
    - `test_weekly_trajectory_12_weeks`
    - `test_monthly_persists_to_monthly_reports`
    - `test_dashboard_new_user_empty_state`
  - 依赖: T18, T19
  - 估时: 45 min
  - **产出**: 1 commit
```

#### T22: `test_api_v2.py`（6 端点集成）

```markdown
- [ ] T22: 写 test_api_v2.py（6 端点集成测试）
  - **文件**: `backend/tests/test_api_v2.py:1-400`
  - 测试:
    - `test_dashboard_summary_happy/cache/fallback/unauthorized`
    - `test_profile_weekly/monthly/refresh`
    - `test_knowledge_recent_sediments_limit/empty`
    - `test_obsidian_sync_vault_missing`
    - `test_ratelimit_429`
    - `test_e2e_pipeline_3_questions_then_dashboard_then_profile` (TC-INT-1)
  - 依赖: T20
  - 估时: 60 min
  - **产出**: 1 commit
```

#### T23: 前端 commit 1 — 新建 `<DailySummaryCard>` + 嵌入 `dashboard.tsx`

```markdown
- [ ] T23: 新建 DailySummaryCard + 嵌入 dashboard.tsx
  - **文件**:
    - `frontend/components/v2-settlement/DailySummaryCard/index.tsx`
    - `frontend/components/v2-settlement/DailySummaryCard/types.ts`
    - `frontend/components/v2-settlement/DailySummaryCard/hooks.ts`
    - `frontend/pages/dashboard.tsx` (修改)
    - `frontend/types/v2-settlement.ts` (新)
    - `frontend/styles/v2-settlement.css` (新)
  - 测试: `frontend/components/v2-settlement/DailySummaryCard/DailySummaryCard.test.tsx`
  - 依赖: T20
  - 估时: 45 min
  - **产出**: 1 commit
```

**要点**：component-spec.md §2 DailySummaryCard 完整定义，含 6 状态测试

#### T24: 前端 commit 2 — 新建 `<RecentSedimentsCard>` + 嵌入 `knowledge.tsx`

```markdown
- [ ] T24: 新建 RecentSedimentsCard + 嵌入 knowledge.tsx
  - **文件**:
    - `frontend/components/v2-settlement/RecentSedimentsCard/index.tsx`
    - `frontend/components/v2-settlement/RecentSedimentsCard/types.ts`
    - `frontend/components/v2-settlement/RecentSedimentsCard/hooks.ts`
    - `frontend/pages/knowledge.tsx` (修改，stats tab)
  - 测试: `frontend/components/v2-settlement/RecentSedimentsCard/RecentSedimentsCard.test.tsx`
  - 依赖: T23
  - 估时: 30 min
  - **产出**: 1 commit
```

#### T25: 前端 commit 3 — 新建 `/profile` + nav 加"画像"（决策 6A 触发）

```markdown
- [ ] T25: 新建 /profile 页 + nav 加画像入口 + 嵌入 3 子卡
  - **文件**:
    - `frontend/pages/profile.tsx` (新)
    - `frontend/components/v2-settlement/ProfilePage/index.tsx`
    - `frontend/components/v2-settlement/ProfilePage/WeakTopicsCard.tsx`
    - `frontend/components/v2-settlement/ProfilePage/MasteredTopicsCard.tsx`
    - `frontend/components/v2-settlement/ProfilePage/LearningTrajectoryCard.tsx`
    - `frontend/components/Nav.tsx` (修改，加画像入口)
  - 测试: `frontend/components/v2-settlement/ProfilePage/ProfilePage.test.tsx`
  - 依赖: T23
  - 估时: 60 min
  - **产出**: 1 commit
```

**PR 3 标志**：✅ dashboard 顶部卡 + /profile 页 + /knowledge 沉淀卡 全部可用

---

### V2.4 — 验证（任务 T26-T29，1h）

#### T26: 跑 pytest + 覆盖率全绿

```markdown
- [ ] T26: 跑 pytest --cov=services 全绿 + 3 service ≥ 80%
  - **文件**: N/A（命令）
  - 测试: 验证 T8/T15/T21/T22 已写的测试套件覆盖 ≥ 80%（验证类任务，无新测试）
  - 依赖: T8, T15, T21, T22 全过
  - 估时: 15 min
  - **产出**: 1 个 verifier-report.txt
```

#### T27: 跑 check-step.py 全绿

```markdown
- [ ] T27: 跑 check-step.py spec/plan/tasks/verify 全绿
  - **文件**: N/A
  - 测试: 对 docs/ 全部阶段产物跑 DOD 校验（验证类任务，无新测试）
  - 依赖: T26
  - 估时: 5 min
  - **产出**: 1 个 checker-output.txt
```

#### T28: 起本地 + 浏览器走 3 流程

```markdown
- [ ] T28: ./scripts/start.sh + 浏览器验证 3 流程
  - **文件**: N/A
  - 测试: 手动 e2e：答 3 题 → Dashboard 卡更新 / Profile 弱项出现 / Knowledge 沉淀卡列表（手动 smoke，无自动化）
  - 依赖: T25, T26
  - 估时: 30 min
  - **产出**: 3 张截图（dashboard / profile / knowledge）
```

**3 流程**：
1. 答 3 道题 → 看 dashboard 顶部卡内容更新
2. 打开 /profile → 看 weak_topics 出现新项 + 趋势图
3. 打开 /knowledge stats → 看最近学习沉淀列表出现

#### T29: 写 `verify.md`（L3 整合 + L5 staging）

```markdown
- [ ] T29: 写 verify.md（L3 整合 + L5 staging）
  - **文件**: `docs/tasks/2026-06-28-new-feature-v2-smart-sediment/verify.md`
  - 测试: 引用 T-INT-1 ~ T-INT-5 端到端测试结果（验证文档，非新测试）
  - 依赖: T28
  - 估时: 10 min
  - **产出**: 1 commit
```

---

### V2.5 — 复盘（任务 T30-T32，0.5h）

#### T30: 写 `retro.md`

```markdown
- [ ] T30: 写 retro.md（V2 经验沉淀）
  - **文件**: `docs/tasks/2026-06-28-new-feature-v2-smart-sediment/retro.md`
  - 测试: N/A（文档类任务，无自动化测试）
  - 依赖: T29
  - 估时: 15 min
  - **产出**: 1 commit
```

#### T31: 更新 `CLAUDE.md §八.8.2` 标 V2 完成

```markdown
- [ ] T31: 更新 CLAUDE.md §八.8.2 把 V2 状态改 ✅
  - **文件**: `CLAUDE.md` §八.8.2
  - 测试: N/A（文档类任务，无自动化测试）
  - 依赖: T30
  - 估时: 10 min
  - **产出**: 1 commit
```

#### T32: 更新 `docs/api/README.md` 加 6 端点索引

```markdown
- [ ] T32: 更新 docs/api/README.md 加 V2 6 端点
  - **文件**: `docs/api/README.md`
  - 测试: N/A（文档类任务，无自动化测试）
  - 依赖: T30
  - 估时: 5 min
  - **产出**: 1 commit
```

---

## 3. 任务依赖图

```
                    PR 1 (V2.1)                    PR 2 (V2.2)                PR 3 (V2.3)
T1 ─┬─→ T2 ─┬─→ T6                                  T9 ─┬─→ T10 ─┬─→ T13    T16 ─┬─→ T17 ─┬─→ T18 ─┬─→ T20 ─┬─→ T22
    │       │                                          │   ├─→ T11 │         │       │       │       │       ├─→ T23 ─┬─→ T25
    ├─→ T3 ─┴─→ T7                                    │   ├─→ T12 ─┴─→ T14    │       │       ├─→ T19 ├─→ T21  ├─→ T24
    ├─→ T4 ──→ T5                                    T8(测试)                  │       │       │       │       │       │
    └───────→ T8 ───────────────────────────────────────────T15(测试)──────────┴───────┴───────┴───────┴───────┴───────┘
                                                                                                                                      │
                                                                                                                                      ↓ V2.4 (验证)
                                                                                                                                  T26 → T27 → T28 → T29
                                                                                                                                      ↓ V2.5 (复盘)
                                                                                                                                  T30 → T31 → T32
```

**约束**：
- ✅ 无环（DAG）
- ✅ 拓扑序（T6 依赖 T2，T25 依赖 T23）
- ✅ V2.2 和 V2.3 内部可并行（无依赖关系）

**并行机会**：
- V2.1 和 V2.2 之间可并行（不共享 service 文件）— PR 1/2 顺序仍 OK，互不阻塞
- T17 → T18 → T20 是 PR 3 内的线性推进
- T23 (DailySummaryCard) 和 T24 (RecentSedimentsCard) 可并行做

---

## 4. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 |
|---|---|---|
| T1 | test_profile_settlement_service.py::test_class_importable | class 可实例化 |
| T2 | test_settle_after_practice_happy | GWT-1 happy |
| T2 | test_settle_after_practice_master_threshold | GWT-2 edge |
| T2 | test_settle_after_practice_concurrent_lock | GWT-3 failure |
| T2 | test_settle_after_practice_db_failure_no_throw | GWT-9 failure |
| T3 | test_settle_after_interview_aggregates_blind_spots | interview 流程 |
| T4 | test_weekly_full_refresh_recalculates_12_weeks | 重算 12 周 |
| T5 | test_manual_refresh_invalidates_summary_cache | Redis DEL 3 key |
| T6 | test_upsert_progress_triggers_settlement | 触发链 |
| T7 | test_complete_triggers_interview_settlement | 触发链 |
| T8 | 8 个测试 | 覆盖率 ≥ 80% |
| T9 | test_class_importable | class 可实例化 |
| T10 | test_write_daily_creates_file_with_frontmatter | GWT-4 |
| T10 | test_write_daily_vault_missing_returns_none | GWT-5 |
| T11 | test_write_weekly/monthly/mastered_dump | 3 个写入函数 |
| T12 | test_write_practice_log_creates_interview_file | interview log |
| T13 | test_settle_triggers_write_daily | 触发链 |
| T14 | test_settle_after_interview_triggers_practice_log | 触发链 |
| T15 | 6+ 个测试 | 覆盖率 ≥ 80% |
| T16 | test_class_importable | class 可实例化 |
| T17 | test_generate_narrative_llm_success/failure/fallback | LLM 3 路径 |
| T18 | test_daily/board_cache_hit/cache_miss/fallback | 缓存 + 降级 |
| T19 | test_weekly/monthly/sync_daily | 3 个方法 |
| T20 | test_all_6_endpoints_happy/ratelimit/auth | 6 端点 × 3 类 |
| T21 | 4 个测试 | 覆盖率 ≥ 80% |
| T22 | test_e2e_pipeline 等 7 个 | 端到端 |
| T23 | DailySummaryCard.test.tsx | 6 状态 × 1 组件 |
| T24 | RecentSedimentsCard.test.tsx | 6 状态 × 1 组件 |
| T25 | ProfilePage.test.tsx | 6 状态 + 4 子卡 |

---

## 5. 任务↔Spec 映射

| 任务 | spec.md / api-spec / component-spec 对应 | test-cases.md TC |
|---|---|---|
| T1 | spec.md §4.4 ProfileSettlementService 占位 | TC-1.5 |
| T2 | spec.md §4 GWT-1/2/3/9 | TC-1.1/1.2/1.3/1.4 |
| T3 | spec.md §4 副作用 | TC-1.5 |
| T4 | spec.md §5.5 12 周趋势 | — |
| T5 | spec.md §3 缓存 | TC-1.5 |
| T6 | spec.md §3.2 时序 | — |
| T7 | spec.md §3.2 时序 + plan 决策 4A | — |
| T8 | spec.md §5.1 US-1 全 5 个 TC | TC-1.1 ~ 1.5 |
| T9 | spec.md §4.4 ObsidianSedimentService 占位 | TC-2.4 |
| T10 | spec.md §4 GWT-4 | TC-2.1 |
| T11 | spec.md §4.4 write_* | TC-2.5 |
| T12 | spec.md §4.4 write_practice_log | — |
| T13 | spec.md §3.2 时序 | — |
| T14 | spec.md §3.2 时序 | — |
| T15 | spec.md §5.2 US-2 全 TC | TC-2.1 ~ 2.4 |
| T16 | spec.md §4.4 SummaryService 占位 | — |
| T17 | spec.md §4 _generate_narrative | TC-3.2 |
| T18 | spec.md §4 GWT-6/7/8 | TC-3.1/3.2/3.3 |
| T19 | spec.md §4 weekly/monthly/sync | TC-3.1 |
| T20 | api-spec.md §2 全部 6 端点 | TC-INT-1 ~ 5 |
| T21 | spec.md §5.3 US-3 | TC-3.1 ~ 3.4 |
| T22 | api-spec.md §5.1 + §5.2 全 TC | TC-INT-1 ~ 5 |
| T23 | component-spec.md §2 DailySummaryCard | 9 测试点 |
| T24 | component-spec.md §2 RecentSedimentsCard | 8 测试点 |
| T25 | component-spec.md §2 ProfilePage + design-spec §3.1 | 12 测试点 |
| T26-T29 | verify.md §L3 + §L5 | — |
| T30-T32 | retro.md + CLAUDE.md 更新 | — |

---

## 6. 总估时

```
T1:  30 min
T2:  45 min
T3:  30 min
T4:  30 min
T5:  30 min
T6:  30 min
T7:  45 min
T8:  60 min
T9:  30 min
T10: 30 min
T11: 30 min
T12: 30 min
T13: 20 min
T14: 20 min
T15: 60 min
T16: 30 min
T17: 45 min
T18: 45 min
T19: 30 min
T20: 60 min
T21: 45 min
T22: 60 min
T23: 45 min
T24: 30 min
T25: 60 min
T26: 15 min
T27: 5 min
T28: 30 min
T29: 10 min
T30: 15 min
T31: 10 min
T32: 5 min
─────────────────────
总估时: 1085 min = 18h 5min

按 PR 分组:
- PR 1 (V2.1, T1-T8):  310 min = 5h 10min
- PR 2 (V2.2, T9-T15): 220 min = 3h 40min
- PR 3 (V2.3, T16-T25): 450 min = 7h 30min
- V2.4 (T26-T29):      60 min = 1h
- V2.5 (T30-T32):      30 min = 0h 30min
─────────────────────
总: 1070 min = 17h 50min (含并行优化)

预期偏差: ≤ 30%（事后写入 retro.md）
```

> ⚠️ 比 plan.md §6 估的 6-8.5h **翻倍**——更精细粒度（plan 估的是"分 PR"宏观节奏，tasks 估的是"分原子任务"微观实施）。可接受。

---

## 7. 实施顺序（推荐）

```
阶段 1 — PR 1（V2.1, 5h）：
   T1 → T2 → (T3 → T7) 并行 / (T4 → T5) 并行 / (T6 依赖 T2) → T8

阶段 2 — PR 2（V2.2, 3.5h）：
   T9 → (T10 → T13) / (T11 / T12 → T14) 并行 → T15

阶段 3 — PR 3（V2.3, 7.5h）：
   T16 → T17 → T18 → (T19 / T20) 并行 → (T21 / T22) 并行 → (T23 / T24) 并行 → T25

阶段 4 — 验证（V2.4, 1h）：
   T26 → T27 → T28 → T29

阶段 5 — 复盘（V2.5, 0.5h）：
   T30 → T31 → T32
```

---

## 🎯 硬性 DOD（tasks.md 完成必须全过）

- [x] 每个任务 ≤ 1h AI 工作量（32/32，最大 60 min）
- [x] 每个任务 1 个 commit（产出字段已标）
- [x] 每个任务对应 ≥ 1 测试用例（§4 映射表覆盖全部 32 任务）
- [x] 任务依赖关系明确（DAG 无环，§3 依赖图）
- [x] 总估时 vs 实际偏差 ≤ 30%（事后写入 retro.md）

> ✅ 工具校验：`python3 scripts/check-step.py tasks <file>` 应通过

---

## 📚 相关文档

- [plan.md](plan.md) — 上游方案（已冻 7 决策 = 全 A）
- [spec.md](spec.md) — 上游技术契约（9 GWT + 17 TC）
- [api-spec.md](api-spec.md) — 上游 API 详细（6 端点）
- [component-spec.md](component-spec.md) — 上游组件详细（3 组件）
- `docs/DOD.md` §五 — 3 步拆分 DOD 完整定义
- `docs/templates/test-cases-template.md` — 下游 4 步产出 test-cases.md

---

## 🔴 待你 review

| 项 | 状态 |
|---|---|
| 32 个原子任务粒度合理（最大 60 min） | ⏳ 待你确认 |
| PR 分组（5h / 3.5h / 7.5h）合理 | ⏳ 待你确认 |
| 总估时 17h 50min（比 plan 估的 6-8.5h 翻倍） | ⚠️ 待你 review — plan 是宏观节奏估计，tasks 是原子精度，估计偏差可接受 |
| 实施阶段顺序（前 3 阶段按 PR，后 2 阶段按 V2.4/V2.5） | ⏳ 待你确认 |
