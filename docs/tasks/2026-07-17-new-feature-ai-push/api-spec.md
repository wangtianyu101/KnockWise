# API Spec · AI 推送模块

> 日期：2026-07-17 · 作者：Claude · 版本：v1
> 配套：[spec.md](spec.md) · [db-design.md](db-design.md) · [product-doc.md](product-doc.md)
> 模板：[docs/templates/api-spec-template.md](../../templates/api-spec-template.md)
> **Auth**: 所有 endpoint 需 `Authorization: Bearer <token>` · 沿用 KnockWise 现有 JWT（`/api/auth/dev-login`）

---

## § 1 · 接口清单（16 个）

| 分组 | Method | Path | 作用 | 阶段 |
|---|---|---|---|---|
| **A · Digest Daily** | `GET` | `/api/digest/today` | 今日 5 条 digest | MVP |
| | `GET` | `/api/digest/daily/{date}` | 某天完整 digest + items | MVP |
| | `GET` | `/api/digest/dailies?limit=7` | 最近 N 天 digest 列表 | MVP |
| | `GET` | `/api/digest/weekly/{week}` | 周报（ISO 周）| Phase 2 |
| | `GET` | `/api/digest/monthly/{month}` | 月报 | Phase 2 |
| **B · Bookmarks** | `GET` | `/api/digest/bookmarks` | 我的收藏列表 | MVP |
| | `POST` | `/api/digest/bookmarks` | 收藏某条 | MVP |
| | `DELETE` | `/api/digest/bookmarks/{item_id}` | 取消收藏 | MVP |
| **C · Behavior** | `POST` | `/api/digest/read` | 标记已读 + duration | MVP |
| | `POST` | `/api/digest/hide` | 🔇 屏蔽 + 关键词 | MVP |
| **D · Sources** | `GET` | `/api/digest/sources` | 信源列表（含系统 + 自定义）| MVP |
| | `POST` | `/api/digest/sources` | 添加自定义 RSS | MVP |
| | `PATCH` | `/api/digest/sources/{id}` | 启停 / 编辑 / 删除 | MVP |
| **E · Settings** | `GET` | `/api/digest/settings` | 读取推送设置 | MVP |
| | `PATCH` | `/api/digest/settings` | 更新推送设置 | MVP |
| **F · Obsidian** | `POST` | `/api/digest/sync-to-obsidian` | 写回 Obsidian vault | Phase 2 |

---

## § 2 · 通用规范

### 2.1 认证（沿用项目 JWT）

```
Authorization: Bearer <jwt-token>
```

- token 由 `/api/auth/dev-login` 获取（开发环境）
- 用户身份从 token 解析为 `user_id` · 不接受 body 传 user_id（防越权）

### 2.2 限流

| 维度 | 阈值 | 超限响应 |
|---|---|---|
| 每用户 · digest 读操作 | 60/min | 429 + `Retry-After: 60` |
| 每用户 · bookmark / hide / read 写操作 | 30/min | 429 |
| 每用户 · sources 写操作 | 10/min | 429 |
| 全局 · sources 抓取 cron | 不限频（system 触发）| — |

### 2.3 时间格式

- 所有时间字段用 **ISO 8601 字符串**（`2026-07-17T08:00:00+08:00`）
- 数据库存 UTC · API 层按 `user.timezone` 转换

### 2.4 分页

- digest/bookmark 类列表：`?limit=N&offset=M`，默认 `limit=20`，上限 `limit=100`
- 信源列表：不分页（数量小）

### 2.5 错误响应统一格式

```json
{
  "error": {
    "code": "INVALID_PARAMS",
    "message": "tags must be 1-10 items",
    "details": {
      "field": "interested_tags",
      "constraint": "max_length=10"
    }
  }
}
```

| HTTP | 错误 code | 触发场景 |
|---|---|---|
| 400 | `INVALID_PARAMS` | 请求参数不符合 schema |
| 401 | `UNAUTHORIZED` | token 缺失 / 过期 / 无效 |
| 403 | `FORBIDDEN` | 资源不属于当前 user（如删别人的 source）|
| 404 | `NOT_FOUND` | 资源不存在 |
| 409 | `CONFLICT` | URL 已存在 / 已 bookmark |
| 429 | `RATE_LIMITED` | 触发限流 |
| 500 | `INTERNAL_ERROR` | DB / LLM / 第三方服务失败 |

---

## § 3 · 各接口详细定义

### 3.A · Digest Daily（5 个）

#### GET /api/digest/today

**作用**：今日 5 条 digest + vibe（spec R1 · 主入口）|

**Request**：无 body · `?date=YYYY-MM-DD` 可选（默认今日，按 user timezone）

**Response 200**：
```json
{
  "date": "2026-07-17",
  "vibe": "今日 5 条 · 正常推送",
  "item_count": 5,
  "items": [
    {
      "id": "uuid-1",
      "rank": 1,
      "title": "DeepSeek V4 Pro 永久降价至原价 1/4",
      "summary": "缓存命中输入 0.025 元/M tokens...",
      "quality_score": 4.8,
      "type": "model",
      "region": "domestic",
      "category": "headline",
      "source_name": "DeepSeek Docs",
      "source_url": "https://api-docs.deepseek.com/news/...",
      "published_at": "2026-07-17T06:30:00+08:00",
      "estimated_minutes": 3,
      "is_read": false,
      "is_bookmarked": false,
      "related_item_ids": []
    }
  ]
}
```

**错误码**：`404 NOT_FOUND`（今日 digest 未生成）/ `500 INTERNAL_ERROR`

---

#### GET /api/digest/daily/{date}

**作用**：某天完整 digest · 含每条详情（spec R9 引用溯源）

**Path 参数**：`date=YYYY-MM-DD`（按 user timezone 解释）

**Response 200**：同 `/today` · 多了 `related_digest_ids` 字段

```json
{
  "date": "2026-07-17",
  "vibe": "...",
  "items": [
    {
      "id": "uuid-1",
      "title": "...",
      "summary": "...",
      "source_url": "https://...",
      "published_at": "2026-07-17T06:30:00+08:00",
      "related_item_ids": ["uuid-old-1", "uuid-old-2"]
    }
  ]
}
```

**错误码**：`404 NOT_FOUND`

---

#### GET /api/digest/dailies?limit=7

**作用**：最近 N 天 digest 列表（用于"历史"页面）

**Query 参数**：
- `limit` (int, default=7, max=30) — 返回天数
- `offset` (int, default=0) — 跳过 N 天

**Response 200**：
```json
{
  "total": 30,
  "items": [
    { "date": "2026-07-17", "vibe": "...", "item_count": 5 },
    { "date": "2026-07-16", "vibe": "...", "item_count": 5 }
  ]
}
```

**错误码**：`400 INVALID_PARAMS`（limit 越界）

---

#### GET /api/digest/weekly/{week}  *(Phase 2)*

**Path 参数**：`week=YYYY-Www`（ISO week · 例 `2026-W29`）

**Response 200**：类似 `/daily` 但 date 字段为 `week`，字段含 `top5_events` + `trends` + `outlook`

---

#### GET /api/digest/monthly/{month}  *(Phase 2)*

**Path 参数**：`month=YYYY-MM`（例 `2026-07`）

**Response 200**：类似 `/weekly`，含 `top3_events` + `trends` + `paper_summaries`

---

### 3.B · Bookmarks（3 个 · MVP）

#### GET /api/digest/bookmarks

**作用**：我的收藏列表 · 含筛选和排序

**Query 参数**：
- `type` (optional: model|application) — 按内容类型筛
- `sort` (default: `bookmarked_desc`) — 排序：`bookmarked_desc` / `quality_desc` / `published_desc`

**Response 200**：
```json
{
  "total": 18,
  "items": [
    {
      "item_id": "uuid-1",
      "title": "Claude 4.7 Sonnet 发布...",
      "summary": "...",
      "type": "model",
      "region": "overseas",
      "source_name": "Anthropic News",
      "source_url": "https://...",
      "quality_score": 4.9,
      "bookmarked_at": "2026-07-17T12:45:00+08:00",
      "published_at": "2026-07-17T04:30:00+08:00"
    }
  ]
}
```

**错误码**：`400 INVALID_PARAMS`（type 不合法）

---

#### POST /api/digest/bookmarks

**作用**：收藏某条 digest（spec R10 行为反馈）

**Request body**：
```json
{ "item_id": "uuid-1" }
```

**Schema**：
```python
class BookmarkCreate(BaseModel):
    item_id: str  # UUID format
```

**Response 201**：
```json
{
  "id": "uuid-bm-1",
  "user_id": 42,
  "item_id": "uuid-1",
  "created_at": "2026-07-17T13:02:00+08:00"
}
```

**错误码**：
- `400 INVALID_PARAMS`（item_id 非 UUID）
- `404 NOT_FOUND`（item 不存在）
- `409 CONFLICT`（已 bookmark 过同一 item → spec R5 unique 约束）

---

#### DELETE /api/digest/bookmarks/{item_id}

**作用**：取消收藏

**Path 参数**：`item_id`（UUID）

**Response 204**（无 body）

**错误码**：`404 NOT_FOUND`（未 bookmark 过）

---

### 3.C · Behavior Tracking（2 个 · MVP）

#### POST /api/digest/read

**作用**：标记已读 + 上报阅读时长（spec R7 已读标记 + R10 阅读时长进 LLM prompt）

**Request body**：
```json
{
  "item_id": "uuid-1",
  "duration_sec": 120
}
```

**Schema**：
```python
class ReadCreate(BaseModel):
    item_id: str = Field(regex=r"^[0-9a-f-]{36}$")  # UUID
    duration_sec: int = Field(ge=0, le=86400)  # ≤ 24h
```

**Response 200**：
```json
{
  "item_id": "uuid-1",
  "read_at": "2026-07-17T14:30:00+08:00",
  "duration_sec": 120,
  "progress": "5/10"  # 用户总进度（今日已读/10 条）
}
```

**错误码**：
- `400 INVALID_PARAMS`（duration_sec < 0 或 > 86400）
- `404 NOT_FOUND`（item 不存在）
- `409 CONFLICT`（spec R10 unique constraint · 同一 item 第二次 POST）

> **注**：duration_sec < 30 秒不上报已读状态（spec R7 已读标记 · 边界 case）

---

#### POST /api/digest/hide

**作用**：🔇 屏蔽某条 + LLM 提取关键词（spec R5 hide 场景）

**Request body**：
```json
{
  "item_id": "uuid-1",
  "reason": "not_interested",
  "topic_keywords": ["Claude", "Anthropic"]
}
```

**Schema**：
```python
class HideCreate(BaseModel):
    item_id: str
    reason: Literal["not_interested", "low_quality", "already_seen"]
    topic_keywords: list[str] = Field(max_length=5)
    # 业务：topic_keywords 必走白名单过滤（仅 [a-zA-Z0-9一-龥]）防 prompt 注入
```

**Response 200**：
```json
{
  "hide_id": "uuid-hide-1",
  "item_id": "uuid-1",
  "topic_keywords": ["Claude", "Anthropic"],
  "expires_at": "2026-07-24T14:30:00+08:00",
  "message": "7 天内同类内容权重 -50%"
}
```

**错误码**：
- `400 INVALID_PARAMS`（reason 不合法 / keywords > 5）
- `404 NOT_FOUND`

---

### 3.D · Sources（3 个 · MVP）

#### GET /api/digest/sources

**作用**：信源列表（spec R2 · 系统默认 8 + 用户自定义 N）

**Query 参数**：
- `enabled` (optional bool) — 仅看启用中
- `include_system` (default true) — 是否含系统默认源

**Response 200**：
```json
{
  "system_count": 8,
  "user_count": 4,
  "items": [
    {
      "id": "uuid-src-1",
      "user_id": null,  // null = 系统默认
      "name": "Anthropic News",
      "url": "https://www.anthropic.com/news/rss.xml",
      "category": "model",
      "type": "model",
      "region": "overseas",
      "enabled": true,
      "is_default": true,
      "last_fetched_at": "2026-07-17T12:00:00+08:00",
      "last_item_count": 12
    }
  ]
}
```

**错误码**：无

---

#### POST /api/digest/sources

**作用**：添加自定义 RSS 源（spec R5 用户自定义）

**Request body**：
```json
{
  "name": "稀土掘金 LLM tag",
  "url": "https://rsshub.app/juejin/tag/LLM",
  "category": "model",
  "type": "model",
  "region": "domestic"
}
```

**Schema**：
```python
class DigestSourceCreate(BaseModel):
    name: str = Field(max_length=128, min_length=1)
    url: HttpUrl  # 业务：必须 http/https · 服务端校验 RSS 格式
    category: Literal["model", "application"]  # 来源类别
    type: Literal["model", "application"]       # 内容类型（双轴标签）
    region: Literal["domestic", "overseas"]    # 地域（双轴标签）
```

**Response 201**：
```json
{
  "id": "uuid-src-new",
  "user_id": 42,
  "name": "稀土掘金 LLM tag",
  "url": "https://rsshub.app/juejin/tag/LLM",
  "enabled": true,
  "is_default": false,
  "created_at": "2026-07-17T13:30:00+08:00"
}
```

**错误码**：
- `400 INVALID_PARAMS`（URL 不可达 / 非 RSS 格式）
- `409 CONFLICT`（同一 URL 已存在 · spec R5 unique constraint）

---

#### PATCH /api/digest/sources/{id}

**作用**：编辑源（启停 / 改名 / 删除）

**Path 参数**：`id`（UUID）

**Request body**（部分更新）：
```json
{
  "enabled": false,
  "name": "稀土掘金 LLM 标签 (renamed)"
}
```

**Schema**：
```python
class DigestSourceUpdate(BaseModel):
    enabled: bool | None = None
    name: str | None = Field(default=None, max_length=128)
    # 软删除通过 enabled=false 表达 · 真删除是另一 endpoint（暂不实现）
```

**Response 200**：
```json
{
  "id": "uuid-src-new",
  "enabled": false,
  "name": "稀土掘金 LLM 标签 (renamed)"
}
```

**错误码**：
- `400 INVALID_PARAMS`
- `403 FORBIDDEN`（尝试改别人的 source · spec R5 独立性）
- `404 NOT_FOUND`

---

### 3.E · Settings（2 个 · MVP）

#### GET /api/digest/settings

**作用**：读取当前用户推送设置（spec R5 + R6）

**Response 200**：
```json
{
  "user_id": 42,
  "push_hour": 8,
  "push_minute": 0,
  "push_timezone": "Asia/Shanghai",
  "email_enabled": true,
  "macos_enabled": false,
  "interested_tags": ["Agent", "LLM"],
  "blocked_tags": ["元宇宙"],
  "daily_count": 5,
  "weekend_pause": false,
  "updated_at": "2026-07-15T10:00:00+08:00"
}
```

**Schema**：
```python
class DigestSettings(BaseModel):
    user_id: UUID
    push_hour: int = Field(ge=0, le=23, default=8)
    push_minute: int = Field(ge=0, le=59, default=0)
    push_timezone: str = Field(default="Asia/Shanghai", regex=r"^[A-Za-z]+/[A-Za-z_]+$")  # IANA tz
    email_enabled: bool = True
    macos_enabled: bool = False
    interested_tags: list[str] = Field(default=[], max_length=10)
    blocked_tags: list[str] = Field(default=[], max_length=10)
    daily_count: Literal[3, 5] = 5  # MVP 固定 5
    weekend_pause: bool = False
```

**错误码**：`404 NOT_FOUND`（用户无 settings · 返回默认值 → 自动创建）

---

#### PATCH /api/digest/settings

**作用**：更新设置（spec R5 + R6 · 部分更新）

**Request body**：
```json
{
  "push_hour": 7,
  "push_minute": 30,
  "interested_tags": ["Agent", "LLM", "MoE"]
}
```

**Schema**：`DigestSettings` 的部分字段（所有 optional）

**Response 200**：
```json
{
  "push_hour": 7,
  "push_minute": 30,
  "push_timezone": "Asia/Shanghai",  // 未改字段保留
  "email_enabled": true,
  ...
}
```

**错误码**：
- `400 INVALID_PARAMS`（tags > 10 / hour 越界 / 时区非法）
- `404 NOT_FOUND`（用户不存在）

---

### 3.F · Obsidian Sync（1 个 · Phase 2）

#### POST /api/digest/sync-to-obsidian  *(Phase 2)*

**作用**：将今日 digest 写回 Obsidian vault

**Request body**：
```json
{
  "digest_id": "uuid-daily-1",
  "vault_root": "~/Obsidian/coding",
  "target_folder": "ai/"
}
```

**Response 202**：
```json
{
  "file_path": "~/Obsidian/coding/ai/AI 日报 2026-07-17.md",
  "written_at": "2026-07-17T08:05:00+08:00"
}
```

**错误码**：`404` / `500 INTERNAL_ERROR`（vault 不可达）

---

## § 4 · 接口依赖关系

```
GET /api/digest/today
  ├─ 读 digest_daily (by user_id + date)
  ├─ 读 digest_daily_item (by daily_id, order by rank)
  └─ 缓存键 digest:today:{user_id}:{date} · TTL 5min

POST /api/digest/bookmarks
  ├─ 校验 item 存在（digest_daily_item）
  └─ 写 digest_bookmark（unique: user_id + item_id）

POST /api/digest/hide
  ├─ 校验 item 存在
  ├─ topic_keywords 白名单过滤（防 prompt 注入）
  └─ 写 digest_hide（expires_at = now + 7 days）

POST /api/digest/sources
  ├─ 校验 URL 可达 + RSS 格式（HEAD request + 解析 first item）
  └─ 写 digest_source（unique: user_id + url）

PATCH /api/digest/settings
  └─ 写 digest_settings（upsert）
```

---

## § 5 · 测试要点

### 5.1 通用场景（每个 endpoint 都测）

- [ ] 正常请求返回 200/201/204 + 正确响应
- [ ] 未带 token 返回 401 UNAUTHORIZED
- [ ] 过期 token 返回 401
- [ ] 限流触发返回 429 + Retry-After

### 5.2 关键 endpoint

| endpoint | 关键测试点 |
|---|---|
| `GET /api/digest/today` | today 未生成返回 404 · 时区切换后 date 字段按 user tz |
| `POST /api/digest/bookmarks` | 重复收藏返回 409 · item_id 不存在返回 404 |
| `DELETE /api/digest/bookmarks/{id}` | 未 bookmark 返回 404 · 别人的 bookmark 返回 403 |
| `POST /api/digest/read` | duration_sec < 30 不上报已读 · > 86400 返回 400 |
| `POST /api/digest/hide` | topic_keywords 含 emoji / 特殊字符被白名单过滤 |
| `POST /api/digest/sources` | URL 不可达返回 400 · 重复 URL 返回 409 |
| `PATCH /api/digest/sources/{id}` | 改别人的 source 返回 403 |
| `PATCH /api/digest/settings` | tags > 10 返回 400 · 时区非法返回 400 |

### 5.3 集成场景

- [ ] 完整 push 流程：cron → 抓 RSS → LLM 选题 → 写 DB → 发邮件 → 用户 GET /today 看到
- [ ] 屏蔽后 7 天：第 8 天 verify hide 已 expires · LLM 选题恢复
- [ ] bookmark 跨日：昨天 bookmark 的 digest，今天 GET /bookmarks 仍能看到
- [ ] 多设备：用户 A 设备 bookmark 后，B 设备 GET /bookmarks 同步看到

---

## 🎯 硬性 DOD 自检

- [x] 接口清单完整（16 个 · method + path + 作用 + 阶段）
- [x] 每个接口 3 段齐全（Request / Response / 错误码）
- [x] 错误码 ≥ 4 类（400 / 401 / 403 / 404 / 409 / 429 / 500）
- [x] 通用规范明确（认证 / 限流 / 时间 / 分页 / 错误格式）
- [x] 测试要点覆盖核心场景

---

## 📚 相关文档

- [spec.md](spec.md) — 上游：技术契约（10 Requirements + 34 Scenarios）
- [db-design.md](db-design.md) — 配套：9 表 schema + 迁移 SQL
- [component-spec.md](component-spec.md) — 前端组件规格
- [plan.md](plan.md) — **下一步**：技术方案对比 + 推荐
- [product-doc.md](product-doc.md) — 上游：产品意图

---

## 元信息

- **文档版本**：v1 · 2026-07-17
- **路径**：`docs/tasks/2026-07-17-new-feature-ai-push/api-spec.md`
- **下一步**：写 plan.md（技术方案对比 + 推荐 · 含 DB / ORM / RSSHub / cron / 部署方案）
- **MVP 范围**：13 个 endpoint（A-1/2/3, B 全部, C 全部, D 全部, E 全部）
- **Phase 2 范围**：3 个 endpoint（A-4/5, F）
