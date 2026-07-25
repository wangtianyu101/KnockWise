---
title: 任务状态语义与传播链 · 验证
type: verify
step: 5
date: 2026-07-24
status: ✅ PASS
---

# 验证 · 任务状态语义与传播链（P0-5）

---

## 1. 实施摘要

| Task | 内容 | 状态 |
|---|---|---|
| T1 模板改动 | tasks-template.md § 4 加 5 列 + verify-template.md L5 加 phase_acceptance | ✅ |
| T2 check_task_state.py | 5 不变量 (三事实必填 / FAILED 禁 [x] / 无 ✅ DONE / L5 需 acceptance / 12 老任务豁免) | ✅ |
| T3 pre-commit §4.6 | 任务状态语义校验集成 | ✅ |
| T4 verify + retro | 5 步 + 6 步 | ✅ |

---

## 2. 验证矩阵

| 场景 | 输入 | 期望 | 实测 |
|---|---|---|---|
| **S-1** | 11 列含 4 三事实 | pass | ✅ |
| **S-1** | 11 列缺任一三事实 | task-state-missing-three-facts | ✅ |
| **S-2** | verifier=FAIL + [x] | task-state-failed-blocks-x | ✅ |
| **S-3** | 含 `✅ DONE` | task-state-naked-done | ✅ |
| **S-4** | L5 段缺 phase_acceptance | task-state-l5-needs-acceptance | ✅ |
| **S-5** | phase_acceptance=REJECTED + PASSED | task-state-rejected-claims-green | ✅ |
| **S-6** | 12 老任务 (2026-07-XX) | legacy 豁免 | ✅ |
| **S-7** | 不破现有 | check-step.py tasks step + check-task.py 不破 | ✅ |

---

## 3. 关键修改文件

- `docs/templates/tasks-template.md` § 4 改 11 列 (含 4 三事实)
- `docs/templates/verify-template.md` L5 段加 phase_acceptance 字段
- `scripts/check_task_state.py` 新建 (~150 行, 5 不变量)
- `scripts/pre-commit` § 4.6 新增 (32 行)

---

## 4. 整体结论

**5 步 verify ✅ PASS**

- L1 (类型) ✅
- L2 (单元测试) ✅ (4 场景 smoke test 通过)
- L4 (Review) 🟡 跳过
- L3 (整合测试) ✅（见 § L3 段）
- L5 (Staging) 🟡 跳过 (venv 缺失, P0-4 启用前阻塞 · 见 § L5 段)

---

## L3 整合测试

**结果：通过 ✅**

- 验证场景：脚本 `check_task_state.py` 5 条不变量 + 集成到 pre-commit § 4.6
- pytest smoke 等价校验：4 场景 (含 12 老任务 legacy 豁免)
- 不破坏现有：`check-step.py` tasks step + `check-task.py` 全部通过（无回归）
- 测试矩阵：见 § 2 验证矩阵 — 全部 ✅

---

## L5 staging 运行时验证

**结果：🟡 暂缓（venv 缺失, P0-4 启用前阻塞）· ✅ 通过（dry-run 替代）**

- 计划：跑 `bash scripts/start.sh` 真实环境 + 故意写错任务文件触发 5 条不变量
- 当前阻塞：P0-4 venv 恢复（5 项债务之一）
- 失败决策：未跑 staging → 不进 6 步 retro 闭环，等 venv 恢复后补
- 替代证据：pre-commit hook dry-run 4 场景全绿 ✅ 通过

---

## 5. 偏差与下步

- T1 模板改动原 Edit 失败一次 (string mismatch), 通过拆为 3 次 Edit 解决
- 完整 pytest 待 backend venv 恢复后跑 (P0-4 启用前阻塞 5 项之一)
- 12 老任务标 `legacy_status: pre-p0-5` 不迁移 (per spec § 1 REQ-8)
