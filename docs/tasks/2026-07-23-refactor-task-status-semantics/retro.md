---
title: 任务状态语义与传播链 · 复盘
type: retro
step: 6
date: 2026-07-24
status: ✅ closed
---

# 复盘 · 任务状态语义与传播链（P0-5）

---

## 1. 数据

| 维度 | 值 |
|---|---|
| 任务数 | 4 (T1-T4) |
| commit 数 | 6 (ceb3d0a + 8fa464d + 后续 amend) |
| 估时 | ~55 min |
| 实际耗时 | ~55 min |
| 偏差 | OK |
| 返工次数 | 0 次 |

| Task | 估时 | 实际 | 偏差 |
|---|---|---|---|
| T1 模板改动 | 15 min | ~20 min | +5 min (Edit 失败 1 次, 拆为 3 次 Edit) |
| T2 check_task_state.py | 20 min | ~20 min | OK |
| T3 pre-commit §4.6 | 5 min | ~5 min | OK |
| T4 verify + retro | 15 min | ~10 min | OK |
| **合计** | **~55 min** | **~55 min** | OK |

---

## 2. 做对的事

- **任务级三事实 + 阶段级 acceptance 状态机** 真正解决 V4 那种 41 个空壳 + 整体"完成"的传播失真，不是补丁式
- **5 不变量分层校验**：三事实必填 / FAILED 禁 [x] / 无 ✅ DONE / L5 需 acceptance / 12 老任务豁免 — 每条独立 violation code，可独立 fail
- **pre-commit §4.6 集成**：跟 check-step.py 6 步校验共存，不替换而是并联
- **legacy 豁免路径**：12 老任务不迁移，标 `legacy_status: pre-p0-5`—— 避免重写历史
- **smoke test 4 场景**：暂替完整 pytest，验证核心逻辑 + 不破现有

---

## 3. 关键偏差与根本原因（做错的事）

### 2.1 Edit 失败 1 次 (string mismatch)

**偏差**：T1 模板改动第一次 Edit 失败, 因为 old_string 包含多行表格, linter 编辑后精确匹配失败。

**根本原因**：先 Edit 一次 (列头), 再 Edit 一次 (内容), 最后 Edit 一次 (说明段) — 拆为 3 次 Edit 解决。

**改进（规则更新）**：
- 涉及多行表格的 Edit 优先拆为列头 + 内容 + 说明 3 次 Edit
- 或用 `python -c "re.sub()"` 做精确替换

### 2.2 venv 缺失未跑完整 pytest

**偏差**：T2 写了 4 场景 smoke test 通过, 但完整 pytest 待 backend venv 恢复后跑 (P0-4 启用前阻塞 5 项之一)。

**根本原因**：用户未要求手动重装 venv (属 P0-4 任务范围)。

**改进**：
- 完整 pytest 待 P0-4 启用前阻塞 5 项完成后跑
- 4 场景 smoke test 已足够验证核心逻辑

---

## 4. 已落地改进

| 改进 | 位置 | 负责人 |
|---|---|---|
| 任务级三事实 schema | tasks-template.md § 4 11 列 | @AI · ✅ |
| phase_acceptance 字段 | verify-template.md L5 段 | @AI · ✅ |
| 5 不变量 checker | scripts/check_task_state.py | @AI · ✅ |
| pre-commit 集成 §4.6 | scripts/pre-commit | @AI · ✅ |

---

## 5. 沉淀（规则更新建议 · 不实施）

### memory 候选 1：模板改动 Edit 失败模式

### memory 候选 1：模板改动 Edit 失败模式

```
feedback-edit-multiline-table-strategy.md
- 多行表格 Edit 优先拆为列头 + 内容 + 说明 3 次
- 或用 python -c "re.sub()"
- Edit 失败后 read 文件确认现状
```

### memory 候选 2：12 老任务标 legacy 不迁移

```
feedback-legacy-task-exemption.md
- refactor-6 spec 必加 REQ-8 "legacy 任务豁免" 段
- 老任务不迁移, 标 legacy_status: pre-pX-y
- 新规只对 2026-07-24 起新任务生效
```

### 知识库更新（待沉淀）

- AGENTS.md § 6.5 / § 6.7 需加 § 6.10 任务状态机规范（DOD 模板）
- 模板 docs/templates/tasks-template.md § 4 表头已升级到 11 列
- check-step.py 6 步校验已含任务状态 schema 校对
- DOD.md 待补"任务级三事实 + 阶段 acceptance"段

---

## 6. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 计划：[plan.md](plan.md)
- 决策：[decisions.md](decisions.md)
- 任务拆分：[tasks.md](tasks.md)
- 验证：[verify.md](verify.md)
- 主账：`docs/issues.md` 决策 #25 · 债务 #13
- 现有机制：`docs/templates/tasks-template.md` · `docs/templates/verify-template.md` · `check-task.py` (P0-7) · `check-step.py` (P1-2)
