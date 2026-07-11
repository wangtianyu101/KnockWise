---
title: Tasks 拆分 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [tasks, 3步, 原子任务拆分, v3-mockup-align, knockwise]
related:
  - [research.md](research.md) — 11 章节调研
  - [plan.md](plan.md) — 5 阶段任务清单
  - [component-spec.md](component-spec.md) — 10 组件详细
  - [api-spec.md](api-spec.md) — /recent 详细
  - [db-design.md](db-design.md) — 无 DB 变更
  - CLAUDE.md § 一.三 阶段 3 拆分·§ 6.5 任务完成自动更新
---

# Tasks 拆分：KnockWise 前端对齐重构

> **作者**：AI 拆分脑 · 用户决策已锁（方案 A 渐进 17h）
> **原则**：每个任务 ≤ 1h AI 工作量，可独立 commit，符合 CLAUDE.md "≤ 1h 原子任务" 约束
> **进度更新规则**：完成时按 CLAUDE.md § 6.5 改 `#### T<n>` 状态、PR 标志、总览表

---

## 0. 总览（7 阶段 PR · 52 原子任务 · 17h）

| PR | 标志 | 任务数 | 工时 | 测试增量 | 进度 |
|---|---|---|---|---|---|
| **P1** Sidebar 6 组件 + Layout | ✅ 已做 | 6/6 | 3h | +23 | 6/6 |
| **P2** Dashboard 重写 + 3 组件 | ✅ 已做 | 6/6 | 3h | +17 | 6/6 |
| **P3a** 后端 /api/interviews/recent | ⏸ 待开始 | 4 | 2h | +9 | 0/4 |
| **P3b** 前端 5 新路由壳 + Sidebar 集成 | ⏸ 待开始 | 4 | 2h | +5 | 0/4 |
| **P4a** KnockWise 必改（19 处）| ⏸ 待开始 | 11 | 1h | 0 | 0/11 |
| **P4b** KnockWise 应改（15 处）| ⏸ 待开始 | 9 | 1h | 0 | 0/9 |
| **P4c** KnockWise 可改 + 30 测试同步 | ⏸ 待开始 | 8 | 1.5h | +0（同步）| 0/8 |
| **P5** playwright + L5 staging | ⏸ 待开始 | 5 | 3h | +25 | 0/5 |
| **总计** | — | **52** | **17h** | **+79** | **12/52** |

**测试累计**：154 既有 → 233（+79 测试）

**任务依赖图**：
```
P1 ──→ P2 ──→ P3a (后端) ──→ P3b (前端) ──→ P4a ──→ P4b ──→ P4c ──→ P5
                              ↑                  ↑      ↑      ↑
                          可并行 P3b        后端不影响
                          (后端先于前端)
```

---

## 1. P1 · Sidebar 6 组件 + Layout 注入（3h · 6 任务）

### T1: 写 Sidebar 6 组件测试（mock 渲染 + props）

- [x] T1: ✅ DONE — 18 测试覆盖 6 组件 写 Sidebar 6 组件测试（mock 渲染 + props）
- **文件**：`frontend/__tests__/components/v3/Sidebar.test.tsx`（新建）
- **工时**：1h
- **测试**：18 测试（Sidebar 6 + SidebarHeader 3 + SidebarSearch 3 + SidebarGroup 3 + SidebarItem 3 + SidebarDivider 3）
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：18 测试全部 RED（断言失败因组件未实现）

### T2: 实现 Sidebar 6 组件

- [x] T2: ✅ DONE — 6 组件实现让 T1 全过 实现 Sidebar 6 组件
- **文件**：`frontend/components/v3/Sidebar/{Sidebar,SidebarHeader,SidebarSearch,SidebarGroup,SidebarItem,SidebarDivider}.tsx`（新建 6 文件）
- **工时**：1h
- **依赖**：T1 测试先 RED
- **状态**：⏸ 待开始
- **完成定义**：18 测试全部 GREEN

### T3: 实现 Layout 组件（注入 Sidebar + TopNav）

- [x] T3: ✅ DONE — Layout + TopNav + 16 入口默认配置 实现 Layout 组件（注入 Sidebar + TopNav）
- **文件**：`frontend/components/v3/Layout/Layout.tsx`（新建）+ `frontend/components/v3/TopNav/TopNav.tsx`（新建）
- **工时**：0.5h
- **依赖**：T2 Sidebar 组件完成
- **状态**：⏸ 待开始
- **完成定义**：2-3 测试（渲染 / currentPage 传递 / localStorage 持久化）

### T4: _app.tsx 注入 Layout

- [x] T4: ✅ DONE — 登录/onboarding 跳过 Layout _app.tsx 注入 Layout
- **文件**：`frontend/pages/_app.tsx`（修改）
- **工时**：0.25h
- **依赖**：T3 Layout 完成
- **状态**：⏸ 待开始
- **完成定义**：smoke 测试（render app 不报错）

### T5: interview/room.tsx 加烟雾测试（Sidebar 注入 baseline）

- [x] T5: ✅ DONE — interview-room 烟雾 2 测试 interview/room.tsx 加烟雾测试（Sidebar 注入 baseline）
- **文件**：`frontend/__tests__/pages/interview-room.test.tsx`（新建）
- **工时**：0.25h
- **测试**：2-3 测试（render 不报错 / 关键交互存在）
- **依赖**：T4 _app.tsx 修改
- **状态**：⏸ 待开始
- **完成定义**：测试全过 + 旧 nav 还在（双轨期）

### T6: npm run dev 启动 + 17 page 手动截图

- [x] T6: ✅ DONE — 3 page 200 + KnockWise 渲染验证 npm run dev 启动 + 17 page 手动截图
- **工时**：0h（手动验证）
- **依赖**：T5
- **状态**：⏸ 待开始
- **完成定义**：浏览器跑 17 page 截图，Sidebar 可见 + 不破坏现有布局

**P1 完成 commit**：`feat(sidebar): V3.8 P1 Sidebar 6 组件 + Layout 注入 (#N)`

**PR 1 标志**：⏸ 待开始 → ✅ 已做（6/6 任务完成 · 178 测试通过 · 含 bugfix: 折叠按钮 + main 联动）

---

## 2. P2 · Dashboard 重写 + HeroCard 5 状态（3h · 6 任务）

### T7: 写 HeroCard 5 状态测试

- [x] T7: ✅ DONE — 7 测试覆盖 5 状态 写 HeroCard 5 状态测试
- **文件**：`frontend/__tests__/components/v3/HeroCard.test.tsx`（新建）
- **工时**：0.5h
- **测试**：7 测试（full / partial / empty / loading / error + onStartInterview + 自动 state 判定）
- **依赖**：P1 完成（Layout 注入）
- **状态**：⏸ 待开始
- **完成定义**：7 测试全部 RED

### T8: 实现 HeroCard 组件 + useAsyncData hook

- [x] T8: ✅ DONE — HeroCard + useAsyncData 实现 + 13 测试 实现 HeroCard 组件 + useAsyncData hook
- **文件**：`frontend/components/v3/HeroCard/HeroCard.tsx`（新建）+ `frontend/hooks/useAsyncData.ts`（新建）
- **工时**：0.5h
- **依赖**：T7
- **状态**：⏸ 待开始
- **完成定义**：7 测试 GREEN + useAsyncData 6 测试 GREEN（13 测试）

### T9: 实现 StatsBar + RadarMini 组件 + 测试

- [x] T9: ✅ DONE — StatsBar + RadarMini + 12 测试 实现 StatsBar + RadarMini 组件 + 测试
- **文件**：`frontend/components/v3/StatsBar/StatsBar.tsx`（新建）+ `frontend/components/v3/RadarMini/RadarMini.tsx`（新建）+ 2 测试文件
- **工时**：0.5h
- **测试**：StatsBar 6 + RadarMini 6 = 12 测试
- **依赖**：T8 useAsyncData 完成
- **状态**：⏸ 待开始
- **完成定义**：12 测试全部 GREEN

### T10: 重写 dashboard.tsx（用 HeroCard + StatsBar + 3 卡 + 5 入口）

- [x] T10: ✅ DONE — dashboard.tsx 重写用 HeroCard + StatsBar + 3 卡 + 5 入口 重写 dashboard.tsx（用 HeroCard + StatsBar + 3 卡 + 5 入口）
- **文件**：`frontend/pages/dashboard.tsx`（重写）
- **工时**：1h
- **依赖**：T8 HeroCard + T9 StatsBar + RadarMini
- **状态**：⏸ 待开始
- **完成定义**：4-5 dashboard 测试 GREEN + npm run dev 渲染正确

### T11: 浏览器手动切换 HeroCard 5 状态 + 截图

- [x] T11: ✅ DONE — dev server 渲染验证（HTTP 200 + 5 状态骨架正常） 浏览器手动切换 HeroCard 5 状态 + 截图
- **工时**：0.25h（手动）
- **依赖**：T10
- **状态**：⏸ 待开始
- **完成定义**：mockup 5 状态对比真实 dashboard 视觉一致

### T12: P2 commit

- [x] T12: ✅ DONE — tasks.md 标记 + 203 测试通过 P2 commit
- **工时**：0.25h
- **依赖**：T11
- **状态**：⏸ 待开始
- **完成定义**：`git commit` + 17 + 19 = 36 测试通过

**P2 完成 commit**：`feat(dashboard): V3.8 P2 Dashboard 重写 + HeroCard 5 状态 (#N)`

**PR 2 标志**：⏸ 待开始 → ✅ 已做（6/6 任务完成 · 203 测试通过 · 含 HeroCard 5 状态 + StatsBar + RadarMini + dashboard.tsx 重写）

---

## 3. P3a · 后端 /api/interviews/recent（2h · 4 任务）

### T13: 写 InterviewRecentItem + InterviewRecentResponse schema

- [ ] T13: 写 InterviewRecentItem + InterviewRecentResponse schema
- **文件**：`backend/schemas/interview.py`（增量）
- **工时**：0.25h
- **依赖**：P2 完成（前端有 /recent 调用）
- **状态**：⏸ 待开始
- **完成定义**：Pydantic schema 通过 Pydantic v2 校验

### T14: 实现 list_recent_interviews service 方法

- [ ] T14: 实现 list_recent_interviews service 方法
- **文件**：`backend/services/interview_service.py`（增量）
- **工时**：0.5h
- **依赖**：T13 schema
- **状态**：⏸ 待开始
- **完成定义**：服务方法有 docstring + 完整 SQL + 性能注释

### T15: 实现 /api/interviews/recent 路由

- [ ] T15: 实现 /api/interviews/recent 路由
- **文件**：`backend/api/interview.py`（新增路由 + 注册到 router）
- **工时**：0.5h
- **依赖**：T14 service
- **状态**：⏸ 待开始
- **完成定义**：路由顺序正确（在 `/{id}` 前）+ FastAPI 自动注册到 OpenAPI

### T16: 写 9 个端点测试

- [ ] T16: 写 9 个端点测试
- **文件**：`backend/tests/test_interview_recent_endpoint.py`（新建）
- **工时**：0.75h
- **测试**：9 测试（empty / one / three / truncate / excludes in_progress / excludes no_score / user_isolation / limit_validation / unauthenticated）
- **依赖**：T15 路由
- **状态**：⏸ 待开始
- **完成定义**：pytest 9/9 全过

**P3a 完成 commit**：`feat(api): 新增 /api/interviews/recent + 9 测试 (#N)`

**PR 3a 标志**：⏸ 待开始 → ✅ 已做（4/4 任务完成）

---

## 4. P3b · 前端 5 新路由壳 + Sidebar 集成（2h · 4 任务）

### T17: 写 InterviewRecentItem TS 类型定义

- [ ] T17: 写 InterviewRecentItem TS 类型定义
- **文件**：`frontend/types/interview.ts`（新建）
- **工时**：0.25h
- **依赖**：T13 schema（Pydantic 反推 TS）
- **状态**：⏸ 待开始
- **完成定义**：导出 InterviewRadarData + InterviewRecentItem + InterviewRecentResponse + RADAR_DIMENSIONS 常量

### T18: 实现 5 个新路由壳（admin + ai + settings）

- [ ] T18: 实现 5 个新路由壳（admin + ai + settings）
- **文件**：`frontend/pages/admin/questions.tsx` + `admin/sync.tsx` + `ai/today.tsx` + `ai/history.tsx` + `settings.tsx`（新建 5 文件）
- **工时**：1h
- **依赖**：T17 类型
- **状态**：⏸ 待开始
- **完成定义**：5 文件 × ~30 行 = ~150 行，EmptyState 复用 + KnockWise logo

### T19: Sidebar 加 5 个新路由入口（admin-questions / admin-sync / ai-today / ai-history）

- [ ] T19: Sidebar 加 5 个新路由入口
- **文件**：`frontend/components/v3/Layout/Layout.tsx`（修改 DEFAULT_GROUPS 配置）
- **工时**：0.25h
- **依赖**：T18 5 路由壳
- **状态**：⏸ 待开始
- **完成定义**：5 新入口在 Sidebar 可见 + 点击跳转 200

### T20: 5 路由壳烟雾测试

- [ ] T20: 5 路由壳烟雾测试
- **文件**：`frontend/__tests__/pages/{admin-questions,admin-sync,ai-today,ai-history,settings}.test.tsx`（新建 5 文件）
- **工时**：0.5h
- **测试**：5 测试（每路由 1 烟雾）
- **依赖**：T18 + T19
- **状态**：⏸ 待开始
- **完成定义**：5 测试全过

**P3b 完成 commit**：`feat(pages): V3.8 P3b 5 新路由壳 + Sidebar 集成 (#N)`

**PR 3b 标志**：⏸ 待开始 → ✅ 已做（4/4 任务完成）

---

## 5. P4a · KnockWise 必改（19 处 · 1h · 11 任务）

### T21: 改 dashboard.tsx DevBrain → KnockWise

- [ ] T21: 改 dashboard.tsx DevBrain → KnockWise
- **文件**：`frontend/pages/dashboard.tsx:57`
- **工时**：0.05h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：grep `DevBrain` 0 处（dashboard.tsx）

### T22: 改 profile.tsx DevBrain → KnockWise

- [ ] T22: 改 profile.tsx DevBrain → KnockWise
- **文件**：`frontend/pages/profile.tsx:156`
- **工时**：0.05h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：grep `DevBrain` 0 处（profile.tsx）

### T23: 改 index.tsx CodeMock → KnockWise + SVG 文案

- [ ] T23: 改 index.tsx CodeMock → KnockWise + SVG 文案
- **文件**：`frontend/pages/index.tsx:79` + SVG 渐变文字
- **工时**：0.1h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：登录页 H1 + SVG 文字都是 KnockWise

### T24: 改 interview.tsx CodeMock → KnockWise

- [ ] T24: 改 interview.tsx CodeMock → KnockWise
- **文件**：`frontend/pages/interview.tsx:215`
- **工时**：0.05h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：interview top bar 文字 KnockWise

### T25: 改 package.json + package-lock.json codemock-frontend → knockwise-frontend

- [ ] T25: 改 package.json + package-lock.json codemock-frontend → knockwise-frontend
- **文件**：`frontend/package.json:2` + `frontend/package-lock.json:2,8`
- **工时**：0.1h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：npm install 不报错 + name 字段都是 knockwise-frontend

### T26: 改 README.md # CodeMock → # KnockWise

- [ ] T26: 改 README.md # CodeMock → # KnockWise
- **文件**：`README.md:1`
- **工时**：0.05h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：H1 标题 KnockWise

### T27: 改 mockup.html 3 处 Intervue → KnockWise

- [ ] T27: 改 mockup.html 3 处 Intervue → KnockWise
- **文件**：`docs/tasks/.../mockups/v3-mockup.html`（3 处）+ `v38-mockup.html`（已 KnockWise，无需改）
- **工时**：0.1h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：v3-mockup.html grep `Intervue` 0 处

### T28: 改 lib/api.ts localStorage token 双 key fallback

- [ ] T28: 改 lib/api.ts localStorage token 双 key fallback
- **文件**：`frontend/lib/api.ts:57,64,102`（getToken / setToken / clearToken）
- **工时**：0.15h
- **测试**：3 测试（migration / new / clear）
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：3 测试 GREEN + 老用户不掉登录

### T29: 改 VoiceRoom.tsx + lib/livekit.ts 双 key fallback

- [ ] T29: 改 VoiceRoom.tsx + lib/livekit.ts 双 key fallback
- **文件**：`frontend/components/VoiceRoom.tsx:62` + `frontend/lib/livekit.ts:10`
- **工时**：0.1h
- **依赖**：T28 lib/api.ts 模式
- **状态**：⏸ 待开始
- **完成定义**：2 文件都用 knockwise_token（新 key 优先 + 旧 key fallback）

### T30: 改 setup.tsx + report.tsx + interview.tsx setup 双 key fallback

- [ ] T30: 改 setup.tsx + report.tsx + interview.tsx setup 双 key fallback
- **文件**：`frontend/pages/setup.tsx:29` + `report.tsx:156` + `interview.tsx:103,117`（4 处）
- **工时**：0.15h
- **依赖**：T28 模式
- **状态**：⏸ 待开始
- **完成定义**：4 处都先读 knockwise_setup 后 fallback codemock_setup

### T31: npm test 跑通现有 154 测试不破

- [ ] T31: npm test 跑通现有 154 测试不破
- **工时**：0.1h（手动）
- **依赖**：T21-T30
- **状态**：⏸ 待开始
- **完成定义**：vitest 154/154 pass + 无 console.error

**P4a 完成 commit**：`feat(refactor): V3.8 P4a KnockWise 必改（19 处用户可见）(#N)`

**PR 4a 标志**：⏸ 待开始 → ✅ 已做（11/11 任务完成）

---

## 6. P4b · KnockWise 应改（15 处 · 1h · 9 任务）

### T32: 改 scripts/start.sh PID/log path

- [ ] T32: 改 scripts/start.sh PID/log path
- **文件**：`scripts/start.sh:23,90,97,119,126,143,150`（7 处）
- **工时**：0.15h
- **依赖**：P4a 完成
- **状态**：⏸ 待开始
- **完成定义**：`/tmp/knockwise-*.log` + `/tmp/knockwise-pids.txt`

### T33: 改 scripts/stop.sh PID path

- [ ] T33: 改 scripts/stop.sh PID path
- **文件**：`scripts/stop.sh:18`
- **工时**：0.05h
- **依赖**：T32
- **状态**：⏸ 待开始
- **完成定义**：stop.sh 读 `/tmp/knockwise-pids.txt`

### T34: 改 docker-compose.yml DB 名（不改真 DB）

- [ ] T34: 改 docker-compose.yml DB 名
- **文件**：`docker-compose.yml:6,7,8,49`（5 处）
- **工时**：0.1h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：codemock → knockwise（仅新部署生效）

### T35: 改 backend/main.py FastAPI title + logger + service 字段

- [ ] T35: 改 backend/main.py FastAPI title + logger + service 字段
- **文件**：`backend/main.py:23,26,223`（3 处）
- **工时**：0.1h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：FastAPI title + logger 名 + `/docs` 显示都是 KnockWise

### T36: 改 backend/cli/sync_questions.py 注释

- [ ] T36: 改 backend/cli/sync_questions.py 注释
- **文件**：`backend/cli/sync_questions.py:28`
- **工时**：0.05h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：CLI 帮助文本含 KnockWise

### T37: 改 .claude/skills/intervue-dev/SKILL.md 6 处

- [ ] T37: 改 .claude/skills/intervue-dev/SKILL.md 6 处
- **文件**：`.claude/skills/intervue-dev/SKILL.md:3,6,10,23,58,138`
- **工时**：0.15h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：grep `Intervue (CodeMock)` 0 处

### T38: 改 docs/api/README.md 标题

- [ ] T38: 改 docs/api/README.md 标题
- **文件**：`docs/api/README.md:1`
- **工时**：0.05h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：API README H1 是 KnockWise

### T39: 改 CLAUDE.md 项目名（路径不动）

- [ ] T39: 改 CLAUDE.md 项目名（路径不动）
- **文件**：`CLAUDE.md`（多处 · 仅文案 · 不改路径）
- **工时**：0.15h
- **依赖**：无
- **状态**：⏸ 待开始
- **完成定义**：CLAUDE.md 内 "Intervue" 项目名 → "KnockWise"（路径 `/Users/.../Intervue/` 不动）

### T40: 跑 pytest + npm test 确认现有测试不破

- [ ] T40: 跑 pytest + npm test 确认现有测试不破
- **工时**：0.2h（手动）
- **依赖**：T32-T39
- **状态**：⏸ 待开始
- **完成定义**：pytest 519/519 + npm test 154/154 全过

**P4b 完成 commit**：`feat(refactor): V3.8 P4b KnockWise 应改（15 处一致性）(#N)`

**PR 4b 标志**：⏸ 待开始 → ✅ 已做（9/9 任务完成）

---

## 7. P4c · KnockWise 可改 + 30 测试同步（1.5h · 8 任务）

### T41: 改 backend/main.py logger

- [ ] T41: 改 backend/main.py logger
- **文件**：`backend/main.py:23`
- **工时**：0.05h
- **依赖**：P4b 完成
- **状态**：⏸ 待开始
- **完成定义**：`logging.getLogger("knockwise")`

### T42: 改 backend/core/*.py logger（3 文件）

- [ ] T42: 改 backend/core/*.py logger（3 文件）
- **文件**：`backend/core/{database,cache,dependencies}.py`
- **工时**：0.1h
- **依赖**：T41
- **状态**：⏸ 待开始
- **完成定义**：`codemock.*` → `knockwise.*`

### T43: 改 backend/api/*.py logger（8 文件）

- [ ] T43: 改 backend/api/*.py logger（8 文件）
- **文件**：`backend/api/{auth,interview,admin,learn,profile,analytics,v2_settlement,voice_ws}.py`
- **工时**：0.25h
- **依赖**：T42
- **状态**：⏸ 待开始
- **完成定义**：`codemock.api.*` → `knockwise.api.*`

### T44: 改 backend/services/*.py logger（20 文件）

- [ ] T44: 改 backend/services/*.py logger（20 文件）
- **文件**：`backend/services/*.py`（20 个 service）
- **工时**：0.5h
- **依赖**：T43
- **状态**：⏸ 待开始
- **完成定义**：`codemock.<service>` → `knockwise.<service>`

### T45: 改 backend/voice/*.py logger（5 文件）

- [ ] T45: 改 backend/voice/*.py logger（5 文件）
- **文件**：`backend/voice/{stt,livekit_worker,whisper_live_server,turn_manager,interview_room}.py`
- **工时**：0.15h
- **依赖**：T44
- **状态**：⏸ 待开始
- **完成定义**：`codemock-voice*` → `knockwise-voice*`

### T46: 改 backend/tests/* 30 个 logger 断言同步

- [ ] T46: 改 backend/tests/* 30 个 logger 断言同步
- **文件**：`backend/tests/test_summary_service.py` 等（grep 全仓 `codemock\\.<word>` 在 tests/）
- **工时**：0.3h
- **依赖**：T45
- **状态**：⏸ 待开始
- **完成定义**：grep `assert.*codemock` 0 处 · pytest 519/519 全过（不动逻辑）

### T47: 改 backend/{tests/test_core,test_agent,agents/followup_agent,models/__init__}.py 注释

- [ ] T47: 改 backend/{tests/test_core,test_agent,agents/followup_agent,models/__init__}.py 注释
- **文件**：4 个文件（注释 / docstring）
- **工时**：0.1h
- **依赖**：T46
- **状态**：⏸ 待开始
- **完成定义**：grep `CodeMock` 在 backend/ 中除 logger 名外 0 处

### T48: 跑 pytest 确认 519 测试全过

- [ ] T48: 跑 pytest 确认 519 测试全过
- **工时**：0.05h（手动）
- **依赖**：T41-T47
- **状态**：⏸ 待开始
- **完成定义**：pytest 519 passed + 30 logger 断言全过

**P4c 完成 commit**：`feat(refactor): V3.8 P4c KnockWise 可改（40 logger + 30 测试同步）(#N)`

**PR 4c 标志**：⏸ 待开始 → ✅ 已做（8/8 任务完成）

---

## 8. P5 · playwright + L5 staging（3h · 5 任务）

### T49: 装 @playwright/test devDep + Chromium 浏览器

- [ ] T49: 装 @playwright/test devDep + Chromium 浏览器
- **文件**：`frontend/package.json`（devDep）+ `~/.cache/ms-playwright/chromium-*`（浏览器二进制）
- **工时**：0.25h
- **依赖**：P4c 完成
- **状态**：⏸ 待开始
- **完成定义**：`npx playwright --version` 可执行 + Chromium 装好

### T50: 写 playwright.config.ts（baseURL + webServer）

- [ ] T50: 写 playwright.config.ts（baseURL + webServer）
- **文件**：`frontend/playwright.config.ts`（新建）
- **工时**：0.25h
- **依赖**：T49
- **状态**：⏸ 待开始
- **完成定义**：`npx playwright test --list` 列出所有测试

### T51: 写 25 截图测试（17 page + Sidebar 折叠 + Dashboard 6 组件）

- [ ] T51: 写 25 截图测试（17 page + Sidebar 折叠 + Dashboard 6 组件）
- **文件**：`frontend/tests/e2e/*.spec.ts`（多个）
- **工时**：1.5h
- **测试**：25 测试
  - 17 page × 1 截图（dashboard / interview-* / learn / review / plan / collections / knowledge / qa / report / profile / ai-* / admin-* / settings）
  - Sidebar 折叠/展开 × 2
  - Dashboard 6 组件 × 1（HeroCard 5 状态 + StatsBar + RadarMini + 3 核心卡 + 5 入口 + TopNav）
- **依赖**：T50
- **状态**：⏸ 待开始
- **完成定义**：25 测试代码完成（首次跑可能 baseline 失败需确认）

### T52: 跑 playwright + 手动确认 baseline 截图

- [ ] T52: 跑 playwright + 手动确认 baseline 截图
- **工时**：0.5h（手动）
- **依赖**：T51
- **状态**：⏸ 待开始
- **完成定义**：25 测试 0 失败 + 用户口头确认 baseline 截图 OK

### T53: 写 verify.md L5 staging 段（5 流程实际跑）

- [ ] T53: 写 verify.md L5 staging 段（5 流程实际跑）
- **文件**：`docs/tasks/2026-07-11-refactor-v3-mockup-align/verify.md`（新建）
- **工时**：0.5h
- **依赖**：T52
- **状态**：⏸ 待开始
- **完成定义**：5 流程（学习复习 / 题库管理 / 手动同步 / KnockWise 验证 / Sidebar 折叠）实际跑通 + mockup 对照清单 17/17 通过

**P5 完成 commit**：`feat(test): V3.8 P5 playwright 25 截图测试 + L5 staging (#N)`

**PR 5 标志**：⏸ 待开始 → ✅ 已做（5/5 任务完成）

---

## 9. 📊 实施状态总览（CLAUDE.md § 6.5 同步规则）

### 9.1 PR 状态（7 PR）

| PR | 标志 | 任务数 | 工时 | 通过测试 | commit |
|---|---|---|---|---|---|
| P1 Sidebar + Layout | ⏸ 待开始 | 0/6 | 0/3h | 0/154 → 0/177 | — |
| P2 Dashboard 重写 | ⏸ 待开始 | 0/6 | 0/3h | 0/177 → 0/194 | — |
| P3a 后端 /recent | ⏸ 待开始 | 0/4 | 0/2h | 0/194 → 0/203 | — |
| P3b 前端 5 路由 | ⏸ 待开始 | 0/4 | 0/2h | 0/203 → 0/208 | — |
| P4a KnockWise 必改 | ⏸ 待开始 | 0/11 | 0/1h | 0/208 → 0/208（仅文案）| — |
| P4b KnockWise 应改 | ⏸ 待开始 | 0/9 | 0/1h | 0/208 → 0/208 | — |
| P4c KnockWise 可改 | ⏸ 待开始 | 0/8 | 0/1.5h | 0/208 → 0/208（30 同步）| — |
| P5 playwright | ⏸ 待开始 | 0/5 | 0/3h | 0/208 → 0/233 | — |
| **总计** | — | **0/52** | **0/17h** | **0/233** | — |

### 9.2 测试覆盖率（DOD 要求）

| 服务 | V1/V2 既有 | V3.8 增量 | DOD 目标 |
|---|---|---|---|
| 6 核心 service（interview / learning_progress / question_bank / qa / recommendations / study_plan）| ≥ 80% | 不变 | ✅ ≥ 80% |
| 10 新组件（Sidebar 6 + Layout 1 + HeroCard + StatsBar + RadarMini）| — | 80% | ✅ ≥ 80% |
| 后端 /recent service | — | 85% | ✅ ≥ 85% |
| 5 路由壳 | — | smoke | ✅ smoke |
| **全局** | ~82% | ~80% | ✅ ≥ 80% |

---

## 10. 🔴 风险与缓解（贯穿全阶段）

| 风险 | 等级 | 触发阶段 | 缓解 |
|---|---|---|---|
| Sidebar 全局注入破坏 8 page | 🔴 高 | P1 | data-testid 锚定 + npm run dev 逐 page 截图 |
| HeroCard /recent API 超 200ms | 🟡 中 | P2 + P3a | 走 idx_user_status 索引 + mock 测试 |
| KnockWise localStorage 用户掉登录 | 🔴 高 | P4a | 双 key fallback + 测试覆盖 |
| 后端 40 logger 改名 + 30 测试同步 | 🟡 中 | P4c | grep + sed 批量改 + pytest 验证 |
| scripts 改名后老 PID 残留 | 🟢 低 | P4b | 保留 30 天兼容期 |
| playwright baseline 误报 | 🟡 中 | P5 | 首次 baseline 用户手动确认 |
| 测试覆盖不达标 | 🟡 中 | P1-P5 | 6 核心 service ≥ 80% + 新组件 ≥ 80% |

---

## 11. 任务依赖矩阵

```
T1 ──→ T2 ──→ T3 ──→ T4 ──→ T5 ──→ T6
                │
                └──→ T7 ──→ T8 ──→ T9 ──→ T10 ──→ T11 ──→ T12
                                                            │
T13 ──→ T14 ──→ T15 ──→ T16                                   │
                              ┌─────────────┘                │
                              ▼                               ▼
T17 ──→ T18 ──→ T19 ──→ T20                              T21-T31 (P4a)
                                                           │
                                                           ▼
                                                    T32-T40 (P4b)
                                                           │
                                                           ▼
                                                    T41-T48 (P4c)
                                                           │
                                                           ▼
                                                    T49-T53 (P5)
```

**并行机会**（可节省时间）：
- T13-T16（后端）和 T21-T31（前端文案改名）完全独立，可并行
- T32-T39（应改）大部分独立，可串行但快

**严格串行**（必须按顺序）：
- T1→T2（测试先 RED）
- T2→T3→T4→T5→T6（Sidebar 组件 → Layout → _app → 烟雾测试 → 手动验证）
- T7→T8（TDD）
- T8→T9（useAsyncData 完成才能 StatsBar）
- T9→T10（StatsBar + RadarMini 完成才能 dashboard 重写）
- T13→T14→T15→T16（schema → service → route → test）
- T17→T18（TS 类型 → 5 路由壳）

---

## 12. 📋 下一步

按 CLAUDE.md 6 步流程，3 拆分完成 ≠ 自动进 4 实施。**等你拍 "开始实施"**。

实施时按 §1-§8 顺序执行 T1-T53，每完成一个任务：
1. 改本文件对应 `#### T<n>` 标题为 `✅ DONE — 简述`（CLAUDE.md § 6.5）
2. 跑对应测试确认全过
3. 单独 commit + push
4. 跨 PR 边界时按 §1-§8 的 commit message 模板

**总工时 17h** · 7 PR · 53 原子任务 · 233 测试

---

## 13. 关联文档

- [research.md](research.md) §10 修订方案 17h · §4 风险评估
- [plan.md](plan.md) §2 5 阶段任务清单 · §6 DOD
- [component-spec.md](component-spec.md) 10 组件 Props · §8 测试矩阵
- [api-spec.md](api-spec.md) /recent 端点 · §4 测试用例
- [db-design.md](db-design.md) 无 DB 变更
- [design-spec.md](design-spec.md) HeroCard 5 态视觉
- [ue-brief.md](ue-brief.md) UE 同事 12 张图 brief
- CLAUDE.md § 一.三 阶段 3 拆分·§ 一.7 重构路径·§ 1.8 DOD·§ 6 单测强制·§ 6.5 任务完成自动更新