# ♻️ 调研报告 · 重构：任务状态语义与传播链

> 日期：2026-07-23 · 调研人：Claude Code + 4 个独立对抗 Agent
> 路径模式：`refactor-6`（0 → 1 → 2 → 3 → 4 → 5 → 6）
> 当前阶段：0 调研已完成 · 决策已拍板 · 未进入设计或实施

> **调研证据来源**：`docs/issues.md` 决策 #25 · 债务 #13 · `git log` 最近 30 commit + `git status` 当前 workdir（2026-07-23 15:00 末尾）

## 1. 任务理解

- **用户原话**："看下一个问题吧"；对推荐模型回复"确认"。
- **现状**：`[x]`、`✅ DONE` 同时被用于表达实现、测试、独立 verifier、阶段验证和用户验收，导致 FAILED 仍可传播为 DONE。
- **目标**：以最小正交事实模型拆分任务实施、测试、verifier 和阶段验收；禁止模糊 DONE 传播到 retro/milestones/issues。
- **边界**：本任务是流程治理重构，不并入 pre-commit 两个单点 Bug；本轮仅调研与记录决策。

## 2. 现状分析

### 2.1 规则时序冲突

- `AGENTS.md` § 6.5 要求实现任务在 commit 边界回写 `- [x] ... ✅ DONE — commit hash`。
- `AGENTS.md` § 6.7 又规定 writer commit 后才启动独立 verifier。
- 因此当前规则天然产生：先写 DONE，后发生 verifier FAIL。

### 2.2 实际传播事故

1. **V4 T29**：`tasks.md` 标 DONE，但 `verify.md` 为 Playwright 5 failed / 0 passed。
2. **V3 题库扩量**：`verify.md` 7/7 PR 和测试通过，但 `tasks.md` 大量任务仍为 `[ ]`。
3. **V4 整体**：stub commit → tasks DONE → retro 实施完成 → milestones 全部完成 → 审计发现 41 个空壳及交付失败。
4. **CI auto-fix**：verify task 标 DONE，但 L4 部分通过、L5 未做，retro 仍传播为 0-5 步完成。

### 2.3 机器校验缺口

`scripts/check-step.py::check_tasks()` 主要解析未勾选的 `- [ ] T<n>` 与 Markdown 形状，不理解已实施、测试失败、verifier blocked 等事实，也不与 `verify.md` 交叉核对。

## 3. 重构方案

### 3.1 方案比较

| 方案 | 说明 | 结论 |
|---|---|---|
| A | 保持 `[x] + DONE`，依赖现有 verifier/verify.md | ❌ 实际事故已证明传播失真 |
| B | 单一五级线性状态机 | ❌ 无法表达”已实施但测试/验证失败” |
| C | frontmatter + checkbox + table 三份状态 | ❌ 三账重复，维护和迁移成本高 |
| D | **任务级三事实 + 阶段级验收** | ✅ 用户确认 |

### 3.2 关闭条件

- [ ] Checkbox 只表达 implementation，不推导测试、验证或用户验收。
- [ ] 删除新任务格式中的裸 `DONE`。
- [ ] Task 固定记录 `test` 与 `verifier` 事实。
- [ ] `[x] + FAIL` 合法，但 `FAIL + DONE/VERIFIED/阶段完成` 非法。
- [ ] 用户验收只在阶段/step 层记录，不复制到每个原子 task。
- [ ] milestone 完成必须依赖 verify PASS + 阶段 ACCEPTED，而非 checkbox 数量。
- [ ] 新规则只强制新任务；历史文档不全量迁移。
- [ ] checker 有组合状态回归测试，不能只做 emoji/关键词匹配。

## 4. 推荐模型

### 4.1 Task 级事实

```text
implementation：pending | <commit hash>
test：NOT_RUN | PASS | FAIL | N/A
verifier：NOT_RUN | PASS | FAIL | BLOCKED | N/A
```

- `[ ]`：implementation 尚未完成。
- `[x]`：implementation 已落入 commit。
- `[x]` 可以与 test/verifier FAIL 共存，因为失败不否认实施事实。
- 新 commit 会使旧 test/verifier 证据失效，必须重新运行或标为 NOT_RUN。
- `N/A` 必须有理由，不能静默省略。

### 4.2 阶段级事实

```text
acceptance：PENDING | ACCEPTED | REJECTED
```

只有步骤 DOD 满足且用户明确确认，阶段才能 `ACCEPTED`。

### 4.3 最小正文格式

```markdown
- [x] T1: IMPLEMENTED — commit `abc1234`
  - 测试：PASS
  - 校验：FAIL — 偏差说明
```

Emoji 仅用于展示，不作为机器状态源；不在 frontmatter、checkbox、表格复制同一状态。

## 5. 依赖影响

至少涉及以下文件：

1. `AGENTS.md` § 6.5 / § 6.7
2. `docs/DOD.md`
3. `docs/templates/tasks-template.md`
4. `docs/templates/verify-template.md`
5. `docs/templates/retro-template.md`
6. `scripts/check-step.py`
7. `backend/tests/test_check_step.py`
8. `docs/rules/milestones.md`
9. `docs/issues.md`

依赖关系：先定义状态语义与传播契约，再设计 checker schema；不能先写正则再倒推业务语义。

## 6. 风险评估

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| 状态字段过多、维护负担上升 | 🟡 | 仅 3 个 task 事实 + 1 个阶段事实 |
| frontmatter/正文/表格多账漂移 | 🔴 | 正文唯一状态源，不复制 task 状态到 frontmatter |
| checker 只匹配 PASS/FAIL 关键词 | 🔴 | 解析固定字段与合法组合，增加矛盾组合测试 |
| 历史任务迁移成本巨大 | 🟡 | 新任务强制；旧文档 legacy 兼容，不全量迁移 |
| milestones 继续模糊化 FAILED | 🔴 | 完成条件改为 verify PASS + acceptance ACCEPTED |
| commit 前无法记录自身 hash | 🟡 | 设计阶段解决 commit 后回写与 verifier 时序，不在调研阶段假定实现 |

## 7. 输出建议

### 7.1 推荐路径

`refactor-6`：

```text
0 调研（当前）
→ 1 规格：定义状态与传播契约
→ 2 方案：checker/模板/兼容策略至少两案
→ 3 拆分：规则、模板、checker、测试分 commit
→ 4 TDD 实施
→ 5 L3 状态传播整合验证 + L5 新任务样例实跑
→ 6 复盘与规则退役
```

### 7.2 最小验收场景

1. `[ ] + pending + NOT_RUN + NOT_RUN` 合法。
2. `[x] + hash + NOT_RUN + NOT_RUN` 合法。
3. `[x] + hash + PASS + NOT_RUN` 合法。
4. `[x] + hash + FAIL + NOT_RUN` 合法。
5. `[x] + hash + PASS + PASS` 合法。
6. `[x] + hash + PASS + FAIL` 合法。
7. `[x]` 无 hash必须失败。
8. `[ ]` 却声明 implemented 必须失败。
9. Test FAIL + Verifier PASS 必须失败。
10. Verifier FAIL + DONE 必须失败。
11. verify FAILED + milestone completed 必须失败。
12. legacy task 不强制迁移，但走明确兼容路径。

## 8. 用户决策清单

| 日期 | 决策项 | 选择 | 状态 | 用户原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-23 | P0-5 任务状态模型 | 任务级三事实 + 阶段级验收；`[x]` 仅表示 implemented；删除裸 DONE | ✅ 已决策 | "确认" | [`decisions.md` 决策 1](decisions.md#决策-1--采用最小正交事实模型) |

## 自检清单

- [x] 已确认任务理解
- [x] 已读 `docs/issues.md`
- [x] 已检查相关近期提交与当前工作树（沿用本轮 P0 调研证据）
- [x] 已定位 ≥ 3 个相关文件
- [x] 已列依赖影响与分级风险
- [x] 已给完整 `refactor-6` 路径建议
- [x] 4 个独立 Agent 完成对抗调研
