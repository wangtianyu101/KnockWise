---
title: CI 失败自动修复 · 决策主账（v2 · 含安全审查）
date: 2026-07-22（v2 修订）
status: 决策 v2（10/10 全拍 · 含安全审查）
type: 决策详细主账
related:
  - research.md（调研报告 v2）
  - docs/issues.md（议题主账 · 镜像）
  - memory/feedback-ai-agent-security-4-gates.md（4 道关主规则）
---

# 决策主账 · CI 失败自动修复（v2 · 含安全审查）

> 📌 **本文件是决策最权威详细主账**（按 CLAUDE.md § 6.9）
> **v2 修订**：2026-07-22 用户指出 P0 风险 → 重做安全审查 → 决策 2-5 修订 + 决策 7-10 新增
> 镜像位置（按 § 6.8 同步）：
> - 简表 + 链接 → `research.md` § 八
> - 顶部决策段 + 状态字段 → `docs/issues.md` 决策更新
> - 规格实现 → `spec.md`（1 步产出后链接）

---

## ① 顶部权威定位

本文件记录本次新功能任务所有决策的**详细原话 + 理由 + 影响文件 + 关联**。v2 新增 4 项安全决策（7-10），与 v1 决策 1-6（已修订）合并为 10 项全集。

关联文档：
- 调研：[`research.md`](research.md) v2
- 议题主账：[`docs/issues.md`](../../issues.md)
- 规格（待 1 步产出）：`spec.md`
- 安全规则主账：CLAUDE.md § 6.10

---

## ② 决策总览表（10 项 · v2 全集）

| # | 日期 | 决策项 | 选择 | 状态 | v2 修订 | 关联 |
|---|---|---|---|---|---|---|
| 1 | 2026-07-22 | 走哪个方案 | ✅ 方案 1（Claude Code Action）+ pin SHA | ✅ 已决策 | 加 SHA 约束 | research § 6.2 |
| 2 | 2026-07-22 v2 | ~~commit 推原分支~~ → Draft PR | ✅ auto-fix/<branch>-<sha> + Draft PR | ✅ 已决策 | **修订** | research § 6.2 |
| 3 | 2026-07-22 v2 | ~~2 次/commt~~ → 3 次/commt | ✅ 3 次/commt（label 计数） | ✅ 已决策 | **修订** | research § 6.2 |
| 4 | 2026-07-22 v2 | job 白名单加固 | ✅ 含 backend 限 typecheck/coverage + backend service 必走 Draft PR | ✅ 已决策 | **修订加固** | research § 6.2 |
| 5 | 2026-07-22 v2 | ~~[NO-TEST-NEEDED]~~ → 外部 check | ✅ 强制 T33 + pytest 实际绿（移除 self-attestation） | ✅ 已决策 | **修订** | research § 6.2 |
| 6 | 2026-07-22 | API 费用上限 | ✅ $20/月 | ✅ 已决策 | 不变 | research § 6.2 |
| 7 | 2026-07-22 v2 | 🆕 Action pin SHA | ✅ 第三方 Action 完整 40 字符 SHA | ✅ 已决策 | **新增** | memory `pin-third-party-action-sha` |
| 8 | 2026-07-22 v2 | 🆕 双 job 权限分层 | ✅ diagnostic（read-only）+ apply-fix（env approval） | ✅ 已决策 | **新增** | memory `workflow-run-secrets-risk` |
| 9 | 2026-07-22 v2 | 🆕 Fork PR 排除 | ✅ `if: github.event.workflow_run.head_repository.fork == false` | ✅ 已决策 | **新增** | CLAUDE.md § 6.10 关 2 |
| 10 | 2026-07-22 v2 | 🆕 日志净化 | ✅ 仅传 job 名 + 错误类型 + 截断字符串（前 200 字符） | ✅ 已决策 | **新增** | memory `untrusted-data-not-instruction` |

---

## ③ 决策详细记录

### 决策 1 · 走方案 1（Claude Code Action + SHA 约束）

- **日期**：2026-07-22
- **决策项**：用 3 个备选方案中的哪个实现 CI 失败自动修复
- **选项列表**：
  1. **方案 1**：官方 `anthropics/claude-code-action` + `workflow_run` 触发 + 双 job 结构
  2. 方案 2：CI 失败自动开 issue + `@claude` mention
  3. 方案 3：本地 cron 轮询 + 启 Claude Code session
- **选择**：**方案 1**（v1）+ v2 加 SHA 约束
- **用户原话**："按方案一实现吧"（2026-07-22 chat）
- **理由**（3 条）：
  1. **全自动**：不需要 GitHub App 安装 / OAuth 复杂配置
  2. **触发链路清晰**：`workflow_run` 监听 CI 完结事件
  3. **可叠加安全约束**：v2 加 SHA 固定 + 双 job + env approval
- **影响文件**：`.github/workflows/auto-fix-ci.yml`（新增）

### 决策 2 · ~~commit 推原分支~~ → Draft PR（v2 修订）

- **日期**：2026-07-22 v2
- **决策项**：auto-fix 修复后是直接 commit 推原 PR 分支，还是开 Draft PR
- **v1 选择**：❌ 推原分支（已废除）
- **v2 选择**：✅ **auto-fix/<branch>-<sha> 新分支 + Draft PR**（强制人工 gate）
- **用户原话**："风险很高 ... 改成：CI 失败 → 只读诊断 Agent → 生成补丁 → 新建 auto-fix 分支和 Draft PR → 无密钥环境重新跑全部 required checks → 人工 review → 才允许合并"（2026-07-22 chat）
- **理由**（3 条 · v2）：
  1. **密钥风险 ↓**：原分支 push 绕开 review + 暴露 secrets · Draft PR 强制人工 gate
  2. **透明可审计**：所有 auto-fix 都走 PR 流程 · 强制 required status checks
  3. **可叠加 env approval**：apply-fix job 需 environment approval
- **影响文件**：
  - `auto-fix-ci.yml` apply-fix job：开 Draft PR 而非 push 原分支
  - `scripts/ci/check_auto_fix_diff.py`（新增）

### 决策 3 · ~~2 次/commt~~ → 3 次/commt（v2 修订）

- **日期**：2026-07-22 v2
- **决策项**：同一 commit 失败多少次后停止 auto-fix
- **v1 选择**：❌ 2 次/commt（已修订）
- **v2 选择**：✅ **3 次/commt**（Draft PR 流程下给人工 gate 更多缓冲）
- **用户原话**：v2 隐含（按"C 改造"接受推荐）
- **理由**（3 条 · v2）：
  1. Draft PR 流程下，3 次失败仍只产生 1 个 PR（不污染 git history）
  2. 1 USD token × 3 = 3 USD/commt · 仍在 $20/月预算内
  3. 第 4 次失败 → 转人工 issue
- **影响文件**：`auto-fix-ci.yml` label check step

### 决策 4 · job 白名单加固（v2 修订）

- **日期**：2026-07-22 v2
- **决策项**：auto-fix 能修哪些 CI job + backend service 改动处理
- **v1 选择**：含 backend 但限 typecheck/coverage
- **v2 选择**：✅ **v1 不变 + 加固**：**backend service 文件改动必走 Draft PR（不允许 auto-fix 直接 push）**
- **用户原话**："不把原始 CI 日志直接作为高权限 Agent 指令" + 整体安全审查（2026-07-22 chat）
- **理由**（3 条 · v2）：
  1. backend service（interview / digest / report 等）含核心业务逻辑
  2. 即使 Claude 修复"看起来对"，也需人工 review
  3. Draft PR + 强制人工 review = 不让 auto-fix 在 service 层"自动 commit"
- **影响文件**：`scripts/ci/check_auto_fix_diff.py` 检测 `backend/services/*.py` 改动 → 强制 `NEEDS_REVIEW=true` → 走 Draft PR 流程

### 决策 5 · ~~[NO-TEST-NEEDED]~~ → 外部 check（v2 修订）

- **日期**：2026-07-22 v2
- **决策项**：与 CLAUDE.md § 6.1 单测强制规则怎么协同
- **v1 选择**：❌ `[NO-TEST-NEEDED]` 自我豁免（已废除 · 用户指出 self-attestation 不安全）
- **v2 选择**：✅ **强制外部 check（T33 + pytest 实际绿 · 移除 self-exemption）**
- **用户原话**："不允许 [NO-TEST-NEEDED] 仅靠 commit message 自我豁免"（2026-07-22 chat）
- **理由**（3 条 · v2）：
  1. 自我豁免 = self-attestation · 攻击者可借此绕过 § 6.1
  2. T33 阻断器 + pytest 实跑已存在 · 不需要新增机制
  3. Draft PR 流程下 + required checks = 充分把关
- **影响文件**：
  - 移除 v1 中的 `[NO-TEST-NEEDED]` 逻辑
  - `scripts/ci/check_auto_fix_diff.py`：仅检测 `backend/services/*.py` 改动（不再豁免单测）

### 决策 6 · API 费用上限

- **日期**：2026-07-22
- **决策项**：每月 API 费用上限多少
- **选择**：✅ $20/月
- **用户原话**："按照推荐"（2026-07-22 chat）
- **理由**：当前 CI baseline 0 failed · $20 足够 ~20-40 次 auto-fix · 超限 Anthropic Console 拦截

### 决策 7 · 🆕 Action pin 完整 SHA（v2 新增）

- **日期**：2026-07-22 v2
- **决策项**：第三方 Action 版本固定方式
- **选项列表**：
  1. ❌ `@beta` / `@main` / `@v1` 移动 tag（供应链风险）
  2. ❌ `@<7-char-short-sha>` 短 SHA（GitHub 不推荐）
  3. ✅ `@<40-char-full-sha>` 完整 SHA（GitHub 官方建议）
- **选择**：✅ **完整 40 字符 SHA**
- **用户原话**："Action 固定完整 SHA"（2026-07-22 chat）
- **理由**（3 条）：
  1. `@beta` 等移动 tag 被劫持后 workflow 自动跟随（无需 review）
  2. 完整 SHA 不可变 · 升级前可 review commit diff
  3. 符合 GitHub [Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions) 官方建议
- **影响文件**：
  - `auto-fix-ci.yml`：所有 `uses:` 改为完整 SHA
  - 升级流程：手动 review 新 release 的 commit diff → 改 SHA

### 决策 8 · 🆕 双 job 权限分层（v2 新增）

- **日期**：2026-07-22 v2
- **决策项**：workflow job 结构
- **选项列表**：
  1. ❌ 单 job 含 secrets + checkout + push（密钥风险）
  2. ✅ **双 job：diagnostic（read-only）+ apply-fix（env approval）**
- **选择**：✅ **双 job**
- **用户原话**："权限拆分成诊断 job 和写入 job。写入 job 使用 environment approval"（2026-07-22 chat）
- **理由**（3 条）：
  1. 最小权限原则 · diagnostic 无 secrets → 即使被攻陷也无法外发密钥
  2. apply-fix 仅在 human-approved environment 内暴露 secrets
  3. 符合 CLAUDE.md § 6.10 关 2
- **影响文件**：
  - `auto-fix-ci.yml` 拆 `diagnostic` + `apply-fix` 双 job
  - GitHub Settings 配 environment `auto-fix-approval` + required reviewers

### 决策 9 · 🆕 Fork PR 排除（v2 新增）

- **日期**：2026-07-22 v2
- **决策项**：是否处理 fork PR
- **选项列表**：
  1. ❌ 处理 fork PR（非可信代码 · 密钥风险）
  2. ✅ **不处理 fork PR**（`if: head_repository.fork == false`）
- **选择**：✅ **不处理 fork PR**
- **用户原话**："不处理 fork PR 的非可信代码"（2026-07-22 chat）
- **理由**（3 条）：
  1. Fork PR 代码来自非仓库成员 · 不应自动 checkout + Claude 工具执行
  2. 即使有 PR review，auto-fix 流程仍可能被恶意代码污染
  3. 仓库成员通过 branch push 创建 PR · 自然不会被 fork 排除
- **影响文件**：`auto-fix-ci.yml` 加 `if: github.event.workflow_run.head_repository.fork == false`

### 决策 10 · 🆕 日志净化（v2 新增）

- **日期**：2026-07-22 v2
- **决策项**：LLM 接收的 CI 日志如何处理
- **选项列表**：
  1. ❌ 直接传 raw CI 日志（prompt injection 入口）
  2. ✅ **日志净化**：仅传 job 名 + 错误类型 + 截断字符串（前 200 字符）
- **选择**：✅ **日志净化**
- **用户原话**："不把原始 CI 日志直接作为高权限 Agent 指令"（2026-07-22 chat）
- **理由**（3 条）：
  1. CI 日志含 PR 标题 / commit msg / 错误堆栈 · 都可能被攻击者构造
  2. 净化后仅传关键信息 · LLM 无法被注入
  3. 符合 CLAUDE.md § 6.10 关 1
- **影响文件**：
  - `scripts/ci/sanitize_ci_log.py`（新增）
  - `scripts/ci/test_sanitize_ci_log.py`（单测）

---

## ④ 决策落地追踪 + 元信息

### 4.1 落地追踪表

| # | 决策 | 落地状态 | 落地位置 | 落地日期 |
|---|---|---|---|---|
| 1 | 方案 1 + SHA 约束 | 🟡 已决策 · 待实施 | `auto-fix-ci.yml` + 各 `uses:` SHA | 4 步实施时 |
| 2 | Draft PR | 🟡 已决策 · 待实施 | `auto-fix-ci.yml` apply-fix job | 4 步实施时 |
| 3 | 3 次/commt | 🟡 已决策 · 待实施 | `auto-fix-ci.yml` label check | 4 步实施时 |
| 4 | job 白名单 + Draft PR 加固 | 🟡 已决策 · 待实施 | `scripts/ci/check_auto_fix_diff.py` | 4 步实施时 |
| 5 | 外部 check（T33 + pytest） | 🟡 已决策 · 待实施 | T33 已存在 + apply-fix 跑 pytest | 4 步实施时 |
| 6 | API 费用 $20/月 | 🟡 用户去 Anthropic Console 配 | 项目外（Anthropic Console） | 用户手动 |
| 7 | Action pin SHA | 🟡 已决策 · 待实施 | `auto-fix-ci.yml` + 升级流程 | 4 步实施时 |
| 8 | 双 job + env approval | 🟡 已决策 · 待实施 | `auto-fix-ci.yml` + GitHub Settings | 4 步实施时 + 用户配 env |
| 9 | Fork PR 排除 | 🟡 已决策 · 待实施 | `auto-fix-ci.yml` `if:` | 4 步实施时 |
| 10 | 日志净化 | 🟡 已决策 · 待实施 | `scripts/ci/sanitize_ci_log.py` + 单测 | 4 步实施时 |

### 4.2 元信息

- **位置**：`docs/tasks/2026-07-22-new-feature-ci-autofix/decisions.md`
- **创建日期**：2026-07-22
- **v2 修订日期**：2026-07-22（含安全审查 · 用户拍板 "C" 改造）
- **决策总数**：10
- **已决策数**：10（100%）
- **待确认数**：0
- **暂缓数**：0
- **v1 → v2 修订数**：5（决策 2-5）+ 新增数 4（决策 7-10）
- **下一步**：进 1 步写 spec.md（10 Requirement + 12 Scenario） → 2 步 plan.md（T15-T20 双 job 任务） → 3 步 tasks.md（T1-T20 含安全任务）