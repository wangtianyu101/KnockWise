# 复盘 · pre-commit DOD checker 退出码修复

> 路径模式：`fix-mini` · 实施 commit：`d91fdef` + `ee6da13`
> 决策：[`decisions.md`](decisions.md) 决策 1 · 验证：[`verify.md`](verify.md)

## 一、数据

| 维度 | 值 |
|---|---|
| 总估时 | 70 min |
| 实际耗时 | ~30 min（包含 2 次 staging 混乱 + 1 次 smoke 误 commit + 1 次 stash/pop） |
| 偏差 | 提前 57% |
| commit 数 | 2（`d91fdef` + `ee6da13`） |
| 改动文件 | `scripts/pre-commit`（+7/-1）、`backend/tests/test_pre_commit_hook.py`（+238，新增）、`docs/tasks/.../tasks.md`（+31，新增） |
| 测试 | 16/16 PASSED（3 新 + 13 既有 `test_check_step.py`） |
| 返工次数 | 1（VALID_RESEARCH_MD 缺 `## N. 输出建议` 段导致首次场景 1 RED；tasks.md 初稿用表格格式不满足 `- [ ] T\d+` regex） |
| 调研偏差 | 0（research.md § 6.1 方案 A 与实施完全一致） |
| 范围控制 | ✅ 严格遵守 5 项明确排除（环境 fail-closed / hook 安装 / pipefail / check_retro / hook 重构） |

## 二、做对的事

1. **TDD 严格执行**：先写测试，验证修复前 RED（场景 2/3 假绿），修复后 GREEN。3 个测试用 `subprocess.run` 真实跑 `sh scripts/pre-commit`，无 mock，覆盖完整 Shell 调用路径。
2. **最小改动**：仅修改 `scripts/pre-commit` 一段 8 行，与同文件 pytest/tsc 段模式一致 — 认知成本最低、引入风险最低。
3. **决策落地追踪**：decisions.md § 4.1 状态从"待实施" → "✅ 已落地（commit `d91fdef` + `ee6da13`）"，§ 4.3 补落地补充。
4. **独立 verifier 校验**：按 § 6.7 commit 级 verify 用全新 prompt 开 agent 跑 A/B/C/D 四维度校验，全部 PASS。

## 三、做错的事

1. **Smoke 误 commit**：手动 smoke 测试故意把不合规文档暂存时，没意识到 `git add` 会带上用户预先 staged 的 4 个 `.agents/skills/...` 文件，触发了一次 5 文件误 commit。立即 `git reset --soft HEAD~1` + `git restore --staged` 撤回，无残留。**根因**：未先 `git status -sb` 看 staged 列表。
2. **`git stash` 误伤用户**：调查 pre-existing pytest failure 时 `git stash` 把用户的 staged 改动（`profile_settlement_service.py`、`docs/issues.md`）一起 stash 走了。后来 `git stash pop` 恢复，但中间 staging 区短暂处于"丢失"状态 — 用户的工作被打断。**根因**：stash 命令无差别打包所有改动，应先 `git stash --keep-index` 或备份。
3. **测试 fixture 数据疏漏**：VALID_RESEARCH_MD 初稿缺 `## N. 输出建议` 段，导致场景 1 修复后 RED（hook 真的检查了，发现文档不合规）。补段后 GREEN。**根因**：未跑测试前先 `python3 scripts/check-step.py research <tmp_md>` 自检 fixture。
4. **tasks.md 初稿用表格**：用 markdown 表格写任务清单，不满足 `check_tasks` 的 `- [ ] T\d+` regex。改回 `- [ ] T1:` 列表格式才通过。**根因**：未跑 `python3 scripts/check-step.py tasks <tasks.md>` 自检。

## 四、改进项

| # | 改进 | 负责人 | 优先级 |
|---|---|---|---|
| 1 | **smoke 测试前先 `git status -sb`** 看清 staged 列表，避免误 commit 用户文件 | AI 流程规则 | 🟡 高 |
| 2 | **stash 前评估影响**：commit 前诊断用 `git stash --keep-index` 或直接 `git restore --staged <single_file>` | AI 流程规则 | 🟡 高 |
| 3 | **测试 fixture 自检**：写 pytest fixture 前先 CLI 跑一次 checker 验证合规 | AI 流程规则 | 🟢 中 |
| 4 | **v39 pre-existing pytest failure `test_ci_workflow.py`**：断言 `@v6` 但已 pin SHA per R8 commit 66efa3c — 需更新测试或重新设计（assert SHA pin 而非 version tag） | @v39-ci-autofix owner | 🟡 建议另开 task |
| 5 | **AGENTS.md / `feedback-stub-test-debt` 提到**：本修复的 3 个 pytest 是真实 `subprocess` 跑 hook，不是 stub — 验证通过 ✅ | （已避免） | — |

## 五、沉淀（规则更新建议）

1. **新增 memory `feedback-pipe-exit-code-bug-in-sh`**：POSIX `#!/bin/sh` 管道默认取末端退出码，`! cmd1 | cmd2` 判断的是 cmd2 的退出码 → 任何"判断前置命令失败 + 后置命令展示输出"场景必须用 `set +e` + 变量捕获 rc 模式。与 `pytest/tsc` 段同样的修复路径。
2. **更新 AGENTS.md § 6.3 自检清单**：在"边界值 / 异常输入有测试"项后追加："[ ] Shell/管道退出码测试：若修改 hook 或含管道命令，必须有断言 rc 的回归测试（subprocess 真实执行，不只 mock）。"
3. **更新 AGENTS.md § 6.5 任务完成自动更新**：在 commit 前"立即回写 tasks.md"步骤后追加："[ ] tasks.md 通过 `python3 scripts/check-step.py tasks <path>` 自检（避免提交后才被 hook 拦下）。"

## 六、memory 更新清单

- [ ] 写 `feedback-pipe-exit-code-bug-in-sh.md`（POSIX sh 管道退出码陷阱 + 修复模式）→ 必写
- [ ] 写 `feedback-smoke-test-preserve-staged.md`（smoke 测试前先 `git status -sb`，避免误 commit 用户文件）→ 必写
- [ ] 写 `feedback-stash-keeps-user-changes.md`（诊断时 stash 用 `--keep-index`，避免吞掉用户 staged 改动）→ 必写
- [ ] 写 `feedback-test-fixture-selfcheck.md`（pytest fixture 自检：CLI 跑一次 checker 验证合规）→ 必写
- [ ] 更新 `feedback-pin-third-party-action-sha.md`：补充"`test_ci_workflow.py` 旧测试仍断言 `@v6`，v39 修复时需同步更新" → 选写