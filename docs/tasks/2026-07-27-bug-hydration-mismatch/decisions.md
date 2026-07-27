---
title: 决策主账 · Hydration mismatch 全局 _app.tsx + TopNav 时间边界
type: decisions
step: 0
date: 2026-07-27
status: active
tags: [decisions, bug, frontend, hydration, ssr]
related:
  - research.md
---

# 决策主账 · Hydration mismatch · 全局 _app.tsx + TopNav 时间边界

> 📌 **本文件是本任务决策的最权威详细主账**（按 AGENTS.md § 6.9 必备 4 段结构）。
>
> **镜像关系**（按 AGENTS.md § 6.8 v2 同步规则）：
> - `research.md` § 八 — 简表 + 链接（不重复）
> - [`docs/issues.md`](../../issues.md) — 唯一主账（议题状态 + 顶部决策更新）
>
> **关联上下文**：
> - [`docs/issues.md`](../../issues.md) § 二、已发现 bug（登记新议题）
> - [`docs/templates/research-bug.md`](../../templates/research-bug.md)（fix-mini 模板）
> - 同源前次修复（非本次决策范围）：`fb248d5 fix(push): hydration mismatch 根因 + 修复`（仅修 `/push/*` 5 路由）

---

## ① 顶部权威定位

本文件按 AGENTS.md § 6.9 必备 4 段结构记录本任务全部决策（调研阶段 / 实施阶段 / 复盘阶段）。每个决策有日期、选项、选择、用户原话、理由 ≥ 3 条、影响文件、关联决策。**仅链接不重复**原则：research.md § 八与 issues.md 顶部是简表镜像，详细记录在本文件。

---

## ② 决策总览表

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-27 | `_app.tsx` 修复方案 | ✅ **方案 A**：删 `hasToken` 三元 + 受保护路由始终包 Layout（`/` `/auth` `/onboarding` 留 exclude） | ✅ 已决策 | 决策 5（排除 B/C） |
| 2 | 2026-07-27 | TopNav `new Date()` 修复是否合并 | ✅ **合并**（同一 fix-mini · 同一 commit） | ✅ 已决策 | — |
| 3 | 2026-07-27 | 调研文档是否先落地 | ✅ **先写** `research.md` + `decisions.md` 再动手 | ✅ 已决策 | — |
| 4 | 2026-07-27 | 修复路径 | ✅ **fix-mini**（0→4→6，跳 1/2/3 步） | ✅ 已决策 | — |
| 5 | 2026-07-27 | 替代方案排除 | ❌ **方案 B**（cookie 化）/ **方案 C**（强制 `hasToken=true` 简化）均不采纳 | ❌ 已排除 | 决策 1 |

---

## ③ 决策详细记录

### 决策 1 · `_app.tsx` 修复方案 = 方案 A（删 `hasToken` 三元 + 受保护路由始终包 Layout）

- **日期**：2026-07-27
- **决策项**：消除 `_app.tsx:48` `hasToken = typeof window !== "undefined" ? !!getToken() : true` 引发的 hydration mismatch
- **选项列表**：
  - **A. 删 `hasToken` 三元 + 受保护路由始终包 Layout**（受保护路由 = 非 `[/, /auth, /onboarding]`）· `token` 通过各 page 内部 `useEffect` 异步检测 + `router.replace('/auth')` 触发跳转
  - B. 把 `_app.tsx` 改成纯 client component（`'use client'` + `useEffect` 读 token）—— 但 Pages Router 下 `'use client'` 是 no-op（Explore agent 报告），方案实际不可行
  - C. 保留 SSR 用 `hasToken=true` fallback，但 client 也强制 `hasToken=true` 不读 localStorage（折中）—— 治标不治本，未登录用户仍能看到 Layout 内的 page 内容
- **选择**：✅ **A**
- **用户原话**：「1 A」
- **理由**：
  1. **根治 hydration mismatch**：删 `typeof window` 三元 → SSR 渲染路径完全确定（仅依赖 `router.pathname`），不再依赖 `localStorage` 这类浏览器独有 API
  2. **职责清晰**：`_app.tsx` 只负责 Layout 注入策略（基于路由元数据），不受 auth 状态影响；auth 检测下沉到各 page 的 `useEffect`（与 `pages/index.tsx` 现有 `useEffect` 重定向模式一致）
  3. **符合 Pages Router 惯例**：Next.js Pages Router 的 design 是"SPA-style routing + 客户端守卫"，不是 App Router 的 server-side guarding
  4. **改动最小**：仅改 `_app.tsx` 1 个三元 + 涉及到的 20+ 受保护路由都已通过 `LAYOUT_EXCLUDE_PATHS` 机制工作，证明 Layout 注入策略本身稳定
- **影响文件**：
  - `frontend/pages/_app.tsx`（**改** · 删 `hasToken` 三元 + `userName` fallback 简化为常量）
  - **新增**：每个受保护路由的 `useEffect(() => { if (!getToken()) router.replace('/auth') }, [])` —— 实际只需在 `dashboard.tsx` / `interview/profile.tsx` 等"需要 token 才能显示内容"的 page 添加；Layout 内的 page（如 `/profile` `/settings`）可保留现有行为
- **回归测试**（4 步 TDD 必跑）：
  - Playwright mount test：清 localStorage → 访问 `/dashboard` → `console.error` 含 0 条 hydration warning
  - 5 路由代表（`/dashboard` `/interview/profile` `/push/daily/2026-07-27` `/learn` `/admin/questions`）跑同一断言
  - 已登录场景：登录后访问 `/dashboard` → TopNav userName 文本 SSR/CSR 一致（"alice" == "alice"）
- **关联决策**：决策 5（替代方案排除）、决策 4（路径）

### 决策 2 · TopNav `new Date()` 修复合并到同一 PR

- **日期**：2026-07-27
- **决策项**：`TopNav.tsx:51` `new Date().toISOString().slice(0, 10)` 在 render 中调用引发时间边界 mismatch，与决策 1 修复是否合并
- **选项列表**：
  - A. **合并**（同一 fix-mini · 同一 commit）—— 1 个 PR 解决 2 个相关根因
  - B. 拆开（2 个独立 task / 2 个 PR）—— 拆细但同一文件改动会冲突
- **选择**：✅ **A**
- **用户原话**：「2 是 · 合并吧」
- **理由**：
  1. **同源同类**：都是 Pages Router SSR 取值不一致问题，共享根因（"在 render 中调用 SSR 不可用 / 不稳定的 API"）
  2. **同一文件改动**：`_app.tsx` 改完后立即改 `TopNav.tsx`，连续改 2 文件 1 次 commit 更清晰
  3. **合并测试增加边际成本低**：5 路由代表测已覆盖（不需要单测 `TopNav`）
  4. **避免决策链爆炸**：合并不让议题 / 文档同步成本（issues.md / retro.md）翻倍
- **影响文件**：
  - `frontend/components/v3/TopNav/TopNav.tsx`（**改** · `new Date()` 移到 `useEffect`）
  - `frontend/components/v3/TopNav/TopNav.tsx:73`（**改** · `<span hidden={!today}>` 避免初始闪 1 帧）
- **关联决策**：决策 1（同一 PR）

### 决策 3 · 调研文档先落地

- **日期**：2026-07-27
- **决策项**：调研阶段是否先写 `research.md` + `decisions.md` 再动手
- **选项列表**：
  - A. **先写**（按 AGENTS.md § 0.3 调研产物落地硬性要求）
  - B. 直接写代码（违反 § 0.3）
- **选择**：✅ **A**
- **用户原话**：「3 是」
- **理由**：
  1. **AGENTS.md § 0.3 强约束**：长期调研必须落地 `research.md`，临时调研也要"至少在 chat 输出"
  2. **决策可追溯**：决策主账（decisions.md）让"为什么选方案 A"在 6 个月后还能查到
  3. **复盘素材**：6 步 retro.md 直接引用 research.md / decisions.md，不重复造内容
- **影响文件**：
  - `docs/tasks/2026-07-27-bug-hydration-mismatch/research.md`（**新建**）
  - `docs/tasks/2026-07-27-bug-hydration-mismatch/decisions.md`（**新建**）
  - `docs/issues.md`（**改** · 顶部决策更新段 + § 二 新议题登记）
- **关联决策**：无

### 决策 4 · 修复路径 = fix-mini（0→4→6）

- **日期**：2026-07-27
- **决策项**：执行哪条 AGENTS.md 6 步流程
- **选项列表**：
  - A. **fix-mini**（0→4→6，跳 1/2/3 步）—— Bug 修复样式明确 + 范围 ≤ 2 文件 + 单一回归测试
  - B. full-6（0→1→2→3→4→5→6）—— 包含 spec.md / plan.md / tasks.md / 完整设计流程
  - C. refactor-6（0→1→2→3→4→5→6）—— 包含 UI 设计子流程
- **选择**：✅ **A**
- **依据**（AI 推荐 · 用户未否决）：
  1. **路径触发条件**（AGENTS.md § 0.1.1）："普通 Bug" → fix-mini
  2. **范围可控**：方案 A + TopNav 修复 = 2 文件 + 1 回归测试（不需要 spec / plan / 任务拆分）
  3. **决策已落**：方案 A 在调研阶段已拍板，不需要 1 步规格协商
  4. **节省 1-2 小时**：跳过 1/2/3 步 = 直接进 4 步 TDD 实施
- **影响文件**：无（流程选择，不写代码）
- **关联决策**：决策 1, 2

### 决策 5 · 替代方案排除（方案 B / C）

- **日期**：2026-07-27
- **决策项**：方案 B（cookie 化）/ 方案 C（强制 `hasToken=true` 简化）不采纳
- **选项**：❌ 排除
- **排除 B 理由**：
  1. Pages Router 下 `'use client'` 是 no-op（Explore agent 报告已确认）—— 声称转 client component 实际仍 SSR
  2. 即便可强制 client component，Next.js Pages Router 仍会 pre-render，整页 SSR 收益全丢
  3. 与方案 A 比，cookie 化要求改 `getToken()` 实现（走 `next/headers` cookies()）—— 跨栈改动
- **排除 C 理由**：
  1. 治标不治本：仅消除 SSR/CSR 文本不一致，未登录用户仍能短期看到 Layout 包裹 → 数据 API 401 → 内部 redirect → 闪烁
  2. 与方案 A 严重度等价但修复更粗糙（方案 A 删 1 个三元 + 加 page 级 useEffect；方案 C 仅删 1 个三元 + 保留所有 page 现状但仍 401）
- **影响文件**：无（不写代码）
- **关联决策**：决策 1

---

## ④ 决策落地追踪 + 元信息

### 落地追踪表

| # | 决策 | 关联 spec/issue/PR | 落地状态 |
|---|---|---|---|
| 1 | `_app.tsx` = 方案 A（删 hasToken 三元 + 始终包 Layout） | `frontend/pages/_app.tsx` 4 步实施 | ⏳ 待 4 步实施 |
| 2 | TopNav `new Date()` 移到 `useEffect` + `<span hidden={!today}>` | `frontend/components/v3/TopNav/TopNav.tsx` 4 步实施 | ⏳ 待 4 步实施 |
| 3 | 调研文档落地 | `research.md` / `decisions.md` / `issues.md` 同步 | ✅ 已完成（本步） |
| 4 | 路径 = fix-mini | 流程选择 | ✅ 已决策 |
| 5 | 排除 B/C | — | ❌ 排除 |

### 元信息

- **位置**：`docs/tasks/2026-07-27-bug-hydration-mismatch/decisions.md`
- **创建日期**：2026-07-27
- **决策总数**：5（已决策 4 / 已排除 1 / 暂缓 0 / 取消 0）
- **调研偏差次数**：1（4 项修正 · 见 research.md § 9）
- **关联任务**：本目录 `research.md`（同步骤落地）
- **关联主账**：[`docs/issues.md`](../../issues.md) 顶部决策更新段 + § 二新议题登记
- **前次同源修复**：`fb248d5 fix(push): hydration mismatch 根因 + 修复`（**非本次决策范围**，仅作背景关联）
