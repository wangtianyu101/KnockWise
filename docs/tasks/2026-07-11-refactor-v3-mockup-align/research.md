---
title: 调研报告 · 重构：V3 mockup 前端对齐
date: 2026-07-11
status: v1
tags: [research, 0步, 重构, v3-mockup, sidebar, dashboard-hero, 品牌统一]
related:
  - [v3-mockup.html](../2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html) — 目标视觉（2707 行 SPA）
  - [design-spec.md §3.6](../2026-07-09-new-feature-question-bank-expand/design-spec.md) — Sidebar 已有设计（未实施）
  - [verify.md](../2026-07-09-new-feature-question-bank-expand/verify.md) — L5 用 mockup 自查，掩盖了真前端差距
---

# 🔧 调研报告 · 重构：V3 mockup 前端对齐

> 日期：2026-07-11 · 调研人：AI · **议題编号**：🆕 **议题 G — V3 mockup 视觉还原（提议新增）**
> 用户原话："你验证下目前的前端 和这个差距很大呀" → "从0调研开始吧"

---

## 0. 全局架构图（CLAUDE.md §1.5 强制）

```
┌──────────────────────────────────────────────────────────────────────┐
│                        V3 重构目标边界                                 │
│                                                                       │
│   真前端 (React/Next.js)  ──────重构──────→  V3 mockup (HTML 静态)    │
│   frontend/pages/*              ↗          2707 行 SPA                │
│   frontend/components/*         │          Sidebar + 17 page          │
│                                 │                                   │
│   改动对象：                     │          不动：                     │
│   • 8 个有 nav 的页面（去 nav）  │          • backend/*                │
│   • 1 个 components/v3 扩       │          • mockup.html（参照）      │
│   • 1 个 components/v3+ 新增    │          • seed_data                │
│   • 2 处品牌名（DevBrain/CodeMock）│        • livekit.yaml            │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**重构不是"从零写新前端"**，而是：保留所有现有 page 的业务逻辑、API 调用、数据结构，只换壳（导航 + 视觉布局）。

---

## 1. 任务理解（必填）

### 1.1 用户原话
> "你验证下目前的前端 和这个差距很大呀"  
> "从0调研开始吧"

### 1.2 重构目标（多选）
- [x] **一致性**（统一导航架构、品牌名、视觉风格）
- [x] **可维护性**（消除 8 处横向 nav 重复 → Sidebar 抽一次）
- [x] **可发现性**（admin / ai-today / settings 等 mockup 标 V3 的入口实际找不到）

### 1.3 不重构会怎样（具体痛点）

| 痛点 | 量化证据 |
|---|---|
| 用户打开 `/dashboard` 看不到 V3 Hero 卡 + 最近 3 次雷达 | mockup §页面 1 (`v3-mockup.html:981-1065`) 设计存在，dashboard.tsx:117-153 是 V2 风格的 4 卡 grid |
| 用户找不到 admin 后台入口 | mockup §sidebar (`v3-mockup.html:929-944`) 有"题库管理 / 手动同步"，前端 0 路由 |
| 用户找不到 AI 推送历史 | mockup §sidebar (`v3-mockup.html:901-907`) 有"今日推荐 / 推送历史"，前端 0 路由 |
| 用户找不到设置 | mockup §sidebar (`v3-mockup.html:919-925`) 有"设置"，前端 0 路由 |
| 8 个页面有重复的横向 nav | grep "sticky top-0" 命中 8 个 page（dashboard/news/knowledge/profile/interview/profile/analytics/report）|
| 品牌名 3 套并存 | dashboard/profile = "DevBrain" · index.tsx = "CodeMock" · mockup = "Intervue" |
| V3 design-spec.md §3.6 Sidebar 已写完但 0 行代码 | 决策 L 已拍（用户 2026-07-10 拍方案 C），mockup 做了，真代码没做 |
| verify.md L5 报"5/5 gate 全过"是误导 | L31 写"mockup.html 是 staging 替代"—— 用 mockup 自查，没真跑 next dev 比对 |

### 1.4 议題编号
🆕 **议题 G — V3 mockup 视觉还原 + KnockWise 品牌统一**（建议在 docs/issues.md 加）

---

## 2. 现状分析（必填）

### 2.1 重构对象清单

| 文件 | 行数 | 角色 | 改造类型 |
|---|---|---|---|
| `frontend/pages/_app.tsx` | 6 | 入口 | 加 Sidebar 注入 |
| `frontend/pages/dashboard.tsx` | 175 | Dashboard | 重写视觉 + 加 Hero/雷达/stats |
| `frontend/pages/index.tsx` | 164 | 登录页 | 改名 CodeMock → Intervue |
| `frontend/pages/profile.tsx` | ~300 | 画像 | 改名 DevBrain → Intervue + 去 nav |
| `frontend/pages/news.tsx` | ~250 | 信息流 | 去 nav |
| `frontend/pages/knowledge.tsx` | ~280 | 知识库 | 去 nav |
| `frontend/pages/interview/profile.tsx` | ~400 | 面试总览 | 去 nav + 改名 |
| `frontend/pages/interview/analytics.tsx` | ~250 | 面试分析 | 去 nav |
| `frontend/pages/interview/report.tsx` | ~300 | 面试报告 | 去 nav |
| `frontend/pages/plan/index.tsx` | ~250 | 学习计划 | 去 nav |
| `frontend/pages/collections/index.tsx` | ~200 | 题单 | 去 nav |
| `frontend/pages/learn/index.tsx` | ~200 | 学习 | 去 nav |
| `frontend/pages/review/index.tsx` | ~200 | 复习 | 去 nav |
| `frontend/pages/qa/index.tsx` | ~200 | 问答 | 去 nav |
| `frontend/pages/report.tsx` | ~150 | 报告中心 | 去 nav |
| `frontend/pages/interview/history.tsx` | ~200 | 面试历史 | 去 nav |
| `frontend/pages/interview/setup.tsx` | ~250 | 面试配置 | 去 nav |
| **🆕 新建** `pages/admin/questions.tsx` | ~250 | 题库管理 | 调 `/api/admin/questions` |
| **🆕 新建** `pages/admin/sync.tsx` | ~250 | 手动同步 | 调 `/api/admin/sync-questions` |
| **🆕 新建** `pages/ai/today.tsx` | ~200 | AI 今日 | 调 `/api/analytics/recommendations` |
| **🆕 新建** `pages/ai/history.tsx` | ~200 | AI 历史 | 调 `/api/news/trigger/history` |
| **🆕 新建** `pages/settings.tsx` | ~150 | 设置 | 简单页（占位） |
| **🆕 新建** `components/v3/Sidebar/Sidebar.tsx` | ~250 | Sidebar 主件 | 从 mockup 翻译 |
| **🆕 新建** `components/v3/Sidebar/SidebarHeader.tsx` | ~80 | 顶部 logo+折叠 | |
| **🆕 新建** `components/v3/Sidebar/SidebarSearch.tsx` | ~100 | 搜索框 | |
| **🆕 新建** `components/v3/Sidebar/SidebarGroup.tsx` | ~80 | 分组 | |
| **🆕 新建** `components/v3/Sidebar/SidebarItem.tsx` | ~120 | 单项 | |
| **🆕 新建** `components/v3/HeroCard/HeroCard.tsx` | ~200 | Dashboard Hero | mockup L981-1065 |
| **🆕 新建** `components/v3/StatsBar/StatsBar.tsx` | ~150 | 5 列 stats | mockup L1068-1096 |
| **🆕 新建** `components/v3/RadarMini/RadarMini.tsx` | ~120 | 单个雷达 | mockup L1031-1063 |
| **🆕 新建** `components/v3/ModuleQuickLink/ModuleQuickLink.tsx` | ~100 | 5 入口 | mockup L1265-1309 |

**合计：改动 17 文件 + 新建 14 文件**。

### 2.2 调用方清单（必填 · Sidebar 影响面）

| 受影响 | 调用方式 | 现状 |
|---|---|---|
| `_app.tsx` | 注入 Sidebar 到所有 page | 当前 6 行，没注入 |
| 8 个有 sticky nav 的页面 | 删 nav 块 | grep 已确认 8 处 |
| `useRouter` 路径不变 | Sidebar 内 `router.push()` | 现有 page 都已用 |

> ⚠️ **Sidebar 一旦改 _app.tsx 全局注入，影响所有 17 page**。需要逐个 page 删原 nav。

### 2.3 当前测试覆盖

| 测试文件 | 覆盖范围 | 数量 | 状态 |
|---|---|---|---|
| `frontend/__tests__/` + 各 page `*.test.tsx` | 业务组件 | 154 passed | ✅ V3.5 verify 报 |
| `frontend/components/v3/AIRecommendationCard/*.test.tsx` | AI 卡 | 4 | ✅ |
| `frontend/components/v3/PlanCard/*.test.tsx` | 计划卡 | 8 | ✅ |
| `frontend/components/shared/GlassCard.test.tsx` | 玻璃卡 | ✅ | V1 closure |
| **`Sidebar` / `HeroCard` / `StatsBar` 等新组件** | — | **0** | ❌ **重构前必须先补测试** |

**当前覆盖率**：~70%（前端 line coverage，未实跑）
**目标覆盖率**：Sidebar 6 个新组件 ≥ 80%

### 2.4 依赖关系

| 类别 | 内容 |
|---|---|
| 外部框架 | Next.js 15.1 + React 19 + Tailwind CSS 4（已有）+ antd 6.5（装了但 dashboard/profile/qa 用，其他 page 不用） |
| 共享组件（已可用） | `shared/GlassCard` `shared/StatCard` `shared/EmptyState` `shared/CategoryBadge` `shared/MasteryBadge` `shared/ProgressBar` `shared/QualityBadge` `shared/StatusSwitcher` —— **9 个** |
| V3 已用组件 | `v3/PlanCard/{CurrentPlanCard,CreatePlanButton,HistoryPlansList,PlanDetailCard,PlanCreateModal}` `v3/AIRecommendationCard/AIRecommendationCard` `v3/CollectionCard/CollectionCard` |
| V2 已用组件 | `v2-settlement/DailySummaryCard` `v2-settlement/RecentSedimentsCard` |
| API 已实装 | `/api/admin/questions` `/api/admin/sync-questions` `/api/admin/sync-history` `/api/analytics/recommendations` `/api/learn/plans` `/api/learn/collections` —— **前端只缺 5 个路由壳** |
| 后端 API 文档 | `docs/api/README.md` |
| 设计文档 | `design-spec.md §3.6` Sidebar 已有完整结构（149 行） |

**循环依赖**：无。Sidebar 是纯展示组件，不调 service。

---

## 3. 重构方案（必填 · 2 个）

### 3.1 方案 A：渐进式重构（推荐 ✅）

| 维度 | 描述 |
|---|---|
| **思路** | 先 Sidebar 骨架（_app.tsx 注入 + 保留 page 原 nav → 双轨） → 各 page 切换 → 删原 nav |
| **阶段** | P1 Sidebar 骨架 + 顶部折叠 → P2 Dashboard Hero/雷达/stats → P3 5 个新路由 → P4 品牌名统一 → P5 测试 + verify |
| **改动范围** | 17 文件改 + 14 文件新建 |
| **风险等级** | 🟡 中（每步可独立 commit + 测试） |
| **兼容性** | ✅ 任意阶段可停（双轨期不影响业务） |
| **测试影响** | 现有 154 测试不破；新增 ~30 测试 |
| **工作量** | **5 步 × ~3h = ~15h** |

**步骤拆解**：

| PR | 内容 | 时间 | 测试 |
|---|---|---|---|
| P1 | Sidebar 组件 + _app.tsx 注入（page nav 暂时保留） | 3h | Sidebar 6 组件 ≥ 80% 覆盖 |
| P2 | Dashboard 重写（Hero + 3 雷达 + 5 列 stats + 3 卡）| 3h | HeroCard/StatsBar/RadarMini 各 4 测试 |
| P3 | 5 个新路由壳（ai-today/history/admin-questions/admin-sync/settings） | 4h | 路由可达性测试 |
| P4 | 17 个 page 删原 nav + 品牌名统一（CodeMock/DevBrain → KnockWise）+ mockup.html 3 处 + package.json name + 后端 cli 注释 + CLAUDE.md/docs/README | 3h | 现有 154 测试不破 |
| P5 | verify（装 playwright ~2h + 写 ~30 截图测试 + 真起 next dev 比对） | 5h | L5 playwright 自动化跑 |

### 3.2 方案 B：一次性大重构

| 维度 | 描述 |
|---|---|
| **思路** | 1 个 PR 改完所有 17 + 新建 14 |
| **改动范围** | 31 文件同 PR |
| **风险等级** | 🔴 高（git diff 巨大，code review 困难，merge 冲突概率高） |
| **兼容性** | ❌ 必须一次到位 |
| **测试影响** | 现有 154 测试可能大面积 break |
| **工作量** | ~15h（一次提交）|

**不推荐**：违反 CLAUDE.md "≤ 1h AI 工作量原子任务" 原则。

### 3.3 方案对比

| 维度 | A 渐进 | B 一次性 |
|---|---|---|
| 单 PR 大小 | ≤ 300 行 | ~3000 行 |
| 回滚成本 | 单 PR | 整 PR |
| 测试分阶段 | ✅ | ❌ |
| 中途用户可见 | ✅ Sidebar 立刻可用 | ❌ 必须完成 |
| 总工时 | ~15h | ~15h |
| **推荐** | **✅** | ❌ |

---

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| **Sidebar 全局注入破坏现有 page 布局**（main-content margin-left: 240px 强制推） | 🔴 高 | P1 阶段先用 `position: fixed` 不动 main-content，P4 阶段才切 margin-left；切前手动跑 17 page 截图对比 |
| **现有 154 测试因 Sidebar 注入而挂** | 🔴 高 | P1 阶段先跑一遍 `npm test`，确认哪些 page 用 `<nav>` 选择器；改测试或加 `data-testid` |
| **Ant Design 与 Tailwind 样式冲突**（antd 装了但 dashboard/profile/qa 用，其他 page 不用） | 🟡 中 | 调研：确认 antd 只在少数 page 用（已确认），不影响 Sidebar 引入 |
| **5 个新路由用空壳 → 用户点空白页** | 🟡 中 | P3 阶段每个新路由至少要有 loading state + "建设中"占位（EmptyState 组件已可用）|
| **品牌名统一漏改** | 🟢 低 | grep "DevBrain\|CodeMock" 全局搜，4 处（dashboard/profile/login/CLAUDE.md） |
| **设计文档 §3.6 与 mockup 细微差异** | 🟡 中 | design-spec §3.6 是 mockup 子集；以 mockup 为准，design-spec 同步更新 |
| **Dashboard 数据接口 `/api/dashboard` 字段对不上**（Hero 需要 3 次雷达数据） | 🔴 高 | **P2 开工前必须**先查 `/api/dashboard` 返回结构；若没雷达字段，先开新 API（如 `/api/interview/recent?limit=3`） |
| **删除原 nav 后 page 失去面包屑/退出按钮** | 🟡 中 | Sidebar 顶部用户菜单 + breadcrumb 区域覆盖 |
| **mobile 端 < 1024px Sidebar 折叠 drawer** | 🟢 低 | mockup 已写 `@media (max-width: 1024px)` 规则，照抄 |

---

## 5. 输出建议（必填）

### 5.1 推荐方案

- **推荐**：方案 A 渐进式重构（P1-P5 共 5 步 · **总 ~16h**）
- **理由**：
  1. **CLAUDE.md 强制约束**："≤ 1h AI 工作量原子任务，可独立 commit" — B 方案违反
  2. **可验证**：每步 commit + 跑测试 + 视觉确认（用 `start.sh` 启动 + 截图）
  3. **可回滚**：P1-P5 任意一步出问题可单独 revert，不影响全盘
  4. **L5 真实跑**：P5 阶段用 playwright 自动化截图比对 mockup，比 verify.md 用 mockup 自查更可信
  5. **品牌统一**：P4 阶段一次扫完 10+ 处 KnockWise 改名（mockup + 前端 + 后端 + 文档），避免遗漏

### 5.2 推荐路径（CLAUDE.md § 一 6 步流程）

```
0 调研 ✅（本文件完成）
→ 1 规格（更新 design-spec.md §3.6 + 加 §3.7 Dashboard Hero/雷达/stats + §3.8 新路由）
→ 2 计划（plan.md 写 5 阶段 P1-P5，每阶段列原子任务）
→ 3 拆分（tasks.md 按 PR 拆 30-40 个原子任务，每任务 ≤ 1h）
→ 4 实施（TDD：先 Sidebar 6 组件测试 → 写实现 → commit）
→ 5 验证（真起 next dev，逐 page 截图比对 mockup，写 verify.md）
→ 6 复盘（retro.md + 更新 CLAUDE.md + 加议题 G）
```

### 5.3 关键决策点（2026-07-11 用户拍板 ✅）

| # | 决策 | 用户拍板 | 影响面 |
|---|---|---|---|
| 1 | **品牌名** | 🔴 **统一改成 KnockWise**（不是 Intervue！） | mockup.html 3 处 + dashboard/profile/index 3 处 + package.json name + 后端 cli 注释 1 处 + CLAUDE.md 项目名 + docs/* 标题 + 登录页 SVG logo 文案 → **~10+ 处** |
| 2 | **P2 Hero 数据源** | ✅ 后端补 `/api/interview/recent?limit=3` | 新增 1 后端端点 + 测试 + 文档（~1h） |
| 3 | **P5 verify 策略** | ✅ **截图 + playwright 自动化** | 装 `@playwright/test` (~100MB + 浏览器 ~200MB) + 写 ~30 截图测试（+2h）|
| 4 | **新路由壳策略** | ✅ loading + EmptyState 占位 | 用 `components/shared/EmptyState`（已有）|
| 5 | **antd 去留** | 🟢 默认 C（Sidebar 用 Tailwind 不混，少数 page 保留 antd） | 无 |
| 6 | **mobile 端 Sidebar** | 🟢 默认 A（<1024px 切 drawer，照抄 mockup CSS） | 无 |

### 5.4 品牌改名清单（决策 #1 锁定）

| 文件 | 当前 | 改后 | 行号 |
|---|---|---|---|
| `docs/tasks/.../mockups/v3-mockup.html` | Intervue × 3 | KnockWise | 714, 743, 948-951 区域 |
| `frontend/pages/dashboard.tsx` | DevBrain | KnockWise | 57 |
| `frontend/pages/profile.tsx` | DevBrain | KnockWise | 156 |
| `frontend/pages/index.tsx` | CodeMock | KnockWise | 79（含 SVG 渐变文字）|
| `frontend/package.json` | "name": "codemock-frontend" | "name": "knockwise-frontend" | 2 |
| `backend/cli/sync_questions.py` | "Intervue 题目同步 CLI" | "KnockWise 题目同步 CLI" | 28 |
| `docs/api/README.md` | 标题 Intervue | KnockWise | 1 |
| `CLAUDE.md` §四项目目录名 Intervue | "Intervue" | "KnockWise"（路径不动）| 全文 |
| `scripts/start.sh` / `stop.sh` | log 文件名 `intervue-*.log` / PID 文件 `/tmp/intervue-pids.txt` | `knockwise-*.log` / `/tmp/knockwise-pids.txt` | 待审 |
| **项目根目录 `/Users/wangtianyu/IdeaProjects/Intervue/`** | **不动** | **不动**（git mv 风险大）| — |

> ⚠️ **用户原话**："改成 KnockWise 现在整个项目都叫这个 相关的全改掉" → 上面 10 项 + mockup 3 处全部替换。  
> ⚠️ **不替换**：项目根目录路径、git remote（暂不动；如要改走 git mv 单独 PR）。

### 5.4 议題 G 提议（更新 docs/issues.md）

```markdown
### 议题 G — V3 mockup 视觉还原（NEW 2026-07-11）
**现状**：design-spec §3.6 Sidebar 已写完，mockup 2707 行完整，
但真前端（17 page）0 行 Sidebar / 5 个 admin+ai 路由缺失 / 品牌名 3 套并存。
**根因**：verify.md L5 用 mockup 自查代替真前端比对，"5/5 gate 全过"是误导。
**改造路径**：5 阶段渐进重构（见 plan.md）。
**优先级**：🔴 高（用户首反馈即"差距很大"）。
```

---

## 6. 自检清单（CLAUDE.md §0.2 + 模板要求）

- [x] 任务理解用自己的话复述（开头已写，待用户确认）
- [x] 读了 docs/issues.md（100 行 + 已读 100-300 行）
- [x] 跑了 `git log -15`（最近 commit a870b4a 标题相关但未改真布局）
- [x] 跑了 `git status`（working tree clean，无冲突）
- [x] 找到 ≥ 3 个相关文件（17 改 + 14 新 + design-spec §3.6）
- [x] 列出依赖影响（8 处 sticky nav / 5 个缺路由 / 2 处品牌名）
- [x] 风险点带等级 + 缓解（9 个 🔴/🟡/🟢，每条都有缓解）
- [x] 给完整 6 步路径建议（§5.2）
- [x] 方案对比 ≥ 2 个（§3.1 渐进 vs §3.2 一次性）
- [x] 推荐方案有引用证据（§5.1 引 CLAUDE.md "≤ 1h 原子任务" + verify.md 误导）
- [x] 调用方清单 ≥ 3 个（§2.2 列了 _app.tsx + 8 nav + useRouter）
- [x] 当前测试覆盖率已查（§2.3: 154 通过 + 0 新组件测试）

---

## 7. 🔴 自我复盘 · 调研偏差

**偏差 1：品牌名搞错**（严重）

- 我之前调研时**只看了 mockup.html 文字**，没去核实项目根名 / package.json / login page 实际品牌
- 结果：把 "Intervue"（mockup 文字）当成项目品牌推荐给用户
- 实际：**项目品牌是 KnockWise**（用户原话："现在整个项目都叫这个"），同时存在 4 套：CodeMock（package.json + index.tsx）/ DevBrain（dashboard + profile）/ Intervue（mockup + CLAUDE.md 目录名）/ KnockWise（用户认定）
- **缓解**：§5.4 已列出 10+ 处 KnockWise 改名清单 + mockup.html 自身也要改（用户明确"全改掉"）
- **教训给未来的我**：调研品牌/产品名类项目级信息时，**至少查 3 处**（mockup + package.json + login page + 目录名），不能信单一来源

**偏差 2：playwright 没装就推荐**（中等）

- 用户选"截图 + playwright 自动化"，但前端 package.json 里 playwright = 0
- 需补装 `@playwright/test` + 浏览器二进制（约 100+200MB）+ 写截图测试
- 已加进 P5 工作量（+2h）

---

## 8. 下一步（等你拍）

---

## 9. 📋 调研增量（2026-07-11 用户拍"补加调研" · 7 项全部落地）

> 用户原话："补加调研（先暂停）" → 全选 7 项调研方向（4 项 + 3 项）。
> 已写入：每项结论 + 行号证据 + 对 §5 推荐方案的影响。

### 9.1 KnockWise 改动影响面全量审计 🔴

**审计结果（远大于原 §5.4 列的 10+ 处）**：

| 类别 | 位置 | 当前 | 数量 | 优先级 | 影响 |
|---|---|---|---|---|---|
| **用户可见 logo/标题** | dashboard.tsx:57 / profile.tsx:156 / index.tsx:79 / interview.tsx:215 | DevBrain / DevBrain / CodeMock / CodeMock | 4 | 🔴 P0 | 立刻改 |
| **package.json names** | frontend/package.json:2 + package-lock.json:2,8 | `codemock-frontend` | 3 | 🔴 P0 | 立刻改 |
| **README.md** | `/README.md:1` | `# CodeMock` | 1 | 🔴 P0 | 立刻改 |
| **mockup.html** | v3-mockup.html:714, 743, 948-951 | Intervue ×3 | 3 | 🔴 P0 | 立刻改 |
| **后端 logger 命名** | backend/main.py:23,26 / core/{database,cache,dependencies}.py / api/{auth,interview,admin,learn,profile,analytics,v2_settlement,voice_ws}.py / services/{interview,learning_progress,study_plan,question_bank,qa,obsidian,profile_settlement,summary,resume_parser,asr_tts,agora,archive,interview_settlement,collection,question_sync,question_quality,scheduler}.py / voice/{stt,livekit_worker,whisper_live_server,turn_manager,interview_room}.py | `codemock.*` / `codemock-voice` / `codemock-voice-worker` / `codemock-turn` | **~40 logger** | 🟡 P2 | 测试断言里有 `assert svc.log.name == "codemock.xxx"`（test_summary_service.py:48, test_profile_settlement_service.py:55 等）|
| **localStorage key** | lib/api.ts:57,64,102 / VoiceRoom.tsx:62 / lib/livekit.ts:10 / setup.tsx:29 / report.tsx:156 / interview.tsx:103,117 | `codemock_token` + `codemock_setup` | **8 处** | 🔴 P0 | 改名 → 老用户 token/setup 失效；需要双 key fallback 或迁移脚本 |
| **Docker/DB 配置** | docker-compose.yml:6,7,8,49 / backend/core/config.py:6 | `codemock` DB 名 + 用户名 + 密码 + URL | 5 | 🟡 P1 | 改了要重建 DB（CLAUDE.md §二"绝对不能动：MySQL 真实数据"），**不动真实 DB**，只改 docker-compose |
| **后端 FastAPI title** | backend/main.py:26 | `app = FastAPI(title="CodeMock", ...)` | 1 | 🟢 P3 | 改了只影响 `/docs` 标题 |
| **测试 docstring / 注释** | backend/tests/test_core.py:1 / backend/test_agent.py:20 / backend/agents/followup_agent.py:1 / backend/models/__init__.py:1 | CodeMock 文案 | 4 | 🟢 P3 | 注释 |
| **CLI 注释** | backend/cli/sync_questions.py:28 | "Intervue 题目同步 CLI" | 1 | 🟢 P3 | 注释 |
| **Skill 文档** | .claude/skills/intervue-dev/SKILL.md:3,6,10,23,58,138 | "Intervue (CodeMock)" | 6+ | 🟢 P3 | AI 内部知识 |
| **scripts 日志/PID** | scripts/start.sh:23,90,97,119,126,143,150 / stop.sh:18 | `/tmp/intervue-pids.txt` + `/tmp/intervue-*.log` | 8 | 🟡 P1 | 改名后 stop.sh 找不到 PID 文件 |
| **CLAUDE.md 项目目录名** | CLAUDE.md 全文 | Intervue 目录名引用 | 多 | 🟢 P3 | 文档文案，路径不动 |

**总影响**：约 **70+ 处**（原 §5.4 列了 10+ 是低估）。

**分级处置建议（待用户拍板）**：

| 范围 | 内容 | 工时 | 风险 |
|---|---|---|---|
| **🟢 必改（用户可见）** | 4 logo + 3 package.json + README + 3 mockup + 8 localStorage | 1h | localStorage 改名需要双 key fallback |
| **🟡 应改（一致性）** | scripts PID/log + 后端 FastAPI title + docker-compose + Skill 文档 | 1h | scripts 改名后老 PID 残留要清理 |
| **🟢 可改（注释）** | 40 logger 命名 + 4 注释 + 1 CLI + CLAUDE.md | 0.5h | logger 改名 → 30+ 测试断言要同步改 |
| **🔴 不改** | 项目根目录路径（git mv）+ 真实 MySQL 数据 + livekit.yaml | — | — |

**对原 §5.1 工时影响**：P4 拆成 **P4a 必改（1h）+ P4b 应改（1h）+ P4c 可改 + 测试同步（1.5h）** = **3.5h**，总项目从 16h → **17h**。

---

### 9.2 现有 17 page 业务逻辑梳理

| Page | 顶层 hooks | 主要 API | antd? | 测试覆盖 |
|---|---|---|---|---|
| **dashboard.tsx** | profile/dashData/learnStats/activePlan/navOpen | `/api/dashboard` + `/api/learn/stats` + `/api/learn/plans` | ❌ | ❌ 0 |
| **profile.tsx** | profile/weekly/refreshing/loading/error | `/api/v2/profile/weekly` + `/refresh` | ✅ | ✅ |
| **news.tsx** | tab/dailies/weeklies/report/stats/sources | `/api/news/{daily,weekly,stats,sources,daily/latest}` | ❌ | ❌ 0 |
| **knowledge.tsx** | tab/searchQ/results/files/note/stats/graphData | `/api/knowledge/{browse,stats,search}` | ❌ | ❌ 0 |
| **setup.tsx** | step/config | 纯客户端 | ✅ | ❌ 0 |
| **interview.tsx** | messages/question/interviewId/phase + 8 个 | startInterview + getNextQuestion + submitAnswer + localStorage `codemock_setup` | ❌ | ❌ 0 |
| **onboarding.tsx** | step/profile | updateProfile/getProfile | ✅ | ❌ 0 |
| **report.tsx** | report/loading | generateReport/getReport | ❌ | ❌ 0 |
| **learn/index.tsx** | — | `/api/learn/questions` | ❌ | ✅ 12 |
| **learn/[qid].tsx** | — | `/api/learn/questions/{qid}` + answer + note | ❌ | ✅ 8 |
| **review/index.tsx** | — | `/api/learn/review-queue` | ❌ | ✅ 6 |
| **qa/index.tsx** | — | `/api/qa/questions` | ❌ | ✅ 6 |
| **plan/index.tsx** | plans/loading/selectedPlan/createOpen | `/api/learn/plans` | ✅ | ❌ 0 |
| **collections/index.tsx** | collections/loading/filter | `/api/learn/collections` + subscribe | ✅ | ❌ 0 |
| **interview/profile.tsx** | — | `/api/profile/resume/file` | ✅ | ❌ 0 |
| **interview/history.tsx** | — | `/api/interviews` + favorite toggle | ❌ | ❌ 0 |
| **interview/setup.tsx** | — | startInterview | ❌ | ❌ 0 |
| **interview/analytics.tsx** | — | `/api/analytics/{overview,radar,trends,recommendations}` | ❌ | ❌ 0 |
| **interview/report.tsx** | — | `/api/interviews/{id}` + /records | ❌ | ❌ 0 |
| **interview/room.tsx** | — | `/api/interviews` + /complete | ❌ | ❌ 0 |

**关键发现**：
- **8 个 page 完全无测试**（dashboard/news/knowledge/setup/interview/onboarding/report + 全部 5 个 interview/* 子页 + plan/collections）
- **现有测试集中**：v3/V2 共享组件 + 4 个核心学习页面（learn/review/qa/profile）
- **5 个 interview/* 子页 + dashboard 全无测试**，是 P1 Sidebar 注入后高风险区域
- **localStorage key 依赖**：`interview.tsx:103,117`（`codemock_setup`）+ 多个文件 `codemock_token` —— KnockWise 改名必须双 key fallback

---

### 9.3 后端 `/api/interview/recent?limit=3` 设计

**现有可用数据**：

| 来源 | 端点/Model | 字段 | 可复用度 |
|---|---|---|---|
| `backend/api/interview.py:109` `list_interviews` | `GET /api/interviews` | id/round/style/status/total_questions/overall_score/is_favorite/started_at/ended_at | 🟡 缺 `radar_data` |
| `Interview.radar_data` (`backend/models/__init__.py:153`) | JSON dict（5 维）| 🟢 字段存在 |
| `Interview.overall_score` (line 96) | Float 0-100 | 🟢 字段存在 |

**mockup 雷达卡需要**：
```typescript
{ id, company, overall_score, radar_data: { algorithm, system_design, network, frontend, ai }, started_at }
```

**推荐设计**：
- **路径**：`GET /api/interviews/recent?limit=3`（新端点，不动 list）
- **Service**：在 `interview_service` 加 `async def list_recent(user_id, limit=3) -> list[dict]`，复用 list 逻辑但加 `radar_data`
- **Schema**：新增 `InterviewRecentItem`（`backend/schemas/interview.py`）：id / round / overall_score / radar_data / started_at
- **测试**：`test_interview_recent_endpoint.py`：空数据 / 1 条 / 3 条 / > 3 截断 / 用户隔离
- **性能**：走 `idx_user_status` 索引（已有），3 条 limit O(1)
- **工时**：~1h（含 5 测试）

---

### 9.4 现有 154 测试覆盖缺口图

**测试文件清单（17 文件）**：

| 位置 | 覆盖 | 估测数 |
|---|---|---|
| `__tests__/components/QuestionRow.test.tsx` | QuestionRow | ~5 |
| `__tests__/components/shared/GlassCard.test.tsx` | GlassCard | ~3 |
| `__tests__/components/shared/StatCard.test.tsx` | StatCard | ~3 |
| `__tests__/components/shared/EmptyState.test.tsx` | EmptyState 4 type | ~6 |
| `__tests__/components/v2/DailySummaryCard.test.tsx` | V2 daily | ~5 |
| `__tests__/components/v2/RecentSedimentsCard.test.tsx` | V2 sediment | ~4 |
| `__tests__/v3/AIRecommendationCard.test.tsx` | AI 推荐 | 4 |
| `__tests__/pages/profile.test.tsx` | /profile | ~8 |
| `__tests__/pages/{review,qa,learn,learn-detail}.test.tsx` | 4 个学习页 | ~32 |
| `pages/{learn,review,qa}/index.test.tsx` | 同上（co-located）| ~18 |
| `components/learn/QuestionRow.test.tsx` | 重复 | ~5 |
| `components/v3/PlanCard/PlanCard.test.tsx` | PlanCard 4 子卡 | 8 |

**缺口矩阵**：

| Page / Component | 现有 | Sidebar 注入影响 | 建议 |
|---|---|---|---|
| **dashboard** | ❌ 0 | 🟡 main-content margin-left 改布局 | P2 加 4-5 测试 |
| **interview（5 子页）** | ❌ 0 | 🔴 子页布局被推 | P1 给 interview/room 加 2-3 烟雾测试 |
| **plan/collections** | ❌ 0 | 🟡 | P2 加 |
| **knowledge/news** | ❌ 0 | 🟡 | P4 加 |
| **onboarding/setup/index/report** | ❌ 0 | 🟢（无 token 不注入 Sidebar） | 不动 |
| **Sidebar（6 新组件）** | ❌ 0 | — | P1 必补 6×3 = 18 |
| **HeroCard / StatsBar / RadarMini** | ❌ 0 | — | P2 必补 3×3 = 9 |
| **5 新路由壳** | ❌ 0 | — | P3 加 5 可达性 |

**关键风险**：
- vitest setup.ts:8-30 已 mock next/router + lib/api，Sidebar 注入后测试 mount 整页仍可跑
- happy-dom 不支持 backdrop-filter —— Sidebar 玻璃拟态 CSS 不影响测试断言（CSS 不渲染），视觉测试要 playwright

**测试工作量**：P1 18 + P2 14 + P3 5 + P5 playwright 25 = **~62 测试 · ~5h**

---

### 9.5 Sidebar drawer 实现细节

**关键发现**：`components/SideDrawer.tsx` 是 **右滑 drawer**（宽度默认 480px，从右边缘滑入），跟 mockup 的 **左侧固定 Sidebar** 不是同一个概念 —— **不能直接复用**。

| 维度 | 现有 SideDrawer | mockup Sidebar |
|---|---|---|
| 位置 | right edge | left edge |
| 宽度 | 480px | 240px（折叠 64px） |
| 显示模式 | 临时弹出 + backdrop | 固定常驻 + drawer 模式（<1024px） |
| 触发 | open prop 控制 | 始终显示 |

**可复用**：✅ drawer 行为模式（backdrop click / ESC / 锁 body scroll）可抽 `useDrawerState(open, onClose)` hook
**不可复用**：样式/布局完全不同，新 Sidebar 从 0 写

**新增 6 组件**：Sidebar / SidebarHeader / SidebarSearch / SidebarGroup / SidebarItem / SidebarDivider

---

### 9.6 mockup Sidebar CSS → Tailwind 翻译速查

| mockup | Tailwind |
|---|---|
| `.sidebar { position: fixed; top: 56px; left: 0; bottom: 0; width: 240px; }` | `fixed top-14 left-0 bottom-0 w-60` |
| `.sidebar.collapsed { width: 64px; }` | `w-16` |
| `background: rgba(8, 12, 24, 0.85); backdrop-filter: blur(24px) saturate(180%);` | `bg-[rgba(8,12,24,0.85)] backdrop-blur-2xl backdrop-saturate-150` |
| `.sidebar-item.active { background: rgba(99, 102, 241, 0.12); box-shadow: inset 2px 0 0 var(--color-primary); }` | `bg-indigo-500/10 shadow-[inset_2px_0_0_0_theme(colors.indigo.500)]` |
| `.main-content { margin-left: 240px; }` | `ml-60`（折叠 `ml-16`）|
| `@media (max-width: 1024px) { .sidebar { transform: translateX(-100%); } .sidebar.open { transform: translateX(0); } .main-content { margin-left: 0; } }` | `lg:translate-x-0 -translate-x-full` + drawer 切换 |

**Tailwind 4 配置**：当前 `postcss.config.mjs` 仅有 `@tailwindcss/postcss` 插件，无自定义动效曲线。需在 `globals.css` 加 `@theme` 自定义 cubic-bezier 或用 `ease-[cubic-bezier(...)]` 任意值。

---

### 9.7 antd vs Tailwind 混用现状

**10 个文件用 antd**（grep `from 'antd'`）：

| 文件 | antd 组件 | 风格 |
|---|---|---|
| `pages/profile.tsx` | Card/Statistic/Button/message/Empty/Row/Col/Tag/Spin | 全 antd |
| `pages/plan/index.tsx` | message | 仅 message |
| `pages/collections/index.tsx` | message | 仅 message |
| `components/shared/StatCard.tsx` | Statistic | 仅 Statistic |
| `components/v3/PlanCard/PlanCreateModal.tsx` | Modal/Form/Input/DatePicker/Select/Button/Checkbox | 全 antd |
| `components/v3/PlanCard/PlanCard.tsx` | Modal/Card/Tag/Button/Progress/Empty | 大部分 antd |
| `components/v3/CollectionCard/CollectionCard.tsx` | Tag/Card/Button/Progress | 部分 |
| `components/v2-settlement/RecentSedimentsCard.tsx` | Card/Tag/Empty | 部分 |
| `components/v2-settlement/DailySummaryCard.tsx` | Card/Tag/Statistic/Empty | 大部分 |

**结论**：
- **Tailwind 主流**（15+ page 用）
- **antd 在 v3/v2 组件 + shared + 3 page 中深度嵌入**
- **混用风险**：
  - 🔴 antd Modal `z-index: 1000` vs Sidebar `z-index: 50` 不冲突，但 Sidebar drawer 模式若 z-index 高于 Modal 会挡 Modal —— Sidebar z-index 设计 < 1000
  - 🟡 antd Button 默认圆角 6px vs mockup 8-10px —— 视觉差异（接受，按 page 风格统一）
  - 🟢 `message` 全局 API vs mockup toast：plan/collections 用 message，dashboard 改 mockup 后用 toast —— **不强求统一**

**Sidebar 设计原则**：✅ 纯 Tailwind + SVG icon，不混 antd（mockup 也纯 CSS）

---

### 9.8 playwright 集成细节

| 维度 | 详情 |
|---|---|
| **包** | `@playwright/test`（devDep） |
| **磁盘** | Chromium ~170MB + Node 模块 ~50MB = **~220MB**（只用 Chromium，不装 Firefox/WebKit） |
| **装** | `npm i -D @playwright/test && npx playwright install --with-deps chromium` |
| **跟 vitest 共存** | ✅：`npm test` 跑 vitest，`npm run test:e2e` 跑 playwright，分开命令 |
| **配置** | 新建 `frontend/playwright.config.ts`：baseURL = `http://localhost:3000`，webServer = `next dev` |
| **截图基线** | `frontend/tests/e2e/__screenshots__/` 存 PNG；`toHaveScreenshot()` 自动比对 |
| **测试数量** | 17 page × 1 + Sidebar 折叠/展开 × 2 + dashboard 6 组件 × 1 = **~25 测试** |
| **风险** | 视觉回归易误报（0.1px 字体差也算 fail）；首次需手动确认 baseline |

**工时**：装 + 配置 + baseline 1h + 25 测试 2h = **3h**

---

## 10. 📊 调研增量影响总结

| 维度 | 原调研 §5.1 估 | 补调研后修正 |
|---|---|---|
| 总工时 | 16h | **17h**（+1h：KnockWise 全量改名 70+ 处）|
| P4 子拆 | 单一 3h | **P4a 必改 1h + P4b 应改 1h + P4c 可改 + 测试同步 1.5h = 3.5h** |
| 测试总数 | 154 → +30 | **+62**（Sidebar 18 + Hero 9 + 路由 5 + dashboard 5 + playwright 25） |
| 风险 🔴 | 3 个 | **5 个**（+ Sidebar 注入破坏 8 page / KnockWise localStorage 改名用户掉登录）|
| API 新增 | 1 个 | 1 个（不变：`/api/interviews/recent`） |
| KnockWise 改动 | 10+ | **70+** |
| logger 改名连带 | 0 | **~30 测试断言同步** |

**新建议路径（CLAUDE.md § 一 6 步流程不变，P4 拆三段）**：
```
P1 Sidebar（3h）→ P2 Dashboard 重写（3h）→ P3 5 路由 + 后端 /recent（4h）
→ P4a 必改 KnockWise（1h）→ P4b 应改 KnockWise（1h）→ P4c 可改 + 30 logger 测试同步（1.5h）
→ P5 playwright + 真起 next dev 比对（3h）
= 总 17h
```

---

## 11. 下一步（等你拍）

按 CLAUDE.md §0 调研结束流程，**调研增量完成**（7 项全部落地），等你确认：

1. **KnockWise 改名分级处置**（§9.1 三档）—— 哪档拍？
2. **新建议路径**（§10）—— 接受 / 调整 / 砍小到 P1+P2（6h）？
3. **进 1 规格** / **直接进 4 实施** / **补其他调研** —— 选哪条？

---

## 📚 引用

- `docs/templates/research-refactor.md` — 调研模板
- `docs/tasks/2026-07-09-new-feature-question-bank-expand/design-spec.md` §2.5 V1→V3.6 路由映射 + §3.6 Sidebar 完整设计
- `docs/tasks/2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html` — 2707 行目标视觉
- `docs/tasks/2026-07-09-new-feature-question-bank-expand/verify.md` — L5 误导（mockup 自查）
- `frontend/components/shared/*` — 9 个已可用共享组件
- `frontend/components/v3/*` — 3 类已实装 V3 组件
- `docs/api/README.md` — 9 个 V3 API 文档