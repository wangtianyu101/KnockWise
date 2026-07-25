# Tasks · AI 推送 digest pipeline stub 修复

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [research.md](research.md)
> 模板：[docs/templates/tasks-template.md](../../templates/tasks-template.md)
> **策略**：TDD（红→绿→refactor）· 每任务 1 commit · 每任务 ≤ 1h · 配套单测
> **范围**：🔴 完整修（seed + scheduler + Sources API + E2E）

---

## § 1 · 任务粒度原则

✅ 每任务 ≤ 1h AI · 1 commit · ≥ 1 测试
✅ 测试代码与实现代码同 commit
✅ 依赖关系 DAG · 拓扑序

---

## § 2 · 任务清单（7 个 · 按阶段 A-D）

### 阶段 A · Seed + Scheduler（1.5h）

- [ ] **T1**: seed 8 默认信源
  - 文件: `backend/core/database.py` 新增 `_seed_default_digest_sources()` + `init_db()` 调用
  - 数据源: `backend/seed_data/digest_sources.json`（8 项已存在）
  - 幂等: `SELECT COUNT(*) FROM digest_sources WHERE is_default=TRUE` · 已是 8 跳过
  - 测试: `tests/test_migrations.py` 加 `TestSeedDefaultSources.test_seed_runs_idempotent`
  - 依赖: —
  - 估时: 30 min
  - commit: `feat(db): seed 8 默认 digest_sources + 幂等保护`

- [ ] **T2**: 启动 DigestScheduler
  - 文件: `backend/main.py` on_startup 加 `_digest_scheduler_task = asyncio.create_task(_digest_loop())`
  - loop: 每 60s 调 `digest_scheduler.check_and_push()`
  - 错误处理: try/except + log · 不挂 backend
  - shutdown: on_shutdown 取消 task
  - 测试: `tests/services/test_digest_scheduler.py` 加 `test_loop_runs_check_and_push`
  - 依赖: T1（需要信源数据）
  - 估时: 30 min
  - commit: `feat(scheduler): 启动 DigestScheduler 每分钟检查`

### 阶段 B · Sources API DB 实现（1.5h）

- [ ] **T3**: Sources API GET 改 DB query
  - 文件: `backend/api/digest/sources.py` GET endpoint
  - 实现: SELECT all sources where enabled=True · system_count + user_count + items
  - 响应 shape 保持向后兼容
  - 测试: `tests/api/test_digest_sources_api.py` 加 `test_get_returns_db_sources`
  - 依赖: T1（需要 seed 数据）
  - 估时: 30 min
  - commit: `feat(api): Sources GET 改 DB query`

- [ ] **T4**: Sources API POST 改 DB insert
  - 文件: `backend/api/digest/sources.py` POST endpoint
  - 校验: URL HEAD 5s timeout · 失败 400
  - 重复检查: UNIQUE(user_id, url) · 重复 409
  - 写: DigestSource(user_id=user.id, is_default=False, enabled=True)
  - 响应 201: 创建对象
  - 测试: 3 case (success/duplicate/invalid_url)
  - 依赖: T3
  - 估时: 45 min
  - commit: `feat(api): Sources POST 改 DB insert + RSS HEAD 校验`

- [ ] **T5**: Sources API PATCH 改 DB update
  - 文件: `backend/api/digest/sources.py` PATCH endpoint
  - 所有权: source.user_id != user.id → 403
  - enabled / name 部分更新
  - 测试: 3 case (success/forbidden/not_found)
  - 依赖: T3
  - 估时: 30 min
  - commit: `feat(api): Sources PATCH 改 DB update + 所有权检查`

### 阶段 C · E2E 验证（30 min）

- [ ] **T6**: E2E pipeline 端到端跑通
  - 步骤:
    1. 重启 backend → DB 中 8 行 ✅
    2. curl /api/digest/sources → 8 行 ✅
    3. 手动触发 push_daily → digest_daily 有 1 行 ✅
    4. curl /api/digest/today → 200 + items ✅
    5. 浏览器访问 /push → 看到 5 卡片
  - 测试: `tests/e2e/test_digest_pipeline.py`
  - 依赖: T1-T5
  - 估时: 30 min
  - commit: `test(e2e): digest pipeline 端到端验证`

### 阶段 D · 验证 + 收尾（30 min）

- [ ] **T7**: 全量 verify + retro
  - pytest backend 全绿
  - typecheck frontend 不变差
  - vitest frontend 不变差
  - e2e Playwright 全绿
  - retro.md 5 段
  - 依赖: T1-T6
  - 估时: 30 min
  - commit: 与上一个 T 合并 / 或独立

---

## § 3 · 实施顺序（拓扑序）

```
T1 ──┬──> T3 ──┬──> T4
     │         └──> T5
     └──> T2 ──┘
              │
              v
            T6 ──> T7
```

可并行：
- T1 完成后 T2 / T3 可并行
- T4 / T5 互不依赖 · 可并行

建议 commit 顺序：T1 → T3 → T5 → T4 → T2 → T6 → T7（按依赖最短路径）

---

## § 4 · 测试覆盖矩阵

| API/Hook | 单测 | E2E | 集成 |
|---|---|---|---|
| seed_default_digest_sources | ✅ T1 | — | — |
| digest_scheduler.check_and_push | ✅ T2 | — | T6 |
| GET /api/digest/sources | ✅ T3 | — | T6 |
| POST /api/digest/sources | ✅ T4 | — | T6 |
| PATCH /api/digest/sources/{id} | ✅ T5 | — | T6 |
| 端到端 pipeline | — | ✅ T6 | — |

---

## § 5 · 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| seed 重复插 | 幂等检查 |
| scheduler 启动失败 | try/except 不阻断 |
| RSS HEAD 超时 | 5s timeout · 失败 400 |
| 系统默认 source 误改 | spec 要求 is_default 不允许 PATCH name · 本期不实现 |
| pytest fixture 冲突 | 沿用项目约定（独立 DB）|

---

## § 6 · 总估时

| 阶段 | 工时 |
|---|---|
| A · Seed + Scheduler | 1 h |
| B · Sources API | 1.75 h |
| C · E2E | 30 min |
| D · 验证 + 收尾 | 30 min |
| **合计** | **~3.5 h AI** |

---

## § 7 · commit 历史表（实施后回填）

| 实际 commit | 估时 vs 实际 | 偏差分析 |
|---|---|---|
| _pending_ | — | — |

---

## § 8 · 关键决策

| # | 决策 | 选择 | 理由 |
|---|---|---|---|
| 1 | scheduler 模式 | asyncio.create_task + sleep 60 · 不是真 APScheduler | 项目 archive_service 用同样模式 · 一致 |
| 2 | seed 时机 | init_db() 内 · 与 V3.1 collection seed 平行 | 启动幂等 · 与既有约定一致 |
| 3 | RSS HEAD 校验 | aiohttp 5s timeout · 失败 400 | spec R5 要求 · 5s 是行业标准 |
| 4 | T3-T5 顺序 | T3 (GET) → T4 (POST) → T5 (PATCH) | 读先于写 · 利于调试 |
| 5 | 系统默认 source PATCH | 本期不做 24h 自动重新启用 | TODO follow-up · 不在 P0 |

---

## § 9 · 元信息

- **任务作者**：Claude
- **任务日期**：2026-07-25
- **路径模式**：fix-mini（实际跨多组件按 full-6 跑）
- **范围**：🔴 完整修
- **关联**：[`docs/issues.md`](../../issues.md) 债务 9 · v2 audit 记录