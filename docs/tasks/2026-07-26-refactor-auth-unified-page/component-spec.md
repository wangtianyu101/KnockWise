---
title: 组件设计规格 · /auth + ToastProvider
type: component-spec
step: 2
date: 2026-07-26
status: draft
tags: [component-spec, frontend, auth]
related:
  - design-spec.md
  - api-spec.md
  - mockups/01-auth.html
  - mockups/index.html
---

# 组件设计规格 · /auth + ToastProvider

> **上游设计引用**：
> - design-spec: `design-spec.md`（v4 视觉精简 · 单一表单自动判断 + V3 glassmorphism）
> - HTML mockup: `mockups/01-auth.html`（5 状态演示）+ `mockups/index.html`（wrapper）
> - 设计索引: `docs/designs/auth-unified-page/index.md`
> - **用户验收**: ✅ 已验收 2026-07-26（用户原话"下一步"）

---

## 1. 组件清单

| 组件名 | 类型 | 复用范围 | 依赖 |
|---|---|---|---|
| `<ToastProvider>` | Provider 组件 | 全局（包在 `_app.tsx`） | sonner / next/dynamic |
| `<AuthForm>` | 页面组件（`/auth`） | 单页 | React Hook Form 风格 / sonner |
| `<BrandBlock>` | 展示组件 | auth 页头 | V3 K logo SVG |
| `<TabButton>` | UI 原子（暂未使用 · v3 撤回） | — | — |

> **本任务 v4 后只剩 2 个核心组件**：`<ToastProvider>`（T1 已落地） + `<AuthForm>`（T5 待实施）

---

## 2. `<ToastProvider>` 组件规格

### Props

```typescript
import type { ComponentProps } from "react";
export type ToastProviderProps = ComponentProps<typeof SonnerToaster>;
```

### 行为

- 使用 `next/dynamic` + `ssr: false` 包裹原 `sonner` `<Toaster />`
- 在 `_app.tsx` 的两条路径（`shouldWrapLayout=true/false`）都包 `<ToastProvider />`
- 提供 sonner 全局 toast API：`toast.success(...)` / `toast.error(...)`

### 测试覆盖

- `__tests__/toast-provider.test.tsx`（4 case · 4/4 PASS）
  - export-shape · 真渲染 · position 透传 · 默认导出 === named 导出

---

## 3. `<AuthForm>` 组件规格（T5 待实施）

### Props

```typescript
interface AuthFormProps {
  // 无 props · 自包含页面组件
}
```

### 行为

#### 3.1 邮箱输入 + onBlur 自动判断
- 用户输入邮箱 + onBlur → 调 `GET /api/auth/check-email?email=xxx`
- 成功 → `mode = exists ? login : register`
- UI 切换：
  - `login` 态：邮箱字段 readonly · 密码 autofocus · 按钮 "登 录"
  - `register` 态：邮箱 readonly · 多显示昵称字段 · 按钮 "注 册"
- 默认态：标题 "欢迎来到 KnockWise" · 邮箱 + 密码 + 按钮 "登录 / 注册"

#### 3.2 提交
- 调 `POST /api/auth/authenticate` · body: `{email, password, display_name?}`
- 成功响应 `mode` 字段：
  - `mode="register"` → `toast.success("创建成功")` → 跳转 `/dashboard`
  - `mode="login"` → `toast.success("登录成功")` → 跳转 `/dashboard`
- 失败 → `toast.error(error.message)` · 不跳转 · 保留表单输入

#### 3.3 视觉（继承 V3 glassmorphism · v4 精简）
- Logo: V3 K logo SVG（不是闪电 ⚡）
- Toast 图标: SVG check / X（不是文字 ✓ ✕）
- 卡片**只有标题**（无副标题 · 无 tagline · 无检查状态指示器）
- 默认按钮文字 = "登录 / 注册"

### 测试覆盖（T7 待实施）

- `__tests__/auth.test.tsx`
  - onBlur 调 check-email mock → UI 切换
  - 提交调 authenticate mock → mode 字段处理 → toast + router.push
  - 失败 → toast.error + 不跳转

---

## 4. 依赖

- `frontend/lib/auth.ts`（T2 已落地 · `decodeJwt` + `getUserNameFromToken`）
- `frontend/components/ToastProvider.tsx`（T1 已落地）
- `frontend/pages/_app.tsx`（T2 已修改 · 包 ToastProvider + 注入 userName）
- `frontend/lib/api.ts`（待修改 · 新增 `authenticate()` 函数）

---

## 5. 元信息

- **任务目录**: `docs/tasks/2026-07-26-refactor-auth-unified-page/`
- **已落地**: T1 ToastProvider · T2 _app.tsx 包 Toaster + JWT 解码
- **待实施**: T5 AuthForm 页面组件（T5 任务）
- **关联**: [`design-spec.md`](design-spec.md) / [`api-spec.md`](api-spec.md) / [`tasks.md`](tasks.md)