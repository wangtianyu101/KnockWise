# Auto-fix CI · GitHub Environment 配置指南

> 关联：[spec.md R10](../../tasks/2026-07-22-new-feature-ci-autofix/spec.md) + [tasks.md T19](../../tasks/2026-07-22-new-feature-ci-autofix/tasks.md)

## 为什么需要 Environment

`auto-fix-ci.yml` 的 `apply-fix` job 配置了 `environment: auto-fix-approval`。这个环境是 **人工审批 gate**（CLAUDE.md § 6.10 关 4）· 没有这个环境，apply-fix job 会立即跑（不安全）。

## 配置步骤

### 1. 创建 Environment

1. 打开 GitHub repo → **Settings** → **Environments** → **New environment**
2. Name: `auto-fix-approval`
3. 点击 **Configure environment**

### 2. 配置 Required reviewers（R10 关 4）

- ✅ **Required reviewers**: 添加你自己（或团队 lead）
- **Deployment branches**: 选 `Selected branches` → 添加 `feature/**` 和 `codex/**`（与 ci.yml 监听范围一致）

> 📌 **关键**：必须勾选 "Required reviewers" · 否则 workflow 会跳过审批直接跑

### 3. 限制 Secrets 范围

- **ANTHROPIC_API_KEY** secret → 默认是全 repo 可见
- 在 Environment 配置页下方有 **Environment secrets**
- 把 `ANTHROPIC_API_KEY` 改到 **Environment secrets** 而非 Repository secrets
- 这样 secrets 仅在 `auto-fix-approval` env 内可用 · 进一步限制暴露面

### 4. 验证

推送一个故意失败的 commit → 触发 `CI` → CI 失败 → auto-fix 启动

预期行为：
- ✅ diagnostic job 立即跑（无需审批）
- ⏸ apply-fix job 状态显示 "Waiting for approval"
- 你的邮箱收到 GitHub notification
- 点击 "Approve" 后 apply-fix 跑
- 失败上限到 3 次后 apply-fix 自动跳过 + 开 issue

## 关闭 Auto-fix

**完全关闭**（不推荐）：
- Settings → Environments → `auto-fix-approval` → 删环境

**临时关闭**：
- 在 PR 上加 label `auto-fix-disabled`（workflow 应检查此 label · 当前实现未做 · 后续 T19+ 加）

## 故障排查

| 现象 | 排查 |
|---|---|
| apply-fix 一直 "Waiting" | 没配 Required reviewers？或 reviewers 没批？ |
| auto-fix 完全不触发 | workflow_run 触发器只监听 `CI` workflow · 改名了？ |
| label API 404 | label 不存在会创建 · 但首次需 GITHUB_TOKEN 有写权限 |
| fork PR 也跑了？ | 检查 `head_repository.fork` filter · 不应在 fork 跑 |

## 相关文档

- [GitHub: Using environments for deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub: Workflow security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [memory: workflow-run-secrets-risk](../../../../Users/wangtianyu/.claude/projects/-Users-wangtianyu-IdeaProjects-KnockWise/memory/feedback-workflow-run-secrets-risk.md)