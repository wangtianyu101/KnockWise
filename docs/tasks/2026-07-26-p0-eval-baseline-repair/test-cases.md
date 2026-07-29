---
title: P0 AI Eval 基线修复 · 测试用例
type: test-cases
step: 4
date: 2026-07-26
status: red
tags: [p0, eval, regression]
related: [tasks.md, research.md]
---

# P0 AI Eval 基线修复 · 测试用例

## 0. 测试策略

- **自动化覆盖率目标**: ≥ 80%（实际 100% 覆盖本批两个根因）。
- **手测场景**: 0；全部为确定性离线测试。
- **E2E 场景**: 1；完整读取 107 行并运行 6 类 agent Eval。
- **回归测试**: JSONL 语法、Python `None`→JSON `null` 语义、Digest 注入 fallback schema。

## 1. 验收测试

| TC | 场景 | 类型 | 自动化 | 手测脚本 | 实际结果 |
|---|---|---|---|---|---|
| TC-001 | 107 行逐行合法 JSON | failure | `test_dataset_integrity.py::test_all_eval_dataset_lines_are_valid_json` | — | RED |
| TC-002 | fmatch-017 的 null 解析为 None | edge | `test_dataset_integrity.py::test_prompt_injection_expected_branch_is_null` | — | RED |
| TC-003 | Digest 正常 mock 结构化 | happy | `test_digest_llm.py::test_digest_llm_12_case_contract` | — | 7/8 PASS |
| TC-004 | Digest 注入 fallback 仍满足结构化 schema | security | `test_digest_llm.py::test_digest_llm_12_case_contract` | — | 1/8 FAIL |
| TC-005 | 六类 Agent Eval 完整运行 | regression | `backend/tests/eval/test_*.py` | — | 12 FAIL |

## 2. 自动化测试

| 自动化测试 | 对应 TC | 覆盖范围 |
|---|---|---|
| `backend/tests/eval/test_dataset_integrity.py` | TC-001/002 | 数据集语法与 null 语义 |
| `backend/tests/test_digest_llm.py` | TC-003/004 | Digest schema/fallback |
| `backend/tests/eval/test_*.py` | TC-005 | 6 agent 套件 |

**覆盖率**：目标 5/5 场景自动化 = 100%。

## 3. 手测场景

- 无：本任务没有浏览器、数据库或网络边界。

## 4. 回归测试

| 旧功能 | 自动化测试 | 验证点 |
|---|---|---|
| 107-case Eval fixture | `test_dataset_integrity.py` | 每行可解析且 case_id 唯一 |
| Digest schema contract | `test_digest_llm.py` | 正常/注入均 JSON |
| 六类 Agent runner | `tests/eval/test_*.py` | 原有数量与不变量保持 |

## 5. 边界 case

- [ ] JSON `null` 解析为 Python `None`。
- [ ] prompt-injection fallback 不回显恶意输入。
- [ ] fallback `quality_score` 在 0..1。

## 6. Bug 回归测试

- [ ] 非法 `None` 不再进入 JSONL。
- [ ] fallback 普通文本不再破坏 JSON parser。
