---
title: 业务规格 · 注册/登录合并页 + 注册流程 Bug
type: spec
step: 1
date: 2026-07-26
status: draft
tags: [spec, auth, ux]
related:
  - research.md
  - decisions.md
  - design-spec.md
---

# 业务规格 · 注册/登录合并页 + 注册流程 Bug

> ✅ **已验收 · 2026-07-26 · 用户原话"下一步"**（接受 mockup + spec + 自动接受推荐组合决策 5/6/7/8）

> **路径模式**：refactor-6（含 UI 重构 + 后端简化 + 修 Bug）
>
> **范围**：路径 B = 修 Bug + 路由迁移 `/` → `/auth` + 单一表单自动判断 + **合并 login/register → 单接口 `authenticate`** + V3 glassmorphism + UI 精简
>
> **决策主账**：[`decisions.md`](decisions.md)（13 项决策 · 12 已拍 / 1 取消）
>
> **关键决策**：
> - 决策 1：路径 B = 修 Bug + 改路由
> - 决策 4：Header "开发者" 根因 = Layout hardcode + `_app` 未传 userName
> - 决策 10：表单行为 = **单一表单 + 自动判断**（onBlur → check-email → UI 静默切换）
> - 决策 11：视觉 = **继承 V3 dark glassmorphism**（与 App 内部一致）
> - 决策 12：UI 精简 = **去副标题 + 去检查状态指示器 + 默认按钮"登录 / 注册" + V3 K logo + SVG toast**
> - **决策 13：合并 login + register → 单一 `POST /api/auth/authenticate`**（后端内部按 email 存在性自动判断 · 用户原话"登录注册现在应该是一个接口了吧 内部接口自动判断是登录还是注册"）

---

## 1. 用户故事

### US-1 · 新用户注册
- **As a** 首次访问 KnockWise 的求职者
- **I want to** 在 `/auth` 输入邮箱后**静默**自动切到注册态（仅卡片标题变化 + 多一个昵称字段 + 按钮变"注册"）
- **So that** 我不需要先判断"我有没有账号"，系统自动判断且 UI 干净（无副标题 · 无检查状态指示器）

### US-2 · 已有用户登录
- **As a** 已注册账号的求职者
- **I want to** 在 `/auth` 输入邮箱后**静默**自动切到登录态（仅卡片标题变化 + 邮箱 readonly + 按钮"登录"）
- **So that** 我直接输密码就能登录，不用选 tab，也看不到冗余提示

### US-3 · Header 显示真实用户名
- **As a** 任何登录用户
- **I want to** 右上 Header 显示我的真实名字（或 email 前缀），不是固定"开发者"
- **So that** 我知道当前登录的是哪个账号

### US-4 · 注册/登录错误可见
- **As a** 输入错密码 / 注册时邮箱已存在
- **I want to** 看到明确的 **SVG 图标 + 状态色边 toast**（不是页面内一闪而过的 error · 不是文字符号 ✓ ✕）
- **So that** 我知道发生了什么错误并能修正

---

## 3. 业务规则（Requirement + Scenario · spec-template.md § 2）

> 以下业务规则同时作为 Requirement（系统承诺 · 用 SHALL 强约束），与 § 测试场景联动。

### Requirement: 单一认证接口与自动判断登录/注册
The system SHALL provide a single `POST /api/auth/authenticate` endpoint that internally decides login vs register flow based on email existence (existence → login; not exists → register). The system SHALL also expose `GET /api/auth/check-email` for UI state pre-check. Legacy `POST /api/auth/login` and `POST /api/auth/register` endpoints SHALL remain available but marked deprecated, internally redirecting to `authenticate`.

### Requirement: 头部 userName 注入
The system SHALL inject the actual `userName` into the Layout/TopNav component (derived from JWT `email` prefix), and SHALL NOT display the hardcoded string "开发者".

### Requirement: 路由统一入口
The system SHALL migrate the default landing route from `/` to `/auth` and SHALL redirect `/` to `/auth` for backwards compatibility.

### Requirement: UI 精简 + V3 视觉
The system SHALL render the `/auth` page using a single form with automatic login/register switching, with no subtitle, no check-status indicator, no tagline in the brand block, and SHALL inherit V3 dark glassmorphism visual tokens.

### Requirement: Toast 反馈
The system SHALL display a toast on every 4xx/5xx response (error · SVG X icon · red left border) and on successful login/register (success · SVG check icon · green left border).

| # | 业务规则编号 | 描述 | 优先级 |
|---|---|---|---|
| BR-1 | `POST /api/auth/authenticate` 成功后，前端必须调 `toast.success`（**SVG check 图标**） + 500ms 后跳转 `/dashboard` | P0 |
| BR-2 | `POST /api/auth/authenticate` 失败（4xx/5xx）必须调 `toast.error`（**SVG X 图标**） · 保留表单输入 | P0 |
| BR-3 | Header TopNav 显示 `userName`（不再是 hardcode "开发者"） | P0 |
| BR-4 | `userName` 注入路径：从 localStorage token 解 JWT payload → 取 `email` 前缀 → 注入 Layout | P0 |
| BR-5 | 路由迁移：`/` → `/auth`（统一入口） · `/dashboard` 等登录后路由不变 | P0 |
| BR-6 | `/auth` 表单**单一表单 + 自动判断**：onBlur 调 `GET /api/auth/check-email` → UI 静默切换登录/注册态 | P0 |
| BR-7 | `/auth` UI 精简：卡片**只有标题**（无副标题 · 无检查状态指示器 · brand-block 无 tagline） | P0 |
| BR-8 | `/auth` 默认态按钮文字 = **"登录 / 注册"** · 切换后变"登录"或"注册" | P0 |
| BR-9 | `/auth` 视觉继承 V3 glassmorphism（dark + 渐变光晕 + glass-card + 紫色渐变按钮） | P0 |
| BR-10 | 登录/注册走**单一接口** `POST /api/auth/authenticate` · 后端内部根据 email 是否存在自动判断走登录或注册流程 · 旧 `login` / `register` endpoint 保留标 deprecated 兼容 | P0 |
| BR-11 | 旧路由 `/` 重定向到 `/auth`（兼容浏览器历史 + 外链） | P1 |
| BR-12 | 用户模型**不引入** `role` 字段（项目无 role 业务诉求） | P1 |

---

## 3. 边界条件

### 3.1 空值 / 异常 / 并发
- **空值**：email/password 为空时返回 400 + toast.error
- **异常**：网络失败时 toast.error + 不跳转
- **并发**：check-email 后到 submit 之间的 race condition → 后端 create 时捕获 IntegrityError 返回 409

### 3.2 时序
- check-email 必须先于 authenticate（用于 UI 状态切换 · 决策 10）
- authenticate 成功后 setToken 必须先于 router.push

### 3.3 安全 / 权限
- 密码用 PBKDF2-SHA256（600K iterations · OWASP 2023 推荐 · 已达标）
- JWT payload 不含敏感信息（仅 sub/exp/email · 决策 4）
- authenticate 响应不返回 password_hash
- 不引入 User.role 字段（决策 7）

### 3.4 性能 / QPS
- check-email 响应时间 P95 < 50ms（简单查询）
- authenticate 响应时间 P95 < 200ms（含 PBKDF2 验证 600K iterations）

### 3.5 兼容性 / 版本
- 旧 `POST /api/auth/login` / `POST /api/auth/register` endpoint 标 deprecated · 内部 redirect 到 `authenticate`（决策 13）
- 旧调用方继续可用（onboarding / dev-login / 集成测试）
- 路由 `/` 重定向到 `/auth`（兼容浏览器历史 + 外链 · 决策 6）

### 3.6 国际化
- 不适用（项目当前仅中文）

## 4. 端点契约

### 3.1 `GET /api/auth/check-email`（UI 状态判断用）

**Query param**：`?email=wangtianyu@example.com`

**Response 200**：
```json
{ "exists": true, "email": "wangtianyu@example.com" }
```

或：
```json
{ "exists": false, "email": "newuser@example.com" }
```

**Response 4xx**：
- 400：邮箱格式错

**注意**：不返回 user 对象 · 不限流 · 公开 endpoint。

### 3.2 🆕 `POST /api/auth/authenticate`（v5 · 合并 login + register · **核心接口**）

**设计思路**：前端只调这一个接口，body 含 email + password + 可选 display_name。后端查 email 存在性：
- **不存在** → 创建用户（display_name 缺省用 email 前缀） + 生成 token
- **存在** → 验证密码（display_name 忽略） + 生成 token

**Request body**：
```json
{
  "email": "wangtianyu@example.com",
  "password": "123456",
  "display_name": "王天宇"  // 仅注册流程用 · 缺省 = email 前缀
}
```

**Response 200**（登录/注册两种流程响应结构一致）：
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
  "mode": "login"  // 🆕 告诉前端这次走的是哪种流程 · 用于 toast 文案
}
```

`mode` 取值：
- `"login"` → 已有用户登录成功
- `"register"` → 新用户注册成功

**Response 4xx**：
- 400：邮箱格式错 / 密码 < 6 位
- 401：邮箱已存在但密码错（旧用户输错密码）
- 409：极端 race condition · 邮箱刚被注册（理论上不应该发生 · 后端 create 时 try/except 捕获 IntegrityError 返回 409）
- 422：display_name 过长（注册时校验）

**关键差异（v5 vs 旧 login/register）**：
- ❌ 旧：前端先 `GET /api/auth/check-email` 决定调 `POST /login` 还是 `POST /register`
- ✅ v5：前端**仍调** `check-email`（用于 UI 状态切换：是否显示昵称字段）但**提交时统一调** `authenticate`

### 3.3 ⚠️ `POST /api/auth/login`（已 deprecated · 保留兼容）

> **状态**：v5 决策后标 deprecated · 内部 redirect 到 `/api/auth/authenticate` · 仅供老代码兜底

### 3.4 ⚠️ `POST /api/auth/register`（已 deprecated · 保留兼容）

> **状态**：v5 决策后标 deprecated · 内部 redirect 到 `/api/auth/authenticate` · 仅供老代码兜底

### 3.5 JWT payload（已有 · 不变）

```json
{
  "sub": "12",                // user.id
  "exp": 1754000000,
  "email": "wangtianyu@example.com"  // 可选
}
```

> 前端从 `sub` 解不出用户名 → 退化用 `email` 前缀（`wangtianyu`）。**这就是 BR-4 的依据**。

---

## 5. 路由契约

| 路由 | 组件 | Layout | 鉴权 |
|---|---|---|---|
| `/` | `router.replace('/auth')` 重定向 | — | 公开 |
| `/auth` | `pages/auth.tsx`（原 `pages/index.tsx` 迁移） | **不包 Layout**（在 `LAYOUT_EXCLUDE_PATHS`） | 公开 |
| `/dashboard` | `pages/dashboard.tsx` | 包 Layout + Sidebar | 需 token |
| `/interview/*` | … | 包 Layout + Sidebar | 需 token |
| `/onboarding` | `pages/onboarding.tsx` | **不包 Layout** | 公开 |

---

## 5. 测试场景（happy + invalid + edge + failure 各 ≥ 1）

> 满足 6 步 v2 DOD 5 段齐全要求 · 与 § 6 验收标准 AC-1~AC-7 联动 · spec-template.md § 2.2 风格（Scenario: <场景名> + Given/When/Then/And）

#### Scenario: 邮箱失焦 · 自动切登录态（happy · AC-1）
- **Given** 用户输入已注册邮箱 `wangtianyu@example.com`
- **When** 输入框 onBlur 触发 `GET /api/auth/check-email`
- **Then** 后端返回 `{exists: true, email: "..."}`
- **And** 前端切到登录态：标题变"欢迎回来" + 邮箱 readonly + 密码 autofocus + 按钮"登录"

#### Scenario: 邮箱失焦 · 自动切注册态（happy · AC-1）
- **Given** 用户输入未注册邮箱 `newuser@example.com`
- **When** 输入框 onBlur 触发 `GET /api/auth/check-email`
- **Then** 后端返回 `{exists: false, email: "..."}`
- **And** 前端切到注册态：标题变"加入 KnockWise" + 多显示昵称字段 + 按钮变"注册"

#### Scenario: 注册成功（happy · AC-7）
- **Given** 前端已切到注册态 + display_name="王天宇" + password="123456"
- **When** 提交调 `POST /api/auth/authenticate`
- **Then** 后端创建用户 + 返回 `{access_token, user, mode: "register"}` 200
- **And** 前端调 `toast.success("创建成功")` + 500ms 后 `router.push('/dashboard')`

#### Scenario: 邮箱格式错（invalid · AC-1）
- **Given** 用户输入非法邮箱 `wangtianyu@`（含 @ 但无域名）
- **When** 提交调 `POST /api/auth/authenticate`
- **Then** 后端返回 400
- **And** 前端调 `toast.error("邮箱格式错误")` + 不跳转

#### Scenario: 密码 < 6 位（invalid · AC-1）
- **Given** 用户输入密码 `"123"`
- **When** 提交调 `POST /api/auth/authenticate`
- **Then** 后端返回 400
- **And** 前端调 `toast.error("密码至少 6 位")` + 不跳转

#### Scenario: 登录成功（happy · AC-7）
- **Given** 已注册用户 `wangtianyu@example.com` + 正确密码
- **When** 提交调 `POST /api/auth/authenticate`
- **Then** 后端验证密码 + 返回 `{access_token, user, mode: "login"}` 200
- **And** 前端调 `toast.success("登录成功")` + 跳转 `/dashboard`

#### Scenario: 登录密码错（invalid · failure · AC-1）
- **Given** 已注册用户 `wangtianyu@example.com` + 错误密码
- **When** 提交调 `POST /api/auth/authenticate`
- **Then** 后端返回 401
- **And** 前端调 `toast.error("邮箱或密码错误")` + 不跳转

#### Scenario: race condition（edge · failure · AC-7）
- **Given** 用户 A 在 check-email 后到 submit 之前，邮箱被用户 B 抢先注册
- **When** 用户 A 提交调 `POST /api/auth/authenticate`
- **Then** 后端 create 时捕获 IntegrityError 返回 409
- **And** 前端调 `toast.error("该邮箱已注册 · 请返回登录")` + 不跳转

#### Scenario: Header 显示真实 userName（edge · AC-2）
- **Given** 用户登录 `wangtianyu@example.com`（JWT payload 含 email）
- **When** `_app.tsx` 注入 userName = `wangtianyu`（email 前缀）
- **Then** TopNav 显示 "wangtianyu" · **不再**是 hardcode "开发者"

#### Scenario: 路由迁移（happy · AC-3）
- **Given** 用户访问 `http://localhost:3000/`
- **When** `_app.tsx` 不包 Layout + `pages/index.tsx` 调 `router.replace('/auth')`
- **Then** 浏览器 URL 变成 `/auth`
- **And** 渲染默认态卡片（无 Layout 残留）

#### Scenario: Toast SVG 图标（edge · AC-4 + AC-5）
- **Given** 注册/登录成功
- **When** 前端调 `toast.success(...)`
- **Then** toast 用 **SVG check 图标**（lucide `polyline points="20 6 9 17 4 12"`）+ 左侧绿边
- **And** **不**使用文字符号 ✓ ✕

#### Scenario: 旧 endpoint deprecated 兼容（edge · AC-7）
- **Given** 老代码调用 `POST /api/auth/login` 或 `POST /api/auth/register`
- **When** 提交到旧 endpoint
- **Then** 内部 redirect 到 `/api/auth/authenticate` 逻辑
- **And** 返回相同的 `{access_token, user, mode}` 结构

#### Scenario: 视觉 v4 精简（edge · AC-5）
- **Given** 打开 `/auth` 默认态
- **When** 渲染卡片
- **Then** 卡片**只有标题**（无副标题 · 无 tagline · 无检查状态指示器）
- **And** brand-block 无 tagline
- **And** 默认按钮文字 = "登录 / 注册"

---

## 5. 数据契约（前端 store / localStorage）

| Key | 来源 | 用途 |
|---|---|---|
| `access_token`（`knockwise_token` localStorage key） | `lib/api.ts:setToken()` 后写 | JWT 字符串 |
| JWT payload → `email` | 解码 `access_token` | userName fallback（email 前缀） |
| JWT payload → `sub` | 解码 `access_token` | user.id（暂不直接用） |

> 不引入 AuthContext / Redux · 最小改动 · `lib/api.ts` + `_app.tsx` 已够用

### § 5.1 Schema 定义（TypeScript interface · 满足 6 步 v2 DOD 数据契约 schema 关键字要求）

```typescript
// frontend/lib/auth.ts · JWT 解码与 userName 派生
export interface JwtPayload {
  sub: string;          // user.id (string per JWT spec)
  exp: number;          // expiration timestamp
  email?: string;       // optional · 用于 userName fallback
}

export interface UserInfo {
  userName: string;      // 注入 Layout 的 userName（email 前缀或 display_name）
  email: string | null;
  userId: number;        // 来自 sub string
}

export interface AuthApiResponse {
  access_token: string;
  token_type: "bearer";
  user: {
    id: number;
    email: string;
    display_name: string | null;
    avatar_url: string | null;
  };
  mode: "login" | "register";  // v5 新增 · 后端自动判断结果
}

export interface CheckEmailResponse {
  exists: boolean;
  email: string;
}
```

---

## 6. 验收标准

### AC-1 · 自动判断 + 提交流程可见
- [ ] 打开 `/auth` → 默认态：标题"欢迎来到 KnockWise" + 邮箱 + 密码 + 按钮"登录 / 注册"（**无副标题 · 无检查状态指示器**）
- [ ] 输入 `newuser@example.com`（未注册）+ onBlur → 0.5s 内切到注册态：标题变"加入 KnockWise" + 多显示昵称字段 + 按钮变"注册"（**无副标题**）
- [ ] 填写昵称 + 密码 → 提交 → 调 `POST /api/auth/authenticate` → 响应 `mode="register"` → `toast.success`（**SVG check 图标**）弹出"创建成功" → 0.5s 后跳转 `/dashboard`
- [ ] 输入已注册邮箱 + onBlur → 切到登录态：标题变"欢迎回来" + 邮箱 readonly + 密码 autofocus + 按钮"登录"
- [ ] 输入错误密码 → 提交 → 调 `authenticate` → 后端返回 401 → `toast.error`（**SVG X 图标**）弹出"邮箱或密码错误" + 不跳转
- [ ] 输入非法邮箱（含 @ 但无域名）→ `toast.error` 弹出"邮箱格式错误"
- [ ] 输入 < 6 位密码 → `toast.error` 弹出"密码至少 6 位"

### AC-2 · Header 显示真实 userName
- [ ] 登录 `wangtianyu@example.com` → Header 显示 `wangtianyu`（email 前缀）
- [ ] 登录 `admin@knockwise.dev`（display_name="管理员"）→ Header 显示 `管理员`
- [ ] **不再**显示硬编码"开发者"

### AC-3 · 路由迁移
- [ ] 直接访问 `/` → 浏览器 URL 变成 `/auth`
- [ ] 直接访问 `/auth` → 渲染默认态卡片
- [ ] Sidebar 仅在 `/dashboard` 等登录后路由出现
- [ ] `/auth` 与 `/dashboard` 互不干扰（无 Layout 残留）

### AC-4 · Toast 集成
- [ ] `package.json` 加 `sonner` 依赖
- [ ] `_app.tsx` 包 `<Toaster />` Provider
- [ ] 所有 4xx/5xx 响应都有 toast（**SVG X 图标 · 左侧红边**）
- [ ] 注册/登录成功都有 toast（**SVG check 图标 · 左侧绿边**）
- [ ] **不**使用文字符号 ✓ ✕（用户反馈 v3 文字符号"图标改改很差"）

### AC-5 · v4 视觉精简
- [ ] Logo 用 **V3 K logo SVG**（与 sidebar 一致）
- [ ] Toast 图标用 **inline SVG**（lucide check / X）
- [ ] 默认态卡片**只有标题**（无副标题 · 无 tagline · 无检查状态指示器）
- [ ] 已注册 / 未注册态卡片**只有标题**（无副标题）
- [ ] brand-block **无 tagline**
- [ ] 默认按钮文字 = **"登录 / 注册"**
- [ ] 视觉 = **V3 dark glassmorphism**

### AC-6 · check-email endpoint
- [ ] `GET /api/auth/check-email?email=xxx` 返回 `{exists: true|false, email: "..."}`
- [ ] 邮箱格式错返回 400
- [ ] 不返回 user 对象
- [ ] 公开 endpoint

### AC-7 🆕 v5 authenticate 接口（合并 login + register）
- [ ] `POST /api/auth/authenticate` body `{email, password, display_name?}` 返回 `{access_token, user, mode: "login"|"register"}`
- [ ] 邮箱不存在 + display_name 提供 → 创建用户 + 返回 `mode="register"`
- [ ] 邮箱不存在 + display_name 缺省 → 创建用户（display_name = email 前缀） + 返回 `mode="register"`
- [ ] 邮箱存在 + 密码对 → 验证密码 + 返回 `mode="login"`
- [ ] 邮箱存在 + 密码错 → 返回 401
- [ ] 旧 `POST /api/auth/login` / `POST /api/auth/register` 标 deprecated · 内部 redirect 到 `/api/auth/authenticate` · 老调用方继续可用

---

## 7. 范围外（明确不做）

- ❌ 不引入 `User.role` 字段（决策 7 · 避免 schema 改动）
- ❌ 不引入 AuthContext / Redux（决策 8A · 最小改）
- ❌ 不动 `/onboarding`（独立流程 · 用户未提及）
- ❌ 不改密码哈希算法（PBKDF2 600K 已达标 · 见 issues.md 债务 5）
- ❌ 不改 JWT payload 结构（决策 4 · 已有 sub/email 够用）
- ❌ 不引入 OAuth / 第三方登录（决策 1C 排除）
- ❌ 不改 dev-login 流程（`auth.py:218-261` 保留 · 测试用）
- ❌ 不引入 tab 切换 UI（决策 3 v1 撤回）
- ❌ 不引入 auth 极简版设计（决策 9 撤回）
- ❌ 不引入"等待邮箱检查"等检查状态指示器（决策 12）
- ❌ **不删除**旧 `login` / `register` endpoint（决策 13 · 保留标 deprecated 兼容 · 避免破坏其他调用方如 onboarding / dev-login / 集成测试）
- ❌ 不动 dashboard / interview / push 等其他页面的视觉（只改 `/auth`）

---

## 8. 实施顺序（8 个 commit · 1 步 tasks.md 拆分依据）

| T# | 范围 | commit 边界 | 估时 |
|---|---|---|---|
| T1 | 加 sonner 依赖 + `<Toaster />` Provider | 1 commit | 10 min |
| T2 | `_app.tsx` 包 `<Toaster />` + 注入 userName（从 JWT 解 email 前缀） | 1 commit | 15 min |
| T3 | `Layout.tsx` 去掉 hardcode `'开发者'` · userName 必填 | 1 commit | 5 min |
| T4 | **后端**：新增 `GET /api/auth/check-email` + **新增 `POST /api/auth/authenticate`**（合并 login + register 逻辑）+ 旧 login/register endpoint 加 deprecated 标记（内部 redirect 到 authenticate） | 1 commit | 20 min |
| T5 | `pages/auth.tsx`（从 `pages/index.tsx` 迁移）+ **单一表单自动判断**（onBlur 调 check-email）+ 提交调 **authenticate**（替代 login/register）+ 全 toast + **V3 K logo** + **SVG 图标** + v4 UI 精简（无副标题/无检查状态/默认按钮"登录 / 注册"） | 1 commit | 30 min |
| T6 | `pages/index.tsx` 改为重定向 `/` → `/auth` | 1 commit | 3 min |
| T7 | 前端测试 `__tests__/auth.test.tsx`（token 解码 + userName 注入 + toast 调用 mock + check-email 自动判断 mock + authenticate 调用 mock + `mode` 字段处理） | 1 commit | 15 min |
| T8 | 后端测试 `tests/api/test_auth_register.py` 重写为 `test_auth_authenticate.py`（happy/4xx/race-condition + check-email 200/400 case + 旧 login/register deprecated 兼容） | 1 commit | 10 min |

**依赖关系**：
```
T1 ──→ T2 ──→ T3
            ↓
            T5 ──→ T6 ──→ T7
T4 ─────────┘                 ↓
                              T8 (与 T7 可并行)
```

**关键改动（T4 后端）**：
1. 新增 endpoint `POST /api/auth/authenticate`（内部流程：query User by email → 不存在则 create（display_name 缺省 = email 前缀）→ 验证密码（已存在）或无密码（新建）→ 生成 token → 返回 `{access_token, user, mode}`）
2. 新增 endpoint `GET /api/auth/check-email`（query User by email → 返回 `{exists, email}`）
3. 旧 `POST /api/auth/login` / `POST /api/auth/register` endpoint 加 deprecated 标记（接口签名不变）· 内部直接调 `authenticate` 逻辑（DRY）
4. `backend/api/auth.py` 整体重构（提取共享逻辑 `_authenticate_or_register(user, password, display_name)`）

---

## 9. 元信息

- **任务目录**：`docs/tasks/2026-07-26-refactor-auth-unified-page/`
- **路径模式**：refactor-6（含后端简化）
- **紧急度**：🟡 P1
- **决策数**：12 已决策 / 1 取消（决策 2 调研偏差）
- **实施顺序**：8 个 commit（spec.md § 8）
- **估时**：~2h（含 8 个 commit + 单测 + verify-loop + 后端重构）
- **v4 关键改动**：去副标题 + 去检查状态指示器 + 默认按钮"登录 / 注册" + V3 K logo + SVG toast 图标
- **v5 关键改动**：**合并 login + register → 单接口 `authenticate`**（后端内部自动判断 · 旧 endpoint deprecated 兼容）
- **关联**：
  - [`decisions.md`](decisions.md)（13 项决策主账）
  - [`research.md`](research.md)（调研 + § 9.7 偏差修正）
  - [`design-spec.md`](design-spec.md)（UI 设计规格）
  - [`mockups/01-auth.html`](mockups/01-auth.html)（v4 HTML mockup · 5 状态演示）
  - `plan.md` / `tasks.md`（§ 3/§ 4 待写）