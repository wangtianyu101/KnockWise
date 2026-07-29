---
title: Tasks · Digest bookmark 404 full-suite event-loop flake
date: 2026-07-29
status: implemented
mode: fix-mini
layer: L1
type: tasks
---

# Tasks · Digest bookmark 404 full-suite event-loop flake

- **layer**: L1
- **总估时**: 1–2h（实际实施约 15min，另含 90s 全量测试 + 独立验证）

## 实施状态

- [x] T1: ✅ 已实施 — commit `e26a80d`
  - 依赖: 无
  - 测试: TC-01, TC-02, TC-03
  - implementation: ✅ implemented（局部 mock async session）
  - test: ✅ target 1/1；Digest API 8 passed；backend full 866 passed / 0 failed
  - verifier: ✅ independent PASS
  - 范围：`backend/tests/api/test_digest_api.py`

## 实施顺序

1. 保留全量 RED 证据：1 failed。
2. 局部 mock `bookmarks.async_session`，让 scalar 返回 None。
3. 跑单 case、整文件、全量 backend pytest。
4. 独立 verifier。

## 状态与 Commit 历史

| 任务 | 测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | bookmark delete 404 | missing bookmark | BUG-01 | SCN-01 | TC-01/02/03 | L1 | `e26a80d` | PASS（866 passed / 0 failed） | PASS | PENDING（待用户验收） |
