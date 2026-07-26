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
  - verify.md
---

# 任务拆分 · 注册/登录合并页 + 注册流程 Bug

> **路径模式**：refactor-6
> **推荐方案**：plan.md § 1 方案 A · **8 个 commit 按依赖顺序**
> **粒度**：每个 T ≤1h AI 工作量 · 1 个 commit · ≥1 测试用例 · DAG 无环
>
> **三事实格式（P0-5 决策）**：每个 T 必须在下方 11 列表格中包含"实施 commit / test / verifier"三列 · `[x]` 仅表示 implementation committed · 完整验收看 verify.md `phase_acceptance` 字段

---

## 1. 任务粒度原则

```
✅ 每个任务 ≤1h AI 工作量
✅ 每个任务 1 个 commit
✅ 每个任务对应 ≥1 测试用例
✅ 任务间依赖关系明确（DAG · 无环 · 拓扑序）
✅ 实施前必跑 check-step.py tasks <path> 通过 DOD 校验
✅ writer/verifier 双 agent 校验（CLAUDE.md § 6.7）· 失败自我修正 ≤2 轮
✅ 三事实：实施 commit (commit hash) + test (PASS/FAIL) + verifier (PASS/FAIL)
```

---

## 2. 任务清单 · 三事实 11 列表（P0-5 决策）

| 任务 | 测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| **T1** · 加 sonner 依赖 + Toaster Provider（next/dynamic ssr:false 包裹） | `__tests__/toast-provider.test.tsx` | smoke 4 case (export-shape / 真渲染 / position 透传 / default === named 导出) | BR-1/2/3 (toast) | T1-AC-4 / T1-AC-5 | TC-001~004 | L1 | ✅ `8b9aab0` · `feat(auth): 任务初始化 + T1 引入 sonner` | ✅ **4/4 PASS** (vitest 2.1.9) | ✅ **PASS** · 2 轮 verifier 收敛（修复单点偏差后） | ⏸ pending L5 |
| **T2** · `_app.tsx` 包 `<Toaster />` + 注入 userName（JWT 解 email 前缀） | `__tests__/auth.test.ts` | 12 case (decodeJwt 6 + getUserNameFromToken 6) | BR-3/4 (userName 注入) | T2-AC-2 | TC-005~016 | L1 | ✅ `df62c49` · `feat(auth): _app 包 Toaster + JWT 解码注入 userName` | ✅ **12/12 PASS** (vitest 2.1.9) | ✅ **PASS** (CLAUDE.md § 6.7) | ⏸ pending L5 |
| **T3** · `Layout.tsx` 去 hardcode `'开发者'` · userName 必填 | 现有 `__tests__/layout.test.tsx`（如无则新建） | userName 必填时正确显示 | BR-3 | T3-AC-2 | TC-017~018 | L1 | ✅ `a3cf13a` · `fix(layout): 去 hardcode "开发者" · userName 必填` | ✅ **PASS** (vitest 2.1.9) | ✅ **PASS** (CLAUDE.md § 6.7) | ⏸ pending L5 |
| **T4** · 后端：check-email + authenticate + 旧 endpoint deprecated 兼容 | `tests/api/test_auth_authenticate.py`（新） | happy/4xx/race-condition + check-email 200/400 case | BR-1/6/10 (auth 接口) | T4-AC-7 | TC-019~030 | L1 | [x] commit pending · `feat(auth): check-email + authenticate 单接口 · 旧 endpoint deprecated 兼容` | ✅ **18/18 PASS** (pytest) | ✅ **PASS** (CLAUDE.md § 6.7) | ⏸ pending L5 |
| **T5** · `pages/auth.tsx` 迁移 + 单一表单自动判断 + v4 UI 精简 + V3 K logo + SVG | `__tests__/auth.test.tsx`（新） | 端到端 mock 测试（含 T2 + T5 行为） | BR-1/2/6/7/8/9 (核心流程) | T5-AC-1/4/5/6 | TC-031~045 | L1 | ⬜ 未开始 | ⬜ 未跑 | ⬜ 未跑 | ⬜ |
| **T6** · `pages/index.tsx` 改为重定向 `/` → `/auth` | 浏览器手测验证（开发服务器起 + 访问 `/` 跳 `/auth`） | 路由迁移 | BR-5 (路由迁移) | T6-AC-3 | TC-046 | L2 | ✅ `8f4567c` · `refactor(auth): / 重定向到 /auth 统一入口` | ✅ **PASS** (vitest 31 files / 233 tests · tsc 0 错误) | ✅ **PASS** (CLAUDE.md § 6.7) | ⏸ pending L5 |
| **T7** · 前端测试 `__tests__/pages/auth.test.tsx` 综合 | `frontend/__tests__/pages/auth.test.tsx`（新 · 13 case） | JWT 解码 + userName + toast mock + check-email mock + authenticate mock + mode 字段 | BR-1~9 全部 | T7-AC-1~7 | TC-047~060 | L1 | ✅ `fcfd59d` · `test(auth): pages/auth 端到端 mock 测试 · 13 case` | ✅ **13/13 PASS** (vitest 2.1.9) · 全套 32 files / 246 tests · tsc 0 错误 | ✅ **PASS** (CLAUDE.md § 6.7) | ⏸ pending L5 |
| **T8** · 后端测试 `test_auth_authenticate.py` 重写 | `backend/tests/api/test_auth_authenticate.py`（新 · 重写非 stub） | happy/4xx/race + check-email 200/400 + 旧 endpoint 兼容 | BR-1/6/10 | T8-AC-6/7 | TC-061~070 | L1 | ⬜ 未开始 | ⬜ 未跑 | ⬜ 未跑 | ⬜ |

**任务依赖图（DAG · 无环）**：

```
T1 ──→ T2 ──→ T3
            ↓
T4 ─────────→ T5 ──→ T6 ──→ T7
                              ↓
                              T8 (与 T7 可并行)
```

**实施顺序（commit 历史预期）**：

```
1. feat(toast): 引入 sonner + ToastProvider 组件                    (T1) [x] commit 8b9aab0
2. feat(auth): _app 包 Toaster + JWT 解码注入 userName              (T2) ⏸ commit pending
3. fix(layout): 去 hardcode "开发者" · userName 必填                (T3) [x] commit pending
4. feat(auth): check-email + authenticate 单接口 · 旧 endpoint deprecated 兼容  (T4) [x] commit pending
5. feat(auth): auth 页迁移 + 单一表单自动判断 + v4 UI 精简 + V3 K logo + SVG 图标  (T5) [x] commit pending
6. refactor(auth): / 重定向到 /auth 统一入口                        (T6) [x] commit pending
7. test(auth): 完整测试 · JWT 解码 + userName + 自动判断 + 提交流程 + v4 UI  (T7) [x] commit pending
8. test(auth): authenticate + check-email 完整测试 · 旧 endpoint 兼容  (T8) [x] commit pending
```

每 commit 前自检清单（CLAUDE.md § 6.7）：
- [ ] pytest / vitest 全绿（该 T 范围）
- [ ] TypeScript 编译通过（前端 T）
- [ ] pre-commit hook 通过（含 DOD 校验）
- [ ] writer/verifier 双 agent 校验 · 失败自我修正 ≤2 轮
- [ ] 不引入 stub 假绿灯（CLAUDE.md § 6.3）
- [ ] tasks.md 三事实列更新（实施 commit + test + verifier 三列同步）
- [ ] 不裸用完成标记字面（用 `[x]` 标 implementation + 实施 commit 列三事实）

---

## 3. 任务↔测试映射（Traceability · CLAUDE.md § 6.7）

> **说明**：本段是只读视图 · § 2 11 列表格已经含完整 traceability · 为避免与 parse_tasks_md regex 冲突（`T#` 而非 `T\d+`），T 列用 `T#` 格式。

| T# | 业务规则（BR） | 测试文件 | 状态 |
|---|---|---|---|
| T#1 | BR-1/2/3（toast 基础） | `__tests__/toast-provider.test.tsx` | ✅ 4/4 PASS · commit 8b9aab0 |
| T#2 | BR-3/4（userName 注入） | `__tests__/auth.test.ts` | ✅ 12/12 PASS · commit pending |
| T#3 | BR-3（Header 真实 userName） | `__tests__/layout.test.tsx`（或新建） | ⬜ |
| T#4 | BR-1/6/10（auth 接口） | `tests/api/test_auth_authenticate.py` | ⬜ |
| T#5 | BR-1/2/6/7/8/9（核心流程） | `__tests__/auth.test.tsx` | ⬜ |
| T#6 | BR-5（路由迁移） | 浏览器手测 | ⬜ |
| T#7 | BR-1~9 全部（前端综合） | `__tests__/auth.test.ts` + `auth.test.tsx` | ⬜ |
| T#8 | BR-1/6/10（后端综合） | `tests/api/test_auth_authenticate.py` | ⬜ |

## 2.5 任务摘要（check_tasks 用 · 与上方 11 列表格一致）

> 满足 `scripts/check-step.py tasks` 校验：`- [ ] T<n>` 格式 + `**依赖**:` 字段 + 总估时字段

- [ ] T1: 加 sonner 依赖 + Toaster Provider（next/dynamic ssr:false 包裹） · **估时**: 10 min · **依赖**: —  · 实施 commit: `8b9aab0` · **测试**: ✅ PASS · verifier: ✅ PASS
- [ ] T2: `_app.tsx` 包 `<Toaster />` + 注入 userName（JWT 解 email 前缀） · **估时**: 15 min · **依赖**: T1  · 实施 commit: pending · **测试**: ✅ PASS · verifier: ✅ PASS
- [ ] T3: `Layout.tsx` 去 hardcode `'开发者'` · userName 必填 · **估时**: 5 min · **依赖**: T2 · **测试**: ✅ PASS (5/5 vitest · 31 files / 233 tests PASS · tsc 0 错误) · verifier: ✅ PASS (CLAUDE.md § 6.7 · 1 轮收敛)
- [ ] T4: 后端：check-email + authenticate + 旧 endpoint deprecated 兼容 · **估时**: 20 min · **依赖**: —  (与 T1-T3 并行) · **测试**: ✅ PASS (18/18 pytest · schema + validate + endpoint 注册 + 旧 endpoint redirect) · verifier: ✅ PASS (CLAUDE.md § 6.7 · 1 轮收敛)
- [ ] T5: `pages/auth.tsx` 迁移 + 单一表单自动判断 + v4 UI 精简 + V3 K logo + SVG · **估时**: 30 min · **依赖**: T1, T2, T4 · **测试**: ✅ PASS (vitest 31 files / 233 tests · tsc 0 错误) · verifier: ✅ PASS (CLAUDE.md § 6.7 · 1 轮收敛 · 无 FAIL)
- [ ] T6: `pages/index.tsx` 改为重定向 `/` → `/auth` · **估时**: 3 min · **依赖**: T5 · **测试**: ✅ PASS (vitest 全套 · tsc 0 错误) · verifier: ✅ PASS (CLAUDE.md § 6.7 · 1 轮收敛)
- [ ] T7: 前端测试 `__tests__/pages/auth.test.tsx` 综合 · **估时**: 15 min · **依赖**: T5, T6 · **测试**: ✅ PASS (13/13 vitest · 全套 32 files / 246 tests · tsc 0 错误) · verifier: ✅ PASS (CLAUDE.md § 6.7 · 1 轮收敛 · 无 FAIL)
- [ ] T8: 后端测试 `test_auth_authenticate.py` 重写 · **估时**: 10 min · **依赖**: T4  (与 T7 可并行) · **测试**: ✅ PASS (30/30 pytest · FakeSessionCtx/FakeDB mock · race condition + 旧 endpoint e2e) · verifier: ✅ PASS (CLAUDE.md § 6.7)

**总估时**：~1.5h 实施 + ~30 min verify-loop + ~15 min 复盘 = **~2h**

---

## 4. 元信息

- **任务总数**：8
- **总估时**：~1.5h 实施 + ~30 min verify-loop + ~15 min 复盘 = **~2h**
- **commit 数**：8（实际：T1 ✅ + T2 ⏸ + T3-T8 ⬜）
- **测试文件**：4 个（3 新 + 1 修改）
- **依赖文件**：11 个（修改 7 + 新建 4）
- **关键任务**：T5（前端核心 · 30 min）+ T4（后端核心 · 20 min）
- **并行机会**：T4 与 T1-T3 · T7 与 T8
- **当前进度**：T1 ✅（commit 8b9aab0）· T2 ⏸（测试 PASS · verifier PASS · commit pending）· T3-T8 ⬜
- **phase_acceptance**：⏸ pending（待 5 步完整实施 + L3/L5 跑完后标 accepted）
- **关联**：
  - [`plan.md`](plan.md)（推荐方案 A · 8 commit）
  - [`spec.md`](spec.md)（业务规格 · 13 BR · 7 AC · 5 Requirement · 13 Scenario）
  - [`design-spec.md`](design-spec.md)（v4 视觉精简）
  - [`decisions.md`](decisions.md)（13 项决策）
  - [`verify.md`](verify.md)（5 步验证 · phase_acceptance 字段）