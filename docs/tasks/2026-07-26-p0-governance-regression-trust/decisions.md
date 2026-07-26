---
title: P0 治理回归可信度 · 决策主账
type: meta
step: 0
date: 2026-07-26
status: approved
tags: [decisions, p0, governance]
related: [research.md, task.yaml]
---

# P0 治理回归可信度 · 决策主账

本文件是本任务决策最权威详细主账。调研证据见 [research.md](research.md)，项目状态镜像见 [docs/issues.md](../../issues.md)，实现证据见 [test-cases.md](test-cases.md)。

## 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-26 | 治理测试可信标准 | 黑盒 CLI + 临时 Git + 真实 rc | ✅ 已确认 | research § 2/7 |

## 决策详细记录

### 决策 1 · 关键契约采用黑盒行为证据

- **日期**：2026-07-26
- **决策项**：治理工具自身回归应以内部函数覆盖、静态源码断言，还是生产入口行为作为主证据。
- **选项**：继续内部单测；黑盒 CLI + 临时 Git；引入 mutation testing 框架。
- **选择**：以真实 subprocess、Git INDEX 和 rc/output 双断言作为关键契约主证据；内部单测仅作补充。
- **用户原话**：「P0-3：治理工具自己的回归测试不可信 开始修复这个吧」
- **理由**：
  1. 内部函数通过不能证明 argparse、main 和退出码正确。
  2. 静态 workflow 字符串不能证明 checker 对真实 diff 的行为。
  3. 临时 Git repo 无外部依赖，P0 内可快速形成可复现证据。
- **影响文件**：治理测试文件与本任务主账；生产脚本仅在红测暴露真实缺陷时最小修改。
- **关联决策**：P0-1 治理执行链、P0-2 空模板 DOD Gate。

## 决策落地追踪

| 决策 | 落地点 | 状态 |
|---|---|---|
| 1 | CLI/INDEX 回归测试 | ✅ commit `f1cf815` · 6/6 PASS |
| 1 | workflow 静态证据边界 | ✅ 已明确；CI 行为由真实 CLI E2E 证明 |
| 1 | 独立 verifier | ✅ PASS |

## 元信息

- **位置**：`docs/tasks/2026-07-26-p0-governance-regression-trust/decisions.md`
- **创建日期**：2026-07-26
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **负责人**：Codex / 用户
- **状态**：实施与独立验证完成 · 用户验收待完成
