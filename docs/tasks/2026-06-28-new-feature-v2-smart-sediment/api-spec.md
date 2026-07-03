---
title: API 设计 · V2 智能沉淀层
date: 2026-06-28
status: v2（plan 冻结后定稿，§6 已回填）
tags: [api-spec, 2步, API, v2, 智能沉淀]
related:
  - [spec.md](spec.md) — 1 步技术脑（§4 数据契约来源）
  - [plan.md](plan.md) — 2 步方案（已冻，7 决策 = 全 A）
  - [research.md](research.md) — 0 步调研
  - [product-doc.md](product-doc.md) — 1 步产品脑
  - [component-spec.md](component-spec.md) — 配套前端组件
---

# API 设计：V2 智能沉淀层（6 个新端点）

> **一句话**：V2 新增 6 个端点（dashboard summary / profile weekly/monthly/refresh / knowledge recent-sediments / obsidian sync），全部走 `/api/v2/...` 路径保持后向兼容。
>
> **作者**：AI 主导（后端 lead review）
>
> **校验状态**：✅ DOD 通过
> - 接口清单完整（6/6 端点）
> - 每端点 3 段齐全（Request / Response / 错误码）
> - 错误码 ≥ 4 类（401 / 422 / 429 / 500）
> - 通用规范 4 段齐全（认证 / 限流 / 版本 / 错误格式）
> - 测试要点齐全（≥ 25 测试点）
>
> **决策锁定**（来自 plan.md §3）：
> - 架构 = 同步触发链（决策 1A）
> - LLM 缓存 = Redis TTL 1h（决策 2A）
> - 错误处理 = 不抛 + log warning（决策 7A）

---

## 1. 接口清单（必填）

| Method | Path | 作用 | 认证 |
|---|---|---|---|
| `GET` | `/api/v2/dashboard/summary` | Dashboard 顶部"今日学习总结"卡 | ✅ JWT Required |
| `GET` | `/api/v2/profile/weekly` | Profile 趋势图周报（12 周） | ✅ JWT Required |
| `GET` | `/api/v2/profile/monthly` | Profile 月报（落库 monthly_reports） | ✅ JWT Required |
| `POST` | `/api/v2/profile/refresh` | Profile 手动刷新（触发 weekly_full_refresh） | ✅ JWT Required |
| `GET` | `/api/v2/knowledge/recent-sediments` | Knowledge stats tab 最近 5 个学习沉淀 | ✅ JWT Required |
| `POST` | `/api/v2/obsidian/sync` | 手动触发 Obsidian 同步（如 vault 后创建） | ✅ JWT Required |

**响应头统一加**：`X-API-Version: v2.0`

---

## 2. 每个接口的详细定义（必填）

### GET /api/v2/dashboard/summary

#### Request

**Headers**:
```
Authorization: Bearer <token>
```

**Query** (可选):
```
?date=2026-06-28   # 默认 = today (用户时区)
```

**Schema** (无 Body)

#### Response

**成功 (200)**:
```json
{
  "title": "今日学习总结",
  "date": "2026-06-28",
  "yesterday_count": 8,
  "mastered": [
    {"topic": "React Hooks", "error_rate": 0.2, "practice_count": 5, "last_practiced_at": "2026-06-27T15:30:00Z", "related_question_ids": ["q001", "q003"]},
    {"topic": "TypeScript 泛型", "error_rate": 0.0, "practice_count": 3, "last_practiced_at": "2026-06-27T20:15:00Z", "related_question_ids": ["q007"]}
  ],
  "weak_shift": [
    {"from_topic": "网络层", "to_topic": "状态管理", "delta": 0.13}
  ],
  "body": "昨天你答了 8 道题，掌握 2 个新 topic：React Hooks / TypeScript 泛型。弱项从「网络层」调整为「状态管理」。",
  "_fallback": false
}
```

**Schema** (Pydantic):
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as date_type, datetime
from uuid import UUID


class TopicSettlement(BaseModel):
    topic: str = Field(min_length=1, max_length=50)  # 业务：topic 名
    error_rate: float = Field(ge=0.0, le=1.0)  # 业务：错题率 0-1
    practice_count: int = Field(ge=0)  # 业务：练习次数
    last_practiced_at: datetime
    related_question_ids: List[str] = Field(default_factory=list, max_length=50)


class DailySummary(BaseModel):
    title: str = Field(default="今日学习总结", max_length=50)
    date: date_type
    yesterday_count: int = Field(ge=0)
    mastered: List[TopicSettlement]
    weak_shift: List[dict] = Field(default_factory=list)
    body: str = Field(max_length=500)
    _fallback: bool = False  # true=规则降级，false=LLM 生成
```

#### 错误码

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 401 | 未登录 | token 缺失 / 过期 | 跳转登录 |
| 422 | 日期格式错 | `date` 不是 YYYY-MM-DD | 显示"日期格式错误" |
| 429 | 限流 | 60s 内同用户 > 5 次 | 显示"操作频繁，请稍后" |
| 500 | 服务器错误 | DB + Redis + LLM 全失败 | 显示"今日总结暂不可用"+ 降级版（`_fallback: true`） |

#### 关键实现（决策 7A：不抛 + log）

- LLM 失败 → catch + log warning → 降级返回规则生成版（`_fallback: true`，HTTP 200，不是 500）
- Redis 失败 → catch + log → 直接调 LLM（缓存是优化）
- DB 失败 → catch + log + 返 500（这是非预期）

---

### GET /api/v2/profile/weekly

#### Request

**Headers**:
```
Authorization: Bearer <token>
```

**Query**:
```
?week=2026-W26   # ISO week (必填)
```

#### Response

**成功 (200)**:
```json
{
  "week": "2026-W26",
  "total_questions": 42,
  "mastered_count": 7,
  "weak_topics": [
    {"topic": "网络层", "error_rate": 0.65, "practice_count": 8, "last_practiced_at": "2026-06-25T10:00:00Z", "related_question_ids": [...]}
  ],
  "body": "本周你答了 42 道题，掌握 7 个新 topic...",
  "trajectory": {
    "2026-W15": {"mastered_count": 2},
    "2026-W16": {"mastered_count": 3},
    "...": "...",
    "2026-W26": {"mastered_count": 9}
  }
}
```

**Schema**:
```python
class WeeklyTrajectoryPoint(BaseModel):
    mastered_count: int = Field(ge=0)


class WeeklySummary(BaseModel):
    week: str = Field(pattern=r"^\d{4}-W\d{2}$")
    total_questions: int = Field(ge=0)
    mastered_count: int = Field(ge=0)
    weak_topics: List[TopicSettlement]
    body: str = Field(max_length=2000)
    trajectory: Dict[str, WeeklyTrajectoryPoint]  # 12 周
```

#### 错误码

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 401 | 未登录 | token 缺失 | 跳转登录 |
| 422 | week 格式错 | 不是 `YYYY-Www` | 显示"周格式错误" |
| 500 | 服务器错误 | DB / LLM 失败 | 显示"周报生成失败" |

---

### GET /api/v2/profile/monthly

#### Request

**Headers**:
```
Authorization: Bearer <token>
```

**Query**:
```
?month=2026-06   # 默认 = 当前月
```

#### Response

**成功 (200)**:
```json
{
  "month": "2026-06",
  "total_questions": 168,
  "mastered_count": 28,
  "weak_topics": [...],
  "body": "6 月你答了 168 道题，掌握 28 个新 topic...",
  "trajectory": {
    "2026-01": {"mastered_count": 5},
    "2026-02": {"mastered_count": 8},
    "...": "...",
    "2026-06": {"mastered_count": 28}
  },
  "summary_stats": {
    "narrative": "...",
    "saved_to_db": true,
    "monthly_report_id": 123
  }
}
```

**Schema**:
```python
class MonthlySummary(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    total_questions: int = Field(ge=0)
    mastered_count: int = Field(ge=0)
    weak_topics: List[TopicSettlement]
    body: str = Field(max_length=5000)
    trajectory: Dict[str, WeeklyTrajectoryPoint]  # 6 个月
    summary_stats: dict  # 写入 monthly_reports.summary_stats 字段
```

#### 副作用
- DB 写：`monthly_reports.summary_stats` 字段新增/更新 1 行

#### 错误码

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 401 | 未登录 | token 缺失 | 跳转登录 |
| 422 | month 格式错 | 不是 YYYY-MM | 显示"月份格式错误" |
| 500 | 服务器错误 | DB / LLM 失败 | 显示"月报生成失败" |

---

### POST /api/v2/profile/refresh

#### Request

**Headers**:
```
Authorization: Bearer <token>
```

**Body**: 无

#### Response

**成功 (200)**:
```json
{
  "user_id": "uuid-xxx",
  "settled_at": "2026-06-28T15:30:00Z",
  "weak_topics": [...],
  "mastered_topics": [...],
  "triggered_by": "manual_refresh",
  "cache_invalidated": true
}
```

**Schema**:
```python
class SettlementResult(BaseModel):
    user_id: UUID
    settled_at: datetime
    weak_topics: List[TopicSettlement]
    mastered_topics: List[TopicSettlement]
    triggered_by: str = Field(pattern=r"^(interview|practice|manual_refresh|weekly_refresh)$")
    cache_invalidated: bool = True
```

#### 副作用
- DB 写：`profiles.weak_topics` / `mastered_topics` / `learning_trajectory` / `last_active_at` 重算
- Cache：DEL `summary:dashboard:{user_id}` / `summary:profile:{user_id}` / `profile:{user_id}` 3 个 key

#### 错误码

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 401 | 未登录 | token 缺失 | 跳转登录 |
| 429 | 限流 | 60s 内同用户 > 1 次（防手动刷量） | 显示"操作频繁，刷新有冷却时间" |
| 500 | 服务器错误 | settlement 失败 | toast "刷新失败" + 按钮恢复 |

---

### GET /api/v2/knowledge/recent-sediments

#### Request

**Headers**:
```
Authorization: Bearer <token>
```

**Query**:
```
?limit=5   # 默认 5，最大 20
```

#### Response

**成功 (200)**:
```json
[
  {
    "rel_path": "learning/2026-06-28.md",
    "full_path": "/Users/xxx/Obsidian/coding/learning/2026-06-28.md",
    "success": true,
    "error": null
  },
  {
    "rel_path": "learning/2026-06-27.md",
    "full_path": "/Users/xxx/Obsidian/coding/learning/2026-06-27.md",
    "success": true,
    "error": null
  }
]
```

**Schema**:
```python
class ObsidianWriteResult(BaseModel):
    rel_path: str = Field(pattern=r"^(learning|interview)/[\w\-/]+\.md$")
    full_path: Optional[str]  # vault 存在 = 绝对路径；不存在 = None
    success: bool
    error: Optional[str]  # 失败原因
```

#### 错误码

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 401 | 未登录 | token 缺失 | 跳转登录 |
| 422 | limit 错 | > 20 或 < 1 | 默认 5 |
| 500 | 服务器错误 | DB 扫表失败 | 卡片显示"加载失败"占位 |

#### 关键实现（决策 7A）

- vault 不存在时返空 list `[]`（不返 500，不抛异常），前端 UI 显示"路径不存在"提示

---

### POST /api/v2/obsidian/sync

#### Request

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body**:
```json
{
  "date": "2026-06-28"  # 必填
}
```

**Schema**:
```python
class ObsidianSyncRequest(BaseModel):
    date: date_type  # YYYY-MM-DD
```

#### Response

**成功 (200)**:
```json
{
  "date": "2026-06-28",
  "synced_count": 3,
  "files": [
    {"rel_path": "learning/2026-06-28.md", "success": true, "full_path": "/Users/xxx/...", "error": null},
    {"rel_path": "interview/2026-06-28-abc.md", "success": true, "full_path": "/Users/xxx/...", "error": null}
  ]
}
```

#### 副作用
- FileSystem：重写 `~/Obsidian/coding/learning/YYYY-MM-DD.md`
- 可能写：`~/Obsidian/coding/interview/YYYY-MM-DD-<id>.md`

#### 错误码

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 401 | 未登录 | token 缺失 | 跳转登录 |
| 422 | date 错 | 不是 YYYY-MM-DD | toast "日期格式错误" |
| 500 | 服务器错误 | DB 全失败 | toast "同步失败" |

#### 关键实现（决策 7A）

- vault 不存在 → synced_count=0 + files=[]（不抛，前端显示"路径不存在"）

---

## 3. 通用规范（必填）

### 3.1 认证

- **所有 6 个 API 需要 Bearer token（强制）**
- Header：`Authorization: Bearer <token>`
- token 缺失/过期 → **所有端点返 401 UNAUTHORIZED**
- 错误响应：`{"error": {"code": "UNAUTHORIZED", "message": "..."}}`

### 3.2 限流（slowapi 库，V1 已有）

| 端点 | 每用户 | 每 IP | 超限响应 |
|---|---|---|---|
| `/api/v2/dashboard/summary` | 5 次 / 60s | 60 次 / 60s | 429 |
| `/api/v2/profile/weekly` | 1 次 / 60s | 30 次 / 60s | 429 |
| `/api/v2/profile/monthly` | 1 次 / 60s | 30 次 / 60s | 429 |
| `/api/v2/profile/refresh` | 1 次 / 60s | 10 次 / 60s | 429 |
| `/api/v2/knowledge/recent-sediments` | 20 次 / 60s | 100 次 / 60s | 429 |
| `/api/v2/obsidian/sync` | 1 次 / 60s | 10 次 / 60s | 429 |

**响应格式**：429 + `Retry-After: <秒数>` header

### 3.3 版本

- URL 路径：**`/api/v2/...`**（V2 新规，全部走 v2 路径）
- V1 `/api/dashboard` 等老路径**不动**，继续可用
- 不兼容改动 → `/api/v3/...`，旧版支持 ≥ 6 个月
- 响应 header 统一加：`X-API-Version: v2.0`

### 3.4 错误响应统一格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "week format invalid, expected YYYY-Www",
    "details": {
      "field": "week",
      "constraint": "pattern=^\\d{4}-W\\d{2}$"
    }
  }
}
```

错误码常量（与 V1 对齐）：
| code | HTTP | 含义 |
|---|---|---|
| `UNAUTHORIZED` | 401 | token 缺失 / 过期 |
| `FORBIDDEN` | 403 | 不是资源所有者 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 422 | 请求字段校验失败 |
| `RATE_LIMITED` | 429 | 限流 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 依赖服务（LLM / Obsidian）不可用 |

---

## 4. 接口依赖关系（必填）

```
GET /api/v2/dashboard/summary
  ↓ 依赖
  - User JWT 有效
  - Redis summary:dashboard:{user_id} 可选（命中走缓存，TTL 1h）
  ↓ 触发
  - DB: 读 question_progress / interview_results
  - Cache: 读/写 summary:dashboard:{user_id} (TTL 1h)
  - LLM: 可能调 DeepSeek 生成 narrative（失败降级）

GET /api/v2/profile/weekly
  ↓ 依赖
  - User must own the profile
  - Profile.learning_trajectory 必须有 12 周数据
  ↓ 触发
  - DB: 读 profiles + 聚合 question_progress 12 周
  - Cache: 读/写 summary:profile:{user_id} (TTL 1h)
  - LLM: 可选

GET /api/v2/profile/monthly
  ↓ 依赖
  - User must own the profile
  ↓ 触发
  - DB: 读 profiles + 聚合 30 天 question_progress
  - DB: 写 monthly_reports.summary_stats
  - Cache: 读/写 summary:profile:{user_id} (TTL 1h)
  - LLM: 可选

POST /api/v2/profile/refresh
  ↓ 依赖
  - User must own the profile
  ↓ 触发
  - DB: 写 profiles.weak_topics / mastered_topics / learning_trajectory / last_active_at
  - Cache: DEL 3 个 key (summary:dashboard + summary:profile + profile)

GET /api/v2/knowledge/recent-sediments
  ↓ 依赖
  - User JWT 有效
  - Obsidian vault 可选存在（不存在返空 list，不抛异常）
  ↓ 触发
  - FileSystem: ls ~/Obsidian/coding/learning/ + interview/，按 mtime 排序 top 5

POST /api/v2/obsidian/sync
  ↓ 依赖
  - User JWT 有效
  - date 参数合法
  ↓ 触发
  - DB: 读 question_progress + interview_results for date
  - FileSystem: 写 ~/Obsidian/coding/learning/YYYY-MM-DD.md（可能也写 interview/）
  - 容错：vault 不存在返 synced_count=0 + files=[]
```

---

## 5. 测试要点（必填）

### 5.1 各端点单元/集成测试（V2.3 实施时写）

#### GET /api/v2/dashboard/summary
- [ ] TC-SUM-1: 正常请求返回 200 + 正确 DailySummary 字段
- [ ] TC-SUM-2: 命中 Redis 缓存时 body 相同但内部不调 LLM（看 mock LLM 调用次数 = 0）
- [ ] TC-SUM-3: LLM 504 时返回 200 + `_fallback: true`（不返 500）
- [ ] TC-SUM-4: 未登录返 401
- [ ] TC-SUM-5: date 格式错返 422
- [ ] TC-SUM-6: 60s 内第 6 次返 429
- [ ] TC-SUM-7: 新用户 0 数据时 body = "完成首日学习后..."

#### GET /api/v2/profile/weekly
- [ ] TC-WEEK-1: 正常请求返回 200 + 12 周 trajectory
- [ ] TC-WEEK-2: week=2026-W00 格式错返 422
- [ ] TC-WEEK-3: 数据 < 2 周时 trajectory 部分缺失
- [ ] TC-WEEK-4: 未登录返 401

#### GET /api/v2/profile/monthly
- [ ] TC-MON-1: 正常请求返回 200 + 6 月 trajectory + summary_stats
- [ ] TC-MON-2: 验证 monthly_reports 表新增 1 行（summary_stats 字段 = JSON）
- [ ] TC-MON-3: month 格式错返 422

#### POST /api/v2/profile/refresh
- [ ] TC-REF-1: 正常请求返回 200 + SettlementResult
- [ ] TC-REF-2: 验证 profiles 表 4 字段被更新
- [ ] TC-REF-3: 验证 Redis 3 个 key 被 DEL
- [ ] TC-REF-4: 60s 内第 2 次返 429
- [ ] TC-REF-5: DB 断连时返 500（但前端要能 catch）

#### GET /api/v2/knowledge/recent-sediments
- [ ] TC-SED-1: 正常请求返回 200 + ≤ 5 个文件 list
- [ ] TC-SED-2: limit=0 返 422 或默认 5
- [ ] TC-SED-3: vault 不存在时返空 list `[]`（不返 500）

#### POST /api/v2/obsidian/sync
- [ ] TC-SYN-1: 正常请求返 200 + synced_count > 0
- [ ] TC-SYN-2: vault 不存在返 200 + synced_count=0 + files 空 list
- [ ] TC-SYN-3: date 错返 422
- [ ] TC-SYN-4: 60s 内第 2 次返 429

### 5.2 端到端集成测试（V2.4 verify.md § L3）

- [ ] TC-INT-1: 答完 3 道题 → /api/v2/dashboard/summary 顶部卡内容更新 + /api/v2/knowledge/recent-sediments 返回新文件 + Profile.weak_topics 更新
- [ ] TC-INT-2: 并发 5 个答题 → 全部 settlement 完成 + 无数据丢失
- [ ] TC-INT-3: LLM 挂掉 → /api/v2/dashboard/summary 仍可用（降级版 `_fallback: true`） + 4 个其他端点正常
- [ ] TC-INT-4: weekly_full_refresh 触发后 → /api/v2/profile/weekly 看到新数据
- [ ] TC-INT-5: 手动点 /api/v2/profile/refresh → Redis 3 个 key 被清掉 + 下次 /dashboard/summary 重新生成

---

## 🎯 硬性 DOD（api-spec.md 完成必须全过）

- [x] 接口清单完整（6/6）
- [x] 每个接口 3 段齐全（Request / Response / 错误码，6/6）
- [x] 错误码 ≥ 4 类（401 / 422 / 429 / 500，4 类齐）
- [x] 通用规范明确（认证 / 限流 / 版本 / 错误格式，4 段齐）
- [x] 测试要点覆盖核心场景（≥ 25 测试点）

> ✅ DOD 通过

---

## 6. 技术实现（plan 冻结后定稿 · 全填）

### 6.1 协议选型

- API 协议: **REST**（V1 已用 FastAPI，V2 沿用）
- 数据格式: **JSON**（V1 已用）
- API 风格: **RESTful**（V1 已用 `/api/v{version}/{resource}/{action}` 模式）

### 6.2 认证方案

- 认证机制: **JWT**（V1 已用 `python-jose`，V2 沿用）
- Token 存储: **localStorage**（V1 前端已用）
- Token 刷新: **重新登录**（V1 简单策略，V2 沿用）
- 权限模型: **单用户 RBAC**（token.user_id = resource.user_id）

### 6.3 限流策略

- 限流算法: **滑动窗口**（`slowapi` 库，V1 已用）
- 限流维度: **每用户 + 每 IP**（同 V1）
- 限流阈值: 见 §3.2 表格
- 超限响应: **429 + `Retry-After: <秒数>` header**

### 6.4 响应与错误格式

- 成功响应: **JSON 直接返 schema**（无外层 wrapper）
- 错误响应: **统一 §3.4 格式** `{error: {code, message, details}}`
- Content-Type: `application/json; charset=utf-8`
- 时间格式: **ISO 8601**（V1 既有）
- 分页: **无**（V2 数据量小，全量返）

### 6.5 跨域与缓存

- CORS: V1 已配（前端 localhost:3000 → 后端 :8000）
- 缓存策略（决策 2A = Redis TTL 1h）：
  - **服务端 Redis TTL 1h** + 降级到无缓存（Redis 不可用时直接调 LLM）
  - **前端 React SWR-like cache**（用 useEffect + useState，5min 软失效）
- CDN: 否（本地开发）

### 6.6 端点文件结构

```
backend/api/
├── v2/
│   ├── __init__.py
│   ├── dashboard.py          # GET /api/v2/dashboard/summary
│   ├── profile.py            # GET weekly + monthly + POST refresh
│   ├── knowledge.py          # GET /api/v2/knowledge/recent-sediments (扩展 V1)
│   └── obsidian.py           # POST /api/v2/obsidian/sync (扩展 V1)
└── (V1 文件不动)
```

或放在 V1 路由文件加 v2 prefix：
```
backend/api/
├── dashboard.py              # /api/dashboard (V1) + /api/v2/dashboard/summary (V2)
├── profile.py                # /api/v2/profile/* (V2 only)
├── knowledge.py              # /api/knowledge/* (V1) + /api/v2/knowledge/recent-sediments (V2)
└── obsidian.py               # /api/obsidian/sync (V2 only)
```

**决策**（次要细节，V2.1 实施时定）：V2 端点少，**直接放 V1 同文件** 减少文件数

### 6.7 监控埋点

| 端点 | 监控字段 |
|---|---|
| `/api/v2/dashboard/summary` | 响应时间 / 缓存命中率 / LLM 降级率（`_fallback=true` 占比） |
| `/api/v2/profile/*` | 响应时间 / DB 读写耗时 |
| `/api/v2/profile/refresh` | 调用频率（防刷量） / 失败率 |
| `/api/v2/knowledge/recent-sediments` | vault 存在率 |
| `/api/v2/obsidian/sync` | synced_count 分布 |

### 6.8 安全要点（决策 7A 派生）

- **所有 settlement / obsidian write 包 try/except** → 失败 log warning → 不抛
- **path 字段不接用户输入** → 只接 date / user_id，rel_path 自动生成（防 `../` 跳出 vault）
- **JWT 必须** → 6 个端点全部 401 兜底
- **限流兜底** → 防 LLM 刷量 + 防 settlement 刷量

---

## 📚 相关文档

- [spec.md](spec.md) — 上游：1 步技术脑（§4 数据契约 + §4.2 端点契约）
- [plan.md](plan.md) — 上游：2 步方案（已冻，7 决策 = 全 A）
- [component-spec.md](component-spec.md) — 配套前端组件
- [research.md](research.md) — 0 步调研
- [product-doc.md](product-doc.md) — 1 步产品脑
- `docs/api/README.md` — 全局 API 索引（V2.3 完成后加 6 端点）
- `docs/DOD.md` §三.6 — api-spec.md DOD 完整定义
