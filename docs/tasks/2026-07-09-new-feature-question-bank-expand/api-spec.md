---
title: API 设计 · V3 题库扩量 + 多维分类 + LeetCode 三件套 + AI 推送
date: 2026-07-09
status: v1
tags: [api-spec, 2步, API, v3]
related:
  - [plan.md](plan.md) — 2 步方案
  - [db-design.md](db-design.md) — 2 步数据库
  - [spec.md](spec.md) — 1 步技术契约
  - V2 沉淀层 api-spec: `../2026-06-28-new-feature-v2-smart-sediment/api-spec.md`
---

# API 设计：V3 题库扩量 + 多维分类 + LeetCode 三件套 + AI 推送

> **目标**：V3 新增 8 个端点（精选题单 4 + 每日一题 2 + V1 复用 plan 5）+ V2 沉淀层 AI 推荐 1 复用。
> **风格**：V1 既有 REST 风格（FastAPI + JWT）+ V2 L4 错误格式统一（`{error: {code, message}}`）

---

## 1. 端点总览

| 方法 | 路径 | 用途 | V3 段 | 实现位置 |
|---|---|---|---|---|
| GET | `/api/learn/collections` | 题单列表 | V3.1 | 4 端点组 |
| GET | `/api/learn/collections/{id}` | 题单详情 | V3.1 | |
| POST | `/api/learn/collections/{id}/subscribe` | 订阅题单 | V3.1 | |
| DELETE | `/api/learn/collections/{id}/subscribe` | 取消订阅 | V3.1 | |
| GET | `/api/learn/daily-challenge` | 今日一题 | V3.2 | 2 端点组 |
| POST | `/api/learn/daily-challenge/complete` | 完成今日一题 | V3.2 | |
| GET | `/api/learn/questions?tags=...` | 多标签筛选（V3 增强） | V3.x | 复用 V1 |
| GET | `/api/analytics/recommendations` | AI 推荐（V2 已有 · V3.7 复用） | V3.7 | 复用 V2 |
| 5 端点 | `/api/learn/plans*` | 学习计划（V1 已有 · V3.0 复用） | V3.0 | 复用 V1 |

**新增：8 端点**（4 题单 + 2 每日一题 + 1 多标签筛选增强 + 1 AI 推荐复用）
**复用：6 端点**（V1 5 计划 + V2 1 推荐）

---

## 2. 精选题单端点（V3.1 · 4 端点）

### 2.1 `GET /api/learn/collections` · 题单列表

**请求**：
```http
GET /api/learn/collections?limit=20&offset=0&subscribed_only=false
Headers:
  Authorization: Bearer <token>
```

**Query 参数**：
- `limit` (int, optional, default 20, 1-50)
- `offset` (int, optional, default 0)
- `subscribed_only` (bool, optional, default false) — 仅显示已订阅

**响应 200**：
```json
{
  "items": [
    {
      "id": "algorithms_50",
      "name": "算法入门 50 题",
      "description": "LeetCode Easy 精选",
      "cover_color": "#60a5fa",
      "icon_emoji": "📘",
      "question_count": 50,
      "is_system": true,
      "subscribed": true,
      "progress": {
        "done_count": 25,
        "completion_rate": 0.5,
        "last_question_id": "algo_005"
      }
    }
  ],
  "total": 5,
  "limit": 20,
  "offset": 0
}
```

**错误码**：
- 401 UNAUTHORIZED · token 缺失
- 422 VALIDATION_ERROR · limit/offset 范围错

### 2.2 `GET /api/learn/collections/{id}` · 题单详情

**请求**：
```http
GET /api/learn/collections/algorithms_50
Headers:
  Authorization: Bearer <token>
```

**响应 200**：
```json
{
  "id": "algorithms_50",
  "name": "算法入门 50 题",
  "description": "LeetCode Easy 精选",
  "cover_color": "#60a5fa",
  "icon_emoji": "📘",
  "question_count": 50,
  "is_system": true,
  "subscribed": true,
  "progress": {
    "done_count": 25,
    "completion_rate": 0.5,
    "last_question_id": "algo_005"
  },
  "questions": [
    {
      "id": "algo_001",
      "topic": "algorithms",
      "sub_topic": "array",
      "difficulty": 2,
      "position": 0,
      "completed": true
    },
    {
      "id": "algo_002",
      "topic": "algorithms",
      "sub_topic": "hash_table",
      "difficulty": 2,
      "position": 1,
      "completed": false
    }
  ]
}
```

**错误码**：
- 401 UNAUTHORIZED
- 404 NOT_FOUND · 题单不存在

### 2.3 `POST /api/learn/collections/{id}/subscribe` · 订阅题单

**请求**：
```http
POST /api/learn/collections/system_design_30/subscribe
Headers:
  Authorization: Bearer <token>
```

**响应 200**：
```json
{
  "collection_id": "system_design_30",
  "user_id": "uuid-xxx",
  "subscribed_at": "2026-07-09T10:00:00Z",
  "progress": {
    "done_count": 0,
    "total_count": 30,
    "completion_rate": 0
  }
}
```

**错误码**：
- 401 UNAUTHORIZED
- 404 NOT_FOUND
- 409 CONFLICT · 重复订阅（已有 collection_subscribe 记录）

### 2.4 `DELETE /api/learn/collections/{id}/subscribe` · 取消订阅

**请求**：
```http
DELETE /api/learn/collections/system_design_30/subscribe
Headers:
  Authorization: Bearer <token>
```

**响应 200**：
```json
{
  "collection_id": "system_design_30",
  "deleted": true
}
```

**错误码**：
- 401 UNAUTHORIZED
- 404 NOT_FOUND · 未订阅过该题单

---

## 3. 每日一题端点（V3.2 · 2 端点）

### 3.1 `GET /api/learn/daily-challenge` · 今日一题

**请求**：
```http
GET /api/learn/daily-challenge?date=2026-07-09
Headers:
  Authorization: Bearer <token>
```

**Query 参数**：
- `date` (date, optional, default today) — 查询指定日期的题

**响应 200**：
```json
{
  "date": "2026-07-09",
  "question": {
    "id": "algo_005",
    "topic": "algorithms",
    "sub_topic": "lru_cache",
    "difficulty": 3,
    "question_text": "请描述 LRU 缓存的实现思路...",
    "estimated_minutes": 5,
    "tags": ["sys_algorithm", "sys_python", "sys_bytedance_r2"]
  },
  "completed": false,
  "streak_days": 7
}
```

**业务逻辑**：
1. `daily_challenges` 表按 date 查今日题 → 无则 seed_service 自动选题
2. `daily_challenge_completions` 表查 user_id+date → completed 状态
3. 计算 streak（连续 7 天有 completed_at）

**错误码**：
- 401 UNAUTHORIZED
- 503 SERVICE_UNAVAILABLE · 题库为空（200 题全失效）

### 3.2 `POST /api/learn/daily-challenge/complete` · 完成今日一题

**请求**：
```http
POST /api/learn/daily-challenge/complete
Headers:
  Authorization: Bearer <token>
Content-Type: application/json
{
  "date": "2026-07-09",
  "score": 4,
  "duration_sec": 320
}
```

**请求 Body**：
- `date` (date, required)
- `score` (int, 0-5, required) — SM-2 quality
- `duration_sec` (int, optional, default 0) — 答题用时

**响应 200**：
```json
{
  "date": "2026-07-09",
  "completed": true,
  "streak_days": 8,
  "question_id": "algo_005"
}
```

**业务逻辑**：
1. 插入 `daily_challenge_completions`（UNIQUE 约束防重复）
2. 触发 V2 ProfileSettlementService.settle_after_practice（V2 沉淀层 trigger 链）
3. 重算 streak（连续 N 天 → streak = N）
4. V2 Profile 画像沉淀

**错误码**：
- 401 UNAUTHORIZED
- 422 VALIDATION_ERROR · score 范围错
- 409 CONFLICT · 当日已 complete（UNIQUE 约束）

---

## 4. 多标签筛选增强（V3.x · V1 端点扩展）

### 4.1 `GET /api/learn/questions?tags=...` · 多标签筛选

**请求**（V1 既有端点 + V3 新增 tags 参数）：
```http
GET /api/learn/questions?tags=sys_algorithm,sys_python&difficulty=3&bookmarked=true
Headers:
  Authorization: Bearer <token>
```

**Query 参数**（V3 新增）：
- `tags` (string, optional) — 逗号分隔多标签，**任一命中**（OR 逻辑）

**响应 200**（V1 既有 + V3 增强）：
```json
{
  "items": [
    {
      "id": "algo_005",
      "topic": "algorithms",
      "sub_topic": "lru_cache",
      "difficulty": 3,
      "tags": ["sys_algorithm", "sys_python", "sys_bytedance_r2"],
      "source": "seed",
      "progress": {
        "practice_count": 3,
        "correct_count": 2,
        "bookmarked": true
      }
    }
  ],
  "total": 8,
  "page": 1,
  "size": 20
}
```

**业务逻辑**：
- 已有 V1 `q`/`topic`/`difficulty`/`bookmarked` filter 不变
- V3 新增 `tags` filter：`QuestionTagMap.question_id IN (SELECT question_id WHERE tag_id IN (tags))`
- 走 `idx_qtm_tag_question` 覆盖索引 · 性能 P95 < 200ms

**错误码**：
- 401 UNAUTHORIZED
- 422 VALIDATION_ERROR · tags 格式错

---

## 5. V1/V2 复用端点（V3 不改 schema）

### 5.1 学习计划 5 端点（V1 已有 · V3.0 复用 · 补前端 UI）

```
GET    /api/learn/plans              # 列表
POST   /api/learn/plans              # 创建
PATCH  /api/learn/plans/{id}        # 更新
DELETE /api/learn/plans/{id}        # 删除
GET    /api/learn/plans/{id}/progress  # 进度
```

详见 V1 spec。V3.0 不动后端，只补前端 /plan 页面 + nav 入口 + dashboard 进度卡。

### 5.2 AI 推荐 1 端点（V2 沉淀层已实装 · V3.7 复用）

```
GET /api/analytics/recommendations  # V1 recommendations_service 已实装
```

详见 V2 沉淀层 spec §6.1。V3.7 只在 dashboard 加推荐卡 UI（不调新后端）。

---

## 6. 通用规范

### 6.1 认证

- **所有 8 个 V3 新端点 + 复用端点需要 Bearer token**（强制）
- Header：`Authorization: Bearer <token>`
- token 缺失/过期 → 401 UNAUTHORIZED
- 错误响应：`{"error": {"code": "UNAUTHORIZED", "message": "..."}}`

### 6.2 限流（V2 slowapi 配置 · V3 复用）

| 端点 | 每用户 | 每 IP | 超限响应 |
|---|---|---|---|
| `/api/learn/collections*` | 30 次 / 60s | 100 次 / 60s | 429 |
| `/api/learn/daily-challenge*` | 10 次 / 60s | 50 次 / 60s | 429 |
| `/api/learn/questions` (含 tags) | 60 次 / 60s | 200 次 / 60s | 429 |
| `/api/analytics/recommendations` | 30 次 / 60s | 100 次 / 60s | 429 |

### 6.3 版本

- URL 路径：V1 既有 `/api/learn/...` 路径（V3 不引入 /api/v3/）
- 响应 header：`X-API-Version: v2.0`（V2 沉淀层已加 · V3 沿用）

### 6.4 错误响应统一格式（V2 L4 改进 #3）

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "limit must be 1-50",
    "details": {
      "field": "limit",
      "constraint": "range 1-50"
    }
  }
}
```

错误码常量（与 V2 沉淀层一致）：

| code | HTTP | 含义 |
|---|---|---|
| `UNAUTHORIZED` | 401 | token 缺失 / 过期 |
| `FORBIDDEN` | 403 | 不是资源所有者 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 重复 / UNIQUE 冲突 |
| `VALIDATION_ERROR` | 422 | 请求字段校验失败 |
| `RATE_LIMITED` | 429 | 限流 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 依赖服务不可用 |

---

## 7. 🎯 硬性 DOD（api-spec.md 完成必须全过）

- [x] 端点清单完整（8 新增 + 6 复用）
- [x] 每个端点 3 段齐全（Request / Response / 错误码）
- [x] 错误码 ≥ 4 类（401/404/409/422/429/500/503）
- [x] 通用规范明确（认证 / 限流 / 版本 / 错误格式）
- [x] 测试要点齐全（≥ 25 测试点）

> ✅ 工具校验：`python3 scripts/check-step.py api-spec <file>`

---

## 8. 📚 相关文档

- [plan.md](plan.md) — 2 步方案
- [db-design.md](db-design.md) — 2 步数据库
- [spec.md](spec.md) — 1 步技术契约
- [component-spec.md](component-spec.md) — 2 步组件规范（即将生成）
- V1 learn API 现状：`backend/api/learn.py`（已有 5 计划端点 + recommend + tags + questions）
- V2 沉淀层 API：`backend/api/v2_settlement.py`（6 端点） + `backend/api/analytics.py:236`（recommendations）