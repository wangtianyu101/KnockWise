---
title: 测试基础架构 L1-L5 + 追溯 + Fixture · 决策主账
date: 2026-07-23
status: 1/1 自动决策 · 待步骤 1 规格
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · P1 测试基础架构三位一体

> 📌 本文件是本任务决策最权威详细主账。用户授权 P1+P2 调研后自动采用单一推荐。

## ① 顶部权威定位

关联：[`research.md`](research.md) · [`docs/issues.md`](../../issues.md) · [`testing-rules.md`](../../rules/testing-rules.md) · [`tasks-template.md`](../../templates/tasks-template.md) · [`verify-template.md`](../../templates/verify-template.md) · [`product-doc-template.md`](../../templates/product-doc-template.md) · [`conftest.py`](../../../backend/tests/conftest.py) · [`playwright.config.ts`](../../../frontend/playwright.config.ts)

## ② 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | P1-1 + P1-2 + P1-3 合并方案 | L1-L5 Mock 边界 + Traceability Matrix + E2E Fixture 三位一体 | ✅ 自动决策 · 待规格 | research § 4 |

## ③ 决策详细记录

### 决策 1 · 测试基础架构三位一体

- **日期**：2026-07-23
- **选项**：三块独立方案；另建 YAML/JSON 主账；三位一体合并。
- **选择**：✅ 三位一体。
- **授权原话**："循环把上面哪些问题都处理一遍…不需要我确认了"。
- **理由**：
  1. L1-L5 Level 字段是追溯矩阵的列；三块共享 schema。
  2. E2E fixture 的 Mock 边界列需引用 L1-L5 字段。
  3. Traceability 的 Test Node 必须能被 E2E fixture 解析。
  4. 拆成 3 任务会产生三份 `tasks.md` 跨 P0-5/P0-7 模板冲突。
- **核心规则**：
  - **P1-1 · L1-L5 Mock 边界**：唯一主账在 `testing-rules.md` § 6.5.1。Provider 边界例外条款 + 前端 `block_external_network`。
  - **P1-2 · Traceability Matrix**：唯一主账在 `verify.md` 的 10 列规范化表。`check-step.py` 验证 10 条不变量。
  - **P1-3 · E2E Fixture**：8 项契约（DB 边界、用户命名空间、登录态、Digest 预生成、seed 只读、时间固定、清理幂等、并行隔离）。
- **明确排除**：
  - 改 `mock_db / mock_cache / mock_llm` 默认行为
  - 改 `seed_data/digest_sources.json`
  - 改老 e2e 文件以适配新 fixture
  - 引入新测试框架
  - 跑测试、提交代码
- **影响文件**：`testing-rules.md`、`tasks-template.md`、`verify-template.md`、`product-doc-template.md`、`conftest.py`、新 `frontend/vitest.setup.ts`、新 `e2e/conftest.py` 共享 fixture。

## ④ 落地追踪 + 元信息

| # | 决策 | 落地状态 | 落地位置 |
|---|---|---|---|
| 1 | 测试基础架构三位一体 | 🟡 待步骤 1 规格 | spec.md → plan/tasks → 实施 |

- **位置**：`docs/tasks/2026-07-23-refactor-test-foundation/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1（自动授权）
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：refactor-6
- **下一步**：继续 P1 批次 2（xfail / AI 评估 / a11y 性能）。
