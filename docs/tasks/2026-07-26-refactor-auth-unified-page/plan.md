---
title: 实施计划 · 注册/登录合并页 + 注册流程 Bug
type: plan
step: 2
date: 2026-07-26
status: draft
tags: [plan, auth, refactor-6]
related:
  - spec.md
  - design-spec.md
  - decisions.md
  - research.md
---

# 实施计划 · 注册/登录合并页 + 注册流程 Bug

> **路径模式**：refactor-6（含 UI 重构 + 后端简化 + 修 Bug）
>
> **上游**：[`spec.md`](spec.md)（13 项业务规则 · 4 个端点契约 · 7 项验收标准）+ [`design-spec.md`](design-spec.md)（v4 视觉精简）+ [`decisions.md`](decisions.md)（13 项决策）
>
> **下游**：[`tasks.md`](tasks.md)（3 步拆分 · 8 个原子任务）
>
> **product-doc.md 适用性说明**：本任务路径模式 = refactor-6（非 new-feature）· 按 AGENTS.md § 一规格阶段说明，product-doc 是 new-feature 必填产物，refactor 任务**不适用 product-doc**（无新增产品意图，仅重构现有功能）。引用上游：[`decisions.md`](decisions.md) 决策 1/10/11/12/13 即作为重构方案的产品决策依据。

---

## 1. 推荐方案

**推荐**: 方案 A · 8 个 commit 按依赖顺序（spec.md § 8 已列）

```markdown
### 推荐方案
- **方案**：**方案 A · 8 个 commit 按依赖顺序**（spec.md § 8 已列）
- **理由**：
  1. 与 spec.md § 8 顺序对齐（基于验证粒度最细的拆分）
  2. 每个 commit 独立可回滚（CLAUDE.md § 6.5 任务粒度 · 每 commit ≤1h AI 工作量）
  3. T1-T3 是基础（sonner + Toaster + userName 注入），T4 是后端核心（合并 authenticate），T5 是前端核心（单一表单自动判断），T6 是路由迁移，T7-T8 是测试
  4. T4 后端可与 T1-T3 前端**并行启动**（独立模块），T7 与 T8 可并行
- **工作量**：~1.5h 实施 + ~30 min verify-loop + ~15 min 复盘 = **~2h**
- **风险**：🟢 低（所有改动在 UI / 后端 auth 模块 · 不改业务核心 · 旧 endpoint 保留 deprecated 兼容）
```

---

## 2. 方案对比

### 方案 A：8 个 commit 按依赖顺序（✅ 推荐）

- **思路**：spec.md § 8 拆 8 个 commit
- **优点**：
  - 每个 commit 独立可回滚（CLAUDE.md § 6.5 任务粒度）
  - T1-T3（前端基础） + T4（后端核心）**可部分并行**
  - T7（前端测试） + T8（后端测试）**可并行**
  - 测试 T7/T8 独立前后端，CI 可分开跑
- **缺点**：
  - commit 数较多（8 个）
  - 需要 8 次 verify-loop（CLAUDE.md § 6.7）
- **风险等级**：🟢
- **工作量**：~1.5h 实施 + verify ~30 min
- **兼容性**：✅ 完全兼容（authenticate 后端合并不影响旧 endpoint · 旧 login/register deprecated 兼容）
- **测试影响**：T7 新增 `__tests__/auth.test.tsx`（含 token 解码 + userName 注入 + toast mock + check-email mock + authenticate mock + mode 字段处理）· T8 重写 `test_auth_register.py` → `test_auth_authenticate.py`（含 happy/4xx/race + check-email 200/400 case + 旧 endpoint 兼容）

### 方案 B：5 个 commit 合并版

- **思路**：T1+T2 合并（"引入 sonner + Provider + userName 注入"） + T3 独立 + T4 后端独立 + T5+T6+T7+T8 合并（"前端 auth 页 + 路由迁移 + 测试"）
- **优点**：
  - commit 数少（5 个）
  - verify-loop 次数少
- **缺点**：
  - **T5+T6+T7+T8 合并后单 commit 工作量 ~60min · 超过 ≤1h 边界**（违反 CLAUDE.md § 6.5）
  - 前后端测试合并丢失分离的清晰边界
- **风险等级**：🟡
- **工作量**：~1.5h
- **兼容性**：✅
- **测试影响**：T7+T8 合并后测试丢失前后端分离的清晰边界

### 方案 C：12 个 commit 拆更细

- **思路**：T1 拆 "sonner 安装" + "sonner 集成" 两个 commit · T5 拆 "auth 迁移" + "toast 集成" + "v4 UI 精简" + "V3 K logo + SVG 图标" 四个 commit
- **优点**：
  - 每个 commit 工作量更小（~5-10 min）
- **缺点**：
  - **过度拆分**（"sonner 安装" 不带测试不算完整 commit · 违反 CLAUDE.md § 6.5）
  - commit 数过多增加噪声
- **风险等级**：🟢
- **工作量**：~2h
- **兼容性**：✅
- **测试影响**：无差异

---

## 3. 风险评估

| # | 风险 | 等级 | 缓解措施 |
|---|---|---|---|
| 1 | **authenticate 后端合并改动现有 login/register 调用方**（profile / dashboard / onboarding / dev-login 等） | 🟡 中 | **旧 endpoint 保留 deprecated 兼容**（spec.md § 3.3/3.4）· 内部直接 redirect 到 authenticate 逻辑（DRY 共享）· lib/api.ts:authenticate 函数替代 login/register |
| 2 | sonner 引入后 Next.js SSR 不兼容（Toaster 在 server 渲染报错） | 🟡 中 | T1 用 `next/dynamic` + `ssr: false` 包裹 Toaster 组件 |
| 3 | race condition（用户 A check-email → 用户 B 同时注册 → A 提交 → 后端发现已注册） | 🟢 低 | 后端 create 时 `try/except IntegrityError` → 返回 409 + 友好错误 |
| 4 | 旧 `login` / `register` endpoint 调用方未切到 authenticate（遗留调用） | 🟢 低 | lib/api.ts:authenticate 替代 · 前端其他组件 `grep -r "login\|register" frontend/` 确认 · 旧 endpoint 内部 redirect 兜底 |
| 5 | pre-commit 41 stub 干扰（issues.md 债务 9） | 🟡 中 | T7/T8 仅加新 case，**不动**已有 stub（避免债务 9 扩大化） |
| 6 | dev-login 流程被破坏 | 🟢 低 | 不动 `auth.py:218-261` dev-login · 仅添加新 endpoint |
| 7 | `_app.tsx` 注入 userName 后其他页面拿到 undefined | 🟡 中 | T3 把 Layout userName 改必填 · TS 类型检查强制 |
| 8 | 路由迁移 `/` → `/auth` 后旧外链失效 | 🟢 低 | T6 `pages/index.tsx` 保留重定向兼容（`router.replace('/auth')`） |
| 9 | Header 修复：JWT email 前缀注入在某些 token 无 email claim 时 fallback | 🟢 低 | BR-4 明确 fallback = email 前缀 · 如全无则返回 `user.id`（暂不实现 · 实际 email 必填） |
| 10 | 后端测试 `test_auth_register.py` 41 假绿灯（债务 9）| 🟡 中 | T8 重命名为 `test_auth_authenticate.py` 重新写（不是加 case · 是重写）· 但保留旧文件名作为 deprecated 兼容测试（避免突然删除触发更多债务）|

---

## 4. 决策点（已决策 · 见 decisions.md）

| 决策 | 选择 | 文档 |
|---|---|---|
| 决策 1：实施范围 | ✅ 路径 B | decisions.md 决策 1 |
| 决策 2：~~默认 role=candidate~~ | ❌ 已取消 | 决策 2（User 模型无 role 字段） |
| 决策 3：合并页 UI | ✅ 单一表单自动判断 | 决策 3（v3 撤回 v1 tab 切换） |
| 决策 4：Header 根因 | ✅ Layout hardcode + `_app` 未传 | 决策 4 |
| 决策 5：toast 库 | ✅ **sonner** | 决策 5 |
| 决策 6：路由 `/` → `/auth` | ✅ **迁移** | 决策 6 |
| 决策 7：User.role | ✅ **不引入** | 决策 7 |
| 决策 8：Header 修复 | ✅ **方案 A 最小改**（JWT email 前缀注入） | 决策 8 |
| 决策 9：~~暗色极简版~~ | ❌ 已撤回 | 决策 9（改回 V3） |
| 决策 10：表单自动判断 | ✅ onBlur + check-email | 决策 10 |
| 决策 11：视觉 | ✅ 继承 V3 glassmorphism | 决策 11 |
| 决策 12：UI 精简 | ✅ v4（去副标题 + 去检查状态 + 默认按钮"登录 / 注册" + V3 K logo + SVG toast） | 决策 12 |
| 决策 13：合并 login + register | ✅ 单一 `POST /api/auth/authenticate`（后端内部按 email 存在性自动判断） | 决策 13 |

> 📌 **决策 5/6/7/8**：基于用户"进第二步"默认接受之前推荐组合（sonner / 迁路由 / 不引入 role / 方案 A 最小改）。如有不同意见，在验收 plan.md 时一并指出。

---

## 5. 任务拆分（→ tasks.md 详化）

按 spec.md § 8：

| T# | 范围 | 估时 | 依赖 |
|---|---|---|---|
| T1 | 加 sonner 依赖 + `<Toaster />` Provider（`next/dynamic` + `ssr: false` 包裹） | 10 min | — |
| T2 | `_app.tsx` 包 `<Toaster />` + 注入 userName（从 JWT 解 email 前缀） | 15 min | T1 |
| T3 | `Layout.tsx` 去掉 hardcode `'开发者'` · userName 必填 | 5 min | T2 |
| T4 | **后端**：新增 `GET /api/auth/check-email` + **新增 `POST /api/auth/authenticate`** + 旧 login/register 加 deprecated 标记（内部 redirect） | 20 min | —（与 T1-T3 并行） |
| T5 | `pages/auth.tsx`（从 `pages/index.tsx` 迁移）+ **单一表单自动判断**（onBlur 调 check-email）+ 提交调 **authenticate** + 全 toast + **V3 K logo** + **SVG 图标** + v4 UI 精简 | 30 min | T1, T2, T4 |
| T6 | `pages/index.tsx` 改为重定向 `/` → `/auth` | 3 min | T5 |
| T7 | 前端测试 `__tests__/auth.test.tsx`（token 解码 + userName 注入 + toast mock + check-email mock + authenticate mock + mode 处理） | 15 min | T5, T6 |
| T8 | 后端测试 `test_auth_authenticate.py`（重写非 stub · 含 happy/4xx/race + check-email 200/400 + 旧 endpoint 兼容） | 10 min | T4 |

总估时：**~1.5h**（不含 verify-loop）

**依赖图**：

```
T1 ──→ T2 ──→ T3
            ↓
T4 ─────────→ T5 ──→ T6 ──→ T7
                              ↓
                              T8 (与 T7 可并行)
```

---

## 6. 验证策略（5 步 · spec.md § 6 验收）

| 层级 | 内容 | 命令 / 方法 |
|---|---|---|
| **L1 单元**（commit 级） | 每个 T 完成跑该 T 单测 | `cd frontend && npm test -- --run auth` / `cd backend && ./.venv/bin/python -m pytest tests/test_auth_authenticate.py -v` |
| **L2 集成**（commit 级） | TS 编译 + auth 模块无破坏 | `cd frontend && npx tsc --noEmit` |
| **L3 整合**（PR 级） | 全栈 pytest + vitest | `cd backend && ./.venv/bin/python -m pytest -q` + `cd frontend && npm test -- --run` |
| **L4 review**（活动） | writer/verifier 双 agent 校验 | CLAUDE.md § 6.7 · Agent tool · 失败自我修正（最多 2 轮） |
| **L5 staging** | dev server 起 + 浏览器真测 | `cd frontend && npm run dev` + 浏览器开 `http://localhost:3000/auth` + 手动测 5 个状态 |

---

## 7. 元信息

- **推荐方案**：A（8 个 commit · 按依赖顺序）
- **总估时**：~1.5h 实施 + ~30 min verify + ~15 min 复盘 = **~2h**
- **决策依赖**：13 项决策全部已拍板（decisions.md）· 决策 5/6/7/8 按推荐组合（用户"进第二步"默认接受）
- **风险总数**：🟢 4 + 🟡 5 + 🔴 0（v5 合并后增加 race condition 处理）
- **下一步**：→ [`tasks.md`](tasks.md)（3 步拆分 · 8 个原子任务 + 依赖图 + 测试映射）