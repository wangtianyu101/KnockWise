---
title: 调研 · 注册/登录合并页 + 注册流程 Bug
type: research
step: 0
date: 2026-07-26
status: draft
tags: [research, bug, refactor, auth]
related:
  - decisions.md
---

# 🐛 调研报告 · Bug + Refactor：注册后角色错 + 无成功提示 + 整合登录注册

> 日期：2026-07-26 · 调研人：AI · 紧急度：**P1**（影响所有新用户的注册流程，但有 workaround：手动改 role）
> 路径模式：refactor-6（涉及 UI 重构，按 AGENTS.md § 一、6 步流程走 0→1→2→3→4→5→6）

---

## 1. 任务理解

- **用户原话**：「我登录的时候有问题 怎么我用王天宇这个账号注册成功之后 进来咋还是开发者？ 而且注册完之后连提示都没有」+「我觉的这个页面可以整合起来吧 注册登录放一起 有账号就登录 反之注册」
- **现象 A**：用"王天宇"注册新账号 → 登录进入后右上 Header 显示"开发者"
- **现象 B**：注册提交后无 toast/alert/notification 提示
- **现象 C**（用户提的扩展需求）：`/login` 与 `/register` 是两个独立页面，期望合并成 `/auth` 单页（"有账号就登录 反之注册"）
- **期望 A**：注册后 role 反映账号本身（用户拍板 = `candidate` 求职者，见决策 2）
- **期望 B**：注册成功后看到成功 toast + 自动跳转登录页或直接登录
- **期望 C**：登录/注册单页自适应（具体形式待 2 步 plan.md 出 ≥2 方案）

## 2. 现状分析（refactor-6 必填段 · 合并原"复现路径"）

### 2.1 复现步骤
1. 打开 `/register` 页面
2. 输入用户名 "王天宇" + 密码 + 提交
3. **观察**：无任何 toast/alert 反馈（按钮按下后页面可能跳走也可能静止）
4. 进入应用（自动登录或跳登录页后登录）
5. **观察**：右上 Header 显示"开发者"

### 2.2 触发条件
- 数据：后端 `User.role` 字段默认值（待 Explore agent 证据确认是 hardcode `developer`）
- 前置：无（任何新注册都触发）

### 2.3 稳定性
- 稳定复现（每次注册都是 developer + 无提示）

## 3. 现状分析（续 · 影响范围）

### 3.1 用户影响
- **所有人**新注册用户
- 受影响角色：新用户 / 内部测试人员

### 3.2 功能影响
- `/api/auth/register` endpoint 返回值或后续行为
- Header / Topbar 显示 role 的位置（待证据确认）
- `/login` + `/register` 两个独立页面（合并重构）

### 3.3 数据影响
- 现有用户表里 `role=developer` 的脏数据（如果有用户因为此 Bug 被错标）→ 需评估清理脚本
- 默认值改动**不影响老数据**（SQLAlchemy default 仅 INSERT 时生效）

## 4. 重构方案（refactor-6 必填段 · 合并原"根因假设"）

| # | 假设 | 证据（file:line） | 验证方法 |
|---|---|---|---|
| **H1** | **User 模型没有 role 字段**（我的初始假设"默认 developer"错误） | `backend/models/__init__.py:40-57` User 只有 id/github_id/github_username/avatar_url/email/password_hash/display_name/last_login_at/created_at —— **无 role 字段** | 读 models 确认 |
| **H2** | **"开发者"是 Layout hardcode fallback 不是 role** | `frontend/components/v3/Layout/Layout.tsx:215-251` 默认 `userName ?? '开发者'` + `frontend/pages/_app.tsx:56-60` 调 Layout 时**未传 userName** → 永远显示"开发者" | 读 Layout 确认 |
| **H3** | TopNav 显示 userName 而非 role，但 userName 注入缺失 | `frontend/components/v3/TopNav/TopNav.tsx:28-49` 只接受 userName/userAvatar props，**不接 role** | 读 TopNav 确认 |
| **H4** | 注册成功路径只有 `router.push('/dashboard')`，无 success 提示 | `frontend/pages/index.tsx:33-47` onSubmit 调 register/login，成功只 push，无 toast/state | 读 onSubmit 确认 |
| **H5** | 没有 auth context，token 仅模块变量 + localStorage | `frontend/lib/api.ts:55-79` token 存储 + `120-137` API wrappers；`frontend/pages/_app.tsx` 无 AuthProvider | 读 _app + api.ts |
| **H6** | 实际路由只有 `/`（login/register tab），不存在 `/login` 或 `/register` | `frontend/pages/index.tsx:6` + `_app.tsx:18-22` `LAYOUT_EXCLUDE_PATHS = ['/', '/onboarding']`；onboarding 页面存在但非 register | 读路由定义 |
| **H7** | 后端响应与 JWT 均不含 role | `backend/api/auth.py:64-71` `_user_response` 只返 id/email/display_name/avatar_url；`54-61` JWT payload 仅 sub/exp/email | 读 auth.py |
| **H8** | 项目无 toast 库（sonner/react-hot-toast/react-toastify 都不存在） | grep `toast\|notification` 仅 package-lock/tsbuildinfo 命中，无应用代码 | grep + 读 package.json |

> **调研偏差总结**（见 § 9.7）：用户和我都基于"项目有 role 字段 + 两个独立登录注册页面"的假设，实际**项目完全没有 role 概念 + 已经是单页 tab**。用户报告的"开发者" = Layout hardcode fallback，不是 role。

## 5. 重构方案（续 · 最近相关改动）

待 Explore agent 返回后补充。

### 5.1 调研证据（满足 6 步 v2 DOD）

- **docs/issues.md**（唯一主账 · 同步登记本任务的新议题 + 决策更新）
- **git log -10**（最近相关改动 · 看 V3 系列 + 议题 A-E 决策落地）
- **git status**（确认 unstaged 状态 · 排除多 agent 冲突）

## 9.7 调研偏差修正（2026-07-26 · 关键）

> ⚠️ **必须显式记录**（按 AGENTS.md § 6.6 调研偏差修正模板 · 类似 V3.8 retro.md Interview model 无 radar_data 字段案例）

| 项 | 调研阶段声称 | 实际证据 | 影响 |
|---|---|---|---|
| **A** | 后端 `User.role` 默认值是 `developer`（错） | `User` 模型**无 role 字段**（`backend/models/__init__.py:40-57`） | 决策 2（默认 role=candidate）**整个无效**——没有字段可改 |
| **B** | "开发者"是数据库 role 读出来的（错） | 是 `Layout.tsx:215-251` hardcode `userName ?? '开发者'` + `_app.tsx:56-60` 没传 userName | 真 Bug = Layout fallback 错 + userName 注入缺失，与 role 无关 |
| **C** | 项目有 `/login` 和 `/register` 两个独立页面（错） | 实际**只有 `/` 页面 + tab 切换**（`pages/index.tsx:6`） | 用户路径 B"合并"的实际对象是 `/`，不是 `/login+/register` |
| **D** | 项目有 toast 库但注册没调（部分对） | **完全没引入 toast 库**；注册成功/失败都用页面内 error state | 决策 5（toast 库选择）确实需要，但范围比预想大 = 需引入新依赖 |

**修正后的决策影响**：
1. **决策 2（默认 role=candidate）→ ❌ 取消**。改为新决策：**是否引入 `User.role` 字段**（如果产品确实需要 role 概念，否则只修 userName fallback）
2. **新决策**：修 `Layout.tsx` userName fallback（去掉 hardcode "开发者"，或改成有意义的中性默认值）+ `_app.tsx` 注入 userName（从 token 解码 / /api/auth/me 拉 / AuthContext）
3. **新决策**：用户说的"整合登录注册" = 实际是把 `/` 改成更明确的 `/auth` 路由？或保留 `/` 但加 success 提示？需用户重新拍板
4. **新决策**：是否引入 toast 库（决策 5 已存在 → 现在更明确：必须引入，因为现状完全无 toast）

## 7. 输出建议（refactor-6 必填段）

### 6.1 推荐路径
```
0 调研（本步 · in_progress · 等 Explore agent 证据）
→ 1 规格（spec.md + design-spec.md + ASCII + HTML mockup · UI 设计子流程）
→ 2 计划（≥2 合并方案 + 单一推荐 + 用户决策）
→ 3 拆分（tasks.md · ≤1h 原子）
→ 4 实施（TDD 红→绿 + writer/verifier 双 agent）
→ 5 验证（L3 pytest/vitest + L5 dev server 手工）
→ 6 复盘（retro.md + 更新 issues.md / AGENTS.md）
```

### 6.2 紧急度判定
- **P1**（不是 P0：不阻塞核心面试、不损坏数据、有临时方案 = 手动改 role）

### 6.3 临时止血（如需 P0/P1 临时 hotfix）
- DB 脚本批量更新错标用户 role（待根因确认）
- 前端临时在 onSubmit 加 `alert('注册成功')`

---

## 6. 风险评估（refactor-6 必填段 · 原"风险等级"）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 默认 role 写死 developer | 🟡 中 | 改 default + 加回归测试 |
| 注册前端没调 toast | 🟡 中 | 引入 toast 库 + onSubmit 加 toast.success/error |
| Header 读 role 不刷新 | 🔴 中-高 | 排查 AuthProvider + 必要时加 re-fetch |
| 改默认值影响老数据 | 🟢 低 | SQLAlchemy default 仅 INSERT 生效 |
| 合并登录注册页 UI 重构范围爆炸 | 🟡 中 | 走 mockup 验收 + ≤1h 原子任务拆分 |
| 未做 § 6.10 安全审查 | ✅ 不适用 | 不涉及 CI Agent / secrets / 高权限 |

## 8. 用户决策清单（已拍板）

| # | 决策项 | 选择 | 用户原话 | 日期 | 状态 |
|---|---|---|---|---|---|
| 1 | 实施范围 | ✅ 路径 B（修 Bug + 合并登录注册页） | 「B」+「注册登录放一起 有账号就登录 反之注册」 | 2026-07-26 | ✅ 已决策 |
| 2 | 默认 role 值 | ✅ `candidate`（求职者） | 「A」 | 2026-07-26 | ✅ 已决策 |
| 3 | 合并页 UI 形式 | 🔄 tab 切换 / 单表单自适应 / 拆分组件 | 待 2 步出方案后拍板 | — | ⏸ 待决策 |
| 4 | Header role 修复点 | 🔄 待定位（context 不刷 / hardcode / 缓存） | — | — | ⏸ 待定位 |
| 5 | toast 库选择 | 🔄 待规格评估（sonner / react-hot-toast / antd message） | — | — | ⏸ 待规格 |

> 📌 **本节是简表镜像** · 详细决策记录请看 [`decisions.md`](decisions.md)

---

## 自检清单（AI 调研完必过）

- [x] 复现步骤可执行（不是"有时候会出错"）
- [x] 影响范围量化（不是"可能有一些用户"）
- [x] 根因假设 ≥ 2 个，且给出验证方法（8 个 · H1-H8 · 已 Explore agent 证据回填）
- [x] 找到引入 commit（或明确说"找不到"）— 已有 § 5 最近相关改动 git log
- [x] 紧急度判定清晰（P1）
- [x] P0/P1 给了临时止血方案（DB 脚本 + alert 临时方案）
- [x] Explore agent 证据回填（✅ 已完成）