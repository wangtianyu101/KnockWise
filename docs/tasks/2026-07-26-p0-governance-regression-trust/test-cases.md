---
title: P0 治理回归可信度 · 测试用例
type: test-cases
step: 4
date: 2026-07-26
status: executed
tags: [p0, governance, subprocess, git-index]
related: [research.md, tasks.md]
---

# P0 治理回归可信度 · 测试用例

> 实施 commit：`f1cf815`（2026-07-27）。

## 测试策略

- **自动化覆盖率目标**：≥ 80%；本任务 8/8 场景自动化，目标 100%。
- 关键 case 通过 `subprocess.run` 执行生产 CLI，并同时断言退出码与稳定输出。
- Git 语义在临时仓库内验证，不读写真实仓库 INDEX。

## 验收测试

| TC | 场景 | 类型 | 自动化 | 实际结果 |
|---|---|---|---|---|
| TC-001 | 合法 worktree manifest CLI rc=0 | happy | `test_check_task.py` | PASS |
| TC-002 | 非法 manifest CLI rc=1 | failure | `test_check_task.py` | PASS |
| TC-003 | 缺 manifest CLI rc=2 | failure | `test_check_task.py` | PASS |
| TC-004 | CLI 缺必填参数 rc=3 | edge | `test_check_task.py` | PASS |
| TC-005 | staged 合法、worktree 非法时 INDEX rc=0 | regression | `test_check_task.py` | PASS |
| TC-006 | INDEX 缺 manifest、worktree 存在时仍 rc=2 | regression | `test_check_task.py` | PASS |
| TC-007 | CI CLI 阻断缺 manifest commit | e2e | `test_check_governance.py` | PASS |
| TC-008 | CI CLI 接受合法 manifest commit | e2e | `test_check_governance.py` | PASS |

## 回归与边界

- workflow 文本测试只声明为 wiring/security contract，不计入行为 E2E。
- Hook 测试继续执行复制自当前生产文件的完整 Shell 入口。
- 无浏览器、数据库、网络或手工场景。

## TDD 证据

- **RED**：`3 failed, 3 passed`；缺 manifest 两个场景返回 1 而非 2，调用错误返回 2 而非 3。
- **GREEN**：CLI 专项 `6 passed`。
- **治理回归**：七文件 `84 passed`；测试质量 7 files / 75 tests / 0 violations。
- **独立 verifier**：PASS；独立选择集 81 passed，CLI rc 0/1/2/3 与 INDEX 对抗均符合。
- **全后端参考**：808 passed / 10 failed / 2 skipped / 4 xfailed；失败集中于并行 Auth 改动及既有 Digest/MySQL fixture，未纳入 P0-3 通过证据。
