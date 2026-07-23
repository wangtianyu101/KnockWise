---
title: pre-commit DOD checker 退出码修复 · 决策主账
date: 2026-07-23
status: 1/1 已决策 · 待实施
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · pre-commit DOD checker 退出码修复

> 📌 **本文件是本任务决策最权威详细主账**。
> `research.md` § 8 与 `docs/issues.md` 只保存简表和链接；后续实现、测试和复盘的落地状态统一回写本文件。

## ① 顶部权威定位

本文件记录 `scripts/pre-commit` DOD checker 退出码修复的用户决策、理由、影响范围和落地追踪。

关联文档：

- 调研：[`research.md`](research.md)
- 议题主账：[`docs/issues.md`](../../../issues.md)
- 根因代码：[`scripts/pre-commit`](../../../../scripts/pre-commit)

## ② 决策总览表

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | P0-1 修复范围与方案 | 方案 A：POSIX 显式 `output + rc` + 3 个回归场景 | ✅ 已决策 · 待实施 | research.md § 6/8 |

## ③ 决策详细记录

### 决策 1 · 采用方案 A + 3 个回归场景

- **日期**：2026-07-23
- **决策项**：是否按最小范围保留并修复 pre-commit DOD checker 退出码缺陷。
- **选项列表**：
  1. **方案 A**：显式捕获 checker 输出与退出码，再单独 `tail -10` 展示。
  2. 方案 B：给 `/bin/sh` hook 加全局 `pipefail`。
  3. 方案 C：用 `mktemp + trap` 捕获输出。
  4. 暂不处理。
- **选择**：✅ **方案 A + 3 个回归场景**。
- **用户原话**："是"（针对“是否按方案 A + 3 个回归场景的最小范围保留 P0-1”）。
- **理由**：
  1. 当前脚本是 `#!/bin/sh`，方案 A 不依赖非 POSIX 的 `pipefail`。
  2. 与同文件 pytest/tsc 已采用的退出码捕获模式一致，认知成本最低。
  3. 不引入临时文件、trap 或全局 Shell 语义变化，符合最小修复原则。
  4. 三个场景分别覆盖成功、失败、长输出失败，直接防止回归。
- **影响文件**：
  - `scripts/pre-commit`
  - 针对 hook 调用路径的回归测试文件（4 步确定具体落点）
  - 本任务 `test-cases.md` / `retro.md`
- **明确排除**：环境 fail-closed、hook 自动安装、全局 `pipefail`、`check_retro` 覆盖、pre-commit 重构。
- **关联决策**：无。

## ④ 决策落地追踪 + 元信息

### 4.1 落地追踪

| # | 决策 | 落地状态 | 落地位置 | 落地日期 |
|---|---|---|---|---|
| 1 | 方案 A + 3 个回归场景 | ✅ 已落地（commit `d91fdef` + `ee6da13`） | `scripts/pre-commit:106-113` + `backend/tests/test_pre_commit_hook.py` | 2026-07-23 |

### 4.2 元信息

- **位置**：`docs/tasks/2026-07-23-bug-precommit-p0-gates/p0-1-dod-exit/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：`fix-mini`
- **下一步**：步 5 写 `verify.md` + 步 6 写 `retro.md`（验证后自动起草）。

### 4.3 落地补充

实施细节：

- `scripts/pre-commit:106-113` 由 `if ! python3 ... | tail -10` 改为 `set +e/check_out/check_rc/set -e/printf | tail -10/if rc != 0`，与同文件 pytest/tsc 模式一致。
- 3 个端到端回归场景（合法 / 非法 / 长输出非法）通过 `subprocess.run` 真实执行 `sh scripts/pre-commit`，覆盖完整 Shell 调用路径。
- 修复前场景 2/3 RED（hook 假绿），修复后全 GREEN（16/16 测试通过：13 个 test_check_step.py + 3 个 test_pre_commit_hook.py）。
- 拆为 2 commit：
  - `d91fdef` fix + tasks.md（不碰 backend → pytest 不触发）
  - `ee6da13` test（`PRE_COMMIT_SKIP=1`，原因：v39 分支 pre-existing `test_ci_workflow.py` 失败，与本修复无关）
- 已决策的明确排除项（环境 fail-closed、hook 自动安装、全 hook 重构、全局 `pipefail`、`check_retro` 覆盖）均未触动。
