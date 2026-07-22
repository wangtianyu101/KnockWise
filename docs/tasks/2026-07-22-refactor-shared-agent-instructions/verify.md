# 验证报告 · 统一 Codex / Claude 项目指令

> 日期：2026-07-22 · 路径：文档整理短路径 `0 → 4 → 5 → 6`

## 1. 验证范围

- `AGENTS.md`：公共规则唯一主账；完整保留原 `CLAUDE.md` 的公共硬约束。
- `CLAUDE.md`：首行原生导入 `@AGENTS.md`，仅保留 Claude Code 工具适配。
- 本任务文档：research 决策状态与 decisions 落地追踪一致。

本任务没有业务代码变化，不运行 pytest / Vitest，也不需要启动本地服务；验证采用加载契约、内容等价和静态格式检查。

## 2. 静态验证

| 检查 | 结果 | 证据 |
|---|---|---|
| Claude 原生导入 | ✅ | `CLAUDE.md:1` 为 `@AGENTS.md` |
| 单向关系、无循环 | ✅ | `AGENTS.md` 不含 `CLAUDE.md` / `@CLAUDE.md` |
| 公共硬规则完整 | ✅ | §0.2.1、§6.3、§6.5-§6.10 全部存在，具体字段与旧主账一致 |
| 工具边界 | ✅ | Claude Workflow / Agent 具体语法只存在于 `CLAUDE.md` |
| Codex 上限 | ✅ | `AGENTS.md` 25,704 bytes，低于默认 32 KiB |
| Markdown / whitespace | ✅ | `git diff --check` 无输出 |
| 实施范围 | ✅ | 未迁移 README、脚本、历史任务中的入口引用 |

## 3. Verify-Loop

### Round 1 — FAIL

- 发现 §6.8 / §6.9 被概括，遗漏决策同步的硬字段与长度要求。
- 发现公共主账仍出现 Claude `Agent` 具体工具名。
- 修复：以已提交 `HEAD:CLAUDE.md` 为公共正文基线完整重建 `AGENTS.md`，只抽离 Claude Workflow 工具段。

### Round 2 — PASS

- 独立 verifier 逐段对比旧主账和新入口。
- 确认公共正文无额外删除；差异只包括主账名替换、能力中立化和 Claude 工具段迁移。
- `AGENTS.md`：456 行 / 25,704 bytes。
- `CLAUDE.md`：53 行 / 3,176 bytes。

## 4. 结论

✅ 步骤 5 验证通过。Codex 与 Claude Code 现在共享同一公共主账，同时保留 Claude 专属工具适配；未发现规则丢失、循环导入或工具能力串线。
