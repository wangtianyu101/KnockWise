---
title: 任务拆分 · V3 题库扩量 + 多维分类 + LeetCode 三件套 + AI 推送 + Sidebar
date: 2026-07-09
status: v1
tags: [tasks, 3步, 实施, v3, 题库扩量, 多维分类, LeetCode三件套, AI推送, Sidebar]
related:
  - [plan.md](plan.md) — 上游 2 步方案
  - [spec.md](spec.md) — 上游 1 步技术契约（14 GWT）
  - [api-spec.md](api-spec.md) — 上游 2 步 API（8 新端点 + 6 复用）
  - [db-design.md](db-design.md) — 上游 2 步数据库（5 新表）
  - [component-spec.md](component-spec.md) — 上游 2 步组件（3 新组件 + 6 复用）
  - [design-spec.md](design-spec.md) — 上游 1 步设计脑
---

# 任务拆分：V3 题库扩量 + 多维分类 + LeetCode 三件套 + AI 推送 + Sidebar

> **一句话**：把 plan.md 拆成 **34 个原子任务**（V3.0 = 4 / V3.1 = 7 / V3.2 = 7 / V3.3 = 3 / V3.4 = 3 / V3.5 = 4 / V3.6 = 6），每个 ≤ 1h AI 工作量 = 1 commit = ≥ 1 测试。
>
> **作者**：AI 主导（实施指南），待你 review 任务粒度
>
> **下游**：4 步实现按 T1 → T34 顺序推进，PR 1-7 边界 = V3.0-V3.6

---

## 0. 任务进度自动更新规则（2026-07-10 用户加规则 · CLAUDE.md § 6.5）

> **规则**：每次执行完任务标 completed 时，**AI 自动同步本文档**：
> 1. **PR 标题**：`(暂缓)` → `(✅ 已做)` 同步
> 2. **PR 状态行**：`本 PR 可延后` → `✅ 已实施（N/N 测试通过）` 同步
> 3. **该 PR "标志"行**：后做/暂缓 描述 → ✅ 已做
> 4. **任务标记**：`- [ ] T<n>:` → `- [x] T<n>: ✅ DONE — ...`
> 5. **CLAUDE.md § 八 / § 十 总览**：同步状态（✅ 已做 / ⏸ 暂缓）
>
> **效果**：用户从 tasks.md 一眼看出真实进度，避免"AI 做了事但文档没更新"。

---

## 1. 任务粒度原则（已锁定）

```
✅ 每个任务 ≤ 1h AI 工作量
✅ 每个任务 1 个 commit
✅ 每个任务对应 ≥ 1 测试用例
✅ 任务间依赖关系明确（拓扑序，无环）
✅ 并行任务标"可并行"
```

---

## 2. 任务清单（34 个，按 PR 分组）

### PR 1 — V3.0 学习计划补全（任务 T1-T4 · 2-3h）

> **目标**：前端 /plan 页面 + Nav 入口 + Dashboard 进度卡。**后端 0 改动**（V1 5 端点已实装）。

#### T1: 建 `/plan` 页面骨架 + 4 子卡组件

```markdown
- [ ] T1: 建 /pages/plan/index.tsx 骨架 + 4 子卡组件
  - 文件: frontend/pages/plan/index.tsx (新建 350 行) + frontend/components/v3/PlanCard/ 4 个
  - 测试: T1.1 PlanCard.test.tsx 渲染 4 子卡（当前计划 / 创建按钮 / 历史 / 详情）
  - 依赖: —
  - 估时: 45 min
  - 产出: 1 commit
```

**实施要点**：
- 4 子卡：当前活跃计划 / 历史计划列表 / 创建按钮 / 计划详情
- 复用 V1 `<PlanCard>` 组件（如果有）+ GlassCard 共享
- 当前计划卡含 mastery radar 5 维

#### T2: Nav.tsx 加"计划"入口 + 路由跳转

```markdown
- [ ] T2: Nav.tsx 加"计划"入口（位于"复习"和"画像"之间）
  - 文件: frontend/components/Nav.tsx (改)
  - 测试: T2.1 Nav.test.tsx 渲染计划 tab + 点击跳转
  - 依赖: T1
  - 估时: 20 min
  - 产出: 1 commit
```

**实施要点**：
- 位置：复习 → 计划 → 画像（紧邻学习复习模块）
- 颜色：emerald-400（与其他 V3 模块一致）

#### T3: Dashboard.tsx 加"当前计划进度"卡

```markdown
- [ ] T3: dashboard.tsx 加"当前计划进度"卡（接 GET /api/learn/plans/{id}/progress）
  - 文件: frontend/pages/dashboard.tsx (改)
  - 测试: T3.1 Dashboard 渲染当前计划卡 + 进度条 0/10 / 5/10
  - 依赖: T1
  - 估时: 30 min
  - 产出: 1 commit
```

**实施要点**：
- 进度条 + 完成度百分比 + "查看详情"按钮
- 弱项剩余标签（emerald 高亮）
- 无计划时显示 Empty 状态

#### T4: 创建计划 Modal（复用 V1 5 端点）

```markdown
- [ ] T4: 创建计划 Modal 组件（表单 + 日期范围 + 周目标 JSON）
  - 文件: frontend/components/v3/PlanCreateModal/（新建）+ 集成到 /plan
  - 测试: T4.1 Modal 提交创建 + 422 错误处理 + 409 同名冲突
  - 依赖: T1
  - 估时: 45 min
  - 产出: 1 commit
```

**实施要点**：
- 字段：name / start_date / end_date / goal / weekly_target JSON
- 422 错误展示（V2 L4 错误格式）
- 409 同名冲突 toast 提示

**PR 1 标志**：✅ /plan 完整闭环（创建 / 查看 / 进度 / 历史 / 详情）+ Nav 入口 + Dashboard 卡

---

### PR 2 — V3.1 Agent 题单框架 + Collections（任务 T5-T11 · 4-5h · 数据解耦）

> **目标**：3 张新表 + 4 API 端点 + 1 个 agent 题单（占位）+ /collections 页面 + CollectionCard 组件。
> **数据解耦**（用户 2026-07-10 决定）：题单先建好结构，**题目后续手动加 / 定时任务拉**（不在 V3 范围）。

#### T5: ~~建 `system_design.json` + 25 题~~ ❌ 已删除（用户 2026-07-10 改 V3 方向为 agent）

#### T5': 建 Agent 题单"壳"框架（占位 · 0 题目）

```markdown
- [x] T5': ✅ DONE — collection_service.py SYSTEM_COLLECTIONS 改为 1 个 agent_foundation 题单（占位）
  - 文件: backend/services/collection_service.py (改)
  - 测试: T5'.1 seed 1 题单存在 + question_count=0
  - 依赖: —
  - 估时: 已完成
  - 产出: 1 commit
```

**实施要点**：
- 删除 seed_data/system_design.json（用户改方向）
- SYSTEM_COLLECTIONS 现在只 1 题单 agent_foundation（占位，0 题目）
- 题目**后续手动加 / 定时任务拉**（不在 V3 范围）

#### T6: ~~seed_service 加 system_design.json~~ ❌ 已撤销（与 T5' 合并）

#### T7: 建 question_collections / maps / subscribes 3 张新表（_MIGRATIONS）

```markdown
- [ ] T7: backend/core/database.py:_MIGRATIONS 加 3 张新表 SQL
  - 文件: backend/core/database.py (改)
  - 测试: T7.1 pytest conftest 启动时 3 表自动创建
  - 依赖: —
  - 估时: 30 min
  - 产出: 1 commit
```

**实施要点**：
- IF NOT EXISTS 幂等
- 外键 ON DELETE CASCADE
- UNIQUE 约束 (user_id, collection_id)

#### T8: 写 CollectionService + 4 方法（list / get / subscribe / unsubscribe）

```markdown
- [ ] T8: backend/services/collection_service.py（新建 5 方法）
  - 文件: backend/services/collection_service.py (新建 180 行)
  - 测试: T8.1 list_collections + T8.2 get_collection + T8.3 subscribe + T8.4 unsubscribe
  - 依赖: T7
  - 估时: 60 min
  - 产出: 1 commit
```

**实施要点**：
- list_collections：JOIN collection_subscribes 算 subscribed + progress
- get_collection：JOIN question_collection_maps 算 position
- subscribe：INSERT IGNORE（防 409）
- unsubscribe：DELETE WHERE

#### T9: 写 4 API 端点 + slowapi 限流（learn.py 加 collection 路由组）

```markdown
- [ ] T9: backend/api/learn.py 加 4 collection 端点
  - 文件: backend/api/learn.py (改 ~80 行)
  - 测试: T9.1 happy + 422 + 404 + 409 + 401 全覆盖
  - 依赖: T8
  - 估时: 60 min
  - 产出: 1 commit
```

**实施要点**：
- 4 端点：GET list / GET detail / POST subscribe / DELETE unsubscribe
- 慢速 API 限流 30次/60s/用户
- V2 L4 错误格式统一（`{error: {code, message}}`）

#### T10: ~~预填精选题单 seed（5 个官方题单 + 题目关联）~~ → 改 1 题单占位

```markdown
- [x] T10: ✅ DONE — main.py 启动调用 seed_collections_system()（1 个 agent 题单占位）
  - 文件: backend/main.py (改)
  - 测试: T10.1 启动后 agent_foundation 题单存在 + question_count=0
  - 依赖: T8
  - 估时: 已完成
  - 产出: 1 commit
```

**实施要点**：
- 5 题单 → 1 题单（agent_foundation）
- 题目**后续手动添加**（不在 V3 范围）或通过**定时任务**从外部拉取
- 关联 0 题目（seed_collections_system 关联 V1 agent_core.json 但题目数量由 seed_questions 决定）

#### T11: 前端 `/collections` 列表页 + CollectionCard 组件

```markdown
- [ ] T11: 建 /pages/collections/index.tsx + CollectionCard 组件
  - 文件: frontend/pages/collections/index.tsx + frontend/components/v3/CollectionCard/ (~250 行)
  - 测试: T11.1 列表渲染 5 题单 + 订阅/取消订阅按钮 + 进度环
  - 依赖: T9, T10
  - 估时: 60 min
  - 产出: 1 commit
```

**实施要点**：
- 复用 design-spec §3.2 视觉规范（玻璃拟态 + 环形进度 + 5 题单不同渐变色）
- 5 状态：未订阅/已订阅 × 0 进度/有进度/加载中
- 409 错误 toast

**PR 2 标志**：✅ Agent 题单框架 + 3 表 + 4 API + /collections 完整（1 占位题单，题目后续填）

---

### PR 3 — V3.2 Agent 题目入库（25 题 · 任务 T12-T18 · 6-7h · 后做）

> **目标**：25 道 agent 方向题目（如 agent_evaluations / agent_memory / multi_agent / tool_use），用户后续手动填。
> **状态**：本 PR 可延后到用户决定入库时机。

#### T12: 建 `algorithms.json` + 25 题（B2 详细 · ~75 追问）

```markdown
- [ ] T12: 建 seed_data/algorithms.json + 25 题
  - 文件: backend/seed_data/algorithms.json (新建 750 行)
  - 测试: T12.1 seed_service 导入后 algorithms 表 50 题 (25 旧 + 25 新)
  - 依赖: T6 (seed_service 已支持)
  - 估时: 60 min
  - 产出: 1 commit
```

**实施要点**：
- ID 命名：algo_001 ~ algo_025
- 字段：topic=algorithms / sub_topic / difficulty=2-4 / round / question_text + followup_tree
- topic 分布：数组 5 / 链表 4 / 树 4 / 动态规划 5 / 图 4 / 哈希 3

#### T13: seed_service 加 algorithms.json + T11 时关联 algorithms 题单

```markdown
- [ ] T13: seed_service.py SEED_FILES 列表加 algorithms.json + 关联题单
  - 文件: backend/services/seed_service.py (改)
  - 测试: T13.1 seed_questions 导入 algorithms + algorithms_50 题单关联 25 题
  - 依赖: T12
  - 估时: 30 min
  - 产出: 1 commit
```

#### T14: 建 daily_challenges / daily_challenge_completions 2 张新表

```markdown
- [ ] T14: backend/core/database.py:_MIGRATIONS 加 2 张新表 SQL
  - 文件: backend/core/database.py (改)
  - 测试: T14.1 pytest conftest 启动时 2 表自动创建
  - 依赖: —
  - 估时: 20 min
  - 产出: 1 commit
```

#### T15: 写 DailyChallengeService + 2 方法（get / complete）+ 选题策略

```markdown
- [ ] T15: backend/services/daily_challenge_service.py（新建 3 方法）
  - 文件: backend/services/daily_challenge_service.py (新建 100 行)
  - 测试: T15.1 get_today + T15.2 complete_today + T15.3 选题策略
  - 依赖: T14
  - 估时: 45 min
  - 产出: 1 commit
```

**实施要点**：
- get_today_challenge：按 date 查 daily_challenges → 无则 seed 选题（hash % 200）
- complete_today_challenge：INSERT IGNORE + 触发 V2 ProfileSettlement
- streak 计算：连续 N 天有 completed_at

#### T16: 写 2 API 端点 + streak 计算

```markdown
- [ ] T16: backend/api/learn.py 加 2 daily-challenge 端点
  - 文件: backend/api/learn.py (改 ~40 行)
  - 测试: T16.1 get_today + T16.2 complete + 409 重复 + 422 score 错
  - 依赖: T15
  - 估时: 30 min
  - 产出: 1 commit
```

#### T17: 前端 DailyChallengeCard 组件（嵌入 dashboard 顶部）

```markdown
- [ ] T17: 建 frontend/components/v3/DailyChallengeCard/ + 嵌入 dashboard
  - 文件: frontend/components/v3/DailyChallengeCard/ (~200 行) + dashboard.tsx (改)
  - 测试: T17.1 6 状态全覆盖（加载/未完成/已完成/跨日/无题/错误）
  - 依赖: T16
  - 估时: 60 min
  - 产出: 1 commit
```

**实施要点**：
- 6 状态：加载中 / 未完成 / 已完成 / 跨日 / 0 题隐藏 / API 错误隐藏
- 7 天热力图 + streak 徽章
- 完成触发 V2 ProfileSettlement

#### T18: algorithms_50 题单 25 题关联 + 选题策略 seed

```markdown
- [ ] T18: seed_service algorithms_50 题单关联 + daily challenge 选题策略
  - 文件: backend/services/collection_service.py + daily_challenge_service.py (改)
  - 测试: T18.1 algorithms_50 关联 algo_001~algo_025 + daily 选题覆盖 200 题
  - 依赖: T13, T15
  - 估时: 30 min
  - 产出: 1 commit
```

**PR 3 标志**：✅ algorithms 25 题 + 2 表 + 2 API + DailyChallengeCard + dashboard 嵌入

---

### PR 4 — V3.3 题库质量监控（meta · 用户 2026-07-10 拍 · ✅ 已做）

> **重定义**：PR 4 不做题目入库（与"先不加题"原则一致），改为 **题库质量监控基础设施**。
> **目标**：题库同步历史 / 字段缺失统计 / 重复题检测 / 错误告警。

#### T19: 写 QuestionQualityService（4 方法）

```markdown
- [ ] T19: backend/services/question_quality_service.py（新建 ~200 行）
  - check_field_completeness() · 统计 answer_key_points / followup_tree 缺失率
  - detect_duplicates() · 按 question_text 哈希找重复
  - record_sync_history() · 每次 sync 落库一条记录
  - get_sync_history() · 拉最近 N 条同步历史
  - 估时: 30 min
```

#### T20: 加 sync_history 表 + 错误告警

```markdown
- [ ] T20: backend/core/database.py:_MIGRATIONS 加 sync_history 表 + 告警 endpoint
  - 表字段: id / source / fetched / created / skipped / errors / started_at / finished_at
  - endpoint: GET /api/admin/sync-history?limit=10（admin 端点）
  - 错误告警: sync_questions 失败 N 次连续 → log error（V1 模式 · 不接告警平台）
  - 估时: 20 min
```

#### T21: 写 5 测试点

```markdown
- [ ] T21: tests/test_question_quality_service.py（5 测试点）
  - T21.1 字段缺失统计（无 answer_key_points → 计数 +1）
  - T21.2 重复题检测（2 题同 text → 标记）
  - T21.3 sync_history 写入 + 读取
  - T21.4 错误告警（连续 3 次失败 → 触发）
  - T21.5 端到端 sync + 落库
  - 估时: 25 min
```

**PR 4 标志**：✅ 同步历史可视化 + 字段缺失告警 + 重复题检测（题库质量 meta 工具）

---

### PR 5 — V3.4 题库后台管理（admin API · 用户 2026-07-10 拍 · ✅ 已做）

> **重定义**：PR 5 不做 RAG 题库，改为 **admin 后台管理题库标签/难度/round**。
> **目标**：admin 可手动调整题的 tag / difficulty / round · 前端后台 UI。

#### T22: 加 QuestionTag 绑定 API（PATCH /api/admin/questions/{id}）

```markdown
- [ ] T22: backend/api/admin.py 加 PATCH /api/admin/questions/{id}
  - Pydantic: { topic?, sub_topic?, difficulty?, round? }（部分更新）
  - 鉴权: get_current_user（V1 无 admin 角色）
  - 校验: difficulty 1-5, round ∈ {'round1', 'round2'}
  - 估时: 25 min
```

#### T23: 加 GET /api/admin/questions（列表 + 过滤）

```markdown
- [ ] T23: GET /api/admin/questions?topic=&difficulty=&skip=&limit=
  - 列表题库（admin 端点）
  - 过滤: topic / difficulty / 关键词（question_text contains）
  - 排序: id asc / created_at desc
  - 估时: 25 min
```

#### T24: 写 admin 后台 UI（mockup · /pages/admin/questions.tsx）

```markdown
- [ ] T24: frontend/pages/admin/questions.tsx + 表格组件
  - 题目列表表格（antd Table + 搜索/过滤/分页）
  - 行编辑：topic / difficulty / round（antd Select）
  - 保存调 PATCH /api/admin/questions/{id}
  - 估时: 60 min
```

#### T25: 写 6 测试点

```markdown
- [ ] T25: tests/test_admin_questions.py（6 测试点）
  - T25.1 PATCH topic → 更新成功
  - T25.2 PATCH difficulty=0 → 422 校验失败
  - T25.3 PATCH round='invalid' → 422
  - T25.4 GET 列表 + 过滤
  - T25.5 GET 关键词搜索
  - T25.6 PATCH 不存在 id → 404
  - 估时: 30 min
```

**PR 5 标志**：✅ admin 后台 UI 可手动管理题库（不依赖自动拉取）

---

### PR 6 — V3.5 dashboard AI 推荐卡（任务 T25-T28 · 2-3h）

> **目标**：调 V2 已实装的 `/api/analytics/recommendations` endpoint + dashboard 加推荐卡。**后端 0 改动**。

#### T25: 前端 `useAIRecommendations` hook（SWR）

```markdown
- [ ] T25: 建 frontend/hooks/useAIRecommendations.ts
  - 文件: frontend/hooks/useAIRecommendations.ts (新建 40 行)
  - 测试: T25.1 SWR 调 /api/analytics/recommendations + 错误隐藏
  - 依赖: —
  - 估时: 20 min
```

#### T26: AIRecommendationCard 组件（4 种类型配色）

```markdown
- [ ] T26: 建 AIRecommendationCard 组件（[补]/[练]/[读]/[盘] 4 种类型）
  - 文件: frontend/components/v3/AIRecommendationCard/ (~250 行)
  - 测试: T26.1 4 种类型渲染 + 点击埋点 + 0 数据降级
  - 依赖: T25
  - 估时: 60 min
```

**实施要点**：
- 复用 design-spec §3.5 视觉规范
- 4 类型配色：[补] 红色 / [练] 蓝色 / [读] 紫色 / [盘] 琥珀
- 失败时隐藏整张卡（决策 7A）

#### T27: 嵌入 dashboard 顶部 + 埋点

```markdown
- [ ] T27: dashboard.tsx 顶部嵌入 AIRecommendationCard + click_recommend 埋点
  - 文件: frontend/pages/dashboard.tsx (改)
  - 测试: T27.1 卡片渲染 + 4 类型点击 + 控制台埋点
  - 依赖: T26
  - 估时: 30 min
```

#### T28: 端到端测试 + 失败降级

```markdown
- [ ] T28: AI 推荐 e2e 测试 + 失败降级（V1 已有数据模拟 + 失败场景）
  - 文件: backend/tests/test_api_v2.py (改) + frontend/test 集成
  - 测试: T28.1 happy 4 类型 + 失败隐藏 + 无数据 Empty
  - 依赖: T27
  - 估时: 30 min
```

**PR 6 标志**：✅ dashboard AI 推荐卡 + 埋点 + 降级（V2 复用 · 后端 0 改动）

---

### PR 7 — V3.6 整体架构 Sidebar（任务 T29-T34 · 3-4h）

> **目标**：左侧 Sidebar 5 大分组 14 page + 折叠 + 搜索。**dashboard 内容不动**，只换导航结构。

#### T29: Sidebar 基础组件（玻璃拟态 + 折叠）

```markdown
- [ ] T29: 建 Sidebar 基础组件（240px 展开 / 64px 折叠）
  - 文件: frontend/components/v3/Sidebar/ (新建 ~300 行)
  - 测试: T29.1 展开/折叠 + localStorage 持久化
  - 依赖: —
  - 估时: 60 min
```

#### T30: 5 大分组 + 14 page 菜单项

```markdown
- [ ] T30: Sidebar 加 5 大分组 14 page 菜单项
  - 文件: frontend/components/v3/Sidebar/SidebarNav.tsx
  - 测试: T30.1 5 分组渲染 + 14 page 高亮
  - 依赖: T29
  - 估时: 45 min
```

#### T31: Sidebar 搜索 + active 状态

```markdown
- [ ] T31: Sidebar 搜索框 + active 状态 + 徽章
  - 文件: frontend/components/v3/Sidebar/SidebarSearch.tsx
  - 测试: T31.1 搜索过滤 + 当前 page 高亮 + V3 徽章显示
  - 依赖: T30
  - 估时: 45 min
```

#### T32: 顶 nav 极简化（logo + breadcrumb + 用户菜单）

```markdown
- [ ] T32: 顶 nav 极简化（删除 4 tab · logo + breadcrumb + 用户）
  - 文件: frontend/components/Nav.tsx (重写)
  - 测试: T32.1 breadcrumb 切换 + 用户菜单
  - 依赖: —
  - 估时: 30 min
```

#### T33: AppShell 集成 + 14 page 占位

```markdown
- [ ] T33: AppShell 集成 Sidebar + 14 page 路由 + 占位 page
  - 文件: frontend/app/layout.tsx + frontend/pages/14-placeholders/
  - 测试: T33.1 Sidebar 切换 14 page 路由
  - 依赖: T29, T32
  - 估时: 60 min
```

#### T34: Sidebar 响应式（< 1024px drawer 模式）

```markdown
- [ ] T34: Sidebar 响应式 < 1024px drawer + 汉堡按钮
  - 文件: frontend/components/v3/Sidebar/ + Nav.tsx
  - 测试: T34.1 768px 抽屉 + 1024px 展开
  - 依赖: T33
  - 估时: 30 min
```

**PR 7 标志**：✅ Sidebar 5 大分组 14 page + 折叠 + 搜索 + 响应式

---

## 3. 任务依赖图（DAG）

```
                    PR 1 (V3.0)                    PR 2 (V3.1)                PR 3 (V3.2)                PR 4 (V3.3)      PR 5 (V3.4)    PR 6 (V3.5)    PR 7 (V3.6)
T1 ─┬─→ T2                                         T5 ─┬─→ T6 ─┬─→ T7 ─┬─→ T8 ─┬─→ T9 ─┬─→ T10 ─┬─→ T11       T19─→T20─→T21  T22─→T23─→T24       T25─→T26─→T27  T29─┬─→T30
    ├─→ T3                                                │       │       │       │       │       │                                                                  ├─→T31
    └─→ T4                                                │       │       │       │       │       │                              T12─→T13─┬─→T14─→T15─→T16─→T17        ├─→T32
                                                             │       │       │       │       │       │                                       │       │              │   T28        ├─→T33
                                                             │       │       │       │       │       │                                       │       │              │              ├─→T34
                                                                                                                            T18 ─────────┘
```

**约束**：
- ✅ 无环（DAG）
- ✅ 拓扑序（T1 → T2-4 / T5 → T6 → T7 → T8 → T9-10 → T11 / T12 → T13 → T14 → T15 → T16 → T17-18）
- ✅ V3.0（PR 1）独立，不依赖其他 PR
- ✅ V3.6（PR 7）独立，dashboard 内容不动
- ✅ V3.1-V3.5 内部线性推进

**并行机会**：
- V3.0（PR 1）和 V3.1-V3.5（PR 2-6）可并行（不共享文件）
- V3.6（PR 7）和 V3.0-V3.5 可并行
- T29-T34（V3.6）内部线性推进
- T12 → T18 之后才能关联 algorithms_50 题单

---

## 4. 任务↔测试映射

| 任务 | 自动化测试 | 测试场景 |
|---|---|---|
| T1 | PlanCard.test.tsx 渲染 4 子卡 | GWT-4 happy |
| T2 | Nav.test.tsx 加计划 tab | 路由跳转 |
| T3 | Dashboard.test.tsx 计划卡 | GWT-5 完成度聚合 |
| T4 | PlanCreateModal.test.tsx | GWT-4 happy + 422 + 409 |
| T5 | test_seed_service.py 25 题 | seed 导入 |
| T6 | test_seed_service.py force=True | seed 重跑幂等 |
| T7 | conftest.py 自动建表 | 5 表自动创建 |
| T8 | test_collection_service.py | list / get / subscribe / unsubscribe |
| T9 | test_api_v2.py happy + 422 + 404 + 409 + 401 | 4 端点全覆盖 |
| T10 | test_seed_collections.py 5 题单 | seed 题单 + 关联 count |
| T11 | CollectionCard.test.tsx 5 状态 | GWT-6/7 |
| T12 | test_seed_service.py 50 algorithms | seed 累计 |
| T13 | test_seed_collections.py 关联 | algorithms_50 25 题 |
| T14 | conftest.py | 2 表自动创建 |
| T15 | test_daily_challenge_service.py | get + complete + 选题策略 |
| T16 | test_api_v2.py daily | 2 端点 + 409 + 422 |
| T17 | DailyChallengeCard.test.tsx 6 状态 | GWT-8/9 |
| T18 | test_e2e.py | 端到端 + streak |
| T19 | test_seed_service.py 20 network | seed 70 题 |
| T20 | test_seed_service.py force | 幂等 |
| T21 | test_collections.py bytedance_net_20 | 题单关联 |
| T22 | test_seed_service.py 20 frontend | seed 200 题 |
| T23 | test_seed_tags.py 50 标签 + 270 maps | 标签预填 |
| T24 | TagFilter.test.tsx 9 测试点 | GWT-1/2/3 |
| T25 | useAIRecommendations.test.ts | SWR + 错误隐藏 |
| T26 | AIRecommendationCard.test.tsx 4 类型 | 渲染 + 埋点 |
| T27 | dashboard.test.tsx 嵌入 | 卡片渲染 + 埋点 |
| T28 | e2e test happy + 降级 | 集成测试 |
| T29 | Sidebar.test.tsx 展开/折叠 | 持久化 |
| T30 | SidebarNav.test.tsx 5 组 14 page | 渲染 + 高亮 |
| T31 | SidebarSearch.test.tsx | 过滤 + active + 徽章 |
| T32 | Nav.test.tsx 极简化 | breadcrumb |
| T33 | AppShell.test.tsx 集成 | 14 page 路由 |
| T34 | Sidebar 响应式 | < 1024px drawer |

---

## 5. 任务↔Spec 映射

| 任务 | spec.md / GWT | test-cases.md TC |
|---|---|---|
| T1-T4 | GWT-4 / GWT-5 | TC-2.1 / TC-2.2 / TC-2.3 / TC-2.4 |
| T5-T11 | GWT-6 / GWT-7 | TC-3.1 / TC-3.2 / TC-3.3 / TC-3.4 |
| T12-T18 | GWT-8 / GWT-9 | TC-4.1 / TC-4.2 / TC-4.3 / TC-4.4 |
| T19-T21 | TC-1.1（200 题） | TC-1.1 |
| T22-T24 | GWT-1 / GWT-2 / GWT-3 | TC-1.1 / TC-1.2 / TC-1.3 |
| T25-T28 | GWT-12 / GWT-13 | TC-5.1（AI 推荐） |
| T29-T34 | （V3.6 整体架构 · 不在 spec GWT 中） | Sidebar 集成测试 |

---

## 6. 总估时

```
T1:  45 min
T2:  20 min
T3:  30 min
T4:  45 min
T5:  60 min
T6:  15 min
T7:  30 min
T8:  60 min
T9:  60 min
T10: 45 min
T11: 60 min
T12: 60 min
T13: 30 min
T14: 20 min
T15: 45 min
T16: 30 min
T17: 60 min
T18: 30 min
T19: 50 min
T20: 10 min
T21: 30 min
T22: 50 min
T23: 60 min
T24: 60 min
T25: 20 min
T26: 60 min
T27: 30 min
T28: 30 min
T29: 60 min
T30: 45 min
T31: 45 min
T32: 30 min
T33: 60 min
T34: 30 min
─────────────────────
总估时: 1295 min = 21.6h

按 PR 分组:
- PR 1 (V3.0, T1-T4):     140 min = 2h 20min
- PR 2 (V3.1, T5-T11):   320 min = 5h 20min
- PR 3 (V3.2, T12-T18):  275 min = 4h 35min
- PR 4 (V3.3, T19-T21):  90 min = 1h 30min
- PR 5 (V3.4, T22-T24):  170 min = 2h 50min
- PR 6 (V3.5, T25-T28):  140 min = 2h 20min
- PR 7 (V3.6, T29-T34):  270 min = 4h 30min
─────────────────────
总: 1405 min = 23.4h
```

> 偏差说明：plan.md 估 18-26h，tasks.md 估 23.4h，差异 +5%（更精细粒度 · 含测试 + 文档）

---

## 7. 实施顺序（推荐）

```
阶段 1 — PR 1（V3.0 · 2.5h）：
   T1 → (T2 / T3 / T4 并行)  [独立]

阶段 2 — PR 2 + PR 3（V3.1 + V3.2 · 10h）：
   T5 → T6 → T7 → T8 → T9 → T10 → T11
                                       ↓
   T12 → T13 → T14 → T15 → T16 → T17 → T18

阶段 3 — PR 4 + PR 5（V3.3 + V3.4 · 4.5h）：
   T19 → T20 → T21
                      ↓
   T22 → T23 → T24

阶段 4 — PR 6 + PR 7（V3.5 + V3.6 · 6.5h）：
   T25 → T26 → T27 → T28 [可与 PR 7 并行]
                                    ↓
   T29 → T30 → T31 → T32 → T33 → T34
```

---

## 8. 🎯 硬性 DOD（tasks.md 完成必须全过）

- [x] 每个任务 ≤ 1h AI 工作量（34/34，最大 60 min）
- [x] 每个任务 1 个 commit（产出字段已标）
- [x] 每个任务对应 ≥ 1 测试用例（§4 映射表覆盖全部 34 任务）
- [x] 任务依赖关系明确（DAG 无环，§3 依赖图）
- [x] 总估时 vs plan.md 偏差 ≤ 30%（21.6h vs 18-26h 中位数 22h，差异 ~2%）

> ✅ 工具校验：`python3 scripts/check-step.py tasks <file>`

---

## 9. 📚 相关文档

- [plan.md](plan.md) — 上游 2 步方案（13 决策 · 5 PR 拆分）
- [spec.md](spec.md) — 上游 1 步技术契约（14 GWT）
- [api-spec.md](api-spec.md) — 上游 2 步 API
- [db-design.md](db-design.md) — 上游 2 步数据库
- [component-spec.md](component-spec.md) — 上游 2 步组件
- [design-spec.md](design-spec.md) — 上游 1 步设计脑
- `docs/templates/test-cases-template.md` — 下游 4 步产出 test-cases.md
- `docs/DOD.md` §五 — 3 步拆分 DOD 完整定义