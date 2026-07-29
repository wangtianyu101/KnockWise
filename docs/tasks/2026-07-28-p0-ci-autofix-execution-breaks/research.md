---
title: P0 调研 · CI auto-fix 三项执行断链
type: research
step: 0
date: 2026-07-28
status: approved
tags: [p0, bug, github-actions, agent, security, auto-fix]
related: [task.yaml, decisions.md, ../../issues.md]
---

# P0 调研 · CI auto-fix 三项执行断链

> 路径模式：`timebox`（用户已验收）
>
> 当前阶段：步骤 0 已验收，进入步骤 4 TDD 实施。

## 1. 影响

AF-01 和 AF-02 会在每个进入对应步骤的 auto-fix run 中确定性断链；AF-03 位于含 secret 与写权限的
apply-fix job，会破坏提交边界。完整量化、分级与关闭条件见本文 § 三。

## 2. 临时止血

永久修复前不批准 `auto-fix-approval` 的 pending job；持续触发造成噪声时，由用户在 GitHub 手工 disable
`auto-fix-ci`。本任务不代替用户执行远端操作。方案比较见本文 § 六。

## 3. 根本原因

根因分别是：把 Action `with:` 输入误当 shell、写 `$GITHUB_OUTPUT` 时遗漏 step identity、补丁载体与
Git index 生命周期未隔离，以及测试 oracle 只验声明文本。证据和反证见本文 § 二/四。

## 4. 后续时间盒

- **T+30m**：三项失败回归先红，完成最小 workflow/index 修复。
- **T+2h**：定向测试、治理/安全回归与独立 verifier 收敛。
- **T+24h**：L5 GitHub run 验证非空分支、精确 commit 与 Draft PR。
- **T+48h**：同步 `verify.md`、`tasks.md`、`docs/issues.md`。
- **T+72h**：如用户要求，起草单阶段 retro；既有 v4 七项安全债保持独立。

## 5. 沟通

- **当前状态**：步骤 0 已验收，步骤 4 TDD 实施中。
- **负责人**：Codex 负责测试/实现/本地证据；独立 verifier 负责固定 commit 校验；用户负责步骤验收与
  GitHub environment approval。
- **通报位置**：当前 Codex 对话、本文和 `docs/issues.md` 债务 24。

## 一、任务理解

- **用户原话**：「Claude prompt 里的 `$(jq ...)` 不会执行；`create-branch` 缺少 step id，后续分支输出为空；`git add -A` 可能把 `patch.diff` 一并提交。是这三项，可以。」
- **确认范围**：
  1. 让净化后的结构化 CI 信息真正进入 Claude `prompt`，不再出现字面量 `$(jq ...)`。
  2. 给创建分支步骤补可引用的 step id，确保 push 与 Draft PR 获得非空分支名。
  3. 取消 `git add -A` 的全工作区 staging，确保只提交 `patch.diff` 描述的变更，且 `patch.diff` 本身不入 commit。
- **明确排除**：
  - 既有 auto-fix v4 的其余七项安全债。
  - retry label、错误评论 API、`head_branch`/`head_sha` 漂移、environment 远端配置。
  - 当前 31 个 backend 基线失败。
  - AI Coding Control Plane v2。

## 二、复现与现状证据

### 2.1 AF-01 · `with.prompt` 保留三个字面量 `$(jq ...)`

位置：`.github/workflows/auto-fix-ci.yml:154-168`。

静态复现：

```text
AF01_LITERAL_JQ=True
AF01_LITERAL_COUNT=3
```

GitHub Actions 仅把 `run:` 步骤交给 shell；`with:` 是 Action 输入映射。当前固定版本
`anthropics/claude-code-action@787c5a0ce96a9a6cfb050ea0c8f4c05f2447c251`
的 `action.yml` 把 `inputs.prompt` 直接放进 `PROMPT` 环境变量，没有 shell 求值。因此三段 `$(jq ...)`
会作为普通文本进入 Action，而不会读取 `/tmp/sanitized.json`。

官方依据：

- [GitHub workflow syntax：`steps[*].with` 是 Action 输入映射](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepswith)
- [固定版本 Claude Action manifest](https://raw.githubusercontent.com/anthropics/claude-code-action/787c5a0ce96a9a6cfb050ea0c8f4c05f2447c251/action.yml)

### 2.2 AF-02 · 输出生产者无 step id

位置：`.github/workflows/auto-fix-ci.yml:179-190,231-246`。

静态复现：

```text
AF02_CREATE_BRANCH_HAS_ID=False
AF02_DOWNSTREAM_REFERENCES=2
```

创建分支步骤向 `$GITHUB_OUTPUT` 写 `new_branch`，但没有 `id: create-branch`；两个下游步骤却读取
`${{ steps.create-branch.outputs.new_branch }}`。GitHub 对不存在的 context property 返回空字符串，且官方文档明确要求
step 必须有 `id` 才能读取其 output。

官方依据：

- [GitHub workflow commands：step output 需要 step id](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-an-output-parameter)
- [GitHub contexts：不存在的 property 求值为空字符串](https://docs.github.com/en/enterprise-cloud@latest/actions/reference/workflows-and-actions/contexts)

### 2.3 AF-03 · `patch.diff` 会被全量 staging

位置：`.github/workflows/auto-fix-ci.yml:167-168,192-201,223-229`。

复现事实：

1. Claude 被要求把 `patch.diff` 写入仓库根目录。
2. `.gitignore` 不排除 `patch.diff`。
3. 应用补丁后没有删除该文件。
4. 临时 Git 仓库真实运行 `git add --dry-run -A` 输出：

```text
add 'patch.diff'
```

因此 `git add -A` 会把补丁载体和工作区中任何其他模型临时文件一起 stage。

### 2.4 当前测试 oracle 为假绿

以下现有测试在三项缺陷全部存在时仍返回 0：

| 命令 | 当前结果 | 缺口 |
|---|---|---|
| `bash scripts/ci/test_auto_fix_e2e.sh` | 8/8 PASS | 主要 grep 文本存在，不执行 prompt/output/staging 链 |
| `bash scripts/ci/test_security_e2e.sh` | 全 PASS | 只证明四类关键字存在 |
| `pytest backend/tests/test_ci_workflow.py -q` | 7 PASS | 只读取 `.github/workflows/ci.yml`，不验证 auto-fix |

结论：本任务必须先写失败回归，不能只改三行 YAML。

### 2.5 最近相关改动

| commit | 内容 | 判断 |
|---|---|---|
| `4648d50` | 把 Claude step 移到 apply-fix | 引入/保留 AF-01 |
| `68ad540` | 建立双 job auto-fix workflow | 引入 AF-02、AF-03 |
| `c35338f` | 新增 auto-fix E2E / security E2E | oracle 未覆盖三条执行链 |
| `f1cf815` | 治理 Gate 回归链 | 未扩展到 auto-fix 行为 |

当前 HEAD 在调研期间由并行任务从 `95def39` 前进到 `dde8c4f`；实现时必须重新读取 diff，禁止覆盖其他 Agent
对 `.github/workflows/auto-fix-ci.yml`、`backend/tests/test_ci_workflow.py`、`scripts/ci/test_security_e2e.sh`
等文件的未提交修改。

## 三、影响范围与关闭条件

### 3.1 影响

| 缺陷 | 频率 | 直接影响 | 等级 |
|---|---:|---|---|
| AF-01 | 每个进入 Claude 的 run | Agent 收不到真实失败字段，可能盲目生成补丁 | 🔴 P0 |
| AF-02 | 每个进入 push/PR 的 run | 分支输出为空，交付链确定性中断 | 🔴 P0 |
| AF-03 | 每个进入 commit 的 run | 过度 staging，提交补丁载体或其他临时文件 | 🟠 P1；因处在高权限 Agent job 中并入本 P0 |

- **业务数据**：不修改 MySQL；无已知业务数据损坏。
- **代码完整性**：存在错误补丁、错误 staging、无法形成 Draft PR 的风险。
- **安全边界**：apply-fix job 经 environment approval 后拥有 `ANTHROPIC_API_KEY`、`contents: write`、
  `pull-requests: write`、`issues: write`，因此 staging 和不可信输入错误不能按普通脚本 Bug 处理。

### 3.2 关闭条件

- [ ] `prompt` 中不存在 `$(jq` 或其他假定 shell 展开的文本。
- [ ] Claude 获得真实、结构化的 `failed_job` 和 `error_code`。
- [ ] 当前 raw-prefix `key_string` 不进入 prompt；等既有 v4 sanitizer 安全债修复后再恢复。
- [ ] prompt 把 CI context 明确标记为不可信数据，不允许其改变指令或工具权限。
- [ ] 创建分支步骤有稳定 `id: create-branch`，两个消费者读取到同一非空 `new_branch`。
- [ ] patch 使用 `git apply --index` 或等价的精确 staging；不再出现 `git add -A`。
- [ ] `patch.diff` 应用后删除，且不会出现在 cached diff 或 commit 中。
- [ ] 新增文件、修改文件、删除文件均可由 patch 正确 stage；无关 untracked 文件不被 stage。
- [ ] diff policy 检查读取当前 staged patch，而不是旧的 `HEAD~1`。
- [ ] 三个缺陷各有先红后绿的回归测试；测试运行生产 workflow/真实 git/jq 行为，不只 grep 关键字。
- [ ] 原 auto-fix E2E、安全 E2E、治理测试与 Action provenance 全绿。
- [ ] 独立 verifier 对固定 commit 给出 PASS；L5 真实 GitHub run 能创建 Draft PR。

## 四、根因假设与验证

| 假设 | 证据 | 结论 |
|---|---|---|
| H1：把 Action `with:` 误当成 shell | 三个 `$(jq ...)` 位于 `with.prompt`；固定 Action 直接传 `PROMPT` env | ✅ 已确认 |
| H2：输出协议只写 `$GITHUB_OUTPUT`，遗漏 step identity | 生产者无 id，消费者引用不存在的 id | ✅ 已确认 |
| H3：补丁载体与提交内容生命周期未分离 | patch 在 repo root，未删除，随后 `git add -A` | ✅ 已确认 |
| H4：测试只验声明文本，没有跑真实执行链 | 三套测试全部 PASS，但三项稳定复现 | ✅ 已确认 |
| H5：现有 diff checker 能保护 staged patch | `get_changed_files()` 实际运行 `git diff HEAD~1 --name-only` | ❌ 已否定；必须改为检查 cached diff |

## 五、相关文件与依赖影响

### 5.1 直接文件

- `.github/workflows/auto-fix-ci.yml`
- `scripts/ci/check_auto_fix_diff.py`
- `scripts/ci/test_check_auto_fix_diff.py`
- `scripts/ci/test_auto_fix_e2e.sh`
- `scripts/ci/test_security_e2e.sh`
- `backend/tests/test_ci_workflow.py` 或新增专用 workflow contract test

### 5.2 依赖链

```text
/tmp/sanitized.json
  → prompt context step
  → Claude Action prompt
  → patch.diff
  → git apply --index
  → cached diff policy
  → test-quality + backend pytest
  → commit（只提交 cached patch）
  → branch output
  → push
  → Draft PR
```

变更影响：

- 改 prompt 输入会影响 R9 不可信输入边界。
- 改 apply/stage 会影响 `check_auto_fix_diff.py` 的数据源和所有现有单测。
- 补 step id 会影响 push 与 PR 两个消费者。
- 当前 backend 全量 31 个既有失败仍可能让真实 run 停在测试阶段；这不属于本任务修复范围。

## 六、止血与推荐路径

### 6.1 临时止血

在永久修复完成前，不批准 `auto-fix-approval` environment 的 pending job；如持续触发造成噪声，可由用户在 GitHub
手工 disable `auto-fix-ci`。本任务不代替用户操作远端。

### 6.2 方案比较

| 方案 | 内容 | 优点 | 风险 | 结论 |
|---|---|---|---|---|
| A. 最小安全修复 | 结构化 step output；补 id；`git apply --index`；cached diff；真实回归 | 范围最小、可快速回滚 | 暂不传 `key_string`，上下文较少 | **推荐** |
| B. 同时完成 auto-fix v4 | 三项 + 既有七项安全债 | 一次收口 | 扩大到跨模块重构，违反用户本次 scope | 不采用 |
| C. 永久关闭 auto-fix | disable workflow | 风险最低 | 失去自动修复能力 | 仅失败回滚 |

### 6.3 路径建议

整体按 `timebox`：

```text
0 调研（当前，待用户验收）
→ 4 TDD 实施：三项失败回归 → 最小安全修复
→ commit 级独立 verifier
→ 5 L3 集成 + L5 GitHub staging
→ 6 单阶段复盘（用户要求时）
```

建议降级为一个实现 commit，但在 commit 前按三个行为契约分别完成红→绿；不得把既有 v4 七项安全债混入 diff。

## 七、风险与安全审查

### 7.1 官方资料

- [GitHub Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub Script injections](https://docs.github.com/en/actions/concepts/security/script-injections)
- [GitHub Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Claude Code Action security](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md)
- [OWASP LLM Excessive Agency](https://genai.owasp.org/llmrisk2023-24/llm08-excessive-agency/)

### 7.2 威胁模型

| 场景 | 攻击者能力 | 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|---|
| T1 间接 prompt injection | 可让 CI 输出任意文本 | raw-prefix `key_string` 被修通后进入 Claude | 越权工具调用、错误 patch | 🔴 | 本任务暂不传 key_string；只传 allowlisted fields；数据边界标签 |
| T2 过度 staging | Claude 可在 workspace 写临时文件 | `git add -A` | 非预期文件进入 Draft PR | 🔴 | `git apply --index`；删除 patch；cached allowlist evidence |
| T3 分支输出为空 | 可触发失败 run | 缺 step id | push/PR 中断，修复链不可用 | 🟠 | 明确 id + 非空断言 + 真实 output test |
| T4 同工作区并发污染 | 其他 Agent/步骤产生文件 | 全量 staging | 混入无关或敏感文件 | 🔴 | 只提交 patch 产生的 index；提交前 cached diff 断言 |
| T5 测试假绿 | 可提交只满足 grep 的 YAML | oracle 只查关键字 | 同类断链再次上线 | 🔴 | 真实 subprocess + temp git + rc/输出/索引内容断言 |

### 7.3 权限边界

```text
不可信 CI log
      |
      v
diagnostic job
contents: read · 无 Anthropic secret · 输出 sanitized.json
      |
      v artifact
[GitHub environment approval]
      |
      v
apply-fix job
ANTHROPIC_API_KEY + contents/PR/issues write
      |
      +→ prompt context：仅 failed_job/error_code，标记 untrusted data
      |
      +→ Claude 生成 patch.diff
      |
      +→ git apply --index → cached diff policy → tests
      |
      +→ commit cached patch only → push → Draft PR

禁止路径：raw log/key_string → prompt；workspace 全量 → git add -A。
```

### 7.4 外部依赖审查

当前工作区所有 Action 均为完整 SHA，且本次使用生产 checker 联网核验通过：

```text
All third-party Actions pinned to full SHA
All third-party Action provenance verified
```

本任务不修改 Action 版本。关键固定依赖：

- `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803`
- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
- `actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`
- `anthropics/claude-code-action@787c5a0ce96a9a6cfb050ea0c8f4c05f2447c251`

### 7.5 不可信输入

| 输入 | 当前问题 | 本任务策略 |
|---|---|---|
| raw CI log | 包含攻击者可控文本 | 只在 diagnostic 读取，不进入 apply-fix prompt |
| `sanitized.json.failed_job/error_code` | 仍是不可信数据 | jq schema/type 检查，单行 JSON，明确数据标签 |
| `key_string` | raw log 前 200 字符 | 本任务不传入 Claude |
| branch / head SHA | 外部 metadata | 不拼成 shell 源代码；始终引用 env 并双引号 |
| Claude `patch.diff` | 模型不可信输出 | `git apply --check/--index`、cached diff policy、测试、Draft PR |
| workspace 其他文件 | 其他 Agent/步骤产生 | 不使用 `git add -A`，不进入 index |

## 八、用户决策

| 日期 | 决策项 | 选择 | 状态 | 用户原话 |
|---|---|---|---|---|
| 2026-07-28 | 修复范围 | 只处理 AF-01 / AF-02 / AF-03 及必要回归测试 | ✅ 已确认 | 「是这三项，可以。」 |
| 2026-07-28 | 路径与 prompt 安全边界 | `timebox`；只传 failed_job/error_code，暂不传 raw-prefix key_string | ✅ 已验收 | 「验收步骤 0，开始实施。」 |

## 自检

- [x] 用户已确认任务理解与三项 scope
- [x] 已读 `docs/issues.md`
- [x] 已运行 `git log -10`、相关文件历史与 `git status`
- [x] 已定位 ≥ 3 个相关文件
- [x] 三项均有可重复证据
- [x] 根因假设 ≥ 2 且均已验证
- [x] 依赖链与范围外事项已列
- [x] 风险分级与缓解已列
- [x] 官方安全文档已读
- [x] 威胁模型 ≥ 3
- [x] 权限边界、外部依赖、不可信输入已列
- [x] 给出完整路径建议
- [x] 用户验收步骤 0 与 `timebox` 路径
