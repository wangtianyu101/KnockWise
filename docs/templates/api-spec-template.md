---
title: API 设计模板（api-spec）
date: 2026-06-30
status: v1
tags: [api-spec, 1步, API, 模板]
related:
  - [spec-template.md](spec-template.md) — 上游
  - [db-design-template.md](db-design-template.md) — 配套 DB
---

# API 设计模板（api-spec.md）

> **一句话**：定义 REST / GraphQL / RPC 接口——**端点的完整契约**。
>
> **产出时机**：**2 步技术详细化阶段**（**涉及新/改 API 时**必填）。从 1 步挪到 2 步，避免 1 步过早定技术细节。
>
> **作者**：**AI 主导**（后端 lead review）。
>
> **对应 DOD**：见 `docs/DOD.md` §四.6（5 条）。

---

## 1. 接口清单（必填）

| Method | Path | 作用 | 认证 |
|---|---|---|---|
| `POST` | `/api/v1/push/subscribe` | 创建推送订阅 | ✅ Required |
| `GET` | `/api/v1/push/subscriptions` | 查询用户订阅 | ✅ Required |
| `PUT` | `/api/v1/push/subscriptions/{id}` | 更新订阅 | ✅ Required |
| `DELETE` | `/api/v1/push/subscriptions/{id}` | 删除订阅 | ✅ Required |

---

## 2. 每个接口的详细定义（必填）

### POST /api/v1/push/subscribe

#### Request

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body**:
```json
{
  "tags": ["ai", "programming"],
  "time_window": {
    "start": "08:00",
    "end": "09:00"
  }
}
```

**Schema**:
```python
class SubscribeRequest(BaseModel):
    tags: List[str] = Field(min_items=1, max_items=3)  # 业务：1-3 个
    time_window: TimeWindow

class TimeWindow(BaseModel):
    start: str = Field(regex=r"^([01]\d|2[0-3]):[0-5]\d$")  # HH:MM
    end: str = Field(regex=r"^([01]\d|2[0-3]):[0-5]\d$")
```

#### Response

**成功 (201)**:
```json
{
  "id": 123,
  "user_id": 456,
  "tags": ["ai", "programming"],
  "time_window": {"start": "08:00", "end": "09:00"},
  "created_at": "2026-06-30T08:00:00Z"
}
```

**Schema**:
```python
class SubscribeResponse(BaseModel):
    id: int
    user_id: int
    tags: List[str]
    time_window: TimeWindow
    created_at: datetime
```

#### 错误码（必填）

| 状态码 | 含义 | 触发条件 | 客户端处理 |
|---|---|---|---|
| 400 | 参数错误 | tags 超过 3 个 / time_window 格式错 | 显示"参数错误" |
| 401 | 未登录 | token 缺失 / 过期 | 跳转登录 |
| 409 | 重复订阅 | 用户已有订阅 | 提示"已订阅，请编辑" |
| 500 | 服务器错误 | DB 失败 / 其他 | 显示"服务异常，请重试" |

---

### GET /api/v1/push/subscriptions

（同上结构：Request / Response / 错误码）

---

## 3. 通用规范（必填）

### 3.1 认证
- 所有 API 需要 Bearer token
- token 在 Header: `Authorization: Bearer <token>`

### 3.2 限流
- 每用户：<X> 次/分钟
- 每 IP：<Y> 次/分钟
- 超限返回 429

### 3.3 版本
- URL 路径带版本：`/api/v1/...`
- 不兼容改动 → `/api/v2/...`，旧版继续支持 6 个月

### 3.4 错误响应统一格式

```json
{
  "error": {
    "code": "INVALID_PARAMS",
    "message": "tags must be 1-3 items",
    "details": {
      "field": "tags",
      "constraint": "min_items=1, max_items=3"
    }
  }
}
```

---

## 4. 接口依赖关系（必填）

```
POST /subscribe
  ↓ 依赖
  - User 必须存在
  - Tags 必须来自合法标签表
  ↓ 触发
  - DB: 插入 users_push_subscription
  - Cache: 失效 user_subscription:{user_id}
  - Event: SubscriptionCreated
```

---

## 5. 测试要点（必填）

```markdown
- [ ] 正常请求返回 201 + 正确响应
- [ ] tags 超 3 个返回 400
- [ ] time_window 格式错返回 400
- [ ] 未登录返回 401
- [ ] 重复订阅返回 409
- [ ] DB 失败返回 500
- [ ] 限流生效（每用户 60 次/分钟）
```

---

## 🎯 硬性 DOD（api-spec.md 完成必须全过）

- [ ] 接口清单完整（method + path + 作用 + 认证）
- [ ] 每个接口 3 段齐全（Request / Response / 错误码）
- [ ] 错误码 ≥ 4 类（400 / 401 / 409 / 500）
- [ ] 通用规范明确（认证 / 限流 / 版本 / 错误格式）
- [ ] 测试要点覆盖核心场景

> ⚠️ 任何 1 条未满足 → api-spec.md 不算完成
> ⚠️ TODO: 接入 `scripts/check-api-spec.py`（pre-commit hook）

---

## 🔴 触发条件

| 调研类型 | api-spec.md |
|---|---|
| new-feature + 新/改 API | ✅ 必填 |
| bug + API 行为异常 | ⚠️ 涉及 API 时 |
| refactor + 重构 API | ✅ 必填 |
| p0 | ⚠️ 涉及 API 时 |

---

## 6. 技术实现（plan 阶段后填 · ⚠️ 非 1 步必填）

> **本段不在 1 步必填范围**——技术选型需要 2 步 plan 阶段确定。
>
> **填写时机**：2 步 plan.md 完成后，回填本段。
>
> §1-5 是"业务契约"（接口清单、Request/Response、错误码），这些 1 步定。
> §6 是"技术实现"（协议选型、认证方案、限流策略），这些 plan 后定。

### 6.1 协议选型

```markdown
- API 协议: <REST / GraphQL / gRPC / WebSocket / Server-Sent Events>
- 数据格式: <JSON / Protocol Buffers / MessagePack>
- API 风格: <RESTful / RPC / 混合>
```

### 6.2 认证方案

```markdown
- 认证机制: <JWT / Session Cookie / OAuth 2.0 / API Key / mTLS>
- Token 存储: <localStorage / httpOnly cookie / sessionStorage>
- Token 刷新: <Refresh Token / Sliding Window / 重新登录>
- 权限模型: <RBAC / ABAC / ACL>
```

### 6.3 限流策略

```markdown
- 限流算法: <令牌桶 / 漏桶 / 滑动窗口 / 固定窗口>
- 限流维度: <每用户 / 每 IP / 全局 / 每接口>
- 限流阈值: <X 次/分钟>
- 超限响应: <429 + Retry-After header>
```

### 6.4 响应与错误格式

```markdown
- 成功响应: <JSON { data: ... } / JSON { result: ... }>
- 错误响应: <统一格式 JSON { error: { code, message, details } }>
- Content-Type: <application/json; charset=utf-8>
- 时间格式: <ISO 8601 / Unix timestamp / RFC 3339>
- 分页: <offset/limit / page/size / cursor>
```

### 6.5 跨域与缓存

```markdown
- CORS: <允许的 origin / 方法 / header>
- 缓存策略: <Cache-Control / ETag / 协商缓存>
- CDN: <是 / 否>
```

---

## 📚 相关文档

- [spec-template.md](spec-template.md) — 上游：技术规格
- [plan-template.md](plan-template.md) — **2 步 plan 后填 §6**
- [db-design-template.md](db-design-template.md) — 配套 DB 设计
- `docs/DOD.md` §三.6 — api-spec.md DOD 定义
- `docs/DOD.md` §三.6 — api-spec.md DOD 定义
- `docs/api/README.md` — 全局 API 索引（聚合所有 api-spec）