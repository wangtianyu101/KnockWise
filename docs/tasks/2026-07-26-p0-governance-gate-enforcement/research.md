---
title: P0 调研 · 任务治理 Gate 未形成闭环
type: research
step: 0
date: 2026-07-26
status: approved
tags: [p0, governance, pre-commit, ci, task-state]
related: [task.yaml, decisions.md]
---

# P0 调研 · 任务治理 Gate 未形成闭环

> 路径模式：`timebox`
> 用户确认：2026-07-26「确认」

## 0. 任务理解

修复任务治理的整条本地与 CI 执行链：消除新任务状态误豁免，新增任务目录必须提供 `task.yaml`，实际 Git Hook 必须使用仓库受版本管理的脚本，CI 必须执行同一组治理检查。GitHub Ruleset 是外部设置，本次先完成代码侧 Gate 并单列残留。

## 1. 影响

- **受影响对象**：所有 2026-07 新任务、所有本地 pre-commit 使用者、所有进入 GitHub CI 的工作流文档。
- **证据**：
  - `scripts/check_task_state.py` 使用 `^docs/tasks/2026-07-\d{2}-`，误豁免整个月任务。
  - 2026-07-23 之后 18 个顶层任务目录仅 1 个含 `task.yaml`。
  - `.git/hooks/pre-commit` 与 `scripts/pre-commit` SHA-256 不一致。
  - `.github/workflows/ci.yml` 未执行 task contract / task state / DOD checker。
  - `backend/tests/test_check_task.py` 因 `_spec/spec` 变量错误无法收集。
- **数据损坏**：不涉及业务数据；影响治理事实可信度。
- **基线**：已读 `docs/issues.md`，已运行 `git log -10` 和 `git status`；不覆盖工作区现有无关改动。

## 2. 临时止血

| 方案 | 时间 | 副作用 | 结论 |
|---|---:|---|---|
| A. 只修日期正则 | 10 min | 其他逃逸仍存在 | 不采用 |
| B. checker + manifest Gate + 版本化 hooksPath + CI job | 30-60 min | 少量 CI 时间 | 推荐 |
| C. 立即回填全部历史 task.yaml | 2h+ | 易伪造历史状态 | 后续迁移 |

推荐 B：修正 legacy 范围；新增 task 目录缺 manifest 时 fail closed；用 `core.hooksPath=scripts` 消除复制漂移；CI 以只读权限运行治理 Gate；每条逃逸路径补真实退出码回归。

## 3. 根本原因

1. 宽泛日期正则把“明确历史目录”扩大成整月豁免。
2. task contract 只在 `task.yaml` 已 staged 时触发，无法发现缺失文件。
3. Hook 手工复制，仓库脚本升级不会传播。
4. CI 没有治理 job，Required Checks 也尚未配置。
5. checker 自身测试存在收集错误或缺失。

### 3.1 相关文件

- `scripts/check_task_state.py`
- `scripts/check-task.py`
- `scripts/pre-commit`
- `.github/workflows/ci.yml`
- `backend/tests/test_check_task.py`
- `backend/tests/test_pre_commit_hook.py`

### 3.2 关闭条件

- [x] 2026-07-24 之后任务不再被 legacy 正则豁免。
- [x] 新增/重命名任务目录缺 `task.yaml` 时，本地 Hook 与 CI 均非零。
- [x] 合法 manifest 在 index/worktree 两种视图均通过，INDEX 不回退 worktree。
- [x] Git 实际执行版本化 `scripts/pre-commit`。
- [x] checker 回归测试可收集且专项 74/74 全绿。
- [x] CI job 只读、无 secrets、Action 全 SHA pin。
- [x] Ruleset 未配置时保持 BLOCKED，不宣称已不可绕过。

## 4. 后续时间盒

- **T+30m**：修正误豁免、manifest 缺失逃逸和测试收集错误。
- **T+2h**：完成 CI job、hooksPath 切换和端到端回归。
- **T+24h**：建立历史任务显式迁移清单。
- **T+48h**：配置并验证 Required Checks（需外部仓库权限）。
- **T+72h**：用真实 PR/commit 故意破坏验证阻断。

## 5. 沟通

- **当前状态**：代码侧 P0 修复与独立 verifier 已 PASS；GitHub Ruleset 外部 BLOCKED。
- **通报渠道**：当前 Codex 对话。
- **负责人**：Codex 实施；用户验收；Ruleset 由具备仓库管理权限者配置。

## 6. 安全审查

已读 GitHub Actions Secure use 与 OWASP LLM Top 10。CI job 只需 `contents: read`，无 secrets、无 LLM、无写权限；第三方 Action继续 pin 完整 SHA。

| 攻击者能力 | 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|
| 可提交 PR | 新任务不带 manifest | 绕过阶段/产物约束 | 🔴 | changed-files manifest Gate |
| 可编辑 Markdown | 利用宽泛 legacy 路径 | 状态 checker 不运行 | 🔴 | 精确范围 + 负向测试 |
| 本地开发者/AI | 使用过期复制 Hook | 本地假通过 | 🔴 | 版本化 hooksPath |
| PR 作者 | 构造路径影响 Shell 分词 | 漏检或错检 | 🟡 | Python 参数数组，不用 eval |
| 第三方 Action 被移动 tag 劫持 | 供应链执行 | 恶意代码运行 | 🔴 | 完整 SHA |

```text
PR / push（不可信代码）
        |
        v
CI governance（contents: read；secrets: none；writes: none）
        |
        v
checker（只读 Git index/worktree） → PASS / non-zero FAIL

GitHub Ruleset（外部人工配置）才负责不可绕过合并 gate
```

不可信输入包括路径名、Markdown、YAML 与 Git diff；不使用 `eval`，不把 PR 元数据或日志传给 LLM。

## 7. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| 强制全部历史目录会阻断当前工作 | 🔴 | 只对新增目录 fail closed，历史迁移单列 |
| INDEX/WORKTREE 不一致 | 🔴 | 两种视图分别做临时 Git 仓库回归 |
| CI base SHA 不可用 | 🟡 | 明确 fallback，无法确定时 fail closed |
| 与现有 `docs/issues.md` 修改冲突 | 🟡 | 只追加，不覆盖 |
| 写 `.git/config` | 🟡 | 仅设置可逆的 `core.hooksPath=scripts` |

## 8. 用户决策

| 日期 | 决策项 | 选择 | 状态 | 用户原话 |
|---|---|---|---|---|
| 2026-07-26 | P0-1 范围 | 误豁免 + manifest + Hook + CI；Ruleset 单列 | ✅ 已确认 | 「确认」 |

## 自检清单

- [x] 影响判断完成
- [x] 止血方案不超过 3 个并给出单一推荐
- [x] 根因有代码与真实命令证据
- [x] 后续时间盒明确
- [x] 通报已通过当前对话发出
- [x] 已读 `docs/issues.md`
- [x] 已运行 `git log -10` 与 `git status`
- [x] 已定位至少 3 个相关文件
- [x] 已完成 CI/Agent 安全四道关
