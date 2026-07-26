---
title: UI 设计规格 · /auth 合并登录注册页
type: design-spec
step: 1
date: 2026-07-26
status: draft
tags: [design, auth, ux]
related:
  - spec.md
  - ../2026-07-26-refactor-auth-unified-page/decisions.md
---

# UI 设计规格 · /auth 合并登录注册页

> 页面：`/auth`（原 `/` 迁移）
> 视觉系统：**继承 KnockWise V3**（dark glassmorphism + 渐变光晕 · 见 [`docs/rules/design-mockup-workflow.md` § 8](../../rules/design-mockup-workflow.md#8-⚠️-必须继承项目视觉系统knockwise-v3-案例)）
> Mockup 位置：`docs/tasks/2026-07-26-refactor-auth-unified-page/mockups/01-auth.html`
> 设计索引：`docs/designs/auth-unified-page/index.md`

---

## § 1 用户旅程（v4 · 单一表单自动判断 · 无副标题无检查状态指示）

### Journey 1 · 新用户首次访问
1. 浏览器输入 `http://localhost:3000/` 或点外链
2. → 路由重定向到 `/auth`
3. → 看到默认卡片：仅「欢迎来到 KnockWise」标题 + 邮箱 + 密码 + 「登录 / 注册」按钮（**无副标题 · 无检查状态指示器**）
4. → 输入新邮箱（如 `newuser@example.com`）+ **失焦** → 调 `GET /api/auth/check-email?email=newuser@example.com`
5. → 后端返回 `{exists: false}` → **UI 自动切到「加入 KnockWise」注册态**（仅标题变化 + 多显示昵称字段 + 按钮变 "注册"）
6. → 填昵称 + 设置密码 → 提交
7. → **toast 弹出"创建成功"**（SVG check 图标 · 左侧绿边） → 0.5s 后自动跳转 `/dashboard`
8. → Header 显示 `newuser`（email 前缀）· **不是"开发者"**

### Journey 2 · 老用户登录
1. 直接访问 `/auth`（或被重定向）
2. → 默认卡片
3. → 输入已注册邮箱（如 `wangtianyu@example.com`）+ **失焦** → 调 `GET /api/auth/check-email`
4. → 后端返回 `{exists: true}` → **UI 自动切到「欢迎回来」登录态**（邮箱 readonly + 密码 autofocus + "登录" 按钮）
5. → 输入密码 → 提交
6. → **toast 弹出"登录成功"** → 跳转 `/dashboard`

### Journey 3 · 错误处理
1. 切到注册态后，邮箱已被人抢先注册（race condition）→ 提交后端返回 409
2. → **toast 弹出 "该邮箱已注册 · 请返回登录"**（SVG X 图标 · 左侧红边）
3. → 表单保留输入（不重置）

---

## § 2 页面地图

| 路径 | 组件 | Layout | 鉴权 | 备注 |
|---|---|---|---|---|
| `/` | redirect → `/auth` | — | 公开 | 兼容旧路径 |
| `/auth` | `pages/auth.tsx` | **无**（不进 Layout） | 公开 | **本任务核心** |
| `/dashboard` | `pages/dashboard.tsx` | 包 Layout + Sidebar | 需 token | Header 显示真实 userName |

---

## § 3 页面线框（ASCII Wireframe · v4 · 单一表单 · 无副标题无指示器）

### 3.1 `/auth` · 默认状态（用户开始输入）

```
┌─────────────────────────────────────────────────────────┐
│        ✨ [K logo SVG · V3 style]   KnockWise             │ ← 渐变 logo
│                                                      （无 tagline）
├─────────────────────────────────────────────────────────┤
│  ┌─ glass-card ──────────────────────────────────────┐ │
│  │                                                    │ │
│  │   欢迎来到 KnockWise                                │ │
│  │                                                    │ │
│  │   邮箱                                              │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ wangtianyu@example.com                       │ │ │ ← onBlur
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   密码                                              │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ ••••••••                                      │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   ┌─ btn-primary ──────────────────────────────┐ │ │
│  │   │          登 录 / 注 册                      │ │ │ ← 按钮文字
│  │   └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│        🛡 Dev Login                                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 `/auth` · 邮箱已注册 → 自动切登录态

```
┌─────────────────────────────────────────────────────────┐
│        ✨ [K logo]   KnockWise                           │
├─────────────────────────────────────────────────────────┤
│  ┌─ glass-card ──────────────────────────────────────┐ │
│  │                                                    │ │
│  │   欢迎回来                                          │ │
│  │                                                    │ │
│  │   邮箱                                              │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ wangtianyu@example.com      [readonly]       │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   密码                                              │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ ••••••••         [autofocus]                 │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   ┌─ btn-primary ──────────────────────────────┐ │ │
│  │   │              登 录                          │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.3 `/auth` · 邮箱未注册 → 自动切注册态

```
┌─────────────────────────────────────────────────────────┐
│        ✨ [K logo]   KnockWise                           │
├─────────────────────────────────────────────────────────┤
│  ┌─ glass-card ──────────────────────────────────────┐ │
│  │                                                    │ │
│  │   加入 KnockWise                                    │ │
│  │                                                    │ │
│  │   邮箱                                              │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ newuser@example.com         [readonly]       │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   昵称（可选）                                       │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ 你的昵称                [autofocus]          │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   设置密码（≥ 6 位）                                 │ │
│  │   ┌──────────────────────────────────────────────┐ │ │
│  │   │ ••••••••                                      │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  │   ┌─ btn-primary ──────────────────────────────┐ │ │
│  │   │              注 册                          │ │ │
│  │   └──────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.4 `/auth` · 创建成功 toast（叠加在 3.3 上）

```
┌─────────────────────────────────────────────────────────┐
│        ✨ [K logo]   KnockWise                           │
├─────────────────────────────────────────────────────────┤
│  ┌─ glass-card ──────────────────────────────────────┐ │
│  │  ... (注册表单 · 加载中 · 按钮 disabled)            │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─── toast (SVG check · 左侧绿边) ────────────────┐   │
│  │  ✓  创建成功 · 正在跳转 Dashboard...                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.5 `/dashboard` · Header 显示真实 userName

```
┌─────────────────────────────────────────────────────────┐
│ [Sidebar]  │   TopNav (V3 glassmorphism)                 │
│  ...       │   ┌──────────────────────────────────────┐ │
│            │   │  DASHBOARD                [wangtianyu] │ │
│            │   │                          ┌── avatar ─┐ │ │
│            │   │                          │  W T     │ │ │
│            │   │                          └──────────┘ │ │
│            │   └──────────────────────────────────────┘ │
│            │                                              │
│            │   ... (dashboard 内容)                        │
└─────────────────────────────────────────────────────────┘
```

---

## § 4 交互细节

### 4.1 自动判断触发时机
- 邮箱 input `onBlur` 触发（不是 onChange · 避免每个字符都查）
- 邮箱格式合法（含 `@`）才查
- 加 debounce 300ms 防止快速连续失焦
- 调 `GET /api/auth/check-email?email=xxx`（新 endpoint · 见 spec.md § 3.4）
- 后端返回 `{exists: true | false}` → UI 切状态
- **v4**：UI 切换**静默进行**（无副标题 · 无检查状态指示器 · 用户无感知）

### 4.2 表单验证（前端 + 后端双校验）
| 字段 | 规则 | 错误提示 |
|---|---|---|
| email | 含 `@` + 域名 | "邮箱格式错误" |
| password | ≥ 6 位 | "密码至少 6 位" |
| nickname | ≤ 50 字符 · 可选 | "昵称过长" |

### 4.3 Toast 时序（v4 · SVG 图标 · sonner 框架）
| 事件 | 图标 | toast 类型 | 持续时间 |
|---|---|---|---|
| 注册/登录成功 | **SVG check**（lucide `polyline points="20 6 9 17 4 12"`） | `success` · 左侧绿边 | 1.5s · 自动消失 |
| 注册/登录失败 | **SVG X**（lucide 两条 cross line） | `error` · 左侧红边 | 4s · 需手动关闭 |
| 网络错误 | **SVG X** | `error` · 左侧红边 | 4s |

> **v4 关键**：**不使用**文字符号 ✓ ✕（用户反馈"图标改改很差"） · 改用 inline SVG

### 4.4 跳转时序
- 注册/登录成功 → toast 弹出 → 500ms 后 `router.push('/dashboard')`
- 失败 → toast 弹出 → 不跳转 · 保留表单

### 4.5 v4 UI 精简规则（决策 12）
- ❌ 卡片**不显示副标题**（"输入邮箱开始..." / "检测到 xxx 已注册..." / "xxx 是新账号..." 全部去掉）
- ❌ 卡片**不显示检查状态指示器**（⏳ 等待 / ● ✓ 已识别 / ● ✓ 准备创建 全部去掉）
- ❌ brand-block **不显示 tagline**（"智能面试 · 真正会追问" 去掉）
- ✅ 默认态按钮文字 = **"登录 / 注册"**（不是"继续"也不是 disabled）
- ✅ Logo = **V3 K logo SVG**（与 sidebar 一致 · 不用闪电 ⚡ / Mail / 其他图标）
- ✅ 按钮根据状态切换文字：
  - 默认态："登录 / 注册"
  - 已注册态："登 录"
  - 未注册态："注 册"

### 4.5 Header userName 来源链（v4 移除了之前的"检查状态指示器"段——副标题和检查状态指示器按用户反馈去掉）
```
localStorage.access_token
  ↓ jwtDecode (lib/auth.ts · 新)
{ sub: '12', email: 'wangtianyu@example.com' }
  ↓ userName = display_name ?? email.split('@')[0]
"wangtianyu"
  ↓ _app.tsx 注入 Layout
  ↓ Layout 传给 TopNav
TopNav 显示 "wangtianyu"
```

---

## § 5 视觉规范（用户决策 11 · 2026-07-26 · **继承 V3 glassmorphism**）

> 📌 **本任务 mockup 必须继承 V3 视觉系统**（与 App 内部 dashboard / interview / push 等页面一致）。用户原话「整体的颜色和内容要与内部统一」。

### 5.1 CSS Variables（继承 V3 token · 来自 design-mockup-workflow.md § 8）

```css
:root {
  /* 主题色 */
  --color-primary: #6366f1;
  --color-primary-hover: #4f46e5;
  --color-cyan: #06b6d4;
  --color-emerald: #10b981;

  /* 背景（dark glassmorphism） */
  --color-bg-page: #050914;
  --color-bg-card: rgba(15, 20, 40, 0.7);
  --color-bg-card-hover: rgba(20, 26, 50, 0.85);

  /* 文字 */
  --color-text-primary: #f8fafc;
  --color-text-secondary: #94a3b8;
  --color-text-tertiary: #64748b;

  /* 状态 */
  --color-success: #34d399;
  --color-error: #f87171;

  /* 边框 + glow shadow */
  --color-border: rgba(148, 163, 184, 0.08);
  --color-border-hover: rgba(99, 102, 241, 0.25);
  --shadow-glow-primary: 0 0 0 1px rgba(99, 102, 241, 0.15), 0 4px 16px rgba(99, 102, 241, 0.2);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.25);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.3);

  /* 动效 */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);

  /* 字体 */
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "PingFang SC", "Microsoft YaHei", sans-serif;
}
```

### 5.2 必须复用的 V3 component 类

| 类名 | 用途 |
|---|---|
| `.glass-card` | 主卡片 · `backdrop-filter: blur(20px)` + rgba bg + border + box-shadow |
| `.btn` `.btn-primary` | 主按钮 · 渐变背景（`linear-gradient(135deg, primary, #8b5cf6)`）+ glow shadow |
| `.input` | 输入框 · `rgba(15,20,40,0.5)` bg + focus 时 primary 边框 + glow |
| `.toast` (sonner 自带) | 顶部 toast · 不自建 |
| `.app-nav` | 顶部 nav（登录页不渲染）|
| `.sidebar` | 左侧 sidebar（登录页不渲染）|

### 5.3 V3 背景光晕（必加）

```css
body {
  background: var(--color-bg-page);
  background-image:
    radial-gradient(circle at 20% 10%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
    radial-gradient(circle at 80% 90%, rgba(16, 185, 129, 0.1) 0%, transparent 40%);
  background-attachment: fixed;
}
```

### 5.4 V3 Logo + Brand 渐变（必加）

```css
.brand-name {
  background: linear-gradient(135deg, #818cf8 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### 5.5 反例（V3 项目禁忌）

- ❌ 自创 light theme（项目统一 dark）
- ❌ 自创颜色 token（如 `#3b82f6` · `#2563eb`）
- ❌ 自创 button class（用 `.btn-primary`）
- ❌ 裸 top nav（auth 页不显示 Sidebar/TopNav）
- ❌ 单层 box-shadow · 改用 `--shadow-glow-primary`
- ❌ default transition · 用 `--ease-spring` / `--ease-out`
- ❌ Lorem ipsum 占位（用真实 `wangtianyu@example.com` / `王天宇`）
- ❌ flat 实底色 badge
- ❌ 自建 toast（用 sonner）
- ❌ 自创暗色极简版（用户已 v3 撤回决策 9 · 改回继承 V3）

### 5.6 响应式断点

| 断点 | 行为 |
|---|---|
| ≥ 480px | 卡片宽 400px · 居中 |
| < 480px | 卡片宽 calc(100% - 32px) · padding 缩到 24px |

### 5.4 响应式断点

| 断点 | 行为 |
|---|---|
| ≥ 640px | 卡片宽 400px · 居中 |
| < 640px | 卡片宽 calc(100% - 32px) · padding 缩小 |

---

## § 6 元信息

- **任务目录**：`docs/tasks/2026-07-26-refactor-auth-unified-page/`
- **Mockup**：`mockups/01-auth.html`（登录 / 注册 / 注册成功 三状态切换演示）
- **设计索引**：`docs/designs/auth-unified-page/index.md`
- **视觉继承**：KnockWise V3 dark glassmorphism
- **下一步**：用户验收 ASCII + HTML mockup → 进 § 2 plan.md 出 ≥2 实施方案