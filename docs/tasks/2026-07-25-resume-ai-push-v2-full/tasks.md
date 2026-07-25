# Tasks · AI 推送 v2 完整实施

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [research.md](research.md)

---

## Phase A · 即时可做（不依赖 RSSHub/LLM/邮件）

### A1 · R6 时区字段完整化

- [ ] T-A1: DB schema 加 `push_timezone` 列（`core/database.py:_MIGRATIONS`）
- [ ] T-A2: Pydantic schema 同步（`schemas/digest.py:DigestSettings` 加 timezone 字段）
- [ ] T-A3: API 层：GET/PATCH settings 暴露 timezone
- [ ] T-A4: settings UI 加时区下拉（5 预设 · save 调用 PATCH）
- [ ] T-A5: pytest · invalid timezone → 默认 fallback Asia/Shanghai

**估时 1h**

### A2 · R10 阅读时长上报

- [ ] T-A6: daily/[date].tsx 加 30s timer（useEffect mount + setTimeout）
- [ ] T-A7: 上报 POST /api/digest/read `{ item_id, duration_sec }`
- [ ] T-A8: backend API GET /api/digest/today 返回 is_read（基于 digest_read 表）
- [ ] T-A9: today page DigestCard `is_read=true` 显示已读视觉（已有）
- [ ] T-A10: e2e 场景 8：模拟停留 30s → 主区域标已读

**估时 2h**

### A3 · R5 URL + tags 校验

- [ ] T-A11: backend api/digest/sources.py POST 改 Pydantic HttpUrl schema
- [ ] T-A12: tags 上限 Pydantic Field(max_length=10) 在 settings PATCH
- [ ] T-A13: 重复 URL 改 409 error code = SOURCE_DUPLICATE（已 409 · 仅改 error code）
- [ ] T-A14: pytest 4 case · invalid url / dup / tag overlimit / valid

**估时 1h**

### A4 · 34 TCs pytest 化（spec § 5）

- [ ] T-A15: tests/services/test_r1_digest_generation.py（TC-1~4 · 4 case）
- [ ] T-A16: tests/services/test_r2_source_aggregation.py（TC-5~9 · 5 case）
- [ ] T-A17: tests/services/test_r3_composite_scoring.py（TC-11~14 · 4 case）
- [ ] T-A18: tests/services/test_r4_diversity_balance.py（TC-15~18 · 4 case）
- [ ] T-A19: tests/api/test_r5_user_customization.py（TC-19, TC-20, TC-34 · 3 case）
- [ ] T-A20: tests/services/test_r6_push_time.py（TC-21~23 · 3 case）
- [ ] T-A21: tests/services/test_r7_in_product_reading.py（TC-24~25 · 2 case）
- [ ] T-A22: tests/services/test_r8_email.py（TC-26~28 · 3 case · mock email service）
- [ ] T-A23: tests/services/test_r9_citation.py（TC-29~31 · 3 case）
- [ ] T-A24: tests/services/test_r10_user_behavior.py（TC-32~33 · 2 case）
- [ ] T-A25: pytest 全跑通 33 case（TC-10 移 A3）

**估时 4h**

### A5 · verify + commit + retro

- [ ] T-A26: tsc + vitest + pytest + e2e 全绿
- [ ] T-A27: commit + retro.md

---

## Phase B-F · 后续 session 接力

> 这些阶段**不依赖上述 Phase A**（可直接独立推进）· 文档已定义清楚 · 由后续 session 执行

### Phase B · RSS 真集成

- [ ] T-B1: RSSHub 部署（Docker 或 mock 8 XML · 国内 docker 镜像）
- [ ] T-B2: 真 fetch_all_sources 验证 signal pool ≥ 30
- [ ] T-B3: LLM 评分（DeepSeek / Anthropic / Mock 三选一）

### Phase C · 行为反馈

- [ ] T-C1: 阅读后 user_pref 权重 +20% 反馈到 scoring
- [ ] T-C2: 屏蔽到期自动清除 cron

### Phase D · 多渠道

- [ ] T-D1: 邮件集成（Resend + retry 3 次）
- [ ] T-D2: 用户退订 unsubscribe 回调

### Phase E · 可观测性

- [ ] T-E1: push_daily metrics
- [ ] T-E2: P95 性能预算 测量

### Phase F · UX 完整化

- [ ] T-F1: bookmarks / settings / sources / daily / today's 视觉补齐
- [ ] T-F2: i18n（spec § 3.6 MVP 中文）

---

## 总估时

| Phase | 工时 |
|---|---|
| A | 8h |
| B-F | 27h |
| **合计** | **~35h AI** |

---

## commit 历史表（实施后回填）

| 实际 commit | 估时 vs 实际 | 偏差分析 |
|---|---|---|
| _pending_ | — | — |