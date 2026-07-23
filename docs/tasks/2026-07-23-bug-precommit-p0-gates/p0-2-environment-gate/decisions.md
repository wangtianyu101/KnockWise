---
title: pre-commit 环境 Gate · 决策主账
date: 2026-07-23
status: 1/1 已决策 · 待实施
type: 决策详细主账
related:
  - research.md
  - docs/issues.md
---

# 决策主账 · pre-commit 环境 Gate

> 📌 **本文件是本任务决策最权威详细主账**。
> `research.md` § 8 与 `docs/issues.md` 只保存简表和链接；后续实现、测试和复盘的落地状态统一回写本文件。

## ① 顶部权威定位

本文件记录 pre-commit 在后端/前端执行环境缺失或损坏时的处理策略、用户原话、范围和落地追踪。

关联文档：

- 调研：[`research.md`](research.md)
- 议题主账：[`docs/issues.md`](../../../issues.md)
- 根因代码：[`scripts/pre-commit`](../../../../scripts/pre-commit)

## ② 决策总览表

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| 1 | 2026-07-23 | 环境缺失/损坏时如何处理 | 风险范围感知的 fail closed + 最小健康探针 + 8 个回归场景 | ✅ 已决策 · 待实施 | research.md § 6/8 |

## ③ 决策详细记录

### 决策 1 · 采用风险范围感知的 fail closed

- **日期**：2026-07-23
- **决策项**：pre-commit 检测到相关改动但对应测试环境缺失或损坏时，是警告放行、一律阻断，还是按风险范围阻断。
- **选项列表**：
  1. 保持现状：警告后跳过，依赖 CI。
  2. 所有 commit 一律要求完整后端和前端环境。
  3. 只对生产源码阻断，纯测试允许静态检查后放行。
  4. **风险范围感知的 fail closed**：相关可执行/测试/依赖配置变更才触发；测试与生产代码同等要求真实执行；纯文档不触发。
- **选择**：✅ **选项 4 + 最小健康探针 + 8 个回归场景**。
- **用户原话**："确认"。
- **理由**：
  1. 当前缺环境时未运行 Gate 却继续成功，构成确定性假绿。
  2. 纯测试、fixture 和 `conftest.py` 同样能制造假绿或破坏收集，不能仅靠 AST 后放行。
  3. 当前已有 staged path 分流，无需让纯文档安装全栈环境。
  4. binary + 工具探针能同时识别目录缺失和半损坏环境。
  5. required checks 尚未完全配置，当前不能把本地未执行检查完全交给 CI。
- **影响文件**：
  - `scripts/pre-commit`
  - 针对环境 Gate 的回归测试文件（4 步确定具体落点）
  - 本任务 `test-cases.md` / `retro.md`
- **明确排除**：hook 自动安装、required checks、bypass 审计、多 profile setup、start 服务健康、全 hook 重构、P0-1。
- **关联决策**：[`P0-1 决策 1`](../p0-1-dod-exit/decisions.md#决策-1--采用方案-a--3-个回归场景)。

## ④ 决策落地追踪 + 元信息

### 4.1 落地追踪

| # | 决策 | 落地状态 | 落地位置 | 落地日期 |
|---|---|---|---|---|
| 1 | 风险范围感知的 fail closed | ✅ 已落地（commit `e0c9995`） | `scripts/pre-commit:21-100` + `backend/tests/test_pre_commit_env_gate.py` | 2026-07-23 |

### 4.2 元信息

- **位置**：`docs/tasks/2026-07-23-bug-precommit-p0-gates/p0-2-environment-gate/decisions.md`
- **创建日期**：2026-07-23
- **决策总数**：1
- **已决策数**：1
- **待确认数**：0
- **暂缓数**：0
- **路径模式**：`fix-mini`
- **下一步**：步 5 + 6 已完成（verify.md + retro.md · hook commit 通过）。

### 4.3 落地补充

实施细节：

- `scripts/pre-commit:21-65` 后端段：3 层健康检查（`.venv` 目录 → `python` 可执行 → `pytest --version` 探针），任一失败则阻断 + 真实恢复命令（`python3 -m venv .venv && pip install -r requirements.txt`）。
- `scripts/pre-commit:67-100` 前端段：3 层健康检查（`node_modules` 目录 → `tsc` 可执行 → `tsc --version` 探针），任一失败则阻断 + `npm ci` 恢复命令。
- 删除原 `scripts/setup.sh` 误导指引（该项目无该脚本）。
- 路径分类不动：`^backend/` / `^frontend/` 已按 staged path 分流，纯 docs 不触发应用环境 Gate（已有 DOD check 兜底）。
- 8 个端到端场景全 GREEN（修复前场景 2/6 RED，修复后 8 GREEN）；完整 `pytest tests/` 722 passed。
- 测试 fixture 关键发现：python 通过 symlink 调用时 `sys.executable` 指向真实 binary，找不到 venv site-packages → 必须 wrapper script `exec host_python "$@"`。
- 决策 1 § 明确排除项全部遵守：未 hook 自动安装 / required checks / bypass trailer / 新建多 profile setup.sh / start.sh 服务健康 / 端口误判 / 全 hook 重构 / P0-1。
