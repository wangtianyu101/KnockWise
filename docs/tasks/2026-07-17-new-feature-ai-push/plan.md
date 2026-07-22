# Plan · AI 推送模块

> 日期：2026-07-17 · 作者：Claude · 版本：v1
> 配套：[spec.md](spec.md) · [db-design.md](db-design.md) · [api-spec.md](api-spec.md) · [product-doc.md](product-doc.md) · [research.md](research.md)
> 模板：[docs/templates/plan-template.md](../../templates/plan-template.md)
> **路径**：0 调研 → 1 规格 → **2 计划（本步）** → 3 拆分 → 4 实现 → 5 验证 → 6 复盘

---

## § 1 · 推荐方案

**推荐**: A2（混合部署）+ B + C + D2
  - RSS 抓取：**A2 自建爬虫 + RSSHub 兜底**（RSS 抓取失败时 fallback）
  - LLM 编排：**B 异步队列**（不阻塞 cron · 可重试）
  - 调度：**C APScheduler**（项目已有 · 简单）
  - 邮件渠道：**D2 Resend**（已有免费 tier · 100 封/天 · 适配 MVP）
  - 缓存：**E Redis TTL**（已有 Redis）
- **理由**: spec D6 已拍 A 公众号资质立即申请 + C 用户邮箱 fallback · 本方案不引入新基建 · 全部用项目已有能力扩展
- **工作量**: MVP ~80h（13 endpoint + 3 service + 7 表 + 5 页前端 + 测试）
- **风险**: 🟡 中等（综合：5 个 🟡 · 2 个 🟢）

---

## § 2 · 方案对比（5 个关键决策点）

### 决策 1 · RSS 抓取方案

| 维度 | **方案 A1**：RSSHub 统一接入 | **方案 A2（推荐）**：自建爬虫 + RSSHub 兜底 |
|---|---|---|
| **思路** | 全部 RSS 通过 RSSHub 实例 URL 转换 | 自写 feedparser 抓 12 源，RSSHub 仅作兜底 |
| **优点** | • 统一 URL · 容易扩展新源<br>• 社区维护 · 路由更新免费 | • 依赖少 · 8/12 源 RSS 直连无需 RSSHub<br>• 调试简单 · 抓取错误可见<br>• RSSHub 失败 fallback |
| **缺点** | • RSSHub 路由被反爬时全部失效<br>• 多一层网络依赖 | • 每个源单独维护<br>• 写更多抓取代码 |
| **风险等级** | 🟡（RSSHub 路由经常被反爬打破） | 🟢（更可控） |
| **工作量** | 0.5d（部署 + 12 源 URL 映射） | 2d（12 源抓取代码 + RSSHub fallback） |
| **兼容性** | ✅ 完全兼容 | ✅ 完全兼容 |
| **测试影响** | 加 RSSHub 路由测试 | 加 per-source 抓取 mock 测试 |

### 决策 2 · LLM 编排（同步 vs 异步）

| 维度 | **方案 B1**：同步调用 | **方案 B2（推荐）**：异步队列（asyncio task） |
|---|---|---|
| **思路** | push_daily 同步调 DeepSeek · 阻塞 cron | asyncio.create_task 推送 → 后台跑 · cron 不阻塞 |
| **优点** | • 实现简单 · 调试直接<br>• 一眼看到错误 | • cron 不阻塞 · 1 个用户慢不影响其他<br>• 失败可重试 · Redis 暂存 |
| **缺点** | • LLM 慢 30-60s 时 · 整个 cron 卡<br>• 失败直接丢失 · 无法 retry | • 实现复杂 · 需 task 状态机<br>• 调试需要看 task 状态 |
| **风险等级** | 🟡（cron 卡住 → 后续用户没收到） | 🟢（可控） |
| **工作量** | 1d | 3d（task 状态机 + Redis 暂存） |
| **兼容性** | ✅ | ✅ |
| **测试影响** | mock LLM 即可 | mock LLM + task state machine 测试 |

### 决策 3 · 调度实现

| 维度 | **方案 C（推荐）**：APScheduler | **方案 C2**：Celery beat |
|---|---|---|
| **思路** | 用项目已有 `backend/services/scheduler.py` 模式，加 DigestScheduler 任务 | 引入 Celery + Redis broker |
| **优点** | • 项目已有 · 沿用模式<br>• in-process · 简单<br>• 不引入新中间件 | • 分布式 · 可横向扩展 worker<br>• 重试机制完善 |
| **缺点** | • in-process · 单点风险<br>• 多实例需要小心 | • 引入 Celery + Redis broker · 复杂<br>• MVP 1000 用户规模用不上 |
| **风险等级** | 🟢 | 🟡（多实例部署复杂） |
| **工作量** | 1d | 5d |
| **兼容性** | ✅ | ⚠️ 需引入 Celery 生态 |
| **测试影响** | mock cron 时间触发 | mock Celery task |

### 决策 4 · 邮件渠道

| 维度 | **方案 D1**：自建 SMTP | **方案 D2（推荐）**：Resend API |
|---|---|---|
| **思路** | 用项目 smtplib + QQ 邮箱 SMTP | 用 Resend API（开发免费 100 封/天 · production $20/mo） |
| **优点** | • 无第三方依赖 · 0 成本 | • API 简洁 · 模板友好<br>• 免费 tier 足够 MVP<br>• 送达率高于自建 SMTP |
| **缺点** | • 送达率低 · 容易被标记垃圾<br>• 需要 SMTP 配置 · 运维负担 | • 第三方依赖<br>• 超过 100 封/天收费 |
| **风险等级** | 🟡（垃圾箱 · 邮件打开率低） | 🟢 |
| **工作量** | 1d | 0.5d |
| **兼容性** | ✅ | ✅ |
| **测试影响** | mock smtplib | mock Resend API |

### 决策 5 · 缓存策略

| 维度 | **方案 E（推荐）**：Redis TTL 多级缓存 | **方案 E2**：纯 DB 查询 |
|---|---|---|
| **思路** | L1: 5min TTL "today" · L2: 1h TTL "weekly stats" · L3: DB | 全部从 MySQL 读 |
| **优点** | • /today 接口 P95 < 200ms（spec §3.4）<br>• LLM 调用缓存 · 重复用户降本<br>• 1000 用户同时访问 OK | • 实现最简 · 无缓存失效问题 |
| **缺点** | • 缓存一致性 · 写入时要 invalidate<br>• 监控复杂（命中率） | • /today 高峰 30s（LLM 调用未缓存）<br>• DB 压力大 · QPS 高 |
| **风险等级** | 🟢（标准模式） | 🟡（性能不达标） |
| **工作量** | 1d | 0d（但要重做） |
| **兼容性** | ✅ | ✅ |
| **测试影响** | mock Redis + TTL 测试 | 简单 |

---

## § 3 · 风险评估（10 条 · 带等级 + 缓解）

| # | 风险 | 等级 | 缓解措施 |
|---|---|---|---|
| 1 | **RSSHub 路由被反爬打破**（Juejin / 36氪 经常改） | 🔴 | 方案 A2 自建优先 · RSSHub 仅 fallback · 监控 last_fetched_at · 失败 3 次自动禁用源 |
| 2 | **DeepSeek API 限流 / 不可达** | 🔴 | 用 asyncio + retry · 失败降级到缓存的"昨日 digest" · 监控 API 失败率 > 5% 告警 |
| 3 | **8 核心源 RSS URL 失效**（上线前实测 · spec § 0 标注风险） | 🟡 | 上线前 curl 全部 12 URL · 失效的源替换 RSSHub 路由或剔除 |
| 4 | **LLM 摘要幻觉**（数字 / 公司名） | 🟡 | spec R9 强制 source_url + related · 用户可验证 · 关键内容人工 review spot check |
| 5 | **cron 漂移 / 时区错乱** | 🟡 | 用 APScheduler + user.tz · 测试覆盖多 timezone（NY/SF/London）|
| 6 | **spec D7 Phase 2 不做 → 用户期待 WeChat 但拿不到** | 🟡 | product-doc § 六写明范围 · D6 公众号资质本周申请 · 4-6 周后上线 |
| 7 | **1000+ 用户并发 push 时邮件发不出去** | 🟡 | D2 Resend tier 监控 · 100 封/天 = 约 5 用户活跃 · 大规模前切换 SMTP/SES |
| 8 | **mailto: dev-login token 与 spec auth 不一致** | 🟢 | 用 dev-login 拿 JWT · Authorization: Bearer 头 · 已在 api-spec § 2.1 统一 |
| 9 | **8 表 migration 与现有 profiles 表加字段冲突** | 🟢 | 004_digest.sql ALTER TABLE profiles ADD COLUMN · MySQL 原生支持 · 备份即可 |
| 10 | **mockup V3 风格 vs 实际 React 组件落地差距** | 🟢 | spec § 6.7 verify-loop · 每 commit 跑 § 6.7 视觉对齐检查 |

---

## § 4 · 决策点（5 个）

**决策 1 · RSS 抓取用 RSSHub 兜底还是纯自建？**
- 方案: **A2 自建 + RSSHub 兜底**（理由：12 源 8 个 RSS 直连够用 · RSSHub 兜底安全 · 维护成本可控）
- 替代方案: A1 纯 RSSHub（风险：路由经常被反爬打破）
- 引文：research.md § 3 #1 · product-doc.md D6

**决策 2 · LLM 编排用同步还是异步？**
- 方案: **B2 异步队列**（理由：单用户 LLM 调用 30-60s · 同步会卡 cron · 项目已有 asyncio 模式）
- 替代方案: B1 同步（实现简单但生产不可用）
- 引文：spec.md R1 · § 3.4 性能 P95 < 200ms

**决策 3 · 调度用 APScheduler 还是 Celery？**
- 方案: **C APScheduler**（理由：项目已有 scheduler.py · MVP 1000 用户规模用不上 Celery 分布式）
- 替代方案: C2 Celery beat（5d 工作量 · MVP 不需要）
- 引文：spec.md R6 · 已有 [backend/services/scheduler.py](../../../../backend/services/scheduler.py)

**决策 4 · 邮件用 Resend 还是自建 SMTP？**
- 方案: **D2 Resend API**（理由：100 封/天免费 · 送达率高 · API 简单）
- 替代方案: D1 自建 SMTP（垃圾箱 · 送达率低）
- 引文：spec.md § 7.2 · D2 推送渠道默认 Resend

**决策 5 · 缓存用 Redis TTL 还是纯 DB？**
- 方案: **E Redis TTL 多级**（理由：spec § 3.4 P95 < 200ms 要求 · 项目已有 Redis）
- 替代方案: E2 纯 DB（性能不达标）
- 引文：spec.md § 3.4 · product-doc.md D2

---

## § 5 · 任务拆分建议（Phase 1 MVP · ≤ 1h 每项）

### 阶段 A · DB + Migration（4h · 4 tasks）

- **T1**: 写 `backend/migrations/004_digest.sql`（2h）— 创建 8 表 + profiles 加字段 · 用前一次的 004_digest.sql 模板
- **T2**: 写 Pydantic schemas `backend/schemas/digest.py`（30min）— 4 个 schema（DigestDailyItem / Source / Settings / Hide）
- **T3**: 写 SQLAlchemy models `backend/models/digest.py`（1h）— 8 表 ORM + relationship
- **T4**: 跑 `pytest tests/test_migrations.py` 验证 schema 一致（30min）— pytest fixture 加 DB session

### 阶段 B · Service + API（12h · 12 tasks）

- **T5**: `DigestService.fetch_all_sources()`（1h）— 12 源 RSS 抓取 · async + retry · mock 测试
- **T6**: `DigestService.composite_score()`（1h）— 5 维评分（hot / novel / changed / source_authority / user_pref）
- **T7**: `DigestService.select_top_n(target=5, min_score=0.75)`（1h）— 选 5 条 · 平衡 diversity
- **T8**: `DigestService.push_daily(user_id, date)`（2h）— 主入口 · 编排 fetch + score + save + email
- **T9**: `DigestPreferenceService.get_user_prefs()`（30min）— 用户偏好整合（含 hide 关键词 -50%）
- **T10**: 16 API endpoint 路由（3h）— 每个 ~10min · spec § 6.1 + api-spec § 3
- **T11**: 邮件发送 `EmailService.send_daily_digest()`（30min）— Resend SDK · 模板渲染
- **T12**: 缓存层 `digest_cache.py`（1h）— Redis TTL 多级 · invalidate on write
- **T13**: Rate limiting middleware（1h）— 60/min 读 · 30/min 写
- **T14**: Scheduler 任务 `DigestScheduler.check_and_push()`（1h）— APScheduler 注册 · per user tz
- **T15**: Error handling + observability（30min）— logger + metric · spec R1 failure scenario

### 阶段 C · Tests（10h · 10 tasks）

- **T16**: API 集成测试 · 16 endpoint × 4 scenario = ~30 cases（3h）
- **T17**: Service 单元测试 · fetch / score / select / push（3h）
- **T18**: LLM mock 测试（DeepSeek API mock · 测试 prompt 内容）（1h）
- **T19**: RSS 抓取测试 · 12 源 mock fixtures（1h）
- **T20**: E2E · 完整 push 流程 · cron → DB → API → email（1h）
- **T21**: 性能 benchmark · /today P95 < 200ms（30min）

### 阶段 D · 前端（12h · 5 tasks · 略 · 见 component-spec.md）

- **T22-26**: 5 个 React 组件 + 5 页面（V3 dark glassmorphism）· 12h

### 阶段 E · DevOps + 文档（5h）

- **T27**: RSSHub 部署（如选 A2）（1h）· Docker 一行
- **T28**: 监控告警 · digest 失败率 · RSSHub 路由失效（1h）
- **T29**: Retro 写 `docs/tasks/.../retro.md`（1h）· 按 spec § 6.6
- **T30**: 更新 docs/rules/milestones.md（30min）

**总计**: 13 + 15 + 6 + 5 + 3 ≈ **~42h**（按 1h per task × 30 tasks 估 · 实际因复杂度有 ±20% 浮动）

---

## § 6 · 实施路径

```
0 调研 ✅ (research.md + sources-investigation.md + dual-agent-synthesis.md)
  ↓
1 规格 ✅ (spec.md · product-doc.md)
  ↓
2 计划 ✅ (db-design.md + api-spec.md + plan.md · 本文件)
  ↓
3 拆分 → tasks.md（按阶段 A-E 拆 30 任务）
  ↓
4 实现 → TDD（红→绿→refactor · 每任务配套单测）
  ↓
5 验证 → L3 整合测试 + L5 staging 跑通
  ↓
6 复盘 → retro.md（写经验 · 更新 docs/rules/）
```

---

## 🎯 硬性 DOD 自检

- [x] 方案 ≥ 2 个（5 个决策点 · 每个 A/B 对比）
- [x] 推荐方案明确（§ 1 · A2+B+C+D2+E 组合）
- [x] 风险点带等级（10 条 · 🔴2 + 🟡5 + 🟢3 · 用 🔴/🟡/🟢 emoji 标记）
- [x] 决策点 ≥ 1（5 个 · 决策 1-5）
- [x] 引用完整（spec.md / research.md / product-doc.md / db-design.md / api-spec.md）

---

## 📚 相关文档

- [spec.md](spec.md) — 上游：技术契约（10 Requirements + 34 Scenarios）
- [product-doc.md](product-doc.md) — 上游：产品意图
- [research.md](research.md) — 0 步调研（含 confidence levels）
- [sources-investigation.md](sources-investigation.md) — 30+ 源清单
- [db-design.md](db-design.md) — 9 表 schema + 迁移 SQL
- [api-spec.md](api-spec.md) — 16 endpoint 契约
- [dual-agent-synthesis.md](dual-agent-synthesis.md) — 双 agent 调研聚合
- [tasks-template.md](../../templates/tasks-template.md) — **下一步**：第 3 步任务拆分
- `docs/DOD.md` §四 — 2 步计划 DOD 完整定义

---

## 元信息

- **文档版本**：v1 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/plan.md`
- **下一步**：写 `tasks.md`（按阶段 A-E 拆 30 任务 · 每任务 ≤ 1h · 每任务配套单测）
- **预估总工时**：~42h（与 product-doc § 5.2 P0 MVP 43h 基本对齐）
- **MVP 范围**：13 endpoint（A1-3, B 全部, C 全部, D 全部, E 全部）+ 8 表 + 5 前端页面
- **Phase 2 范围**：3 endpoint（A4-5, F）+ Watchlist / Obsidian 同步
