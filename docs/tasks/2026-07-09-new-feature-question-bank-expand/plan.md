---
title: 方案文档 · V3 题库扩量 + 多维分类 + LeetCode 三件套 + AI 推送
date: 2026-07-09
status: v1
tags: [plan, 2步, 方案, v3, 题库扩量, 多维分类, LeetCode三件套, AI推送]
related:
  - [research.md](research.md) — 上游 0/0.5/0.6 调研（13 决策全锁定）
  - [spec.md](spec.md) — 上游 1 步技术脑
  - [product-doc.md](product-doc.md) — 上游 1 步产品脑
  - [design-spec.md](design-spec.md) — 上游 1 步设计脑
---

# 方案文档：V3 题库扩量 + 多维分类 + LeetCode 三件套 + AI 推送

> **作者**：AI 主导（写多方案对比 + 列判断点），**方案选择权交回你**
>
> **下游文档状态**：
> - ✅ spec.md 已冻结（1 步产物，技术契约 = 基准）
> - ✅ 决策已拍板（13/13 全 A，L 方案 C · Sidebar 架构）
> - 🚧 db-design.md / api-spec.md / component-spec.md（本文件后续产物）
>
> **当前状态**：✅ **PLAN 冻结**（13 决策 + L 方案 C），下游文档生成中

---

## 0. ⚠️ 决策总览（顶层摘要）

| # | 决策 | 选项 | 状态 |
|---|---|---|---|
| **A** | schema 策略 | A1 扩 topic/sub_topic + QuestionTag 系统标签 | ✅ 已拍 |
| **B** | followup 复杂度 | B2 保留 V1 详细 2-4 追问/题 | ✅ 已拍 |
| **C** | 前端 UI 同步 | C1 /learn + /review TagFilter | ✅ 已拍 |
| **D** | PR 拆分 | D2 4 PR 按方向拆（+V3.0 学习计划 = 5 PR） | ✅ 已拍 |
| **G** | V3+ 是否并入 | G3 V3 + LeetCode 三件套 | ✅ 已拍 |
| **H** | V3.5 优先 | ⏸ 跳过 | — |
| **I** | LeetCode 三件套顺序 | I1 学习计划先 → 精选题单 + 每日一题嵌入 | ✅ 已拍 |
| **J** | AI 推送 V3 子范围 | A 极简（dashboard 推荐卡） | ✅ 已拍 |
| **K** | 学习复习模块定位 | 保留 1 模块 + 2 子页 | ✅ 已拍 |
| **L** | 整体架构 | **方案 C · 侧边栏 Sidebar 多级菜单** | ✅ 已拍 |
| **M** | Sidebar 5 大分组 | V1 4 大模块 + V3 AI 推送 | ✅ 已拍 |
| **N** | 14 page 路由映射 | dashboard / interview / learn / knowledge / ai / me | ✅ 已拍 |
| **E** | V3+ V3.5 优先 gap | (V3 已推) | ⏸ 跳过 |
| **F** | V3.5 第一批 gap | (V3 已推) | ⏸ 跳过 |

**合计 13 个决策全锁定**（A-N，含 J/K 用户拍板 · L 方案 C · M/N Sidebar 子决策）。

---

## 1. 方案对比 · 已选定（推荐方案 = A1 + B2 + C1 + D2 + G3 + I1 + J A 极简 + L C）

> ✅ **已选定完整方案**：V3 = 5 PR（V3.0 学习计划 / V3.1 system_design + 精选题单 / V3.2 algorithms + 每日一题 / V3.3 network / V3.4 frontend） + 1 PR（V3.7 AI 推荐卡） + Sidebar 整体架构重构。本节保留对比供未来 V4+ 选 B 时参考。

### 方案 A1：schema 兼容（已选定）

```markdown
- 思路: 扩 Question.topic / sub_topic + 新增 QuestionTag 系统标签机制（is_system=True）
- 优点:
  - 复用 V1 既有 Question 字段（不破坏 schema 兼容）
  - 复用 V1 既有 QuestionTag 表（已实装 + UNIQUE 约束 + generated column）
  - 0 数据库迁移 ALTER
- 缺点:
  - 多维分类需要预填 ~50 条系统标签（seed 阶段一次性工作）
  - A 维度（方向）和 B 维度（栈）仍用 topic/sub_topic 字符串，不够灵活
- 风险等级: 🟢
- 兼容性: ✅ 完全兼容
- 工作量: 中（系统标签预填 ~1h）
- 估时: 14-20h（5 PR）
```

### 方案 A2：全 QuestionTag 多对多（备选 · 未选）

```markdown
- 思路: Question 表只保留基础字段，topic/sub_topic 改用 QuestionTag 多对多
- 优点: 灵活度最高 · 一道题可任意多 tag
- 缺点:
  - 现有 50 道题全要重新打 tag（迁移工作量大）
  - 现有 SQL 查询 `WHERE topic = ?` 性能慢（需多 JOIN）
  - V2 Profile 已有 `weak_topics` 字符串字段，改 schema 影响面大
- 风险等级: 🔴
- 兼容性: ❌ 破坏 schema
- 工作量: 大
- 估时: 25-30h
```

### 方案对比表

| 维度 | A1（已选） | A2（备选） |
|---|---|---|
| schema 兼容 | ✅ 完全 | ❌ 破坏 |
| 现有 50 题迁移 | ❌ 不需要 | ✅ 全量 |
| 多维度筛选 | 🟡 topic + 系统 tag | ✅ 全 tag |
| 查询性能 | ✅ topic 直接索引 | 🟡 多 JOIN |
| 工作量 | 中 | 大 |
| 估时 | 14-20h | 25-30h |
| 风险 | 🟢 | 🔴 |

**我的判断点**：
- 选 A1 的信号：项目保持小而美 / 不想破坏 V1 数据 / 快速上线
- 选 A2 的信号：未来 V4+ 想全维度多标签 / 愿意做一次性数据迁移

### 我的判断点（不替你选）

- 选 **A1** 的信号：项目保持小而美 / V3 量级适中 / 不想破坏 V1 数据
- 选 **A2** 的信号：V4+ 会大规模重构题库 / 愿意一次性数据迁移
- **当前 V3 用户已拍 A1**（schema 兼容优先），但这是 AI 推荐。

---

## 2. 风险评估（客观列表，不替你定接受度）

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | 200 题写作工作量大 + B2 追问详细 | 🔴 | 拆 5 PR（每方向 25 题）· 模板化追问 |
| 2 | seed_data 冻结区已解除但写入不可逆 | 🟡 | 用 git 跟踪每次 seed 变更，rollback 容易 |
| 3 | QuestionTag 系统标签与现有用户标签 name 冲突 | 🟡 | seed_service 启动检查 + `sys_` 前缀 |
| 4 | 新 200 题 ID 与旧 50 题 ID 重复 | 🟡 | ID 命名规范：`{topic_short}{3位序号}`，如 `sys_001` / `algo_005` |
| 5 | 前端多标签筛选 UI 性能 | 🟡 | 服务端预聚合索引（`idx_qtm_tag_question` 已建）+ 前端防抖 300ms |
| 6 | seed_service 改动影响现有 50 题导入 | 🟢 | 现有 50 题 ID 保留，QuestionTag 只给新题预填 |
| 7 | 多维标签语义模糊（A/B/C 边界） | 🟡 | spec.md 定义明确 tag 命名空间 + 示例 5 个 |
| 8 | V2 沉淀层 trigger 依赖题目结构 | 🟢 | V3 不动 Question 字段即无冲突 |
| 9 | Sidebar 整体架构改动（V3.6）风险 | 🟡 | 14 page 拆 11 占位 + 4 完整，渐进实施 |
| 10 | 估时偏差 > 50% | 🟡 | 拆 5 PR + 1 V3.7，每 PR 可独立验证 |
| 11 | AI 推送 V3.7 极简方案不足 | 🟢 | V3 推 dashboard 推荐卡够用，/push 完整页留 V4+ |
| 12 | 5 个新表 schema 错误 | 🟡 | V1 既有 _MIGRATIONS 模式启动 ALTER 易回滚 |

**风险等级合计**：🔴 1 / 🟡 7 / 🟢 4

### 等你接受的风险策略

- 风险 1（🔴 200 题写作）：是否接受"拆 5 PR · 每方向 25 题 · 模板化追问"？
- 风险 9（🟡 Sidebar 改动）：是否接受"11 占位 + 4 完整渐进实施"？

---

## 3. 决策点（已拍板 · 见 §0 决策总览）

### 决策 A（schema 策略） ✅ 已拍 A1
- 选定：**方案 A1 扩 topic/sub_topic + QuestionTag 系统标签**（理由：复用 V1 schema，零迁移）
- 备选 A2 已锁：V4+ 想要全 tag 多对多时再考虑

### 决策 B（followup 复杂度） ✅ 已拍 B2
- 选定：**B2 保留 V1 详细 2-4 追问/题**
- 缺点：估时翻倍（4-6h → 8-12h）

### 决策 C（前端 UI 同步） ✅ 已拍 C1
- 选定：**C1 /learn + /review 都加 TagFilter**（用户感知最强）

### 决策 D（PR 拆分） ✅ 已拍 D2
- 选定：**D2 4 PR 按方向拆**（+V3.0 学习计划 = 5 PR）+ V3.7（AI 推送） = 6 PR
- 备选 D1/D3 已锁：未来想换粒度再考虑

### 决策 G（V3+ 是否并入 V3） ✅ 已拍 G3
- 选定：**G3 V3 + LeetCode 三件套**（学习计划 + 精选题单 + 每日一题）
- 估时 +7-12h

### 决策 H（V3.5 优先 gap） ⏸ 跳过
- G3 已包含 V3.5 内容，H 不再需要

### 决策 I（LeetCode 三件套顺序） ✅ 已拍 I1
- 选定：**I1 学习计划先（用户痛点）→ 精选题单 + 每日一题嵌入 V3.1/V3.2**
- 备选 I2/I3 已锁

### 决策 J（AI 推送 V3 子范围） ✅ 已拍 A 极简
- 选定：**A 极简 · dashboard 推荐卡**（不建独立页，2-3h）
- 备选 B/C/D 已锁：V3.5+ 升级

### 决策 K（学习复习模块定位） ✅ 已拍保留
- 选定：**保留 1 个"学习复习"模块 + 2 子页**（学 + 复习）
- 备选 拆分/合并已锁

### 决策 L（整体架构） ✅ 已拍 方案 C
- 选定：**Sidebar 5 大分组多级菜单**（14 page）
- 备选 A 顶 Tab / B Dashboard 内 Tab 已锁

### 决策 M（Sidebar 5 大分组依据） ✅ 已定
- 选定：V1 4 大模块 + V3 新增 AI 推送
- 分组：概览 / 面试 / 学习复习 / 知识库 / AI 推送 / 我的

### 决策 N（14 page 路由映射） ✅ 已定
- 详见 [design-spec.md §2.5](../2026-07-09-new-feature-question-bank-expand/design-spec.md#25-v1--v36-路由映射已实施--待实施)

---

## 4. 任务拆分建议（已锁定 — 决策 D + G + J + L 综合）

| 子任务 | 内容 | 工时 | PR | 备注 |
|---|---|---|---|---|
| **V3.0** | 学习计划补全（前端 UI） | 2-4h | PR 1 | 决策 G + I1 优先；后端 0 改动 |
| **V3.1** | system_design 25 题 + 精选题单 Collections | 5-7h | PR 2 | 新建 system_design.json + 25 题 + ~75 追问 + 3 张新表 + /api/learn/collections 4 端点 + /collections 页 + 题单详情页 |
| **V3.2** | algorithms 25 题 + 每日一题 Daily Challenge | 5-7h | PR 3 | 新建 algorithms.json + 25 题 + ~75 追问 + 2 张新表 + /api/learn/daily-challenge 2 端点 + DailyChallengeCard 嵌入 dashboard |
| **V3.3** | network 20 题 | 3-4h | PR 4 | 新建 network.json + 20 题 + ~60 追问 |
| **V3.4** | frontend 20 题 | 3-4h | PR 5 | 新建 frontend.json + 20 题 + ~60 追问 |
| **V3.x** | A+B+C 多维标签系统（跨 V3.1-V3.4） | 1h | (并入 V3.1) | seed_service 预填 50 个系统标签 + 600 条 QuestionTagMap 关联 |
| **V3.x** | /learn + /review TagFilter UI | 2-3h | (并入 V3.4) | 多选标签筛选 + 实时筛选 |
| **V3.5**（🆕 J 决策） | dashboard 加 AI 推荐卡 | 2-3h | PR 6 | 调 V1 `/api/analytics/recommendations` 已实装 endpoint |
| **V3.6**（🆕 L 决策） | 整体架构改为 Sidebar | 2-3h | PR 7 | 5 大分组 14 page + 折叠 + 搜索 |
| **V3.7** | 验证（V2 L4 改进 #3 模式） | 1.5h | verifier | L1-L5 全层 gate |
| **V3.8** | 复盘 + 更新 CLAUDE.md / memory | 0.5h | retro | 经验沉淀 |

**总估时**：18-26h（5 → 6 → 7 PR）

每个子任务 ≤ 4h AI 工作量，对应 ≥ 1 commit（CLAUDE.md § 三 DOD）。

---

## 5. 路径建议（必填 · 7 步流程 + V3 子流程）

```
0 调研（research.md）✅
        ↓
1 规格（spec.md / product-doc.md / design-spec.md）✅
        ↓ (V3.6 Sidebar 架构已纳入 design-spec §2/§3.6)
2 计划（本文件 plan.md）✅
        ↓ (即将)
2.x db-design.md（5 张新表 schema）         — 0.5h
2.x api-spec.md（6 个新端点契约）           — 0.5h
2.x component-spec.md（3 组件 props 规范）  — 0.5h
        ↓
3 拆分（tasks.md · 30-40 原子任务）         — 1h
        ↓
4 实现（TDD · 7 PR · V3.0-V3.6 渐进）       — 16-22h
        ↓
5 验证（verify.md · L1-L5 全层 gate）        — 1.5h
        ↓
6 复盘（retro.md + 更新 CLAUDE.md / memory）  — 1h
```

---

## 6. AI vs 人分工

| AI 适合做 | 人适合做 |
|---|---|
| ✅ 填 §2 数据契约（schema 是结构化） | ✅ 验收 §3 GWT（业务判断） |
| ✅ 列 §4 边界（8 类 checklist） | ✅ 签字"已验收"（决策） |
| ✅ 列 §5 测试场景（从 GWT 提炼） | ✅ 决定 §1 用户故事优先级 |
| ✅ 检查 5 段齐全（check-step.py 自动） | ✅ 拍板 product-doc 成功指标 |

**核心原则**：**人填空白（业务决策），AI 校验完整性（缺什么提醒）**。

---

## 7. 🎯 硬性 DOD（plan.md 完成必须全过）

- [x] 方案 ≥ 2 个（实际 2：A1 兼容 + A2 全 tag）
- [x] 推荐方案明确（**A1 + B2 + C1 + D2 + G3 + I1 + J A 极简 + L C**）
- [x] 风险点 ≥ 3 条带等级（实际 12 条：🔴 1 / 🟡 7 / 🟢 4）
- [x] 决策点 ≥ 1（实际 13 条全部 ✅ 拍板）
- [x] 引用完整（research.md v4 + spec.md + product-doc.md + design-spec.md）

> ✅ 工具校验：`python3 scripts/check-step.py plan <file>` 应通过

---

## 8. 📚 相关文档

- [research.md](research.md) — 0/0.5/0.6 调研（13 决策 · 含 L/M/N V3.6 Sidebar）
- [spec.md](spec.md) — 1 步技术脑（5 US + 14 GWT）
- [product-doc.md](product-doc.md) — 1 步产品脑（5 指标）
- [design-spec.md](design-spec.md) — 1 步设计脑（§2 V3.6 Sidebar + §3.6 Sidebar 规范）
- [V1 母模块 plan](../2026-06-22-new-feature-question-bank/plan.md) — 4 大模块独立决策
- [V2 沉淀层 plan](../2026-06-28-new-feature-v2-smart-sediment/plan.md) — 7A 兜底贯穿