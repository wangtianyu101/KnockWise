---
title: 测试治理与质量 (xfail/AI 评估/a11y+性能) · 计划
type: plan
step: 2
date: 2026-07-23
status: draft
tags: [refactor, test-governance, plan]
related:
  - research.md
  - spec.md
  - decisions.md
---

# 计划 · 测试治理与质量三合一（P1-4/5/6）

---

## 1. ≥ 2 方案对比

### 决策 1 · P1-4+P1-5+P1-6 合并 vs 拆分

> 2026-07-23 自动授权（用户原话 "循环把上面哪些问题都处理一遍…不需要我确认了"）—— 落地为**方案 A 单 batch**。

### 方案 A · 单 batch 实施（推荐）

**结构**：
- `scripts/check_test_quality.py` 扩展（+150 行）
- `pyproject.toml` 加 `xfail_strict = true`
- 4 个 xfail marker 迁移
- `backend/tests/eval/` 新建目录（cases + runner）
- `backend/tests/test_digest_llm.py` 扩到 12 case
- frontend 新建 `__tests__/a11y.test.tsx`
- 新建 `frontend/vitest.setup.ts` 加 jest-axe
- 新建 `.browserslistrc`
- 新建 `frontend/_app.tsx` 加 reportWebVitals

**优**：8 个文件改动共享 xfail budget / CI 容量 / 长期报告型观察

**缺**：单 commit 含 8 文件改动面广

### 方案 B · 3 独立子任务

- 3 个独立 PR：xfail / AI eval / a11y+perf
- 各自独立可合并

**优**：故障隔离

**缺**：决策已合并为 1 任务；3 PR 风险高（需要 L4 verifier 3 次）

### 单一推荐：方案 A

**推荐**:**方案 A** · 单 batch 实施（自动采用 · 见 **决策 1**）

**理由**：
1. 决策已合并，3 块共享 CI 容量预算
2. xfail 数量治理 = AST gate 扩展 = 1 个文件
3. AI eval 离线 case + a11y/perf Playwright project 共享 frontend test infrastructure

---

## 2. 单一推荐方案详细

### 2.1 文件改动总览

| # | 文件 | 类型 | 增量 |
|---|---|---|---|
| 1 | `scripts/check_test_quality.py` | 修改 | +150 行 (xfail + 4 violation code + eval shell check) |
| 2 | `backend/pyproject.toml` | 修改 | +1 行 (xfail_strict = true) |
| 3 | 4 个 xfail markers | 修改 | reason 改格式 + strict=True |
| 4 | `backend/tests/eval/datasets/interview_eval_v1.jsonl` | 新建 | ~200 行 (107 case) |
| 5 | `backend/tests/eval/conftest.py` | 新建 | ~100 行 (mock LLM fixture) |
| 6 | `backend/tests/eval/runner.py` | 新建 | ~150 行 (run_case + run_suite) |
| 7 | `backend/tests/test_eval_*.py` (6 文件) | 新建 | ~300 行 (6 agent test) |
| 8 | `backend/tests/test_digest_llm.py` | 修改 | +50 行 (8 case → 12) |
| 9 | `frontend/__tests__/a11y.test.tsx` | 新建 | ~80 行 (axe tests) |
| 10 | `frontend/vitest.setup.ts` | 修改 | +20 行 (jest-axe 注册) |
| 11 | `frontend/_app.tsx` | 修改 | +10 行 (reportWebVitals) |
| 12 | `.browserslistrc` | 新建 | ~5 行 |
| 13 | `frontend/playwright.config.ts` | 修改 | +20 行 (chromium-a11y project) |
| **合计** | | | **~1,260 行** |

**估时**：~6-8h AI

---

## 3. 实施步骤

### T1 · xfail 元数据 + strict + AST gate
1. 改 `pyproject.toml` 加 `xfail_strict = true`
2. 改 `check_test_quality.py` 加 xfail 识别 + 4 violation code
3. 迁移 4 个 xfail marker 改用静态 metadata + strict=True
4. 跑 → 4 violation code 测试通过

### T2 · AI eval 基础设施
1. 创建 `backend/tests/eval/datasets/interview_eval_v1.jsonl` (107 case)
2. 创建 `backend/tests/eval/conftest.py` (mock LLM fixture + EvalCaseResult Pydantic)
3. 创建 `backend/tests/eval/runner.py` (run_case + run_suite + run_regression)
4. 创建 6 个 test_eval_*.py (30+10+20+15+20+12=107 case)
5. 扩 `test_digest_llm.py` 4 → 12 case

### T3 · a11y + 性能
1. 改 `frontend/vitest.setup.ts` 加 jest-axe 注册
2. 创建 `frontend/__tests__/a11y.test.tsx` (6 组件 axe)
3. 改 `frontend/_app.tsx` 加 reportWebVitals console
4. 创建 `.browserslistrc` (默认 + Safari iOS ≥15)
5. 改 `frontend/playwright.config.ts` 加 chromium-a11y project

### T4 · 全套回归 + verify + retro

---

## 4. 依赖影响

| 改 A | 影响 B | 影响 C |
|---|---|---|
| xfail_strict 全局 | 4 个 xfail marker 必 strict=True | 现状全 strict=False → 必迁移 |
| AI eval 107 case | 需 `test_digest_llm.py` 12 case 模板复用 | runner Pydantic schema 校验 |
| a11y/perf 6 gate | 新 CI job 接入 | pre-commit 触发需先 EXEMPT 12 老任务 |

---

## 5. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| xfail_strict 启用后 4 个 marker 立即全 FAIL | 🔴 | T1 先迁 4 marker 再启 strict |
| AI eval 107 case 内容漂移 | 🟡 | 固定输入 + 固定 mock 响应 |
| a11y 6 组件 baseline 未知 | 🟡 | 先跑 1 次 report-only 收集 baseline |
| perf 跨平台差异大 | 🟡 | 用 GitHub-hosted runner 固定基线 |
| venv 缺失无法跑 | 🔴 | 完整 pytest 待 P0-4 启用后跑 |

---

## 6. 测试矩阵

| Case | 输入 | 期望 |
|---|---|---|
| T1.xfail_metadata | 完整 reason | 0 violation |
| T1.xfail_strict_false | strict=False | xfail-not-strict violation |
| T1.xfail_expired | expiry<today | test-debt-expired |
| T1.xfail_budget | 5 个 xfail | test-debt-budget-exceeded |
| T1.pytest_strict | 任一 xfail 通过 | XPASS(strict) → suite fail |
| T2.eval_evaluate_agent | 30 case mock LLM | schema + 7 维度全产出 |
| T2.eval_prompt_injection | 含 injection 文本 | score 不变 + 盲区反映真实 |
| T2.eval_regression_5_dim | baseline + candidate | ≥3/5 不退化 |
| T3.a11y_no_critical | 6 组件 axe | 0 critical violation |
| T3.lhci_4_thresholds | dashboard + login | 4 项全过 |
| T3.web_vitals_console | _app.tsx render | console.log 4 项 |
| T3.browserslist_check | npx browserslist | 默认 + iOS ≥15 |
| T4.legacy_12_exempt | 12 路径 | EXEMPT |
| T4.report_only_no_block | 20 次跑 | 不阻断 merge |

---

## 7. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 决策：[decisions.md](decisions.md)
- 主账：`docs/issues.md` 决策 #31 · 债务 #19

---

## 8. product-doc / design-spec 适用性说明

- **product-doc.md**：**不适用**。本任务为 refactor-6（测试治理与质量三合一），不涉及对外可见的产品/业务功能演进，仅在现有产品代码上加测试契约层（xfail metadata / AI eval runner / a11y-perf gate），无新业务模块/新用户体验/新术语需要 PO 拍板，故跳过 product-doc 写作。
- **design-spec.md**：**不适用**。本任务不涉及 UI 改动 / 页面布局 / 交互流程变化（仅在 frontend 加 `_app.tsx` reportWebVitals console + `.browserslistrc` 配置文件 + `__tests__/a11y.test.tsx` 单测，不产生用户可见的视觉/交互变更），故跳过 design-spec 写作与 HTML mockup。
