---
title: P0 调研 · AI Coding Gate 与 Action provenance 止血
type: research
step: 0
date: 2026-07-28
status: approved
tags: [p0, governance, github-actions, supply-chain, ruleset]
related: [task.yaml, decisions.md, tasks.md, test-cases.md]
---

# P0 调研 · AI Coding Gate 与 Action provenance 止血

> 路径模式：`timebox`
>
> 用户授权：2026-07-28「验收步骤 0，先修两个 P0，再按方案 B 做规格。」
>
> 来源：[`AI Coding 全流程核心缺陷审计`](../2026-07-28-refactor-ai-coding-workflow-audit/research.md)

## 0. 任务理解

先恢复两条安全底线，再进入控制面 v2 规格：

1. F-02：替换不存在的 Action ref，并把 checker 从“40 位格式”升级为“`owner/repo@sha` 在上游仓库真实存在”。
2. F-01：把 GitHub ruleset 从 `disabled` 改为真实 `active`，以 required checks 形成不可由本地 skip 绕过的远端裁决。

本 P0 不重构状态机、不迁移历史任务、不修复当前后端 31 个范围外失败。

## 1. 影响

- **受影响对象**：所有 GitHub Actions run、所有依赖 required checks 的合并、CI auto-fix。
- **用户影响**：Action ref 不存在导致 auto-fix workflow 在 job 创建前失败；本地 Gate 与 CI 即使失败也不能可靠阻止合并。
- **数据损坏**：没有业务数据损坏；存在代码供应链与不合规合并风险。
- **动态基线**：
  - 本地 HEAD：`455b5d6`（审计后有并行提交，必须以当前 HEAD 验证）。
  - Ruleset `合并保护`：id `19763447`，`enforcement=disabled`。
  - `actions/upload-artifact`、`anthropics/claude-code-action` 当前共用的 `de8e...c1ac` 在目标仓库不存在。
  - 当前 checker 与 `test_security_e2e.sh` 均误报 PASS。

## 2. 临时止血

| 方案 | 时间 | 副作用 | 结论 |
|---|---:|---|---|
| A. 只换三个 SHA | 10 min | checker 仍会接受下一次伪 SHA | 不采用 |
| B. 换为官方 release SHA + CI 在线 provenance + active ruleset | 30-60 min | CI 需要访问 GitHub API；现有红检查会真实阻断 | **采用** |
| C. 暂停 auto-fix workflow，不启用 ruleset | 5 min | 失去修复能力，且 Gate 仍可绕过 | 仅作失败回滚 |

**推荐 B**。本地无网络时允许只做结构检查，但 CI 必须在线验证；网络/鉴权失败应返回非零 `BLOCKED`，不能伪 PASS。Ruleset 不提供常规 bypass。

## 3. 根本原因

1. `scripts/ci/check_action_sha.py` 把 40 位十六进制格式误当作来源真实性。
2. `scripts/ci/test_security_e2e.sh` 复用了同一弱 oracle，没有故意伪造 40 位 SHA 的反证。
3. `.github/workflows/ci.yml` 的 governance job 没运行 Action provenance 在线检查。
4. 远端 ruleset 已创建但 enforcement 为 disabled；本地 Hook 天生可被 `--no-verify` 或环境变量绕过。

### 3.1 相关文件与外部对象

- `scripts/ci/check_action_sha.py`
- `scripts/ci/test_check_action_sha.py`
- `scripts/ci/test_security_e2e.sh`
- `.github/workflows/auto-fix-ci.yml`
- `.github/workflows/ci.yml`
- GitHub ruleset `19763447`

### 3.2 官方依赖与已核验 release

| Action | release | commit SHA | 核验 |
|---|---|---|---|
| `actions/upload-artifact` | `v7.0.1` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | 官方 release API + commit API |
| `actions/download-artifact` | `v8.0.1` | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | 官方 release API + commit API |
| `anthropics/claude-code-action` | `v1.0.133` | `787c5a0ce96a9a6cfb050ea0c8f4c05f2447c251` | 官方 annotated tag 解引用 |

GitHub 的 [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use) 要求固定完整 SHA，并确认 SHA 来自该 Action 的原仓库。

### 3.3 关闭条件

- [ ] 三个无效 Action ref 替换为逐仓核验的不可变 commit SHA。
- [ ] 40 位但不存在的 SHA 在 provenance 模式返回非零。
- [ ] 网络错误、403/429、404 均 fail closed；错误信息不泄露 token。
- [ ] governance CI 执行在线 provenance，使用只读 `GITHUB_TOKEN`，无 secrets 写权限。
- [ ] ruleset `19763447` 回读为 `active`，required checks 至少含四个 CI job。
- [ ] 无常规 bypass actor；红 required check 不能满足合并条件。
- [ ] 单元测试、Shell E2E、真实 GitHub API smoke 与独立 verifier 均 PASS。

## 4. 后续时间盒

- **T+30m**：完成 Action ref 与 provenance checker 止血。
- **T+2h**：完成 CI 接线、远端 ruleset 启用和回读验证。
- **T+24h**：由本任务与 `docs/issues.md` 记录证据。
- **T+48h**：在真实 PR 上故意破坏一个 required check，确认 merge 被阻断。
- **T+72h**：在方案 B 的步骤 1 规格中吸收 Gate/证据契约。

## 5. 沟通

- **当前状态**：P0 已获用户授权，正在实施。
- **通报渠道**：当前 Codex 对话与 `docs/issues.md` 债务 23。
- **负责人**：Codex 修改与验证；用户验收；GitHub 远端配置以 API 回读为准。

## 6. 安全审查

### 6.1 威胁模型

| 攻击者能力 | 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|
| 可编辑 workflow | 伪造任意 40 位 SHA | 执行恶意/不存在 Action | 🔴 | GitHub commits API 按 repo 验证 |
| 可本地 commit/push | 跳过 Hook | 不合规变更进入远端 | 🔴 | active required ruleset |
| 可影响 API/网络 | 让 provenance 查询超时或限流 | checker 假绿或 CI 不稳定 | 🔴 | fail closed、明确 BLOCKED、超时 |
| 可提交 PR 元数据 | 诱导 shell/LLM | 注入或越权 | 🔴 | 本 P0 不把 PR 文本送入命令/LLM |

### 6.2 权限边界

```text
PR / workflow（不可信）
        |
        v
CI governance
contents: read + GITHUB_TOKEN（只用于 GET commits API）
secrets: none
writes: none
        |
        v
GitHub ruleset (active)
required checks: governance + quality + backend + frontend
bypass actors: none
        |
        v
merge allowed / blocked
```

### 6.3 不可信输入与净化

- `uses:`：只接受 `owner/repo@40hex`，owner/repo 需满足 GitHub slug allowlist 字符集。
- GitHub API 响应：只消费 HTTP 状态和返回 `sha`；限制超时与响应大小，不执行响应内容。
- Token：只从环境请求头读取，不打印、不写 artifact。
- Workflow/PR 文本：不作为 LLM 或 shell 指令。

## 7. 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 最新 Action major 版本接口不兼容 | 🔴 | 先解析 action.yml/现有 inputs；保留单独回滚 SHA |
| ruleset 启用后现有红 CI 阻断合并 | 🟠 | 这是 P0 的预期保护；不降低 required set，另修红基线 |
| API rate limit 导致 governance 阻断 | 🟠 | GITHUB_TOKEN、去重查询、短超时；明确 BLOCKED |
| 并行工作区误提交 | 🟠 | 只 stage 本 P0 白名单文件；提交前核对 staged diff |

## 8. 用户决策

| 日期 | 决策项 | 选择 | 状态 | 用户原话 |
|---|---|---|---|---|
| 2026-07-28 | P0 优先级与后续方案 | 先修 F-01/F-02，再按方案 B 做规格 | ✅ 已确认 | 「验收步骤 0，先修两个 P0，再按方案 B 做规格。」 |

## 自检清单

- [x] 任务理解已确认
- [x] 路径模式为 `timebox`
- [x] 已读 `docs/issues.md`
- [x] 已运行 `git log -10` 与 `git status`
- [x] 已定位至少 3 个相关文件
- [x] 止血方案 ≤ 3 个且有单一推荐
- [x] 依赖影响与风险已分级
- [x] 已读官方安全文档
- [x] 威胁模型 ≥ 3 个场景
- [x] 权限边界、不可信输入与依赖 SHA 已列
- [x] 用户已通过当前对话授权实施
