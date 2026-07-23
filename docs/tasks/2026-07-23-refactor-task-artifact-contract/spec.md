---
title: 任务路径/阶段/条件产物契 · 规格
type: spec
step: 1
date: 2026-07-23
status: draft
tags: [refactor, governance, contract, task-yaml, checker]
related:
  - research.md
  - ../../templates/research-refactor.md
  - ../../templates/tasks-template.md
  - ../../templates/verify-template.md
  - ../../rules/checklist.md
  - ../../../scripts/check-step.py
  - ../../../AGENTS.md
  - ../../issues.md (决策 26)
---

# 规格 · 任务路径/阶段/条件产物契（P0-7）

> 路径模式：refactor-6
> 调研 0 步已落地 → [`research.md`](research.md)
> 决策已拍板 → [`decisions.md`](decisions.md)（决策 1：最小 task.yaml + check-task.py；测试证据多落点；INDEX 校验）

---

## 0. 复述与边界（不可省略）

**用户原话**："把上面哪些问题都处理一遍（剩余 P0/P1/P2）...自动决策...不要进入代码实施"。

本任务在 0 步决策为：建立机器可读的"路径—阶段—条件触发—测试证据落点"契约，使用最小 `task.yaml` + 目录级 `check-task.py` + INDEX 视图校验。**不**为强制实施代码，**不**解决 P0-4 启用前清理 5 项（用户手动），**不**迁移历史任务目录，**不**复制 task 状态到 `task.yaml`。

---

## 1. 业务契约（Requirement）

### REQ-1 · 任务目录契约唯一性

- 每个新任务目录必须含 `task.yaml`，记录 mode / current_step / step_state / triggers / test_evidence
- 路径模式作为 `mode` 字段唯一来源（替代 research.md 自由文本、decisions.md 重复声明、template 模板标题模糊）
- `task.yaml` schema 版本号强制 `task/v1` 起步

### REQ-2 · 当前步骤真实性

- `current_step` ∈ {0, 1, 2, 3, 4, 5, 6}
- `step_state` ∈ {in_progress, accepted, failed, blocked}
- 路径模式下步骤集合：
  - `full-6` / `refactor-6`：0, 1, 2, 3, 4, 5, 6
  - `fix-mini`：0, 4, 6
  - `timebox`：T+30m, T+2h, T+24h, T+48h, T+72h（timebox 不在本任务内）

### REQ-3 · 条件触发

- `triggers` 仅记录不能从 mode 推导的条件
- 字段：`ui_design` / `ui_components` / `api_change` / `db_change`
- 已知 type：
  - `ui_design` = true → 必产 design-spec.md（与 §1 spec.md 一起）
  - `ui_components` = true → 必产 component-spec.md
  - `api_change` = true → 必产 api-spec.md
  - `db_change` = true → 必产 db-design.md
- 字段不写 = 未触发 = 校验时不能强制产物

### REQ-4 · 测试证据多落点

- `test_evidence.type` ∈ {pending, code, tasks-inline, standalone, e2e}
- 字段映射（来自研究 § 4.3 P1-1 决定）：
  - `pending` → 步骤 4 之前
  - `code` → 引用 pytest node
  - `tasks-inline` → 引用 tasks.md 章节
  - `standalone` → 引用 test-cases.md
  - `e2e` → 引用 Playwright spec
- `test_evidence.path` 必填（除 pending 外）
- 步骤 4 accepted 后 `type` 不得为 `pending`

### REQ-5 · INDEX 视图校验

- pre-commit 调用 `check-task.py` 时强制 `--view=index`
- `task.yaml` 必填字段只能读 INDEX blob（`git show :path`）
- 不得用 working tree 文件
- 当前 pre-commit 已存在 INDEX/WORKTREE 错位问题（pre-commit:79-124 用 staged path 触发但读 working tree 文件）→ 本任务修复此错位

### REQ-6 · 必填产物按模式 + current_step 推导

| mode | current_step | 必填 |
|---|---|---|
| full-6 | 0 | research.md |
| full-6 | 1 | research.md + spec.md + product-doc.md |
| full-6 | 2 | research.md + spec.md + plan.md |
| full-6 | 3 | + tasks.md（视 ui_design 加 design-spec.md / mockups/） |
| full-6 | 4 | + test-cases.md（强制）|
| full-6 | 5 | + verify.md（强制 L3 + L5 段）|
| full-6 | 6 | + retro.md（强制）|
| fix-mini | 0 | research.md |
| fix-mini | 4 | test-cases.md（强制）|
| fix-mini | 6 | retro.md（强制）|
| refactor-6 | 0/1/2/3/4/5/6 | 同 full-6（除不要求 product-doc.md）|

### REQ-7 · 步骤 5 step_state 必须先 accepted 再 verify 闭环

- `step_state: accepted` 才能产出 `verify.md`
- `verify.md` L4 review 必含独立 verifier agent 输出
- `verify.md` L5 staging 必填真实路径与证据
- `verify.md` 标"🟢 可进入 6 步"前必须 L1-L5 全 accepted（当前 CI auto-fix verify.md:257 是反例）

### REQ-8 · EXEMPT_TASKS 白名单

- 12 个 2026-07-23 已存在任务目录默认 LEGACY_UNVERIFIED
- 旧归档 `docs/archive/...` 全豁免
- EXEMPT_TASKS 字符串匹配规则（与 check-step.py EXEMPT_SPECS 同模式）
- 新任务必须满足 task.yaml 契约 · 不豁免

---

## 2. 验收场景（Scenario · GWT 形式）

### S-1 · 新建任务最小 task.yaml
**Given** 用户创建新 `docs/tasks/2026-07-XX-new-task/` 目录
**When** 提交 1 个 commit 含 backend 文件
**Then** pre-commit 应：
1. 检查 task.yaml 存在
2. 校验 task.yaml schema 合法（task/v1，6 必填字段齐全）
3. 若 mode=full-6 且 current_step≥3：检查 spec/plan/tasks.md 存在
4. 若 triggers.ui_design=true：检查 design-spec.md + mockups/index.html 存在
5. 若 test_evidence.type≠pending 且 current_step≥4：检查对应路径存在
6. INDEX 视图（git show :path）= 验证所用视图（不得用 working tree）

### S-2 · 当前步骤真实性
**Given** task.yaml `current_step=1, step_state=accepted`
**When** 提交
**Then** `mode=full-6` → spec.md + product-doc.md 必存在
**And** `mode=refactor-6` → spec.md 必存在 · product-doc.md 不强制
**And** `mode=fix-mini` → spec.md 不强制

### S-3 · 条件触发闭包
**Given** task.yaml `triggers.ui_design=true`
**When** 提交
**Then** design-spec.md + mockups/index.html + ≥1 个 mockup HTML 必存在
**And** component-spec.md 必存在（隐式依赖 ui_components）

### S-4 · 测试证据多落点
**Given** task.yaml `test_evidence.type=code`
**When** current_step=4
**Then** `test_evidence.path` 字段引用的 pytest node 必须存在（parse + collect）
**And** 不能为空

### S-5 · 步骤 5 step_state 必 accepted
**Given** 提交 verify.md
**When** task.yaml `step_state != accepted`
**Then** 阻断 + 错误信息：'verify.md requires step_state=accepted'

### S-6 · INDEX 视图校验
**Given** working tree 改了 task.yaml 但 INDEX 未更新
**When** pre-commit 跑
**Then** 校验器使用 `git show :path` · 应阻断（working tree 新值不入校验）
**And** 反向：INDEX 改了但 working tree 未改 → 同样阻断（防止 working tree 漂移）

### S-7 · EXEMPT_TASKS 白名单
**Given** 路径匹配 `docs/tasks/2026-07-23-*/` 任一老任务目录（不在白名单）
**When** pre-commit 跑
**Then** 阻断：'task.yaml required for new tasks (not in EXEMPT_TASKS)'

### S-8 · 旧归档豁免
**Given** 路径匹配 `docs/archive/`
**When** pre-commit 跑
**Then** 跳过校验（不阻断）

### S-9 · 字段类型校验
**Given** task.yaml `mode=full-6` 但 `current_step=10`
**When** 校验
**Then** 阻断：'current_step must be 0-6'

### S-10 · 缺失 mode
**Given** task.yaml 缺 `mode` 字段
**When** 校验
**Then** 阻断：'mode is required'

---

## 3. 数据契约（task.yaml schema · task/v1）

```yaml
---
schema: task/v1          # 必填 · 当前唯一版本
task_id: 2026-07-24-p0-7-task-artifact-contract  # 必填 · 与目录名一致
mode: full-6             # 必填 · full-6 | fix-mini | refactor-6 | timebox
current_step: 1         # 必填 · 0-6
step_state: in_progress  # 必填 · in_progress | accepted | failed | blocked

triggers:                # 必填字段（可空 map）· 字段值必填或留空
  ui_design: true
  ui_components: true
  api_change: false
  db_change: false

test_evidence:           # 必填字段
  type: code             # pending | code | tasks-inline | standalone | e2e
  path: backend/tests/test_artifact_contract.py::test_task_yaml_schema

metadata:                # 可选
  created: 2026-07-24
  author: user
  related:
    - research.md
    - decisions.md
---
```

### 3.1 字段详细

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `schema` | string | ✅ | 固定 `task/v1` · 升级时改为 `task/v2` 并双轨期 |
| `task_id` | string | ✅ | 严格匹配目录名 basename（不含前缀斜杠）|
| `mode` | enum | ✅ | `full-6` / `fix-mini` / `refactor-6` / `timebox` |
| `current_step` | int 0-6 | ✅ | 路径模式限制范围（如 fix-mini 限 0/4/6）|
| `step_state` | enum | ✅ | `in_progress` / `accepted` / `failed` / `blocked` |
| `triggers.ui_design` | bool | ✅（可 false）| true 触发 design-spec + mockups 闭包 |
| `triggers.ui_components` | bool | ✅ | true 触发 component-spec 闭包 |
| `triggers.api_change` | bool | ✅ | true 触发 api-spec 闭包 |
| `triggers.db_change` | bool | ✅ | true 触发 db-design 闭包 |
| `test_evidence.type` | enum | ✅ | 5 种落点类型 |
| `test_evidence.path` | string | step≥4 必填 | 引用 test node / 文件路径 / 章节 |
| `metadata` | map | ❌ | 自由扩展 · 不校验 |

### 3.2 已知 schema 错误

- `mode` 不在枚举 → E001
- `current_step` 越界 → E002
- `step_state` 不在枚举 → E003
- `triggers.*` 缺字段 → E004
- `test_evidence.type` 不在枚举 → E005
- `test_evidence.path` 引用不存在文件 → E006
- `task_id` 不匹配目录名 → E007
- `schema` 不是 `task/v1` → E008

---

## 4. 边界与非目标

### 边界

- ✅ `task.yaml` 是路径/阶段/条件触发的唯一机器主账
- ✅ `check-task.py` 校验 contract 但不解析 Markdown 内容
- ✅ pre-commit INDEX 视图修复
- ✅ 12 个现有任务标 LEGACY_UNVERIFIED · 12 任务全豁免
- ✅ `docs/archive/` 全部豁免

### 非目标

- ❌ 不解析 Markdown 内容（由 check-step.py 现有功能负责）
- ❌ 不强制实施代码
- ❌ 不迁移历史任务目录的 step_state（保持不变）
- ❌ 不修改 `mock_db` / `mock_cache` / `mock_llm` 默认行为
- ❌ 不引入新测试框架
- ❌ 不自动回写 `decisions.md`（CLAUDE.md § 6.8 v2 由用户/AI 主动同步）
- ❌ 不替代 P1-7 baseline 字段（product_baseline 在 product-doc，task.yaml 只放目录契约）
- ❌ 不替代 P0-5 任务状态字段（task status 在 tasks.md，task.yaml 只放路径契约）
- ❌ 不触发 task.yaml 自动生成（由创建者手动写）

---

## 5. 与现有机制关系

| 文件 | 角色 | 关系 |
|---|---|---|
| `docs/issues.md` | 项目级债务/议题主账 | task.yaml 不复制债务 |
| `AGENTS.md` | 项目级 hook 准则 | task.yaml 不复制 hook |
| `DOD.md` | 每步 DOD 主账 | task.yaml 不复制 DOD |
| `docs/rules/checklist.md` | 每步交付物清单 | task.yaml 不复制清单 |
| `docs/templates/research-*.md` | 调研模板 | task.yaml 替代其 step 字段 |
| `docs/templates/tasks-template.md` | 任务清单模板 | task.yaml 是其元数据 |
| `docs/templates/verify-template.md` | verify 模板 | task.yaml 在 step_state=accepted 时使用 |
| `scripts/check-step.py` | 单文件内容校验 | check-task.py 是目录级补充 |
| `scripts/check_test_quality.py` | AST 拦截 | 不重叠 |
| `scripts/check-frontmatter.py`（P2-4）| frontmatter 校验 | 独立脚本 |

---

## 6. 安全 / 不可信输入审查

- 不涉及 CI/CD · 不涉及 Agent · 不涉及 secrets · 不涉及网络
- 不涉及文件系统写 · 只读校验
- 无需 § 0.2.1 安全审查
- INDEX 视图用 `git show :path` 只读

---

## 7. 测试场景（pytest 期望）

```python
# tests/test_check_task.py

def test_minimal_task_yaml_valid():
    """完整 task.yaml 通过校验"""
    yaml = """\
schema: task/v1
task_id: 2026-07-24-test
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
"""
    assert validate(yaml) == []

def test_missing_mode_blocked():
    yaml = "schema: task/v1\ncurrent_step: 0"
    errors = validate(yaml)
    assert any("mode" in e for e in errors)

def test_current_step_out_of_range():
    yaml = "schema: task/v1\nmode: full-6\ncurrent_step: 10"
    errors = validate(yaml)
    assert any("current_step" in e for e in errors)

def test_test_evidence_required_after_step_4():
    yaml = """\
schema: task/v1
task_id: 2026-07-24-test
mode: full-6
current_step: 4
step_state: accepted
triggers:
  ui_design: false
  ui_components: false
  api_change: false
  db_change: false
test_evidence:
  type: pending
"""
    errors = validate(yaml)
    assert any("test_evidence" in e for e in errors)

def test_task_id_must_match_dir_name():
    """task_id 与目录名 basename 不一致 → 阻断"""
    yaml = """\
schema: task/v1
task_id: wrong-name
mode: full-6
current_step: 0
step_state: in_progress
triggers: {ui_design: false, ui_components: false, api_change: false, db_change: false}
test_evidence: {type: pending}
"""
    errors = validate_in_dir(yaml, "/docs/tasks/2026-07-24-correct-name/")
    assert any("task_id" in e for e in errors)

def test_trigger_ui_design_requires_design_spec():
    """ui_design=true → design-spec.md + mockups/index.html 必存在"""
    yaml = """\
schema: task/v1
task_id: 2026-07-24-ui-task
mode: full-6
current_step: 3
step_state: in_progress
triggers:
  ui_design: true
  ui_components: false
  api_change: false
  db_change: false
test_evidence: {type: pending}
"""
    errors = validate_in_dir(yaml, "/docs/tasks/2026-07-24-ui-task/")
    assert any("design-spec" in e for e in errors)
    assert any("mockups" in e for e in errors)

def test_legacy_task_dir_exempted():
    """老任务目录路径匹配 EXEMPT_TASKS → 跳过校验"""
    assert is_exempt("/docs/tasks/2026-07-21-issues-audit/") is True
    assert is_exempt("/docs/tasks/2026-07-22-new-feature-ci-autofix/") is True

def test_archive_dir_exempted():
    assert is_exempt("/docs/archive/some-old-task/") is True

def test_step_state_required_for_verify():
    """verify.md 存在但 step_state != accepted → 阻断"""
    yaml = """\
schema: task/v1
task_id: 2026-07-24-test
mode: full-6
current_step: 5
step_state: in_progress
triggers: {ui_design: false, ui_components: false, api_change: false, db_change: false}
test_evidence: {type: code, path: backend/tests/test_x.py::test_y}
"""
    errors = validate_with_files(yaml, dir_with_verify_md=True)
    assert any("step_state" in e for e in errors)
```

---

## 8. 实施约束（4 步 TDD 必做）

1. 先写失败 pytest → 红
2. 写 `scripts/check-task.py` 最小实现 → 绿
3. pre-commit 加 5 行 case · 优先用 INDEX 视图
4. EXEMPT_TASKS 白名单初始化 12 个老任务
5. 回归测试：`pytest backend/tests/` 全绿

**Verifier agent 必开**：每个 commit 后用独立 verifier agent 跑 § 1 + § 2 + § 7 验证。

---

## 9. 后续接口（本任务不实现）

- `check-frontmatter.py`（P2-4）· 独立脚本
- `check-spec.py` 5 模板（P2-3）· 独立脚本
- `check-product-doc.py`（P1-7 baseline 字段）· 独立脚本
- `task.yaml` 升级 `task/v2` 时双轨期

---

## 10. 关联文档

- 调研：[`research.md`](research.md)
- 决策：[`decisions.md`](decisions.md)
- 主账：[`docs/issues.md`](../../issues.md) 决策 #26 · 债务 #14
- 公共规则：`AGENTS.md` § 0.2.1 安全审查 · `AGENTS.md` § 6.5 任务完成回写 · `AGENTS.md` § 6.8 v2 决策六处同步 · `AGENTS.md` § 6.7 verify-loop
- 现有机制：`scripts/check-step.py` · `scripts/check_test_quality.py` · `scripts/pre-commit`
- 模板：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md`
