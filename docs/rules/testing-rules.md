# 单测规则详情（CLAUDE.md § 六）

> **来源**：原 CLAUDE.md § 六.1 + § 六.2（2026-07-17 拆出 · § 六.3+ 保留在 CLAUDE.md）
> **触发**：实施阶段（步 4）写代码 / 修测试时读

## § 6.1 适用范围

| 类型 | 必须测 | 说明 |
|---|---|---|
| **新 service 函数** | ✅ | 至少 1 个 happy path + 边界条件 |
| **新 endpoint** | ✅ | schema 校验 + happy path + 失败路径 |
| **新 schema (Pydantic)** | ✅ | 必填字段 + Literal 校验 + 边界值 |
| **新组件 (UI)** | 🟡 推荐 | 测核心交互逻辑（不用 mount 整个页面） |
| **类型定义 (`types/`)** | 🟡 推荐 | 字段对齐校验（防 schema drift） |
| **Bug 修复** | ✅ | 加回归测试防止复发 |
| **配置/常量** | ❌ 不需要 | — |

## § 6.2 测试基础设施

| 端 | 框架 | 命令 | 位置 |
|---|---|---|---|
| 后端 | **pytest** | `cd backend && ./.venv/bin/python -m pytest tests/ -v` | `backend/tests/test_*.py` |
| 前端 | **vitest** + RTL + happy-dom | `cd frontend && npm test` | `frontend/**/*.test.{ts,tsx}` |

## § 6.3 有效测试判定（Harness Gate）

测试被 pytest / Vitest 收集，不等于测试有效。新增或修改测试必须至少包含一个能在行为错误时失败的 **oracle**：

- Python `assert`、`pytest.raises`、Mock `assert_*`；
- 前端 `expect(...)`、用户交互后的可观察状态；
- helper 内显式断言或抛错（调用点必须能追溯到该 helper）。

以下情况一律视为无效测试并阻断 CI：

- 函数体只有 `pass`、`...`、docstring、注释或占位返回值；
- 包含 `placeholder` / `TODO` / `FIXME` 且没有关联 issue 与明确 `skip` 原因；
- 只验证“没有抛异常”、列表非空或 Mock 返回了自身配置值，不能证明需求；
- `skip` / `xfail` 未写原因或 issue；二者必须单独统计，禁止计入 passed；
- 测试文件放进 Next.js `pages/` / `app/` 路由树，导致测试被构建成页面。

提交前必须运行：

```bash
python3 scripts/check_test_quality.py backend/tests
```

## § 6.4 需求链路与断言

- API 集成测试至少验证 HTTP 状态、响应契约和数据库最终状态；写操作还要验证重复请求与权限边界。
- Provider 契约测试只 Mock 公共 provider 边界，不 Patch service 的私有方法来证明 service 正确。
- 异步方法使用 `AsyncMock`，同步方法使用 `Mock`；新增测试产生的 unawaited coroutine / RuntimeWarning 必须处理，不能当作绿灯噪声。
- RSS / LLM fixture 固定且默认禁止公网；必须覆盖解析/输入契约、异常和降级，不只验证返回非空。
- 核心逻辑至少保留一条“故意破坏后会变红”的证据：可用 mutation test，或临时反转条件并记录失败测试；验证后恢复代码。

## § 6.5 E2E Mock 边界

每个 E2E 必须在测试或 `verify.md` 列出真实层与 Mock 层。名称、目录和 docstring 不能证明它是 E2E。

Digest Harness 的允许 Mock 边界仅为：**RSS 网络、LLM、Email、Clock**。以下内部层必须走真实代码：

```text
Scheduler → Service → ORM → 隔离测试数据库 → FastAPI API
```

禁止在同一条“真实 E2E”中 Mock Scheduler、目标 Service、ORM、数据库或目标 API handler。若环境无法提供真实层，必须降级命名为 integration/unit，并在验证结论中写 BLOCKED，不能包装为 E2E passed。

E2E 必查：外部源部分失败的降级、持久化结果、API 查询同一数据、重复执行、进程重启后的幂等、启动与关闭路径。

### § 6.5.1 L1-L5 边界主账（per P1-1 决策）

| 层 | 必真实 | 允许 Mock | 禁止 | 触发命令 |
|---|---|---|---|---|
| L1 单元 | 被测函数 | 纯 fixture · 时间 (freezegun) | 框架 Runtime | `pytest tests/services -q` |
| L2 服务集成 | service 公开方法链 | db · cache · clock · llm · email · rss | service 私有方法 | `pytest -m "not e2e"` |
| L3 API 集成 | router + Pydantic 422 | db (AsyncMock) · get_current_user | mock 整个 handler | `pytest tests/api` + `pytest tests/integration` |
| L4 E2E | scheduler + service + ORM + DB + API | 仅 rss · llm · email · clock | mock 上述 5 层任何 | `RUN_MYSQL_INTEGRATION=1 pytest tests/e2e` |
| L5 Staging | 全栈真服务 | 无 | 任何 mock | `verify.md` 引用 |

### § 6.5.2 Provider 边界例外

- `service` 命名形如 `_fetch_and_parse` / `_send_email` 的 provider boundary method 在 L2 中可 patch
- **不得**用来证明 service 内部逻辑正确性，仅用于替换 IO provider

## § 6.6 Gate 矩阵与状态口径

| Gate | 最低证据 |
|---|---|
| test-quality | AST 扫描 0 violations |
| backend-test | pytest 分类计数 + coverage + 隔离 MySQL 集成测试 |
| frontend-test | Vitest + `tsc --noEmit` + Next build |
| browser E2E | Playwright 场景结果；不得依赖公网 |

- Gate 绿只证明本 Gate，不自动推导整个任务 DONE。
- 任务状态只允许：`已实现未验证`、`L1/L2 已通过`、`L3 已通过`、`L5 已通过/完成`、`FAILED/BLOCKED`。
- 证据必须记录 commit、命令、工作目录、环境、时间、退出码和 passed/failed/skipped/xfail 分类计数。
- GitHub workflow 存在不等于能阻断合并；required checks / ruleset 未配置时必须作为外部待办单列。

## § 6.7 关联规则（AGENTS.md 中保留）

- **§ 6.3 自检清单** — 每个代码 commit 前必过的 5 条
- **§ 6.4 违反处置** — 没单测 = 没完成
- **§ 6.5 任务完成自动更新** — `TaskUpdate completed` → 自动改 `tasks.md`
- **§ 6.6 verify 后写 retro** — verify.md commit 后立刻写 retro.md
- **§ 6.7 Verify-Loop** — 实施每步自校验 · 双 agent (`Agent` tool / 升级 `Workflow` tool)
- **§ 6.7.1 进阶路径** — `Workflow` 工具脚本模板在 `.claude/workflows/verify-loop-example.js`
