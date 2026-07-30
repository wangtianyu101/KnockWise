---
title: AI Coding 全流程核心缺陷审计
type: research
step: 0
date: 2026-07-28
status: approved
tags: [research, refactor, ai-coding, governance, security]
related:
  - decisions.md
  - ../../issues.md
  - ../../DOD.md
---

# 🔧 调研报告 · 重构：AI Coding 全流程控制面

> 日期：2026-07-28 · 调研人：Codex · 议题编号：债务 23
>
> 路径模式：`refactor-6`
>
> **结论先行**：流程的价值观和质量目标没有根本错误，但执行控制面存在核心缺陷。当前系统能生产大量“合规文档”，却不能可靠保证状态唯一、证据真实、Gate 不可绕过。综合判定为 **2 个 P0 + 8 个 P1**；在 P0 修复前，不应把“流程通过”等同于“可安全合并”。
>
> **步骤 0 验收**：✅ 用户已于 2026-07-28 验收本调研；决策为先修复两个 P0，再按方案 B 进入步骤 1 规格。用户原话：「验收步骤 0，先修两个 P0，再按方案 B 做规格。」

## 1. 任务理解

- **用户原话**：「再检验一下整个ai coding 流程吧 判断有没有核心缺陷」
- **用户确认**：「确认调研」
- **任务复述**：系统审计 0→6 路径、双 Gate、TDD、verifier、状态主账、Hook、CI、远端合并保护与 Agent 安全边界，判断是否存在结构性缺陷；本步骤只记录事实、风险与备选方案，不修改流程实现。
- **重构目标**：
  - [x] 一致性：规则、模板、checker、历史实践使用同一语义
  - [x] 可维护性：减少镜像主账与人工同步
  - [x] 可测试性：Gate 验证真实契约，而非只匹配文本形状
  - [x] 安全性：本地 Agent、CI Agent、verifier 和远端合并均有明确权限边界
  - [x] 效率：治理成本与任务风险成比例
- **议题编号**：债务 23
- **不重构会怎样**：流程可以继续出现“本地跳过、CI 失败、ruleset 未启用，但任务已写 ACCEPTED”的分裂状态；安全 checker 也可能接受根本不存在的依赖 SHA。
- **范围外**：本步骤不修代码、不启用 ruleset、不改 GitHub 设置、不迁移历史任务。

## 2. 现状分析

### 2.1 重构对象

| 对象 | 规模/位置 | 职责 |
|---|---|---|
| `AGENTS.md` | 474 行 | 0→6 流程、双 Gate、任务状态、决策同步、安全四关 |
| `docs/DOD.md` | 166 行 | 各阶段完成定义 |
| `docs/rules/checklist.md` | 114 行 | 阶段交付物和路径说明 |
| `docs/rules/testing-rules.md` | 105 行 | L1-L5、Harness、E2E 边界 |
| `scripts/pre-commit` | 290 行 | 本地测试、文档、manifest、状态 Gate |
| `scripts/check-step.py` | 500+ 行 | 单文档 DOD checker |
| `scripts/check-task.py` | 300+ 行 | `task.yaml` 目录契约 |
| `scripts/check_task_state.py` | 230+ 行 | tasks/verify 状态语义 |
| `.github/workflows/ci.yml` | 4 jobs | 远端治理、测试质量、后端、前端 |
| `.github/workflows/auto-fix-ci.yml` | Agent workflow | CI 失败诊断与 Draft PR |
| `docs/issues.md` | 898 行 | 长期议题唯一主账与决策镜像 |

### 2.2 调用方清单

1. **Writer Agent** → 读取 `AGENTS.md` / task docs，修改代码、测试和状态。
2. **Verifier Agent** → 读取同一 workspace 的 spec/plan/tests，输出 PASS/FAIL。
3. **用户** → 在每个阶段执行人工 Gate，并决定产品、设计、方案和验收。
4. **本地 Git Hook** → 根据 staged files 运行测试和治理 checker。
5. **GitHub Actions** → 在提交后运行远端 CI。
6. **GitHub ruleset** → 决定失败的检查是否真的阻止合并。
7. **后续会话/Agent** → 从 `task.yaml`、tasks、issues、decisions、verify、retro 恢复状态。

### 2.3 当前测试与执行基线

| 探针 | 实测结果 | 含义 |
|---|---|---|
| `./scripts/start.sh` | 5 个服务已运行 | 满足项目开工规则；也证明纯文档审计被迫启动无关服务 |
| `git status --short --branch` | 11 组未跟踪文件/目录 | 多任务并行，状态同步和误提交风险真实存在 |
| `git log -10` | 大量“实施 commit → commit hash 回写”交替提交 | commit 协议存在结构性回填 |
| `python3 scripts/ci/check_action_sha.py` | rc=0，声称全部 SHA 合法 | 只验证 40 位格式 |
| `sh scripts/ci/test_security_e2e.sh` | rc=0，声称四关全过 | 静态结构测试通过 |
| GitHub API：两个 Action SHA | `No commit found for SHA` | 格式 Gate 与供应链真实性脱节 |
| GitHub Actions baseline run `30272696075` | `conclusion=failure` | 审计基线 commit `21414ad` 的远端 CI 为红 |
| GitHub ruleset API | 唯一 ruleset `合并保护` 为 `disabled` | 红 CI 不阻止合并 |
| 重放 `1665a5b` 的 governance diff | 6 类失败 | Gate 上线后仍有不合规任务提交进入历史 |

仓库共有 35 个一级 task 目录；其中 `research.md` 31 个、`decisions.md` 21 个、`tasks.md` 21 个、`verify.md` 13 个、`task.yaml` 仅 7 个。数量本身不是错误，但说明历史状态恢复需要跨代兼容，不能假定 manifest 已覆盖全仓。

### 2.4 依赖关系

```text
用户意图
  ↓
research/spec/plan/tasks/decisions
  ↓
Writer Agent ──→ code + tests ──→ local pre-commit
  │                    │                │
  │                    └──────────────→ commit
  │                                      ↓
  └────────→ Verifier Agent          GitHub CI
                   │                     ↓
                   └→ PASS/FAIL      ruleset / merge

状态恢复并行读取：
task.yaml + tasks.md + verify.md + retro.md + decisions.md + issues.md + milestones.md
```

任一状态镜像漂移，后续 Agent 就可能选错阶段；任一强制 Gate 可绕过且远端没有替代 Gate，流程就只剩自我声明。

### 2.5 已确认的优点

1. 任务理解确认、先调研后实施，能显著减少跑偏。
2. TDD、Harness oracle、Mock 边界、故意破坏反证，比“只看 pytest 绿”成熟。
3. 对 untrusted input、权限分层、Action SHA、人工 approval 的安全方向正确。
4. `INDEX` 视图、真实 CLI subprocess、退出码断言，是治理 checker 应有的测试方式。
5. 明确区分 workflow 存在与 required check 生效，这是正确原则。

### 2.6 核心缺陷清单

| ID | 等级 | 核心缺陷 | 关键证据 | 直接后果 |
|---|---|---|---|---|
| F-01 | 🔴 P0 | **强制链可绕过，远端无最终裁决** | 审计基线 commit `21414ad` 的 message 明写 `PRE_COMMIT_SKIP=1 · 31 failed`；CI run 失败；唯一 ruleset 为 disabled | 任意文档/代码 Gate 都可成为建议而非约束 |
| F-02 | 🔴 P0 | **供应链 Gate 只验 SHA 形状，不验归属/存在性** | `de8e...` 同时用于 upload-artifact 与 claude-code-action；两个仓库 API 均返回不存在；本地安全检查仍全 PASS | auto-fix workflow 无 job 失败；“安全四关全过”是误报 |
| F-03 | 🟠 P1 | **状态机分裂，且 manifest 无法表达双 Gate 历史** | product-foundation `task.yaml` 仍 `next_task: T2`，tasks 已 T1-T5 ACCEPTED；auth 已完成但 manifest 仍 step 4/in_progress | 恢复会话时无法确定真实阶段 |
| F-04 | 🟠 P1 | **commit hash 回写形成循环依赖** | DOD 要求 commit 前写“实际 commit hash”；hash 只有 commit 后才存在；历史出现多次独立 hash 回写 commit | 一个 task 不再对应一个原子 commit，状态和实现短暂分离 |
| F-05 | 🟠 P1 | **状态语义内部矛盾** | tasks 模板同时说 `[x]` 需 verifier+acceptance、又说仅表示 implementation；pre-commit 错误提示要求写被 checker 禁止的 `✅ DONE` | 遵守一条规则会违反另一条 |
| F-06 | 🟠 P1 | **Verifier 独立性不可证明，L4 一词三义** | L4 在不同文件分别表示 review、E2E、independent verifier；证据只是 Agent ID 文本，writer/verifier共享可写 workspace | PASS 是自我声明，不是独立控制 |
| F-07 | 🟠 P1 | **路径图不闭合且不按风险定级** | `fix-mini` 定义为 0→4→6，但真实任务另写 4→5、L3/L4/L5；步骤 6 又依赖 verify；纯文档审计也强制启动全栈 | Agent 必须临场解释流程，流程本身不能决定下一步 |
| F-08 | 🟠 P1 | **DOD checker 主要验证文本形状，不验证证据语义** | `check_verify()` 只查 L3/L5 段和 PASS 词；Traceability checker 独立存在但未并入 verify；completed tasks 会因只匹配 `[ ]` 而失败 | 容易形式合规，也会误拒合法完成态 |
| F-09 | 🟠 P1 | **决策与状态扇出过大，主账概念冲突** | decisions 是“最权威主账”、issues 又是“唯一主账”，每次决策同步六处；issues 顶部已有 47 行决策镜像 | 写放大、漂移、冲突和绕过动机同步增长 |
| F-10 | 🟠 P1 | **安全模型偏 CI，缺本地 coding Agent 的能力契约** | § 6.10 主要约束 workflow；未定义本地 Agent 的 secret/egress/工具/外部内容来源边界；“用户输入均不可信”又与用户控制指令冲突 | 无法区分授权指令与作为数据的外部文本，易受间接注入或过度授权 |

### 2.7 两个 P0 的完整失效链

#### P0-A · Gate 绕过链

```text
Writer 产生不合规状态
  → PRE_COMMIT_SKIP=1 跳过本地 Gate
  → commit/push 成功
  → GitHub CI 失败
  → ruleset enforcement=disabled
  → 分支仍可继续推进/合并
  → tasks/commit message 可写 PASS/ACCEPTED
```

实证：commit `21414ad` 的 message 同时包含 “verifier PASS + acceptance ACCEPTED” 和 `PRE_COMMIT_SKIP=1 · 31 failed`；对应 CI run `30272696075` 为 failure。

#### P0-B · 供应链假绿链

```text
任意 40 位十六进制字符串
  → check_action_sha.py 只验 regex
  → security_e2e 只验结构
  → “All third-party Actions pinned” + “四关全过”
  → GitHub 解析 Action 时发现 SHA 不属于目标仓库
  → workflow 在 job 前失败
```

GitHub 官方要求不仅固定完整 SHA，还应确认 SHA 来自该 Action 的原仓库；当前 checker 缺少 provenance 校验。参考 [GitHub Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)。

### 2.8 历史任务实证

`2026-07-27-bug-hydration-mismatch` 在治理 Gate commit `f1cf815` 上线约 20 小时后提交：

- 新 task 目录缺 `task.yaml`；
- 当前 `check-governance.py` 重放该 commit 得到 6 类失败；
- tasks 含大量已被状态 checker 禁止的 `✅ DONE`；
- 该 Bug 实现 commit 约 137 行变更，随后文档 commit 约 936 行，再追加 hash 回写 commit。

这不是在否定该 Bug 修复本身，而是说明流程成本、状态原子性和强制链已经脱节。

### 2.9 安全审查

#### 官方安全文档

- [GitHub Actions Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)：最小权限、不可信 checkout、完整 SHA 与来源核验。
- [GitHub Actions Script injections](https://docs.github.com/en/actions/concepts/security/script-injections)：PR 标题、branch、message 等 context 均可能是不可信代码输入。
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)：Prompt Injection、Insecure Output Handling、Supply Chain、Excessive Agency。
- [OWASP Excessive Agency](https://owasp.org/www-project-top-10-for-large-language-model-applications/2_0_vulns/LLM06_ExcessiveAgency.html)：限制工具、权限、自治范围，并对高影响动作保留人工审批。

#### 威胁模型

| 场景 | 攻击者能力 | 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|---|
| T-01 仓库内间接 prompt injection | 可提交 PR/修改 issue、日志或代码注释 | Writer/Verifier 把外部文本当指令 | 越权改代码、泄露信息、绕过测试 | 🔴 | 控制指令与数据通道分离；外部内容只作引用数据；工具 allowlist |
| T-02 本地 Gate 绕过 | 有本地 commit/push 权限 | `PRE_COMMIT_SKIP=1` | 不合规提交进入远端 | 🔴 | 远端 required checks 不可绕过；skip 必须 incident ID + 审计 |
| T-03 伪造供应链 pin | 能编辑 workflow | 填任意 40 位 hex | CI 中断或指向错误依赖 | 🔴 | 在线/缓存 provenance 校验：repo + SHA 必须存在；记录上游 tag/commit |
| T-04 Writer 与 Verifier 合谋/同源偏差 | Writer 可改 spec、测试和验证文档 | 同 workspace、同权限、无不可变输入快照 | 错误实现被自证 PASS | 🟠 | verifier 只读 checkout 固定 commit；spec hash；证据独立落库 |
| T-05 状态镜像投毒 | 可更新其中一个主账 | 修改 tasks/verify/issues 中最有利的一份 | 后续 Agent 选错阶段或错误关闭 | 🟠 | 单一事件账本；其他视图自动生成 |

#### 权限边界图

```text
不可信：PR/issue/log/branch/代码注释
             │ 仅数据，不得升级为控制指令
             v
┌──────────────────────┐      用户批准高影响动作
│ Local Writer Agent   │───────────────┐
│ repo write + tools   │               │
└──────────┬───────────┘               v
           │ commit              ┌───────────────┐
           v                     │ GitHub merge  │
┌──────────────────────┐         │ ruleset       │  当前：disabled
│ Local Hook           │         └───────┬───────┘
│ 可被 env skip 绕过   │                 │
└──────────┬───────────┘                 │
           v                             │
┌──────────────────────┐                 │
│ CI diagnostic        │ read-only/no secrets
└──────────┬───────────┘
           │ sanitized artifact
           v
┌──────────────────────┐
│ CI apply-fix Agent   │ environment approval + secrets + write
└──────────────────────┘

Verifier 应为：固定 commit 的只读 checkout + 独立证据输出；
当前实际为：共享 workspace，权限边界未由仓库契约强制。
```

#### 外部依赖审查

| Action | 当前 ref | 格式 | 来源存在性 |
|---|---|---|---|
| `actions/checkout` | `d234...f803` | 40 位 SHA | ✅ GitHub API 已确认 |
| `actions/setup-python` | `ece7...61a1` | 40 位 SHA | 未在本次逐项复核 |
| `actions/setup-node` | `2499...1a38` | 40 位 SHA | 未在本次逐项复核 |
| `actions/upload-artifact` | `de8e...c1ac` | 40 位 SHA | ❌ 目标仓库无此 commit |
| `actions/download-artifact` | `de8e...c1ac` | 40 位 SHA | 高风险，需逐仓核验 |
| `anthropics/claude-code-action` | `de8e...c1ac` | 40 位 SHA | ❌ 目标仓库无此 commit |

结论：**“完整 SHA”只是必要条件，不是充分条件**。

#### 不可信输入清单

| 输入 | 当前用途 | 需要的策略 |
|---|---|---|
| 用户授权指令 | 控制流程 | 认证后的控制通道；与引用数据明确区分 |
| PR title/body、commit message、branch | CI metadata | 不进入 shell/LLM 指令；结构化字段、长度限制、allowlist |
| CI raw log | Agent 修复上下文 | 只传失败 job、错误类型、允许字符摘要；原文隔离 |
| 仓库代码、注释、README、AGENTS 嵌套引用 | Writer/Verifier 上下文 | 仅根级受信政策可发指令；业务文件按数据处理 |
| 测试输出与模型输出 | Gate 证据 | 解析退出码和结构；输出不得直接执行 |
| artifact / patch.diff | apply-fix 输入 | 来源 run/commit 绑定、hash 校验、路径限制 |

## 3. 重构方案

| 维度 | 方案 A：补丁式止血 | 方案 B：单一状态机控制面 | 方案 C：流程收缩为三 Gate |
|---|---|---|---|
| 思路 | 修 P0、统一冲突文案、补 checker | 以 append-only task events 为真源，生成 task.yaml/tasks/issues 等视图 | intake → build → release/learn，删除大部分阶段文档 |
| 改动范围 | ruleset + 5-8 个治理文件 | 状态 schema、CLI、Hook、CI、模板、迁移器 | AGENTS/DOD/模板/checker 全面重写 |
| 风险 | 🟡 继续保留高同步成本 | 🟡 迁移和工具实现成本 | 🔴 破坏既有习惯与历史兼容 |
| 兼容性 | ✅ 高 | 🟡 新任务原生，历史只读适配 | ❌ 低 |
| 测试影响 | 补 provenance、skip、状态回归 | 状态转移 property tests + 端到端 Gate | 全套治理测试重写 |
| 预估 | 0.5-1.5 天 | 3-5 天，分阶段 | 3-6 天 |
| 能否解决根因 | 只能解决 P0 和显性矛盾 | ✅ 解决状态、证据、Gate、同步根因 | ✅ 解决复杂度，但可能丢失必要严谨度 |

### 3.1 方案 A · 补丁式止血

1. 修复无效 Action SHA，并让 checker 验证 `owner/repo@sha` 的来源存在性。
2. 启用最小 required ruleset，至少 required：governance、backend、frontend、test-quality。
3. 禁止无审计 `PRE_COMMIT_SKIP`；紧急绕过必须含 incident ID，且远端 Gate 不豁免。
4. 统一 `[x]`、DONE、PASS、ACCEPTED 的语义和错误提示。
5. 修正 `fix-mini` 是否包含步骤 5 的路径定义。

优点是能快速恢复底线；缺点是镜像主账和状态分裂仍在。

### 3.2 方案 B · 单一状态机控制面（推荐）

**2026-07-30 状态**：用户已验收步骤 2，原话「按推荐全部拍板，验收步骤 2」；
技术落点为独立受保护 `workflow-state` branch + 每事件一文件 + CAS，五项决策详见
[`plan.md` § 10](plan.md#10-需要用户拍板的决策) 与 [`decisions.md` D-006](decisions.md)。
按 `refactor-6` 双 gate，用户已于 2026-07-30 明确「验收步骤 3，开始实施」；
[`tasks.md`](tasks.md) 的 4 批 20 个原子任务已获验收，当前进入步骤 4，从 T1 开始实施。

建议新增唯一机器真源（名称在步骤 2 决定），记录不可覆盖事件：

```text
task_created
scope_confirmed
step_accepted(step, user, timestamp)
implementation_committed(task, commit)
tests_observed(commit, command, rc, counts)
verifier_observed(commit, spec_hash, result, evidence)
phase_accepted(user, commit)
merge_gate_observed(commit, checks)
```

- `task.yaml`、tasks、issues 顶部状态、milestones 全部由事件投影视图生成，不再人工六处同步。
- commit 前只记录 `implementation: staged/pending`；commit 后由 hook/CI 根据 `HEAD` 自动补事件，不把未知 hash 写入即将生成的 commit。
- verifier 在只读 worktree 上验证固定 commit + 固定 spec hash，不能修改 Writer 的 checkout。
- 路径从“任务名触发词”升级为“风险 × 变更面 × 可逆性”：
  - S0：只读问答/审计，不启动服务、不建完整 task；
  - S1：小 Bug，research-lite + regression + CI；
  - S2：常规功能/重构，完整规格与方案；
  - S3：安全/迁移/高权限，双 verifier + 人工 environment/merge Gate。
- 人工验收只发生在真正需要人判断的 scope、产品/视觉、最终行为，不要求人确认机器事实。

### 3.3 方案 C · 三 Gate 收缩

把现有阶段压成：

1. **Intent Gate**：任务理解、scope、风险等级、验收标准。
2. **Change Gate**：TDD、实现、独立 verifier、CI。
3. **Outcome Gate**：真实路径、用户验收、学习/复盘。

优点是认知成本最低；缺点是需要一次性重写现有治理体系，且复杂产品任务可能重新长出隐式子阶段。

## 4. 风险评估

### 4.1 当前风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 红 CI 仍可合并 | 🔴 | 先启用并验证 required ruleset；不以 workflow 文件存在代替 |
| 无效 Action SHA 造成 CI/auto-fix 失效 | 🔴 | 逐 repo provenance 校验 + 真实 workflow smoke |
| 本地 Agent 读到恶意仓库指令 | 🔴 | 控制面 allowlist + 数据/指令分离 + 最小工具权限 |
| 状态主账互相矛盾 | 🟠 | 单一事件真源，镜像自动生成 |
| verifier 自我证明 | 🟠 | 固定 commit/spec hash、只读环境、独立 evidence |
| 规则复杂度诱发频繁 skip | 🟠 | 风险分级路径 + 记录 skip 原因 + 远端不可绕过底线 |
| 改造影响正在进行的任务 | 🟡 | 新任务使用 v2；旧任务只读，不全量回填 |

### 4.2 改造风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 一次性大改治理导致全员阻塞 | 🟠 | 先 A 止血，再 B 分阶段；每阶段保留回滚开关 |
| 自动投影器成为新单点故障 | 🟠 | 事件文件可读、schema versioned、投影可重建 |
| 风险分级被滥用为降级通道 | 🟠 | S2/S3 由 diff trigger 自动抬升，降级需用户确认 |
| 在线 SHA 校验受网络影响 | 🟡 | CI 在线核验 + 本地缓存；网络失败标 BLOCKED，不伪 PASS |
| 历史 35 个任务兼容成本过高 | 🟡 | 标 `LEGACY_UNVERIFIED`，只迁活跃任务 |

### 4.3 用户决策后的风险缓解更新

- F-01 的缓解从“建议启用”升级为“先行 P0 实施”：远端 required ruleset 必须真实 `active`，且回读结果作为验收证据。
- F-02 的缓解从“建议逐仓核验”升级为“先行 P0 实施”：修复所有无效引用，并让 CI 对 `owner/repo@sha` 做远端存在性核验；网络失败不得误报 PASS。
- 方案 B 在两个 P0 完成前只准备边界，不提前实施状态迁移，避免把失效的 Gate 带入新控制面。
- 2026-07-29 用户授权「那你修复下」后，方案 B 开始进入步骤 1；本步只冻结系统承诺和验收场景，
  存储介质、CLI 和投影实现方案留到步骤 2 比选。
- 2026-07-29 用户验收步骤 1 并要求「出方案」；规格不变量已冻结，步骤 2 只能在该契约内比较
  存储、并发、投影、迁移与 Gate 接入方案，不得借技术选型改写已验收行为。
- 2026-07-30 用户「按推荐全部拍板，验收步骤 2」；风险缓解正式锁定为：
  state branch 禁止 force-push/delete、Actor 独立签名与 trust-config hash、GitHub API
  二次取证、两周期 Shadow、ruleset 未 active 时禁止 Enforce。
- 2026-07-30 用户明确指令「拆任务」；步骤 3 已把高风险边界拆为 Core、Git Store/CLI、
  Trust/Gates、Migration/Shadow 四批，并把独立 verifier、真实 Git/CI、回滚与外部人工 Gate
  写入每个相关原子任务；任务清单验收前仍禁止实施。
- 2026-07-30 用户明确「验收步骤 3，开始实施」；步骤 4 必须逐任务执行 TDD、
  回写 `tasks.md`、独立 verifier 和 commit，不得把未执行的 GitHub 外部 Gate 写成 PASS。

## 5. 输出建议

### 5.1 推荐方案

**推荐：方案 B，但按 A→B 两段实施。**

1. **P0 containment（先做）**：修 Action SHA provenance、启用 required ruleset、关闭无审计绕过。
2. **Control-plane v2（再做）**：单一状态事件源、自动投影、固定 commit 的 verifier、风险分级路径。

理由：

- 只做 A 会很快再次遇到主账漂移和 commit 回填；
- 直接做 C 会丢掉现有流程中真正有价值的调研、TDD 和真实路径验证；
- B 能保留质量原则，同时去掉最危险的“人工多处同步 + 自我签字”。

### 5.2 推荐路径

```text
0 调研（本文件，等待用户验收）
→ P0 containment 单独走 timebox/fix-mini（需用户授权）
→ 1 规格（状态事件、角色权限、风险等级、迁移边界）
→ 2 计划（至少两种 schema/投影实现方案）
→ 3 拆分（P0、state v2、verifier isolation、retirement 四批）
→ 4 实现（治理 CLI TDD + 真实 Git/CI 回归）
→ 5 验证（本地绕过、远端红灯、provenance、恢复会话四条真实路径）
→ 6 复盘（删除被 v2 自动覆盖的重复规则）
```

### 5.3 关键决策点

| 决策点 | 2026-07-28 决策 | 落地 |
|---|---|---|
| 接受“2 个 P0 + 8 个 P1”的判断 | ✅ 接受并验收步骤 0 | 本文件转为 `approved` |
| 是否先处理两个 P0 | ✅ 先修两个 P0，再进入步骤 1 | 新建独立 `timebox` containment 任务 |
| 后续 A / B / C | ✅ 方案 B | 步骤 1 规格定义单一状态机控制面 |
| required ruleset 是否覆盖 admin 且禁止 bypass | ✅ 按 P0 修复目标实施；不设置常规 bypass | 在远端设置后以 API 回读为准 |
| 历史任务迁移范围 | 🟡 留到步骤 1 规格验收 | 先定义兼容边界，不在 P0 阶段迁移 |
| 是否开始修复单一状态与自动投影 | ✅ 开始，但遵守 `refactor-6` 从步骤 1 规格进入 | 用户原话：「那你修复下」 |
| 步骤 1 规格是否验收 | ✅ 已验收，进入步骤 2 | 用户原话：「验收步骤 1，出方案」 |
| 步骤 2 技术方案与五项决策 | ✅ 全部按推荐拍板并验收 | 用户原话：「按推荐全部拍板，验收步骤 2」；详见 decisions D-006 |
| 是否授权步骤 3 拆分 | ✅ 已授权拆分，待验收任务清单 | 用户原话：「拆任务」；详见 decisions D-007 与 tasks.md |
| 步骤 3 是否验收并进入实施 | ✅ 已验收；步骤 4 开始 | 用户原话：「验收步骤 3，开始实施」；详见 decisions D-008 |

### 5.4 关闭条件建议

- [ ] 所有第三方 Action 的 `owner/repo@sha` 均验证存在且来源正确
- [ ] main/feature/codex 的 required ruleset 真实启用，红 CI 无法合并
- [ ] 紧急 skip 有机器可审计记录，且不能绕过远端底线
- [ ] 一个任务只有一个机器状态真源，其他状态均可重建
- [ ] commit 不再需要后续“hash 回写 commit”
- [ ] `[x]` / PASS / ACCEPTED / MERGEABLE 四种事实语义正交
- [ ] verifier 固定 commit + spec hash，使用只读环境
- [ ] L4 只保留一个定义
- [ ] fix-mini 的完整路径无矛盾
- [ ] 至少用一个新功能、一个 Bug、一个重构、一个 P0 验证新流程

## 6. 专项核验：单一状态与自动投影（2026-07-29）

### 6.1 结论

**问题成立，而且当前实现尚未具备“自动投影”的最小闭环。**

现有 `task.yaml` 是一个人工维护的阶段快照；`tasks.md`、`verify.md`、`decisions.md`、
`docs/issues.md` 和 `milestones.md` 仍各自承载状态。`check-task.py`、
`check_task_state.py`、pre-commit 和 governance CI 只校验各文件的局部文本，
没有 append-only 事件源、投影器、重建命令或跨视图一致性检查。

因此“单一状态”目前只是方案目标，不是仓库事实。

### 6.2 当前状态载体与职责冲突

| 载体 | 当前职责 | 写入方式 | 是否可由其他状态重建 |
|---|---|---|---|
| `task.yaml` | mode/current_step/step_state/triggers/test evidence | AI/人手改 | ❌ |
| `tasks.md` | implementation/test/verifier/acceptance + commit 历史 | AI/人手改 | ❌ |
| `verify.md` | L3/L5 与 phase acceptance | AI/人手改 | ❌ |
| `decisions.md` | 决策详细主账与落地状态 | AI/人手改 | ❌ |
| `docs/issues.md` | 长期议题唯一主账 + 决策/状态镜像 | AI/人手改 | ❌ |
| `milestones.md` | 跨任务里程碑流水账 | AI/人手改 | ❌ |
| Git commit / CI checks | 实施、测试与远端 Gate 的事实 | Git/CI 产生 | 仅被人工抄回文档 |

关键冲突：

1. `decisions.md` 被称为“决策最权威详细主账”，`docs/issues.md` 又被称为“唯一主账”；
   这可以解释为不同领域的主账，但机器没有编码该边界。
2. `task.yaml` 自称路径/阶段唯一机器契约，task 级实施状态又明确留在 `tasks.md`；
   后续 Agent 必须自行合并两份状态。
3. § 6.8 要求一次决策人工同步最多六处；这是人工复制协议，不是投影。

### 6.3 仓库实证

2026-07-29 对 11 个含 `task.yaml` 的任务目录扫描：

- **6/11 存在明显状态漂移**：`task.yaml.step_state=in_progress`，但 `tasks.md` 已是
  completed/implemented/implementation complete，或全部 T 项已勾选。
- `2026-07-28-p0-ci-autofix-execution-breaks`：
  - `task.yaml = current_step: 0, step_state: in_progress`
  - `tasks.md = status: completed, 1/1 implementation 完成`
  - `check-task.py` 与 `check_task_state.py` **同时 PASS**。
- 隔离探针：
  - `mode=refactor-6, current_step=1, step_state=accepted`
  - 只有 `task.yaml` + 空 `verify.md`，没有 `spec.md`
  - `test_evidence.path` 指向不存在的 pytest node
  - `check-task.py` 仍 **PASS**，证明它没有校验步骤产物或 evidence path 的存在性。
- 最近 100 个 commit 中有 **16 个**命中 `docs(tasks)` / `回写` / commit evidence
  模式，说明 hash 与状态回填已成为常态，而非偶发。

另有两个结构性限制：

1. `MODE_STEPS["timebox"] = {0}`，所以所有 timebox 任务无论实施到哪里都只能停在 step 0。
2. pre-commit 的 tasks 同步 Gate：
   - 只要求 backend/frontend commit 同时带任意 `tasks.md`；
   - 不证明该 tasks 文件对应本次代码；
   - 注释声称包含 `scripts/`，实现却未把 `scripts/` 纳入触发条件。

### 6.4 为什么“把 task.yaml 当唯一真源”仍不够

若只把 `task.yaml` 升级为更大的可变快照，再从它生成 Markdown，仍有四个根问题：

1. **历史丢失**：快照不能证明状态如何到达、谁验收、失败后是否重跑。
2. **并发覆盖**：多个 Agent 同时更新同一 YAML 时只能最后写入者获胜。
3. **commit 自引用**：包含在 commit 内的文件无法可靠记录该 commit 自己的最终 hash；
   仍需要后续回写。
4. **证据来源不可信**：AI 可以同时修改状态、测试与 PASS 文本，快照无法区分观察者。

所以方案 B 的“单一状态”必须定义为**单一机器事件真源**，不是单一大 YAML。

### 6.5 事件真源的正确边界

单一真源只负责**机器执行状态**，不吞并所有知识：

- 继续人工维护：research/spec/plan 的业务内容、decisions 的理由与用户原话。
- 进入事件真源：
  - task 创建、scope 确认、步骤开始/验收；
  - implementation commit；
  - test observation；
  - verifier observation；
  - phase acceptance；
  - merge Gate observation；
  - issue/milestone 链接状态。

建议最小事件 envelope：

```yaml
schema: task-event/v1
event_id: <uuid>
task_id: <task-id>
seq: 17
type: verifier_observed
occurred_at: 2026-07-29T12:00:00+08:00
actor:
  kind: verifier
  id: <run-id>
subject:
  commit: <40-char-sha>
  spec_hash: <sha256>
payload:
  result: PASS
  evidence_ref: <immutable-ref>
prev_event_hash: <sha256>
```

必须正交保存六种事实，禁止再压成一个模糊 `status`：

```text
workflow_phase
implementation_state
test_state
verifier_state
acceptance_state
merge_gate_state
```

### 6.6 三种落地方式

| 方式 | 优点 | 核心问题 | 结论 |
|---|---|---|---|
| A. 扩大 `task.yaml`，同分支生成 Markdown | 最简单、全在 repo | 无历史；并发覆盖；commit 自引用仍需回填 | 不推荐 |
| B. 同一 feature branch 保存 `events.jsonl` 并提交投影 | 可审阅、可离线 | implementation commit 后仍需状态 commit；多个 Agent 易冲突 | 仅适合原型 |
| C. 独立 `workflow-state` ref/branch 保存事件，视图按需生成 | 实施 commit 原子；CI 可在观察到 SHA 后写事件；可重放 | 需要 CAS/权限/失败恢复 | **推荐进入步骤 1 规格** |

外部数据库/GitHub Checks 也能解决 commit 自引用，但会增加供应商绑定和离线恢复成本；
第一版可把 GitHub Check 作为证据来源，事件真源仍保留在独立 Git ref。

### 6.7 自动投影边界

推荐投影器只拥有状态区域，不覆盖人工正文：

```text
events (唯一机器真源)
  ├─ task snapshot        → task.yaml（generated，禁止手改）
  ├─ task status block    → tasks.md 的 generated marker 区
  ├─ verification view    → verify 状态表 / evidence links
  ├─ issue index          → docs/issues.md 的 generated status 区
  └─ milestone index      → milestones generated 区
```

投影器必须满足：

1. 同一事件集重复运行，输出字节完全一致。
2. 每个投影带 `source_seq` / `source_hash`，可检测手改和陈旧视图。
3. 输出无变化时不写文件，避免无意义 commit。
4. 可删除全部 generated view 后从事件重建。
5. 任何手改 generated 区域由 Gate 拒绝，而不是被静默覆盖。

### 6.8 commit hash 循环的处理

推荐流程：

```text
feature commit 产生真实 SHA
  → CI / post-commit observer 验证 SHA
  → 以 idempotency key 追加 implementation_committed 事件到 workflow-state ref
  → projector 更新读模型
```

这样 feature commit 不包含自己的 hash，也不需要人工再做“hash 回写 commit”。
若状态分支暂时不可用，事件写入必须标 `BLOCKED` 并可重试，不能把未记录状态伪装成 PASS。

### 6.9 步骤 1 规格必须锁定的不变量

1. 事件 append-only；修改/删除历史事件一律失败。
2. `(task_id, seq)` 单调递增，写入使用 compare-and-swap。
3. `event_id` / idempotency key 防止 CI 重试产生重复事实。
4. verifier 的 `subject.commit` 必须等于 implementation commit，`spec_hash` 必须固定。
5. user acceptance 只能来自显式 accept 命令，不能从聊天文本或 `[x]` 自动推断。
6. test/verifier/merge 事实只能由对应观察者写入，Writer 不能自签。
7. 投影可完全重建；projection mismatch 必须 fail closed。
8. 新任务原生使用 v2；活跃旧任务只导入一个
   `legacy_snapshot_imported(LEGACY_UNVERIFIED)`，历史任务保持只读。

### 6.10 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 状态分支成为新单点故障 | 🟠 | 本地事件队列 + CAS 重试 + BLOCKED，不伪 PASS |
| 两个 CI run 并发追加 | 🟠 | sequence CAS、幂等键、冲突后重放 |
| 投影器 Bug 批量改文档 | 🟠 | golden tests、dry-run diff、generated 区域限定 |
| AI 伪造用户验收 | 🔴 | 显式用户命令/受信 actor，聊天只作 evidence ref |
| 迁移时把旧 PASS 当真 | 🔴 | legacy import 一律标 `LEGACY_UNVERIFIED` |
| 状态 ref 写权限过大 | 🔴 | 独立最小权限 job；不 checkout/执行非可信代码 |

### 6.11 专项建议

方案 B 可以继续，但步骤 1 不应写成“新增一个更完整的 task.yaml”。应明确：

1. `events` 是唯一机器真源；
2. `task.yaml/tasks/issues/milestones` 是可丢弃、可重建的读模型；
3. 事件位于独立 state ref，避免 commit 自引用和 feature branch 污染；
4. 用户验收、测试、verifier、mergeability 是不同 actor 产生的正交事实。

本专项只完成调研，不实施事件存储、投影器或迁移。

2026-07-30 用户已验收步骤 3 并明确「开始实施」；当前进入步骤 4，
每个 commit 单元必须完成 TDD、任务回写与独立 verifier，未执行证据不得写成通过。

## 自检清单

- [x] 任务理解已由用户确认
- [x] 路径模式明确为 `refactor-6`
- [x] 已读 `docs/issues.md`
- [x] 已跑 `git log -10`
- [x] 已跑 `git status`
- [x] 已找到至少 3 个相关文件
- [x] 调用方清单 ≥ 3 个
- [x] 当前治理测试与远端执行基线已查
- [x] 依赖影响已列
- [x] 方案对比 ≥ 2 个
- [x] 推荐方案有证据
- [x] 风险均有等级与缓解
- [x] 已读 GitHub Actions 与 OWASP 官方安全文档
- [x] 威胁模型 ≥ 3 个场景
- [x] 权限边界图已写
- [x] 外部依赖与不可信输入已审查
- [x] 完整 0→6 推荐路径已给出
