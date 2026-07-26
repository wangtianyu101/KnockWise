---
title: 决策主账 · 注册/登录合并页 + 注册流程 Bug
type: decisions
step: 0
date: 2026-07-26
status: active
tags: [decisions, auth, ux]
related:
  - research.md
  - ../2026-07-21-issues-audit/decisions.md
---

# 决策主账 · 注册/登录合并页 + 注册流程 Bug

> 📌 **本文件是本任务决策的最权威详细主账**（按 CLAUDE.md § 6.9 / AGENTS.md § 6.9）。
>
> **镜像关系**（按 CLAUDE.md § 6.8 v2 同步规则）：
> - `research.md` § 八 — 简表 + 链接（不重复）
> - [`docs/issues.md`](../../issues.md) — 唯一主账（议题状态 + 顶部决策更新）
> - `spec.md` / `design-spec.md`（1 步规格实施时）— 业务规格反映决策
>
> **关联上下文**：
> - [`docs/issues.md`](../../issues.md) § 二、已发现 bug（登记新议题）
> - [`docs/templates/research-bug.md`](../../templates/research-bug.md)（fix-mini 模板）

---

## ① 顶部权威定位

本文件按 CLAUDE.md § 6.9 必备 4 段结构记录本任务全部决策（调研阶段 / 规格阶段 / 计划阶段 / 实施阶段）。每个决策有日期、选项、选择、用户原话、理由 ≥3 条、影响文件、关联决策。**仅链接不重复**原则：research.md § 八与 issues.md 顶部是简表镜像，详细记录在本文件。

---

## ② 决策总览表

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-26 | 实施范围 | ✅ **路径 B**（修 Bug + 路由迁移 `/` → `/auth`） | ✅ 已决策 | 决策 6 |
| 2 | 2026-07-26 | ~~注册接口 `role` 默认值~~ | ❌ **取消**（User 模型无 role 字段 · 见 research.md § 9.7） | ❌ 已取消 | 决策 7 |
| 3 | 2026-07-26 | 合并页 UI 形式 | ❌ **tab 切换**（v1 撤回）→ 🆕 v3 = **单一表单 + 自动判断**（用户输入邮箱 → 失焦调 `GET /api/auth/check-email` → 已存在显示登录表单 · 不存在显示注册表单 · 见决策 10） | ✅ 已决策（v3） | 决策 10 |
| 4 | 2026-07-26 | Header "开发者" 根因 | ✅ **Layout hardcode + _app 未传 userName** | ✅ 已定位 | 决策 8 |
| 5 | 2026-07-26 | toast 库选择 | ✅ **sonner**（用户"进第二步"默认接受推荐组合 · 实际装 `^1.7.4`） | ✅ 已决策 | — |
| 6 | 2026-07-26 | 路径 B 实际对象 | 🟡 **A. 迁 `/` 到 `/auth`**（之前基于"都按默认来"自动拍 · 撤回） | 🔄 待决策 | 决策 1 |
| 7 | 2026-07-26 | 是否引入 `User.role` | 🟡 **A. 不引入**（之前基于"都按默认来"自动拍 · 撤回） | 🔄 待决策 | 决策 2（取消） |
| 8 | 2026-07-26 | "开发者" 修复方案 | 🟡 **A. 最小改**（之前基于"都按默认来"自动拍 · 撤回） | 🔄 待决策 | 决策 4 |
| **9** | ❌ 2026-07-26 v3 撤回 | ~~`/auth` mockup 视觉 = 暗色居中极简版~~ | ❌ **撤回**（用户要求"颜色和内容与内部统一" → 视觉继承 V3 glassmorphism · 见决策 11） | ❌ 已撤回 | 决策 11 |
| **10** | 🆕 2026-07-26 | `/auth` 表单行为 = 单一表单 + 自动判断登录/注册 | ✅ **方案 A · 自动判断**：单表单 + email 失焦调 `GET /api/auth/check-email?email=xxx` → 已存在切登录态 · 不存在切注册态 · 用户原话"自动根据他是否有账号来判断" | ✅ 已决策 | 决策 11, 6 |
| **11** | 🆕 2026-07-26 | `/auth` 视觉 = 继承 V3 dark glassmorphism | ✅ **继承 V3**（dark + 渐变光晕 + glass-card + 紫色主按钮 · 与 dashboard/interview/push 等内部页面一致 · 用户原话"颜色和内容要与内部统一"） | ✅ 已决策 | 决策 10, 9（撤回） |
| **12** | 🆕 2026-07-26 v4 | `/auth` UI 精简 = 去副标题 + 去检查状态指示器 + 默认按钮"登录 / 注册" | ✅ **v4**：v3 的副标题（"输入邮箱开始..." / "检测到 xxx 已注册..." 等）和检查状态指示器（⏳ / ● / ✓）全部去掉 · 默认态按钮改"登录 / 注册"（之前 v3 是 disabled "继续"）· 用户原话"文字提示也去掉 直接把继续改成登录/注册" + "图标改改很差" | ✅ 已决策 | 决策 10, 11 |
| **13** | 🆕 2026-07-26 v5 | **合并** `login` + `register` → 单一 `authenticate` 接口（后端内部自动判断） | ✅ **v5**：原 `POST /api/auth/login` + `POST /api/auth/register` 合并成 `POST /api/auth/authenticate` · body: `{email, password, display_name?}` · 后端查 email 是否存在：不存在 → 创建用户 + 返回 token；存在 → 验证密码 + 返回 token · 用户原话"登录注册现在应该是一个接口了吧 内部接口自动判断是登录还是注册" · 旧 login/register endpoint 保留标 deprecated 兼容（避免破坏其他调用方） | ✅ 已决策 | 决策 10 |

---

## ③ 决策详细记录

### 决策 1 · 实施范围 = 路径 B（修 Bug + 合并登录注册页）

- **日期**：2026-07-26
- **决策项**：Bug 修复时是否同时合并 `/login` 与 `/register` 路由
- **选项列表**：
  - A. 仅修 Bug（30 min · 不动页面布局）
  - B. 修 Bug + 合并到 `/auth` 单页（估时半天-1 天 · 涉及 UI 重构 → 走 refactor-6 / full-6）
  - C. 合并 + 引入第三方 auth 服务（auth0 / clerk）→ 范围爆炸，不考虑
- **选择**：✅ **B**
- **用户原话**：「B」+ 「我觉的这个页面可以整合起来吧 注册登录放一起 有账号就登录 反之注册」
- **理由**：
  1. 注册流程没提示反馈 → 独立注册流程让"注册成功"语义丢失，合并后单流程能明确 toggle
  2. 用户体验诉求明确（"有账号就登录 反之注册"= 单表单自适应 vs tab 切换）
  3. 现状是两套页面维护成本 > 一套页面，且共享表单/校验逻辑可以复用
- **影响文件**：
  - `frontend/app/login/page.tsx` + `frontend/app/register/page.tsx`（可能合并到 `frontend/app/auth/page.tsx`）
  - 新建共享组件 `frontend/components/auth/AuthForm.tsx`（含 mode toggle）
  - `backend/api/auth.py`（注册 endpoint 默认 role 修改，见决策 2）
  - Header / Topbar 组件（修 role 显示，见决策 4）
- **关联决策**：决策 2 / 决策 3 / 决策 4

### 决策 2 · ~~注册接口 `User.role` 默认值 = `candidate`~~ ❌ 已取消（调研偏差）

- **日期**：2026-07-26（决策）→ 2026-07-26（取消）
- **决策项**：注册时 `role` 字段不传时的默认值
- **调研偏差**：Explore agent 证据（`backend/models/__init__.py:40-57`）显示 **User 模型完全没有 role 字段**——既无字段，也无 default，更无 choices 清单。决策基于错误假设（"后端硬编码默认 developer"）。
- **真实根因**（见决策 4 / 决策 8）："开发者"不是 role，是 `Layout.tsx:215-251` hardcode 的 `userName ?? '开发者'` fallback + `_app.tsx:56-60` 未传 userName。
- **取消理由**：没有 role 字段可改默认值。决策 2 整个失去依据。
- **替代决策**：决策 7（是否引入 `User.role` 字段）+ 决策 8（修 userName fallback 与注入）
- **影响文件**：无（未做任何代码改动）
- **教训**：调研阶段必须先 `grep` 字段定义 + 读模型，不能凭用户表述推断（按 AGENTS.md § 6.6 调研偏差修正 · 类似 V3.8 retro Interview model 无 radar_data 字段案例）

### 决策 3 · 合并页 UI 形式 = 保留现有 tab 切换

- **日期**：2026-07-26
- **决策项**：合并后的 `/auth` 页面 UI 形式
- **选项列表**：
  - A. tab 切换（保留现状 · 最简）✅
  - B. 单表单自适应（无 tab · 一个表单字段根据登录/注册态切换）
  - C. 拆分两个独立组件 + 共享 layout（彻底解耦）
- **选择**：✅ **A. tab 切换**
- **依据**：用户原话"有账号就登录 反之注册"= tab 切换最直观；现有 `pages/index.tsx` 已实现 tab，迁移成本最低；A/B 测试代价 < 5min
- **影响文件**：`frontend/pages/index.tsx` → `frontend/pages/auth.tsx`（迁移 + 强化）
- **关联决策**：决策 1, 6

### 决策 4 · Header "开发者" 根因 = Layout hardcode + _app 未传 userName

- **日期**：2026-07-26
- **决策项**："开发者"为何显示在 Header
- **证据**（来自 Explore agent）：
  - `frontend/components/v3/Layout/Layout.tsx:215-251` 默认 `userName ?? '开发者'`（hardcode fallback）
  - `frontend/pages/_app.tsx:56-60` 调 Layout 时**未传 userName**（无 AuthProvider）
  - `frontend/components/v3/TopNav/TopNav.tsx:28-49` 仅显示 userName，不接 role
- **选择**：✅ 根因 = Layout hardcode + _app 注入缺失（**不是 role 问题**，User 模型无 role 字段）
- **关联决策**：决策 8（修复方案）

### 决策 5 · toast 库 = sonner

- **日期**：2026-07-26
- **决策项**：前端引入哪个 toast 库
- **选项列表**：
  - A. **sonner**（轻量 · ~5KB · API 极简 · Next.js 友好）✅
  - B. react-hot-toast（老牌 · ~10KB）
  - C. antd `message`（项目已有 antd · 但 antd 4 vs 5 API 不同）
  - D. 自建极简（无依赖 · ~30 行）
- **选择**：✅ **A. sonner**
- **理由**：
  1. 项目当前是 **完全无 toast**（不是"有但没用"），引入新依赖不可避免
  2. sonner 体积最小、API 最简（`toast.success('注册成功')` 一行）
  3. 与 Next.js 13+ App Router 兼容好（`'use client'` 边界友好）
- **影响文件**：新 `frontend/components/ToastProvider.tsx` + `frontend/pages/_app.tsx` 包裹 + `frontend/lib/toast.ts` 封装
- **关联决策**：—

### 决策 6 · 路径 B 实际对象 = 迁 `/` 到 `/auth`

- **日期**：2026-07-26
- **决策项**：原"合并 `/login`+`/register`"基于错误假设（实际只有 `/`）→ 实际要做什么？
- **选项列表**：
  - A. **迁 `/` 到 `/auth`**（更明确的语义路径）✅
  - B. 保留 `/`（最小改动 · 但语义不清）
  - C. 保留 `/` + 强提示（折中）
- **选择**：✅ **A. 迁 `/` 到 `/auth`**
- **依据**：
  1. 用户原话"注册登录放一起" → 期望明确的统一入口
  2. `/auth` 命名更符合 RESTful 语义
  3. 迁移成本可控（路由改名 + `_app.tsx` 的 `LAYOUT_EXCLUDE_PATHS` 同步更新）
- **影响文件**：
  - 新 `frontend/pages/auth.tsx`（迁移自 `pages/index.tsx`）
  - `frontend/pages/index.tsx` → 改为重定向到 `/auth` 或保留作旧路径兼容
  - `frontend/pages/_app.tsx` LAYOUT_EXCLUDE_PATHS 加 `/auth`
- **关联决策**：决策 1, 3

### 决策 7 · 是否引入 `User.role` 字段 = 不引入

- **日期**：2026-07-26
- **决策项**：产品是否需要 role 概念（candidate / developer / admin）
- **选项列表**：
  - A. **不引入**（项目当前无 role 业务诉求 · 避免 schema 改动 + migration 风险）✅
  - B. 引入 + 默认 `candidate`（但实际不需要 · 浪费 schema）
  - C. 引入 + 不设默认（NOT NULL 约束下需 nullable）
- **选择**：✅ **A. 不引入**
- **依据**：
  1. 项目当前是单人开发 + 单用户角色场景（求职者用 KnockWise 面试）
  2. 改 schema 需 `_MIGRATIONS` 加 ALTER + 测试（不必要风险）
  3. 如未来真需要 role，再走新任务决策
- **影响文件**：无（不写代码）
- **关联决策**：决策 2（取消）

### 决策 8 · "开发者" 修复方案 = 方案 A 最小改

- **日期**：2026-07-26
- **决策项**：如何修 Layout 永远显示"开发者"
- **选项列表**：
  - A. **最小改**：去掉 hardcode `'开发者'` fallback → Layout 必填 userName prop + `_app.tsx` 从 `lib/api.ts` token 解 JWT payload（sub/email）取 email 前缀作为 userName ✅
  - B. 完整改：引入 AuthContext + 新增 `/api/auth/me` endpoint + Layout/TopNav 从 context 读
- **选择**：✅ **A. 最小改**（估时 5-10 min）
- **依据**：
  1. 当前 JWT payload 含 sub + email（来自决策 4 Explore agent 证据 · `auth.py:54-61`）
  2. email 前缀（如 `wangtianyu@example.com` → `wangtianyu`）可作为 displayName 临时方案
  3. 不引入 AuthContext 复杂度（后续如有需要再单独决策）
  4. 范围可控，避免决策 7 类似的范围爆炸
- **影响文件**：
  - `frontend/components/v3/Layout/Layout.tsx:215-251`（去 hardcode · 必填 userName）
  - `frontend/pages/_app.tsx:56-60`（注入 userName · 从 token 解 email 前缀）
  - `frontend/lib/auth.ts`（新 · 解 JWT payload 工具函数）
- **回归测试**：`frontend/__tests__/auth.test.ts`（新增 token 解码 + userName 注入）
- **关联决策**：决策 4

---

## ④ 决策落地追踪 + 元信息

### 落地追踪表

| # | 决策 | 关联 spec/issue/PR | 落地状态 |
|---|---|---|---|
| 1 | 路径 B（修 Bug + 改 `/` 或 `/auth`） | spec.md + design-spec.md（1 步） | 🟡 范围偏差待用户拍板（决策 6） |
| 2 | ~~默认 role=candidate~~ | ❌ 已取消（决策 2 调研偏差） | ❌ 不落地 |
| 3 | 合并页 UI 形式 | design-spec.md + mockup（1 步） | ⏸ 待规格 |
| 4 | Header "开发者" 根因 | ✅ 已定位 = Layout hardcode + _app 注入缺失 | ✅ 已定位 |
| 5 | toast 库选择 = **sonner** | `frontend/package.json` 加 `"sonner": "^1.7.4"`（T1 已实施） | ✅ 已落地 |
| 6 | 路径 B 实际对象 = `/` 是否迁 `/auth` | 1 步规格 + 2 步计划 | 🔄 待用户拍板 |
| 7 | 是否引入 `User.role` 字段 | spec.md（如决定引入） | 🔄 待用户拍板 |
| 8 | "开发者" 修复方案（去 hardcode + 注入 userName） | backend/auth.py + frontend/Layout.tsx + _app.tsx | 🔄 待用户拍 A/B |

### 元信息

- **位置**：`docs/tasks/2026-07-26-refactor-auth-unified-page/decisions.md`
- **创建日期**：2026-07-26
- **决策总数**：13（已决策 12 / 已定位 1 / 待决策 0 / 取消 1 / 暂缓 0）
- **调研偏差次数**：1（决策 2 因"假设 User 有 role 字段"被取消 · 按 AGENTS.md § 6.6 记录）
- **撤回记录（v2 · 2026-07-26）**：决策 3/5/6/7/8 之前基于用户"都按默认来"自动拍板 · 用户撤回 plan.md + tasks.md 后回到"待决策"状态 · 关联 plan.md / tasks.md 已删
- **v5 撤回/合并记录（2026-07-26）**：决策 13 = 合并 login + register → authenticate · 旧 endpoint 保留 deprecated 兼容
- **关联任务**：本目录 `research.md` / `spec.md` / `design-spec.md` / `mockups/01-auth.html` · `plan.md` / `tasks.md` 已撤回（待 2-3 步重新拍板后写）
- **关联主账**：[`docs/issues.md`](../../issues.md) 顶部决策更新段 + 新议题登记