# 🐛 调研报告 · Bug：pre-commit DOD 校验吞掉 checker 失败退出码

> 日期：2026-07-23 · 调研人：Claude Code + 3 个独立对抗 Agent · 紧急度：P0
> 路径模式：`fix-mini`（0 → 4 回归测试与修复 → 6 复盘）

## 1. 任务理解

- **用户原话**："我们一个个来哈 先看P0"；对推荐范围回复"是"。
- **现象**：`scripts/pre-commit` 的 DOD 校验把 `scripts/check-step.py` 与 `tail -10` 组成管道；checker 返回非零时，管道仍可能以末端 `tail` 的 0 退出，导致非法任务文档未设置 `failed=1`。
- **期望**：保留最后 10 行输出，同时显式传播 checker 自身退出码；checker 失败必须阻断 commit。
- **任务边界**：仅修 DOD checker 的退出码传播并增加 3 个回归场景；不捆绑环境 fail-closed、hook 安装、全局 `pipefail`、`check_retro` 覆盖或 pre-commit 重构。

## 2. 复现路径

### 2.1 复现步骤

1. 暂存一个位于 `docs/tasks/` 下且能映射到步骤的 Markdown 文件。
2. 让 `scripts/check-step.py` 对该文件返回非零并输出诊断。
3. `scripts/pre-commit:105` 执行 `if ! python3 ... 2>&1 | tail -10; then`。
4. POSIX `sh` 默认采用管道末端 `tail` 的退出码 0，`!` 后条件为 false，`failed=1` 不执行，DOD 段假绿。

### 2.2 触发条件

- 暂存文件匹配 `docs/tasks/.*\.md`，且 basename 为 `research.md`、`spec.md`、`plan.md`、`tasks.md`、`test-cases.md`、`verify.md` 或 `retro.md`。
- `scripts/check-step.py` 对该文件返回非零。
- 当前 hook 使用 `#!/bin/sh` 且未提供可移植的 `pipefail`。

### 2.3 稳定性

- 静态语义上稳定复现：只要 checker 非零而 `tail` 正常返回 0，就会吞掉 checker 退出码。
- 需在实施阶段先写真实执行 Shell 路径的红测试，不能只单测 `check-step.py`。

## 3. 影响范围与关闭条件

### 3.1 影响范围

- **直接文件**：`scripts/pre-commit:78-117`、`scripts/check-step.py`（被调用方，不需改主体）。
- **流程影响**：0-6 步任务文档的本地 DOD gate；违反双 gate 的文档可能进入 commit。
- **数据影响**：无业务数据损坏；风险是错误状态和不合规文档被提交。
- **依赖影响**：修改 hook 调用方式会影响所有被识别的任务文档步骤，但不改变 checker 规则。

### 3.2 关闭条件

- [ ] 采用 POSIX `sh` 兼容的显式 `output + rc` 捕获，不引入全局 `pipefail`。
- [ ] 合法 checker 结果（exit 0）通过。
- [ ] 非法 checker 结果（exit 非 0）阻断。
- [ ] 非法 checker 输出超过 10 行时只显示末 10 行，仍保持阻断。
- [ ] 不扩大到环境 fail-closed、hook 安装、全 hook 重构等其他事项。

## 4. 根因假设与对抗核验

| 假设 | 证据 | 结论 / 验证方法 |
|---|---|---|
| H1：管道吞掉 checker 的非零退出码 | `scripts/pre-commit:105`；`#!/bin/sh` 仅 `set -e` | ✅ 主根因；实施阶段 Shell 回归测试复现 |
| H2：`set -e` 会自动传播管道前部失败 | POSIX `sh` 默认只看末端命令；`if` 条件本身也属于 `errexit` 例外上下文 | ❌ 已反驳 |
| H3：全局 `pipefail` 是最小修复 | `pipefail` 非 POSIX；当前 shebang 是 `/bin/sh` | ❌ 不采用，避免跨平台与全局语义变化 |
| H4：必须用 `mktemp + trap` 保留退出码 | checker 输出规模有限；同文件 pytest/tsc 已使用变量捕获 | ❌ 过度设计 |

## 5. 最近相关改动与仓库状态

执行证据：

```bash
git log --oneline -10 -- scripts/pre-commit scripts/check-step.py docs/issues.md
git status --short --branch
```

相关提交：

- `47cfc15 fix(hook): pre-commit pytest/tsc 门捕获真实退出码`：已修 pytest/tsc，同类 DOD 管道遗漏。
- `cce9712 docs(workflow): CLAUDE.md v2.1 同步 + DOD/规则/check-step 对齐`：DOD/checker 最近调整。
- `0f64064 chore(devops): pre-commit hook 加 tasks.md 同步校验`：hook 最近结构改动。

当前工作树已有多项用户/其他任务改动，包括 `.agents/`、`backend/services/profile_settlement_service.py`、多个 task 文档和 `frontend/test-results/`。本任务不得覆盖或整理这些既有改动。

相关文件不少于 3 个：

1. `scripts/pre-commit`
2. `scripts/check-step.py`
3. `backend/tests/test_check_step.py`
4. `docs/issues.md`
5. `docs/DOD.md`

## 6. 输出建议

### 6.1 单一推荐方案

采用与现有 pytest/tsc 段一致的显式捕获模式：

```sh
set +e
check_output=$(python3 scripts/check-step.py "$step" "$file" 2>&1)
check_rc=$?
set -e
printf '%s\n' "$check_output" | tail -10
if [ "$check_rc" -ne 0 ]; then
  failed=1
fi
```

理由：

1. 兼容当前 `#!/bin/sh`。
2. 不改变整个 hook 的管道语义。
3. 不引入临时文件和 trap。
4. 与 `scripts/pre-commit` 现有 pytest/tsc 模式一致。

### 6.2 三个回归场景

| 场景 | checker 退出码 | 期望 |
|---|---:|---|
| 合法文档 | 0 | DOD 段通过 |
| 非法文档 | 非 0 | DOD 段阻断 |
| 非法文档且输出超过 10 行 | 非 0 | 仅显示末 10 行且仍阻断 |

### 6.3 路径与风险

- 推荐路径：`fix-mini`，0 调研 → 4 红测试/修复/回归 → 6 复盘。
- 🔴 当前风险：DOD checker 失败可假绿。
- 🟡 实施风险：测试若只调 checker 而不执行 Shell，会产生新的假绿测试。
- 🟢 缓解：真实执行 Shell 调用路径，保持最小改动。

## 7. 风险与缓解方案

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| 修复扩散为全 hook 重构 | 🟡 | 锁定单段修改 + 3 场景 |
| 使用 `pipefail` 破坏 `/bin/sh` 可移植性 | 🟡 | 明确排除全局 `pipefail` |
| 回归测试只证明 checker、自身不证明 hook | 🔴 | 必须真实执行 Shell 路径 |
| 覆盖当前工作树其他改动 | 🔴 | 仅写本 task 文档；实施前复核 diff |

## 8. 用户决策清单

| 日期 | 决策项 | 选择 | 状态 | 用户原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P0-1 是否按最小范围保留 | 方案 A：POSIX 显式 `output + rc` + 3 个回归场景 | ✅ 已决策 | "是" | [`decisions.md` 决策 1](decisions.md#决策-1--采用方案-a--3-个回归场景) |

## 自检清单

- [x] 任务理解与用户确认完成
- [x] 已读 `docs/issues.md`
- [x] 已运行相关 `git log -10`
- [x] 已运行 `git status`
- [x] 已定位 ≥ 3 个相关文件
- [x] 已列依赖影响与分级风险
- [x] 已给出 fix-mini 路径建议
- [x] 3 个独立 Agent 完成对抗调研并纠正报告中的 Shell 语义偏差
