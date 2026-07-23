# ♻️ 调研报告 · 重构：任务路径、阶段与条件产物契约

> 日期：2026-07-23 · 调研人：Claude Code + 4 个独立对抗 Agent
> 路径模式：`refactor-6`
> 当前阶段：0 调研完成 · 自动执行授权下采用单一推荐 · 未进入设计或实施

## 1. 任务理解

- **用户授权**：循环处理剩余 P0，无需逐项确认，最终提供汇总报告。
- **原问题**：任务目录缺少 `test-cases.md` 等产物，但单文件 checker 仍可通过。
- **修正后的问题定义**：项目缺少机器可读的“路径模式—当前阶段—条件触发—测试证据落点”契约；机械强制某个文件名会产生空文档假绿。
- **目标**：为正式新任务建立唯一机器契约，按当前阶段和触发条件校验真实产物与测试证据，同时解决 pre-commit 的 INDEX/WORKTREE 视图错位。

## 2. 事实证据

1. `scripts/check-step.py` 是单文件内容校验器，不检查同目录上下游产物。
2. `scripts/pre-commit` 只在某文件已 staged 时调用 checker，无法发现缺失文件。
3. pre-commit 用 staged path 触发，但 checker `open(path)` 读取 working tree，存在“检查 A、提交 B”的视图错位。
4. DOD 已定义 full-6/fix-mini/refactor-6/timebox 与 UI/API/DB 条件产物，但机器规则没有实现。
5. 历史流程几乎未实际落地独立 `test-cases.md`；测试证据常位于测试代码、tasks 内嵌契约或 verify。
6. `checklist.md` 禁止为了文档齐全生成不适用空文件。

## 3. 方案比较与关闭条件

| 方案 | 结论 |
|---|---|
| 固定目录文件列表 | ❌ 不理解当前阶段，误报合法暂停 |
| 所有任务强制 test-cases.md | ❌ 双账与空模板假绿 |
| research/decisions/frontmatter 多处复制 mode/status | ❌ 多账漂移 |
| 完整大型 manifest/事件平台 | ❌ 第一版过重 |
| **最小 task.yaml + 目录级 checker** | ✅ 自动采用 |

关闭条件：

- [ ] `task.yaml` 是 mode/current step/step state/triggers/test evidence 的唯一机器主账。
- [ ] Task 级 implementation/test/verifier 仍留在 tasks.md，不复制到 task.yaml。
- [ ] 强制真实测试证据，但不强制 `test-cases.md` 文件名。
- [ ] 当前步骤未到时，不误报后续产物缺失。
- [ ] 当前步骤 accepted 时，必需及条件产物必须存在且通过内容 validator。
- [ ] pre-commit 固定按 INDEX 视图校验。
- [ ] 新任务严格；旧任务标 `LEGACY_UNVERIFIED`，不维护永久白名单。

## 4. 最小机器契约

```yaml
schema: knockwise-task/v1
mode: full-6
current_step: 1
step_state: accepted
triggers:
  ui_design: true
  ui_components: true
  api_change: false
  db_change: false
test_evidence:
  type: pending
```

字段：

- `mode`：full-6 / fix-mini / refactor-6 / timebox。
- `current_step`：0-6；timebox 后续扩展到到期状态。
- `step_state`：in_progress / accepted / failed / blocked，与阶段双 gate 对齐。
- `triggers`：只记录 UI/API/DB 等不能由 mode 推导的条件。
- `test_evidence`：pending / code paths / tasks-inline / standalone；步骤 4 accepted 后不得 pending。

## 5. 路径与阶段闭包

- full-6：按已 accepted 的 0→6 阶段逐步要求 research、spec/product/design、plan/条件技术文档、tasks、测试证据、verify、retro。
- refactor-6：同阶段推进，但默认不要求 product-doc，非 UI 不要求 design-spec。
- fix-mini：0 accepted 要 research；4 accepted 要真实回归测试证据；6 accepted 要 retro；不机械要求 spec/plan/tasks/verify/test-cases。
- timebox：第一版只表达当前到期项，不一次实现调度器。

条件产物：

- `ui_design=true` → design-spec + mockups/index + 至少一个 HTML。
- `ui_components=true` → component-spec。
- `api_change=true` → api-spec。
- `db_change=true` → db-design。

## 6. Checker 职责

```text
check-step.py：单文件内容 validator
check-task.py：task.yaml + 阶段/条件产物/测试证据闭包
pre-commit：收集受影响目录，以 INDEX 视图调用 check-task.py
```

视图：

- `--view index`：pre-commit，使用 `git show :path`。
- `--view worktree`：手工本地检查。
- `--view head`：后续审计，可第二阶段实现。

禁止混合 INDEX manifest 与 WORKTREE 文档后报告通过。

## 7. 风险与最小验收

风险：

- 🔴 manifest 变成重复状态主账 → 仅保存阶段契约，不保存 task 状态。
- 🔴 只检查文件存在 → 继续调用 check-step 内容 validator并验证引用路径。
- 🟡 历史迁移成本 → legacy warning，不全量迁移。
- 🟡 trigger 自我漏报 → 第一版显式声明；后续与 staged diff 做有限一致性检查。
- 🟡 范围膨胀为工作流平台 → 第一版不做调度器、事件账本、evidence hash、Agent 自动调用。

最小验收场景：

1. full-6 步骤 1 in_progress 缺 plan/tasks 合法。
2. 步骤 1 accepted 缺 spec/product-doc 失败。
3. 步骤 4 accepted 且 test_evidence pending 失败。
4. fix-mini 引用真实回归测试代码，不要求 test-cases.md。
5. UI/API/DB trigger 缺条件产物分别失败。
6. test_evidence 引用不存在路径/section 失败。
7. INDEX 不合规但 WORKTREE 合规时 pre-commit 失败。
8. INDEX 合规但 WORKTREE 不合规时按 INDEX 结果处理。
9. 新目录缺 task.yaml 失败；旧目录输出 LEGACY_UNVERIFIED。
10. verify/retro 阶段顺序与 step state 矛盾时失败。

## 8. 决策清单

| 日期 | 决策项 | 选择 | 状态 | 授权原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P0-7 目录完整性方案 | 最小 task.yaml + check-task.py；强制测试证据、不强制 test-cases.md；INDEX 校验 | ✅ 自动决策 | “循环把上面哪些问题都处理一遍…不需要我确认了…最后给我一个汇总报告” | [`decisions.md` 决策 1](decisions.md#决策-1--采用最小任务契约) |

## 自检

- [x] 已读 issues/DOD/checklist/templates/checker 证据
- [x] ≥3 相关文件
- [x] 4 个独立 Agent 对抗调研
- [x] 区分未到阶段、路径跳过与真正缺失
- [x] 给出 refactor-6 路径、风险和验收矩阵
