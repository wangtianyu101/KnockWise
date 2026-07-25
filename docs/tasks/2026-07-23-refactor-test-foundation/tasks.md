---
title: 测试基础架构 L1-L5 + 追溯 + Fixture · 任务拆分
type: tasks
step: 3
date: 2026-07-23
status: ✅ closed
tags: [refactor, test-foundation, tasks]
related:
  - research.md
  - spec.md
  - plan.md
  - decisions.md
---

# 任务拆分 · 测试基础架构三位一体（P1-1/2/3）

> 路径模式：refactor-6 · 1 步 spec + 2 步 plan 已落地

---

## 任务清单（可勾选）

- [ ] T1: 测试先行：3 套失败 pytest — **估时**: 25 min · **commit**: `test(p1): 3 套失败 pytest` · **测试**: 20 case（10 verify + 8 fixture + 2 vitest）· **依赖**: 无
- [ ] T2: testing-rules.md § 6.5.1 + § 6.5.2 — **估时**: 15 min · **commit**: `refactor(p1-1): L1-L5 边界主账` · **测试**: T1 rules 相关 case 转绿 · **依赖**: T1
- [ ] T3: 4 模板更新（verify / tasks / product-doc / verify-template）— **估时**: 30 min · **commit**: `refactor(p1): 4 模板同步` · **测试**: 模板 sanity + T1 部分 · **依赖**: 无
- [ ] T4: scripts/check-step.py verify step + 10 不变量 — **估时**: 30 min · **commit**: `refactor(p1-2): check-step traceability 10 不变量` · **测试**: T1 verify 10 case 转绿 · **依赖**: T1
- [ ] T5: frontend/vitest.setup.ts 加 block_external_network — **估时**: 15 min · **commit**: `refactor(p1): vitest block_external_network` · **测试**: T1 vitest 2 case 转绿 · **依赖**: T1
- [ ] T6: backend/tests/e2e/conftest.py 8 项契约 fixture — **估时**: 45 min · **commit**: `test(p1-3): e2e fixture 8 契约` · **测试**: T1 fixture 8 case 转绿 · **依赖**: T1
- [ ] T7: 全套回归 + EXEMPT 兼容 — **估时**: 20 min · **commit**: `test(p1): 全套回归 + EXEMPT` · **测试**: pytest backend/tests + vitest 全绿 · **依赖**: T2, T3, T4, T5, T6
- [ ] T8: verify.md + retro.md — **估时**: 25 min · **commit**: `docs(p1): verify + retro` · **测试**: 文档产物（无自动化测试）· **依赖**: T7

**总估时**：~3h 25min

---

## 任务总览

| ID | 任务 | 估时 | 状态 | 依赖 |
|---|---|---|---|---|
| T1 | 测试先行：3 套失败 pytest | 25 min | 🔴 待做 | 无 |
| T2 | testing-rules.md § 6.5.1 + § 6.5.2 | 15 min | 🔴 待做 | T1 部分 |
| T3 | 4 模板更新（verify / tasks / product-doc / verify-template）| 30 min | 🔴 待做 | 无 |
| T4 | scripts/check-step.py verify step + 10 不变量 | 30 min | 🔴 待做 | T1 |
| T5 | frontend/vitest.setup.ts 加 block_external_network | 15 min | 🔴 待做 | T1 |
| T6 | backend/tests/e2e/conftest.py 8 项契约 fixture | 45 min | 🔴 待做 | T1 |
| T7 | 全套回归 + EXEMPT 兼容 | 20 min | 🔴 待做 | T2-T6 |
| T8 | verify.md + retro.md | 25 min | 🔴 待做 | T7 |

**总估时**：~3h 25min

---

## 任务依赖图

```text
T1 (test fail)
 ├─► T2 (rules) ─┐
 ├─► T4 (checker)┤
 ├─► T5 (vitest) ┼─► T7 (regression) ─► T8 (verify+retro)
 └─► T6 (e2e)   ┘
                    ▲
                    └─ T3 (templates) ┘
```

---

## T1 · 测试先行：3 套失败 pytest

### 描述
按 spec § 7 写 3 套失败测试：check-step verify 10 不变量 + e2e fixture 8 契约 + vitest 网络拦截。

### 步骤
1. 在 `backend/tests/test_check_step.py` 加 `test_verify_step_10_invariants`（10 case）
2. 创建 `backend/tests/test_e2e_fixture.py`（8 case 测 8 项契约）
3. 创建 `frontend/__tests__/setup.test.ts`（2 case 测网络拦截）
4. 跑 → 全部应红

### 估时
25 min

---

## T2 · testing-rules.md § 6.5.1 + § 6.5.2

### 描述
加 L1-L5 边界主账表 + Provider 边界例外条款。

### 步骤
1. 改 `docs/rules/testing-rules.md`
2. 在 § 6.5 后加 § 6.5.1 5 层表
3. 加 § 6.5.2 Provider 边界例外条款
4. 跑 T1 相关测试

### 估时
15 min

---

## T3 · 4 模板更新

### 描述
按 spec § 1 REQ-7 同步更新 4 个模板。

### 步骤
1. `docs/templates/verify-template.md` § 0.4 加 Traceability 10 列 + ID 规则
2. `docs/templates/tasks-template.md` § 4 任务↔测试映射加 REQ/SCN/TC 列
3. `docs/templates/product-doc-template.md` § 5 8 必填 + 4 可选（与 P1-8 同步）
4. 跑模板相关 sanity

### 估时
30 min

---

## T4 · scripts/check-step.py verify step + 10 不变量

### 描述
在 `check-step.py` 加 `traceability` step，验证 10 条不变量。

### 步骤
1. 改 `scripts/check-step.py`
2. 加 `check_traceability(content)` 函数
3. 在 CHECKS 字典注册 `'traceability': check_traceability`
4. 跑 T1 verify 测试

### 估时
30 min

---

## T5 · frontend/vitest.setup.ts 加 block_external_network

### 描述
默认拦截真网络请求，单测需要时显式 `__allowNetwork__` 标记。

### 步骤
1. 改 `frontend/vitest.setup.ts`
2. 加 `beforeEach`/`afterEach` 拦截 + `__allowNetwork__` 标记
3. 跑 T1 vitest 测试

### 估时
15 min

---

## T6 · backend/tests/e2e/conftest.py 8 项契约 fixture

### 描述
新建 conftest.py 实现 8 项 E2E fixture 契约（DB 边界、用户命名空间、登录态、Digest 预生成、seed 只读、时间固定、清理幂等、并行隔离）。

### 步骤
1. 创建 `backend/tests/e2e/conftest.py`
2. 实现 8 个 fixture + 8 个 helper 函数
3. 跑 T1 e2e fixture 测试

### 估时
45 min

---

## T7 · 全套回归 + EXEMPT 兼容

### 描述
跑所有测试 + EXEMPT 兼容性 + pre-commit 端到端。

### 步骤
1. 跑 `pytest backend/tests/` 全绿
2. 跑 frontend vitest 全绿
3. EXEMPT 兼容性：12 老任务 + archive 仍豁免
4. pre-commit 端到端
5. P0-7 task.yaml 契约仍通过

### 估时
20 min

---

## T8 · verify.md + retro.md

### 描述
5 步 verify + 6 步 retro 落地。

### 步骤
1. 写 `verify.md`：7 个 verify 场景结果
2. 写 `retro.md`：实施偏差 + 改进项 + memory 候选

### 估时
25 min

---

## 任务↔Spec 映射

| Task | Spec REQ | Spec S |
|---|---|---|
| T1 | REQ-3, REQ-4, REQ-5, REQ-6 | S-2, S-3, S-4 |
| T2 | REQ-1, REQ-2 | S-1 |
| T3 | REQ-4, REQ-5, REQ-7 | S-3, S-5 |
| T4 | REQ-4, REQ-5 | S-3 |
| T5 | REQ-3 | S-2 |
| T6 | REQ-6 | S-4 |
| T7 | REQ-8 | S-6, S-7 |
| T8 | — | 全部 |

## 任务↔Evidence 映射

| Task | 自动化测试 | E2E |
|---|---|---|
| T1 | unit: 20 case (10 verify + 8 fixture + 2 vitest) | — |
| T2-T6 | unit: T1 全绿 | — |
| T7 | unit: pytest backend/tests/ | e2e: pre-commit 端到端 |
| T8 | 文档产物 | — |

---

## 任务状态跟踪

| # | 任务 | 状态 | 实施 commit | 实际耗时 | 偏差分析 |
|---|---|---|---|---|---|
| T1 | 测试先行 | 🔴 待做 | — | — | — |
| T2 | testing-rules.md | 🔴 待做 | — | — | — |
| T3 | 4 模板 | 🔴 待做 | — | — | — |
| T4 | verify step | 🔴 待做 | — | — | — |
| T5 | vitest.setup.ts | 🔴 待做 | — | — | — |
| T6 | e2e/conftest.py | 🔴 待做 | — | — | — |
| T7 | 回归 + EXEMPT | 🔴 待做 | — | — | — |
| T8 | verify+retro | 🔴 待做 | — | — | — |

实施开始后按 T1→T2→T3→T4→T5→T6→T7→T8 顺序填写实际 commit hash + 耗时 + 偏差。
