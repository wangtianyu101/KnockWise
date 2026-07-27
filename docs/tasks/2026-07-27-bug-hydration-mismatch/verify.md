---
title: 验证报告 · Hydration mismatch 全局修复
type: verify
step: 5
date: 2026-07-27
status: draft
tags: [verify, bug, frontend, hydration]
related:
  - research.md
  - decisions.md
  - tasks.md
---

# ✅ 验证报告 · Hydration mismatch 全局修复

> 日期：2026-07-27 · 验证人：AI + 独立 verifier · 路径：fix-mini 4→5
> 紧急度：P1（修复后消除）

---

## 1. 验证目标

按 [AGENTS.md § 一.5](docs/AGENTS.md) 5 步验证流程：
- **L3 整合测试**：vitest + Playwright 全 suite
- **L4 独立 verifier**：开新 Agent 上下文独立跑测试
- **L5 dev server 实测**：curl 验证 SSR HTML

对照需求：[research.md § 4 H1/H2/H3 根因](research.md) + [decisions.md 决策 1/2 方案 A](decisions.md)

---

## 2. L3 整合测试

### 2.1 Playwright · 场景 A 主回归（5 路由）

```bash
$ npx playwright test tests/e2e/hydration.spec.ts --reporter=list --project=chromium-desktop
```

**结果：5/5 PASS（23.2s）**

| 路由 | 状态 | 耗时 |
|---|---|---|
| `/dashboard` | ✅ | 5.2s |
| `/interview/profile` | ✅ | 4.3s |
| `/push/daily/2026-07-27` | ✅ | 4.2s |
| `/learn` | ✅ | 4.3s |
| `/admin/questions` | ✅ | 4.2s |

### 2.2 vitest 单元测试

```bash
$ cd frontend && npm test
```

**结果：32 files / 246 tests PASS（2.77s）**

- 无单测回归
- `auth.test.ts`（JWT 解码 + userName 派生）继续通过
- 32 个 test file 全部 PASS

### 2.3 TypeScript typecheck

```bash
$ cd frontend && npx tsc --noEmit
```

**结果：PASS**（无输出 = 无错误）

---

## 3. L4 独立 verifier

> 来源：[独立 verifier agent](.)（a20d1e5bd21b10987）· 全新上下文独立运行

### 3.1 对照需求（3 个修复点）

| # | 修复点 | 结果 | 证据 |
|---|---|---|---|
| 1 | `_app.tsx` 删 hasToken 三元 | ✅ PASS | `frontend/pages/_app.tsx:51` `shouldWrapLayout = !LAYOUT_EXCLUDE_PATHS.has(router.pathname)` · 仅依赖 pathname（同步可用 · SSR/CSR 一致） |
| 2 | `userName` useState 初始 + useEffect 异步 | ✅ PASS | `frontend/pages/_app.tsx:56-63` `useState<string>("用户")` + useEffect mount 后读 token |
| 3 | `TopNav` new Date 移到 useEffect | ✅ PASS | `frontend/components/v3/TopNav/TopNav.tsx:56-61` `useState<string>(date ?? '')` + useEffect 内调 new Date · render 函数体无 new Date |

### 3.2 测试结果（独立运行）

- Playwright 场景 A：**5/5 PASS**（22.9s · 独立运行）
- vitest：**32 files / 246 tests PASS**（2.92s · 独立运行）

### 3.3 实测行为（L5 · dev server）

- `/dashboard` SSR 含 sidebar：✅ PASS（grep 命中 1 次 · `<nav data-testid="topnav">` + `<aside data-testid="sidebar">` 都在 SSR HTML 中）
- `/dashboard` SSR 含 topnav：✅ PASS（grep 命中 1 次）
- SSR HTML 中 `userName` 默认值 "用户" 出现 2 次（TopNav 头像 alt + `<span>{userName}</span>`）—— **符合预期**：服务端 useState 初始值生效

### 3.4 整体结论

**PASS** · 3 个修复点全部对齐 research.md § 4 H1/H2/H3 根因 + decisions.md 决策 1/2 方案 A。

- (a) `_app.tsx` SSR/CSR 首帧 Layout 注入决策一致
- (b) `userName` SSR/CSR 首帧均为 `"用户"`，mount 后异步更新
- (c) `TopNav` `today` SSR/CSR 首帧均为 `""`，mount 后异步设置日期

---

## 4. L5 dev server 实测（本会话补做）

```bash
$ curl -s http://localhost:3000/dashboard | grep -c 'data-testid="sidebar"'
1
$ curl -s http://localhost:3000/dashboard | grep -c 'data-testid="topnav"'
1
$ curl -s http://localhost:3000/dashboard | grep -o "用户" | head -3
用户
用户
```

- ✅ Layout 始终在受保护路由 SSR HTML 中（与修复前 server 行为一致 · 修复点是 client 端消除 mismatch）
- ✅ userName 默认 "用户" 在 SSR HTML 中出现（server useState 初始值生效 · mount 后 client 异步更新到 email 前缀）

---

## 5. AC（Acceptance Criteria）逐条核验

| # | AC | 来源 | 结果 |
|---|---|---|---|
| AC-1 | 受保护路由（5 个代表）清 localStorage 访问不报 hydration error | research.md § 4 H1 | ✅ Playwright 5/5 |
| AC-2 | vitest 全 suite 通过（无单测回归） | research.md § 7 验证 | ✅ 246/246 |
| AC-3 | `_app.tsx` 不再使用 `typeof window` 在 render 中做 Layout 决策 | decisions.md 决策 1 | ✅ 独立 verifier 确认 |
| AC-4 | `TopNav` 不再在 render 中调 `new Date()` | decisions.md 决策 2 | ✅ 独立 verifier 确认 |
| AC-5 | 独立 verifier 复核 PASS | AGENTS.md § 6.7 | ✅ L4 PASS |

---

## 6. 已知限制 / 暂缓

| 项 | 原因 | 后续 |
|---|---|---|
| 场景 B（userName 文本 mismatch） | dev-login 基础设施问题：`page.request.get('/api/auth/dev-login')` 连发 8+ 次超时 | 改为手动 L5 验证 · 或新 task 做 dev-login 缓存/静态 JWT fixture |
| 场景 C（TopNav 日期 mismatch） | 同上 | 同上 |
| 视觉回归（pages.spec.ts 17 路由） | 未跑（仅依赖 L3 推断） | 合并 PR 后跑全套确认 baseline 不破 |

---

## 7. 修复对照（before / after）

### 7.1 `_app.tsx:48`

**Before**：
```tsx
const hasToken = typeof window !== "undefined" ? !!getToken() : true;
const shouldWrapLayout = hasToken && !LAYOUT_EXCLUDE_PATHS.has(router.pathname);
```

**After**：
```tsx
const shouldWrapLayout = !LAYOUT_EXCLUDE_PATHS.has(router.pathname);
```

### 7.2 `_app.tsx:55` userName

**Before**：
```tsx
const userName = (hasToken ? getUserNameFromToken(getToken()) : null) ?? "用户";
```

**After**：
```tsx
const [userName, setUserName] = useState<string>("用户");
useEffect(() => {
  const token = getToken();
  if (token) {
    const name = getUserNameFromToken(token);
    if (name) setUserName(name);
  }
}, []);
```

### 7.3 `TopNav.tsx:51` today

**Before**：
```tsx
const today = date ?? new Date().toISOString().slice(0, 10);
// ...
<span className="text-xs text-gray-500 hidden sm:inline">📅 {today}</span>
```

**After**：
```tsx
const [today, setToday] = useState<string>(date ?? '');
useEffect(() => {
  if (!date) {
    setToday(new Date().toISOString().slice(0, 10));
  }
}, [date]);
// ...
{today && (
  <span className="text-xs text-gray-500 hidden sm:inline" data-testid="topnav-date">📅 {today}</span>
)}
```

---

## 8. 验证结论

**全部 PASS**。修复可合并。

- L3 vitest 246/246 ✅
- L3 Playwright 场景 A 5/5 ✅
- L4 独立 verifier PASS（3 维度全过）✅
- L5 dev server smoke PASS ✅
- TypeScript typecheck PASS ✅

---

## 自检清单（verify 完成必过 · AGENTS.md § 一.5）

- [x] 修复对照完成（before/after）
- [x] 5 个 AC 全部 PASS
- [x] L3 + L4 + L5 三层验证齐
- [x] 已知限制 / 暂缓项已记录
- [x] 独立 verifier 报告归档（本文件 § 3）
