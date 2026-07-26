---
title: P0 空模板 DOD Gate · 测试用例
type: test-cases
step: 4
date: 2026-07-26
status: executed
tags: [p0, dod, regression]
related: [research.md, tasks.md]
---

# P0 空模板 DOD Gate · 测试用例

## 0. 测试策略

- **自动化覆盖率目标**: ≥ 80%；本任务 5/5 场景自动化，实际为 100%。
- **手测场景**: 0；使用真实 CLI subprocess。
- **E2E 场景**: 1；从实际模板文件进入 checker CLI。
- **回归测试**: 原阶段 checker、P0-1 Hook 退出码和 CI 共享调用链。

## 1. 验收测试

| TC | 场景 | 类型 | 自动化 | 手测脚本 | 实际结果 |
|---|---|---|---|---|---|
| TC-001 | 7 类原样步骤模板均返回非零 | failure | `TestTemplateResidueGate::test_repository_templates_are_rejected` | — | PASS（10/10 模板 rc=1） |
| TC-002 | 复制改名但仍含占位的模板返回非零 | security | `TestTemplateResidueGate::test_renamed_template_with_placeholders_is_rejected` | — | PASS |
| TC-003 | 合法阶段文档仍通过 | happy | 既有 `TestSixStepWorkflowV2` | — | PASS |
| TC-004 | JSX、路径参数和性能比较符不误伤 | edge | `TestTemplateResidueGate::test_technical_angle_brackets_are_not_placeholders` | — | PASS |
| TC-005 | CLI 输出明确原因且退出码为 1 | regression | `TestTemplateResidueGate::test_cli_reports_template_residue` | — | PASS |

## 2. 自动化测试

| 自动化测试 | 对应 TC | 覆盖范围 |
|---|---|---|
| `backend/tests/test_check_step.py` | TC-001~005 | 共享 Gate、CLI rc、兼容边界 |
| `backend/tests/test_pre_commit_hook.py` | TC-003/005 | 非零退出码继续被 Hook 传播 |

**覆盖率**：5/5 场景 = 100%。

## 3. 手测场景

- 无；本任务不涉及浏览器、数据库或网络。

## 4. 回归测试

| 旧功能 | 自动化测试 | 验证点 |
|---|---|---|
| 6 步 v2 合法短文档 | `TestSixStepWorkflowV2` | 合法输入不被误伤 |
| Markdown bold 兼容 | `TestCheckTasksBoldTolerance` | tasks 字段格式保持 |
| Hook 非零传播 | `test_pre_commit_hook.py` | checker 失败仍阻断 |

## 5. 边界 case

- [x] `<Component>` 与 `<id>` 是技术语法，不是填空占位。
- [x] `< 200ms` 是比较符，不是 Markdown 占位。
- [x] 单处说明性 `Scenario: <场景名>` 不直接判整文档为空。
- [x] 两处以上高置信度未填写语义会阻断复制空壳。

## 6. Bug 回归测试

- [x] `spec-template.md` 不再返回 0。
- [x] `tasks-template.md` 不再返回 0。
- [x] `test-cases-template.md` 不再返回 0。
- [x] `verify-template.md` 不再返回 0。
- [x] `retro-template.md` 不再返回 0。

## 7. TDD 证据

- **RED**：`7 failed, 6 passed`；原 checker 对五类模板、复制改名模板和 CLI 原因均未阻断。
- **GREEN**：`14 passed`；模板残留 Gate 和误伤边界全部通过。
- **治理回归**：`77 passed`。
- **测试质量**：7 files / 68 AST tests / 0 violations。
- **独立 verifier**：PASS；独立重跑 77/77、专项 14/14、模板 CLI 10/10 rc=1，对抗样本 rc=1/0。
