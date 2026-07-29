---
title: Research · Digest bookmark 404 full-suite event-loop flake
date: 2026-07-29
status: accepted
mode: fix-mini
type: research
related:
  - ../../2026-07-28-fix-v40-pytest-env/research.md
---

# Research · Digest bookmark 404 full-suite event-loop flake

路径模式: `fix-mini`

## 1. 任务理解

- **用户原话**：「修（1 failed + 168 errors · 1-2h · 🟡 高风险 · 跨任务）」；复跑后用户进一步要求「把这一个failed修了把」。
- **现象**：规范全量命令得到 `1 failed, 865 passed, 2 skipped, 17 xfailed, 10 xpassed`，历史 `168 errors` 当前无法复现。
- **目标**：只修 `TestBookmarkAPI::test_delete_bookmark_404_when_missing`，不顺带处理 17 个 xfail 或其他任务改动。
- **路径模式**：`fix-mini`（0→4→6）。原建议 full-6 因当前只剩单个测试隔离缺陷而降级；用户已明确要求只修这一个 failed。

## 2. 复现路径

```bash
cd backend && ./.venv/bin/python -m pytest tests --tb=short -q
# 1 failed, 865 passed, 2 skipped, 17 xfailed, 10 xpassed
```

失败：`tests/api/test_digest_api.py::TestBookmarkAPI::test_delete_bookmark_404_when_missing`，报 `Future attached to a different loop`。

单独运行该 case 为 `1 passed`，整文件也通过但产生 aiomysql 连接跨 loop/关闭后回收警告，证明是顺序相关的测试隔离问题。

## 3. 影响范围与关闭条件

相关文件：

1. `backend/tests/api/test_digest_api.py`：失败测试未注入 DB，误连真实 MySQL。
2. `backend/api/digest/bookmarks.py`：endpoint 直接使用模块级 `async_session()`。
3. `backend/core/database.py`：模块级 async engine/pool 会把连接绑定到创建它的 event loop。
4. `backend/tests/conftest.py`：没有替该 router 隔离模块级 session；不计划在共享 fixture 中做全局补丁。

关闭条件：

- [ ] 先保留全量失败证据（已完成）。
- [ ] 测试使用本地 mock session，不访问真实 MySQL。
- [ ] 单 case、整文件、全量 backend pytest 均 0 failed。
- [ ] 不改业务行为，不修改 `.env.local`，不覆盖其他任务工作区改动。
- [ ] 独立 verifier 对照本报告并复跑相关测试。

## 4. 根因假设与证据

| 假设 | 证据 | 结论 |
|---|---|---|
| H1：测试未隔离 DB | `make_client(..., db=None)`；endpoint 直接调 `async_session()` | ✅ 主因 |
| H2：业务 404 逻辑错误 | isolated case 返回 404 且通过 | ❌ 排除 |
| H3：共享 engine pool 跨 TestClient event loop 复用连接 | full suite 报 different loop；整文件结束有 connection cleanup / loop closed | ✅ 放大机制 |

根因：测试自称 router 隔离测试，却没有替换 `api.digest.bookmarks.async_session`，导致真实 async engine/pool 被多个 TestClient event loop 使用。修复应落在测试边界，而不是给生产逻辑加重试或全局重建 event loop。

## 5. 最近相关改动与仓库证据

调研已读取 `docs/issues.md`，并执行：

```bash
git status --short --branch
git log --oneline -10 -- backend/tests/api/test_digest_api.py backend/api/digest/bookmarks.py backend/core/database.py
```

- `27580ea`：同文件 bookmark list flake 被标 xfail。
- `6b72d56`：Digest API 7 个失败标 xfail。
- `dd546d9`：T20 重写真实 API case。
- `b41c7e7`：Digest endpoint 初始实现。

## 6. 输出建议

推荐按 `fix-mini` 执行：步骤 0 调研 → 步骤 4 TDD 局部测试隔离 → 步骤 6 小任务按需复盘。只修当前唯一 failed，不扩大到历史 errors、已有 xfail 或生产 DB 依赖重构。

| 风险 | 等级 | 缓解 |
|---|---|---|
| 修改共享 conftest 影响 800+ case | 🔴 | 不改共享 fixture，只对该测试局部注入 |
| 修改生产 DB 依赖引入 API 回归 | 🟡 | 本批只修测试隔离，不改 endpoint 行为 |
| 单跑假绿、全量仍失败 | 🟡 | 必须复跑单 case、整文件和全量 |
| 覆盖并行任务未提交改动 | 🟡 | 仅改新任务文档和目标测试 |

推荐：局部 monkeypatch `bookmarks.async_session` 为异步 context manager，返回 `AsyncMock.scalar(None)`；这是最小根因修复。

## 7. 决策

用户决定只修当前唯一 failed，范围不含历史 168 errors、17 xfailed 或生产重构。详细主账见 [decisions.md](decisions.md)。
