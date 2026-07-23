---
title: 任务路径/阶段/条件产物契 · 任务拆分
type: tasks
step: 3
date: 2026-07-23
status: draft
tags: [refactor, governance, contract, task-yaml, checker, tasks]
related:
  - research.md
  - spec.md
  - plan.md
  - decisions.md
---

# 任务拆分 · 任务路径/阶段/条件产物契（P0-7）

> 路径模式：refactor-6
> 1 步 spec + 2 步 plan 已落地
> 路径：4 步 TDD（先红后绿）+ 6 步 verify + 7 步 retro

---

## 任务总览

| ID | 任务 | 估时 | 状态 | commit | 依赖 |
|---|---|---|---|---|---|
| T1 | test_check_task.py 失败用例先行 | 30 min | 🔴 待做 | — | 无 |
| T2 | check-task.py 最小实现 | 45 min | 🔴 待做 | — | T1 |
| T3 | pre-commit INDEX 视图集成 | 30 min | 🔴 待做 | — | T2 |
| T4 | task-yaml-template + 本任务 task.yaml | 20 min | 🔴 待做 | — | T2 |
| T5 | 12 老任务白名单 + 归档豁免 | 20 min | 🔴 待做 | — | T2 |
| T6 | 全套回归（pytest + pre-commit 端到端）| 30 min | 🔴 待做 | — | T3-T5 |

**总估时**：2h 55min · 与 1h/任务预算接近 · 适合单 AI 工作日

---

## 任务依赖图

```text
T1 (test fail)
 │
 ▼
T2 (impl pass) ─────┐
 │                  │
 ├──► T3 (hook)     ├──► T6 (regression)
 ├──► T4 (template) ┤
 └──► T5 (exempt)  ┘
```

---

## T1 · test_check_task.py 失败用例先行

### 描述
按 spec § 7 写 10 个失败用例，验证 `check-task.py` 主流程。

### 输入
- `backend/tests/test_check_task.py`（新建 · 200 行）
- 10 个 fixture YAML 文件（`backend/tests/fixtures/task-yaml/`）

### 步骤
1. 创建 `backend/tests/fixtures/task-yaml/` 目录
2. 创建 10 个 fixture YAML（valid_minimal / valid_full_ui / invalid_missing_mode / invalid_step_out_of_range / invalid_step_4_pending / invalid_task_id_mismatch / invalid_trigger_ui_design / invalid_step_state_no_verify / invalid_mode_unknown / invalid_schema_version）
3. 写 `test_validate_*` 系列 10 个函数（每函数 1 个 fixture）
4. 写 `test_is_exempt` 2 个函数（老任务 + 归档）
5. 写 `test_read_task_yaml_index_view` 1 个函数（用 `git init` 创建临时 repo）

### 预期（红）
```bash
$ pytest backend/tests/test_check_task.py
ModuleNotFoundError: No module named 'check_task'
```

### 估时
30 min

### 验证
```bash
pytest backend/tests/test_check_task.py
# exit 5 (ModuleNotFoundError)
```

---

## T2 · check-task.py 最小实现

### 描述
按 plan § 2.2 写 `scripts/check-task.py` ~250 行，让 T1 全部变绿。

### 输入
- `scripts/check-task.py`（新建）

### 步骤
1. 创建 `scripts/check-task.py`
2. 实现 argparse（接受 `--dir` + `--view {index,worktree}`）
3. 实现 `read_task_yaml()`（INDEX 视图用 `git show :path`）
4. 实现 `validate()`（spec § 1 8 项 error code）
5. 实现 `list_dir_artifacts()`（INDEX 用 `git ls-tree -r --name-only`）
6. 实现 `is_exempt()`（regex 匹配 EXEMPT_PATHS）
7. 主入口 + 退出码

### 预期（绿）
```bash
$ pytest backend/tests/test_check_task.py
10 passed
$ pytest backend/tests/
# 722+ passed
```

### 估时
45 min

### 验证
```bash
pytest backend/tests/        # 全绿
```

### 依赖
- T1（先红）

---

## T3 · pre-commit INDEX 视图集成

### 描述
在 `scripts/pre-commit` 真实安装版（不是仓库内模板）加 5 行 case 调用 `check-task.py`。

### 输入
- 当前 pre-commit 真实安装位置（`~/.git/hooks/pre-commit` 或 `.claude/hooks/`）
- 仓库内 `scripts/pre-commit` 模板

### 步骤
1. 复制 `scripts/pre-commit:108` case 分发表
2. 加 5 行：
   ```sh
   docs/tasks/*/task.yaml)
     python3 scripts/check-task.py --dir "$(dirname "$file")" --view index
     ;;
   ```
3. 同步更新仓库内 `scripts/pre-commit` 模板（用一致内容）
4. 测试：mock commit 含 backend 改动 + 合法 task.yaml → 跑 hook → 通过
5. 测试：mock commit 含 backend 改动 + 缺 task.yaml → 跑 hook → 阻断
6. 测试：mock commit 含 docs 改动 → 不触发 task contract 校验

### 预期
- 合法 task.yaml + 实施代码 → hook 通过
- 缺 task.yaml → hook 阻断 + 友好错误信息
- 纯 docs commit → hook 不触发

### 估时
30 min

### 验证
```bash
# mock commit
git init /tmp/test-repo
cd /tmp/test-repo
mkdir -p docs/tasks/2026-07-24-test-task
cat > docs/tasks/2026-07-24-test-task/task.yaml <<EOF
schema: task/v1
task_id: 2026-07-24-test-task
mode: full-6
current_step: 1
step_state: in_progress
triggers:
  ui_design: false
  ui_components: false
  api_change: false
  db_change: false
test_evidence:
  type: pending
EOF
git add .
git commit -m "test"  # 应通过
```

### 依赖
- T2（实现存在）

---

## T4 · task-yaml-template + 本任务 task.yaml

### 描述
创建 `task-yaml-template.yaml` 模板 + 本任务自身的 `task.yaml`（自我示范）。

### 输入
- `docs/templates/task-yaml-template.yaml`（新建）
- 本任务 `task.yaml`（新建）

### 步骤
1. 创建 `docs/templates/task-yaml-template.yaml`（按 spec § 3 模板）
2. 创建本任务 `task.yaml`：
   ```yaml
   ---
   schema: task/v1
   task_id: 2026-07-23-refactor-task-artifact-contract
   mode: refactor-6
   current_step: 3
   step_state: in_progress
   triggers:
     ui_design: false
     ui_components: false
     api_change: false
     db_change: false
   test_evidence:
     type: code
     path: backend/tests/test_check_task.py::test_minimal_task_yaml_valid
   metadata:
     created: 2026-07-23
     author: user
     related:
       - research.md
       - spec.md
       - plan.md
       - decisions.md
   ---
   ```
3. 跑 `python3 scripts/check-task.py --dir docs/tasks/2026-07-23-refactor-task-artifact-contract --view index` → 应通过

### 预期
- 模板文件存在
- 本任务 task.yaml 通过校验
- 其他 4 步更新（research.md / spec.md / plan.md / decisions.md）已存在

### 估时
20 min

### 依赖
- T2（实现存在）

---

## T5 · 12 老任务白名单 + 归档豁免

### 描述
验证 EXEMPT_PATHS 覆盖所有 12 个 2026-07 老任务 + docs/archive/。

### 输入
- 当前 `EXEMPT_PATHS` 列表
- 12 个老任务路径
- docs/archive/ 路径

### 步骤
1. 列 12 个老任务路径（grep 已有列表）
2. 写测试 `test_exempt_covers_12_legacy_tasks`（spec § 7.7）
3. 写测试 `test_exempt_covers_archive`（spec § 7.8）
4. 跑测试 → 应通过
5. 模拟 commit 12 个老任务目录之一（不带 task.yaml）→ hook 跑 → 应通过（豁免）
6. 模拟 commit docs/archive/ 任意文件 → hook 跑 → 应通过

### 预期
- 所有 12 个老任务路径在 EXEMPT 列表中
- 归档路径在 EXEMPT 列表中
- mock commit 不阻断

### 估时
20 min

### 依赖
- T2（实现存在）

---

## T6 · 全套回归

### 描述
跑全套测试 + pre-commit 端到端验证。

### 输入
- T1-T5 全部完成

### 步骤
1. `pytest backend/tests/` 全绿
2. `pytest backend/tests/test_check_step.py` 不破（不破 14 个现有 test）
3. `pytest backend/tests/test_check_test_quality.py` 不破（不破 34 个现有 test）
4. pre-commit 端到端：mock 新任务 + 合法 task.yaml → 通过
5. pre-commit 端到端：mock 非法 task.yaml → 阻断
6. pre-commit 端到端：mock 12 老任务之一 → 不阻断（豁免）
7. pre-commit 端到端：mock docs 改动 → 不触发 task contract
8. 写 verify.md（按 spec § 7 验证）
9. 写 retro.md（实施偏差、改进项、规则更新）

### 预期
- 所有 pytest 全绿
- pre-commit 4 种场景分别行为正确
- verify.md 标 ✅ PASS
- retro.md 标实施完成

### 估时
30 min

### 依赖
- T3 + T4 + T5

---

## 任务↔测试映射

| Task | 自动化测试 |
|---|---|
| T1 | test_check_task.py（10 个 test_validate + 3 个 test_is_exempt + 1 个 test_read）|
| T2 | 同上 + test_check_step.py + test_check_test_quality.py（不破）|
| T3 | pre-commit 端到端 4 种场景（见 plan § 6）|
| T4 | test_check_task.py 自身（template 复用 valid_minimal）|
| T5 | test_exempt_covers_12 + test_exempt_covers_archive |
| T6 | 全套回归 |

## 任务↔Spec 映射

| Task | Spec REQ | Spec S |
|---|---|---|
| T1 | REQ-1 ~ REQ-8 | S-1 ~ S-10 |
| T2 | REQ-1 ~ REQ-8 | S-1 ~ S-10 |
| T3 | REQ-5 (INDEX 视图) | S-6 |
| T4 | REQ-1, REQ-4, REQ-6 | S-1, S-4, S-7, S-8 |
| T5 | REQ-8 (EXEMPT) | S-7, S-8 |
| T6 | 全部 | 全部 |

## 任务↔Evidence 映射

| Task | 自动化测试 | E2E |
|---|---|---|
| T1 | unit: test_validate_* × 10 | — |
| T2 | unit: test_validate_* 10 passed | — |
| T3 | — | e2e: pre-commit 端到端 4 场景 |
| T4 | unit: test_check_task.py 包含 template | — |
| T5 | unit: test_exempt_* × 2 | e2e: 模拟 12 老任务 commit |
| T6 | unit: pytest backend/tests/ | e2e: 4 种 pre-commit 场景 |

## 阶段必填产物（依 spec § 1 REQ-6）

| current_step | 必填 |
|---|---|
| 0 (本任务当前) | research.md ✅ · spec.md ✅ · plan.md ✅ · tasks.md (本文) ✅ · decisions.md ✅ |
| 1 | spec.md ✅ (上面已落) |
| 2 | plan.md ✅ |
| 3 | tasks.md ✅ (本文件) |
| 4 | test-cases.md (含 backend/tests/test_check_task.py) |
| 5 | verify.md (5 verify 场景全绿) |
| 6 | retro.md (实施偏差 + 改进项) |

---

## 总估时

| 阶段 | 估时 |
|---|---|
| 0 调研 | 已落地 |
| 1 规格 | 已落地 |
| 2 计划 | 已落地 |
| 3 任务拆分 (本文) | — |
| 4 实施 | T1: 30min + T2: 45min + T3: 30min + T4: 20min + T5: 20min = 2h 25min |
| 5 验证 | T6: 30min |
| 6 复盘 | 估 30 min |
| **总计** | **3h 25min** |

---

## 任务状态跟踪

| # | 任务 | 状态 | 实施 commit | 实际耗时 | 偏差分析 |
|---|---|---|---|---|---|
| T1 | test_check_task.py | ✅ 已做 | 包含在 P0-7 提交中 | ~25 min | fixture 设计一次到位（-5 min） |
| T2 | check-task.py | ✅ 已做 | 包含在 P0-7 提交中 | ~50 min | +5 min（修复 fixture 多文档问题） |
| T3 | pre-commit 集成 | ✅ 已做 | 包含在 P0-7 提交中 | ~10 min | -20 min（已标准化） |
| T4 | task-yaml-template | ✅ 已做 | 包含在 P0-7 提交中 | ~5 min | -15 min（直接复用） |
| T5 | EXEMPT 白名单 | ✅ 已做 | 包含在 P0-7 提交中 | ~5 min | -15 min（regex 一行） |
| T6 | 全套回归 | ✅ 已做 | 包含在 P0-7 提交中 | ~15 min | -15 min（10 schema case 一次通过） |
| **合计** | | ✅ 全部完成 | | **~1h 50min** | **-1h 5min** |

**实施偏差（详见 retro.md）**：
1. task.yaml 双 `---` 多文档问题（10 fixture + 1 self + 1 template）
2. EXEMPT_PATTERNS 范围过宽（自身任务被误豁免）
3. pre-commit 多余 `fi` + 孤儿 echo

**修正完成**：3 项偏差已修，verify.md 5 步全绿，retro.md 沉淀 3 个 memory 候选。

实施完成时间：2026-07-23（按用户授权"按你的计划来"，完整 0→1→2→3→4→5→6 闭环）。

## 6 步流程产物（按 refactor-6 路径）

| 步 | 产物 | 状态 |
|---|---|---|
| 0 调研 | research.md | ✅ |
| 1 规格 | spec.md | ✅ |
| 2 计划 | plan.md | ✅ |
| 3 任务拆分 | tasks.md (本文件) | ✅ |
| 4 实施 | 4 个新文件 + 1 修改 | ✅ |
| 5 验证 | verify.md | ✅ |
| 6 复盘 | retro.md | ✅ |
