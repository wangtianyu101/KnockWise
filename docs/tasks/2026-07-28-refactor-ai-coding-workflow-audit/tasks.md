---
title: AI Coding 控制面 v2 · 实施任务拆分
type: tasks
step: 3
date: 2026-07-30
status: in_progress
layer: L0
tags: [tasks, refactor, governance, event-source, projection]
related:
  - research.md
  - spec.md
  - plan.md
  - decisions.md
  - task.yaml
phase_acceptance: PENDING
---

# AI Coding 控制面 v2 · 实施任务拆分

> 路径模式：`refactor-6`。
>
> 上游方案：[`plan.md`](plan.md) 已于 2026-07-30 验收；权威决策为
> [`decisions.md` D-006～D-008](decisions.md)。步骤 3 授权原话：「拆任务」；
> 步骤 3 验收及步骤 4 授权原话：「验收步骤 3，开始实施」。
>
> 步骤 3 已于 2026-07-30 验收；步骤 4 从 T1 开始，严格按本文件的 commit 边界实施。

## 0. 拆分约束

- 每个任务预计 45～60 分钟，不超过 1 小时。
- 每个任务对应 1 个独立 commit，生产代码与该任务测试同 commit。
- 每个任务先红灯、再绿灯、最后 refactor；测试必须有行为 oracle。
- 每个 commit 完成后先回写本文件，再启动独立 verifier。
- 任何高权限 CI job 不 checkout/执行 PR head；上游 artifact 一律视为不可信。
- `workflow-state` ruleset、Environment reviewers 和 writer credential 由用户配置，
  AI 只提供代码、检查器和可复现验收清单。
- 本任务是 L0 治理基础设施，不涉及产品埋点，§ 9 按规则豁免。

## 1. 任务清单

### P1 · Core

### T1: ✅ 已实现 · 定义事件与投影模型

- [x] T1: 实现 TaskEvent/TaskProjection 枚举、字段校验和 schema version Gate
  - **文件**: `scripts/workflow_state/__init__.py`, `scripts/workflow_state/models.py`
  - **测试**: `backend/tests/test_workflow_state_models.py`
  - **Spec**: REQ-001/REQ-002/REQ-010；SCN-017；TC-017
  - **依赖**: —
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T1 add event and projection models`
  - **实际**: 18 min；RED=模块不存在、pytest collection error；GREEN=30/30 passed；
    test-quality 0 violations；commit `fa1a0fc`；独立 verifier PASS（偏差 0）

### T2: ✅ 已实现 · canonical JSON 与 hash chain

- [x] T2: 实现稳定序列化、event hash、previous hash 校验和历史不可变检测
  - **文件**: `scripts/workflow_state/canonical.py`
  - **测试**: `backend/tests/test_workflow_state_canonical.py`
  - **Spec**: REQ-001；SCN-002；TC-002
  - **依赖**: T1
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T2 add canonical hash chain`
  - **实际**: 20 min；RED=canonical 模块不存在，并补抓空历史首次创建缺陷；
    GREEN=14/14 target、44/44 Core passed；test-quality 0 violations；
    commit `dca321e`；独立 verifier PASS（5/5 行为探针，偏差 0）

### T3: 实现状态 reducer 与失效语义

- [ ] T3: 实现 ordered events → projection，并处理 commit/spec 变化后的 STALE/NOT_RUN
  - **文件**: `scripts/workflow_state/reducer.py`
  - **测试**: `backend/tests/test_workflow_state_reducer.py`
  - **Spec**: REQ-002/REQ-006；SCN-003/009/010；TC-003/009/010
  - **依赖**: T1, T2
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T3 add deterministic reducer`

### T4: ✅ 已实现 · Actor 权限矩阵

- [x] T4: 将 event type → allowed actor 编码为 fail-closed policy，拒绝跨 Actor 自签
  - **文件**: `scripts/workflow_state/actors.py`
  - **测试**: `backend/tests/test_workflow_state_actors.py`
  - **Spec**: REQ-003；SCN-004/005；TC-004/005/020
  - **依赖**: T1
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T4 enforce actor policy`
  - **实际**: 15 min；RED=actors 模块不存在；GREEN=79/79 target、
    123/123 Core passed；70 个权限矩阵单元全覆盖；test-quality 0 violations；
    Python 3.9 语法解析通过；commit `2b282b4`；独立安全 verifier
    PASS（8/8 对抗探针，偏差 0）

### T5: 实现决定性 projector 与 drift 检测

- [ ] T5: 生成 task JSON/YAML/Markdown projection，支持零 diff 重放与 source-hash mismatch
  - **文件**: `scripts/workflow_state/projector.py`
  - **测试**: `backend/tests/test_workflow_state_projector.py`
  - **Spec**: REQ-001/REQ-008；SCN-001/012/013；TC-001/012/013
  - **依赖**: T3, T4
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T5 add deterministic projector`

### P2 · Git Store 与 CLI

### T6: 建立 workflow-state branch store

- [ ] T6: 实现 orphan branch bootstrap、只读加载、临时 worktree 和 FORMAT 校验
  - **文件**: `scripts/workflow_state/git_store.py`
  - **测试**: `backend/tests/test_workflow_state_git_store.py`
  - **Spec**: REQ-001/REQ-010；SCN-001/016；TC-001/016
  - **依赖**: T2
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T6 bootstrap git state store`

### T7: 实现本地原子追加与 CAS

- [ ] T7: 使用 `fcntl.flock`、临时 worktree 和 `git update-ref old_oid` 原子提交事件+投影
  - **文件**: `scripts/workflow_state/git_store.py`
  - **测试**: `backend/tests/test_workflow_state_git_store_cas.py`
  - **Spec**: REQ-001/REQ-009；SCN-002/015；TC-002/015
  - **依赖**: T5, T6
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T7 add atomic CAS append`

### T8: 实现幂等与远端并发重试

- [ ] T8: 拒绝重复逻辑事件，处理 fast-forward reject，最多三次重放后返回 BLOCKED
  - **文件**: `scripts/workflow_state/git_store.py`
  - **测试**: `backend/tests/test_workflow_state_concurrency.py`
  - **Spec**: REQ-009/REQ-010；SCN-014/015/016；TC-014/015/016
  - **依赖**: T7
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T8 add idempotent retry`

### T9: 建立 taskctl 基础命令

- [ ] T9: 实现 init/start/show/project/check 的参数、退出码与纯读/写边界
  - **文件**: `scripts/taskctl.py`, `scripts/workflow_state/cli.py`
  - **测试**: `backend/tests/test_taskctl_cli.py`
  - **Spec**: REQ-001/REQ-002/REQ-008/REQ-010；SCN-001/003/017；TC-001/003/017
  - **依赖**: T3, T5, T6
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(taskctl): T9 add core commands`

### T10: 建立 commit 与 test 观察器

- [ ] T10: 实现 observe-commit/run-test，验证 Git object，直接执行 argv 并记录 rc/counts/digest
  - **文件**: `scripts/workflow_state/observers.py`, `scripts/taskctl.py`
  - **测试**: `backend/tests/test_taskctl_observers.py`
  - **Spec**: REQ-004/REQ-005；SCN-006/007/008；TC-006/007/008
  - **依赖**: T7, T9
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(taskctl): T10 observe commits and tests`

### P3 · Trust 与 Gates

### T11: 实现 trust config 与 SSH receipt 验签

- [ ] T11: 加载 default-branch trust config，校验 config hash、namespace、principal 和 detached signature
  - **文件**: `scripts/workflow_state/receipts.py`, `config/workflow-state/allowed_signers`
  - **测试**: `backend/tests/test_workflow_state_receipts.py`
  - **Spec**: REQ-003/REQ-007；SCN-004/005/011；TC-004/005/011/020
  - **依赖**: T1, T4
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T11 verify signed receipts`

### T12: 实现 verifier 与用户验收 adapter

- [ ] T12: 实现 import-verifier/accept，绑定 active commit/spec hash 并拒绝 Writer 身份
  - **文件**: `scripts/workflow_state/receipts.py`, `scripts/taskctl.py`
  - **测试**: `backend/tests/test_taskctl_trusted_events.py`
  - **Spec**: REQ-003/REQ-006/REQ-007；SCN-004/005/009/010/011；TC-004/005/009/010/011
  - **依赖**: T3, T9, T11
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(taskctl): T12 import trusted acceptance`

### T13: 实现 GitHub run 二次取证

- [ ] T13: 用 GitHub API 回读 repo/workflow/ref/head SHA/conclusion/digest，拒绝仅凭 artifact hint 写状态
  - **文件**: `scripts/workflow_state/github_observer.py`, `scripts/taskctl.py`
  - **测试**: `backend/tests/test_workflow_state_github_observer.py`
  - **Spec**: REQ-003/REQ-010；SCN-005/016；TC-005/016/020
  - **依赖**: T9, T11
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T13 verify github run evidence`

### T14: 接入本地 Hook

- [ ] T14: version-controlled post-commit 观察真实 HEAD，pre-commit 增加 taskctl check 且失败显式 BLOCKED
  - **文件**: `scripts/post-commit`, `scripts/install-hooks.sh`, `scripts/pre-commit`
  - **测试**: `backend/tests/test_workflow_state_hooks.py`
  - **Spec**: REQ-004/REQ-009/REQ-010；SCN-006/007/016；TC-006/007/016
  - **依赖**: T8, T10, T12
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(hooks): T14 observe workflow state`

### T15: 接入 CI 权限分层与远端能力检查

- [ ] T15: 拆 read-only diagnostic/state-writer jobs，禁止非可信 checkout，并回读 Environment/ruleset 能力
  - **文件**: `.github/workflows/workflow-state.yml`, `scripts/ci/check_workflow_state_security.py`
  - **测试**: `backend/tests/test_workflow_state_ci.py`, `scripts/ci/test_workflow_state_security_e2e.sh`
  - **Spec**: REQ-003/REQ-010；SCN-004/005/016；TC-004/005/016/020
  - **依赖**: T12, T13, T14
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(ci): T15 add protected state writer`

### P4 · Migration、Shadow 与收敛

### T16: 实现 legacy snapshot 迁移

- [ ] T16: 新任务原生 v2；活跃旧任务只写 LEGACY_UNVERIFIED snapshot；归档任务保持只读
  - **文件**: `scripts/workflow_state/migrate.py`, `scripts/taskctl.py`
  - **测试**: `backend/tests/test_workflow_state_migration.py`
  - **Spec**: REQ-011；SCN-018/019；TC-018/019
  - **依赖**: T5, T9
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T16 migrate legacy snapshots`

### T17: 实现文档 generated marker 发布

- [ ] T17: 只替换 tasks/verify/issues/milestones marker 区，支持 dry-run、重建与人工正文保护
  - **文件**: `scripts/workflow_state/materialize.py`, `scripts/taskctl.py`
  - **测试**: `backend/tests/test_workflow_state_materialize.py`
  - **Spec**: REQ-008；SCN-001/012/013；TC-001/012/013
  - **依赖**: T5, T9
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T17 materialize generated views`

### T18: 建立 Shadow 对账与 cutover 报告

- [ ] T18: 比较 legacy/v2 状态、输出解释性 drift，覆盖新任务与 legacy 两类试运行
  - **文件**: `scripts/workflow_state/shadow.py`, `scripts/taskctl.py`
  - **测试**: `backend/tests/test_workflow_state_shadow.py`
  - **Spec**: REQ-008/REQ-011；SCN-001/012/013/018/019；TC-001/012/013/018/019
  - **依赖**: T16, T17
  - **估时**: 45 min
  - **产出**: 1 commit，建议 `feat(workflow-state): T18 add shadow comparison`

### T19: 更新治理规则并准备旧 Gate 退役

- [ ] T19: 将 AGENTS/DOD/模板/checker 改为读取 v2 事件投影，Shadow 期保留旧 Gate，登记退役条件
  - **文件**: `AGENTS.md`, `docs/DOD.md`, `docs/rules/checklist.md`, `docs/templates/`, `scripts/check-task.py`, `scripts/check_task_state.py`
  - **测试**: `backend/tests/test_workflow_state_governance.py`
  - **Spec**: REQ-001/REQ-005/REQ-007/REQ-011；SCN-008/011/019；TC-008/011/019
  - **依赖**: T15, T18
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `refactor(governance): T19 route gates to workflow state`

### T20: 建立控制面端到端故障演练

- [ ] T20: 在临时真实 Git 仓串联 commit→event→projection→test→verifier→acceptance，并演练并发/断网/损坏
  - **文件**: `backend/tests/test_workflow_state_e2e.py`, `scripts/ci/test_workflow_state_e2e.sh`
  - **测试**: `backend/tests/test_workflow_state_e2e.py`
  - **Spec**: REQ-001～REQ-011；SCN-001～020；TC-001～020
  - **依赖**: T8, T12, T15, T19
  - **估时**: 60 min
  - **产出**: 1 commit，建议 `test(workflow-state): T20 add end-to-end failure drills`

## 2. 任务依赖图

```text
T1 ─→ T2 ─→ T3 ───────────────┐
 │     │     └────────→ T5 ───┼─→ T9 ─→ T10 ─→ T14 ─┐
 │     └──────────────→ T6 ─→ T7 ─→ T8 ────────────┤
 └─→ T4 ───────────────→ T5   │                     │
       └─→ T11 ─→ T12 ────────┼───────────────→ T15 ┤
                    └─→ T13 ──┘                     │
T5 + T9 ─→ T16 ─┐                                  │
        └→ T17 ─┴→ T18 ─→ T19 ─────────────────────┤
                                                    └→ T20
```

- DAG 无环。
- T2 与 T4 可在 T1 后并行。
- T3 与 T6 可在 T2 后并行。
- T11 可与 T6～T10 并行。
- T16 与 T17 可在 T5/T9 后并行。

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 主要场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_workflow_state_models.py` | 未知 schema 拒绝 | REQ-010 | SCN-017 | TC-017 | L1 | `fa1a0fc` | PASS | PASS | PENDING |
| T2 | `test_workflow_state_canonical.py` | 历史覆盖拒绝 | REQ-001 | SCN-002 | TC-002 | L1 | `dca321e` | PASS | PASS | PENDING |
| T3 | `test_workflow_state_reducer.py` | 状态正交与 evidence 失效 | REQ-002/006 | SCN-003/009/010 | TC-003/009/010 | L1 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T4 | `test_workflow_state_actors.py` | Writer 跨 Actor 自签拒绝 | REQ-003 | SCN-004/005 | TC-004/005/020 | L1 | `2b282b4` | PASS | PASS | PENDING |
| T5 | `test_workflow_state_projector.py` | 重建、幂等、drift | REQ-008 | SCN-001/012/013 | TC-001/012/013 | L1 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T6 | `test_workflow_state_git_store.py` | state branch 可用性 | REQ-001/010 | SCN-001/016 | TC-001/016 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T7 | `test_workflow_state_git_store_cas.py` | 原子追加与 CAS | REQ-001/009 | SCN-002/015 | TC-002/015 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T8 | `test_workflow_state_concurrency.py` | 幂等与并发重试 | REQ-009/010 | SCN-014/015/016 | TC-014/015/016 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T9 | `test_taskctl_cli.py` | CLI 重放与 fail closed | REQ-001/002/008/010 | SCN-001/003/017 | TC-001/003/017 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T10 | `test_taskctl_observers.py` | 真实 commit/test evidence | REQ-004/005 | SCN-006/007/008 | TC-006/007/008 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T11 | `test_workflow_state_receipts.py` | allowed-signers 与 trust hash | REQ-003/007 | SCN-004/005/011 | TC-004/005/011/020 | L1 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T12 | `test_taskctl_trusted_events.py` | verifier/user 受信事件 | REQ-003/006/007 | SCN-004/005/009/010/011 | TC-004/005/009/010/011 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T13 | `test_workflow_state_github_observer.py` | API 二次取证 | REQ-003/010 | SCN-005/016 | TC-005/016/020 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T14 | `test_workflow_state_hooks.py` | post-commit 与 BLOCKED | REQ-004/009/010 | SCN-006/007/016 | TC-006/007/016 | L3 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T15 | `test_workflow_state_ci.py` + Shell E2E | CI 分权与非可信输入 | REQ-003/010 | SCN-004/005/016 | TC-004/005/016/020 | L3 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T16 | `test_workflow_state_migration.py` | legacy 三层迁移 | REQ-011 | SCN-018/019 | TC-018/019 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T17 | `test_workflow_state_materialize.py` | marker 保护与重建 | REQ-008 | SCN-001/012/013 | TC-001/012/013 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T18 | `test_workflow_state_shadow.py` | 双轨 drift 对账 | REQ-008/011 | SCN-001/012/013/018/019 | TC-001/012/013/018/019 | L2 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T19 | `test_workflow_state_governance.py` | 新旧 Gate 切换与兼容 | REQ-001/005/007/011 | SCN-008/011/019 | TC-008/011/019 | L3 | PENDING | NOT_RUN | NOT_RUN | PENDING |
| T20 | `test_workflow_state_e2e.py` + Shell E2E | 全链路与故障演练 | REQ-001～011 | SCN-001～020 | TC-001～020 | L3 | PENDING | NOT_RUN | NOT_RUN | PENDING |

## 4. Spec 覆盖汇总

| Spec Requirement | 实施任务 | 验收 TC |
|---|---|---|
| REQ-001 唯一机器事件真源 | T1/T2/T5/T6/T7/T9/T19/T20 | TC-001/002 |
| REQ-002 正交状态语义 | T1/T3/T9/T20 | TC-003 |
| REQ-003 受信 Actor 写入 | T4/T11/T12/T13/T15/T20 | TC-004/005/020 |
| REQ-004 Commit 后置观察 | T10/T14/T20 | TC-006/007 |
| REQ-005 Test Evidence 绑定 | T10/T19/T20 | TC-008 |
| REQ-006 Verifier Evidence 绑定 | T3/T12/T20 | TC-009/010 |
| REQ-007 用户显式验收 | T11/T12/T19/T20 | TC-011 |
| REQ-008 决定性自动投影 | T5/T9/T17/T18/T20 | TC-001/012/013 |
| REQ-009 幂等与并发控制 | T7/T8/T14/T20 | TC-014/015 |
| REQ-010 Fail-closed 可用性 | T1/T6/T8/T9/T13/T14/T15/T20 | TC-016/017 |
| REQ-011 兼容迁移 | T16/T18/T19/T20 | TC-018/019 |

## 5. 用户外部 Gate

| Gate | Owner | 触发时机 | 关闭证据 |
|---|---|---|---|
| 创建/保护 `workflow-state` branch | 用户 | T15 文件完成后、Enforce 前 | Ruleset API 回读 `active`；禁止 force-push/delete |
| 配置 Environment required reviewers + prevent self-review | 用户 | T15 L5 前 | Environment API/截图；未配置则 BLOCKED |
| 提供最小权限 state-writer 身份 | 用户 | T15 L5 前 | 独立 GitHub App 或等价凭据；权限仅目标 ref 写入 |
| 持有 user/verifier/CI 独立私钥 | 用户 | T11/T12 L5 前 | 仓库只含公钥；签名 namespace 与 principal 验签通过 |
| 验收 Shadow 两个真实周期 | 用户 | T18 后 | 两个任务周期无未解释 drift，再批准 Enforce |

以上均为外部配置或人工 Gate，不计入 T1～T20 的 AI 实施 commit；缺任一必需证据时，
相关阶段标 `BLOCKED`，不得写成 PASS。

## 6. 总估时

| 批次 | 任务 | 估时 |
|---|---|---:|
| P1 Core | T1～T5 | 4h15m |
| P2 Git Store 与 CLI | T6～T10 | 4h30m |
| P3 Trust 与 Gates | T11～T15 | 4h45m |
| P4 Migration/Shadow | T16～T20 | 4h30m |
| **总估时** | **20 个 commit** | **18h** |

实施后在本文件追加每项实际耗时、commit、测试、verifier 结果及偏差；总体估时偏差目标 ≤30%。

## 7. 实施顺序

1. P1 Core：T1 → T2/T4 → T3 → T5。
2. P2 Git Store：T6 → T7 → T8；T9 → T10。
3. P3 Trust：T11 → T12/T13 → T14 → T15。
4. P4 Migration：T16/T17 → T18 → T19 → T20。
5. 每个 T 完成后立即回写本文件，再运行独立 verifier；FAIL 修复后重验。
6. 两轮 verifier 修复仍不收敛时停止，列出偏差并请求用户决策。

## 8. 步骤 3 DOD

- [x] 20 个任务均 ≤1h AI 工作量。
- [x] 每个任务对应 1 个 commit 边界。
- [x] 每个任务映射至少一个 Spec Requirement/Scenario/TC 和自动化测试。
- [x] 依赖关系为无环 DAG，实施顺序明确。
- [x] 总估时 18h，处于 plan.md 的 14～18h 范围。
- [x] 用户外部 Gate 与 AI commit 分离，不伪造远端完成态。
- [x] 用户于 2026-07-30 验收任务粒度、依赖和实施顺序。

> 当前 Gate：**ACCEPTED / IMPLEMENTATION AUTHORIZED**。步骤 4 已开始；尚未完成的任务
> 继续保持 `[ ] + PENDING/NOT_RUN`，不得预写测试或 verifier PASS。

## 9. 埋点挂载点

本任务 `layer: L0`，属于内部治理控制面，不产生终端用户产品事件或业务指标；
按 `docs/templates/tasks-template.md` 的 L0 豁免规则，不挂载产品埋点。

## 10. Commit 历史

| Task | commit | 实际耗时 | test | verifier | acceptance | 偏差 |
|---|---|---:|---|---|---|---|
| `T1` | `fa1a0fc` | 18 min | PASS 30/30 | PASS | PENDING | 比估时少 27 min；独立 verifier 偏差 0 |
| `T2` | `dca321e` | 20 min | PASS 14/14 | PASS | PENDING | 比估时少 25 min；独立 verifier 5/5 探针 |
| `T4` | `2b282b4` | 15 min | PASS 79/79 | PASS | PENDING | 比估时少 30 min；独立 verifier 8/8 探针 |
| `T3、T5～T20` | PENDING | — | NOT_RUN | NOT_RUN | PENDING | 待实施 |
