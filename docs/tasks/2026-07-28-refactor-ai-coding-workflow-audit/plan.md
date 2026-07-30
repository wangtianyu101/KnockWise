---
title: AI Coding 控制面 v2 · 技术实施方案
type: plan
step: 2
date: 2026-07-29
updated: 2026-07-30
status: approved
tags: [plan, refactor, governance, event-source, projection]
related:
  - research.md
  - spec.md
  - decisions.md
  - task.yaml
---

# AI Coding 控制面 v2 · 技术实施方案

> 当前路径：`refactor-6` 步骤 2。
>
> 本文件只做技术选型和实施规划。用户未拍板本步骤前，不创建 `tasks.md`，
> 不修改 checker、Hook、CI 或状态存储实现。

## 0. 上游与适用性

- 调研依据：[`research.md`](research.md)，重点是 F-03/F-04/F-09 与 § 6 专项核验。
- 已验收规格：[`spec.md`](spec.md)，2026-07-29 用户原话：「验收步骤 1，出方案」。
- 决策主账：[`decisions.md`](decisions.md) D-002、D-004、D-005。
- `product-doc.md`：不适用；本任务不改变终端用户产品能力。
- `design-spec.md`：不适用；本任务不涉及 UI/UX。
- `db-design.md`：推荐方案不使用数据库，不触发。
- `api-spec.md`：推荐方案不新增 HTTP API，不触发。
- `component-spec.md`：不涉及前端组件，不触发。
- 运行约束：本地为 Python 3.9.6，CI 为 Python 3.12；控制面实现必须兼容 Python 3.9，
  不使用业务 MySQL，不读取或修改受保护的 seed/env 文件。

### 0.1 官方技术依据

- [Git `update-ref`](https://git-scm.com/docs/git-update-ref)：三参数形式会先核对旧 OID，
  只有 ref 仍等于预期值才更新，满足本地 CAS 前提。
- [Git `push` fast-forward 规则](https://git-scm.com/docs/git-push#_push_rules)：普通 branch push
  默认只允许 fast-forward；并发领先会被拒绝，禁止使用 `--force` 绕过。
- [GitHub Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
  与[可用规则](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)：
  可针对 `workflow-state` branch 限制更新/删除并阻断 force push；最终是否有效必须回读
  `active` 状态，不能只看仓库里存在配置文字。
- [GitHub Actions Secure use](https://docs.github.com/en/actions/reference/security/secure-use)：
  `workflow_run` / `pull_request_target` 的高权限 job 不得 checkout 或执行非可信 PR 代码，
  且上游 workflow artifact 必须继续视为不可信。
- [GitHub Environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)：
  required reviewers、prevent self-review 与 secrets 延迟暴露可作为人工 Gate，但私有仓库
  的可用性受 GitHub 套餐限制；不可用时必须 `BLOCKED`，不能静默降级。
- [OpenSSH `ssh-keygen -Y`](https://man.openbsd.org/ssh-keygen.1)：
  `sign` / `verify` 支持独立 namespace 与 allowed-signers；本机 OpenSSH 10.2 已确认支持。

## 1. 推荐方案

### 推荐方案

- **推荐**：技术方案 B——独立 `workflow-state` Git branch + 不可变事件文件 +
  纯函数 reducer/projector + 受限 `taskctl` CLI。
- **理由**：
  1. 独立 state branch 的 commit 在业务 commit 之后产生，因此事件可以引用真实业务 SHA，
     不再形成“当前 commit 回写自身 hash”的循环。
  2. 事件、projection 和 source hash 可在同一个 state commit 内原子落地；业务分支不再依赖
     `task.yaml/tasks.md/issues.md` 的人工同步状态来做 Gate。
  3. Git 已是仓库现有共享、审计和同步基础设施；相比外部数据库，无新增服务、备份和密钥运维。
  4. `git update-ref` 的 compare-and-swap、本地锁和远端 fast-forward push 可以覆盖并发、
     幂等与重试；状态 ref 可由 GitHub ruleset 禁止 force-push/delete。
  5. 迁移可渐进进行：新任务原生 v2，活跃旧任务导入一个
     `legacy_snapshot_imported` 事件，其余历史任务继续 `LEGACY_UNVERIFIED`。
- **工作量**：约 14～18 AI 小时，分 4 个批次；另需用户配置 state branch ruleset、
  Actor 公钥/受保护环境并完成 L5 验收。
- **风险**：🟡 中等。核心代码可本地完整测试；远端 ref 保护和高权限 Actor 仍是外部 Gate，
  未配置前必须标 `BLOCKED`，不得宣称控制面闭环。

## 2. 方案对比

### 方案 A：业务分支内 `events.jsonl`

- **思路**：每个任务在当前业务分支保存
  `docs/tasks/<task-id>/events.jsonl`，pre-commit 在提交前追加事件并同步生成视图。
- **优点**：
  - 文件布局直观，普通 `git diff` 就能看到事件和视图。
  - 不需要维护额外 Git branch/ref，也不需要跨 ref 读取。
  - 对现有 `task.yaml`、`tasks.md` 和 Hook 改动最少。
- **缺点**：
  - 当前 commit 的 SHA 在 commit 前不存在，仍需后置补写或额外状态 commit。
  - 多 Agent 同时追加同一个 JSONL 文件时容易产生冲突。
  - 业务 patch、状态写入和 generated view 继续混在一个分支。
  - 绕过本地 Hook 后，事件链和业务提交可以再次分裂。
- **风险等级**：🔴 高；无法根治 F-04 的 commit 自引用。
- **工作量**：8～11 AI 小时。
- **兼容性**：✅ 文件级兼容最好，但语义根因未消除。
- **测试影响**：需补 JSONL append、并发冲突、Hook 和 commit 回填回归；现有
  `check-task.py` 仍需保留为主要 Gate。

### 方案 B：独立 Git state branch（推荐）

- **思路**：创建受保护的 orphan branch `workflow-state`。每个状态事件是独立不可变 JSON 文件；
  reducer 从有序事件计算 projection，事件和 projection 在同一个 state commit 中提交。
  正常业务分支通过 `taskctl` 查询或按需 materialize 只读视图。
- **优点**：
  - 业务 commit 与状态 commit 分离，后者可以安全引用前者的真实 SHA。
  - state commit 的父链天然提供 append-only 审计；禁止 force-push 后不能静默重写历史。
  - 不依赖常驻数据库或服务，离线也可读写本地 state ref。
  - 本地 CAS + 远端 fast-forward reject 能明确检测并发。
  - generated projection 与事件原子提交，不再出现“事件已写、视图未更新”的半状态。
  - 可用 Git 原生命令重放、备份和灾难恢复。
- **缺点**：
  - Agent 和用户必须通过 `taskctl` 读取状态，不能只看业务分支中的旧 `task.yaml`。
  - 多 worktree/多 Agent 并发写 ref 需要本地锁、CAS 和有界重试。
  - GitHub CI 默认 checkout 不一定带 state branch，需要显式只读 fetch。
  - Actor 真身份不能靠 JSON 字段自报，必须增加签名 receipt 或受保护 workflow。
- **风险等级**：🟡 中；实现复杂度可控，远端权限配置是关键外部依赖。
- **工作量**：14～18 AI 小时。
- **兼容性**：⚠️ 新任务原生、活跃任务迁移、历史任务只读。
- **测试影响**：新增 event/reducer/projector、真实临时 Git 仓、CAS 冲突、签名 receipt、
  Hook/CI 端到端和迁移回归；逐步替代 `check-task.py` / `check_task_state.py`。

### 方案 C：外部 SQLite/PostgreSQL 状态服务

- **思路**：建立事务数据库和受认证 API，所有 Agent/CI 通过服务追加事件、查询 projection。
- **优点**：
  - 事务、唯一约束、并发控制和查询能力最强。
  - Actor 认证、权限与审计可由服务统一处理。
  - 不受 Git branch 合并、fetch 和 ref 同步影响。
- **缺点**：
  - SQLite 不能可靠承担多机器共享；PostgreSQL/API 又引入服务部署、密钥、备份和可用性。
  - 本地离线开发会依赖额外基础设施，服务不可用时所有任务必须 fail closed。
  - 需要额外 `db-design.md`、`api-spec.md`、迁移和运维方案，超出当前仓库治理脚本的合理规模。
  - 状态服务自身变成新的单点故障和高权限攻击面。
- **风险等级**：🔴 高；技术上强，但对当前单仓 AI coding 流程明显过重。
- **工作量**：28～40 AI 小时，外加部署与长期运维。
- **兼容性**：⚠️ 需要双写迁移期和服务可用性兜底。
- **测试影响**：除控制面测试外，还需 DB migration、API auth、故障注入、备份恢复和网络分区测试。

### 2.1 对比结论

| 维度 | 方案 A | 方案 B | 方案 C |
|---|---:|---:|---:|
| 根治 commit hash 自引用 | ❌ | ✅ | ✅ |
| append-only 审计 | 🟡 文件约定 | ✅ Git 历史 + hash chain | ✅ 事务日志 |
| 并发控制 | 🟡 合并冲突 | ✅ CAS + fast-forward | ✅ 数据库事务 |
| 离线可用 | ✅ | ✅ | ❌/🟡 |
| 新增运维 | 低 | 低～中 | 高 |
| Actor 强身份 | ❌ | 🟡 签名/受保护 workflow | ✅ 服务认证 |
| 渐进迁移 | 🟡 | ✅ | 🟡 |
| 综合判断 | 不解决根因 | **推荐** | 当前过度设计 |

## 3. 方案 B 目标架构

```text
业务分支 / 固定 commit
  code + tests + research/spec/plan/tasks 的人工正文
                │
                │ 只通过受限 adapter 观察真实事实
                v
┌──────────────────────────────────────────┐
│ scripts/taskctl.py                       │
│ create/start · observe-commit · run-test │
│ import-verifier · accept · observe-ci    │
└──────────────┬───────────────────────────┘
               │ schema + actor + evidence 校验
               v
┌──────────────── workflow-state branch ─────────────────┐
│ tasks/<id>/events/<seq>-<event-id>.json                │
│ tasks/<id>/events/<seq>-<event-id>.sig                 │
│ tasks/<id>/projection/task.json                        │
│ tasks/<id>/projection/task.yaml                        │
│ tasks/<id>/projection/tasks-status.md                  │
│ views/issues-status.md                                 │
│ views/milestones-status.md                             │
└──────────────┬──────────────────────────────────────────┘
               │ pure reducer + deterministic projector
               v
    taskctl show / taskctl project / CI check / job summary

业务分支里的旧状态字段只作为 legacy facade；
v2 Gate 一律从 state ref + source hash 读取，不从镜像文件反推事实。
```

### 3.1 State branch 结构

```text
workflow-state
├── FORMAT
├── tasks/
│   └── <task-id>/
│       ├── events/
│       │   ├── 000001-<event-id>.json
│       │   ├── 000001-<event-id>.sig
│       │   └── ...
│       └── projection/
│           ├── task.json
│           ├── task.yaml
│           ├── tasks-status.md
│           └── verify-status.md
└── views/
    ├── issues-status.md
    └── milestones-status.md
```

- 每个事件一个文件，不使用共享 JSONL，降低冲突面并让不可变性可逐文件验证。
- 文件名 sequence 必须与内容一致；事件 canonical JSON 使用 UTF-8、排序 key、固定分隔符。
- `event_hash = sha256(canonical_json)`；下一事件的 `previous_event_hash` 必须匹配。
- projection 携带 `source_sequence` 与 `source_hash`，必须与事件链末端一致。
- event + 所有受影响 projection 在一个 state commit 内提交；禁止只提交一半。
- state branch 只允许 fast-forward；禁止 force-push、delete 和人工直接编辑 projection。

### 3.2 原子追加与并发

1. 读取本地 `refs/heads/workflow-state` 的 `old_sha`。
2. 取得 `.git/taskctl.lock` 的进程锁；无法加锁则返回 `BLOCKED`。
3. 在 `mktemp` 临时 worktree 中校验完整事件链、schema 和当前 projection。
4. adapter 采集真实证据，生成带 `expected_sequence` / `previous_event_hash` 的事件。
5. reducer 重放并生成全部受影响 projection。
6. 创建 state commit，并用 `git update-ref <ref> <new_sha> <old_sha>` 做本地 CAS。
7. push 只允许普通 fast-forward；远端领先时 fetch、重新校验并最多重试 3 次。
8. 3 次仍冲突则返回 `BLOCKED`，不覆盖、不 force push、不静默丢事件。

state commit SHA 不写回事件；事件只引用业务 commit SHA，因此不存在自引用。

## 4. 模块与 CLI 契约

### 4.1 代码布局

| 文件 | 职责 |
|---|---|
| `scripts/taskctl.py` | 稳定 CLI、退出码和用户提示 |
| `scripts/workflow_state/models.py` | TaskEvent/Projection schema 与枚举 |
| `scripts/workflow_state/canonical.py` | canonical JSON、hash chain、时间格式 |
| `scripts/workflow_state/reducer.py` | ordered events → TaskProjection 纯函数 |
| `scripts/workflow_state/projector.py` | JSON/YAML/Markdown 只读视图 |
| `scripts/workflow_state/git_store.py` | 临时 worktree、锁、CAS、fetch/push |
| `scripts/workflow_state/actors.py` | actor-event allowlist 与 adapter 路由 |
| `scripts/workflow_state/receipts.py` | 签名 receipt 校验与证据 digest |
| `scripts/workflow_state/migrate.py` | legacy snapshot 导入 |

控制面保持 Python 3.9 兼容。事件 canonical JSON、hash、reducer、Git 调用和锁只用标准库。
现有 checker 已直接 `import yaml`，本机/venv 实测为 PyYAML 6.0.3，但
`backend/requirements.txt` 没有直接 pin；若 compatibility `task.yaml` 继续使用 PyYAML，
实施任务必须先把 6.0.3 设为直接锁定依赖，并加 deterministic dump/round-trip 测试。
不新增 Pydantic/Hypothesis，避免无必要扩大供应链。

### 4.2 CLI

```text
taskctl init --task <id> --mode <mode>
taskctl start --task <id> --step <0..6>
taskctl observe-commit --task <id> --commit <40hex>
taskctl run-test --task <id> --commit <40hex> -- <argv...>
taskctl import-verifier --task <id> --receipt <json> --signature <sig>
taskctl accept --task <id> --receipt <json> --signature <sig>
taskctl observe-ci --task <id> --run-id <id>
taskctl show --task <id> [--format json|yaml|markdown]
taskctl project --task <id>|--all [--materialize]
taskctl check --task <id>|--all
taskctl migrate --task <id> --from-legacy
```

约束：

- 不提供生产可用的 `append --actor --result` 自由入口；调用方不能自报 Actor 或 PASS。
- `observe-commit` 必须用 `git cat-file -e <sha>^{commit}` 验证 commit 存在。
- `run-test` 接收 argv 数组并直接执行，不通过 shell 拼接；记录 command、rc、counts、stdout/stderr
  digest 和受限摘要，不能接受手写 `PASS`。
- `import-verifier` 必须校验固定 commit、spec hash、verifier identity 和 detached signature。
- `accept` 只接受配置在 allowed-signers 中的 user identity；Writer 的 key 无权限签
  `step_accepted/phase_accepted`。
- `observe-ci` 通过 GitHub API 回读 run 的 repository、head SHA、workflow、conclusion，
  网络失败返回 `BLOCKED`。

建议退出码：

| rc | 含义 |
|---:|---|
| 0 | 成功或同 idempotency key 的同内容重放 |
| 1 | 事件/schema/状态转移非法 |
| 2 | state ref、证据或网络不可用，`BLOCKED` |
| 3 | CLI 使用错误 |
| 4 | CAS/远端并发冲突超过重试上限 |

### 4.3 Actor 信任

采用“受限 adapter + 签名 receipt”，不信任事件 JSON 内自报的 `actor.kind`。

| Actor | 可信来源 | 可写事件 |
|---|---|---|
| writer | `taskctl init/start`，仓库本地身份 | task_created、step_started |
| git_observer | CLI 实际解析 Git object | implementation_committed |
| test_runner | CLI 实际执行 argv 并观察 rc | tests_observed |
| verifier | 独立 verifier key 的签名 receipt | verifier_observed |
| user | 用户 key 的签名 receipt或受保护 workflow identity | step_accepted、phase_accepted |
| ci_gate | GitHub API receipt + 受保护 state writer | merge_gate_observed |
| migration | 显式 migration command | legacy_snapshot_imported |

`allowed_signers` 只提交公钥与 identity 映射；私钥不进入仓库。信任配置必须锚定在
受保护 default branch 的固定 commit，并把 `trust_config_hash` 写入 receipt/event；
不得从 Writer 可写的 state branch 自举信任。用户/verifier/CI key 必须隔离，
否则 Actor 矩阵只会退化成新的自我声明。

## 5. Projection 与旧文档边界

### 5.1 权威读路径

- 新 v2 任务：Gate、Agent 恢复和 CI 只读 `workflow-state` projection。
- `task.yaml v2` 是 state branch 内的全文件 projection，不再人工维护。
- `tasks.md`、`verify.md`、`issues.md`、`milestones.md` 的人工正文继续在业务分支；
  状态区域由 projector 生成。
- `taskctl project --materialize` 可把 generated 区域写入工作树供人阅读，但这些镜像不参与判定。
- 默认发布目标是 state branch projection 与 CI job summary，不要求为了 commit SHA 再做业务分支
  “hash 回写 commit”。

### 5.2 Generated marker

```markdown
<!-- workflow-state:begin task=<id> source_sequence=<n> source_hash=sha256:<hash> -->
<generated content>
<!-- workflow-state:end -->
```

- projector 只能替换 marker 内区域。
- marker 外的业务正文和决策理由禁止自动改写。
- `taskctl check` 发现 marker 内人工编辑时报告 drift，但从事件重建即可恢复。
- 在 shadow 期继续生成旧视图作对比；enforce 后 checker 不从旧视图读取事实。

## 6. Hook、CI 与权限分层

### 6.1 本地

- `scripts/install-hooks.sh` 增加 version-controlled `post-commit` observer，但它只是快速反馈，
  不能作为最终强制 Gate。
- `pre-commit` 保留代码测试与文档 DOD；增加 `taskctl check`，逐步删除人工 `tasks.md` 同步要求。
- `post-commit` 只观察已经存在的 commit，追加 `implementation_committed`；失败必须显式
  `BLOCKED` 并提示恢复命令，不能修改刚产生的业务 commit。
- `PRE_COMMIT_SKIP` 不能产生任何 PASS 事件；远端 required check 仍是最终底线。

### 6.2 GitHub

```text
PR/feature code
  └─ CI diagnostic: contents:read，只读 fetch state ref，执行 check/tests
       └─ untrusted hint: repo + workflow + run_id + head_sha + conclusion + digest

protected environment approval
  └─ state writer: contents:write
       ├─ 只 checkout trusted main 上的 taskctl + workflow-state
       ├─ 不 checkout、不执行 PR head
       └─ 用 GitHub API 二次回读 run 元数据后 fast-forward 更新 workflow-state
```

- 高权限 state writer 与非可信代码严格分 job。
- diagnostic 产物/receipt 仅是 untrusted hint；state writer 必须用 `run_id` 回读 GitHub API，
  并核对 repository、trusted workflow path/ref、head SHA、conclusion、artifact digest。
- state writer 使用 GitHub Environment approval，并启用 prevent self-review；环境未配置、
  required reviewers 不可用或保护规则未回读生效时，L5 为 `BLOCKED`。
- 第三方 Action 必须固定真实完整 SHA 并过 provenance checker。
- `workflow-state` ruleset 至少禁止 force push/delete；写入身份优先使用独立 GitHub App
  或等价的最小权限凭据。若无法可靠限制 writer 身份，Shadow 可继续、Enforce 必须阻断。
- 用户已明确远端配置由自己操作；Codex 只提供文件和验收清单，不擅自修改 GitHub 设置。

## 7. 迁移与回滚

### 7.1 三层迁移

1. **新任务**：cutover 后直接 `task-event/v1`，`legacy_trust=NATIVE`。
2. **活跃旧任务**：读取当前 docs，生成一个 `legacy_snapshot_imported` 事件；
   所有导入事实标 `LEGACY_UNVERIFIED`，之后的新事件可为 native。
3. **历史/归档任务**：不批量伪造事件；保持只读，查询时显示 `LEGACY_UNVERIFIED`。

首批只迁移本控制面任务和 1 个代表性的活跃任务。通过两个完整真实任务周期后再扩大。

### 7.2 Shadow → Enforce

| 阶段 | 行为 | 退出条件 |
|---|---|---|
| Shadow 1 | 旧 checker 决策，v2 只计算并报告差异 | event/reducer/projector 测试全绿 |
| Shadow 2 | v2 与旧状态并行两个真实任务周期 | 无未解释漂移；恢复/并发演练通过 |
| Enforce | CI Gate 只认 v2 state；旧状态为只读镜像 | 用户验收 + state ref ruleset 生效 |
| Retire | 按 AGENTS § 6.11 标记旧规则退役 | 保留一个季度后归档 |

### 7.3 回滚

- Enforce 前可关闭 v2 Gate，旧 checker 仍在，不丢任务正文。
- Enforce 后若 projector 故障，固定到上一个已验证 taskctl 版本并从事件重建 projection。
- 事件永不删除；错误事实通过补偿事件处理，不改历史。
- state ref 损坏时从远端保护分支或 bundle 备份恢复；无法验证 hash chain 时 fail closed。
- 禁止通过 force-push “回滚” state branch。

## 8. 测试策略

### 8.1 测试层

| 层 | 覆盖 | 主要文件 |
|---|---|---|
| L1 | schema、actor allowlist、hash chain、reducer 不变量、projector deterministic | `backend/tests/test_workflow_state_*.py` |
| L2 | 临时 Git 仓中的 append、CAS、retry、idempotency、重建、迁移 | `backend/tests/test_taskctl_integration.py` |
| L3 | 真实 `taskctl` subprocess + pre/post-commit + governance checker | `backend/tests/test_workflow_state_gate.py` |
| L4 | 独立 verifier 固定 commit/spec hash 审阅 | verifier receipt |
| L5 | state ref ruleset、CI read/write 分权、失败阻止合并 | `verify.md` + GitHub run |

### 8.2 对 spec TC 的覆盖

- TC-001～004：事件重放、不可变、正交状态、verifier FAIL。
- TC-005～011：Actor 越权、commit/test/verifier/user receipt 真实性。
- TC-012～017：deterministic、drift、幂等、CAS、fail-closed、未知 schema。
- TC-018～020：新任务、legacy import、actor 权限矩阵。
- 不引入 Hypothesis；使用固定 seed 的事件序列生成器覆盖顺序组合，保证 Python 3.9/3.12 一致。
- 所有 shell/管道路径用真实 `/bin/sh` subprocess 断言 rc，不能只 mock。
- 对 reducer 做 mutation-style 反证：故意移除 stale/reset/CAS 检查，相关测试必须失败。

## 9. 风险评估

| 风险 | 等级 | 缓解措施 |
|---|---|---|
| state branch 未保护，事件历史可被重写 | 🔴 | 用户配置 ruleset；未回读 active 前 L5=`BLOCKED`，禁止宣称完成 |
| Writer 获得 user/verifier 私钥，Actor 权限退化 | 🔴 | 私钥不入仓；独立 key/环境；receipt 验签；无签名不得 ACCEPTED/PASS |
| 高权限 workflow checkout 非可信 PR 代码 | 🔴 | diagnostic/action 分 job；writer 只运行 trusted main + state ref；environment approval |
| 本地与远端 state ref 并发 | 🟡 | Python `fcntl.flock`（macOS/Linux）+ `git update-ref old_sha` CAS + fast-forward push + 最多 3 次重试 |
| projector bug 批量生成错误视图 | 🟡 | pure reducer、golden tests、source hash、shadow 两周期、可全量重建 |
| legacy import 把旧自述当成可信事实 | 🟡 | 单一 snapshot 事件统一 `LEGACY_UNVERIFIED`；不得升级为 native PASS |
| state ref/网络不可用阻塞开发 | 🟡 | 本地 ref 可继续记录；远端 Gate 标 BLOCKED；不把缺证据转成 PASS |
| GitHub 套餐不支持所需 Environment protection | 🟡 | 步骤 4 先回读能力；缺 required reviewers/prevent self-review 时保持 Shadow 或改用独立审批系统，禁止 Enforce |
| 规则迁移期间双轨成本上升 | 🟡 | 明确两周期 timebox；满足退出条件立即按 § 6.11 标旧规则退役 |
| generated marker 误伤人工正文 | 🟢 | marker 精确替换、工作树 diff 检查、正文区域 golden test |

## 10. 需要用户拍板的决策

### 决策 1：事件存储与并发模型

- **推荐选择**：技术方案 B，独立 `workflow-state` branch + 每事件一文件 + CAS。
- 替代方案：A 同分支 JSONL；C 外部状态服务。
- **2026-07-30 用户决策**：✅ 按推荐拍板。

### 决策 2：Actor 信任根

- **推荐选择**：受限 adapter + SSH detached signature/allowed-signers；
  GitHub 高权限写入必须经过 protected environment。
- 替代方案：
  - 只靠 CLI 参数自报 Actor：成本低但不满足 spec，拒绝推荐。
  - 全部交给外部状态服务认证：强但会转为方案 C。
- **2026-07-30 用户决策**：✅ 用户/verifier/CI 私钥由独立环境持有，仓库只存公钥；
  trust config 锚定受保护 default branch。

### 决策 3：视图发布位置

- **推荐选择**：state branch projection 是持久只读 cache；业务分支只按需 materialize
  generated marker，不再要求 hash 回写 commit。
- 替代方案：每次自动向业务分支提交生成视图；会重新引入提交噪声和同步 commit。
- **2026-07-30 用户决策**：✅ Gate 只读 state ref，不读业务分支镜像。

### 决策 4：迁移范围

- **推荐选择**：新任务原生 + 活跃任务逐个 snapshot import + 历史任务只读。
- 替代方案：全量历史回填；成本高且会把旧自述伪装成可信事件。
- **2026-07-30 用户决策**：✅ 首批只迁本任务和 1 个活跃代表任务。

### 决策 5：上线节奏

- **推荐选择**：Shadow 两个真实任务周期 → Enforce → Retire。
- 替代方案：一次性切换；回滚和误判风险更高。
- **2026-07-30 用户决策**：✅ state ruleset 未 active 时不进入 Enforce。

> **步骤 2 验收**：✅ 用户于 2026-07-30 按推荐拍板全部五项并验收。
> 用户原话：「按推荐全部拍板，验收步骤 2」。

## 11. 步骤 3 的任务拆分建议

> 以下只用于估算；未收到步骤 2 验收前不创建 `tasks.md`。正式拆分时每项仍须
> ≤ 1 小时、一个 commit、至少一个测试。

| 批次 | 建议任务 | 估时 |
|---|---|---:|
| P1 Core | schema/canonical hash、reducer、projector、20 TC 基础测试 | 4～5h |
| P2 Git Store | state branch bootstrap、临时 worktree、锁、CAS、重试、CLI | 4～5h |
| P3 Trust/Gates | Actor adapters、receipt 验签、Hook、CI 读写分层 | 4～5h |
| P4 Migration | legacy import、shadow 对账、文档模板/规则退役准备 | 2～3h |
| 合计 | 预计 16～22 个原子任务 | 14～18h |

建议依赖：

```text
schema/canonical → reducer → projector
        │             │          │
        └─────────────┴──→ git store/CAS → taskctl
                                      ├→ actor receipts
                                      ├→ hooks/CI
                                      └→ migration/shadow
```

## 12. 实施路径与 Gate

```text
0 调研 ✅
→ P0 containment ✅/外部 ruleset 由用户管理
→ 1 规格 ✅ 2026-07-29 用户验收
→ 2 计划 ✅ 2026-07-30 用户验收
→ 3 拆分 ✅ 2026-07-30 用户验收
→ 4 实现 🚧 已获授权（TDD + 每 commit 独立 verifier）
→ 5 验证（L3 本地整合 + L5 state ref/ruleset/CI）
→ 6 复盘（规则退役与偏差）
```

## 13. 步骤 2 DOD

- [x] 提供三个真实可选方案。
- [x] 每个方案含优缺点、兼容性、工作量和测试影响。
- [x] 单一推荐为技术方案 B，并引用 research/spec 证据。
- [x] 风险带等级和具体缓解措施。
- [x] 五个用户决策点已列出。
- [x] `research.md`、`spec.md` 引用齐全。
- [x] `product-doc.md`、`design-spec.md` 及条件技术文档适用性已说明。
- [x] 给出工作量、批次和步骤 3 拆分建议。
- [x] 用户于 2026-07-30 拍板技术方案和五个决策点。
- [x] 用户于 2026-07-30 验收步骤 2。

> 当前 Gate：**ACCEPTED**。步骤 2、步骤 3 均已完成；用户于 2026-07-30
> 明确「验收步骤 3，开始实施」，当前进入步骤 4。
