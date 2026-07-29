---
title: CI auto-fix 三项执行断链 · 测试用例
type: test-cases
step: 4
date: 2026-07-28
status: in-progress
tags: [p0, tests, github-actions, git]
related: [research.md, tasks.md]
---

# CI auto-fix 三项执行断链 · 测试用例

## 0. 测试策略

- **自动化覆盖率目标**：三项 P0 风险场景 ≥ 80%；TC-001～TC-010 当前全部有自动化证据，达到 100%。
- **L1 contract**：解析生产 workflow，验证真实 Action input、step id、index/commit 命令。
- **L2 behavior**：在临时 Git 仓库运行生产等价的 `git apply --index` 和 cached diff checker。
- **L3 regression**：auto-fix E2E、安全 E2E、governance、Action provenance。
- **L5**：真实 GitHub workflow run 创建 Draft PR；本地无法替代时明确 BLOCKED。
- 禁止只用 grep “关键字存在”作为三项 PASS 的唯一证据。

## 1. 验收测试

| ID | 层级 | 场景 | 输入/前置 | 预期 |
|---|---|---|---|---|
| TC-001 | L1 | prompt 无 shell 假展开 | 生产 workflow | 不含 `$(jq` |
| TC-002 | L1 | prompt 使用结构化 output | `failed_job/error_code` | Action `prompt` 引用真实 step output |
| TC-003 | L1/Security | raw-prefix key_string | 恶意 CI log 前 200 字符 | 不进入 Claude prompt |
| TC-004 | L1 | branch step identity | 创建分支步骤 | `id: create-branch` |
| TC-005 | L1 | branch output 消费者 | push + Draft PR | 两处引用同一 `new_branch`，非空断言存在 |
| TC-006 | L2 | patch 修改 tracked 文件 | 临时 Git repo | 只把 patch 指定修改 stage |
| TC-007 | L2 | patch 新增/删除文件 | 临时 Git repo | 新增/删除均正确 stage |
| TC-008 | L2/Security | workspace 有 patch.diff 与无关文件 | temp repo | 两者均不在 cached diff/commit |
| TC-009 | L2 | diff policy | staged service/test files | 从 cached diff 得到正确 needs_review/test_files |
| TC-010 | L3 | 旧回归 | auto-fix/security/governance/provenance | 全绿，无 Action ref 回退 |

## 2. 红灯判定

旧实现必须至少出现：

- TC-001：检测到三个 `$(jq ...)`。
- TC-004：创建分支步骤无 id。
- TC-008：`git add -A` 会 stage `patch.diff`。
- TC-009：diff checker 读取 `HEAD~1` 而不是 cached diff。

若新增测试在旧实现上不红，测试 oracle 不合格，禁止进入实现。

## 3. 自动化命令

```bash
backend/.venv/bin/python -m pytest backend/tests/test_auto_fix_workflow.py -q
python3 scripts/ci/test_check_auto_fix_diff.py
bash scripts/ci/test_auto_fix_e2e.sh
bash scripts/ci/test_security_e2e.sh
backend/.venv/bin/python -m pytest \
  backend/tests/test_ci_workflow.py \
  backend/tests/test_check_governance.py \
  backend/tests/test_task_governance_gate.py -q
python3 scripts/ci/check_action_sha.py --verify-remote --timeout 15
```

## 4. 故意破坏反证

1. 把 prompt 改回 `$(jq ...)`，TC-001 必须失败。
2. 删除 `id: create-branch`，TC-004/005 必须失败。
3. 恢复 `git add -A`，TC-008 必须失败。
4. 把 diff checker 改回 `HEAD~1`，TC-009 必须失败。

## 5. 当前状态

| 阶段 | 结果 |
|---|---|
| baseline 生产行为 | 三项 FAIL |
| baseline 旧测试 | 假绿 |
| 新回归 RED | PASS（7 failed，命中三条断链与 cached diff） |
| 修复后 GREEN | PASS（8 workflow + 7 checker + 31 扩展 pytest + Shell E2E） |
| L5 GitHub run | BLOCKED（用户自行操作远端；本任务不操控 GitHub） |
