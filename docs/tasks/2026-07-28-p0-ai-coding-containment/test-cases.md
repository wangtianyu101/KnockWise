---
title: P0 AI Coding containment · 测试用例
type: test-cases
step: 4
date: 2026-07-28
status: in-progress
tags: [p0, tests, github-actions, ruleset]
related: [research.md, tasks.md]
---

# P0 AI Coding containment · 测试用例

## 0. 测试策略

- **自动化覆盖率目标**：≥ 80%；T1 的 8 个风险场景全部自动化或由真实 API smoke 覆盖，目标 100%。
- **L1**：production CLI 对本地 HTTP server 的真实请求、响应与退出码。
- **L3**：CI wiring、Shell security E2E、官方 GitHub API provenance smoke。
- **L5**：远端 ruleset API 回读。

## 1. 验收测试

| ID | 层级 | 场景 | 输入/前置 | 预期 |
|---|---|---|---|---|
| TC-001 | L1 | 合法完整 SHA 的结构检查 | `owner/repo@40hex` | PASS |
| TC-002 | L1 | 移动 tag | `@main` / `@v1` | FAIL |
| TC-003 | L1 | 伪 40 位 SHA | API 404 | FAIL，包含 repo/ref，不含 token |
| TC-004 | L1 | API 网络错误 | timeout / URLError | BLOCKED/FAIL |
| TC-005 | L1 | 同一 SHA 被不同 repo 使用 | 一个 repo 200，一个 404 | 逐 repo 判定，不能缓存为 SHA-only |
| TC-006 | L3 | governance CI wiring | `ci.yml` | provenance 命令存在、只读 token |
| TC-007 | L3 | Security Shell E2E | 仓库当前 workflow | 四关 PASS 且 provenance wiring 真检查 |
| TC-008 | L3 | 当前三个修复 ref | 官方 GitHub commits API | 全部 200 且返回 SHA 相等 |
| TC-009 | L5 | ruleset enforcement | API 回读 id `19763447` | `active` |
| TC-010 | L5 | required checks 与 bypass | API 回读 | 四个检查；bypass actors 为空 |

## 2. 自动化测试

| 自动化测试 | 对应 TC | 当前结果 |
|---|---|---|
| `scripts/ci/test_check_action_sha.py` | TC-001～005 | 11/11 PASS |
| `scripts/ci/test_security_e2e.sh` | TC-006～007 | PASS |
| `scripts/ci/check_action_sha.py --verify-remote` | TC-008 | PASS |
| GitHub ruleset API readback | TC-009～010 | PENDING |

**自动化覆盖率**：T1 当前 8/8 风险场景有机器证据，100%，达到 ≥ 80% 目标；T2 等远端设置后记录。

## 3. 故意破坏反证

1. 将 `actions/upload-artifact` 的 ref 改回 `de8e...c1ac`，provenance 模式必须非零。
2. 将 API endpoint 指向本地返回 404 的 HTTP server，测试必须断言真实 rc=1。
3. 将 ruleset enforcement 改为 `disabled` 的只读 fixture，解析器必须判 FAIL；不在真实仓库做破坏性切换。

## 4. 回归测试

- 旧的移动 tag、短 SHA、本地 Action 规则继续通过原 6 条测试。
- Workflow security 四关继续由 Shell E2E 覆盖。
- T1：TC-001～008 全部 PASS。
- T2：TC-009～010 API 回读 PASS。
- 任何网络/权限不确定状态不得记录为 PASS。
