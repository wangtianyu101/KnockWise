---
title: P0 AI Eval 基线修复 · 实施任务
type: tasks
step: 4
date: 2026-07-26
status: in_progress
layer: L0
tags: [p0, eval, testing]
related: [research.md, decisions.md, test-cases.md]
---

# P0 AI Eval 基线修复 · 实施任务

## 1. 任务清单

### T1: 修复 JSONL 完整性

- [x] T1: 把非法 Python literal 改为合法 JSON，并补逐行解析回归
  - **文件**: `backend/tests/eval/datasets/interview_eval_v1.jsonl` (commit `e247ecd` v40 期间已 None→null), `backend/tests/eval/test_dataset_integrity.py` (本次 working tree 新增)
  - **测试**: `test_dataset_integrity.py::test_all_eval_dataset_lines_are_valid_json` ✅ PASSED + `test_prompt_injection_expected_branch_is_null` ✅ PASSED
  - **依赖**: —
  - **估时**: 20 min
  - **产出**: 1 个 commit 边界（JSONL `e247ecd` + 本次 working tree `test_dataset_integrity.py`）

### T2: 修复 Digest fallback 契约

- [x] T2: prompt-injection fallback 返回 schema-valid JSON + followup_match/text mock 扩展
  - **文件**: `backend/tests/eval/conftest.py` (digest_fallback 改 schema-valid JSON + followup_match_2/3/4 + followup_text_0-4 模板 + mock 函数签名改 branch_index/topic), `backend/tests/eval/runner.py` (followup_text dispatch 用 case input)
  - **测试**: `test_digest_llm.py::test_digest_llm_12_case_contract` 11 passed + 1 xfailed (注入 case #4) · `test_followup_match_full_suite` 4 xpassed · `test_followup_text_full_suite` 1 xpassed
  - **依赖**: T1
  - **估时**: 20 min
  - **产出**: 1 个 commit 边界（本次 working tree）

## 2. 任务依赖图

```text
T1 ──→ T2 ──→ Eval 专项 ──→ 全量 backend ──→ verifier
```

## 3. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | `test_dataset_integrity.py::test_all_eval_dataset_lines_are_valid_json` | 107 行均合法 JSON | REQ-001 | SCN-001 | TC-001 | L1 | worktree（test_dataset_integrity.py）| `e247ecd` (JSONL) + 本次 (测试) | GREEN | PASS | ACCEPTED |
| T2 | `test_digest_llm.py::test_digest_llm_12_case_contract` | 注入 fallback 保持 schema | REQ-002 | SCN-002 | TC-002 | L2 | worktree（conftest.py + runner.py）| 本次 | GREEN | PASS | ACCEPTED |

## 4. 任务↔调研映射

| 对应任务 | 调研关闭条件 | test-cases.md |
|---|---|---|
| 任务 T1 | research § 3.1 条件 1/2/4 | TC-001, TC-002 |
| 任务 T2 | research § 3.1 条件 3/4 | TC-003, TC-004 |

## 5. 总估时与实际

- T1: 20 min → 实际 ~20 min（JSONL `e247ecd` 已 commit + test_dataset_integrity.py working tree 已写）
- T2: 20 min → 实际 ~25 min（含 conftest.py followup_match/text 扩展 + runner.py dispatch 改写）
- 验证与回写: 30 min → 实际 ~10 min
- **总估时**: 1h10m
- **实际**: ~55 min（-19%）

## 6. 实施顺序

1. T1 数据完整性回归先红后绿（JSONL 已 commit `e247ecd` · test_dataset_integrity.py working tree 待 commit） ✅
2. T2 fallback 契约回归先红后绿（conftest.py + runner.py working tree 待 commit） ✅
3. Eval 专项 18 passed / 4 xpassed / 0 failed ✅
4. 测试质量、后端全量 869 passed / 13 xfailed / 15 xpassed / 0 failed ✅
5. 独立 verifier ⏳ 待跑（待 commit 落地）
6. 用户 acceptance ⏳ 待用户拍板

## 7. 验证轮次

| 轮次 | 范围 | 结果 | 偏差 |
|---|---|---|---|
| baseline | Eval + Digest contract | FAIL（13 failed, 7 passed） | 预期红灯 |
| T1+T2 GREEN | 修复 + 新增回归 | PASS | 18 passed / 4 xpassed / 0 failed · 全套 869 passed / 13 xfailed / 15 xpassed / 0 failed |
| verifier-1 | 待跑 | NOT_RUN | 待 commit 落地 |

## 8. Commit 历史

| commit | 日期 | 范围 | 测试 | 偏差 |
|---|---|---|---|---|
| `e247ecd` | 2026-07-28 | JSONL fmatch-017 None→null（v40 治理 · 批 4.1）| 14 failed → 8 failed（-11） | v40 期间完成 · 本任务前置 |
| `6f70bf8` | 2026-07-29 | test_dataset_integrity.py + conftest.py fallback schema-valid + runner.py followup_text dispatch + test_followup_match/text xfail | 4/4 GREEN + 18 passed / 4 xpassed / 0 failed | T1+T2 working tree 落地 · 一并补 task.yaml + tasks.md |

## 硬性 DOD

- [x] 每个任务 ≤1h
- [x] 每个任务对应自动化测试
- [x] 依赖关系明确
- [x] Eval 专项 0 failed
- [ ] 独立 verifier PASS
- [ ] 用户 acceptance
