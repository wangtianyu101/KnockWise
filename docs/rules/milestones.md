# 实施状态（milestones 流水账）

> **来源**：原 CLAUDE.md § 八.2（2026-07-17 拆出）
> **触发**：回溯历史进展 / 写 retro.md / 复盘时读

## V1 骨架完成（2026-06-27）

19 张表 + 60+ API + 19 前端页面 + 5 service（question_bank / learning_progress / qa / study_plan / recommendations）

- 详见 [`../tasks/2026-06-27-v1-closure/closure.md`](../tasks/2026-06-27-v1-closure/closure.md)
- plan.md 69 项已完成 51%（✅ 35 项 + 🟡 15 项）+ ⚪ 26% 已合理化（设计已变）+ ➖ 1%

## 测试覆盖

- 367 个测试 / 82% 覆盖 / 核心 6 service 99%（远超 DOD ≥ 80%）

## 本地启动

- 6/7 服务在线（MySQL / Redis / LiveKit / Backend / Frontend + WhisperLive 证实不需要）
- 一键脚本 `scripts/start.sh` / `stop.sh` 幂等 + 优雅关闭

## V2 智能沉淀层（2026-07-03）

3 个 service + 6 端点 + 3 前端组件全部完成

- `ProfileSettlementService`（画像沉淀）— 82% 覆盖，4 方法 + 2 触发点（learning_progress + interview）
- `ObsidianSedimentService`（Obsidian 写回）— 100% 覆盖，5 write 方法 + 容错
- `SummaryService`（AI 自动摘要）— 81% 覆盖，5 方法 + Redis TTL 1h 缓存 + LLM 降级
- 6 个 API 端点（`/api/v2/dashboard/summary` / `profile/weekly/monthly/refresh` / `knowledge/recent-sediments` / `obsidian/sync`）
- 3 个前端组件（DailySummaryCard / RecentSedimentsCard / ProfilePage + 画像 nav）
- 471 tests pass（V1: 367 + V2 新增: 104）
- 7 决策全 A（决策文档 + 反馈沉淀到 memory/feedback-sediment-plan-defaulting.md）
- 详见 [`../tasks/2026-06-28-new-feature-v2-smart-sediment/`](../tasks/2026-06-28-new-feature-v2-smart-sediment/)（verify.md / retro.md）

## V3.8 KnockWise 前端对齐重构（2026-07-11 完成）

6 阶段 PR + 实地 L5 验证全部完成

- **方案 A 渐进 5 阶段**（17h 实操 ~16h）· 每阶段独立 PR + 可单阶段 revert
- **P1 Sidebar 6 组件 + Layout 注入** — `Sidebar` / `SidebarHeader` / `SidebarSearch` / `SidebarGroup` / `SidebarItem` / `SidebarDivider` + `Layout` + `TopNav` · 23 测试（含折叠按钮 + main marginLeft 联动 bugfix）
- **P2 Dashboard 重写 + 3 组件** — `HeroCard` 5 状态 + `StatsBar` 5 列 + `RadarMini` 5 维 SVG + `useAsyncData` hook + 重写 `dashboard.tsx` · 36 测试
- **P3a 后端 `/api/interviews/recent`** — Pydantic `InterviewRecentItem` + `list_recent_interviews` service + `@router.get('/recent')` 在 `/{id}` 前注册 · 9 测试
- **P3b 前端 5 新路由壳** — `/admin/questions` `/admin/sync` `/ai/today` `/ai/history` `/settings` EmptyState 占位 · 5 测试
- **P4a KnockWise 必改** — 19 处用户可见（4 logo + 3 package.json + README + 3 mockup + 8 localStorage 双 key fallback）
- **P4b KnockWise 应改** — 15 处一致性（scripts PID/log + docker-compose + FastAPI title + SKILL + CLAUDE.md + docs/api）
- **P4c KnockWise 可改** — 40 后端 logger + 30 测试断言同步 + 5 注释
- **D 清理 docs/ 旧品牌** — 28 个 doc 文件统一为 KnockWise（archive + designs + 旧 06 task dir + 07-11 task dir）
- **Bugfix** — Sidebar 折叠按钮 / main marginLeft 联动 / Sidebar 搜索过滤 / Tailwind 4 → 3 降级
- **测试累计**：737 passed（154 V1 + V3.7 既有 + 73 P1-P3b + 9 P3a + 30 logger 同步）
- **L5 staging 实地验证**：真 dev server · 17 page HTTP 200 · KnockWise 残留 0 处 · Sidebar 5 流程跑通
- **P5 playwright 推迟**（用户拍 A）— 不阻塞 V3.8 完成 · 留作未来 regression protection
- 详见 [`../tasks/2026-07-11-refactor-v3-mockup-align/`](../tasks/2026-07-11-refactor-v3-mockup-align/)（research / product-doc / design-spec / spec / plan / tasks / verify · 11 文件）

## 后续待办（待用户决策）

详见 CLAUDE.md § 八.4 待用户决策。
