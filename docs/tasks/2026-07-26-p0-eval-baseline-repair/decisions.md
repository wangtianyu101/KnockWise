---
title: P0 AI Eval 基线修复 · 决策主账
type: meta
step: 0
date: 2026-07-26
status: approved
tags: [decisions, p0, eval]
related: [research.md, task.yaml]
---

# P0 AI Eval 基线修复 · 决策主账

本文件是本任务决策最权威详细主账。证据见 [research.md](research.md)，议题状态见 [docs/issues.md](../../issues.md)；其他位置只链接。

## 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-26 | 22 个失败的修复批次 | 先修 13 个 Eval，9 个 API 后续 | ✅ 已确认 | research § 0/8 |
| 2 | 2026-07-26 | Digest fallback 契约 | 保持结构化 schema，不放宽断言 | ✅ 默认安全决策 | research § 2/5 |

## 决策详细记录

### 决策 1 · 先恢复 Eval 基线

- **日期**：2026-07-26
- **决策项**：先修 Eval 还是 Digest API。
- **选项列表**：1）13 个 Eval；2）9 个 API；3）两批一起。
- **选择**：只修 13 个 Eval。
- **用户原话**：「1」
- **理由**：
  1. 12 个失败共享一个确定性数据根因。
  2. Eval 批次无数据库依赖，能快速恢复 Agent contract 信号。
  3. API 批次包含 test harness 与真实实现边界，应独立排查。
- **影响文件**：Eval JSONL、mock fixture、回归测试与任务主账。
- **关联决策**：P1-5 AI Eval、P0-1 governance Gate。

### 决策 2 · fallback 保持 schema-valid

- **日期**：2026-07-26
- **决策项**：注入 fallback 返回普通文本还是结构化 JSON。
- **选项列表**：放宽测试接受文本；返回 schema-valid JSON；跳过注入 case。
- **选择**：返回保守的 schema-valid JSON。
- **用户原话**：由「1」授权的批次内安全实现决策。
- **理由**：
  1. runner 明确把 `digest_llm` 作为 JSON agent。
  2. 用例明确要求 `summary/category/quality_score`。
  3. 结构化 fallback 保持下游类型契约，不削弱 prompt-injection Gate。
- **影响文件**：`backend/tests/eval/conftest.py` 与对应回归。
- **关联决策**：决策 1。

## 决策落地追踪

| 决策 | 落地点 | 状态 |
|---|---|---|
| 1 | JSONL + Eval 专项 | 🚧 实施中 |
| 2 | Digest fallback mock + contract test | 🚧 实施中 |
| 1 | Digest API 9 failures | ⏸ 后续批次 |

## 元信息

- **位置**：`docs/tasks/2026-07-26-p0-eval-baseline-repair/decisions.md`
- **创建日期**：2026-07-26
- **决策总数**：2
- **已决策数**：2
- **待确认数**：0
- **暂缓数**：1
- **负责人**：Codex / 用户
- **状态**：实施中
