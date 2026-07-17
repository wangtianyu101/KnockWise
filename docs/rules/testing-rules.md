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

## § 6.6 关联规则（CLAUDE.md 中保留）

- **§ 6.3 自检清单** — 每个代码 commit 前必过的 5 条
- **§ 6.4 违反处置** — 没单测 = 没完成
- **§ 6.5 任务完成自动更新** — `TaskUpdate completed` → 自动改 `tasks.md`
- **§ 6.6 verify 后写 retro** — verify.md commit 后立刻写 retro.md
- **§ 6.7 Verify-Loop** — 实施每步自校验 · 双 agent (`Agent` tool / 升级 `Workflow` tool)
- **§ 6.7.1 进阶路径** — `Workflow` 工具脚本模板在 `.claude/workflows/verify-loop-example.js`
