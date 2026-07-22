---
title: Plan（议题 A+B+C+债务 1 实施计划）
date: 2026-07-22
status: v1 (AI 起草 · 待用户验收)
tags: [plan, 2步, refactor-6]
related:
  - spec.md（业务契约）
  - design-spec.md（设计契约）
  - db-design.md（schema 设计）
  - api-spec.md（接口清单）
  - component-spec.md（组件契约）
  - research.md
  - decisions.md
---

# Plan（议题 A + B + C + 债务 1 实施计划）

> **覆盖范围**：🔴 高优先级 4 个议题（A + B + C + 债务 1）
>
> **不在本 plan 范围**：议题 D（🟡 中）/ 议题 F（🟡 中）/ 🟢 低优先级债务 2-8
>
> **业务决策已就绪**（user-approved）：
> - 议题 A + E：联合实施 · service 真调 `graph.ainvoke` + `with_structured_output`
> - 议题 B：按职责拆（lifecycle/runtime/query）—— 🟡 待用户最终确认
> - 议题 C：全力全双工（路径 2）+ LiveKit built-in VAD
> - 债务 1：加复合索引 + 修虚假注释

---

## § 1 实施顺序（推荐）

按风险与依赖排序，**从易到难 + 从独立到耦合**：

| 顺序 | 任务 | 估时 | 难度 | 依赖 |
|---|---|---|---|---|
| **T1** | 债务 1 复合索引 + 修虚假注释 | 0.5h | 🟢 易 | 无 |
| **T2** | 议题 B 按职责拆 interview.py | 2h | 🟡 中 | 无（无反向依赖）|
| **T3** | 议题 A + E 联合 · service 接 `graph.ainvoke` + `with_structured_output` | 1.5h | 🟡 中 | 无（graph 与 agent 独立）|
| **T4** | 议题 C LiveKit 全双工（启用 client + 整合 worker）| 2h | 🔴 难 | 无（前端独立）|

**总估时**：6h AI 工作量（按 CLAUDE.md § 6.1 每 commit 必配单测）

**推荐顺序理由**：
- T1（索引）：**最快胜利** · 验证 `_run_migrations()` 流程 · 修 4 处虚假注释/声明（决策偏差）
- T2（拆 interview.py）：**零反向依赖** · 拆完即可测 13 端点 · 与 T3/T4 并行不冲突
- T3（graph + with_structured_output）：**与 E 强耦合必须联合**（决策 1）· 单测先建立 Pydantic schema
- T4（LiveKit）：**风险最高** · 涉及 client + worker 整合 · 留最多 buffer

---

## § 2 方案对比（每议题 ≥ 2 方案）

### § 2.1 T1 债务 1 · 加复合索引

| 方案 | 描述 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| **A. 直接 ALTER TABLE** | 在 `_PHASE1A_INDEX_DDL` 加 `CREATE INDEX IF NOT EXISTS idx_user_status` | 简单 · 立即生效 · 与现有迁移体系一致 | 不能回滚（无 downgrade）| ✅ |
| B. Alembic 替换 `_MIGRATIONS` | 用 Alembic 生成 migration 文件 | 可回滚 · 多环境一致 | 改造工作量大（决策 3 用户已选 C 暂缓）| ❌ |

**推荐 A**：债务 1 是 🟢 低优先级 · 不值得为此启动 Alembic。

### § 2.2 T2 议题 B · 按职责拆 interview.py

| 方案 | 描述 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| **A. 按职责拆** | `interview_lifecycle.py` (4 端点) + `interview_runtime.py` (5 端点) + `interview_query.py` (4 端点) | 简单 · 零反向依赖 · 13 端点自然分组 | 跨文件共享 `_livekit_workers` 字典需协调 | ✅ |
| B. CQRS 分离 | 写操作 vs 读操作分文件 | 更严谨 | 对单用户项目过度设计 | ❌ |
| C. 保留单文件 | 团队约定避免互相改 | 最小动作 | 问题仍存在 · 文件继续增长 | ❌ |

**推荐 A**（决策 2 默认）：research.md § 三 已确认零反向依赖。

### § 2.3 T3 议题 A + E 联合 · service 接 graph.ainvoke + with_structured_output

| 方案 | 描述 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| **A. 先 with_structured_output 再 service 接 graph**（顺序：E → A）| PR1: `evaluate_agent` + `report_agent` 改 Pydantic · PR2: `interview_service` 真调 `graph.ainvoke` | 单测先建立 Pydantic 边界 · 失败可回滚 | 2 个 PR 顺序有依赖 | ✅ |
| B. 一次 PR 同时改 service + agent | 一次性把 service 接 graph + agent 改 Pydantic | 1 个 PR | 单测覆盖困难 · 失败回滚范围大 | ❌ |
| C. 换 LangGraph 2.x / `create_agent` | 升级到声明式 framework | 上限更高 | 议题 E 决策 = 不升级（决策 1）| ❌ |

**推荐 A**：A 与 E 强耦合（议题 A 不解决 = E 单独修没意义）· 但单测先建边界能降低风险。

### § 2.4 T4 议题 C · LiveKit 全双工

| 方案 | 描述 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| **A. 改造 room.tsx · 删除 livekit_worker.py · 用 `interview_room.py`** | 删除 61 行 `livekit_worker.py`（dead code）· 在 `interview_room.py` 加 LiveKit client 同步驱动 · room.tsx 用 `<LiveKitVoice>` | 消除 dead code + 整合 worker · 最小改动 | 需要读 `interview_room.py` 300 行代码 | ✅ |
| B. 重写 `livekit_worker.py` 为新 client | 保留 61 行文件 · 改写为 LiveKit Agents Framework | 文件名不变 | 61 行升级 300+ 行 · 改动大 | ❌ |
| C. 保留两个 worker · 只换前端组件 | room.tsx 用 `<LiveKitVoice>` · 后端不动 | 最小后端改动 | dead code 仍存在 · worker 仍阻塞 | ❌ |

**推荐 A**：彻底解决"两份独立 worker"问题 · 与 design-spec.md § 3 改动点一致。

---

## § 3 风险 + 缓解

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | **T3 graph.ainvoke 切换时 状态字段语义变化**（如 `questions_asked` 由 reducer 维护）| 🟡 中 | 单测覆盖所有 reducer 字段（`states.py` L26-32 已用 `Annotated[list, operator.add]`）· 跑回归测试 |
| 2 | **T2 拆分后 `_livekit_workers` 字典跨文件协调** | 🟡 中 | 用 FastAPI Depends 注入（不用全局 dict）· 单测覆盖 lifecycle/runtime 共享场景 |
| 3 | **T4 LiveKit client 端到端延迟不达标**（P95 < 800ms）| 🔴 高 | 先跑 staging 性能基线 · 如不达标用方案 B（重写 worker）· 加 retry/backoff |
| 4 | **T4 前端 LiveKit token 与 worker `interview_room.py` 互连** | 🟡 中 | 现有 `/api/interviews/livekit-token` API · 复用即可 · 单测覆盖 token 签发 |
| 5 | **债务 1 加索引触发锁表**（10k+ 行时）| 🟢 低 | MySQL `ALTER TABLE ADD INDEX` 是 online DDL · 不影响读 · 单测验证 |
| 6 | **测试覆盖率可能不达标**（CLAUDE.md § 6.3 强制 ≥ 80%）| 🟡 中 | 每 commit 必配单测（[V4 决策 1](../2026-07-17-new-feature-ai-push/decisions.md) 假绿灯教训）· verifier 跑 `pytest --cov` |

---

## § 4 决策记录（与 decisions.md 主账联动）

| 决策 | 状态 | 影响 plan |
|---|---|---|
| 决策 1 议题 C 全力全双工 | ✅ | T4 实施路径 |
| 决策 2 议题 B 按职责拆 | 🟡 待最终确认 | T2 待确认才能实施 |
| 决策 7 议题 C 实施范围（全部语音路径）| ✅ | T4 包含 room + setup + 入口 3 页面（design-spec 仅 room · 范围已聚焦）|
| 决策 8 议题 C UI 形态（transcript+语音）| ✅ | design-spec.md § 3 已锁定 |
| 决策 9 议题 C VAD（LiveKit built-in）| ✅ | T4 不需要客户端 VAD 实现 |
| [V4 决策 1](../2026-07-17-new-feature-ai-push/decisions.md) 假绿灯处置 | 🔴 执行中 | T1-T4 每 commit 必须有真测试 · 防止假绿灯 |
| [V4 决策 2](../2026-07-17-new-feature-ai-push/decisions.md) 数字偏差 | 🔴 执行中 | T1 顺手修正 docs/issues.md L217 |

---

## § 5 估时与里程碑

| 阶段 | 时间 | 累计 |
|---|---|---|
| T1 债务 1 | 0.5h | 0.5h |
| T2 议题 B 拆 | 2h | 2.5h |
| T3 议题 A + E | 1.5h | 4h |
| T4 议题 C | 2h | 6h |
| 缓冲（含回归 + verify）| 2h | **8h 总** |

**实施窗口**：建议 1 个工作日内完成（早 9 点开工 → 下午 5 点收工）。

---

## § 6 实施原则（CLAUDE.md § 一 + § 六 强约束）

1. **每 commit 必配单测**（CLAUDE.md § 6.1）· [V4 决策 1](../2026-07-17-new-feature-ai-push/decisions.md) 假绿灯教训
2. **每 commit 后开 verifier agent**（CLAUDE.md § 6.7）· 独立 prompt · 不复用 writer 上下文
3. **commit 后立即回写 tasks.md**（CLAUDE.md § 6.5）· `- [x] T<n>: ✅ DONE — commit hash`
4. **verify 后自动写 retro.md**（CLAUDE.md § 6.6）· 含 memory 候选
5. **调研产物同步**（CLAUDE.md § 6.8 v2）· 任何新决策同步到 6 处

---

## § 7 § 2 计划配套产物

按 checklist.md § 2 触发条件：

| 文档 | 触发 | 状态 |
|---|---|---|
| **plan.md**（本文件）| refactor-6 必填 | ✅ 已写 |
| **db-design.md** | 议题 C transcript 表增量 + 债务 1 加索引 | ✅ 已写（见同目录）|
| **api-spec.md** | 13 端点拆分 + LiveKit token + transcript 推送 | ✅ 已写（见同目录）|
| **component-spec.md** | LiveKitVoice + ReconnectToast | ✅ 已写（见同目录）|

---

## 🎯 硬性 DOD（plan.md 完成必须全过）

- [x] ≥ 2 方案对比（4 个议题每个都有 2-3 方案）
- [x] 单一推荐（每议题 1 个 ✅ 推荐方案）
- [x] 风险 + 缓解（6 条风险）
- [x] 决策记录（与 decisions.md 主账联动）
- [x] 估时（总 8h · 含 2h 缓冲）
- [x] § 2 配套产物（plan + db-design + api-spec + component-spec）
- [ ] **用户验收签字**（待用户确认）

---

## ✍️ 验收区

请回复以下任一：
- **"plan 验收通过 · 下一步拆任务"** → 我立即写 § 3 拆分（tasks.md · 4 个 T 原子任务）
- **"plan 调方案 X"** → 修订具体方案
- **"plan 调估时 Y"** → 修订估时
- **"再想想"** → 停在 plan 阶段等讨论