# Research · AI 推送 v2 完整实施（重启）

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [tasks.md](tasks.md)
> 上游：[spec.md](../../2026-07-17-new-feature-ai-push/spec.md) · [decisions.md](../../2026-07-17-new-feature-ai-push/decisions.md)

---

## 0 · 任务理解

用户原话："你看看你目录内的代码改动和设计 现在怎么根本对不上呢？"

我的理解：之前 AI 推送模块的实现（路由、组件、stub 修复、mockup 对齐）只是**页面骨架**。spec.md 的 10 Requirements + 34 Scenarios 没系统对照过 —— 真生产功能（RSSHub / LLM 评分 / 邮件 / 阅读时长上报 / 时区调度）都没接。

## 1 · spec.md Requirements 状态重新审计

| Req | 标题 | 现状 | 缺口性质 |
|---|---|---|---|
| R1 | Daily Digest Generation | 🟡 skeleton | 真 RSSHub 部署 + cron 接通 |
| R2 | Source Aggregation | 🟡 seed ✓ | 真 fetch_all_sources 验证 |
| R3 | Composite Scoring | 🟡 函数在 | 真 LLM 评分 |
| R4 | Source Diversity Balance | ❌ | 真数据跑 pytest 验证 ≥2/2/3/2 |
| R5 | User Customization | 🟡 | HttpUrl 强校验 + tags 上限 |
| R6 | Push Time Configuration | ❌ **大缺口** | `push_timezone` 字段缺 · UI 没时区下拉 |
| R7 | In-Product Reading | 🟡 skeleton | 阅读时长上报（30s） |
| R8 | Email Fallback Notification | ❌ **整个缺** | EmailService 没接 push_daily |
| R9 | Citation & Provenance | 🟡 | related_digest_ids 是 fake |
| R10 | User Behavior Feedback | 🟡 bookmark+hide ✓ | 阅读时长 30s 计时器缺 |

## 2 · 范围（分阶段）

### Phase A · 即时做（不依赖 RSSHub / LLM / 邮件）

| A# | 内容 | 估时 | 依赖 |
|---|---|---|---|
| A1 | R6 时区字段（schema + DB + UI 时区下拉）| 1 h | — |
| A2 | R10 阅读时长上报（30s timer + POST /api/digest/read + 主区域标已读）| 2 h | — |
| A3 | R5 HttpUrl 强校验 + interested_tags max_length=10 拦截 | 1 h | — |
| A4 | 34 TCs 按 R 分组 pytest 化 | 4 h | spec § 5 |

### Phase B · RSS 真集成（依赖 RSSHub）

| B# | 内容 | 估时 |
|---|---|---|
| B1 | RSSHub Docker 部署 + 8 核心源 URL 改 RSSHub | 1 h |
| B2 | 真 fetch_all_sources 跑通 · 验证 signal pool ≥ 30 | 1 h |
| B3 | LLM 评分（DeepSeek / Anthropic / Mock 三选一）| 3 h |

### Phase C · 行为反馈

| C# | 内容 | 估时 |
|---|---|---|
| C1 | R10 阅读后 user_pref 权重 +20% 反馈到 scoring | 2 h |
| C2 | R10 屏蔽到期自动清除 cron | 30 min |

### Phase D · 多渠道

| D# | 内容 | 估时 |
|---|---|---|
| D1 | R8 邮件集成（Resend 接入 + retry 3 次）| 2 h |
| D2 | R8 用户退订 unsubscribe 回调 | 30 min |

### Phase E · 可观测性

| E# | 内容 | 估时 |
|---|---|---|
| E1 | push_daily metrics · 推送耗时 / 成功率 | 1 h |
| E2 | spec § 3.4 P95 性能预算 测量 | 30 min |

### Phase F · UX 完整化

| F# | 内容 | 估时 |
|---|---|---|
| F1 | bookmarks / settings / sources / daily / today's 视觉补齐（mockup 全部对齐）| 4 h |
| F2 | 多语言 i18n（spec § 3.6 · MVP 中文 + digest content 多语言）| 2 h |

**总估时**：~25 h AI（Phase A-D） · ~35 h（全 Phase A-F）

## 3 · 不在本任务范围

| 项 | 原因 |
|---|---|
| 数据库分库分表 | 用户量未到（spec § 3.7 1000 用户天花板）|
| Event 上报（Sentry 等）| spec § 4 副作用 "未来加 P3" |
| RSSHub 多实例 HA | spec § 3.7 1000 用户阈值 |
| LLM 多家 fallback | spec R3 仅一家即可 |

## 4 · Phase A 详细决策

### A1 · R6 时区

| # | 决策 | 选择 |
|---|---|---|
| 1 | 时区字段类型 | IANA str（如 "Asia/Shanghai"）· spec Schema 3 默认值 |
| 2 | UI 选择器 | 5 个预设下拉（Shanghai / NY / LA / London / Tokyo）· spec mockup 04 |
| 3 | DB migration | ALTER TABLE digest_settings ADD push_timezone VARCHAR(64) DEFAULT 'Asia/Shanghai' |
| 4 | backward compat | 旧用户没字段时 fallback 'Asia/Shanghai' |

### A2 · R10 阅读时长

| # | 决策 | 选择 |
|---|---|---|
| 1 | 计时器触发时机 | 详情页 mount 后 30s（一次性）· spec R7 "停留 ≥ 30 秒"|
| 2 | 后端 endpoint | POST /api/digest/read `{ item_id, duration_sec }`（api-spec.md § 3.B 已定义）|
| 3 | 标已读触发 | duration_sec ≥ 30 写入 digest_read · 主区域下次 fetch 时 is_read = true |
| 4 | 计时器失败 | 用户关闭页面也 OK · onbeforeunload 立即上报（best effort）|

### A3 · R5 URL 校验

| # | 决策 | 选择 |
|---|---|---|
| 1 | URL 验证 | Pydantic HttpUrl 类型 + 5s HEAD timeout · spec § 3.3 |
| 2 | 重复检查 | UNIQUE(user_id, url) → 409 SOURCE_DUPLICATE |
| 3 | tags 上限 | interested_tags max_length=10 / blocked_tags max_length=10 → 422 TAGS_LIMIT_EXCEEDED |

### A4 · TCs

按 spec § 5 表写 34 TCs pytest（按 R 分 10 个测试文件）。

## 5 · 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| spec 与 mockup 视觉演化不一致 | 🟡 | spec > mockup · 视觉以 spec 决策为准（V3 dark glassmorphism 已隐式接受）|
| Phase A 写完后 LLM/RSSHub 仍未就绪 → push_daily 不真跑 | 🟡 | dev fallback 保留 · 用户看得到效果 · spec v2 字段先齐 |
| RSSHub Docker 镜像国内拉不动 | 🔴 | 备选：用 RSSHub 公共实例（如有）或 mock 8 源 XML（spec § 3.8 失败恢复）|
| 测试 DB 与本地 DB 冲突 | 🟢 | 沿用 conftest.py TEMPORARY TABLE 约定 |
| pytest 跑 34 case 慢 | 🟢 | 分文件 · pytest -k R1 按需跑 |

## 6 · 关联

- 上游 spec：`/Users/wangtianyu/IdeaProjects/KnockWise/docs/tasks/2026-07-17-new-feature-ai-push/spec.md`
- 决策主账：`/Users/wangtianyu/IdeaProjects/KnockWise/docs/tasks/2026-07-17-new-feature-ai-push/decisions.md`
- 已完成任务：
  - `2026-07-25-refactor-ai-push-route-alignment/` · 路由 + daily/[date] 页面骨架
  - `2026-07-25-bug-digest-pipeline-stub/` · seed + scheduler + Sources API 真实现
  - `2026-07-25-refactor-today-page-mockup-align/` · today 视觉对齐

## 元信息

- **调研日期**：2026-07-25
- **路径模式**：full-6（Path-A only for now · 多周期）
- **下次**：[plan.md](plan.md) → [tasks.md](tasks.md) → Phase A 实施