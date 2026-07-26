---
title: API 设计规格 · /api/auth
type: api-spec
step: 2
date: 2026-07-26
status: draft
tags: [api-spec, backend, auth]
related:
  - spec.md
  - design-spec.md
  - component-spec.md
---

# API 设计规格 · /api/auth

> **一句话**：定义 `/api/auth/*` 接口契约 · 含 v5 合并 authenticate · v4 UI 精简需要 check-email endpoint。
>
> **上游业务规格**：[`spec.md`](spec.md)（v5 · 13 BR · 7 AC · 5 Requirement · 13 Scenario）
> **下游组件规格**：[`component-spec.md`](component-spec.md)
> **用户验收**: ✅ 已验收 2026-07-26

---

## 1. 接口清单

| Method | Path | 作用 | 认证 |
|---|---|---|---|
| `GET` | `/api/auth/check-email` | 检查邮箱是否已注册（UI 自动判断用） | ❌ 公开 |
| `POST` | `/api/auth/authenticate` | **统一登录/注册接口** · 后端内部自动判断 | ❌ 公开 |
| `POST` | `/api/auth/login` | ⚠️ **deprecated** · 内部 redirect 到 `/api/auth/authenticate` | ❌ 公开 |
| `POST` | `/api/auth/register` | ⚠️ **deprecated** · 内部 redirect 到 `/api/auth/authenticate` | ❌ 公开 |
| `POST` | `/api/auth/dev-login` | 跳过认证（仅测试环境） | ❌ 测试 |
| `GET` | `/api/auth/github/url` | GitHub OAuth URL | ❌ |
| `POST` | `/api/auth/github/callback` | GitHub OAuth callback | ❌ |

---

## 2. 详细定义

### 2.1 `GET /api/auth/check-email` 🆕（v5 决策）

**用途**：前端 onBlur 时调 · 用于 UI 状态自动判断（登录态 vs 注册态）

**Query**:
```
GET /api/auth/check-email?email=wangtianyu@example.com
```

**Response 200**:
```json
{ "exists": true, "email": "wangtianyu@example.com" }
```
或
```json
{ "exists": false, "email": "newuser@example.com" }
```

**Response 4xx**:
- 400：邮箱格式错（不含 `@` 或无域名）

**错误响应**（保留与现有 endpoint 一致的 detail 格式）:
```json
{ "detail": "Invalid email format" }
```

**注意**:
- 不返回 user 对象（避免泄露用户信息）
- 不限流（Phase 1 · 后续加 rate limit）
- 公开 endpoint（无需 token）

---

### 2.2 `POST /api/auth/authenticate` 🆕（v5 决策 · 核心接口）

**用途**：合并 login + register · 后端内部按 email 存在性自动判断

**Request body**:
```json
{
  "email": "wangtianyu@example.com",
  "password": "123456",
  "display_name": "王天宇"
}
```

**字段说明**:
| 字段 | 必填 | 说明 |
|---|---|---|
| `email` | ✅ | 邮箱（含 `@`） |
| `password` | ✅ | 密码（≥ 6 位 · PBKDF2-SHA256 哈希存储） |
| `display_name` | ❌ | 注册流程用 · 缺省 = email 前缀 |

**Response 200**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 12,
    "email": "wangtianyu@example.com",
    "display_name": "王天宇",
    "avatar_url": null
  },
  "mode": "register"
}
```

`mode` 取值:
- `"login"` → 已有用户登录成功
- `"register"` → 新用户注册成功

**Response 4xx**:
- 400：邮箱格式错 / 密码 < 6 位
- 401：邮箱已存在但密码错
- 409：race condition · 邮箱刚被注册（理论上不应该发生 · 后端 create 时 `try/except IntegrityError` 返回 409）
- 422：display_name 过长（注册时校验）

**内部流程**（v5 决策）:
```python
def authenticate_core(email, password, display_name):
    user = db.query(User).filter_by(email=email).first()
    if user:
        # 邮箱存在 → 走登录流程（验证密码）
        if not verify_password(password, user.password_hash):
            raise HTTPException(401, "邮箱或密码错误")
        mode = "login"
        # display_name 忽略
    else:
        # 邮箱不存在 → 走注册流程（创建用户）
        user = create_user(
            email=email,
            password=password,
            display_name=display_name or email.split('@')[0],
        )
        mode = "register"

    token = _create_token(user.id, user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_response(user),
        "mode": mode,
    }
```

---

### 2.3 ⚠️ `POST /api/auth/login`（deprecated · 保留兼容）

**状态**: v5 决策标 deprecated · 内部 redirect 到 `/api/auth/authenticate`

**实现**:
```python
@router.post("/login", deprecated=True)
async def login_legacy(req: LoginRequest):
    # 复用 authenticate 逻辑 · 强制 mode=login（display_name 忽略）
    return await _authenticate_core(req.email, req.password, display_name=None)
```

**注意**: 前端 T5 已切到 `/api/auth/authenticate` · 旧调用方（onboarding / dev-login / 集成测试）继续可用

---

### 2.4 ⚠️ `POST /api/auth/register`（deprecated · 保留兼容）

**状态**: v5 决策标 deprecated · 内部 redirect 到 `/api/auth/authenticate`

**实现**: 类似 login_legacy · 强制 mode=register（display_name 必填或 email 前缀）

---

### 2.5 `POST /api/auth/dev-login`（已有 · 测试用）

**保持不变**: 仅测试环境可用 · 跳过认证直接返回 dev user token

---

## 3. Schema 契约

```python
class AuthenticateRequest(BaseModel):
    email: str = Field(..., regex=r"^[^@]+@[^@]+$")
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = Field(None, max_length=50)

class AuthenticateResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse
    mode: Literal["login", "register"]

class CheckEmailResponse(BaseModel):
    exists: bool
    email: str
```

---

## 4. 错误响应格式

所有 4xx/5xx 响应:
```json
{ "detail": "<错误描述>" }
```

例如：
- 400: `{ "detail": "Invalid email format" }`
- 401: `{ "detail": "邮箱或密码错误" }`
- 409: `{ "detail": "该邮箱已被注册" }`

---

## 5. 测试覆盖（T4 + T8 待实施）

- `tests/api/test_auth_authenticate.py`（新 · 重写非 stub）
  - check-email: 邮箱存在 / 不存在 / 格式错
  - authenticate: 注册成功 / 登录成功 / 密码错 / 格式错 / 长度错 / race condition 409
  - 旧 endpoint 兼容: login/register deprecated 仍可用

---

## 6. 元信息

- **任务目录**: `docs/tasks/2026-07-26-refactor-auth-unified-page/`
- **决策**: 决策 13（合并 login + register → authenticate）
- **关联**: [`spec.md`](spec.md)（业务规格）/ [`component-spec.md`](component-spec.md)（前端组件规格）