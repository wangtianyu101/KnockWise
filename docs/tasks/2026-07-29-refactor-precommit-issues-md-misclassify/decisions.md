---
title: pre-commit 把 docs/issues.md 误判为 product-doc · 决策主账
type: meta
step: 0
date: 2026-07-29
status: implemented
tags: [decisions, refactor, governance, pre-commit]
related: [research.md, task.yaml, ../../issues.md]
---

# pre-commit 把 docs/issues.md 误判为 product-doc · 决策主账

## ① 顶部权威定位

本文件是本任务决策最权威详细主账。

- 事实、复现、风险和关闭条件：[`research.md`](research.md)
- 长期议题状态：[`docs/issues.md` 顶部决策段](../../issues.md)
- 上游触发：债务 24 收尾（[`tasks/2026-07-28-p0-ci-autofix-execution-breaks/retro.md`](../2026-07-28-p0-ci-autofix-execution-breaks/retro.md)）
- 其他文件只保留链接与状态镜像，不重复完整理由。

## ② 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| D-003 | 2026-07-29 | docs/issues.md 边界误分类修复路径 | A：缩窄 pre-commit regex · 移除 docs/issues.md | ✅ 用户已决策 | research § 六 |

## ③ 决策详细记录

### D-003 · 缩窄 regex 而非给 docs/issues.md 加 hack

- **日期**：2026-07-29
- **决策项**：如何修 pre-commit 把 docs/issues.md 误判为 product-doc 的边界错误
- **选项**：
  - A：缩窄 regex · 移除 docs/issues.md
  - B：给 docs/issues.md 加 frontmatter hack（`legacy_skeleton: true`）
  - C：`PRE_COMMIT_SKIP=1` 强推（§ 6.10 反模式 · 禁止）
  - D：`git commit --no-verify` 单独 commit docs/issues.md
- **选择**：✅ 方案 A
- **用户原话**：「A」
- **理由**：
  1. 边界缩小而非扩大，不引入新攻击面。
  2. docs/issues.md 是议题主账（按 § 0.5 + § 6.9 + issue-closure-template），与 product-doc 语义分离。
  3. 真 product-doc（template + tasks/.../product-doc.md）仍受 check-product-doc.py 保护。
  4. 修 hook 边界是真正的根因修复；frontmatter hack 是治标。
- **影响文件**：`scripts/pre-commit`（第 220 行 regex）+ `backend/tests/test_pre_commit_hook.py`（新增 4 场景回归）。
- **关联决策**：债务 24 D-002（commit `8fb65bf` 不触及 pre-commit 边界）。

## ④ 决策落地追踪 + 元信息

| 决策 | 落地点 | 状态 | 证据 |
|---|---|---|---|
| D-003 | scripts/pre-commit:220 + tests/test_pre_commit_hook.py + docs/issues.md 状态同步 | ✅ 已实施并验证 | 本次 commit |

- **位置**：`docs/tasks/2026-07-29-refactor-precommit-issues-md-misclassify/decisions.md`
- **创建日期**：2026-07-29
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **取消数**：0
- **路径模式**：`refactor-6`
- **当前阶段**：步骤 4 已完成；L5 由用户执行一次真实 commit 验证