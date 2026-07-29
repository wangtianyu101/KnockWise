---
title: Test Cases · Digest bookmark 404 full-suite event-loop flake
date: 2026-07-29
status: passed
type: test-cases
---

# Test Cases

## 0. 测试策略

- 先以全量 suite 保留顺序相关 RED，再用局部 mock 隔离真实 DB。
- 自动化覆盖率目标：≥ 80%（本次改动仅测试边界；目标行为分支 100% 覆盖）。
- 依次验证单 case、目标文件、backend 全量，避免单跑假绿。

| ID | 场景 | 命令 | 期望 |
|---|---|---|---|
| TC-01 | 删除不存在 bookmark | `pytest ...::test_delete_bookmark_404_when_missing` | 404；mock scalar await 1 次 |
| TC-02 | Digest API 文件回归 | `pytest tests/api/test_digest_api.py -q` | 0 failed |
| TC-03 | Backend 全量回归 | `pytest tests --tb=short -q` | 0 failed |
