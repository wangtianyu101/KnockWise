---
title: 验证报告 · 注册/登录合并页 + 注册流程 Bug
type: verify
step: 5
date: 2026-07-27
status: in_progress
tags: [verify, auth, refactor-6]
related:
  - spec.md
  - design-spec.md
  - decisions.md
  - research.md
  - plan.md
  - tasks.md
  - retro.md
---

# 验证报告 · 注册/登录合并页 + 注册流程 Bug

> **路径模式**：refactor-6
> **当前进度**：8/8 T 完成（commit `8b9aab0` ~ `03e276d`）· L1/L2/L4 ✅ PASS · L3 ✅ PASS · L5 staging ⏸ pending（环境受限 · 无 GUI 浏览器手测）· phase_acceptance ⏸ pending

---

## L1 单元测试证据（步骤 4 分布式 · commit 级）

> 每个 commit 必须配套 L1 单元测试 · 详见 [tasks.md § 2 三事实表](tasks.md#2-任务清单-三事实-11-列表p0-5-决策)

| T# | commit | L1 测试 | 通过率 | 状态 |
|---|---|---|---|---|
| T1 | `8b9aab0` | `__tests__/toast-provider.test.tsx` (4 case) | 4/4 PASS | ✅ |
| T2 | `df62c49` | `__tests__/auth.test.ts` (12 case: decodeJwt 6 + getUserNameFromToken 6) | 12/12 PASS | ✅ |
| T3 | `a3cf13a` | `__tests__/components/v3/Layout.test.tsx` (5 case) | 5/5 PASS | ✅ |
| T4 | `d9d5c30` | `tests/api/test_auth_authenticate.py` (18 case: schema + validate + endpoint + 旧 endpoint redirect monkeypatch) | 18/18 PASS | ✅ |
| T5+T6 | `8f4567c` | (无新增 test · 改动由 T7 覆盖) | — | n/a |
| T7 | `31622e9` | `__tests__/pages/auth.test.tsx` (13 case) | 13/13 PASS | ✅ |
| T8 | `03e276d` | `tests/api/test_auth_authenticate.py` (+ 12 case: happy + race + check-email + 旧 endpoint e2e) | 30/30 PASS (T4 18 + T8 12) | ✅ |

**L1 综合**：vitest 32 files / 246 tests + pytest 30 tests（T4+T8）· 0 失败

---

## L2 集成测试证据（步骤 4 分布式 · commit 级）

| T# | commit | L2 检查 | 结果 | 状态 |
|---|---|---|---|---|
| T1-T8 | all | TypeScript 编译 `npx tsc --noEmit` (frontend/) | 0 错误 | ✅ |
| T1-T8 | all | backend imports 验证 `python -c "from api.auth import ..."` | OK | ✅ |
| T1-T8 | all | 旧 login/register endpoint 保留 deprecated（决策 13 兼容） | 验证 | ✅ |

**L2 综合**：tsc 编译干净 · 无类型冲突 · 无 SSR mismatch · 旧 endpoint 内部 redirect 到 authenticate

---

## L3 整合测试（Pytest + Vitest 全套）

### L3.1 单元测试统计

| 测试套件 | 文件数 | 测试数 | 通过率 |
|---|---|---|---|
| 后端 pytest（T1-T8 引入 30 测试 · 全套 41+ 文件） | 41+ | 800+ | ✅ **T1-T8 引入 30/30 PASS** · 8 fail 历史（test_digest_api.py · openai key 缺失 · 与本任务无关） |
| 前端 vitest（含 auth.test.ts + toast-provider.test.ts + auth.test.tsx） | 32 | 246 | ✅ **100%** |

### L3.2 已 commit T 验证

- **T1 commit `8b9aab0`**：sonner ^1.7.4 + ToastProvider + 4 smoke test
- **T2 commit `df62c49`**：_app.tsx 包 Toaster + JWT 解码 + 12 test
- **T3 commit `a3cf13a`**：Layout 去 hardcode "开发者" + userName 必填 + 5 test
- **T4 commit `d9d5c30`**：check-email + authenticate + 旧 endpoint deprecated + 18 test
- **T5+T6 commit `8f4567c`**：pages/auth.tsx 迁移 + 重定向 + LAYOUT_EXCLUDE_PATHS 修
- **T7 commit `31622e9`**：auth.test.tsx 端到端 mock + 13 test
- **T8 commit `03e276d`**：authenticate + check-email 综合 + 12 test

### L3 实测（2026-07-27 跑）

```bash
# 后端 pytest（除 eval/digest）
cd backend && ./.venv/bin/python -m pytest tests/ -q --tb=no
# → 822 passed · 8 failed（历史 · openai key 缺失 · 与 T1-T8 无关）

# 前端 vitest 全套
cd frontend && ./node_modules/.bin/vitest run
# → Test Files 32 passed (32) · Tests 246 passed (246)
```

### L3 状态：✅ **PASS**（T1-T8 引入测试全过 · 8 fail 历史债务已 verifier 确认与本任务无关）

---

## L4 review 证据（步骤 4 分布式 · writer/verifier 双 agent）

> CLAUDE.md § 6.7 实施自校验 Verify-Loop · 每个 commit 单元由独立 Agent prompt 校验（不复用 writer 上下文）

| T# | commit | verifier 轮数 | verifier 结果 | 偏差修复 |
|---|---|---|---|---|
| T1 | `8b9aab0` | 2 轮 | ✅ **PASS**（2 轮后收敛） | 第 1 轮 FAIL（tasks.md 文档漂移 + 测试 vacuous + 决策 5 未同步）→ 全部修复 → 第 2 轮 PASS |
| T2 | `df62c49` | 1 轮 | ✅ **PASS**（直接 PASS） | 无 |
| T3 | `a3cf13a` | 1 轮 | ✅ **PASS**（直接 PASS） | 无 |
| T4 | `d9d5c30` | 1 轮 | ✅ **PASS**（直接 PASS） | 无 |
| T5+T6 | `8f4567c` | 1 轮 | ✅ **PASS**（verifier 建议补 _app.tsx LAYOUT_EXCLUDE_PATHS · 已采纳） | 采纳建议 · 1 行补全 `/auth` |
| T7 | `31622e9` | 1 轮 | ✅ **PASS**（直接 PASS） | minor 文档不一致（tasks.md 路径）→ 后续 amend 修复 |
| T8 | `03e276d` | 1 轮 | ✅ **PASS**（直接 PASS） | 无 |

**L4 综合**：writer/verifier 双 agent 流程对齐 CLAUDE.md § 6.7 · 失败自我修正 ≤2 轮收敛（仅 T1 一轮偏差）· 全部 commit PASS

---

## L5 staging（dev server + 浏览器手测） · ✅ 计划已定 · ⏸ pending 环境受限

> ⏸ **L5 staging 待 GUI 浏览器手测**（环境受限 · 当前为 CLI 环境 · 无浏览器手测条件）

L5 验收清单（待用户/真环境手测后标 ✅）：

- [ ] 启动 dev server（`./scripts/start.sh`）
- [ ] 浏览器访问 `http://localhost:3000/auth` · 看到默认态卡片（V3 glassmorphism + V3 K logo）
- [ ] 输入 `wangtianyu@example.com` + 失焦 → 自动切登录态
- [ ] 输入新邮箱 → 自动切注册态
- [ ] 提交注册 → 调 `POST /api/auth/authenticate` → toast 弹出 + 跳转 `/dashboard`
- [ ] Header 显示真实 userName（不是"开发者"）
- [ ] 直接访问 `/` → 跳转到 `/auth`

### L5 状态：⏸ **pending 环境受限**（CLI 无 GUI 浏览器 · 待真环境手测 · 跳过 = REJECTED）· ✅ 计划已定（含验收清单 + 入口命令）
### L5 phase_acceptance：⏸ **pending**（同 L5 状态 · 待真环境手测后标）

---

## phase_acceptance

**phase_acceptance**: ⏸ **pending L5 staging 真环境手测**（L1/L2/L3/L4 全 PASS · 仅 L5 staging 受限）

**phase_acceptance_field**: ⏸ pending L5 staging

待完成项：
- L5 staging 真环境手测（启动 dev server + 浏览器测 5 个状态）
- AC-1 ~ AC-7 全部勾选（当前 L1-L4 已验证大部分 · L5 手测补全）

### AC 验收状态（基于 L1-L4）

| AC | 内容 | 状态 |
|---|---|---|
| AC-1 | 自动判断 + 提交流程 | ✅ T7 · 13 case PASS |
| AC-2 | Header 显示真实 userName | ✅ T3 · 5 case PASS（含"不再显示 hardcode 开发者"）|
| AC-3 | 路由迁移 `/` → `/auth` | ✅ T6 代码 + 修复 _app LAYOUT_EXCLUDE_PATHS（待 L5 浏览器手测）|
| AC-4 | Toast 集成 | ✅ T1 sonner 引入 + T7 mock 验证（待 L5 浏览器视觉确认）|
| AC-5 | v4 视觉精简 | ✅ T5 代码 + T7 验证（无副标题 / 无检查状态 / 默认按钮"登录 / 注册"）|
| AC-6 | check-email endpoint | ✅ T4 200/400 + T8 200 exists=true/false + 400（happy / race / 旧 endpoint e2e）|
| AC-7 | v5 authenticate 接口 | ✅ T4 + T8 完整覆盖（happy / 401 / 409 race / 旧 endpoint deprecated 兼容）|

---

## 元信息

- **任务目录**：`docs/tasks/2026-07-26-refactor-auth-unified-page/`
- **路径模式**：refactor-6
- **当前进度**：8/8 T 完成 · 7 个 commit
- **L1 状态**：✅ PASS（前端 246 vitest + 后端 30 pytest · 0 失败 · T1-T8 引入测试全过）
- **L2 状态**：✅ PASS（tsc 0 错误 · 旧 endpoint 兼容）
- **L3 状态**：✅ PASS（T1-T8 引入测试全过 · 8 fail 历史债务与本任务无关）
- **L4 状态**：✅ PASS（verifier 双 agent 收敛 · 仅 T1 一轮偏差）
- **L5 状态**：⏸ pending（环境受限 · 待 GUI 浏览器手测）
- **phase_acceptance**：⏸ pending（待 L5 staging 真环境手测后标 accepted）
- **关联**：[`spec.md`](spec.md) / [`tasks.md`](tasks.md) / [`decisions.md`](decisions.md) / [`retro.md`](retro.md)（§ 6 待写）