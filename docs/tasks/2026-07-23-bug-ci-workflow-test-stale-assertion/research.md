# 🐛 调研报告 · Bug：test_ci_workflow.py 旧断言与 R8 SHA pin 策略冲突

> 日期：2026-07-23 · 调研人：Claude Code · 紧急度：P0-1'（接 P0-1 之后的下一票）· 路径模式：`fix-mini`

## 1. 任务理解

- **用户原话**："2"（针对"v39 test_ci_workflow 旧断言 `@v6` 与 R8 SHA pin 策略冲突 —— 建议另开 task"）；对推荐范围回复"最小修复（推荐）"。
- **现象**：`backend/tests/test_ci_workflow.py::test_ci_uses_current_official_action_majors_and_read_only_permissions` 断言 `actions/checkout@v6` / `actions/setup-python@v6` / `actions/setup-node@v6`，但 R8 commit `66efa3c` 已把所有第三方 Action 改成 pin 完整 40 字符 SHA。
- **期望**：测试断言与 R8 实际一致 —— 验证 SHA pin 而非 major version tag；测试名也应反映新策略。
- **任务边界**：仅改 `backend/tests/test_ci_workflow.py` 一个函数 + 名字；不动 workflow YAML、不动 `scripts/ci/check_action_sha.py`、不重构整个测试文件。

## 2. 复现路径

### 2.1 复现步骤

```bash
cd backend && .venv/bin/python -m pytest tests/test_ci_workflow.py::test_ci_uses_current_official_action_majors_and_read_only_permissions -v
```

输出：

```
>       assert "actions/checkout@v6" in content
E       assert 'actions/checkout@v6' in '... actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 ...'
tests/test_ci_workflow.py:58: AssertionError
FAILED tests/test_ci_workflow.py::test_ci_uses_current_official_action_majors_and_read_only_permissions
```

### 2.2 触发条件

- v39 分支上 commit `66efa3c`（R8 · 2026-07-22）后，任何跑 `pytest backend/tests/test_ci_workflow.py` 的环境都会触发这个失败。
- 因 `pytest` 在 `pre-commit` hook 中跑（修改 backend/ 时），blocking commit。

### 2.3 稳定性

- 静态可重复：workflow YAML 已固化 6 个 SHA pin，测试断言锁死 `@v6`，二者不会自动同步。
- 影响范围：v39 分支上的所有 backend/ 改动 commit 都被 hook 阻断（用户已受影响，retro §3 已记）。

## 3. 影响范围与关闭条件

### 3.1 影响范围

- **直接文件**：`backend/tests/test_ci_workflow.py:54-60`（一个函数 + 6 行断言 + 函数名）。
- **流程影响**：unblock v39 分支所有 backend/ commit；与 pre-commit hook 配合（hook 已修 P0-1，不再假绿）。
- **数据影响**：无业务数据；纯测试断言。
- **依赖影响**：依赖 `scripts/ci/check_action_sha.py` 已知的 3 个 40 字符 SHA（checkout / setup-python / setup-node）。

### 3.2 关闭条件

- [ ] 函数重命名为反映 SHA pin 策略（如 `test_ci_uses_pinned_action_shas_and_read_only_permissions`）
- [ ] 删除 3 条 `@v6` 断言
- [ ] 加 6 条 SHA pin 断言（覆盖 ci.yml 与 auto-fix-ci.yml 的所有 6 处出现）
- [ ] 保留 `permissions:\n  contents: read` 断言
- [ ] `pytest tests/test_ci_workflow.py` 6/6 PASSED
- [ ] 不动 workflow YAML / `check_action_sha.py` / 其他测试函数

## 4. 根因假设与对抗核验

| 假设 | 证据 | 结论 |
|---|---|---|
| H1：R8 commit `66efa3c` 改 workflow 但没同步更新 test_ci_workflow.py | `git show 66efa3c --stat` 只改 `.github/workflows/ci.yml`，未动测试文件 | ✅ 主根因 |
| H2：应回滚 R8 commit 恢复 @v6 | R8 是 security/可重复性决策（[`feedback-pin-third-party-action-sha`](~/.claude/projects/.../feedback-pin-third-party-action-sha.md)）；决策 7 全拍 | ❌ 已反驳，方向相反 |
| H3：测试应同时断言 SHA pin + read-only permissions | R8 策略同时强化两者 | ✅ 推荐做法 |
| H4：应同时给 `check_action_sha.py` 加 pytest 覆盖 | 修复范围最小化原则，且 `check_action_sha.py` 当前是 CLI-only，不在本任务 scope | ⏸ 不在本任务 |

## 5. 最近相关改动与仓库状态

执行证据：

```bash
git show 66efa3c --stat
grep -n "uses: actions/" .github/workflows/ci.yml .github/workflows/auto-fix-ci.yml
ls scripts/ci/check_action_sha.py
pytest backend/tests/test_ci_workflow.py::test_ci_uses_current_official_action_majors_and_read_only_permissions -v
```

相关 commit：

- `66efa3c ci: pin 3rd-party Actions to full SHA (FU-2 / R8)` — 已修 workflow，未同步更新测试。
- `4648d50 ci(auto-fix): FU-3 关 2 改进 · diagnostic 完全无 LLM + secrets` — 同期 CI 安全加固。
- `9d8ecbc docs(verify): 同步 v3 关 2 改进（diagnostic 无 secrets）` — 同期文档。

工作树当前状态：v39 分支上有其他用户 staged 改动（`profile_settlement_service.py`、`docs/issues.md`、`.agents/skills/...`），本任务不动它们。

相关文件 ≥ 3 个：

1. `backend/tests/test_ci_workflow.py`（要改）
2. `.github/workflows/ci.yml`（参考 — 不动）
3. `.github/workflows/auto-fix-ci.yml`（参考 — 不动）
4. `scripts/ci/check_action_sha.py`（参考 — 不动）
5. `docs/issues.md`（同步 — 第 27 / 65 行状态字段）

## 6. 输出建议

### 6.1 单一推荐方案

最小修改 `test_ci_workflow.py:54-60` 一个函数：

```python
def test_ci_uses_pinned_action_shas_and_read_only_permissions():
    content = workflow_text()

    assert "permissions:\n  contents: read" in content
    # R8 / Decision 7: third-party Actions 必须 pin 40-char SHA（非 @v6 / @beta）
    assert "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" in content
    assert "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1" in content
    assert "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38" in content
```

注：3 个 SHA 在 ci.yml / auto-fix-ci.yml 共出现 6 次，但 `assert "X" in content` 用 `in` 是 substring 检查，重复出现也只命中 1 次 —— 1 个 SHA 1 个断言足够覆盖全工作流。

### 6.2 回归场景

| 场景 | 期望 |
|---|---|
| 1. 跑 `pytest tests/test_ci_workflow.py` | 6/6 PASSED（含重命名后的 1 个 + 原 5 个） |
| 2. workflow YAML 中 SHA 被改回 `@v6` | 测试 FAIL（保护 R8 策略不退化） |
| 3. workflow YAML 删除 SHA pin | 测试 FAIL |

### 6.3 路径与风险

- 推荐路径：`fix-mini`（0 调研 → 4 实施 → 6 复盘）。
- 🟢 风险：测试断言 SHA 硬编码 · 未来 R8 升级 SHA 时需同步改测试。
- 🟢 缓解：commit message 注明 SHA 来源（commit 66efa3c），并交叉引用 `scripts/ci/check_action_sha.py` 作为机器化检查兜底。

## 7. 风险与缓解方案

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| SHA 硬编码未来需更新 | 🟢 | `check_action_sha.py` 已机器化强制 pin，SHA 升级路径已有先例（commit 66efa3c 的 commit message） |
| 测试函数名误导（仍含 "majors"） | 🟢 | 改名为 `test_ci_uses_pinned_action_shas_and_read_only_permissions` |
| 其他测试函数也需要更新 | 🟢 | 已 review：其他 5 个测试与 R8 无关，全部继续 PASS |

## 8. 用户决策清单

| 日期 | 决策项 | 选择 | 状态 | 用户原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | v39 test_ci_workflow 修复范围 | ✅ 最小修复（仅改 test_ci_workflow.py 一个函数 + 名字） | ✅ 已决策 | "拍 D" / "最小修复（推荐）" | [decisions.md 决策 1](decisions.md#决策-1--最小修复范围) |

## 自检清单

- [x] 任务理解与用户确认完成
- [x] 已读 `docs/issues.md`（P0-1 决策已同步 · R8 commit 66efa3c 已识别）
- [x] 已运行相关 `git log / git show 66efa3c`
- [x] 已运行 `git status`（v39 分支）
- [x] 已定位 ≥ 3 个相关文件（5 个）
- [x] 已列依赖影响与分级风险（🟢 全部）
- [x] 已给出 fix-mini 路径建议
- [x] 已跑红测试确认 RED（`test_ci_uses_current_official_action_majors_and_read_only_permissions` FAIL · 错误为 `assert 'actions/checkout@v6' in content` 实际含 `@d23441a48e...`）