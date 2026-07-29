---
title: CI auto-fix 三项执行断链 · 复盘
type: retro
step: 6
date: 2026-07-29
status: drafted
tags: [retro, p0, github-actions, agent, tdd]
related: [research.md, decisions.md, tasks.md, test-cases.md, ../../issues.md]
---

# CI auto-fix 三项执行断链 · 复盘（v1.0）

> 单阶段 `timebox` 收尾。任务路径：0（research + user 验收）→ 4（1 原子 commit）→ verifier PASS → 6（retro）。
> L5 GitHub run 由用户自行执行，本任务不操控远端。
> 主账：[`docs/issues.md` 债务 24](../../issues.md)（实施已完整，等 issues.md 顶部决策段同步）。

---

## 1. 数据（必填 · 量化）

### 工作量
- 计划: 1h（T1 估时）
- 实际: 约 2h（含跨并发 gate 收敛与全量 backend 范围外 flake 处理）
- 偏差: +100%（主要来自跨并发 gate 收敛，不是代码本身慢）

### commits
- 总数: 2（实施 `8fb65bf` + 文档收尾本次 commit）
- 平均每个 task: 2 个

### 任务数
- 计划: 1 个（T1：修复 prompt、branch output 与精确 staging）
- 实际完成: 1 个
- 未完成 / 推迟: 0 个（本任务 scope） · 既有 v4 七项安全债另归 `2026-07-23-bug-ci-autofix-safety-drift/`，L5 GitHub run 由用户自执行

### 返工次数
- 总数: 3 次（T1 内验证轮次）
  1. baseline FAIL：旧测试假绿，捕获 oracle 反模式
  2. RED FAIL：新增 7 个真实行为 oracle 命中三条断链 + cached diff 偏差
  3. GREEN PASS：定向 + 扩展回归全绿
- 原因: 旧 oracle 只 grep 关键字不跑真实行为；新 oracle 写入临时 Git repo 跑真实 `git apply --index`

### 关键测试证据
- 8 workflow contract + 7 checker + 31 pytest + 2 Shell E2E + Action provenance，全绿
- 独立 verifier 固定 commit `8fb65bf` 校验 PASS（无偏差）

---

## 2. 做对的事（必填 · 可复用经验）

- ✅ **D-001 scope 锁定 + 单原子 commit**：只修 AF-01/02/03 + 必要回归测试，不污染 v4 安全债。1 commit 可审阅、可回滚。可沉淀为下次 P0 timebox 路径的默认动作（CLAUDE.md § 6 步流程强化）。

- ✅ **§ 6.10 4 道关严格执行**：不可信输入净化（只传 allowlisted `failed_job`/`error_code`，暂不传 raw-prefix `key_string`）/ 权限分层（diagnostic 无 secret + apply-fix env approval）/ 供应链防御（5 个 Action 完整 40 字符 SHA）/ 人工 gate（L5 GitHub run 用户自执行）。任一项被攻击者穿透仍受其他三关拦截。可沉淀为 `docs/rules/security-rules.md` "CI agent 改动必过 4 道关 checklist"。

- ✅ **TDD 红→绿顺序**：先写 7 failed 命中 AF-01/02/03 + cached diff 偏差 → 修复 → 8 PASS。防止"测试只追改后的实现"。可沉淀为 CI workflow 改动的默认流程（`docs/templates/ci-workflow-test-template.md` 起草）。

- ✅ **真实 oracle 而非 grep-only**：用 `subprocess.run(["git", "apply", "--index"], ...)` + 临时 Git repo + `rc/output` 双断言；旧 `test_auto_fix_e2e.sh` 8/8 PASS 但行为断链被直接捕获。可沉淀为 `docs/rules/testing-oracle-anti-patterns.md` 反模式清单（4 类：grep 关键字 / 不执行 prompt 链 / 只读声明文件 / 不跑真实 subprocess）。

- ✅ **独立 verifier 固定 commit 校验**：新 Agent prompt，零上下文复用，复跑 8 workflow + 7 checker + Shell E2E + security 四关。验证 writer 不存在自证循环。可沉淀为 § 6.7 commit 边界独立 verifier 的标准实践。

- ✅ **diff checker 改查 cached diff 而非 `HEAD~1`**：之前 `get_changed_files()` 跑 `git diff HEAD~1 --name-only`，未提交前永远空。阻断"policy 在错误数据源上做决策"反模式。可沉淀为 `docs/rules/git-diff-policy.md`。

- ✅ **`key_string` 暂不传 + 安全债显式标注**：修通 prompt 后 `key_string` 会激活间接 prompt injection，本任务只传 allowlisted fields，安全债保留给 v4 sanitizer 并显式写在 `decisions.md` D-002 落地追踪 + `issues.md` 决策段。

---

## 3. 做错的事（必填 · 根因分析）

- ❌ **issue.md 顶部决策段同步滞后**：
  - **现象**：commit `8fb65bf` 落地 + verifier PASS 后，`docs/issues.md:24` 仍标"🔴 P0 步骤 4 TDD 实施中"；`docs/issues.md:886` 债务 24 章节仍标"🚧 实施中"；`docs/issues.md:43` 决策更新段 D-002 仍写"步骤 4 实施中"。直到 retro.md 起草时才同步。
  - **根因**：§ 6.5 任务完成自动更新规则明确"每个 commit 完成 → 立即回写 → 再做下一个"，但本次在 commit 后只回写了 `tasks.md`，未回写 `issues.md` 顶部决策段（认为"tasks.md 已 ✅ 等于任务完成"）。
  - **影响**：用户重启会话或其他人看 `docs/issues.md`，会把已完成的债务 24 误判为 P0 进行中，重复分配关注度；监控与治理也以 issues.md 顶部决策段为准，状态不准会误导告警与决策。

- ❌ **跨并发 gate 收敛估时偏低**：
  - **现象**：研究阶段估时 1h（T+30m + T+2h 内），实际跨并发 gate + 处理全量 backend 范围外 flake 约 2h（+100%）。
  - **根因**：`timebox` 估时模型只算了"代码时间"，未算"跨并发 gate 收敛时间"（治理 Gate、安全 E2E、Action provenance、workflow contract 等独立 gate 在并发提交下需要稳定通过的额外时间）。
  - **影响**：reporter 看到 +100% 偏差可能误判"实施慢"，但实际是治理成本。

- ❌ **research.md § 六.3 估时模型缺"并发 gate"维度**：
  - **现象**：research.md § 六.3 把"三项失败回归先红后绿 + 最小 workflow/index 修复"估为 T+30m + T+2h，未细分治理/安全/provenance 收敛时间。
  - **根因**：timebox 模板只列了 RED/GREEN/verifier 三阶段，没把"跨任务并发门禁收敛"作为独立维度。
  - **影响**：下次类似任务（CI / auto-fix / 治理工具改动）估时同样会偏低。

- ❌ **`HEAD 漂移` 调研阶段风险已识别但未在 § 0 调研清单加显式 step**：
  - **现象**：research.md § 二.5 提到"实施时必须重新读取 diff，禁止覆盖其他 Agent 的未提交修改"，但 tasks.md § 4 实施顺序未把"git status -sb + git diff HEAD -- <file>"作为 step 0 必做动作。
  - **根因**：调研阶段识别了风险但没把"风险 → 任务动作"的映射写进 tasks.md。
  - **影响**：下次同类型 CI 改动若未先查 working tree，可能覆盖其他 Agent 的并行提交。

### 3.1 失效链五问（针对"Oracle 假绿"严重问题）

```text
需求/Writer → 测试 oracle → Verifier → CI/合并策略 → 文档状态
```

- **本层本应阻断什么**：测试 oracle 应在三项断链（AF-01/02/03）存在时返回 FAIL，阻止 commit 与合并。
- **为什么没阻断**：旧 oracle 跑 `grep "with.prompt" .yml` 等关键字存在性检查，不执行 prompt shell 展开、不验证 step id、不跑 `git add --dry-run -A`。
- **上游信号如何被错误解释**：测试输出 "8/8 PASS" 被解释为"行为正确"，实际只是"声明文本存在"。
- **哪条机器约束能让同类问题下次自动失败**：
  1. CI/E2E 测试必须跑真实 subprocess（`subprocess.run(["git", ...], check=True)`）+ rc/output 双断言，禁止 grep-only oracle
  2. check-step.py 扩展为新增 checker：`scripts/check_oracle_quality.py` 检测测试文件中 `assert "..." in <text>` 类只读声明的语句并 flag
  3. retro.md 模板"做错"段强制要求"失效链五问"（已具备）
- **根因终点的判断**：根因不是"AI 粗心"，而是"测试模板鼓励 grep-only oracle"。要彻底修复需在测试模板层引入"真实 subprocess 强制"约束。

---

## 4. 改进项（必填 · 必须分配）

- [ ] 改进 1: 把"CI agent 改动必过 § 6.10 4 道关"作为强制 checklist 加入 `docs/rules/security-rules.md`，并加 pre-commit `check_security_gates.py` 自动检测变更是否触及 `.github/workflows/auto-fix-ci.yml` / `apply-fix` job / Action 输入映射
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-05
  - 沉淀到: `docs/rules/security-rules.md`（新增 § 6.10 强化段）+ `scripts/check_security_gates.py`（新增 checker）

- [ ] 改进 2: 把"CI/E2E 测试必须跑真实 subprocess"加入 `docs/rules/testing-rules.md`，并扩展 `scripts/check_test_quality.py` 检测 grep-only oracle
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-08
  - 沉淀到: `docs/rules/testing-rules.md` § 6.5 + `scripts/check_test_quality.py`（新增 oracle 模式检测）

- [ ] 改进 3: 把"commit 后立即回写 `docs/issues.md` 顶部决策段"作为 § 6.5 任务完成自动更新规则的硬性条款，并把 check-step.py tasks 校验扩展为同时校验 issues.md 顶部状态字段
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-07-31
  - 沉淀到: `AGENTS.md` § 6.5 + `scripts/check-step.py` tasks 校验（扩展）

- [ ] 改进 4: 把"timebox 估时需含跨并发 gate 收敛维度"加入 research.md / tasks.md 模板的 § 六估时段
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-05
  - 沉淀到: `docs/templates/research-template.md` § 六 + `docs/templates/tasks-template.md` § 5

- [ ] 改进 5: memory 写入 `feedback-oracle-grep-false-green.md` + `feedback-ci-workflow-tdd-red-green-first.md` 两条新 memory
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-07-30
  - 沉淀到: `~/.claude/projects/-Users-wangtianyu-IdeaProjects-KnockWise/memory/MEMORY.md` 索引 + 两个独立文件

---

## 5. 沉淀到哪（必填）

- [ ] 已更新 CLAUDE.md（<哪节>）—— 未直接更新（CLAUDE.md § 6.10 已有 4 道关；本任务合规使用）
- [ ] 已更新 docs/DOD.md（<哪步>）—— 未直接更新（DOD.md § 八 6 步复盘 DOD 已具备；本任务按其执行）
- [ ] 已更新 <某个模板>（<哪段>）—— 改进 4 计划更新 `docs/templates/research-template.md` § 六与 `docs/templates/tasks-template.md` § 5（2026-08-05 前）
- [x] 已新增议題到 docs/issues.md —— 债务 24 已标 ✅ · 关联债务 17（v4 安全债）· 关联债务 23 P0 containment（T1 ✅ + T2 待办）
- [x] 已新增 memory 候选：`feedback-oracle-grep-false-green.md` + `feedback-ci-workflow-tdd-red-green-first.md`（见 § 4 改进 5 · 待写）

### 5.1 规则落地证据

| 失败模式 | 新规则/脚本 | 触发时机 | 失败表现 | 验证状态 |
|---|---|---|---|---|
| CI/E2E 测试 grep-only oracle 让真实行为断链通过 | `docs/rules/testing-rules.md` § 6.5（"必须跑真实 subprocess"）+ `scripts/check_test_quality.py` 扩展检测 | commit 边界 pre-commit | `check_test_quality.py` exit 1 + 阻断 commit | 待验证（改进 2 · 截止 2026-08-08） |
| CI agent 改动绕过 § 6.10 4 道关 | `docs/rules/security-rules.md` 强化段 + `scripts/check_security_gates.py` 新增 | commit 边界 pre-commit + workflow 文件改动 | `check_security_gates.py` exit 1 + 阻断 commit | 待验证（改进 1 · 截止 2026-08-05） |
| 任务完成后 `docs/issues.md` 顶部状态不立即同步 | `AGENTS.md` § 6.5 强化 + `scripts/check-step.py` tasks 扩展 | commit 边界 pre-commit | `check-step.py` exit 1 + 阻断 commit | 待验证（改进 3 · 截止 2026-07-31） |
| timebox 估时偏低，跨并发 gate 收敛未算入 | `docs/templates/research-template.md` § 六 + `docs/templates/tasks-template.md` § 5 | 调研阶段 0 步 + 拆分阶段 3 步 | checker 暂不强制 · 模板自约束 | 待验证（改进 4 · 截止 2026-08-05） |

> 只写"建议增加"不算沉淀；必须给出文件位置。尚未实测的新规则标记"待验证"，不得写成已生效。

---

## 6. 元信息与关联任务

- **路径模式**：`timebox`（步骤 0 → 4 → 6，无 1/2/3/5 独立阶段）
- **commits**：`8fb65bf`（T1 实施）+ 本次 commit（retro.md v1.0 + issues.md 状态同步）
- **测试**：8 workflow contract + 7 checker + 31 pytest + 2 Shell E2E + Action provenance，全绿
- **独立 verifier**：固定 commit `8fb65bf`，PASS
- **L5 GitHub run**：BLOCKED（用户自行执行，本任务不操控远端）
- **关联任务**：
  - 既有 v4 安全债：[`2026-07-23-bug-ci-autofix-safety-drift/`](../2026-07-23-bug-ci-autofix-safety-drift/)（refactor-6，待用户实施授权）
  - Action provenance fail-closed：[`2026-07-28-p0-ai-coding-containment/`](../2026-07-28-p0-ai-coding-containment/)（T1 已 ✅ commit `c2965e6`，T2 远端 ruleset 启用 PENDING）
  - AI Coding 控制面方案 B：[`2026-07-28-refactor-ai-coding-workflow-audit/`](../2026-07-28-refactor-ai-coding-workflow-audit/)（待 P0 完成后做）
- **用户验收**：
  - D-001（scope）：✅ 已确认
  - D-002（path + prompt 边界）：✅ 已验收
  - 步骤 4 实施 + verifier PASS：✅ 已完成
  - L5 GitHub run：⏳ BLOCKED（用户自执行）