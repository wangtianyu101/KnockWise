---
title: 任务拆分 · 注册/登录合并页 + 注册流程 Bug
type: tasks
step: 3
date: 2026-07-26
status: draft
tags: [tasks, auth, refactor-6]
related:
  - plan.md
  - spec.md
  - design-spec.md
  - decisions.md
---

# 任务拆分 · 注册/登录合并页 + 注册流程 Bug

> **路径模式**：refactor-6
> **推荐方案**：plan.md § 1 方案 A · **8 个 commit 按依赖顺序**
> **粒度**：每个 T ≤1h AI 工作量 · 1 个 commit · ≥1 测试用例 · DAG 无环

---

## 1. 任务粒度原则

```
✅ 每个任务 ≤1h AI 工作量
✅ 每个任务 1 个 commit
✅ 每个任务对应 ≥1 测试用例
✅ 任务间依赖关系明确（DAG · 无环 · 拓扑序）
✅ 实施前必跑 check-step.py tasks <path> 通过 DOD 校验
✅ writer/verifier 双 agent 校验（CLAUDE.md § 6.7）· 失败自我修正 ≤2 轮
```

---

## 2. 任务清单

### T1 · 加 sonner 依赖 + Toaster Provider（next/dynamic ssr:false 包裹） ✅ DONE

```markdown
- [ ] T1: ✅ DONE — commit `feat(auth): 任务初始化 + T1 引入 sonner`
  - **文件**:
    - `frontend/package.json`（加 `"sonner": "^1.7.4"` 到 dependencies · 实际装 1.7.4）
    - `frontend/components/ToastProvider.tsx`（新 · 封装 `<Toaster />` 来自 sonner · 用 `next/dynamic` + `ssr: false` 包裹避免 Next.js SSR 报错）
  - **测试**: `frontend/__tests__/toast-provider.test.tsx`（新 · 4 个 smoke test · export-shape + 真渲染 + position 透传 + 默认导出 === named 导出 · 4/4 PASS · vitest 2.1.9）
  - **依赖**: —
  - **估时**: 10 min
  - **产出**: 1 commit · `feat(auth): 任务初始化 + T1 引入 sonner` ✅ 已落地
  - **风险**: 🟡 sonner SSR（已用 next/dynamic 规避）· verifier 2 轮 FAIL 后修复 PASS（决策 5 同步 · tasks.md 描述与代码一致）
```
  - **文件**:
    - `frontend/package.json`（加 `"sonner": "^1.7.4"` 到 dependencies · 实际装 1.7.4）
    - `frontend/components/ToastProvider.tsx`（新 · 封装 `<Toaster />` 来自 sonner · 用 `next/dynamic` + `ssr: false` 包裹避免 Next.js SSR 报错）
  - **测试**: `frontend/__tests__/toast-provider.test.tsx`（新 · 4 个 smoke test · export-shape + 真渲染 + position 透传 + 默认导出 === named 导出）
  - **依赖**: —
  - **估时**: 10 min
  - **产出**: 1 commit · `feat(toast): 引入 sonner + ToastProvider 组件`
  - **风险**: 🟡 sonner SSR（已用 next/dynamic 规避）
```

### T2 · `_app.tsx` 包 `<Toaster />` + 注入 userName（JWT 解 email 前缀）

```markdown
- [ ] T2: _app.tsx 包 Toaster + 注入 userName
  - **文件**:
    - `frontend/lib/auth.ts`（新 · `decodeJwt(token)` 工具函数 + `getUserNameFromToken(token)` 派生函数 · 返回 email 前缀）
    - `frontend/pages/_app.tsx:40-64`（修改 · 包 `<ToastProvider />` + 从 token 解 userName 传给 Layout）
  - **测试**:
    - `frontend/__tests__/auth.test.ts`（新 · `decodeJwt` 解正常 token → 返回 payload · 解无效 token → 返回 null · `getUserNameFromToken` 派生 email 前缀）
  - **依赖**: T1
  - **估时**: 15 min
  - **产出**: 1 commit · `feat(auth): _app 包 Toaster + JWT 解码注入 userName`
  - **风险**: 🟢 低（纯函数 + 现有 _app.tsx 改动小）
```

### T3 · `Layout.tsx` 去 hardcode `'开发者'` · userName 必填

```markdown
- [ ] T3: Layout.tsx 去 hardcode · userName 必填
  - **文件**:
    - `frontend/components/v3/Layout/Layout.tsx:201-275`（修改 · `LayoutProps.userName` 改必填 · 删 `?? '开发者'` fallback）
  - **测试**:
    - TypeScript 编译检查强制必填（`npx tsc --noEmit`）
    - 现有 `frontend/__tests__/layout.test.tsx`（如无则新建）· 验证 userName 必填时正确显示
  - **依赖**: T2
  - **估时**: 5 min
  - **产出**: 1 commit · `fix(layout): 去 hardcode "开发者" · userName 必填`
  - **风险**: 🟡 TS 编译可能发现其他遗漏传 userName 的调用方（_app.tsx 已处理）
```

### T4 · 后端：check-email + authenticate + 旧 endpoint deprecated 兼容

```markdown
- [ ] T4: 后端 auth 模块重构（核心 · 含决策 13）
  - **文件**:
    - `backend/api/auth.py`（修改 · 重构）
      - 新增 `GET /api/auth/check-email` endpoint（~15 行）
      - 新增 `POST /api/auth/authenticate` endpoint（~40 行 · 含 query User by email → 不存在则 create → 验证密码/无密码 → 生成 token → 返回 mode）
      - 旧 `POST /api/auth/login` 加 `@deprecated` 标记 + 内部 redirect 到 `authenticate`
      - 旧 `POST /api/auth/register` 加 `@deprecated` 标记 + 内部 redirect 到 `authenticate`
      - 提取共享 `_authenticate_core(email, password, display_name)` 私有函数（DRY）
  - **测试**:
    - `backend/tests/api/test_auth_authenticate.py`（新 · 见 T8）
  - **依赖**: —（与 T1-T3 并行启动 · 独立模块）
  - **可并行**: T1, T2, T3
  - **估时**: 20 min
  - **产出**: 1 commit · `feat(auth): check-email + authenticate 单接口 · 旧 endpoint deprecated 兼容`
  - **风险**: 🟡 中（auth 模块核心 · 但有旧 endpoint 兜底）
```

### T5 · `pages/auth.tsx` 迁移 + 单一表单自动判断 + v4 UI 精简 + V3 K logo + SVG

```markdown
- [ ] T5: auth.tsx 迁移（核心 · 含决策 10/11/12）
  - **文件**:
    - `frontend/pages/auth.tsx`（新 · 从 `pages/index.tsx` 迁移 + 单一表单 + 自动判断 + v4 UI 精简）
    - `frontend/lib/api.ts:120-138`（修改 · 新增 `authenticate(email, password, display_name)` 函数 · 保留旧 `login`/`register` 不动）
  - **实现要点**（按 design-spec.md § 3 + § 4）:
    - 邮箱 input `onBlur` 调 `checkEmail(email)` → debounce 300ms → 调 `GET /api/auth/check-email`
    - 后端返回 `{exists: true}` → UI 切登录态（标题"欢迎回来" + 邮箱 readonly + 密码 autofocus + 按钮"登 录"）
    - 后端返回 `{exists: false}` → UI 切注册态（标题"加入 KnockWise" + 邮箱 readonly + 昵称字段 + 密码 + 按钮"注 册"）
    - 默认态（未失焦）：标题"欢迎来到 KnockWise" + 邮箱 + 密码 + 按钮"登录 / 注册"
    - 提交：调 `authenticate(email, password, display_name)`
      - 成功（响应 `mode="register"`）→ `toast.success("创建成功")` → 500ms → `router.push('/dashboard')`
      - 成功（响应 `mode="login"`）→ `toast.success("登录成功")` → 500ms → `router.push('/dashboard')`
      - 失败 → `toast.error(error.message)` → 不跳转
    - Logo = V3 K logo SVG（V3 sidebar 一致 · 不是闪电 ⚡）
    - Toast 图标 = SVG check / X（不是文字 ✓ ✕）
    - 卡片**只有标题**（无副标题 · 无检查状态指示器 · brand-block 无 tagline）
  - **测试**:
    - `frontend/__tests__/auth.test.tsx`（新 · 见 T7）
  - **依赖**: T1, T2, T4
  - **估时**: 30 min（核心任务 · 含 UI 重构）
  - **产出**: 1 commit · `feat(auth): auth 页迁移 + 单一表单自动判断 + v4 UI 精简 + V3 K logo + SVG 图标`
  - **风险**: 🟡 中（核心前端 · 但 mock 完整 · 失败可回滚）
```

### T6 · `pages/index.tsx` 改为重定向 `/` → `/auth`

```markdown
- [ ] T6: index.tsx 改重定向
  - **文件**:
    - `frontend/pages/index.tsx`（修改 · 整个组件改为 `useEffect(() => router.replace('/auth'))` + 返回空 loading）
  - **测试**: 浏览器手测验证（开发服务器起 `http://localhost:3000` → 访问 `/` 自动跳 `/auth`） · 或加 e2e（不强求）
  - **依赖**: T5
  - **估时**: 3 min
  - **产出**: 1 commit · `refactor(auth): / 重定向到 /auth 统一入口`
  - **风险**: 🟢 低（路由改动小 · 旧外链兼容）
```

### T7 · 前端测试 `__tests__/auth.test.tsx` 综合

```markdown
- [ ] T7: 前端 auth 综合测试
  - **文件**:
    - `frontend/__tests__/auth.test.ts`（扩展 · 加 `decodeJwt` + `getUserNameFromToken` 测试）
    - `frontend/__tests__/auth.test.tsx`（新 · 综合 T2 + T5 行为）
  - **测试**:
    - **JWT 解码**：
      - `decodeJwt('eyJ...')` 正常 token → 返回 `{sub, exp, email}` payload
      - `decodeJwt('invalid')` → 返回 null
    - **userName 派生**：
      - token 含 `email: 'wangtianyu@example.com'` → 派生 `wangtianyu`
      - token 无 email → 派生 `null`（fallback 处理）
    - **自动判断**：
      - 输 `newuser@example.com` + 失焦 → mock `checkEmail` 返回 `{exists: false}` → UI 切注册态（标题变化 + 昵称字段出现）
      - 输 `wangtianyu@example.com` + 失焦 → mock `checkEmail` 返回 `{exists: true}` → UI 切登录态（邮箱 readonly + 密码 autofocus）
    - **提交流程**：
      - 注册态提交 → mock `authenticate` 返回 `{mode: 'register'}` → `toast.success` 调用 + `router.push('/dashboard')` 调用
      - 登录态提交 → mock `authenticate` 返回 `{mode: 'login'}` → `toast.success` 调用 + `router.push('/dashboard')` 调用
      - 提交失败 → mock `authenticate` 抛错 → `toast.error` 调用 + 不跳转
    - **v4 UI 验收**：
      - 卡片**无副标题**（query `.card-subtitle` 不存在或 hidden）
      - 卡片**无检查状态指示器**（query `.check-status` 不存在）
      - brand-block **无 tagline**
      - 默认按钮文字 = "登录 / 注册"
      - Logo 是 SVG 不是字符
  - **依赖**: T5, T6
  - **估时**: 15 min
  - **产出**: 1 commit · `test(auth): 完整测试 · JWT 解码 + userName + 自动判断 + 提交流程 + v4 UI`
  - **风险**: 🟢 低（mock 完整）
```

### T8 · 后端测试 `test_auth_authenticate.py` 重写

```markdown
- [ ] T8: 后端 auth 测试重写
  - **文件**:
    - `backend/tests/api/test_auth_authenticate.py`（新 · 重写而非扩展 · 避免债务 9 stub 干扰）
    - 旧 `backend/tests/api/test_auth_register.py`（保留 · 加 deprecation 注释 · 标记由 `test_auth_authenticate.py` 覆盖）
  - **测试用例**:
    - **check-email endpoint**:
      - 邮箱存在 → 200 `{exists: true, email}`
      - 邮箱不存在 → 200 `{exists: false, email}`
      - 邮箱格式错 → 400
    - **authenticate endpoint**:
      - 邮箱不存在 + password ≥6 + display_name → 200 + 创建 user + 返回 token + `mode="register"`
      - 邮箱不存在 + display_name 缺省 → 200 + 创建 user（display_name = email 前缀）+ `mode="register"`
      - 邮箱存在 + 密码对 → 200 + 返回 token + `mode="login"`
      - 邮箱存在 + 密码错 → 401
      - 邮箱格式错 → 400
      - 密码 < 6 位 → 400
      - race condition（mock IntegrityError） → 409
    - **旧 endpoint 兼容**:
      - `POST /api/auth/login`（已 deprecated）→ 仍可用 → 内部 redirect 到 authenticate
      - `POST /api/auth/register`（已 deprecated）→ 仍可用 → 内部 redirect 到 authenticate
  - **依赖**: T4
  - **可并行**: T7
  - **估时**: 10 min
  - **产出**: 1 commit · `test(auth): authenticate + check-email 完整测试 · 旧 endpoint 兼容`
  - **风险**: 🟡 中（重写而非扩展 · 但旧文件名保留避免债务 9 扩大化）
```

---

## 3. 任务依赖图（DAG · 无环）

```
T1 (sonner) ──→ T2 (Toaster + userName) ──→ T3 (Layout 去 hardcode)
                                          ↓
T4 (后端 check-email + authenticate + deprecate)
   ↓
T5 (auth.tsx 迁移 + 单一表单 + v4 UI)
   ↓
T6 (index.tsx 重定向)
   ↓
T7 (前端测试) ──→ T8 (后端测试 · 与 T7 可并行)
```

**约束验证**：
- T1 是起点（sonner 必须先引入）
- T2 依赖 T1（必须有 Toaster 才能注入）
- T3 依赖 T2（必须先有 userName 注入才能让 Layout 接收）
- T4 独立（后端模块 · 与 T1-T3 **并行启动**）
- T5 依赖 T1+T2+T4（前端基础 + 后端新接口）
- T6 依赖 T5（必须先有 auth.tsx 才能让 index 重定向）
- T7 依赖 T5+T6（综合前端测试）
- T8 依赖 T4（后端测试 · 与 T7 并行）

---

## 4. 任务↔测试映射（Traceability · CLAUDE.md § 6.7）

| T# | 业务规则（BR） | 测试用例 | 测试文件 |
|---|---|---|---|
| T1 | BR-2 / BR-3（toast 基础） | Toaster 渲染 smoke | `__tests__/toast-provider.test.tsx` |
| T2 | BR-3 / BR-4（userName 注入） | decodeJwt + getUserNameFromToken | `__tests__/auth.test.ts` |
| T3 | BR-3（Header 真实 userName） | TS 强制必填 + userName 渲染 | `__tests__/layout.test.tsx`（或新建）|
| T4 | BR-1 / BR-6 / BR-10（auth 接口） | 单元 + 集成（含 T8）| `tests/api/test_auth_authenticate.py` |
| T5 | BR-1 / BR-2 / BR-6 / BR-7 / BR-8 / BR-9（核心流程） | 端到端 mock 测试（含 T7）| `__tests__/auth.test.tsx` |
| T6 | BR-5（路由迁移） | 浏览器手测 | L5 staging |
| T7 | BR-1~9 全部（前端综合） | 综合 | `__tests__/auth.test.tsx` |
| T8 | BR-1 / BR-6 / BR-10（后端综合） | 综合 | `tests/api/test_auth_authenticate.py` |

---

## 5. 实施顺序（commit 历史预期）

```
1. feat(toast): 引入 sonner + ToastProvider 组件                    (T1)
2. feat(auth): _app 包 Toaster + JWT 解码注入 userName              (T2)
3. fix(layout): 去 hardcode "开发者" · userName 必填                (T3)
4. feat(auth): check-email + authenticate 单接口 · 旧 endpoint deprecated 兼容  (T4)
5. feat(auth): auth 页迁移 + 单一表单自动判断 + v4 UI 精简 + V3 K logo + SVG 图标  (T5)
6. refactor(auth): / 重定向到 /auth 统一入口                        (T6)
7. test(auth): 完整测试 · JWT 解码 + userName + 自动判断 + 提交流程 + v4 UI  (T7)
8. test(auth): authenticate + check-email 完整测试 · 旧 endpoint 兼容  (T8)
```

**每 commit 前自检清单**：
- [ ] pytest / vitest 全绿（该 T 范围）
- [ ] TypeScript 编译通过（前端 T）
- [ ] pre-commit hook 通过（含 DOD 校验）
- [ ] writer/verifier 双 agent 校验（CLAUDE.md § 6.7）· 失败则循环修复（≤2 轮）
- [ ] 不引入 stub 假绿灯（CLAUDE.md § 6.3）

---

## 6. 元信息

- **任务总数**：8
- **总估时**：~1.5h 实施 + ~30 min verify-loop + ~15 min 复盘 = **~2h**
- **commit 数**：8
- **测试文件**：4 个（3 新 + 1 修改）
- **依赖文件**：11 个（修改 7 + 新建 4）
- **关键任务**：T5（前端核心 · 30 min）+ T4（后端核心 · 20 min）
- **并行机会**：T4 与 T1-T3 · T7 与 T8
- **关联**：
  - [`plan.md`](plan.md)（推荐方案 A · 8 commit）
  - [`spec.md`](spec.md)（业务规格 · 13 BR · 7 AC）
  - [`design-spec.md`](design-spec.md)（v4 视觉精简）
  - [`decisions.md`](decisions.md)（13 项决策）
- **下一步**：进 4 步实施（writer/verifier 双 agent · TDD 红→绿→refactor）