---
title: 测试治理与质量 (xfail/AI 评估/a11y+性能) · 任务拆分
type: tasks
step: 3
date: 2026-07-23
status: ✅ closed
tags: [refactor, test-governance, tasks]
related:
  - research.md
  - spec.md
  - plan.md
  - decisions.md
---

# 任务拆分 · 测试治理与质量三合一（P1-4/5/6）

> refactor-6 · 1 步 spec + 2 步 plan 已落地

---

## 任务总览（总估时: ~6h）

| ID | 任务 | 估时 | 状态 | 依赖 |
|---|---|---|---|---|
| T1 | xfail 静态 metadata + strict + AST gate + 4 violation code | 45 min | 🔴 待做 | 无 |
| T2 | AI eval 107 case JSONL + runner + 6 test files | 3h | 🔴 待做 | 无 |
| T3 | a11y + perf 6 gate (jest-axe + LHCI + web-vitals + browserslist) | 1h 30min | 🔴 待做 | 无 |
| T4 | 全套回归 + verify + retro | 45 min | 🔴 待做 | T1-T3 |
| **合计** | | **~6h** | | |

---

## 任务详细拆分

> 任务粒度按 6.1 单测强制规则 + AGENTS.md § 三（拆分 ≤ 1h AI 工作量原子任务）。所有 commit 单位含配套测试用例。

---

## 任务 1

- [ ] T1: xfail 静态 metadata + strict + AST gate
- **描述**：P1-4 决策：xfail 静态 metadata 4 字段（owner/issue/expiry/reason）+ strict=True + pytest 全局 xfail_strict + AST gate 扩展 4 violation code。
- **估时**: 45 min（≤ 1h）
- **依赖**: 无
- **测试**: `tests/test_check_test_quality_xfail.py`（4 violation code 测试用例 · TC-1/TC-2/TC-3/TC-4/TC-5）
- **commit**: 对应 commit `feat(test): xfail 静态 metadata + strict + AST gate 4 violation`
- **步骤**：
  1. 改 `backend/pyproject.toml` 加 `xfail_strict = true`
  2. 改 `scripts/check_test_quality.py` 扩展 xfail 识别 + 4 violation code
  3. 迁移 4 个 xfail marker（test_digest_push_daily.py:73-77/109-113/174-178 + test_digest_select_top_n.py:37-41）
  4. 跑 → 4 violation code 测试通过

---

## 任务 2

- [ ] T2: AI eval 107 case 数据集 + runner + Pydantic schema
- **描述**：P1-5 决策：107 case 离线 JSONL + EvalCaseResult BaseModel + run_case / run_suite 函数落地。后续 T2b/T2c 拆 case 文件。
- **估时**: 1h（≤ 1h）
- **依赖**: 无
- **测试**: `tests/test_eval_runner.py`（schema 校验 + mock LLM case · TC-6/TC-8）
- **commit**: 对应 commit `feat(eval): 107 case JSONL dataset + EvalCaseResult BaseModel + runner`
- **步骤**：
  1. 创建 `backend/tests/eval/datasets/interview_eval_v1.jsonl` (107 case)
  2. 创建 `backend/tests/eval/conftest.py` (mock LLM fixture + EvalCaseResult Pydantic)
  3. 创建 `backend/tests/eval/runner.py` (run_case + run_suite 函数骨架)

---

## 任务 3

- [ ] T3: 6 个 test_eval_*.py 测试文件 + 双模型回归
- **描述**：P1-5 决策：6 个 agent test 文件（evaluate/report/followup_match/followup_text/qa_service/digest_llm）+ test_digest_llm.py 扩到 12 case + run_regression 双模型 baseline。
- **估时**: 1h（≤ 1h）
- **依赖**: T2
- **测试**: `tests/test_eval_*.py` × 6 + `test_digest_llm.py`（合计 12 case · TC-6/TC-7/TC-9）
- **commit**: 对应 commit `test(eval): 6 个 agent test_eval_*.py + digest_llm 12 case + 双模型回归`
- **步骤**：
  1. 创建 6 个 test_eval_*.py（30+10+20+15+20=95 case）
  2. 扩 `backend/tests/test_digest_llm.py` 4 → 12 case
  3. 实现 `run_regression` 双模型对比（≥3/5 维度不退化）

---

## 任务 4

- [ ] T4: a11y jest-axe 接入 + Vitest setup
- **描述**：P1-6 决策：vitest.setup.ts 加 jest-axe 注册 + a11y.test.tsx 6 组件 axe 断言（全 report-only）。
- **估时**: 1h（≤ 1h）
- **依赖**: 无
- **测试**: `frontend/__tests__/a11y.test.tsx`（6 组件 axe 断言 · TC-10）
- **commit**: 对应 commit `test(a11y): jest-axe 6 组件单测 + vitest.setup 注册`
- **步骤**：
  1. 改 `frontend/vitest.setup.ts` 加 jest-axe 注册
  2. 创建 `frontend/__tests__/a11y.test.tsx`（6 组件 axe 断言）

---

## 任务 5

- [ ] T5: web-vitals + browserslist + Playwright 3 viewport + LHCI
- **描述**：P1-6 决策：_app.tsx 加 reportWebVitals console + .browserslistrc manifest + playwright.config.ts chromium-a11y project + LHCI 4 阈值（Performance ≥85 / A11y ≥95 / BP ≥90 / SEO ≥80）。全 report-only。
- **估时**: 1h（≤ 1h）
- **依赖**: T4
- **测试**: `frontend/__tests__/perf.test.tsx` + playwright e2e + lhci config（合计 4 项 gate · TC-11/TC-12/TC-13）
- **commit**: 对应 commit `feat(perf): web-vitals + browserslist + LHCI 4 项 + Playwright 3 viewport report-only`
- **步骤**：
  1. 改 `frontend/_app.tsx` 加 reportWebVitals console
  2. 创建 `.browserslistrc`（默认 + Safari iOS ≥15）
  3. 改 `frontend/playwright.config.ts` 加 chromium-a11y project
  4. 配置 `@lhci/cli` 4 阈值

---

## 任务 6

- [ ] T6: 全套回归 + verify + retro
- **描述**：5 步 verify + 6 步 retro 落地 + pre-commit 端到端校验。
- **估时**: 45 min（≤ 1h）
- **依赖**: T1, T2, T3, T4, T5
- **测试**: verify 矩阵 14 场景（S-1 ~ S-14）+ retro 实施偏差记录
- **commit**: 对应 commit `docs(test): verify.md + retro.md 落地 + 实施偏差记录`
- **步骤**：
  1. 跑 `pytest backend/tests/` 全绿（含 4 个 violation code + 6 个 test_eval_* + 12 case digest_llm）
  2. 跑 frontend vitest 全绿（含 a11y.test.tsx + perf.test.tsx）
  3. EXEMPT 兼容性：12 老任务 + archive 仍豁免
  4. pre-commit 端到端
  5. 写 verify.md（20+ verify 场景结果）
  6. 写 retro.md（实施偏差 + 改进项 + memory 候选）

---

> **总估时**: T1 (45 min) + T2 (1h) + T3 (1h) + T4 (1h) + T5 (1h) + T6 (45 min) ≈ 5h 30 min，原 plan.md 估时 ~6h 与之一致。
> **commit 总数**: 6 个（每个任务 1 commit，对应测试用例各自配套）

---

## 任务状态跟踪

| # | 任务 | 状态 | 实施 commit | 实际耗时 | 偏差分析 |
|---|---|---|---|---|---|
| T1 | xfail + strict + AST | 🔴 待做 | — | — | — |
| T2 | AI eval 107 case | 🔴 待做 | — | — | — |
| T3 | a11y + perf 6 gate | 🔴 待做 | — | — | — |
| T4 | 回归 + verify + retro | 🔴 待做 | — | — | — |
