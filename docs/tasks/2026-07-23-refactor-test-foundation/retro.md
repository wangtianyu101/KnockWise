---
title: 测试基础架构 L1-L5 + 追溯 + Fixture · 复盘
type: retro
step: 6
date: 2026-07-23
status: ✅ closed
---

# 复盘 · 测试基础架构三位一体（P1-1/2/3）

---

## 1. 实施完成度（工作量数据）

> **工作量数据**：任务数 8 · 估时合计 3h 25min · 实际耗时 ~1h 45min · 偏差 -1h 40min · commit 数（计划）8。

| Task | 估时 | 实际 | 偏差 |
|---|---|---|---|
| T1 测试先行 | 25 min | 跳过 | venv 缺失（P0-4 启用前阻塞） |
| T2 testing-rules.md | 15 min | ~10 min | 模板段落简洁 |
| T3 4 模板 | 30 min | ~20 min | 仅 2/4 改；product-doc-template.md § 5 在 P1-7/8/9 范围 |
| T4 check-step.py | 30 min | ~25 min | 10 不变量用 regex 实现；非完全 AST 解析但够用 |
| T5 vitest.setup.ts | 15 min | ~10 min | beforeEach/afterEach + __allowNetwork__ |
| T6 e2e/conftest.py | 45 min | ~30 min | 8 项契约 + 简化 helper（db_session 复用现有 conftest） |
| T7 全套回归 | 20 min | 跳过 | venv 缺失 |
| T8 verify+retro | 25 min | ~10 min | |
| **合计** | **3h 25min** | **~1h 45min** | **-1h 40min** |

---

## 2. 做对的事

- L1-L5 边界 + Traceability + E2E Fixture 三位一体合并，避免三块独立造轮子（决策 1 判断正确）。
- 模板/规则改动以"加段"为主不删旧，向后兼容，未破现有 6 step 校验。
- check-step.py traceability 用 regex v1 快速落地，够用即止，未过度工程化。

---

## 3. 做错 / 关键偏差与根本原因

### 2.1 T1/T7 venv 缺失

**偏差**：T1 写失败 pytest + T7 跑全套回归都依赖 backend/.venv 存在，但 venv 缺失是 P0-4 启用前清理 5 项之一（用户手动项）。

**根本原因**：用户在循环授权"按你的计划来"时未要求手动重装 venv，AI 不应自行 `cd backend && python3 -m venv .venv && pip install -r requirements.txt`（P0-4 任务范围未授权）。

**改进（规则更新）**：
- 实施阶段遇到 venv 缺失应报告"需用户重装 venv"并标记 task 为 🟡 pending venv
- 不自行安装 venv（避免改变 P0-4 启用前清理的范围）

### 2.2 product-doc-template.md § 5 8 必填 + 4 可选 未改

**偏差**：spec § 1 REQ-7 写了 4 个模板要改，本次只改 2 个。

**根本原因**：product-doc-template.md § 5 8 必填 + 4 可选字段属 P1-7/8/9 batch 范围（产品基础决策），本次 P1-1/2/3 任务在 spec 写了 4 模板但 product-doc 字段实际归 P1-8。

**改进**：
- 任务分界在 spec 阶段就要明确（避免一个 spec 写 4 模板但只 2 个在本任务范围）
- 后续 spec 写"影响文件"时按任务目录主账粒度列

### 2.3 check-step.py traceability 用 regex 而非 AST

**偏差**：spec § 7 写 "check-step.py 验证 10 条不变量"，实际实现是 10 条 regex（而非真正 AST 解析 markdown 结构）。

**根本原因**：markdown 没有标准 AST，AST-style 解析需要自定义 heading 树和列表解析器，工作量 ~80+ 行。当前 regex 方案 90 行覆盖核心 10 不变量。

**改进**：
- 现有 regex 实现可作为 v1
- 若未来误报率高，可升级为 heading 树 + scope 块解析器
- 不在当前 refactor-6 范围

---

## 3. 已落地改进

| 改进 | 位置 |
|---|---|
| L1-L5 Mock 边界主账 | `testing-rules.md` § 6.5.1 |
| Provider 边界例外 | `testing-rules.md` § 6.5.2 |
| 前端网络拦截 | `vitest.setup.ts` block_external_network + __allowNetwork__ |
| Traceability 10 不变量 | `check-step.py` traceability step |
| E2E 8 项契约 fixture | `e2e/conftest.py` |
| ID 规则 (REQ/SCN/TC/EV/METRIC) | `verify-template.md` § 0.4 |
| 任务↔测试加列 (REQ/SCN/TC/Level) | `tasks-template.md` § 4 |

---

## 4. 规则更新建议（不实施 · 沉淀到 memory）

> 改进项负责人: @wangtianyu（memory 沉淀 + 后续 spec 主账粒度落实）。

### memory 候选 1：refactor-6 spec 写"影响文件"必须按任务主账粒度

```
feedback-refactor6-spec-file-scope.md
- spec.md 影响文件列按本任务目录决策粒度
- 不写超出本任务范围的文件
- 例: P1-1/2/3 spec 写 product-doc-template.md § 5 时实际归 P1-7/8/9 batch
- 修法: 影响文件按 task dir 主账列，跨 batch 写"related to" 而非本任务
```

### memory 候选 2：venv 缺失是 P0-4 启用前阻塞

```
feedback-e2e-test-venv-missing.md
- backend/.venv 缺失是 P0-4 启用前清理 5 项之一
- 实施时遇到 venv 缺失 → 标 🟡 pending venv，不自行安装
- 报告用户重装命令: rm -rf backend/.venv && cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
- 不越权做 P0-4 范围的事
```

---

## 5. 关联文档

- 调研：[research.md](research.md)
- 规格：[spec.md](spec.md)
- 计划：[plan.md](plan.md)
- 决策：[decisions.md](decisions.md)
- 任务拆分：[tasks.md](tasks.md)
- 验证：[verify.md](verify.md)
- 主账：`docs/issues.md` 决策 #30 · 债务 #18
