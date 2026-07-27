---
title: 产品基础分层 L0-L3 · 决策主账
date: 2026-07-23
status: 1/1 自动决策 · 待步骤 1 规格
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · P1 产品基础分层 L0-L3

> 📌 本文件是本任务决策最权威详细主账。用户授权 P1+P2 调研后自动采用单一推荐。

## ① 顶部权威定位

关联：[`research.md`](research.md) · [`docs/issues.md`](../../issues.md) · [`product-doc-template.md`](../../templates/product-doc-template.md) · [`tasks-template.md`](../../templates/tasks-template.md) · [`check_test_quality.py`](../../../scripts/check_test_quality.py) · [`utils/metrics.py`](../../../backend/utils/metrics.py)

## ② 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | P1-7 + P1-8 + P1-9 合并方案 | 分层 L0-L3 治理 + 模板最小 diff + 埋点按层强制 | ✅ spec v1.1 + plan v1.1 + tasks v1.1 完成 · 待 4 步实施 | [research § 4](research.md#4-单一推荐) · [spec.md](spec.md) · [plan.md](plan.md) · [tasks.md](tasks.md) |
| 2 | 2026-07-27 | 实施前调研偏差修正（trace_id 模块不存在 · 4 Agent 盲点） | 选项 A · 立即修正 spec/plan/tasks · T9-T10 改写为 logger trace_id 字段注入 | ✅ 用户决策 · 文档 v1.1 修正 | [research § 2.3](research.md#23-p1-9) |
| 3 | 2026-07-27 | v1.2 调研偏差修正（4 项：counter 键错 / T4 checker 已存在 / logger 已有 trace_id / 30 pytest 基线） | 选项 A · 修正 spec/plan/tasks + 修订 T4 + 实施 T4-T5 | ✅ 用户决策 · 文档 v1.2 修正 | [research § 2.3 v1.2](research.md#23-p1-9) |

## ③ 决策详细记录

### 决策 3 · v1.2 调研偏差修正（4 项偏差 · 实施 T4 时 verifier FAIL 发现）

- **日期**：2026-07-27
- **触发**：T4 实施前探查 + background verifier FAIL 报告
- **选项**：
  - A · 修正 spec/plan/tasks + 修订 T4 + 实施 T4-T5（推荐）
  - B · 仅文档修正不改代码
  - C · 完全暂停回 0 步
  - D · 保持当前登记议题
- **选择**：✅ 选项 A
- **用户原话**："A"
- **4 项偏差清单**：
  1. **counter 键错误** — `spec.md SCN-P1.9.4` + `tasks.md T13` 写 `push_total / interview_session_started / collect_success / collect_failure`（**错误**）· 实际 `backend/utils/metrics.py:32-37` = `push_total / push_failed / fetch_failures / rsshub_routes_broken`（与 docstring 一致）· api-spec.md 已正确
  2. **T4 checker 已存在** — `scripts/check-product-doc.py` 2026-07-25 创建（v2 P2-3 决策 1/5）· 1730 bytes · 校验"5 段 + 5 成功指标字段"（旧版）· T4 真实工作 = 修订 + 加 product_baseline frontmatter 校验
  3. **logger.py 已有 trace_id**（v1.1 已发现但未完全修正）— `TraceFilter` + `setup_logger` 已实现 · T9 真实工作 = 改 `global _trace_id` → `contextvars.ContextVar`（不是"新增"）
  4. **30 pytest 失败基线** — `30 failed / 817 passed / 2 skipped / 1 xfailed` · feature/v40-product-foundation 预存在 · 与 T1-T3 无关（纯文档改动）· 登记为独立 P1 议题（v40 启动前环境整治）
- **影响文件**：
  - `research.md` § 2.3 + § 8（加 v1.2 偏差修正 + 决策 3 行）
  - `spec.md` § 2.2 SCN-P1.9.4 counter 键 + § 2.1 Requirement: P1-9 文字
  - `plan.md` § 5 T13 counter 键 + 落地追踪
  - `tasks.md` T4 修订 + T13 counter 键 + Traceability T4
  - `api-spec.md` 保留（counter 键已正确）
  - `issues.md` L42 + L103 同步 v1.2 + 加 pytest 基线议题
  - `scripts/check-product-doc.py` 修订（v0 框架 + product_basfrontmatter 校验）
  - `backend/tests/test_check_product_doc.py` T5（修订后跑通）
- **关联决策**：决策 1（整体方案不变） + 决策 2（v1.1 调研偏差修正的扩展）

### 决策 2 · 实施前调研偏差修正（trace_id 模块不存在）

- **日期**：2026-07-27
- **触发**：4 步实施前 git 基线 + 文件存在性探查
- **选项**：
  - A · 立即修正 spec/plan/tasks + 继续 4 步全量实施（推荐）
  - B · 维持当前 spec/plan/tasks + 仅实施 P1-7 + P1-8（11 任务）
  - C · 完全停止 · 回到 0 步重做调研
- **选择**：✅ 选项 A
- **用户原话**："A"
- **理由**：
  1. 偏差范围明确（仅 T9-T10 trace_id 段 · 3 处文档）
  2. P1-9 L1 平台层本质不变（metrics + logger + endpoint）· 只是改写 trace_id 子任务
  3. 立即回写 + 立即实施 · 不累积偏差
  4. 与 CLAUDE.md § 6.7 "FAIL → 改 → 再 verify" 一致
- **影响文件**：
  - `research.md` § 2.3 + § 8（加偏差修正 + 决策 2 行）
  - `spec.md` § 2.1 Requirement P1-9 + § 2.2 SCN-P1.9.1/.2 + § 4.4 + 落地追踪
  - `plan.md` § 1 + § 4 决策 4 + § 5 T9-T10 + 落地追踪
  - `tasks.md` T9-T10 + Traceability + 任务↔Spec + § 7 阶段 2 + 落地追踪
  - `issues.md` L42 + L103（同步 v1.1 状态）
- **关联决策**：决策 1（修正 trace_id 子任务 · 整体方案不变）

### 决策 1 · 产品基础分层 L0-L3

- **日期**：2026-07-23
- **选项**：3 项独立任务；立即要求完整字典；分层 L0-L3。
- **选择**：✅ 分层 L0-L3。
- **授权原话**："循环把上面哪些问题都处理一遍…不需要我确认了"。
- **理由**：
  1. 单人项目 / 用户群未稳 / 多数功能未跑通
  2. 立即要求完整字典会产生形式化但虚的形式主义
  3. L0-L3 分层让"测量深度 = 决策风险 + 用户规模 + 产品成熟度"
  4. 反方证据：5 项 AI 推送产品指标数字未验证
- **核心规则**：
  - **P1-7**：product_baseline 字段 + 模板加 4 段 + check-product-doc.py
  - **P1-8**：8 必填 + 4 可选双层字典；L0 不要求、L1 探索性、L2 核心闭环、L3 稳定用户
  - **P1-9**：L1 平台层（trace_id race fix + logger startup + metrics endpoint）+ L2 接入层（per-task § 9 埋点挂载点）
- **明确排除**：
  - 立即要求所有功能完整字典
  - 引入新分析平台
  - 改业务表 schema 强埋点
  - 改 `mock_db / mock_cache / mock_llm` 默认行为
  - 任何代码实施与提交
- **影响文件**：
  - `product-doc-template.md` 加 baseline 字段 + 角色表 4 列 + 成功指标 baseline_value
  - `tasks-template.md` 加 § 9 埋点挂载点段
  - 新建 `scripts/check-product-doc.py`
  - 新建 `scripts/check_metric_dict.py`
  - `issues.md` 决策段补登记（CI auto-fix verify.md L4/L5 缺失 + issues-audit verify.md 缺失）
  - L1 实施：trace_id race fix / logger startup / metrics endpoint（实施阶段另开任务）

## ④ 落地追踪 + 元信息

| # | 决策 | 落地状态 | 落地位置 |
|---|---|---|---|
| 1 | 产品基础分层 L0-L3 | 🟡 spec v1.1 ✅ + plan v1.1 ✅ + tasks v1.1 ✅ · 待 4 步实施 | [spec.md](spec.md) + [plan.md](plan.md) + [tasks.md](tasks.md) · 19 任务 / ~7h / 关键路径 ~3h |
| 2 | 实施前调研偏差修正 | 🟡 文档 v1.1 修正完成 · 待 4 步实施（T9-T10 改写为 logger trace_id 字段） | research/spec/plan/tasks/issues · 5 文件 |
| 3 | v1.2 调研偏差修正 | 🟡 文档 v1.2 修正中 · T4 修订中 · T5 待跑通 | 6 文档 + 1 脚本修订 + 1 测试 + 1 议题登记 |

- **位置**：`docs/tasks/2026-07-23-refactor-product-foundation/decisions.md`
- **创建日期**：2026-07-23
- **更新日期**：2026-07-27（v1.1 决策 2 + v1.2 决策 3 调研偏差修正）
- **决策总数**：3
- **已决策数**：3（决策 1 自动授权 · 决策 2 + 决策 3 用户拍板选项 A）
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：refactor-6
- **当前阶段**：4 步实施中（T1-T3 ✅ · T4 修订中 · T5 待跑通）
- **下一步**：修订 T4 + 跑 T5 pytest + 启动 background verifier 整批 verify P1-7。
