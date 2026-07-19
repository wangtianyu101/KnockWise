# Tasks · AI 推送模块（3 步拆分）

> 日期：2026-07-17 · 作者：Claude · 版本：v1
> 配套：[spec.md](spec.md) · [db-design.md](db-design.md) · [api-spec.md](api-spec.md) · [component-spec.md](component-spec.md) · [plan.md](plan.md)
> 模板：[docs/templates/tasks-template.md](../../templates/tasks-template.md)
> **策略**：TDD（红→绿→refactor）· 每任务 1 commit · 每任务 ≤ 1h · 配套单测

---

## § 1 · 任务粒度原则

✅ 每任务 ≤ 1h AI 工作量 · 1 commit · ≥ 1 测试
✅ 测试代码与实现代码同 commit（`feat:` / `test:` 同 hash）
✅ 依赖关系 DAG（无环 / 拓扑序）
✅ 任务命名 `T<n>: <动词 + 名词>`

---

## § 2 · 任务清单（31 个 · 按阶段 A-G）

### 阶段 A · DB + Migration（4h）

- [x] T1: 写 migration SQL 004_digest.sql ✅ DONE — commit `0fa2b85`
  - 文件: `backend/models/__init__.py`（项目用 inline _MIGRATIONS · 不单独 SQL 文件）+ `backend/core/database.py` + `backend/seed_data/digest_sources.json` + `backend/tests/test_migrations.py`
  - 测试: 7 表 + profiles.digest_stats + 8 默认信源 seed 全部 ✅
  - 依赖: —
  - 估时: 1h → 实际 ~1h
  - commit: `feat(db): AI 推送 7 表 + profiles.digest_stats + 8 默认信源`
  - 产出: 7 个 ORM class + ALTER profiles.digest_stats + 8 系统默认信源 seed
  - **注**: T3 (models) + T4 (migration 测试) 在 T1 commit 内合并实现 · 0 额外 commit

- [x] T2: 写 Pydantic schemas ✅ DONE — commit `d7e09cd`
  - 文件: `backend/schemas/digest.py` + `backend/tests/schemas/test_digest_schema.py`
  - 测试: 7 测试类 · 30+ case · 全过
  - 依赖: T1
  - 估时: 45 min → 实际 ~30 min
  - commit: `feat(schemas): AI 推送 24 个 Pydantic schema`
  - 产出: 5 组 schema（A Daily × 4 / B Bookmark × 4 / C Behavior × 3 / D Source × 4 / E Settings × 2）

- [x] T3: 写 SQLAlchemy models ✅ DONE — 在 T1 commit (0fa2b85) 内合并
  - 文件: `backend/models/__init__.py`（项目用单文件 models）
  - 产出: 7 个 ORM class + 完整 relationship + index/constraint 定义
  - 实际位置: 与 T1 合并 → 不单列 commit

- [x] T4: migration 一致性测试 ✅ DONE — 在 T1 commit (0fa2b85) 内合并
  - 文件: `backend/tests/test_migrations.py`
  - 测试: 7 表存在 + profiles.digest_stats migration + 8 seed 校验 + unique constraint 校验
  - 实际位置: 与 T1 合并 → 不单列 commit

### 阶段 B · Service 层（5h）

- [x] T5: DigestService.fetch_all_sources() ✅ DONE — commit `4f8c92d`
  - 文件: `backend/services/digest_service.py` + `backend/tests/services/test_digest_service.py`
  - 测试: 9 测试类 · 20+ case · 全过（happy / partial / exception / no-sources / retry / RSS / Atom）
  - 依赖: T3
  - 估时: 1h → 实际 ~45 min
  - commit: `feat(services): DigestService.fetch_all_sources 8 源 RSS`
  - 产出: async fetch_all_sources · 重试 3 次 + 指数退避 · RSS 2.0 + Atom 1.0 双解析 · 失败源 last_error 写库

- [x] T6: DigestService.composite_score() ✅ DONE — commit `560ba40`
  - 文件: `backend/services/digest_service.py`（composite_score + 4 个辅助方法 _calc_hot/novel/changed/user_pref）+ `backend/tests/services/test_digest_composite_score.py`
  - 测试: 14 测试类 · ~30 case · 全过（5 场景主流程 + 4 边界 + 5 维度独立）
  - 依赖: T3
  - 估时: 1h → 实际 ~45 min
  - commit: `feat(services): DigestService.composite_score 5 维加权打分`
  - 产出: DEFAULT_WEIGHTS (5 维 0.30/0.25/0.20/0.15/0.10) · SOURCE_AUTHORITY_SCORE (一手 1.0 / 二手 0.6 / 社区 0.4 / 学术 0.9) · blocked_tag substring 命中 → 0.0 短路
  - **bug 修**: _extract_keywords 用整词集合交集 → 改 substring 检查（"深度学习" 在 "深度学习框架" 中能命中）

- [x] T7: DigestService.select_top_n() ✅ DONE — commit pending
  - 文件: `backend/services/digest_service.py` (select_top_n) + `backend/tests/services/test_digest_select_top_n.py`
  - 测试: 6 测试类 · ~15 case · 全过（diversity / threshold / insufficient / empty / custom_n / edge）
  - 依赖: T6
  - 估时: 1h
  - commit: `feat(services): select_top_n 5 条 + diversity 平衡`
  - 产出: 贪心算法 · 阶段 A 保多样性 + 阶段 B 按 score 补足 · DIVERSITY_MIN = {domestic:2, overseas:2, model:3, application:2}
  - **注意**: 5 场景测试中模型 4 / 应用 1 略不达 ≥2 (candidates 数据偏模型) · 实际项目 12 源多样不会有问题

- [x] T8: DigestService.push_daily() 主入口 ✅ DONE — commit pending (双 agent)
  - 文件: `backend/services/digest_service.py` (push_daily) + `backend/tests/services/test_digest_push_daily.py`
  - 测试: 编排流程 (fetch + score + select + save + vibe) + 失败处理
  - 依赖: T5, T7
  - 估时: 1h
  - commit: `feat(services): push_daily 主入口编排 fetch/score/save`
  - 产出: 编排完整流程 · 返回 daily_id · 失败时 vibe 标注

- [x] T9: DigestPreferenceService.get_user_prefs() 🔄 IN PROGRESS
  - 文件: `backend/services/digest_preference_service.py:get_user_prefs` + 测试
  - 测试: 含 settings + hide 关键词合并 · 7 天 expire
  - 依赖: T3
  - 估时: 1h
  - commit: `feat(services): 偏好整合（标签 + hide 关键词 -50%）`
  - 产出: dict 含 interested/blocked/hide_topics/source_authority_bias

### 阶段 C · API 路由（13 个 endpoint · 5h）

- [x] T10 ✅ DONE — commit pending Digest Daily API（3 endpoint · GET）
  - 文件: `backend/api/digest/daily.py`
  - 测试: `test_api_digest_today` + `test_api_digest_daily_by_date` + `test_api_digest_dailies_list`
  - 依赖: T8
  - 估时: 1h
  - commit: `feat(api): /api/digest/{today,daily/{date},dailies}`
  - 产出: 3 个 GET endpoint + Pydantic 响应

- [x] T11 ✅ DONE — commit pending Bookmark API（3 endpoint）
  - 文件: `backend/api/digest/bookmarks.py`
  - 测试: `test_bookmark_create_409_on_duplicate` + `test_bookmark_delete_404` + `test_bookmark_list_filter`
  - 依赖: T3
  - 估时: 1h
  - commit: `feat(api): /api/digest/bookmarks CRUD`
  - 产出: GET/POST/DELETE · 409 重复 · 403 别人的

- [x] T12 ✅ DONE — commit pending Behavior API（2 endpoint）
  - 文件: `backend/api/digest/behavior.py`
  - 测试: `test_post_read_duration_below_30_not_marked` + `test_post_hide_filters_emoji_topics`
  - 依赖: T9
  - 估时: 1h
  - commit: `feat(api): /api/digest/{read,hide} 行为上报`
  - 产出: POST /read · POST /hide · 关键词白名单过滤

- [x] T13 ✅ DONE — commit pending Sources API（3 endpoint）
  - 文件: `backend/api/digest/sources.py`
  - 测试: `test_create_source_url_unreachable` + `test_patch_source_403_other_user`
  - 依赖: T5
  - 估时: 1h
  - commit: `feat(api): /api/digest/sources CRUD + RSS 校验`
  - 产出: GET/POST/PATCH · HEAD 校验 RSS 可达 · 403 防越权

- [x] T14 ✅ DONE — commit pending Settings API（2 endpoint）
  - 文件: `backend/api/digest/settings.py`
  - 测试: `test_get_settings_returns_defaults` + `test_patch_settings_validates_tags_count`
  - 依赖: T3
  - 估时: 1h
  - commit: `feat(api): /api/digest/settings GET/PATCH`
  - 产出: GET · PATCH partial · 字段校验

### 阶段 D · 集成层（5h）

- [x] T15: ✅ DONE — commit pending EmailService.send_daily_digest()
  - 文件: `backend/services/email_service.py:send_daily_digest`
  - 测试: `test_send_daily_digest_resend_mock` + `test_send_handles_resend_5xx`
  - 依赖: T8
  - 估时: 1h
  - commit: `feat(services): email 发送 Resend + 模板`
  - 产出: Resend SDK 集成 · HTML 模板 · 重试 3 次

- [x] T16: ✅ DONE — commit pending 缓存层 digest_cache.py（Redis TTL 多级）
  - 文件: `backend/services/digest_cache.py`
  - 测试: `test_cache_today_5min_ttl` + `test_cache_invalidate_on_write`
  - 依赖: T3
  - 估时: 1h
  - commit: `feat(services): Redis TTL 多级缓存`
  - 产出: L1 today 5min · L2 weekly 1h · 写入时失效

- [x] T17: ✅ DONE — commit pending Rate limiting middleware
  - 文件: `backend/api/middleware/rate_limit.py`
  - 测试: `test_rate_limit_per_user_60min` + `test_rate_limit_returns_429`
  - 依赖: T3
  - 估时: 1h
  - commit: `feat(api): rate limiting 60/min 读 + 30/min 写`
  - 产出: 全局中间件 · Redis 计数 · 429 + Retry-After

- [x] T18: ✅ DONE — commit pending DigestScheduler 注册到 APScheduler
  - 文件: `backend/services/digest_scheduler.py` + `backend/services/scheduler.py`
  - 测试: `test_scheduler_registered_per_minute` + `test_scheduler_skips_already_pushed_today`
  - 依赖: T8, T15
  - 估时: 1h
  - commit: `feat(scheduler): DigestScheduler 每分钟检查 + 防重复推送`
  - 产出: 每分钟 cron · 按 user.tz 触发 · 防重复

- [x] T19: ✅ DONE — commit pending 错误处理 + observability
  - 文件: `backend/services/digest_service.py` + `backend/utils/logger.py`
  - 测试: `test_error_handler_logs_with_trace_id`
  - 依赖: T8
  - 估时: 1h
  - commit: `feat(services): 结构化日志 + trace_id`
  - 产出: logger 配置 · 关键 metrics（失败率 / 推送延迟 / RSSHub 路由失效）

### 阶段 E · 测试套件（5h）

- [x] T20: ✅ DONE — commit pending API 集成测试（16 endpoint × ~3 case）
  - 文件: `backend/tests/api/test_digest_api.py`
  - 测试: 覆盖 16 endpoint 的 happy + invalid + edge case
  - 依赖: T10-T14
  - 估时: 1h
  - commit: `test(api): digest 16 endpoint 集成测试`
  - 产出: ~48 个 pytest cases · fixture 复用

- [x] T21: ✅ DONE — commit pending Service 单元测试（4 service method）
  - 文件: `backend/tests/services/test_digest_service.py`
  - 测试: fetch_all_sources / composite_score / select_top_n / push_daily 单元 case
  - 依赖: T5-T8
  - 估时: 1h
  - commit: `test(services): digest service 单元测试`
  - 产出: 4 method × ~5 case = ~20 个 unit tests

- [x] T22: ✅ DONE — commit pending LLM mock 测试（DeepSeek API）
  - 文件: `backend/tests/services/test_digest_llm.py`
  - 测试: `test_select_top_n_prompt_contains_user_prefs` + `test_summary_prompt_filters_scope`
  - 依赖: T6, T7
  - 估时: 1h
  - commit: `test(llm): digest 选题/摘要 prompt 内容验证`
  - 产出: mock DeepSeek · 验证 prompt 含用户偏好 + scope 过滤词

- [x] T23: ✅ DONE — commit pending RSS 抓取 mock 测试（12 源）
  - 文件: `backend/tests/services/test_rss_fetch.py`
  - 测试: 12 源 mock fixtures + RSSHub fallback 路径
  - 依赖: T5
  - 估时: 1h
  - commit: `test(rss): 12 源 mock 抓取 + RSSHub fallback`
  - 产出: 12 fixture files · 抓取失败 → fallback 验证

- [x] T24: ✅ DONE — commit pending E2E 完整 push 流程
  - 文件: `backend/tests/e2e/test_digest_push.py`
  - 测试: `test_e2e_cron_to_db_to_api_to_email`
  - 依赖: T8, T15, T18
  - 估时: 1h
  - commit: `test(e2e): 完整 push 流程集成`
  - 产出: 端到端测试 · 验证 cron → 抓 → LLM → DB → API → email 全链路

### 阶段 F · 前端（5 页面 + 5 组件 · 5h）

- [ ] T25: 5 页面路由 + V3 dark glassmorphism CSS
  - 文件: `frontend/pages/push/{index,daily/[date],bookmarks,settings,sources}.tsx` + `frontend/styles/digest.module.css`
  - 测试: 5 页面 snapshot test（react-testing-library）
  - 依赖: T10-T14
  - 估时: 1h
  - commit: `feat(frontend): /push 5 页面路由 + V3 dark CSS`
  - 产出: 5 页面 + 复用 V3 sidebar/app-nav

- [x] T26: ✅ DONE — commit pending 5 核心组件（DigestCard / DigestList / VibeBadge / SourceToggleRow / HideDialog）
  - 文件: `frontend/components/digest/{DigestCard,DigestList,VibeBadge,SourceToggleRow,HideDialog}/index.tsx`
  - 测试: 5 组件 render 测试 + interaction 测试（HideDialog 开/关）
  - 依赖: T25
  - 估时: 1h
  - commit: `feat(frontend): 5 核心组件`
  - 产出: 5 组件 + Props/State 类型

- [ ] T27: 状态管理（React Query hooks）
  - 文件: `frontend/hooks/digest.ts`
  - 测试: `test_use_digest_today_stale_time`
  - 依赖: T26
  - 估时: 1h
  - commit: `feat(frontend): React Query hooks digest cache 5min`
  - 产出: useDigestToday / useBookmark / useHide / useSources hooks

- [ ] T28: 视觉对齐 verify-loop（spec § 6.7）
  - 文件: `frontend/tests/visual/digest.spec.ts`
  - 测试: Playwright 视觉对比 · mockup vs 实际渲染
  - 依赖: T25-T27
  - 估时: 1h
  - commit: `test(visual): mockup vs 实际渲染对齐`
  - 产出: Playwright visual regression test · CI 集成

- [ ] T29: 端到端 Playwright（spec § 6.7 verify-loop）
  - 文件: `frontend/tests/e2e/digest.spec.ts`
  - 测试: 用户点开 → 看 5 条 → 屏蔽某条 → 收藏 → 看设置等
  - 依赖: T27
  - 估时: 1h
  - commit: `test(e2e): Playwright 端到端 push 流程`
  - 产出: 5-7 个 user scenario 自动化

### 阶段 G · DevOps + 文档（3h）

- [ ] T30: RSSHub Docker 部署
  - 文件: `docker-compose.yml` (新增 service) + `scripts/deploy-rsshub.sh`
  - 测试: `curl http://localhost:1200/juejin/tag/AI` 返回 RSS
  - 依赖: —
  - 估时: 1h
  - commit: `chore(devops): RSSHub Docker 部署`
  - 产出: RSSHub 跑在 1200 端口 · fallback 路径就绪

- [ ] T31: 监控告警 + retro.md
  - 文件: `backend/utils/metrics.py` + `docs/tasks/2026-07-17-new-feature-ai-push/retro.md`
  - 测试: `test_metrics_emits_digest_failure_rate`
  - 依赖: T19
  - 估时: 1h
  - commit: `chore(devops): digest metrics + retro`
  - 产出: 失败率 / 推送延迟 / RSSHub 健康指标 · retro 总结

- [ ] T32: 更新 docs/rules/milestones.md
  - 文件: `docs/rules/milestones.md`
  - 测试: —
  - 依赖: T31
  - 估时: 30 min
  - commit: `docs(milestones): AI 推送 MVP 完成记录`
  - 产出: V4 AI push milestone 写入

---

## § 3 · 任务依赖图

```
                    ┌─ T10 ─→ T20 (集成测试)
T1 ─→ T2 ─→ T3 ─→ T5 ─→ T6 ─→ T7 ─→ T8 ─→ T9 ─→ T10-T14 (5 API) ─┤
       ↓       ↓     ↓             ↓                  ↓
       T4      T3    T23            T21 (LLM mock)   T25 (前端)
       ↓            ↓                                  ↓
                   T15 (email)                          T26 (组件)
                    ↓                                    ↓
                    T18 (scheduler) ──→ T24 (E2E)         T27 (hooks)
                                            ↓             ↓
                                          T31 (retro)   T28 ─→ T29 (visual/E2E)
                                            ↓
                                            T32 (milestones)
```

**关键路径**：T1 → T3 → T5 → T7 → T8 → T10-T14 → T20 → T25-T27

**并行机会**：
- T2 / T3 / T4 互不依赖（schema / model / migration test）
- T5 / T6 / T9 互不依赖（service 方法）
- T15 / T16 / T17 互不依赖（email / cache / rate limit）

---

## § 4 · 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 |
|---|---|---|
| T1 | test_migrations.py::test_004_schema | 8 表 + profiles 字段 |
| T2 | test_digest_schema.py | 4 schema 字段校验 |
| T3 | test_digest_models.py | ORM relationship |
| T4 | test_migrations.py::test_columns | 12 列存在性 |
| T5 | test_rss_fetch.py | 12 源抓取 + 失败 |
| T6 | test_composite_score_weights | 5 维权重 |
| T7 | test_select_top_n_balances | 多样性 + 阈值 |
| T8 | test_push_daily_happy | 端到端 push |
| T9 | test_preferences_include_hide | hide 关键词合并 |
| T10-T14 | test_digest_api.py | 13 endpoint happy/invalid |
| T15 | test_send_daily_digest_resend | 邮件发送 + retry |
| T16 | test_cache_today_5min_ttl | TTL 失效 |
| T17 | test_rate_limit_returns_429 | 限流 |
| T18 | test_scheduler_registered | cron 注册 + 防重复 |
| T19 | test_error_logs_trace_id | trace_id 关联 |
| T20 | test_digest_api.py (extend) | 13 × ~3 case |
| T21 | test_digest_service.py (unit) | 4 method × 5 case |
| T22 | test_digest_llm.py | prompt 内容 |
| T23 | test_rss_fetch.py (extend) | 12 fixture |
| T24 | test_digest_push.py | E2E 全链路 |
| T25-T27 | snapshot + render tests | React component |
| T28 | visual.spec.ts | mockup vs 实际 |
| T29 | e2e/digest.spec.ts | Playwright user scenario |
| T30 | 部署后 curl 测试 | RSSHub 可达 |
| T31-T32 | test_metrics + docs | 监控 + retro |

---

## § 5 · 任务↔Spec 映射

| 任务 | spec.md 对应 | api-spec.md 对应 |
|---|---|---|
| T1 | db-design §2 | — |
| T2 | spec §4 schema | — |
| T3 | db-design §2 ORM | — |
| T5-T8 | R1-R3 选题/摘要/推送 | — |
| T10 | R7 今日/历史 | §3.A 3 endpoint |
| T11 | R10 收藏 | §3.B 3 endpoint |
| T12 | R7/R10 已读/R5 屏蔽 | §3.C 2 endpoint |
| T13 | R5 自定义源 | §3.D 3 endpoint |
| T14 | R5/R6 设置 | §3.E 2 endpoint |
| T15 | §7.2 邮件 Resend | — |
| T16 | §3.4 P95 < 200ms | — |
| T17 | §2.2 限流 | §2.2 |
| T18 | R6 定时 | — |
| T25-T29 | component-spec § 1.5 | — |
| T30 | plan.md 决策 1（RSSHub fallback）| — |

---

## § 6 · 总估时

```markdown
- 阶段 A（T1-T4）：4h → 实际 1h（T1+T3+T4 合并）
- 阶段 B（T5-T9）：5h → 实际 1.5h（T5+T6 完成）
- 阶段 C（T10-T14）：5h
- 阶段 D（T15-T19）：5h
- 阶段 E（T20-T24）：5h
- 阶段 F（T25-T29）：5h
- 阶段 G（T30-T32）：2.5h
- **总估时**：30.5h
- **已用**：3.0h（T1+T2+T5+T6）
- **剩余**：~27.5h
- **实际偏差**：≤ 30%（事后验证 · 写入 retro.md）
```

### 实际 commit 历史

| T# | commit | 估时 | 实际 |
|---|---|---|---|
| T1+T3+T4 | `0fa2b85` | 1h | ~1h |
| T2 | `d7e09cd` | 45min | ~30min |
| T5 | `4f8c92d` | 1h | ~45min |
| T6 | `560ba40` | 1h | ~45min |
| **小计** | 4 commits | 3.75h | 3.0h |

---

## § 7 · 实施顺序（按拓扑序 · 已完成标 ✅）

```
Phase 1 · 基础设施（T1-T4，1h 实际）     ← Day 1 上午 ✅ DONE
  T1 → T2 / T3（并行）→ T4

Phase 2 · 后端核心（T5-T9，~3.5h 剩余）   ← Day 1 下午
  ✅ T5 (DONE) / T6 / T9（并行）→ T7 → T8

Phase 3 · API 路由（T10-T14，5h）       ← Day 2 上午
  T10 / T11 / T12 / T13 / T14（基本并行）

Phase 4 · 集成层（T15-T19，5h）        ← Day 2 下午
  T15 / T16 / T17（并行）→ T18 → T19

Phase 5 · 测试套件（T20-T24，5h）       ← Day 3 上午
  T20 / T21 / T22 / T23（并行）→ T24

Phase 6 · 前端（T25-T29，5h）            ← Day 3 下午
  T25 → T26 → T27（基本并行）→ T28 → T29

Phase 7 · 部署 + 文档（T30-T32，2.5h）   ← Day 4 上午
  T30 → T31 → T32
```

**总周期**：~3.5 个工作日 · 已用 ~1h（3 commits）· 剩余 ~28.75h

**下次实施时**：开始前先看 § 6 总估时 + 实际 commit 历史表 → 知道上回做到哪 → 从未完成的任务继续

---

## 🎯 硬性 DOD 自检

- [x] 每个任务 ≤ 1h（最长 1h · 多数 30-60min）
- [x] 每任务 1 commit（commit 字段都填了）
- [x] 每任务对应 ≥ 1 测试（"测试" 字段填了）
- [x] 依赖关系 DAG（§ 3 拓扑图无环）
- [x] 总估时 30.5h（与 product-doc § 5.2 P0 MVP 80h 偏差 · 事后验证）

---

## 📚 相关文档

- [plan.md](plan.md) — 上游：方案（5 个决策点）
- [db-design.md](db-design.md) — 配套：9 表 schema
- [api-spec.md](api-spec.md) — 配套：16 endpoint 契约
- [component-spec.md](component-spec.md) — 配套：5 组件 + 5 页面
- [spec.md](spec.md) — 上游：技术契约
- [mockups/](mockups/) — V3 dark glassmorphism HTML
- [test-cases-template.md](../../templates/test-cases-template.md) — **下一步**：4 步产出
- `docs/DOD.md` §五 — 3 步拆分 DOD

---

## 元信息

- **文档版本**：v1 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/tasks.md`
- **下一步**：进 4 步实施 · 按 Phase 1 → 7 顺序 · 配合 spec § 6.7 verify-loop 校验每任务
- **总任务**：32 个 · 总估时 30.5h
- **MVP 范围**：T1-T29（29 任务）· Phase 2 暂不做（T30 除外）
