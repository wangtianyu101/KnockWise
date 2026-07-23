---
title: 任务路径/阶段/条件产物契 · 计划
type: plan
step: 2
date: 2026-07-23
status: draft
tags: [refactor, governance, contract, task-yaml, checker, plan]
related:
  - research.md
  - spec.md
  - decisions.md
  - ../../templates/research-refactor.md
  - ../../rules/checklist.md
  - ../../../scripts/check-step.py
---

# 计划 · 任务路径/阶段/条件产物契（P0-7）

> 路径模式：refactor-6
> 1 步 spec 已落地 → [`spec.md`](spec.md)
> 决策已拍板 → [`decisions.md`](decisions.md)

---

## 0. 复述与边界

**核心目标**：建立机器可读契约（`task.yaml` + `check-task.py` + INDEX 校验），让任务目录的"路径—阶段—条件触发—测试证据"被强制校验。

**边界**：不实施业务代码；不修改 `mock_db` / `mock_cache` / `mock_llm`；不迁移 12 个老任务目录；不动 `DOD.md` / `AGENTS.md` 主流程；不引入新测试框架。

---

## 1. ≥ 2 方案对比

### 方案 A · 单一目录级 Python 脚本（推荐）

**结构**：
- `scripts/check-task.py`（新增 · ~200 行）
- 接受 `--dir <path>` + `--view {index|worktree}`（默认 index）
- 输出 exit 0（通过）/ 1（阻断）+ 错误信息列表

**优**：
- 复用 `scripts/check-step.py` 风格（380 行范式）· 风格统一
- 与 `pre-commit` 集成简单（5 行 case）
- 单文件 = 单依赖（stdlib re + os + subprocess）
- 12 个老任务白名单 + 归档豁免一致

**缺**：
- 单文件膨胀（预计 250+ 行）
- 与 `check-step.py` 概念边界模糊（都是 checker）

### 方案 B · 5 个独立脚本（按 schema 字段拆）

**结构**：
- `scripts/check-task-yaml-schema.py`（schema 校验）
- `scripts/check-task-triggers.py`（条件产物闭包）
- `scripts/check-task-evidence.py`（测试证据多落点）
- `scripts/check-task-state.py`（步骤 5 step_state 校验）
- `scripts/check-task-view.py`（INDEX vs WORKTREE）

**优**：
- 单一职责
- 失败信息更精准
- 易于单独跑

**缺**：
- 5 个脚本 5 套维护（与方案 C 反例一致）
- pre-commit 加 25 行 case（5 脚本 × 5 触发条件）
- 跨脚本 schema 一致性靠人维护

### 方案 C · 集成到 `check-step.py`

**结构**：
- `check-step.py` 新增 `task-yaml` step
- 复用现有 6 step 框架 + EXEMPT 机制

**优**：
- 0 新增脚本
- 单一校验源

**缺**：
- `check-step.py` 已是 380 行 · 加 task-yaml 后 600+ 行
- "step" 概念本来是 v2 流程的 research/spec/plan/tasks/implement/verify/retro · 硬塞 task-yaml 语义不一致
- INDEX/WORKTREE 视图是 task-yaml 专用需求 · 现有 check-step.py 没这概念

### 单一推荐：方案 A

**理由**：
1. **风格延续**：与 `check-test-quality.py`（AST） + `check-step.py`（6 step）形成"spec 风格套件"
2. **INDEX 视图专属**：方案 A 可独立加 `--view` 参数；方案 C 需要改 check-step.py 全局签名
3. **可读性**：单文件单一职责（task contract 完整流程）· 比 5 脚本易找
4. **测试简单**：单一 import 测全部场景

---

## 2. 单一推荐方案详细

### 2.1 文件结构

```text
scripts/
  check-task.py              # 新增 · 主脚本（~250 行）
backend/
  tests/
    test_check_task.py       # 新增 · 单元测试（~200 行）
    fixtures/
      task-yaml/            # 测试 fixture
        valid_minimal.yaml
        valid_full_ui.yaml
        invalid_missing_mode.yaml
        ...
.git/hooks/
  pre-commit                 # 修改 · 加 5 行 case
docs/templates/
  task-yaml-template.yaml    # 新增 · 新任务用模板
```

### 2.2 check-task.py 核心算法

```python
#!/usr/bin/env python3
"""
Task directory contract validator.
- 校验 task.yaml schema
- 校验路径—阶段—条件触发—测试证据闭包
- 强制 INDEX 视图
- 不修改任何文件
"""
import sys
import os
import re
import argparse
import subprocess
from pathlib import Path

# Schema 常量
SCHEMA_VERSION = "task/v1"
ALLOWED_MODES = ["full-6", "fix-mini", "refactor-6", "timebox"]
ALLOWED_STEP_STATES = ["in_progress", "accepted", "failed", "blocked"]
ALLOWED_EVIDENCE_TYPES = ["pending", "code", "tasks-inline", "standalone", "e2e"]

# 模式 → 允许步骤
MODE_STEPS = {
    "full-6": [0, 1, 2, 3, 4, 5, 6],
    "fix-mini": [0, 4, 6],
    "refactor-6": [0, 1, 2, 3, 4, 5, 6],
    "timebox": [0],  # 不在本任务
}

# 触发条件 → 必填产物
TRIGGER_ARTIFACTS = {
    "ui_design": ["design-spec.md", "mockups/index.html"],
    "ui_components": ["component-spec.md"],
    "api_change": ["api-spec.md"],
    "db_change": ["db-design.md"],
}

# EXEMPT 路径（含已存在任务目录 + 旧归档）
EXEMPT_PATHS = [
    # 已存在 12 个 2026-07 任务目录（LEGACY_UNVERIFIED）
    r"^docs/tasks/2026-07-(0[1-9]|1[0-9]|2[0-3])-",
    # 旧归档
    r"^docs/archive/",
]

def main():
    args = parse_args()
    content = read_task_yaml(args.dir, args.view)
    errors = validate(content, args.dir, args.view)
    if errors:
        for e in errors:
            print(f"::error file={args.dir}/task.yaml::{e}")
        sys.exit(1)
    sys.exit(0)

def read_task_yaml(dir_path, view):
    """INDEX 视图用 git show :path；WORKTREE 视图用 Path.read_text"""
    task_yaml = Path(dir_path) / "task.yaml"
    if not task_yaml.exists():
        raise FileNotFoundError(f"task.yaml not found in {dir_path}")

    if view == "index":
        # 用 git show :path 读 staged version
        rel_path = str(task_yaml)
        result = subprocess.run(
            ["git", "show", f":{rel_path}"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    else:
        return task_yaml.read_text()

def validate(content, dir_path, view):
    """主校验函数 · 8 项 error code"""
    errors = []
    yaml = parse_yaml(content)

    # 1. schema 字段
    if yaml.get("schema") != SCHEMA_VERSION:
        errors.append("E008: schema must be task/v1")
        return errors  # schema 错就早退

    # 2. task_id 匹配目录名
    expected_id = Path(dir_path).name
    if yaml.get("task_id") != expected_id:
        errors.append(f"E007: task_id must match dir name ({expected_id})")

    # 3. mode
    if yaml.get("mode") not in ALLOWED_MODES:
        errors.append(f"E001: mode must be one of {ALLOWED_MODES}")

    # 4. current_step
    mode = yaml.get("mode")
    current_step = yaml.get("current_step")
    if mode in MODE_STEPS:
        if current_step not in MODE_STEPS[mode]:
            errors.append(f"E002: current_step must be in {MODE_STEPS[mode]}")
    else:
        if not isinstance(current_step, int) or not (0 <= current_step <= 6):
            errors.append("E002: current_step must be 0-6")

    # 5. step_state
    if yaml.get("step_state") not in ALLOWED_STEP_STATES:
        errors.append(f"E003: step_state must be one of {ALLOWED_STEP_STATES}")

    # 6. triggers 4 字段
    triggers = yaml.get("triggers", {})
    for field in ["ui_design", "ui_components", "api_change", "db_change"]:
        if field not in triggers:
            errors.append(f"E004: triggers.{field} required (true or false)")

    # 7. test_evidence
    test_ev = yaml.get("test_evidence", {})
    if not test_ev.get("type"):
        errors.append("E005: test_evidence.type required")
    elif test_ev["type"] not in ALLOWED_EVIDENCE_TYPES:
        errors.append(f"E005: test_evidence.type must be one of {ALLOWED_EVIDENCE_TYPES}")
    if current_step and current_step >= 4 and test_ev.get("type") == "pending":
        errors.append("test_evidence.type=pending requires current_step < 4")
    if test_ev.get("type") != "pending" and not test_ev.get("path"):
        errors.append("test_evidence.path required when type != pending")

    # 8. 触发条件闭包 + 步骤必填产物（用 git ls-tree 看 INDEX）
    artifacts = list_dir_artifacts(dir_path, view)
    for trigger, required in TRIGGER_ARTIFACTS.items():
        if triggers.get(trigger) is True:
            for req in required:
                if req not in artifacts:
                    errors.append(f"trigger {trigger}=true requires {req}")

    # 9. step_state=accepted 必含 verify.md
    if yaml.get("step_state") == "accepted" and "verify.md" not in artifacts:
        errors.append("step_state=accepted requires verify.md")

    return errors

def list_dir_artifacts(dir_path, view):
    """用 git ls-tree 或 os.listdir 列文件"""
    if view == "index":
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", dir_path],
            capture_output=True, text=True, check=True
        )
        return set(result.stdout.splitlines())
    else:
        return set(str(p.relative_to(dir_path)) for p in Path(dir_path).rglob("*"))

def is_exempt(path):
    for pattern in EXEMPT_PATHS:
        if re.match(pattern, path):
            return True
    return False
```

### 2.3 pre-commit 集成（5 行 case）

```sh
# 现有 scripts/pre-commit:108 case 分发表加 5 行
docs/tasks/*/task.yaml)
  python3 scripts/check-task.py --dir "$(dirname "$file")" --view index
  ;;
```

### 2.4 task-yaml-template.yaml（新建任务用）

```yaml
---
schema: task/v1
task_id: YYYY-MM-DD-type-topic
mode: full-6
current_step: 0
step_state: in_progress
triggers:
  ui_design: false
  ui_components: false
  api_change: false
  db_change: false
test_evidence:
  type: pending
metadata:
  created: YYYY-MM-DD
  author: user
  related:
    - research.md
    - decisions.md
---
```

---

## 3. 实施步骤（4 步 TDD 拆分 · ≤ 1h AI 工作量/每个）

### T1 · test_check_task.py 失败用例先行

- 创建 `backend/tests/test_check_task.py` 200 行
- 10 测试场景（来自 spec § 7）
- `pytest backend/tests/test_check_task.py` 应全红

### T2 · check-task.py 最小实现

- 创建 `scripts/check-task.py` 250 行
- 实现 § 2.2 核心算法
- 跑 `pytest backend/tests/test_check_task.py` → 全绿
- 跑 `pytest backend/tests/` 全绿（不破现有 722+ 测试）

### T3 · pre-commit INDEX 视图集成

- 改 `.git/hooks/pre-commit:108` 加 5 行 case
- 改 `scripts/pre-commit` 真实安装版（注意仓库内是模板）
- 测试：临时 mock backend 改动 + 看 hook 行为

### T4 · task-yaml-template + 实施时同步

- 创建 `docs/templates/task-yaml-template.yaml`
- 创建本任务自己的 `task.yaml`（本目录）
- 实施 P0-7 当前 task → 在本目录创建真实 task.yaml
- pre-commit 端到端跑一次 → 验证通过

### T5 · 12 老任务白名单 + 归档豁免

- 初始化 EXEMPT_PATHS 已含 12 个老任务模式
- 验证：12 老任务目录 commit 时不阻断
- 验证：docs/archive/* commit 时不阻断
- 跑 P0-3 之类未来任务 → 必含 task.yaml

### T6 · 全套回归

- 跑 `pytest backend/tests/` 全绿
- 跑 pre-commit 在 mock commit
- pre-commit 加 1 个端到端：临时创建 `docs/tasks/test-fake/` 含合法 task.yaml → 跑 pre-commit → 通过

---

## 4. 依赖影响

| 改 A | 影响 B | 影响 C |
|---|---|---|
| `scripts/check-task.py` 新增 | pre-commit 加 5 行 case | 现有 7 步流程不变 |
| pre-commit INDEX 视图修复 | 解决"检查 A 提交 B"的安全错位 | 现有 P0-1/P0-2 钩子也可能受益（需评估）|
| `task-yaml-template.yaml` 新增 | 新任务用 | 历史任务不受影响（EXEMPT）|
| 12 老任务 EXEMPT | 不破现有工作流 | 0 立即迁移成本 |
| 实施本任务 `task.yaml` | 自我示范 | 其他任务可参照 |

---

## 5. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| 12 老任务路径匹配 EXEMPT 漏匹配 | 🟡 | EXEMPT 用 `^docs/tasks/2026-07-` regex + 实际跑 12 次全豁免验证 |
| `task_id` 与目录名必须严格匹配 | 🟢 | schema 校验一致性 |
| pre-commit INDEX 视图需要 git repo | 🟡 | 在 pre-commit 早段检查 `git rev-parse` 失败 → 退化 working tree |
| pytest 解析 task.yaml 失败 | 🟢 | 解析失败视为 1 个错误，错误码独立 |
| 触发条件闭包误判（缺必需产物但实际不该缺） | 🟡 | triggers 字段只能为 true 才强制产物；未触发不报错 |
| 大量历史任务目录 commit 时全部触发校验 | 🟡 | EXEMPT_PATHS regex 一开始就覆盖 |
| 实施自身 task.yaml 不合法 | 🟢 | 写完即跑 check-task.py 验证 |

---

## 6. 测试矩阵

| Case | 输入 | 期望 | 来源 |
|---|---|---|---|
| T1-S1 | 完整 task.yaml | exit 0 · 0 error | spec § 7.1 |
| T1-S2 | 缺 mode | exit 1 · E001 | spec § 7.2 |
| T1-S3 | current_step=10 | exit 1 · E002 | spec § 7.3 |
| T1-S4 | current_step=4 + type=pending | exit 1 · test_evidence 错 | spec § 7.4 |
| T1-S5 | task_id 与目录名不匹配 | exit 1 · E007 | spec § 7.5 |
| T1-S6 | triggers.ui_design=true 缺 design-spec.md | exit 1 · trigger 错 | spec § 7.6 |
| T1-S7 | 路径匹配 EXEMPT 模式 | exit 0（跳过）| spec § 7.7-7.8 |
| T1-S8 | mode 不在枚举 | exit 1 · E001 | spec § 7.9 |
| T1-S9 | step_state=accepted 缺 verify.md | exit 1 · step_state 错 | spec § 7.10 |
| T1-S10 | schema 字段为 task/v2 | exit 1 · E008 | spec § 7.11 |

预 commit 端到端：
- mock commit 含 backend 改动 + 合法 task.yaml → hook 跑成功
- mock commit 含 backend 改动 + 缺 task.yaml → hook 阻断
- mock commit 含 docs 改动 → hook 不触发（按 staged path 过滤）

---

## 7. 关联文档

- 调研：[`research.md`](research.md)
- 规格：[`spec.md`](spec.md)
- 决策：[`decisions.md`](decisions.md)
- 主账：`docs/issues.md` 决策 #26 · 债务 #14
- 公共规则：`AGENTS.md` § 0 / § 6.5 / § 6.7 / § 6.8 v2
- 现有机制：`scripts/check-step.py` · `scripts/check_test_quality.py` · `scripts/pre-commit`
- 模板：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md`
