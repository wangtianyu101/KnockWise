---
title: 测试治理与质量（xfail/AI eval/a11y+性能）· 决策主账
date: 2026-07-23
status: 1/1 自动决策 · 待步骤 1 规格
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · P1 测试治理与质量三合一

> 📌 本文件是本任务决策最权威详细主账。用户授权 P1+P2 调研后自动采用单一推荐。

## ① 顶部权威定位

关联：[`research.md`](research.md) · [`docs/issues.md`](../../issues.md) · [`testing-rules.md`](../../rules/testing-rules.md) · [`check_test_quality.py`](../../../scripts/check_test_quality.py) · [`pyproject.toml`](../../../backend/pyproject.toml) · [`conftest.py`](../../../backend/tests/conftest.py)

## ② 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | P1-4 + P1-5 + P1-6 合并方案 | xfail 静态 metadata + AI 离线 contract + a11y/perf 报告型 | ✅ 自动决策 · 待规格 | research § 4 |

## ③ 决策详细记录

### 决策 1 · 测试治理与质量三合一

- **日期**：2026-07-23
- **选项**：3 项独立任务；YAML registry / pytest plugin；立即全 hard gate；三合一。
- **选择**：✅ 三合一。
- **授权原话**："循环把上面哪些问题都处理一遍…不需要我确认了"。
- **理由**：
  1. xfail 数量预算与 AST gate 扩展共享 `check_test_quality.py`
  2. AI eval 离线 case 与 a11y/perf Playwright 项目共享 CI 容量预算
  3. 三类都需先报告型稳定再升 hard gate，统一观察期 20 次
- **核心规则**：
  - **P1-4 xfail**：静态 metadata（owner/issue/expiry/reason + strict=True）；pytest 全局 `xfail_strict=true`；AST gate 扩展识别 4 violation code；预算只降不升。
  - **P1-5 AI eval**：107 case 离线数据集 + 7 维度契约；commit gate 17 case、nightly 107 case；8 硬 gate 7 软 gate。
  - **P1-6 a11y/perf**：9 维度契约 + 6 gate 全部 report-only + 20 次观察晋升。
- **明确排除**：
  - 立即 hard gate
  - 改 `mock_db / mock_cache / mock_llm` 默认行为
  - 改 `seed_data/digest_sources.json`
  - 引入新测试框架
  - 任何代码实施与提交
- **影响文件**：
  - `check_test_quality.py` 扩展 xfail/skip 识别 + 4 violation code
  - `pyproject.toml` 加 `xfail_strict = true`
  - 4 个 xfail marker 迁移
  - 新 `backend/tests/eval/datasets/interview_eval_v1.jsonl`
  - 新 `backend/tests/eval/conftest.py + runner.py + 6 test_eval_*.py`
  - 前端 axe/jest-axe/lighthouse/web-vitals/browserslist 集成
  - 新 `a11y-axe` / `playwright-viewports` / `lighthouse-ci` CI jobs

## ④ 落地追踪 + 元信息

| # | 决策 | 落地状态 | 落地位置 |
|---|---|---|---|
| 1 | 测试治理与质量三合一 | 🟡 待步骤 1 规格 | spec.md → plan/tasks → 实施 |

- **位置**：`docs/tasks/2026-07-23-refactor-test-governance-quality/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1（自动授权）
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：refactor-6
- **下一步**：继续 P1 批次 3（产品基础）。
