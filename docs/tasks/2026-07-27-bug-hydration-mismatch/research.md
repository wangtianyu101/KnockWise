---
title: 调研 · Hydration mismatch · 全局 _app.tsx + TopNav 时间边界
type: research
step: 0
date: 2026-07-27
status: draft
tags: [research, bug, frontend, hydration, ssr, pages-router]
related:
  - decisions.md
---

# 🐛 调研报告 · Bug：Next.js Pages Router 全局 Hydration Mismatch

> 日期：2026-07-27 · 调研人：AI · 紧急度：**P1**（影响所有受保护路由的 SSR 渲染 · 触发 React 强制 regenerate 整棵子树 · 用户感知为"页面闪一下" / DevTools 报 hydration 警告 · 非 P0：核心面试流程仍可用，仅 SSR → CSR 切换时损伤体验）
> 路径模式：**fix-mini**（0→4→6，按 AGENTS.md § 一、6 步流程）

---

## 1. 任务理解（必填）

- **用户原话**：「Hydration failed because the server rendered text didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used: 经常报这个错误 排查下根本原因」
- **现象**：浏览器 DevTools console 频繁出现 Next.js hydration error 警告；React 18+ 强制重新生成整棵 mismatch 子树，用户感知为"页面闪一下再稳定"，并产生性能损失（SSR 工作白做）
- **期望**：hydration 错误完全消除，SSR 输出的 HTML 与 client 首帧 render 一致
- **错误信息**：Next.js 15 + React 19 标准 hydration mismatch 警告（cut-off 后提示"This can happen if a SSR-ed Client Component used:..."）

---

## 2. 复现路径（必填）

### 2.1 复现步骤

**场景 A（未登录用户 — 结构性 mismatch）**：
1. 清除浏览器 localStorage（确保无 JWT）
2. 访问 `/dashboard`（或 `/interview/profile` / `/push` / `/learn` / `/ai/today` 等任何非 `[/, /auth, /onboarding]` 的路由）
3. **观察**：DevTools console 出现 hydration error；React 强制 regenerate `<main>` 子树

**场景 B（已登录用户 — 文本 mismatch）**：
1. 登录账号（localStorage 写入真实 JWT，email 如 `alice@example.com`）
2. 访问 `/dashboard`
3. **观察**：TopNav 右上角 `<span>` 文本 SSR 渲染"用户" → CSR 渲染"alice" → 触发文本 mismatch

**场景 C（UTC+8 时区用户 — 时间边界 mismatch）**：
1. 登录后访问任何受保护路由
2. **观察**：本地时间 ≥ 08:00 后，TopNav `<span>📅 {today}</span>` SSR 用 UTC 日期，CSR 切换到 UTC+8 → 日期跨天时文本 mismatch

### 2.2 触发条件

- 场景 A：localStorage 无 token + 访问受保护路由（**100% 触发**）
- 场景 B：localStorage 有 token + 任何受保护路由（**100% 触发**）
- 场景 C：UTC+8 时区 + 本地时间 ≥ 08:00 + 任何受保护路由（**每日触发**）

### 2.3 稳定性

- 场景 A：稳定复现（每次都触发）
- 场景 B：稳定复现（每次都触发）
- 场景 C：每日 08:00 后稳定触发

---

## 3. 影响范围（必填）

### 3.1 用户影响

- **未登录用户**（场景 A）：受保护路由全部触发，包含 dev / 内部测试人员
- **已登录用户**（场景 B）：所有受保护路由 + 任何时区（最广泛）
- **国内用户**（场景 C）：每日都会触发 1 次日期边界

### 3.2 功能影响

- **20 个受保护路由**触发 mismatch（所有非 `[/, /auth, /onboarding]` 的路由 + `/admin/*`）：
  - `/dashboard` `/interview/profile` `/interview/history` `/interview/setup` `/interview/room`
  - `/learn` `/review` `/plan` `/collections`
  - `/knowledge` `/qa` `/report`
  - `/push` `/push/bookmarks` `/push/settings` `/push/sources` `/push/daily/[date]`
  - `/ai/today` `/ai/history`
  - `/profile` `/settings`
  - `/admin/questions` `/admin/sync`
- **3 个受保护组件**（在受保护路由下必触发）：
  - `Layout`（受 `_app.tsx` 控制）
  - `TopNav`（受 Layout 包裹）
  - `Sidebar`（受 Layout 包裹）

### 3.3 数据影响

- **无脏数据**：纯前端渲染不一致，不影响 DB / 业务逻辑
- **无清理需求**
- **不可逆**：不是 — React 18+ 的强制 regenerate 会让 SSR 工作白做，但 client 端正确渲染后用户体验恢复

---

## 4. 根因假设（必填，≥ 2 个）

| # | 假设 | 证据（file:line） | 验证方法 |
|---|---|---|---|
| **H1** | `_app.tsx:48` `hasToken = typeof window !== "undefined" ? !!getToken() : true` — server 永远 `true`，client 走 localStorage → 结构性 mismatch | `frontend/pages/_app.tsx:48` + `lib/api.ts:66-81`（getToken 客户端读 localStorage） | grep `typeof window` + `LAYOUT_EXCLUDE_PATHS` + 实际清 localStorage 访问 `/dashboard` 看 console |
| **H2** | `_app.tsx:55` `userName = (hasToken ? getUserNameFromToken(getToken()) : null) ?? "用户"` — 已登录用户 TopNav 文本 SSR "用户" / CSR email 前缀 | `frontend/pages/_app.tsx:55` + `lib/auth.ts:49-56` + `TopNav.tsx:90` | 登录后访问 `/dashboard` 看 TopNav 右上文本 |
| **H3** | `TopNav.tsx:51` `date ?? new Date().toISOString().slice(0, 10)` — SSR vs CSR 时区/时刻不同 → 日期跨天 mismatch | `frontend/components/v3/TopNav/TopNav.tsx:51` | UTC+8 时区用户在 08:00 后访问受保护路由 |
| H4（误判） | `pages/push/daily/[date].tsx:74` `useRef(Date.now())` 不是 mismatch 源（ref 初始值不进 markup） | `frontend/pages/push/daily/[date].tsx:74` | 理论上不需验证 · React 不会对 ref 报 hydration 警告 |
| H5（误判） | `pages/interview/room.tsx:75` `toLocaleTimeString` 在 `useCallback` 内不是 mismatch 源 | `frontend/pages/interview/room.tsx:75` | callback 只在事件回调触发，初始 render 时 `transcript=[]` 不进 markup |

> **H1 + H2 在 `_app.tsx` 同一函数 `App()` 内**，必须联动修复；H3 在 `TopNav` 独立。误判 H4/H5 已剔除（详见 § 9 调研偏差修正）。

---

## 5. 最近相关改动（必填）

```bash
git log --oneline -10 -- frontend/pages/_app.tsx frontend/components/v3/TopNav/TopNav.tsx
```

```
8f4567c feat(auth): auth 页迁移 + 重定向 + _app LAYOUT_EXCLUDE_PATHS       ← 引入 hasToken 三元 + LAYOUT_EXCLUDE_PATHS
a3cf13a fix(layout): 去 hardcode "开发者" · userName 必填                  ← Layout 必填 userName （加重 H2 后果）
df62c49 feat(auth): _app 包 Toaster + JWT 解码注入 userName                ← 引入当前 _app.tsx 结构 + hasToken 三元（**引入 commit**）
6bd78c8 feat(p1-6): a11y + perf 9 维度契约 + 6 gate (全部 report-only)
e57890e test(frontend): complete T39 digest browser harness
099aaa4 feat(sidebar): V3.8 P1 Sidebar 6 组件 + Layout 注入
8dcb91a feat: add CodeMock - AI mock interview platform with LangGraph agent engine
```

**hydration 专项**：
- `fb248d5 fix(push): hydration mismatch 根因 + 修复`（2026-07-27 00:35）— **关键**：上次修复只针对 `/push/*` 路由（`SourceToggleRow` 时间 + `useDigest.ts` `enabled: isAuthed()`），**未触及 `_app.tsx` 全局 hasToken 三元**。本次 Bug 与上次修复**是同源不同面**：
  - 上次：`/push/*` 内的 `enabled: isAuthed()` 触发 query 决策不一致
  - 本次：`_app.tsx` 全局 Layout 包裹决策不一致 + `TopNav` 时间边界

> ⚠️ **调研偏差修正（重要）**：用户"经常报"是因为**前次修复 (`fb248d5`) 只覆盖了 `/push/*` 5 个页面**，未覆盖全局 `_app.tsx` 的 hasToken 三元 + TopNav 时间。其余 18+ 个受保护路由从未被修过（详见 § 9）。

---

## 6. 风险评估（fix-mini 必填段）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 方案 A 删 `hasToken` 后，未登录用户访问受保护路由 → Layout 渲染但 token 不可用 → 后续 API 调用 401 | 🟡 中 | 各 page 内部 `useEffect` 检测 `getToken()` 为 null → `router.replace('/auth')`（与 `index.tsx` 现有重定向模式一致） |
| `TopNav` 改 `useEffect` 设 today → 闪 1 帧空字符串 | 🟢 低 | 给 `today` 初始值 `''` + UI 隐藏（`<span hidden={!today}>`） |
| 修复触及全局 `_app.tsx` 影响所有 20+ 路由 → 任何回归影响面广 | 🟡 中 | 4 步实施 TDD：先写失败 Playwright 测"清 token 访问 /dashboard 不报 hydration" → 改代码 → 测绿 → 跨 5 个代表路由跑 mount test |
| 未做 § 6.10 安全审查 | ✅ 不适用 | 不涉及 CI/CD / Agent / secrets / 网络 — 纯前端渲染 |
| 跨时区用户改 UTC cut-off 可能引入新 mismatch | 🟢 低 | `toISOString().slice(0, 10)` 已经是 UTC 截断，client 用 useEffect 设值后两次值相同（如果同一时刻） |
| 修复后 `fb248d5` 的 `enabled: isAuthed()` 修复是否冲突 | 🟢 低 | 本次不动 `useDigest.ts`，仅动 `_app.tsx` + `TopNav.tsx` — 无冲突 |

---

## 7. 输出建议（fix-mini 必填段）

### 7.1 推荐路径

```
0 调研（本步 · in_progress · 落地 research.md + decisions.md）
→ 1 写回归测试（先红 · Playwright 5 路由 mount + console.error 捕获）
→ 2 改 _app.tsx（方案 A：删 hasToken 三元 + 受保护路由始终包 Layout）
→ 3 改 TopNav.tsx（new Date() 移到 useEffect）
→ 4 验证（L3 vitest + L4 独立 verifier + L5 dev server 5 路由手工）
→ 6 复盘（retro.md + 更新 issues.md / milestones.md + memory 沉淀）
```

> **跳过步 1 规格 / 2 计划 / 3 拆任务**（按 `fix-mini` 路径 — AGENTS.md § 0.1.1）：修复方向明确，方案 A 已拍板，范围 ≤ 2 文件 + 1 回归测试。

### 7.2 紧急度判定

- **P1**（不是 P0）：
  - **不阻塞核心面试流程**（token 校验在后端，UI 闪一下后能恢复）
  - **不损坏数据**
  - **有临时方案**：用户可清缓存硬刷新绕过
  - **影响所有用户的 SSR 体验**（触及面广）

### 7.3 临时止血（如需 P0/P1 临时 hotfix）

- **DevTools 临时方案**：React DevTools → ⚙️ → "Hide hydration warnings"（仅开发体验改善，不解决生产问题）
- **生产临时方案**：在每受保护路由 page 顶部加 `useEffect(() => { if (!getToken()) router.replace('/auth') }, [])` → 不解决 mismatch，但能保证未登录用户被重定向，跳过 Layout 渲染
- **推荐**：直接进 4 步正式修复（fix-mini 估时 ≤ 1.5h）

---

## 8. 用户决策清单（必填 · 6.8 同步位置）

| # | 决策项 | 选择 | 用户原话 | 日期 | 状态 |
|---|---|---|---|---|---|
| 1 | `_app.tsx` 修复方案 | ✅ **方案 A**：删 `hasToken` 三元 + 受保护路由始终包 Layout（`/` `/auth` `/onboarding` 留 exclude） | 用户：「1 A」 | 2026-07-27 | ✅ 已决策 |
| 2 | TopNav `new Date()` 修复是否合并到同一 PR | ✅ **合并**（同一 fix-mini 路径 · 同一 commit） | 用户：「2 是 · 合并吧」 | 2026-07-27 | ✅ 已决策 |
| 3 | 调研文档是否先落地 | ✅ **先写** `research.md` + `decisions.md` 再动手 | 用户：「3 是」 | 2026-07-27 | ✅ 已决策 |
| 4 | 修复路径 | ✅ **fix-mini**（0→4→6，跳 1/2/3 步） | AI 推荐 · 用户未否决 | 2026-07-27 | ✅ 已决策 |
| 5 | 替代方案排除 | ❌ B（cookie 化）/ C（强制 hasToken=true 简化）均不采纳 | — | 2026-07-27 | ❌ 已排除 |

> 📌 **本节是简表镜像** · 详细决策记录请看 [`decisions.md`](decisions.md)

---

## 9. 调研偏差修正（必填 · 6.6 同步）

| 项 | 调研阶段假设 | 实际证据 | 影响 |
|---|---|---|---|
| **A** | "经常报"可能是上次 `fb248d5` 修复的回归 | `fb248d5` 仅修 `/push/*` 5 路由（`SourceToggleRow` 时间 + `useDigest` `enabled: isAuthed()`），**未触及 `_app.tsx` 全局 + TopNav** | 真 Bug = 上次修复**未覆盖**的全局 + TopNav 残留，不是回归。属**同源不同面** |
| **B** | Explore agent 报 `useRef(Date.now())` 是黄色风险 | `useRef` 初始值**不进 markup**，React 不会报 hydration 警告 | 误判 · H4 剔除 |
| **C** | Explore agent 报 `toLocaleTimeString` in `useCallback` 是黄色风险 | callback 只在事件回调触发，初始 render 时 `transcript=[]` 不进 markup | 误判 · H5 剔除 |
| **D** | 用户只说"经常报"，未指明路由 | 实际**所有 20+ 受保护路由**都触发（不是局部） | 决策 1 选方案 A（全局修复）而非局部修复 |

---

## 10. 验证清单（fix-mini 实施前置 · 4 步前必读）

- [ ] 4 步前先写失败测试（Playwright mount test × 5 路由 + console.error 捕获 = 0 → 修复后 1）
- [ ] 5 路由代表：`/dashboard` `/interview/profile` `/push/daily/2026-07-27` `/learn` `/admin/questions`
- [ ] 清除 localStorage + 登录态 + UTC+8 时区 三场景都覆盖
- [ ] 修复后任何受保护路由再访问 → DevTools console 0 hydration warning
- [ ] 修复后性能：消除 React 强制 regenerate 子树（Network 面板观察）

---

## 自检清单（AI 调研完必过）

- [x] 复现步骤可执行（不是"有时候会出错"）
- [x] 影响范围量化（20+ 路由 + 3 组件 + 3 场景）
- [x] 根因假设 ≥ 2 个，且给出验证方法（3 个真 + 2 个误判已剔除）
- [x] 找到引入 commit（`df62c49` + 同源前次 `fb248d5`）
- [x] 紧急度判定清晰（P1）
- [x] P0/P1 给了临时止血方案（DevTools + 路由级 `useEffect` 重定向）
- [x] 决策已落 `decisions.md`（4 段结构）
- [x] 调研偏差修正（4 项 · 误判剔除 2 + 同源不同面 1 + 范围量化 1）
- [x] Explore agent 证据回填（参见同会话的 `add56bfe7f8e8b2ce` 报告）
