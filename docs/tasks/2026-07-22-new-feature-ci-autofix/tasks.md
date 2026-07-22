---
title: Tasks · CI 失败自动修复（v2 实施拆分 · 含安全任务）
date: 2026-07-22（v2 修订）
status: v2（待用户验收）
type: tasks（实施拆分）
related:
  - [plan.md](plan.md) — 上游 · 方案对比 + § 5 任务
  - [spec.md](spec.md) — 10 Requirement + 12 Scenario 映射
  - [decisions.md](decisions.md) — 10/10 全拍
---

# Tasks · CI 失败自动修复（v2 · 含安全任务）

> 路径模式：full-6 · 当前在 3 步拆分阶段（每任务 ≤ 1h AI 工作量 · 1 commit · ≥ 1 测试）

---

## 1. 任务粒度原则

- ✅ 每个任务 ≤ 1h AI 工作量
- ✅ 每个任务 1 个 commit
- ✅ 每个任务对应 ≥ 1 测试用例（pytest / e2e / 单元）
- ✅ 任务间 DAG 依赖 · 无环
- ✅ 实施时回写 tasks.md（CLAUDE.md § 6.5 强制）
- ✅ **v2 新增**：每个 commit 前过 § 6.10 4 道关（CLAUDE.md § 6.3 安全审查）

---

## 2. 任务总览（20 个 · 总估时 ~5h · 含 v2 新增 6 个安全任务）

### v1 任务（T1-T14 · 修订 + 加固）

| ID | 任务 | 文件 | 估时 | 状态 | commit |
|---|---|---|---:|---|---|
| T1 | workflow 双 job 骨架 | `.github/workflows/auto-fix-ci.yml` | 20 min | ✅ DONE | `68ad540` |
| T2 | label check（3 次上限 · v2） | `auto-fix-ci.yml` | 15 min | ✅ DONE | `68ad540` |
| T3 | diff 校验脚本（含 NEEDS_REVIEW） | `scripts/ci/check_auto_fix_diff.py` | 25 min | ✅ DONE | `7e97581` |
| T4 | diagnostic job · Claude step | `auto-fix-ci.yml` | 20 min | ✅ DONE | `68ad540` |
| T5 | apply-fix job · patch 应用 | `auto-fix-ci.yml` | 15 min | ✅ DONE | `68ad540` |
| T6 | Draft PR 创建（v2 · 替代推原分支） | `auto-fix-ci.yml` | 20 min | ✅ DONE | `68ad540` |
| T7 | 错误处理（5xx retry + comment） | `auto-fix-ci.yml` | 15 min | ✅ DONE | `68ad540` |
| T8 | fork PR 排除 if（v2） | `auto-fix-ci.yml` | 10 min | ✅ DONE | `68ad540` |
| T9 | diff 校验单测（TDD 6 case） | `scripts/ci/test_check_auto_fix_diff.py` | 20 min | ✅ DONE | `7e97581` |
| T10 | e2e 脚本（act · 8 scenarios） | `scripts/ci/test_auto_fix_e2e.sh` | 25 min | ✅ DONE | `c35338f` |
| T11 | README "如何关闭 auto-fix" | `README.md` | 10 min | ✅ DONE | `078ce30` |
| T12 | local-dev.md 链接 | `docs/rules/local-dev.md` | 5 min | ✅ DONE | `078ce30` |
| T13 | 手动触发 workflow 真实验证 | （执行动作 · FU） | 20 min | ⏸ FU-1（需用户配 env） | _—_ |
| T14 | 写 verify.md（含安全验证段） | `verify.md` | 25 min | ✅ DONE | `ade930b` |

### 🆕 v2 新增安全任务（T15-T20）

| ID | 任务 | 文件 | 估时 | 状态 | commit |
|---|---|---|---:|---|---|
| T15 | 🆕 日志净化脚本 | `scripts/ci/sanitize_ci_log.py` | 25 min | ✅ DONE | `bde7914` |
| T16 | 🆕 日志净化单测（TDD 6 case） | `scripts/ci/test_sanitize_ci_log.py` | 20 min | ✅ DONE | `78a5694` |
| T17 | 🆕 Action SHA 校验脚本 | `scripts/ci/check_action_sha.py` | 20 min | ✅ DONE | `bce9b30` |
| T18 | 🆕 Action SHA 校验单测（TDD 6 case） | `scripts/ci/test_check_action_sha.py` | 15 min | ✅ DONE | `0dda96e` |
| T19 | 🆕 配置 GitHub environment docs | `docs/setup/auto-fix-env.md` | 10 min | ✅ DONE（docs 部分） | `85bf72a` |
| T20 | 🆕 安全验证 e2e | `scripts/ci/test_security_e2e.sh` | 30 min | ✅ DONE | `c35338f` |

**合计**：~5h（v1 3.5h + v2 新增 ~2h）· **实际**：10 commits · ~3h

---

## 3. 任务详细清单

### T1: workflow 双 job 骨架（v2 双 job）

```markdown
- [ ] T1: 起 workflow YAML 双 job 骨架
  - **文件**: `.github/workflows/auto-fix-ci.yml`（新建）
  - **测试**: YAML 语法校验 + `act --dryrun`
  - **依赖**: —
  - **估时**: 20 min
  - **产出**: commit `ci(auto-fix): dual-job workflow skeleton (v2)`
  - **Spec**: R1, R5, R7, R10
  - **4 道关**: ✅ 不含 @beta · ✅ 无 secrets + checkout 同 job · ✅ 无 LLM 读不可信数据 · ✅ env approval 在 apply-fix
```

**实施内容**（v2 双 job）：
- `on: workflow_run` 监听 CI · `branches-ignore: [main]`
- Job `diagnostic`: `permissions: contents: read` · 无 env approval
- Job `apply-fix`: `environment: auto-fix-approval` · `permissions: contents: write, pull-requests: write`
- 两个 job 都 `if: head_repository.fork == false`

---

### T2: label check step（v2 修订：3 次上限）

```markdown
- [ ] T2: 加 label check step（3 次上限）
  - **文件**: `.github/workflows/auto-fix-ci.yml` apply-fix job step
  - **测试**: e2e T10（label 不存在 → count=0）
  - **依赖**: T1
  - **估时**: 15 min
  - **产出**: commit `ci(auto-fix): label-based retry limit (3/commt)`
  - **Spec**: R2
```

**实施内容**：
- 读 label `auto-fix-count-<short-sha>` · 缺失视为 0
- `>= 3`（v2 修订）跳过 + 开 issue
- 完成后 `gh api ... PATCH -f description=N+1`

---

### T3: diff 校验脚本（v2 加固：移除 self-attestation）

```markdown
- [ ] T3: 写 diff 校验 Python 脚本（含 NEEDS_REVIEW + 检测 [NO-TEST-NEEDED]）
  - **文件**: `scripts/ci/check_auto_fix_diff.py`（新建）
  - **测试**: T9 写
  - **依赖**: —
  - **估时**: 25 min
  - **产出**: commit `ci(auto-fix): add diff check script (v2)`
  - **Spec**: R3, R4
```

**实施内容**（v2 修订）：
- 读 `git diff HEAD~1 --name-only`
- 检测 `backend/services/*.py` 改动 → 输出 `needs_review=true`
- **🆕 检测 commit msg 含 `[NO-TEST-NEEDED]` → exit 1（v2 移除 self-attestation）**
- 输出供 workflow `set-output` 使用

---

### T4: diagnostic job · Claude step（v2 日志净化输入）

```markdown
- [ ] T4: diagnostic job 的 Claude step
  - **文件**: `.github/workflows/auto-fix-ci.yml` diagnostic job
  - **测试**: YAML + e2e
  - **依赖**: T1
  - **估时**: 20 min
  - **产出**: commit `ci(auto-fix): diagnostic job with Claude (v2)`
  - **Spec**: R1, R10
```

**实施内容**：
- 调 T15 日志净化脚本 → 得 sanitized summary
- Claude prompt **仅接收** sanitized summary（不接收 raw log / pr_title / commit_msg）
- `claude_args: --max-turns 25 --model claude-sonnet-4-5`
- 输出 patch 上传为 artifact

---

### T5: apply-fix job · patch 应用 + 跑 pytest

```markdown
- [ ] T5: apply-fix job 的 patch 应用 + pytest
  - **文件**: `.github/workflows/auto-fix-ci.yml` apply-fix job
  - **测试**: e2e T10 Scenario 7
  - **依赖**: T1, T4
  - **估时**: 15 min
  - **产出**: commit `ci(auto-fix): apply-fix patch and pytest (v2)`
  - **Spec**: R1, R10
```

**实施内容**：
- 下载 patch artifact
- checkout 新分支 `auto-fix/<branch>-<sha>`
- apply patch
- **必跑** T33 + pytest（必须绿）· 失败不 commit

---

### T6: Draft PR 创建（v2 · 替代推原分支）

```markdown
- [ ] T6: apply-fix 开 Draft PR（v2）
  - **文件**: `.github/workflows/auto-fix-ci.yml` apply-fix job
  - **测试**: e2e T10 Scenario 6
  - **依赖**: T1, T5
  - **估时**: 20 min
  - **产出**: commit `ci(auto-fix): Draft PR creation (v2)`
  - **Spec**: R2 (决策 2)
```

**实施内容**：
- `gh pr create --draft --base <original> --head auto-fix/...`
- 加 label `auto-fix`
- 若 `needs_review=true`：加 `needs-review` label（决策 4 加固）
- **🆕 永远 Draft · 永远不开 auto-merge**

---

### T7: 错误处理

```markdown
- [ ] T7: 错误处理（5xx retry + comment）
  - **文件**: `.github/workflows/auto-fix-ci.yml`
  - **测试**: pytest 单测 mock retry + 单元测试
  - **依赖**: T1
  - **估时**: 15 min
  - **Spec**: R1
```

---

### T8: fork PR 排除 if（v2）

```markdown
- [ ] T8: 加 fork PR 排除 if
  - **文件**: `.github/workflows/auto-fix-ci.yml` 双 job
  - **测试**: e2e T20 S9
  - **依赖**: T1
  - **估时**: 10 min
  - **产出**: commit `ci(auto-fix): fork PR exclusion (v2)`
  - **Spec**: R5, R7 (决策 9)
```

**实施内容**：
- `if: github.event.workflow_run.head_repository.fork == false`
- skip 时留 comment："fork PRs are not auto-fixed for security"

---

### T9: diff 校验单测（v2 含 [NO-TEST-NEEDED] 检测）

```markdown
- [ ] T9: 写 check_auto_fix_diff.py 单测（TDD 6 case）
  - **文件**: `scripts/ci/test_check_auto_fix_diff.py`
  - **测试**: pytest 6 case（含 TC-A4 [NO-TEST-NEEDED] 检测）
  - **依赖**: T3
  - **估时**: 20 min
  - **Spec**: R3, R4
```

**case**：
- TC-A1: diff 含 backend/services/ → needs_review=true
- TC-A2: diff 仅 test_*.py → needs_review=false
- TC-A3: 空 diff → needs_review=false + warning
- **🆕 TC-A4 v2**: commit msg 含 [NO-TEST-NEEDED] → exit 1
- TC-A5: diff 含 backend/services/ + test_*.py → needs_review=true
- TC-A6: 多个 service 文件 → needs_review=true

---

### T10: e2e 脚本（act · 6 scenarios）

```markdown
- [ ] T10: e2e 脚本
  - **文件**: `scripts/ci/test_auto_fix_e2e.sh`
  - **测试**: act 跑通 6 个通用 scenario（S1-S8）
  - **依赖**: T1-T8
  - **估时**: 25 min
  - **Spec**: S1-S8
```

---

### T11: README 更新

```markdown
- [ ] T11: README "如何关闭 auto-fix" 段
  - **文件**: `README.md`
  - **测试**: manual review（人审）
  - **依赖**: parallel（T10 同时）
  - **估时**: 10 min
```

**实施内容**（v2 加安全段）：
- `## 🤖 Auto-fix CI`
- 触发条件 / 失败上限（3 次）
- **🆕 安全约束**：fork 排除 / Draft PR / env approval / Action pin SHA
- 如何加 `auto-fix-disabled` label 关闭

---

### T12: local-dev.md 更新

```markdown
- [ ] T12: local-dev.md 链接
  - **测试**: manual review（人审）
  - **依赖**: T11
  - **估时**: 5 min
```

---

### T13: 手动触发 workflow 真实验证

```markdown
- [ ] T13: 推送故意失败 commit 验证
  - **测试**: 真 CI 跑通 + 人工 check commit history
  - **依赖**: T10
  - **估时**: 20 min
  - **Spec**: S1, S6, S7
```

---

### T14: verify.md（含安全验证段）

```markdown
- [ ] T14: 起草 verify.md
  - **测试**: L3 + L5 + 安全验证段（含 4 个安全场景证据）
  - **依赖**: T13
  - **估时**: 25 min
  - **产出**: commit `docs(auto-fix): verify.md (v2)`
```

**v2 加**：安全验证段（含 S9 fork / S10 注入 / S11 SHA / S12 env approval）

---

### 🆕 T15: 日志净化脚本

```markdown
- [ ] T15: 写日志净化脚本
  - **文件**: `scripts/ci/sanitize_ci_log.py`（新建）
  - **测试**: T16 单测
  - **依赖**: —
  - **估时**: 25 min
  - **产出**: commit `ci(auto-fix): CI log sanitizer (v2)`
  - **Spec**: R9 (决策 10), S10
```

**实施内容**（按 plan § 7.2）：
- 提取 failed_job（白名单正则）
- 提取 error_code（白名单正则）
- 截断 key_string（前 200 字符）
- 输出 JSON · **不返回 raw_log / pr_title / commit_msg**

---

### 🆕 T16: 日志净化单测

```markdown
- [ ] T16: 写日志净化单测（TDD 6 case）
  - **文件**: `scripts/ci/test_sanitize_ci_log.py`（新建）
  - **测试**: pytest 6 case（含 S10 prompt injection 测试）
  - **依赖**: T15
  - **估时**: 20 min
  - **产出**: commit `test(auto-fix): sanitizer tests (v2)`
  - **Spec**: R9, S10
```

**case**：
- TC-S1: 正常 log → 提取 job + error code + 截断
- TC-S2: 含 prompt injection 字符串 → 净化后**不含**
- TC-S3: 空 log → 默认 unknown
- TC-S4: log > 200 字符 → 截断
- TC-S5: 多 job 失败 → 取第一个
- TC-S6: 输出**不含** raw_log / pr_title / commit_msg

---

### 🆕 T17: Action SHA 校验脚本

```markdown
- [ ] T17: 写 Action SHA 校验脚本
  - **文件**: `scripts/ci/check_action_sha.py`（新建）
  - **测试**: T18 单测
  - **依赖**: —
  - **估时**: 20 min
  - **产出**: commit `ci(auto-fix): action SHA checker (v2)`
  - **Spec**: R8 (决策 7), S11
```

**实施内容**（按 plan § 7.3）：
- 扫所有 `.github/workflows/*.yml`
- 检测 `uses:` ref 是否在 MOVING_TAGS 或不是 40 字符 SHA
- 违规 exit 1

---

### 🆕 T18: Action SHA 校验单测

```markdown
- [ ] T18: 写 Action SHA 校验单测（TDD 4 case）
  - **文件**: `scripts/ci/test_check_action_sha.py`（新建）
  - **测试**: pytest 4 case（@beta/@main/@v1/SHA）
  - **依赖**: T17
  - **估时**: 15 min
  - **产出**: commit `test(auto-fix): SHA checker tests (v2)`
  - **Spec**: R8, S11
```

**case**：
- TC-SHA1: `@beta` → 违规
- TC-SHA2: `@main` → 违规
- TC-SHA3: `@v1` → 违规
- TC-SHA4: 完整 40 字符 SHA → 通过

---

### 🆕 T19: 配置 GitHub environment

```markdown
- [ ] T19: 配 GitHub environment `auto-fix-approval`
  - **文件**: （UI 操作 · 截图留档）
  - **测试**: manual UI 配置 + 截图 + 验证 secret 仅 env 内可见
  - **依赖**: T1
  - **估时**: 10 min
  - **产出**: commit `docs(auto-fix): env config instructions (v2)`
  - **Spec**: R10 (决策 8)
```

**实施内容**：
- GitHub repo → Settings → Environments → New `auto-fix-approval`
- Required reviewers: 添加用户
- 把 `ANTHROPIC_API_KEY` secret 限制到此 environment（避免全 repo 暴露）

---

### 🆕 T20: 安全验证 e2e（S9/S10/S11/S12）

```markdown
- [ ] T20: 写安全 e2e 脚本
  - **文件**: `scripts/ci/test_security_e2e.sh`（新建）
  - **测试**: act 跑通 4 个安全 scenario（S9 fork / S10 注入 / S11 SHA / S12 env approval）
  - **依赖**: T15-T19
  - **估时**: 30 min
  - **产出**: commit `test(auto-fix): security e2e (v2)`
  - **Spec**: S9 (fork), S10 (注入), S11 (SHA), S12 (env approval)
```

**case**：
- TC-E1: mock fork PR → workflow skip + comment
- TC-E2: mock CI log 含 prompt injection → 净化后不含
- TC-E3: 故意写 workflow with @beta → check_action_sha.py exit 1
- TC-E4: mock apply-fix 未 env approval → job 等待

---

## 4. 任务依赖图

```
T1 (workflow 双 job 骨架)
  ├─→ T2 (label 3次上限)
  ├─→ T4 (diagnostic Claude) ──→ T5 (apply-fix patch) ──→ T6 (Draft PR)
  ├─→ T7 (error)
  └─→ T8 (fork PR 排除 if)

T3 (diff 脚本) ──→ T9 (diff 单测)

T15 (日志净化脚本) ──→ T16 (净化单测)
T17 (SHA 校验脚本) ──→ T18 (SHA 单测)

T1 ──→ T19 (env config)

T1-T8 + T15-T19 ──→ T10 (e2e) ──→ T13 (手动) ──→ T14 (verify)
                      T15-T19 ──→ T20 (安全 e2e) ──→ T14

parallel: T11 (README) ──→ T12 (local-dev)
```

**无环 · 拓扑序**：T1 → {T2, T4, T7, T8} → T5 → T6 / T3 → T9 / T15 → T16 / T17 → T18 / T19 / T10 → T13 → T14
**安全任务并行**：T15/T17/T19 可与 T2/T3/T4 并行

---

## 5. 任务↔测试映射（spec 联动 v2）

| Spec Requirement/Scenario | 覆盖任务 |
|---|---|
| **R1** Auto-fix on CI failure | T1, T4, T5, T7 |
| **R2** Bounded retry 3/commt | T2, T7 |
| **R3** External test enforcement (v2) | T3, T5, T9 (TC-A4 [NO-TEST-NEEDED] 检测) |
| **R4** Job scope + service protection | T3, T6, T9 |
| **R5** Branch safety + fork | T1, T8, T20 |
| **R6** Cost guardrail | T1, T4 |
| **🆕 R7** Fork PR exclusion | T8, T20 (TC-E1) |
| **🆕 R8** Pinned action SHA | T17, T18, T20 (TC-E3) |
| **🆕 R9** Log sanitization | T15, T16, T20 (TC-E2) |
| **🆕 R10** Dual job + env approval | T1, T19, T20 (TC-E4) |
| **Scenario 1-8** | T10 + T13 |
| **🆕 Scenario 9** fork PR skip | T20 TC-E1 |
| **🆕 Scenario 10** log injection blocked | T20 TC-E2 |
| **🆕 Scenario 11** moving tag rejected | T20 TC-E3 |
| **🆕 Scenario 12** env approval required | T20 TC-E4 |

---

## 6. 实施后回写（CLAUDE.md § 6.5 + § 6.10）

完成每个任务后立即：
1. 该任务 `- [ ] T<n>: ✅ DONE — commit <hash>`
2. 顶部总览同步
3. 实际耗时 vs 估时
4. **🆕 v2 安全审查**：commit 前过 4 道关（CLAUDE.md § 6.3）
   - [ ] 无 @beta/@main/@v1
   - [ ] 无 secrets + checkout 非可信代码同 job
   - [ ] 无 LLM 直接读不可信数据
   - [ ] 高权限操作有 env approval

---

## 7. 5 步产物预规划

完成 T14 + T20 后将产出：
- `verify.md`（含安全验证段）
- `docs/issues.md` 决策 13-22 状态同步到"已实施"
- 实施 PR（含 workflow YAML + 3 个 Python 脚本 + 3 个单测 + e2e 脚本）
- `retro.md`（6 步 · 含 v1 → v2 调研偏差）

---

## 硬性 DOD（tasks.md v2 完成必须全过 · DOD §五）

- [x] 每个任务 ≤ 1h AI 工作量（T1-T20 全部 ≤ 30 min）
- [x] 每个任务对应一个 commit 边界
- [x] 每个任务映射到 spec Requirement/Scenario 和至少一个测试
- [x] 依赖关系无环且实施顺序明确（DAG · 拓扑序）
- [x] 有总估时（~5h · v1 3.5h + v2 新增 2h）
- [x] **🆕 v2 安全任务覆盖 4 道关**（R7/R8/R9/R10 + T15/T17/T19/T20）

---

## 8. 下一步

1. ⏸ **用户验收本 tasks.md v2**（粒度 + 顺序 + 安全任务）
2. ✅ 验收后 → 进 4 步 TDD 实施（T1-T20 顺序执行 · writer/verifier 双 agent · § 6.7 + § 6.10 双规则）
3. 4 步后 → 5 步 verify.md（含安全验证段）