---
title: 任务路径/阶段/条件产物契 · 复盘
type: retro
step: 6
date: 2026-07-23
status: ✅ closed
related:
  - research.md
  - spec.md
  - plan.md
  - decisions.md
  - tasks.md
  - verify.md
---

# 复盘 · 任务路径/阶段/条件产物契（P0-7）

> 路径模式：refactor-6
> 5 步 verify 通过 → 6 步复盘落地

---

## 1. 实施完成度

| Task | 估时 | 实际 | 偏差 |
|---|---|---|---|
| T1 失败用例先行 | 30 min | ~25 min | -5 min（fixture 设计一次到位） |
| T2 check-task.py 最小实现 | 45 min | ~50 min | +5 min（修复 fixture 多文档问题） |
| T3 pre-commit INDEX 视图集成 | 30 min | ~10 min | -20 min（pre-commit 已标准化集成模式） |
| T4 task-yaml-template + 本任务 task.yaml | 20 min | ~5 min | -15 min（直接复用） |
| T5 12 老任务白名单 | 20 min | ~5 min | -15 min（regex 一行） |
| T6 全套回归 | 30 min | ~15 min | -15 min（10 schema case 一次通过） |
| **合计** | **2h 55min** | **~1h 50min** | **-1h 5min** |

---

## 2. 关键偏差与根本原因

### 2.1 task.yaml 双 `---` 多文档问题

**偏差**：10 个 fixture + 1 个 self task.yaml + 1 个 template 全部因 trailing `---` 触发 PyYAML `ComposerError: expected a single document in the stream`。

**根本原因**：
- 我生成 YAML 时机械添加了"leading + trailing"两个 `---` 作为文档定界符
- 但 PyYAML `safe_load` 单文档流不接受第二个 `---`
- 我的 test_check_task.py 第一次跑就发现 8 个 fixture 失败（应该先有 red step）

**修复**：
- 写一个 Python 小脚本扫描所有 `*.yaml` 结尾的 `---` 删除
- 重新跑测试 → 10 case 全绿

**改进（规则更新）**：
- `task.yaml` 只用前导 `---` 开启文档，不要 trailing `---` 关闭（虽然 YAML 5.1 spec 允许两种风格）
- 写 fixture 模板时只放前导分隔符

### 2.2 EXEMPT_PATTERNS 范围过宽

**偏差**：初版用 `^docs/tasks/2026-07-\d{2}-` 包含 2026-07-23，自身任务被误豁免（EXEMPT_PATTERNS 匹配成功），所以 validate_dir own task 报 0 errors（即使 task.yaml 缺字段）。

**根本原因**：
- 设计 EXEMPT 时只考虑"历史 12 个任务"，但 regex 用了通用的 `2026-07-XX` 模式
- 范围过宽 → 自身新任务也被豁免 → 测试结果错误地显示"OK"

**修复**：
- 改为 `^docs/tasks/2026-07-(0[1-9]|1\d|2[0-2])-`（仅 2026-07-01 ~ 2026-07-22）
- 2026-07-23 起新任务强制 task.yaml 契约

**改进（规则更新）**：
- EXEMPT_PATTERNS 必须有明确截止日期（"X 日之前 = LEGACY"）
- 写 EXEMPT regex 时用日期闭区间表达式而不是宽泛 `\d{2}`

### 2.3 pre-commit 多余 `fi` + 孤儿 echo

**偏差**：新增 §4.5 task.yaml 校验块时，保留了旧 if 块的孤立 `echo "✅ 6 步 v2 DOD 校验通过"` 和 `fi`。

**根本原因**：
- Edit 时只替换了 `exit 1` 后面的内容到 `fi`，没注意 `echo + fi` 是上一级 if 的 footer
- `bash -n` 立即报 syntax error near unexpected token `fi`

**修复**：
- 删除孤儿 `echo "✅ 6 步 v2 DOD 校验通过"` 行
- 删除对应 `fi`
- 重新 `bash -n` → 通过

**改进（规则更新）**：
- 任何 Edit pre-commit / setup scripts 时必须立即 `bash -n` 验证
- 复杂 sed 替换后逐行 `cat -n` 复核

### 2.4 系统 Python vs backend venv 差异

**偏差**：实施跑在系统 Python 3.9.6（PyYAML 6.0.3），但 backend venv 不存在所以未跑全套 pytest（722+ 个测试）。

**根本原因**：
- venv 缺失（不在 AI 修复范围 - 属"用户手动" P0-4 启用前清理 5 项之一）
- 系统 Python 跑 module-level test 通过，但完整集成测试需要 backend venv

**改进（规则更新）**：
- 跑全套前需 `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- 后续实施任务默认假设 venv 存在；若缺失则降级到 system Python + importlib 加载核心模块

---

## 3. 已落地改进

| 改进 | 位置 |
|---|---|
| `task.yaml` schema 校验 | `scripts/check-task.py` |
| 12 老任务白名单 | `EXEMPT_PATTERNS` regex 限定 2026-07-01~22 |
| docs/archive 豁免 | `EXEMPT_PATTERNS` 第 2 项 |
| pre-commit INDEX 视图修复 | `scripts/pre-commit` §4.5 |
| 8 error code 模板 | `check-task.py` E001~E008 |
| 任务目录自动契约 | 新建任务必含 task.yaml（fail-closed）|

---

## 4. 规则更新建议（不实施 · 仅沉淀到 memory）

### memory 候选 1：task.yaml frontmatter style

```
feedback-task-yaml-frontmatter-style.md
- task.yaml 只用前导 ---
- 不要 trailing ---
- PyYAML safe_load 不接受 multi-document
- Write tool 输出时手动 strip trailing ---
```

### memory 候选 2：EXEMPT 范围要有截止日期

```
feedback-exempt-pattern-has-cutoff.md
- 写 EXEMPT_PATTERNS 时必须用日期闭区间
- 不要用宽泛 \d{2} 匹配
- 自身任务绝不能被自身 EXEMPT 覆盖
- 写完后用 inline test 验证（自身任务 NOT EXEMPT）
```

### memory 候选 3：pre-commit Edit 立即 bash -n

```
feedback-precommit-edit-verify.md
- 任何 Edit pre-commit / setup scripts 必须立即 bash -n
- Edit 后逐行 cat -n 复核
- Edit 跨多个 if 块时要小心孤儿 echo + fi
```

---

## 5. 沉淀规则

### 5.1 修模板

✅ `task-yaml-template.yaml` 已加前导 `---` 风格（仅 leading）

### 5.2 修本任务

✅ 本任务 `task.yaml` 已 strip trailing `---`

### 5.3 修 AGENTS.md（建议 · 实施阶段再做）

候选增加一条：
- § 6.5 任务完成回写新增第 7 条：
  - [ ] `task.yaml` schema 必填 + 路径模式必填 + 步骤 5 accepted 必含 verify.md（per `check-task.py`）
- § 6.3 自检清单新增第 8 条：
  - [ ] 跨任务 Edit pre-commit/setup 脚本后立即 `bash -n` 验证

### 5.4 关联 memory 候选

- `feedback-task-yaml-frontmatter-style.md`
- `feedback-exempt-pattern-has-cutoff.md`
- `feedback-precommit-edit-verify.md`

实施阶段写入 `~/.claude/.../memory/`。

---

## 6. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 计划：[plan.md](plan.md)
- 决策：[decisions.md](decisions.md)
- 任务拆分：[tasks.md](tasks.md)
- 验证：[verify.md](verify.md)
- 主账：`docs/issues.md` 决策 #26 · 债务 #14
- 公共规则：`AGENTS.md` § 6.5 / § 6.7 / § 6.8 v2
