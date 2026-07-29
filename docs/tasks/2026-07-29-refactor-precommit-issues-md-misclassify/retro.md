---
title: pre-commit 把 docs/issues.md 误判为 product-doc 边界修复 · 复盘
type: retro
step: 6
date: 2026-07-29
status: drafted
tags: [retro, refactor, governance, pre-commit, hook]
related: [research.md, decisions.md, tasks.md, test-cases.md, ../../issues.md]
---

# pre-commit 把 docs/issues.md 误判为 product-doc 边界修复 · 复盘（v1.0）

> 单步 `refactor-6` 收尾（timebox 风格）。`docs/issues.md` 状态同步已先于本任务 commit（`64d2498`）。
> 待用户处置 baseline flake（`test_metrics_endpoint` 全套顺序污染）后 commit pre-commit 修复。

---

## 1. 数据（必填 · 量化）

### 工作量
- 计划: 30 min（T1 估时）
- 实际: 约 30 min（不含 baseline flake 调查）
- 偏差: 0%

### commits
- 总数: 2（实施 commit 待落地 + docs/issues.md 同步 `64d2498`）
- 平均每个 task: 2 个

### 任务数
- 计划: 1 个（T1：缩窄 regex + 加回归测试）
- 实际完成: 1 个
- 未完成 / 推迟: 0 个（本任务 scope）· `docs/issues.md` 同步由独立 commit `64d2498` 完成

### 返工次数
- 总数: 1 次（T1 内验证轮次）
  1. 新测试 RED：先用 2026-07-* 路径，被 LEGACY_TASKS 豁免（`scripts/check_spec_base.py` `is_exempt`）→ 改用 2026-08-* 路径 → GREEN
- 原因: 调研阶段未识别 `check_spec_base.py::is_exempt` 的 LEGACY 豁免规则，导致 #3/#4 测试用例意外豁免

### 关键测试证据
- 4/4 新加回归测试 PASS（subprocess + 临时 git repo + 真实 pre-commit + 真实 checker）
- 全套治理回归 54/54 PASS（pre-commit / governance / check-task / task-state / env-gate）
- `docs/issues.md` 单独 commit 端到端通过（`64d2498`）

---

## 2. 做对的事（必填 · 可复用经验）

- ✅ **D-003 缩窄 regex 而非 hack docs/issues.md**：边界缩小而非扩大，不引入新攻击面。真 product-doc（`docs/templates/product-doc-template.md` + `docs/tasks/<date>/product-doc.md`）仍受保护。可沉淀为"hook 边界错误优先缩窄 regex，不给被误分类的文档加 hack"的治理准则。

- ✅ **真实 subprocess + 临时 git repo 回归测试**：用 `subprocess.run(["sh", "scripts/pre-commit"], cwd=tmp, ...)` 跑真实 pre-commit + 临时 git repo + 真实 checker，覆盖 4 个场景（核心 / 边界 1 / 边界 2 / 混合 commit）。可沉淀为 `scripts/check_spec_base.py` 反模式清单。

- ✅ **调研阶段完整预判**：research.md § 二根因分析精准命中第 220 行 regex；§ 三影响与依赖列出 3 文件；§ 四风险分级 + 缓解；§ 五安全审查 4 道关全部对齐。可沉淀为"refactor 任务的研究模板"（已具备，只需按 § 0.2 清单执行）。

- ✅ **分阶段 commit 策略**：docs/issues.md 单独 commit（不触发 backend pytest）→ pre-commit 修复后续 commit（避免 baseline flake 阻断债务 24 收尾）。可沉淀为"hook 改动 + 被 hook 误拦的文档 = 分阶段 commit"模式。

- ✅ **`docs/issues.md` 同步前置**：债务 24 retro 起草时立即把 issues.md 顶部决策段 + § 三章节 + 决策更新段同步，与债务 24 收尾的 retro.md 闭环。可沉淀为"commit 顺序：先 commit 议题主账 + 后 commit 治理工具改动"（避免 hook 改动卡住文档同步）。

- ✅ **D-003 决策即时写 decisions.md**：按 § 6.9 必备 4 段结构（顶部权威定位 / 决策总览 / 决策详细记录 / 决策落地追踪），含用户原话"「A」" + 4 条理由 + 影响文件 + 关联决策。

---

## 3. 做错的事（必填 · 根因分析）

- ❌ **调研阶段未识别 `check_spec_base.py::is_exempt` 的 LEGACY 豁免规则**：
  - **现象**：T1 实施时新测试 #3/#4 用 `docs/tasks/2026-07-29-test/product-doc.md` 路径，被 `LEGACY_TASKS = re.compile(r"^docs/tasks/2026-07-\d{2}-")` 命中 → `is_exempt` 返回 True → checker 不校验 → 误判"边界保留"通过。
  - **根因**：research.md § 二根因只看了 pre-commit regex，没看 check-product-doc.py 的依赖链（`check_spec_base.py::is_exempt`）。调研 checklist 缺"依赖链路下游豁免规则"维度。
  - **影响**：第一次跑新测试 2/4 失败，返工 5 min 改用 2026-08-* 路径。返工不算大，但暴露调研模板漏洞。

- ❌ **pre-commit fail closed 副作用：baseline flake 阻断本任务 commit**：
  - **现象**：`scripts/pre-commit:46-49` 跑 `cd backend && ./.venv/bin/python -m pytest tests/ --tb=short -q` 全套 backend 测试。`test_metrics_endpoint::test_returns_timings_after_timing_call` 单独跑 PASS，全套跑 FAIL（测试顺序污染）。与本次改动完全无关，但 fail closed gate 阻断 pre-commit + tests 改动 commit。
  - **根因**：pre-commit 设计假设"backend pytest 全绿 = 安全"，但实际 backend pytest 有 baseline flake（v40 治理已发现 866 passed + 多个 xfail 留待后续）。pre-commit 不区分"本次改动引入的失败 vs baseline 残留"。
  - **影响**：refactor 修复无法落地；用户必须先处置 baseline flake（标 xfail 或修测试），才能 commit。

- ❌ **调研 § 七方案比较未提"分阶段 commit"策略**：
  - **现象**：方案 A 正确选择缩窄 regex，但实施时才发现需要"docs/issues.md 单独先 commit"才能让 pre-commit 修复后续 commit 不被 baseline flake 拦。
  - **根因**：方案比较只评估技术路径（regex vs hack vs skip），未评估"commit 时序"风险。
  - **影响**：实施中临时调整 commit 顺序（unstage pre-commit + 单独 commit docs/issues.md），增加了 1 次额外 commit。

### 3.1 失效链五问（针对"hook fail closed 副作用"严重问题）

```text
需求/Writer → 测试 oracle → pre-commit (fail closed) → Verifier → 文档状态
```

- **本层本应阻断什么**：pre-commit 应阻断"本次改动引入的真实失败"，而不是阻断"baseline pre-existing flake"。
- **为什么没阻断**：pre-commit 第 46-49 行无条件跑 backend pytest 全套，不区分 baseline vs 本次。
- **上游信号如何被错误解释**：1 个 baseline flake 与"pre-commit regex 修复生效"是独立事件，但 fail closed 把它们耦合在一起。
- **哪条机器约束能让同类问题下次自动失败**：
  1. pre-commit 跑 pytest 时加 `--deselect <baseline_xfail_list>` 跳过已知 baseline flake
  2. 把 baseline flake 全部标 xfail（v40 治理已部分执行）
  3. pre-commit 改为"只跑 changed files 相关测试"（按 § 0.2.1 风险范围感知）
- **根因终点的判断**：根因不是"AI 粗心"或"baseline 没清"，而是"pre-commit fail closed gate 没有 baseline 容忍机制"。

---

## 4. 改进项（必填 · 必须分配）

- [ ] 改进 1: 调研阶段清单增加"依赖链路下游豁免规则"维度（识别 `check_spec_base.py::is_exempt` 这类被引用模块的边界规则）
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-05
  - 沉淀到: `docs/templates/research-template.md` § 二（根因分析）+ `scripts/check-step.py` research 校验

- [ ] 改进 2: 调研阶段方案比较增加"commit 时序"评估维度（识别 hook 改动 + 被 hook 误拦文档的耦合关系）
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-05
  - 沉淀到: `docs/templates/research-template.md` § 六（方案比较）

- [ ] 改进 3: 处置 `test_metrics_endpoint::test_returns_timings_after_timing_call` baseline flake（标 xfail 或修测试）
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-01
  - 沉淀到: `backend/tests/test_metrics_endpoint.py`（标 xfail 或修）+ `docs/issues.md` 债务 25（baseline flake 处置）

- [ ] 改进 4: pre-commit 风险范围感知的 fail closed gate 升级（区分 baseline vs 本次改动）
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-12
  - 沉淀到: `scripts/pre-commit` 第 1 段（环境 Gate 已部分实现）+ `docs/rules/pre-commit-gate.md`

- [ ] 改进 5: 治理 hook 改动走"分阶段 commit"标准模式（先 commit 议题主账 + 后 commit hook 改动）
  - 负责人: @wangtianyu（用户）
  - 截止: 2026-08-08
  - 沉淀到: `AGENTS.md` § 6.5（任务完成自动更新）+ `docs/templates/refactor-hook-template.md`（新增）

---

## 5. 沉淀到哪（必填）

- [ ] 已更新 CLAUDE.md（<哪节>）—— 未直接更新（CLAUDE.md § 6.10 / § 6.11 已具备治理基础；本任务合规使用）
- [ ] 已更新 docs/DOD.md（<哪步>）—— 未直接更新（DOD.md § 八 6 步复盘 DOD 已具备；本任务按其执行）
- [x] 已更新 <某个模板>（<哪段>）—— 改进 1/2 计划更新 `docs/templates/research-template.md`（2026-08-05 前）
- [x] 已新增议題到 docs/issues.md —— `64d2498` 已 commit，债务 24 ✅ + 债务 23 用户授权进入步骤 1 规格
- [x] 已新增 memory 候选：`feedback-hook-boundary-shrink-not-hack.md`（"hook 边界错误优先缩窄 regex，不给被误分类文档加 hack"）+ `feedback-staged-commit-for-hook-changes.md`（"hook 改动 + 被误拦文档 = 分阶段 commit"）（待写）

### 5.1 规则落地证据

| 失败模式 | 新规则/脚本 | 触发时机 | 失败表现 | 验证状态 |
|---|---|---|---|---|
| docs/issues.md 误被 product-doc 校验拦下 | `scripts/pre-commit:220` regex 缩窄 | commit 边界 pre-commit | hook 通过（`64d2498` 已 commit 验证） | 已验证（端到端 commit `64d2498`） |
| 真 product-doc（template / task instance）绕过校验 | 4 个回归测试在 `backend/tests/test_pre_commit_hook.py` | 测试套件 | 4/4 GREEN | 已验证（本地 pytest） |
| 调研阶段漏掉 `check_spec_base.py::is_exempt` 豁免 | 改进 1（research-template § 二 + check-step.py）| 调研阶段 0 步 | check-step.py research 校验失败 | 待验证（改进 1 · 截止 2026-08-05） |
| pre-commit fail closed 阻断 baseline flake | 改进 4（pre-commit 风险范围感知升级）| commit 边界 pre-commit | baseline flake 不再阻断 | 待验证（改进 4 · 截止 2026-08-12） |
| hook 改动与被误拦文档耦合 commit 失败 | 改进 5（分阶段 commit 标准模式）| commit 阶段 | 先 commit 议题主账 + 后 commit hook | 待验证（改进 5 · 截止 2026-08-08） |

> 只写"建议增加"不算沉淀；必须给出文件位置。尚未实测的新规则标记"待验证"，不得写成已生效。

---

## 6. 元信息与关联任务

- **路径模式**：`refactor-6`
- **commits**：`64d2498`（docs/issues.md 同步已落地）+ 本次实施 commit（待 baseline flake 处置后落地）
- **测试**：4/4 新加回归 + 全套治理回归 54/54 + 端到端 commit 验证
- **独立 verifier**：待 commit 落地后由新 Agent prompt 固定 commit 校验
- **L5**：BLOCKED（用户自执行 baseline flake 处置 + commit）
- **关联任务**：
  - 上游触发：债务 24 收尾（[`tasks/2026-07-28-p0-ci-autofix-execution-breaks/retro.md`](../2026-07-28-p0-ci-autofix-execution-breaks/retro.md)）
  - 关联改进：v40 pytest 环境整治（`docs/issues.md` 顶部 v40 段 · 0 failed + 15 xfailed 留待后续）
- **用户验收**：
  - D-003（缩窄 regex）：✅ 已决策
  - 步骤 4 实施 + 4/4 测试 PASS + 54/54 治理回归：✅ 已完成
  - pre-commit 修复 commit：⏳ BLOCKED（baseline flake 处置）