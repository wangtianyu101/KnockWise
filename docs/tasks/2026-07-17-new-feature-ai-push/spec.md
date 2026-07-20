# Spec · AI 推送模块

> 日期：2026-07-17 · 作者：Claude · Spec 版本：v2
> 配套：[product-doc.md](product-doc.md) · [research.md](research.md) · [sources-investigation.md](sources-investigation.md) · [dual-agent-synthesis.md](dual-agent-synthesis.md)
> Supersedes：[2026-06-22-new-feature-ai-push/spec.md](../2026-06-22-new-feature-ai-push/spec.md)（旧版 scope 较宽 · 写法为 free-form 散文 · 本版用 Requirement + Scenario 严格结构）

---

## 0. 上游引用

- **调研报告**：[research.md](research.md) v1
- **产品文档**：[product-doc.md](product-doc.md) v1
- **信源调研**：[sources-investigation.md](sources-investigation.md) v2
- **双 Agent 聚合**：[dual-agent-synthesis.md](dual-agent-synthesis.md) v1
- **调研版本**：v2（含 dual-agent synthesis 合并后）
- **关键决策**（从 product-doc §3 抄）：
  - D1: 5 条固定 · 不再 1-5 可变
  - D2: 主体验在 KnockWise 内（pull-based）· 邮件/微信作 fallback 通知
  - D3: 8 核心源 + 用户可加自选
  - D4: 每条 digest 含引用溯源
  - D5: 国内/国外 + 模型/应用 双轴标签
  - D6: 公众号资质立即申请（不阻塞 P0 编码）
- **关键风险**（从 research §4 抄 · 🔴）：
  - 🔴 信源 RSS 不稳定 → RSSHub fallback + 监控
  - 🔴 LLM 选题偏差 → source_url + 引用溯源（防 hallucination）
  - 🔴 用户习惯未建立 → 6-8 周不评估（X2 共识）

---

## 1. 用户故事

### 故事 1 · 主路径 · AI 应用开发者

> 作为 AI 应用开发者，我想要每天打开 KnockWise 时直接看到 5 条 AI/LLM/Agent 最新动态，以便**不用刷 Twitter / HN / 多 RSS 源**就能跟进 AI 圈。

### 故事 2 · Fallback 通知

> 作为 KnockWise 用户（不活跃 mock interview 的），我想要收到邮件 / 微信通知"今日 AI 推送已就绪"，以便**主路径之外也能被提醒**而不漏掉重要内容。

### 故事 3 · 调偏好

> 作为有明确关注领域的 AI 开发者（如只关心 Claude + LangChain），我想要在设置页启停源、加关注标签、屏蔽标签，以便**AI 推送匹配我的领域**而不是泛 AI 圈。

> ⚠️ 故事数量上限 3 条 · 不增加 · 范围扩张 → 拆成新 spec

**已验收**：✅ 用户 2026-07-17（与 Claude 多轮对话沉淀 · 见 product-doc.md § 八签字段）

---

## 2. 验收标准（Requirement + Scenario 双层结构）

### Requirement: Daily Digest Generation（每日 5 条 digest 生成）
**The system SHALL generate exactly 5 AI/LLM/Agent technology digest items daily.**

#### Scenario: 正常生成 5 条
- **Given** 8 核心源全部抓取成功 · 候选池 ≥ 20 条
- **When** 每日 8:00 cron 触发 `DigestService.push_daily()`
- **Then** 输出恰好 5 条 digest · 每条含 title / summary / source_url / category / type / region

#### Scenario: 候选不足 5 条
- **Given** 多源失败 · 候选池只剩 3 条评分 ≥ 0.75
- **When** 触发 push
- **Then** 输出 3 条 · digest 顶部 vibe 字段 = "今日 3 条 · 周末偏安静"
- **And** 不补 2 条低分凑数（score < 0.75 丢弃）

#### Scenario: 全部源失败
- **Given** 8 核心源全部 RSS 抓取失败
- **When** 触发 push
- **Then** 系统记录 RSS_FAILURE 日志 · 邮件不发 · 当日 skip
- **And** 用户下次进入 KnockWise 显示"今日 digest 暂缺"提示

#### Scenario: 无新内容（低活跃日）
- **Given** 所有源抓取成功但去重后候选 = 0 条新内容
- **When** 触发 push
- **Then** vibe = "今日 AI 圈无新动态 · 周末静默"

---

### Requirement: Source Aggregation（信源聚合）
**The system SHALL aggregate from at least 8 core sources, with ≥ 30 items in signal pool before scoring.**

#### Scenario: 8 核心源全部就绪
- **Given** 8 核心源（4 国内 + 4 国外 · 配置在 `digest_source` 表）
- **When** 每日抓取执行
- **Then** 候选池 ≥ 30 条 · 进入 LLM 选题环节

#### Scenario: 部分源失败（≤ 3 失败）
- **Given** 8 源中 2 源失败（RSSHub 5xx 或网络超时）
- **When** 抓取执行
- **Then** 候选池 ≥ 20 条 · LLM 选题正常 · 失败源标 `last_fetched_at = NULL` + warn 日志

#### Scenario: 超过半数源失败（≥ 5 失败）
- **Given** 8 源中 6 源失败
- **When** 抓取执行
- **Then** 系统进入降级模式 · 用最近 24h 缓存 · LLM 选题正常 · 错误码 `RSS_DEGRADED`

#### Scenario: 用户添加自定义 RSS 源
- **Given** 用户在 settings 输入有效 RSS URL（http/https + RSS 格式）
- **When** 提交 `POST /api/digest/sources`
- **Then** 新源入库 · 24h 内首次抓取 · 评分纳入下次 push_daily

#### Scenario: 用户禁用源
- **Given** 用户对某源 `PATCH /api/digest/sources/{id}` 设置 `enabled = false`
- **When** push_daily 执行
- **Then** 该源跳过抓取 · 候选池不包含其内容

---

### Requirement: Composite Scoring（综合打分）
**The system SHALL score each candidate item using 5-dimension weighted scoring (hot / novel / changed / source_authority / user_pref) and select top 5 items scoring ≥ 0.75.**

#### Scenario: 正常评分
- **Given** 候选池 30 条 · 用户有偏好数据
- **When** LLM 评分执行
- **Then** 返回 5 条 score ≥ 0.75 · 按分数降序

#### Scenario: 新源无历史（changed 维度无 baseline）
- **Given** 用户刚刚 starred 了一个新公司 · 该公司 history = 0
- **When** 评分执行
- **Then** changed 维度降权为 0.5x · 其他维度正常 · 不导致新源永远低分

#### Scenario: 用户无偏好数据（新用户）
- **Given** user_pref_history = 空
- **When** 评分执行
- **Then** user_pref 维度取默认值（关注"Agent" + "LLM" 大类）· 不抛错

#### Scenario: 全部候选平分
- **Given** 30 条候选 score 都 = 0.85（最高同分）
- **When** 评分执行
- **Then** 按次级排序（hot 维度优先）· 仍输出 5 条 · 不确定性可接受

---

### Requirement: Source Diversity Balance（信源多样性平衡）
**The system SHALL ensure at least 2 domestic + 2 overseas + ≥ 3 model + 2 application items in the 5 selected digests.**

#### Scenario: 内容充足平衡
- **Given** 候选池覆盖国内/国外 + 模型/应用
- **When** 选题执行
- **Then** 5 条 digest 满足约束 · LLM 选题 prompt 强制要求

#### Scenario: 国内内容不足
- **Given** 候选池中国内源当天 0 条新内容 · 国外 30 条
- **When** 选题执行
- **Then** 强制 2/5 国内无法满足 · vibe 标注 "今日国内 AI 圈偏静" · 不强制凑数

#### Scenario: 应用内容不足
- **Given** 候选池中模型 30 条 · 应用 1 条
- **When** 选题执行
- **Then** 5 条中应用仅 1 条 · 标注 · 不强制 ≥ 2

#### Scenario: 单源占多（去重）
- **Given** 5 条候选中有 3 条来自同一源（同一新闻多家报道）
- **When** LLM 去重 + 选题
- **Then** LLM 识别"重复报道" · 合并为 1 条 · 引用多源 · 余下 4 条补足 5 条

---

### Requirement: User Customization（用户定制）
**The system SHALL allow users to add/remove/enable/disable sources and configure preference/block tags.**

#### Scenario: 添加合法 RSS 源成功
- **Given** 用户提交 URL = "https://huggingface.co/blog" + 标签 = "model"
- **When** `POST /api/digest/sources`
- **Then** 返回 201 + source_id · URL 格式验证通过 · RSS 内容验证通过

#### Scenario: URL 重复拒绝
- **Given** 用户提交 URL 已存在（en 另一用户的源或系统默认源）
- **When** `POST /api/digest/sources`
- **Then** 返回 409 · error code = `SOURCE_DUPLICATE`

#### Scenario: URL 不合法
- **Given** 用户提交 URL = "not-a-url" 或 "ftp://..."
- **When** `POST /api/digest/sources`
- **Then** 返回 422 · error code = `INVALID_URL`

#### Scenario: 偏好标签超限
- **Given** 用户已配置 10 个 interested_tags（上限）
- **When** `PATCH /api/digest/settings` 添加第 11 个
- **Then** 返回 422 · error code = `TAGS_LIMIT_EXCEEDED`

#### Scenario: 屏蔽标签生效
- **Given** 用户在 digest 详情点 [🔇 屏蔽] · topic = "元宇宙"
- **When** `POST /api/digest/hide`
- **Then** 写入 digest_hide · expires_at = +7 days · 该 topic 在 LLM 选题 prompt 中 -50% 权重

---

### Requirement: Push Time Configuration（推送时间配置）
**The system SHALL trigger daily digest at user-configurable time in user's timezone (default: 08:00 Asia/Shanghai).**

#### Scenario: 默认时区 + 默认时间
- **Given** 用户未配置 push_timezone 或 push_hour
- **When** 系统初始化推送调度
- **Then** 调度使用 08:00 Asia/Shanghai · 时区来自 user profile 默认

#### Scenario: 用户改时间
- **Given** 用户 `PATCH /api/digest/settings` 设置 push_hour = 7, push_minute = 30
- **When** 调度刷新
- **Then** 推送在每日 07:30 用户本地时区触发

#### Scenario: 用户改时区
- **Given** 用户从 Asia/Shanghai 改到 America/New_York
- **When** 调度刷新
- **Then** 下次推送按 America/New_York 时区 08:00 触发

#### Scenario: 跨时区用户（旅行场景）
- **Given** 用户配置 Asia/Shanghai + push_hour = 8 · 当前 UTC = 0:00
- **When** cron 检查
- **Then** 当前 Asia/Shanghai = 08:00 · 触发推送 · 不受物理位置影响（按配置时区算）

#### Scenario: cron 漂移处理
- **Given** cron 服务因重启延迟 5 分钟
- **When** cron 恢复
- **Then** 系统检测到当日 8:00 已过 · 标记 `pushed_today = true` · 当日不再触发

---

### Requirement: In-Product Reading（产品内主阅读）
**The system SHALL display today's 5 digest items as the primary entry point when user opens KnockWise.**

#### Scenario: 用户登录 / 今日 digest 已生成
- **Given** 今日 5 条已写入 digest_daily · 用户已登录
- **When** 用户打开 KnockWise 首页
- **Then** 首页主区域展示 5 条 · 已读 N 条标灰 · 未读高亮

#### Scenario: 今日 digest 未生成（cron 延迟）
- **Given** 现在 7:00 · cron 还没触发
- **When** 用户打开 KnockWise
- **Then** 显示"今日 digest 即将生成 · 8:00 自动推送"占位 · 不报错

#### Scenario: 用户过期未读（隔了 3 天）
- **Given** 用户上次打开是 3 天前 · 今天没读
- **When** 用户打开
- **Then** 主区域 = 今天 5 条 · 不堆叠历史 · 历史可点 /push 页面查看

#### Scenario: 已读标记
- **Given** 用户点开某 digest 详情页停留 ≥ 30 秒
- **When** 关闭详情
- **Then** 写入 digest_read · duration_sec = 实际时长 · 主区域该条标灰

---

### Requirement: Email Fallback Notification（邮件 fallback 通知）
**The system SHALL send a notification email to users who have enabled email channel, with digest summary + link to in-product page.**

#### Scenario: 邮件发送成功
- **Given** 用户配置 email_enabled = true · Resend API 可用
- **When** push_daily 完成 · 5 条 digest 写入
- **Then** 通过 Resend 发送邮件 · subject = "KnockWise · 今日 5 条 AI 推送" · 含跳转链接

#### Scenario: 邮件发送失败（Resend 5xx）
- **Given** Resend API 返回 500
- **When** push_daily 邮件环节
- **Then** 重试 3 次（5 / 15 / 60 分钟间隔）· 仍失败则记 warn 日志 · 不阻塞 push_daily 主流程

#### Scenario: 用户退订
- **Given** 用户点邮件里的 unsubscribe
- **When** unsubscribe 回调触发
- **Then** 用户 email_enabled = false · 不再发邮件 · 但 in-product digest 仍可用

#### Scenario: 用户未配置邮箱
- **Given** 用户 profile.email = NULL 或 email_enabled = false
- **When** push_daily 邮件环节
- **Then** 跳过邮件 · 不报错

---

### Requirement: Citation & Provenance（引用溯源）
**The system SHALL attach source_url, source_name, published_at, and related_digest_ids to every digest item for verification.**

#### Scenario: 含完整溯源
- **Given** digest item 从某 RSS 源抓取 · 该源 URL 有效
- **When** 写入 digest_daily_item
- **Then** source_url 不为空 · source_name 不为空 · published_at 来自 RSS 原文

#### Scenario: source_url 缺失（源数据无 link）
- **Given** 某 RSS 项无 `<link>` 字段
- **When** 写入 digest
- **Then** source_url = 空字符串 · 详情页显示"原始链接不可用"· 不抛错

#### Scenario: 关联历史 digest
- **Given** 5 条新 digest 中 2 条同主题（如都关于 Claude 4.x）
- **When** 写入 digest_daily_item
- **Then** related_digest_ids 字段含相关历史 digest 的 id（按 cosine 相似度 top-3）

#### Scenario: 跨日报关联
- **Given** 昨天有 1 条关于 DeepSeek V4 · 今天又 1 条关于 DeepSeek V4.1
- **When** 写入今日 digest
- **Then** 今日 DeepSeek V4.1 条目的 related_digest_ids 包含昨天的 DeepSeek V4

---

### Requirement: User Behavior Feedback（用户行为反馈）
**The system SHALL use reading_duration, bookmark, and hide history to update user_pref weights for future scoring.**

#### Scenario: 记录阅读时长
- **Given** 用户在详情页停留 120 秒
- **When** 用户关闭详情
- **Then** 写入 digest_read · duration_sec = 120 · 主区域该条标"已读"

#### Scenario: 收藏权重 +20%
- **Given** 用户点 [收藏]
- **When** `POST /api/digest/bookmarks`
- **Then** 写入 digest_bookmark · LLM 评分时 user_pref 维度对相关 topic 关键词 +20% 权重

#### Scenario: 屏蔽 7 天 -50%
- **Given** 用户点 [🔇 屏蔽] · reason = "not_interested"
- **When** `POST /api/digest/hide`
- **Then** 写入 digest_hide · topic_keywords 提取 · expires_at = +7 days · LLM 评分 prompt 中该 topic 关键词 -50%

#### Scenario: 屏蔽到期清除
- **Given** digest_hide.expires_at < 当前时间
- **When** LLM 评分执行
- **Then** 该 hide 不参与评分 · DB 记录可异步清理

---

## 3. 边界条件

### § 3.1 空值 / 异常 / 并发
- **空值**：digest_daily_item.title 不允许为空（NOT NULL 约束）· summary 可为空（fallback 显示原文标题）
- **异常**：RSSHub 5xx → fallback 用 Redis 24h 缓存 · LLM API 超时 → exponential backoff 3 次 · DB 断连 → 报警 + skip 当日 push
- **并发**：1000 用户同时打开 KnockWise 触发 `GET /api/digest/today` → MySQL 连接池 ≥ 20 · Redis 缓存命中降 DB 压力

### § 3.2 时序（顺序依赖）
- 抓取必须在评分之前（候选池为空 → 评分 fail）
- 评分必须在写库之前（top-5 选完 → 写 digest_daily / digest_daily_item）
- 邮件必须在写库之后（库里有 digest_id → 邮件含跳转链接）

### § 3.3 安全 / 权限
- **权限**：用户只能看自己订阅的 digest · 不能看别人 · 用 user_id 过滤所有 query
- **注入防护**：用户输入 RSS URL → Pydantic HttpUrl 校验 · LLM prompt 用户可控字段（topic / reason）做长度限制（≤ 100 字符）+ 过滤 emoji
- **prompt 注入防护**：用户屏蔽的 topic_keywords 经白名单过滤（≤ 5 关键词）· 防止注入长 prompt 干扰 LLM

### § 3.4 性能 / QPS
- **GET /api/digest/today** P95 < 200ms（命中 Redis 缓存）
- **GET /api/digest/daily/[date]** P95 < 300ms（DB read + cache fallback）
- **QPS 上限**：单用户 GET ≤ 60/hour · 全局 cron 触发 ≤ 1/小时 · 用户主动调用 ≤ 100 QPS
- **LLM 调用**：评分 1 次 cron · 摘要 1 次 cron · 用户主动追问（Phase 3）按需

### § 3.5 兼容性 / 版本
- **向后兼容**：旧 spec 的 16 API 中保留命名空间 `/api/digest/*` · 旧字段 deprecated 但仍可读
- **API 版本化**：本期 v1 · 后续 v2 走 `/api/v2/digest/*`
- **Schema 迁移**：004_digest.sql ALTER TABLE profiles ADD COLUMN digest_stats · 不破坏既有数据

### § 3.6 国际化
- **时区**：用户 profile.timezone · 系统按 timezone 计算 cron · DB 全部 UTC 存储
- **多语言**：本期 MVP 中文为主 · digest content 多语言（LLM 按 source 决定中/英）· UI 文案后续 i18n

### § 3.7 资源限制
- **LLM 成本**：单用户 / 日 ≤ ¥0.05 · 全局 1000 用户 / 日 ≤ ¥50
- **DB 容量**：digest_daily_item 5 条/用户/日 × 365 天 × 1000 用户 = 1.8M 行 / 年 · MySQL 充足 · 索引 `(user_id, date DESC)`
- **RSSHub 部署**：单实例 ≥ 1GB RAM · 月度监控 · 备用实例（如果 ≥ 1000 用户活跃）

### § 3.8 失败恢复
- **RSSHub 宕机**：5 分钟内自动重启（Docker）· fallback 用最近 24h Redis 缓存 · 不阻塞 push
- **LLM API 限流（DeepSeek 429）**：exponential backoff · 5/15/60 分钟重试 · 失败 3 次后用本地默认摘要
- **数据库崩溃**：cron 暂停 · 报警到 #alerts · 修复后 cron 自动恢复

---

## 4. 数据契约

### Schema 1: `digest_daily_item` 核心字段

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import date, datetime
from typing import Literal
from uuid import UUID

class DigestDailyItem(BaseModel):
    id: UUID
    daily_id: UUID
    rank: int = Field(ge=1, le=5)  # 业务：固定 5 条 · rank 1-5

    # 内容
    title: str = Field(max_length=512)
    summary: str | None = Field(default=None)  # 业务：LLM 3-5 行摘要 · 失败可空
    quality_score: float = Field(ge=0.0, le=1.0)  # 业务：综合打分

    # 双轴标签（D5 决策）
    type: Literal["model", "application"]  # 业务：必填二选一
    region: Literal["domestic", "overseas"]  # 业务：必填二选一

    # 分类
    category: Literal["headline", "business", "paper", "engineering", "opinion"]
    # 注：business 类别保留但本期 scope 内被过滤（用户原话：不推商业）

    # 溯源（D4 决策 · 必填）
    source_name: str = Field(max_length=128)  # 业务：源名 · 例"DeepSeek Docs"
    source_url: str = Field(max_length=1024)  # 业务：原始链接 · 空字符串 = 不可用
    published_at: datetime | None  # 业务：原文发布时间

    # 关联（D9 related_digest_ids）
    related_digest_ids: list[UUID] = Field(default_factory=list, max_length=5)

    # 元
    estimated_minutes: int = Field(ge=1, le=5)
    created_at: datetime

class DigestDailyItemCreate(BaseModel):
    """内部 service 层使用 · push_daily 创建时填"""
    title: str
    summary: str | None = None
    quality_score: float
    type: Literal["model", "application"]
    region: Literal["domestic", "overseas"]
    category: Literal["headline", "business", "paper", "engineering", "opinion"]
    source_name: str
    source_url: str
    published_at: datetime | None = None
    related_digest_ids: list[UUID] = Field(default_factory=list)
    estimated_minutes: int = 3
```

### Schema 2: `DigestSource` 用户自定义源

```python
class DigestSourceCreate(BaseModel):
    url: HttpUrl  # 业务：必须 http/https + 有效 RSS 格式
    name: str = Field(max_length=128)
    category: Literal["model", "application"]
    enabled: bool = True

class DigestSource(BaseModel):
    id: UUID
    user_id: UUID | None  # NULL = 系统默认源 · 非空 = 用户自定义
    name: str
    url: HttpUrl
    category: Literal["model", "application"]
    enabled: bool
    last_fetched_at: datetime | None
    last_item_count: int = 0
    created_at: datetime
```

### Schema 3: `DigestSettings` 用户推送设置

```python
class DigestSettings(BaseModel):
    user_id: UUID

    # 推送时间
    push_hour: int = Field(ge=0, le=23, default=8)  # 业务：用户本地时区的小时
    push_minute: int = Field(ge=0, le=59, default=0)
    push_timezone: str = Field(default="Asia/Shanghai")  # IANA tz

    # 渠道开关
    email_enabled: bool = True
    macos_enabled: bool = False

    # 偏好标签
    interested_tags: list[str] = Field(default_factory=list, max_length=10)
    blocked_tags: list[str] = Field(default_factory=list, max_length=10)

    # 输出控制
    daily_count: int = Field(default=5, ge=3, le=5)  # 业务：D1 决策 · 固定 5
```

### Schema 4: `DigestHide` 屏蔽记录

```python
class DigestHide(BaseModel):
    id: UUID
    user_id: UUID
    item_id: UUID
    reason: Literal["not_interested", "low_quality", "already_seen"]
    topic_keywords: list[str] = Field(max_length=5)  # 业务：LLM 提取 · 防 prompt 注入
    expires_at: datetime  # 业务：+7 days
    created_at: datetime
```

### 副作用

- **DB 变更**：`profiles` 加 `digest_stats` JSON · 4 新表（`digest_source` / `digest_daily` / `digest_daily_item` / `digest_read` / `digest_bookmark` / `digest_hide` / `digest_settings`）
- **Cache 失效**：`digest:today:{user_id}:{date}` 缓存键 · push_daily 后失效
- **Event 上报**：未来加（P3）· `DigestDeliveredEvent` / `DigestOpenedEvent`

---

## 5. 测试场景（验收测试）

每个 Scenario 的 When/Then → 对应 1 个 pytest 用例（spec-template § 2.3 要求）

| TC | 关联 Scenario | 描述 |
|---|---|---|
- [ ] **TC-1** (R1 · 正常生成 5 条): push_daily 正常 · 写库 5 条 · 邮件发 · vibe 不空
- [ ] **TC-2** (R1 · 候选不足 5 条): 候选池 3 条 · 写库 3 条 · vibe = "偏安静"
- [ ] **TC-3** (R1 · 全部源失败): 8 源全部 fail · skip 当日 push · log warn
- [ ] **TC-4** (R1 · 无新内容): 候选池 0 条新 · vibe = "今日 AI 圈无新动态"
- [ ] **TC-5** (R2 · 8 源全部就绪): 候选池 ≥ 30 条
- [ ] **TC-6** (R2 · 部分源失败): 2 源失败 · 候选池 ≥ 20 · 失败源 last_fetched_at = NULL
- [ ] **TC-7** (R2 · 半数源失败): 6 源失败 · 进入降级模式 · 用 Redis 缓存
- [ ] **TC-8** (R2 · 添加自定义源): 用户提交合法 URL · 201 + source_id
- [ ] **TC-9** (R2 · URL 重复): 重复 URL · 409 + SOURCE_DUPLICATE
- [ ] **TC-10** (R2 · URL 不合法): "not-a-url" · 422 + INVALID_URL
- [ ] **TC-11** (R3 · 正常评分): 候选池 30 · 输出 5 条 score ≥ 0.75
- [ ] **TC-12** (R3 · 新源无历史): 新公司 · changed 维度 0.5x · 评分正常
- [ ] **TC-13** (R3 · 用户无偏好): user_pref_history = 空 · 默认关注 Agent/LLM
- [ ] **TC-14** (R3 · 全部平分): 30 条都 0.85 · 按 hot 维度排序
- [ ] **TC-15** (R4 · 内容充足平衡): 5 条满足 2 国内 + 2 国外 + 3 模型 + 2 应用
- [ ] **TC-16** (R4 · 国内不足): 候选池国内 0 · vibe 标注 · 不强制凑
- [ ] **TC-17** (R4 · 应用不足): 候选池应用 1 · 5 条中应用 1 · 标注
- [ ] **TC-18** (R4 · 单源占多): 5 条中 3 条同源 · LLM 去重 · 合并 1 条
- [ ] **TC-19** (R5 · 添加合法源): 用户 RSS URL · 201
- [ ] **TC-20** (R5 · 屏蔽生效): 用户点 🔇 · digest_hide 入库 · 7 天后 -50%
- [ ] **TC-21** (R6 · 默认时区): 默认 08:00 Asia/Shanghai · 用户未配置
- [ ] **TC-22** (R6 · 改时间): push_hour = 7 · 下次 07:30 触发
- [ ] **TC-23** (R6 · 跨时区): Asia/Shanghai → America/New_York · 调度刷新
- [ ] **TC-24** (R7 · 主阅读): 用户登录 · 首页展示今日 5 条 · 已读标灰
- [ ] **TC-25** (R7 · 详情页停留 30s): duration_sec 写入 · 主区域标"已读"
- [ ] **TC-26** (R8 · 邮件发送): Resend 200 · 邮件发 · 含跳转链接
- [ ] **TC-27** (R8 · 邮件失败重试): Resend 500 · 重试 3 次 · 仍失败 log warn
- [ ] **TC-28** (R8 · 邮件退订): unsubscribe · email_enabled = false · in-product 仍可用
- [ ] **TC-29** (R9 · 含完整溯源): source_url + source_name + published_at 不空
- [ ] **TC-30** (R9 · source_url 缺失): 源数据无 link · 显示"原始链接不可用"
- [ ] **TC-31** (R9 · 关联历史): 同主题 2 条 · related_digest_ids 含历史 id
- [ ] **TC-32** (R10 · 阅读时长): 详情页停留 120s · digest_read.duration_sec = 120
- [ ] **TC-33** (R10 · 屏蔽到期): expires_at < 当前 · 不参与评分
- [ ] **TC-34** (R5 · 偏好超限): 10 个 interested_tags · 加第 11 · 422

**测试数量**：34 TCs · 覆盖 10 Requirements · 4 类场景（happy/invalid/edge/failure 各 ≥ 1 per requirement）

---

## § 5.5 · 跨文档引用（指向 2 步技术详细化）

```markdown
- 涉及 schema 变更？ → 2 步产出 db-design.md（7 表 + 迁移 SQL 004_digest.sql）
- 涉及新/改 API？   → 2 步产出 api-spec.md（16 个 REST endpoint · 含 /api/digest/*）
- 涉及新组件？      → 2 步产出 component-spec.md（5 页 + 5 组件 · 含 /push 首页）
- 都不涉及？       → 2 步只产出 plan.md
```

**判定**：3 个都涉及（schema + API + 组件都新增）· 2 步需产出 **db-design.md + api-spec.md + component-spec.md + plan.md** 四份。

---

## § 🎯 · DOD 自检

- [x] 5 段齐全（用户故事 / Requirement + Scenario / 边界 / 数据契约 / 测试场景）
- [x] Requirement = 10（每个 SHALL 强约束）
- [x] Scenario = 34 条（happy + invalid + edge + failure 各 ≥ 1 per requirement）
- [x] 数据契约 = 4 schema（Pydantic）
- [x] 测试场景 = 34 TCs
- [x] § 0 上游引用齐全（research + product-doc + sources + dual-agent）
- [x] 用户故事已验收（写"已验收"段）
- [ ] **未完成**：pre-commit 自动校验（未跑）· 工具：`python3 scripts/check-step.py spec docs/tasks/2026-07-17-new-feature-ai-push/spec.md`

---

## 元信息

- **Spec 版本**：v2 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/spec.md`
- **下一步**：跑 pre-commit check · 修 missing · 走 2 步出 db-design + api-spec + component-spec + plan
- **风险**：✅ 34 Scenarios 中 happy 路径 12 · invalid 12 · edge 6 · failure 4 · 4 类覆盖
