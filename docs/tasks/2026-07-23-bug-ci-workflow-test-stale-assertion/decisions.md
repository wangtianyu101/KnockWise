---
title: test_ci_workflow.py 旧断言修复 · 决策主账
date: 2026-07-23
status: 1/1 已决策 · 待实施
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · test_ci_workflow.py 旧断言修复

> 📌 **本文件是本任务决策最权威详细主账**。
> `research.md` § 8 与 `docs/issues.md` 只保存简表和链接；后续实现、测试和复盘的落地状态统一回写本文件。

## ① 顶部权威定位

本文件记录 `backend/tests/test_ci_workflow.py` 旧 `@v6` 断言与 R8 commit `66efa3c` SHA pin 策略冲突修复的用户决策、理由、影响范围和落地追踪。

关联文档：

- 调研：[`research.md`](research.md)
- 议题主账：[`docs/issues.md`](../../../issues.md)
- 根因 commit：[`66efa3c`](https://github.com/anthropics/skills/commit/66efa3c)（R8 · 2026-07-22）
- 关联测试：[`backend/tests/test_ci_workflow.py`](../../../backend/tests/test_ci_workflow.py)
- 关联脚本：[`scripts/ci/check_action_sha.py`](../../../scripts/ci/check_action_sha.py)（机器化 SHA 检查 · 本任务不动）

## ② 决策总览表

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | v39 test_ci_workflow 修复范围 | 最小修复：仅改 test_ci_workflow.py 一个函数 + 名字 | ✅ 已决策 · 待实施 | research.md § 6/8 |

## ③ 决策详细记录

### 决策 1 · 最小修复范围

- **日期**：2026-07-23
- **决策项**：v39 分支 `test_ci_workflow.py::test_ci_uses_current_official_action_majors_and_read_only_permissions` 与 R8 SHA pin 冲突的修复范围。
- **选项列表**：
  1. **方案 A**：最小修复 · 仅改 `test_ci_workflow.py` 一个函数 + 名字。
  2. 方案 B：完整迁移 · 同时拆出独立 pytest 覆盖 `check_action_sha.py`。
  3. 方案 C：回滚 R8 commit，恢复 `@v6` 断言。
  4. 暂不处理（pre-existing 失败被 hook 阻断 commit，靠 PRE_COMMIT_SKIP=1 绕过）。
- **选择**：✅ **方案 A · 最小修复**。
- **用户原话**："拍 D" / "最小修复（推荐）"（针对方案 A）。
- **理由**：
  1. 测试断言与 R8 实际不一致是测试维护疏漏，不是架构缺陷 —— 单点修改足够。
  2. `check_action_sha.py` 已是机器化兜底，CI 中运行；CI 加 pytest 覆盖是锦上添花，不是阻塞。
  3. 回滚 R8 与 [`feedback-pin-third-party-action-sha`](~/.claude/projects/.../feedback-pin-third-party-action-sha.md) 决策冲突，绝不允许。
  4. 不修复的代价：v39 分支上每个 backend/ commit 都被 hook 阻断，已实质损失效率。
- **影响文件**：
  - `backend/tests/test_ci_workflow.py:54-60`（一个函数 + 名字 · ~10 行）
  - 本任务 `tasks.md` / `verify.md` / `retro.md`
- **明确排除**：workflow YAML 改动 / `check_action_sha.py` 改动 / 重构 test_ci_workflow.py 全部测试 / 升级 SHA。
- **关联决策**：R8（commit 66efa3c）· 决策 7（CI auto-fix SHA pin）。

## ④ 决策落地追踪 + 元信息

### 4.1 落地追踪

| # | 决策 | 落地状态 | 落地位置 | 落地日期 |
|---|---|---|---|---|
| 1 | 最小修复 · test_ci_workflow.py | ✅ 已落地（commit `d5c11e1`） | `backend/tests/test_ci_workflow.py:54-60` | 2026-07-23 |

### 4.2 元信息

- **位置**：`docs/tasks/2026-07-23-bug-ci-workflow-test-stale-assertion/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：`fix-mini`
- **下一步**：步 5 + 6 已完成（verify.md + retro.md · hook commit 后）。

### 4.3 落地补充

实施细节：

- `test_ci_workflow.py:54-60` 由 `test_ci_uses_current_official_action_majors_and_read_only_permissions` 改名为 `test_ci_uses_pinned_action_shas_and_read_only_permissions`，断言从 `@v6` 改成 pin SHA。
- 3 个 SHA（`d23441a48...` / `ece7cb06...` / `24997072...`）在 ci.yml + auto-fix-ci.yml 共出现 6 次，substring 检查 1 次命中即通过。
- 修复前 `pytest tests/test_ci_workflow.py` 1 failed 5 passed；修复后 6 passed。
- 修复后完整 `pytest tests/` 714 passed, 2 skipped, 4 xfailed, 0 failed — pre-commit hook 不再被 pre-existing failure 阻断。
- 决策 1 § 明确排除项全部遵守：未改 workflow YAML、未改 `check_action_sha.py`、未重构 test_ci_workflow.py、未升级 SHA。