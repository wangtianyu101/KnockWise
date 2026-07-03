---
title: 方案文档 · V2 智能沉淀层
date: 2026-06-28
status: 🚧 **草稿 — 等你拍板 7 个决策点后再冻结**
tags: [plan, 2步, 方案, v2, 智能沉淀, 待拍板]
related:
  - [research.md](research.md) — 0 步调研
  - [product-doc.md](product-doc.md) — 1 步产品脑
  - [design-spec.md](design-spec.md) — 1 步设计脑
  - [spec.md](spec.md) — 1 步技术脑（已冻，下游基准）
  - _api-spec.md — 🔒 **未生成**，等本文件决策冻结后重新生成
  - _component-spec.md — 🔒 **未生成**，等本文件决策冻结后重新生成
---

# 方案文档：V2 智能沉淀层

> **作者**：AI 主导（写多方案对比 + 列判断点），**方案选择权交回你**
>
> **下游文档状态**：
> - ✅ spec.md 已冻结（1 步产物，技术契约 = 基准）
> - ✅ 决策已拍板（7/7 全 A，2026-06-28）
> - 🚧 api-spec.md 准备生成
> - 🚧 component-spec.md 准备生成
>
> **当前状态**：✅ **PLAN 冻结**（7 决策 = 全 A），下游文档生成中

---

## 0. ⚠️ 等你拍的 7 个决策点（顶层摘要）

> ✅ **2026-06-28 你拍板：7/7 全 A**

| # | 决策点 | 选项 | 状态 |
|---|---|---|---|
| **1** | 总体架构路径 | **✅ A 同步触发链** | 已拍 |
| **2** | LLM 缓存策略 | **✅ A Redis TTL 1h** | 已拍 |
| **3** | 触发点位置 | **✅ A service 内** | 已拍 |
| **4** | 是否拆 interview.py 803 行 | **✅ A 顺手拆** | 已拍 |
| **5** | V2 是分 PR 还是单 PR | **✅ A 分 3 PR** | 已拍 |
| **6** | 是否新建 `/profile` 页 | **✅ A 新建** | 已拍（多 1h） |
| **7** | settlement/Obsidian 写失败处理 | **✅ A 不抛异常 + log** | 已拍 |

---

## 1. 方案对比 · 已选定（推荐方案 = A）

> ✅ **已选定方案 A**（同步触发链）。本节保留对比供未来 V3+ 选 B 时参考。

### 方案 A: 同步触发链

```markdown
- 思路: service A 写完后内部同步调 service B（settlement / obsidian / summary cache 失效）。失败用 try/except 兜底 log，不阻塞主业务。
- 优点:
  - 实现简单，5-7h 完工
  - 调用栈清晰，debug 容易
  - 0 新增依赖
  - 与 V1 模式一致
- 缺点:
  - Service 内调 service 有循环依赖风险（用 triggered_by 显式方向缓解）
  - Obsidian 写失败只 log（无重试）
  - LLM 同步调会 block 接口响应（用 Redis 缓存缓解）
- 风险等级: 🟡
- 工作量: 5-7h
- 兼容性: ✅ 完全兼容
- 测试影响: 现有 367 测试不动
```

### 方案 B: 事件总线（异步解耦）

```markdown
- 思路: service 写完发 Event 到 Celery / Redis Streams，后台 worker 监听 Event 触发 settlement / obsidian / summary。
- 优点:
  - 完全解耦，可重试 + DLQ
  - 可视化监控（flower）
  - LLM 调用异步化
  - 天然支持批量触发
- 缺点:
  - 新增 Celery + broker + 监控基础设施
  - 工作量 12-15h（vs A 的 5-7h）
  - Debug 链路长（4 跳）
  - V1 没用 Celery，V2 引入 = 给项目增加架构方向
- 风险等级: 🔴
- 工作量: 12-15h
- 兼容性: ✅ 完全兼容
- 测试影响: 加 celery + worker 集成测试
```

### 方案对比表（让你看）

| 维度 | A 同步触发链 | B 事件总线 |
|---|---|---|
| 工作量 | 5-7h | 12-15h |
| 新增依赖 | 0 | Celery + flower + worker 监控 |
| API 响应延迟 | < 50ms（无 LLM）/ < 3s（含 LLM） | < 50ms（全部异步） |
| 失败处理 | try/except + log | 重试 + DLQ |
| Debug 难度 | 易（1-2 跳） | 中（4 跳） |
| 项目规模适配 | ✅ 适合小项目（5 service） | ⚠️ 适合中大型（20+ service） |

### 我的判断点（不替你选）

- 选 **A** 的信号：项目保持小而美 / V2 量级小（人均每天 5-20 次触发）/ 不想引入 Celery 复杂度
- 选 **B** 的信号：V3+ 还会引入更多 service 异步交互 / 你想给项目长期铺事件总线 / 团队有 Celery 经验
- **你的项目当前是 5 service + 1 人 + V2 量级**，A 适配度更高 — 但这是我的判断，**你的项目你定**

---

## 2. 风险评估（客观列表，不替你定接受度）

| # | 风险 | 等级 | 缓解（待你确认是否接受） |
|---|---|---|---|
| 1 | LLM 成本不可控 | 🔴 | Redis TTL 1h + 限流 60s 5 次 + 失败降级 |
| 2 | Obsidian vault 不存在 | 🟡 | log warning 不抛异常 + 前端 UI 提示 |
| 3 | 3 service 循环依赖 | 🟡 | triggered_by 方向约束 + code review |
| 4 | Profile 字段并发覆盖 | 🟡 | 乐观锁 (updated_at 比对) + 重试 1 次 |
| 5 | interview.py 803 行影响判断 | 🟡 | 拆 1-2 个函数到 interview_settlement.py |
| 6 | 估时偏差 > 50% | 🟡 | 拆 3 PR，每阶段 2-3h 可中断 |
| 7 | settlement 失败阻塞主业务 | 🟡 | try/except 兜底不阻塞 |
| 8 | 新建 /profile 页范围扩大 | 🟡 | 等决策 6 |
| 9 | LLM prompt 注入 | 🟡 | strip markdown + 截断 1000 字 + sandbox |
| 10 | PR 顺序耦合 | 🟢 | V2.3 端点先 ready 空数据 |
| 11 | 未提交改动 / 多 agent 冲突 | 🟢 | commit 前 rebase |

**风险等级合计**：🔴 1 / 🟡 8 / 🟢 2

### 等你接受的风险策略

- 风险 1（🔴 LLM 成本）：是否接受"Redis 缓存 + 限流 + 降级"3 重缓解？
- 风险 2-9（🟡）：是否接受我的缓解方案？还是某条你想换策略？

---

## 3. 决策点 · 已拍板（**全 A**）

### 决策 1（architecture） ✅ 已拍 A
- 选定：**方案 A 同步触发链**（理由见 §1 判断点）
- 替代 B 已锁：V3+ 引入事件总线时再考虑

### 决策 2（cache strategy） ✅ 已拍 A
- 选定：**Redis TTL 1h**（key: `summary:dashboard:{user_id}` / `summary:profile:{user_id}` / `profile:{user_id}`）
- Redis 不可用时降级：直接调 LLM（缓存是优化非必需）

### 决策 3（trigger pattern） ✅ 已拍 A
- 选定：**service 内调 settlement**（与 V1 `upsert_from_interview` 模式一致）
- 触发点：`learning_progress_service.upsert_progress` 末尾 + `interview_service.complete` 末尾

### 决策 4（decomposition） ✅ 已拍 A
- 选定：**顺手拆 interview.py 803 行**
- 拆出 `backend/services/interview_settlement.py`（3 触发函数）

### 决策 5（PR 节奏） ✅ 已拍 A
- 选定：**分 3 PR**（V2.1 / V2.2 / V2.3）
- V2.1 = ProfileSettlementService + 触发；V2.2 = ObsidianSedimentService + 触发；V2.3 = SummaryService + 6 端点 + 前端 3 改造

### 决策 6（/profile page） ✅ 已拍 A
- 选定：**新建 `/profile` 页**
- V2.4 工作量 +1h（implement ProfilePage + 嵌入 nav "画像" 入口）

### 决策 7（error handling） ✅ 已拍 A
- 选定：**不抛异常 + log warning**
- 实现：所有 settlement / obsidian write 包 try/except，失败 log + return None，主业务不感知

---

## 1.5 推荐方案（必填，对齐 check-step.py）

**推荐方案**: **方案 A（同步触发链）**

理由摘要（详见 §1 + §3 决策 1）：
- 与 V1 `upsert_from_interview` 模式一致（最小学习成本）
- V1 没 Celery 基础设施，0 新增依赖
- 5-7h 完工 vs 12-15h（B 事件总线）
- V2 量级小（人均每天 5-20 次触发），同步阻塞可接受

---

## 4. 任务拆分建议（已锁定 — 决策 5/6 已定）

### 锁定配置：拆 3 PR（V2.1 / V2.2 / V2.3）+ 新建 /profile 页

| 子任务 | 内容 | 工时 | PR | 备注 |
|---|---|---|---|---|
| **V2.1** | ProfileSettlementService + 触发点（学习复习 + 面试）+ 拆 `interview_settlement.py` | 2-3h | PR 1 | 决策 3 + 4 实现；含乐观锁 |
| **V2.2** | ObsidianSedimentService + 触发（写 daily + interview log） | 1-2h | PR 2 | 决策 7 实现：失败 log 不抛 |
| **V2.3** | SummaryService + 6 端点 + 前端 3 改造（含新建 `/profile`） | 2-3h | PR 3 | 决策 2 实现：Redis TTL 1h + 降级；决策 6 实现：ProfilePage + nav |
| **V2.4** | 验证 + verify.md（L3 整合 + L5 staging） | 1h | 验证 | — |
| **V2.5** | 复盘 + 更新 CLAUDE.md | 0.5h | 复盘 | — |

**总估时**：6-8.5h

**子任务粒度（V2.1 内部，示范）**：
- T1.1 建 service 骨架
- T1.2 settle_after_practice
- T1.3 settle_after_interview
- T1.4 weekly_full_refresh
- T1.5 manual_refresh
- T1.6 改 learning_progress_service 触发
- T1.7 改 interview.py 触发 + 拆 interview_settlement.py
- T1.8 写测试 ≥ 80% 覆盖

每个子任务 ≤ 1h AI 工作量，对应 ≥ 1 commit。

---

## 5. 路径建议（必填）

```
0 调研（research.md）✅
        ↓
1 规格（spec.md + product-doc.md + design-spec.md）✅
        ↓
2 计划（本文件 plan.md）✅ 7 决策 = 全 A
        ↓ (即将)
2.x api-spec.md（6 端点）+ component-spec.md（3 组件）— 生成中
        ↓
3 拆分（tasks.md）— 按已锁方案拆 25 个子任务
        ↓
4 实现（TDD）— V2.1 → V2.2 → V2.3，3 PR
        ↓
5 验证（verify.md）— L3 整合 + L5 staging
        ↓
6 复盘（retro.md）— 经验沉淀
```

---

## 🎯 硬性 DOD（plan.md 完成必须全过）

- [x] 方案 ≥ 2 个（实际 2：A 同步链 + B 事件总线）
- [x] 推荐方案明确（**推荐**: 方案 A — 同步触发链）
- [x] 风险点 ≥ 3 条带等级（实际 11 条：🔴 1 + 🟡 8 + 🟢 2）
- [x] 决策点 ≥ 1（实际 7 条，全部 ✅ approved）
- [x] 引用完整（research.md + product-doc.md + design-spec.md + spec.md）

> ✅ 工具校验：`python3 scripts/check-step.py plan <file>` 应通过

---

## 📚 相关文档

- [research.md](research.md) — 5 决策点 + 8 风险点来源（**注：调研的"推荐"只是原始数据，**不等于** plan 的"推荐"**）
- [product-doc.md](product-doc.md) — 1 步产品脑
- [design-spec.md](design-spec.md) — 1 步设计脑
- [spec.md](spec.md) — 1 步技术脑（已冻，是下游基准）
- _api-spec.md — 🔒 未生成
- _component-spec.md — 🔒 未生成
- `docs/DOD.md` §四 — 2 步计划 DOD 完整定义

---

## 6. 回复模板（给我一句话）

回我时挑一个：

- **"全采纳"** — 7 个决策按我的倾向走，我立刻生成 api-spec.md + component-spec.md
- **"X 改 B"** — 把某个决策改掉，告诉我新选项
- **"X 我自己定"** — 你重写某个决策的判断点 / 接受度
- **"我要打磨"** — 你直接在 plan.md 上 Edit / 改完告诉我"plan 冻结" → 我再生成下游
