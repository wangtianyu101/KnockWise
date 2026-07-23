# 复盘 · test_ci_workflow.py 旧断言修复

> 路径模式：`fix-mini` · 实施 commit：`d5c11e1`
> 决策：[`decisions.md`](decisions.md) 决策 1 · 验证：[`verify.md`](verify.md)

## 一、数据

| 维度 | 值 |
|---|---|
| 总估时 | 20 min |
| 实际耗时 | ~15 min（含 grep SHA 验证 + 写 research/decisions/tasks/verify/retro + 改 1 处函数 + commit + 跑完整 pytest 714） |
| 偏差 | 提前 25% |
| commit 数 | 1（`d5c11e1`） |
| 改动文件 | `backend/tests/test_ci_workflow.py`（+8/-4，单函数）+ `docs/tasks/.../tasks.md`（+31，新增） |
| 测试 | 22/22 PASSED（含原 6/6 test_ci_workflow · 13/13 test_check_step · 3/3 test_pre_commit_hook） + 全套 714/714 PASSED |
| 返工次数 | 0 |
| 调研偏差 | 0（research.md § 6.1 方案 A 与实施完全一致） |
| 范围控制 | ✅ 严格遵守 4 项明确排除（workflow YAML / check_action_sha.py / 重构 test_ci_workflow / 升级 SHA） |

## 二、做对的事

1. **TDD 严格执行**：跑 `pytest tests/test_ci_workflow.py` 确认修复前 1 failed 5 passed（红）；修复后 6 passed（绿）；完整 `pytest tests/` 验证无 regression（714 passed）。
2. **最小改动 + 范围锁定**：单文件单函数 ~10 行；明确不动 workflow YAML、`check_action_sha.py`、其他测试函数。
3. **决策主账同步**：decisions.md § 4.1 状态从"待实施" → 待 § 4.3 落地追踪更新；issues.md 顶部决策段待同步。
4. **grep-first 工作流**：先 grep 实际 SHA 出现位置（6 处），再 Edit 1 处函数就覆盖所有断言，避免漏改或过度断言。
5. **commit message 自带证据链**：包含修复前/后 pytest 输出对比，明确 SHA 来源（commit 66efa3c），便于未来追溯。

## 三、做错的事

1. **首次 commit 被 hook 拦下**：单 commit backend test fix 但忘了带 tasks.md，触发 § 6.5 同步校验阻断。补 tasks.md 后再次 commit 通过。**根因**：commit 前未先 `git status --short` 看 staged 列表是否有 docs/tasks/*/tasks.md。
2. **stash/pop 后续状态混乱**：v39 分支用户预先 staged 的 `profile_settlement_service.py` / `docs/issues.md` 仍在 index 中，影响我对"哪些是 staged"判断。**根因**：未先 `git status --short --branch` 看清晰。

## 四、改进项

| # | 改进 | 负责人 | 优先级 |
|---|---|---|---|
| 1 | **commit 前 checklist**：含 "docs/tasks/*/tasks.md 已 stage（如有 backend/frontend/scripts/ 改动）" | 负责人: AI 流程规则 | 🟡 高 |
| 2 | **测试函数命名约定**：R8 之后任何引用"v6"/"major"的测试函数名应改为"pinned_sha"，便于 reviewer 一眼看出策略对齐 | 负责人: AGENTS.md 规则 | 🟢 中 |
| 3 | **`scripts/ci/check_action_sha.py` 加 pytest 覆盖**（当前 CLI-only，无 pytest） | 负责人: 后续 task | 🟡 建议另开 |

## 五、沉淀（规则更新建议）

1. **新增 memory `feedback-test-vs-implementation-stale-assertion`**：R8 / 安全加固 commit 经常先改实现后改测试；新增 workflow 策略后必须同步检查所有相关测试断言，避免 v39 这种"hook 阻断所有 commit"的连带损失。
2. **更新 `feedback-pin-third-party-action-sha.md`**：补充"`test_ci_workflow.py` 等 CI 测试函数必须断言 SHA pin 而非 major version tag · R8 升级时同步 review"。

## 六、memory 更新清单

- [ ] 写 `feedback-test-vs-implementation-stale-assertion.md`（R8 / 安全加固 commit 后必查测试断言）→ 必写
- [ ] 更新 `feedback-pin-third-party-action-sha.md`（补 CI 测试断言 SHA pin）→ 选写
- [ ] 改进项 #3（`check_action_sha.py` pytest 覆盖）→ 留作新 task，不在本修复 scope