# pre-commit P0 Gates · 任务总览

> 日期：2026-07-23 · 状态：2 项已调研并决策，均待实施
> 目的：集中管理 `scripts/pre-commit` 假绿相关 P0，同时保持每个 Bug 的 `fix-mini` 决策、测试和复盘边界独立。

## 子任务

| # | 子任务 | 状态 | 调研 | 决策 |
|---|---|---|---|---|
| P0-1 | DOD checker 失败退出码被管道吞掉 | ✅ 已决策 · 待实施 | [`p0-1-dod-exit/research.md`](p0-1-dod-exit/research.md) | [`p0-1-dod-exit/decisions.md`](p0-1-dod-exit/decisions.md) |
| P0-2 | 后端/前端环境缺失或损坏时跳过 Gate | ✅ 已决策 · 待实施 | [`p0-2-environment-gate/research.md`](p0-2-environment-gate/research.md) | [`p0-2-environment-gate/decisions.md`](p0-2-environment-gate/decisions.md) |

## 共同约束

- 两项都走 `fix-mini`，但分别保留测试和复盘证据。
- 当前仅完成调研与决策；未修改 `scripts/pre-commit`。
- 只有用户明确说“开始实施”后才进入步骤 4。
- 事实与状态镜像见 [`docs/issues.md`](../../issues.md) 债务 11、12。
