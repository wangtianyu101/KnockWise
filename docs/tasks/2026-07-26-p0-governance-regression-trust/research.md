---
title: P0 调研 · 治理工具回归测试可信度
type: research
step: 0
date: 2026-07-26
status: approved
tags: [p0, governance, regression, subprocess, git-index]
related: [task.yaml, decisions.md, tasks.md]
---

# P0 调研 · 治理工具回归测试可信度

> 路径模式：`timebox`
> 用户确认：2026-07-26「P0-3：治理工具自己的回归测试不可信 开始修复这个吧」

## 0. 任务理解

提高治理 Gate 自身测试的故障检出能力：关键契约必须通过生产 CLI 的真实 subprocess、真实退出码和临时 Git INDEX 验证，不能只调用内部函数、搜索 workflow 源码字符串或断言自造 mock。保留精确内部单测，但不得把它们当成端到端证据。

## 1. 影响与证据

- `backend/tests/test_check_task.py` 多数场景直接 import `check-task.py` 并调用内部函数，绕过 argparse、`main()` 与退出码。
- `backend/tests/test_ci_workflow.py` 只检查 YAML 文本包含若干字符串，能证明静态配置存在，不能证明共享 checker 对坏/好 commit 的行为。
- `backend/tests/test_task_governance_gate.py` 与 `test_check_governance.py` 已使用临时 Git repo + subprocess，是可信基座，但缺少 `check-task.py` CLI 的完整 rc 分类与 INDEX/worktree 对抗样本。
- 已读 `docs/issues.md`；已跑 `git log -10`、`git status`；当前 worktree 含 P0-1/Eval 等既有改动，本任务只追加独立测试与文档。
- 相关文件：`scripts/check-task.py`、`scripts/check-governance.py`、`scripts/pre-commit`、`backend/tests/test_check_task.py`、`backend/tests/test_task_governance_gate.py`、`backend/tests/test_ci_workflow.py`。

## 2. 临时止血

| 方案 | 时间 | 可信度 | 结论 |
|---|---:|---|---|
| A. 继续补内部函数单测 | 15 min | 低，仍绕过入口 | 不采用 |
| B. 黑盒 CLI 契约 + 临时 Git INDEX + 真实 rc | 30-60 min | 高，直接覆盖生产入口 | **采用** |
| C. 引入 mutation testing 框架 | 2h+ | 高，但新增供应链与维护成本 | 后续 P1 |

## 3. 根本原因

1. 之前按函数/行数衡量覆盖，没有明确区分“算法单测”和“执行链证据”。
2. workflow 静态测试被误解释为 CI 行为测试。
3. 缺少统一的黑盒 CLI helper，导致新增 case 倾向直接 import 私有实现。

```text
task.yaml（不可信） ── Git INDEX / worktree
                         │
                         ▼
check-task.py CLI ── rc 0/1/2/3
       │
       ├── scripts/pre-commit
       └── check-governance.py ── CI workflow（静态接线证据）
```

改测试基座会影响治理专项统计，但不改变业务代码、数据库或公开 API。若黑盒测试暴露生产缺陷，再做最小生产修复并补同一回归。

## 4. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 测试复制脚本后测到副本漂移 | 🔴 | 副本只来自当前生产文件；关键 CLI case 直接运行仓库脚本 |
| INDEX case 偷读 worktree | 🔴 | staged 合法 + worktree 非法，以及 staged 缺失 + worktree 存在两组对抗样本 |
| 只断言输出不检查 rc | 🔴 | 每个黑盒场景同时断言 rc 与稳定错误码/摘要 |
| 静态 workflow 测试被当成执行证据 | 🟡 | 明确标注仅为 wiring/security contract；行为由 `test_check_governance.py` 证明 |
| 临时 Git 测试依赖全局配置 | 🟡 | 每个 repo 本地设置 user.name/email，不读写真实仓库 |

## 5. 后续时间盒

- T+30m：新增黑盒回归并记录修复前 RED。
- T+2h：CLI/INDEX/Hook/CI 共享链全绿。
- T+24h：同步 issues 与测试证据。
- T+48h：评估是否需要 mutation score。
- T+72h：在真实 CI PR 上做破坏性样本验证（外部后续，不在本地伪造）。

- [x] `check-task.py` 合法、非法、缺 manifest、错误调用均有真实 rc 证据。
- [x] INDEX 对抗样本证明不读取未暂存 worktree。
- [x] Hook/CI 行为测试继续运行生产入口，而不是 mock 返回值。
- [x] workflow 静态测试的证据边界写清楚。
- [x] 治理专项与测试质量 Gate 全绿，独立 verifier PASS。

## 6. 沟通

- **通报渠道**：当前 Codex 对话。
- **当前状态**：TDD 抓到并修复 3 个退出码契约偏差；独立 verifier PASS，待用户验收。
- **负责人**：Codex 实施；独立 verifier 复验；用户验收。
- **范围外**：Digest API 既有失败、AI Eval 批次、GitHub Ruleset 外部配置。

## 7. 安全审查

已按 GitHub Actions Secure use 与 OWASP LLM Top 10 复核。本任务不新增 Action、依赖、网络、secrets 或写权限。

| 攻击者能力 / 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|
| 提交恶意 YAML/路径 | 逃逸 checker 或命令注入 | 🔴 | subprocess 参数数组；不使用 `shell=True` / `eval` |
| 操纵 worktree 与 INDEX 不一致 | 提交内容未被真实检查 | 🔴 | 临时 Git 对抗回归 |
| 修改 workflow 文本伪造接线 | 静态测试假绿 | 🟡 | 行为证据放在共享 CLI E2E |

```text
fixtures / Git paths（不可信，只读）
          ↓
临时 repo + checker subprocess（无 secrets / 无网络）
          ↓
rc + 受限输出断言
```

外部依赖无新增；现有 Actions 继续固定 40 字符 SHA。人工 gate 仍由用户验收与 GitHub Ruleset 负责。

## 8. 决策

| 日期 | 决策项 | 选择 | 状态 | 用户原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-26 | P0-3 可信测试标准 | 生产 CLI subprocess + 临时 Git INDEX + rc/output 双断言 | ✅ 已确认 | 「开始修复这个吧」 | [decisions.md](decisions.md) |
