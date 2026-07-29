---
title: Decisions · Digest bookmark 404 full-suite event-loop flake
date: 2026-07-29
status: active
type: decisions
---

# Decisions · Digest bookmark 404 full-suite event-loop flake

> 本文件是本任务决策最权威详细主账。调研证据见 [research.md](research.md)；`docs/issues.md` 仅维护状态镜像；测试与实施状态见 [tasks.md](tasks.md)。

## 决策总览

| # | 日期 | 决策项 | 选择 | 状态 | 关联 |
|---|---|---|---|---|---|
| D-001 | 2026-07-29 | 修复范围 | 只修当前 1 failed | ✅ 已决策 | research § 3 |
| D-002 | 2026-07-29 | 路径与方案 | fix-mini；局部测试 DB 隔离 | ✅ 已决策 | research § 6 |

## 决策详细记录

### D-001 · 只修当前唯一 failed

- **日期**：2026-07-29
- **选项**：A. 修当前 1 failed；B. 同时清 17 xfailed；C. 追溯已不可复现的 168 errors。
- **选择**：A。
- **用户原话**：「把这一个failed修了把」
- **理由**：
  1. 当前规范全量基线只有 1 failed、0 errors。
  2. 17 xfailed 已由前序任务登记，扩大范围会跨任务。
  3. 历史 168 errors 当前无复现证据，不能按旧数字猜修。
- **影响文件**：目标测试、新任务文档、`docs/issues.md` 镜像。
- **关联决策**：D-002。

### D-002 · fix-mini + 局部测试 DB 隔离

- **日期**：2026-07-29
- **选项**：A. 局部 patch 测试 session；B. 改生产 endpoint 为 Depends(get_db)；C. conftest 全局重置 engine/event loop。
- **选择**：A。
- **用户原话**：「把这一个failed修了把」
- **理由**：
  1. isolated case 已证明业务 404 行为正确。
  2. 根因是测试未隔离真实 MySQL，而非生产逻辑错误。
  3. 局部 patch 不影响其他 800+ 测试及运行时依赖模型。
- **影响文件**：`backend/tests/api/test_digest_api.py`。
- **关联决策**：D-001。

## 决策落地追踪

| 决策 | 落地项 | 状态 |
|---|---|---|
| D-001 | 仅处理目标 failed | ✅ 已落地（full suite 0 failed） |
| D-002 | 局部 mock async session + 三层测试 | ✅ 已落地；独立 verifier PASS |

## 元信息

- **位置**：`docs/tasks/2026-07-29-bug-bookmark-event-loop-flake/decisions.md`
- **创建日期**：2026-07-29
- **决策总数**：2
- **已决策数**：2
- **待确认数**：0
- **暂缓数**：0
