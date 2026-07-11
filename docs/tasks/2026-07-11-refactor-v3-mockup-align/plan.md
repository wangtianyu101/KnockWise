---
title: 实施计划 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [plan, 2步, 实施计划, v3-mockup-align, knockwise]
related:
  - [research.md](research.md) — 11 章节调研
  - [product-doc.md](product-doc.md) — 用户视角
  - [design-spec.md](design-spec.md) — 视觉规范
  - [spec.md](spec.md) — 技术契约
  - [db-design.md](db-design.md) — DB 变更（无）
  - [api-spec.md](api-spec.md) — API 详细
  - [component-spec.md](component-spec.md) — 组件详细
  - [ue-brief.md](ue-brief.md) — UE 同事出图清单
---

# 实施计划：KnockWise 前端对齐重构

> **作者**：AI 计划脑 · 用户决策已锁（三档全改 / 接受 17h / 进 2 计划）
> **核心原则**：业务层冻结 · 重构只换壳 · 5 阶段渐进式（CLAUDE.md "≤ 1h AI 工作量原子任务" 约束）

---

## 0. 全局架构图（CLAUDE.md §1.5 强制）

```
┌──────────────────────────────────────────────────────────────────────┐
│                   V3.8 重构 5 阶段交付路径（17h 总）                  │
│                                                                       │
│  P1 Sidebar ──→ P2 Dashboard ──→ P3 5 路由 + 后端 /recent             │
│  (3h)             (3h)             (4h)                              │
│                                    ↓                                  │
│  P5 playwright ←─ P4c logger ←─ P4b scripts ←─ P4a 必改               │
│  (3h)              (1.5h)        (1h)        (1h)                     │
│                                                                       │
│  每阶段独立 PR · 可单独 revert · 测试分阶段 · 不破坏业务              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. 方案对比（CLAUDE.md § 一.三 阶段 2 必填 · ≥ 2 个方案）

### 方案 A：渐进式 5 阶段重构（17h · ✅ 推荐）

| 维度 | 描述 |
|---|---|
| **思路** | 5 阶段独立 PR · 每阶段可单独 revert · 测试分阶段 |
| **范围** | 17 文件改 + 14 文件新建 + 30 logger 测试同步 |
| **风险** | 🟡 中（每步 commit + 测试 + 视觉确认）|
| **兼容性** | ✅ 任意阶段可停（7 阶段部署顺序全验证，spec.md §7.5）|
| **测试影响** | 现有 154 测试不破；新增 62 测试 |
| **工作量** | **17h**（P1 3h + P2 3h + P3 4h + P4a 1h + P4b 1h + P4c 1.5h + P5 3h）|

**5 阶段路径**：
```
P1 Sidebar 6 组件 + _app.tsx 注入（page nav 暂时保留）  3h
  ↓
P2 Dashboard 重写（Hero + 3 雷达 + 5 列 stats + 3 卡 + 5 入口）  3h
  ↓
P3 5 个新路由壳 + 后端 /api/interviews/recent                 4h
  ↓
P4a KnockWise 必改（4 logo + 3 package.json + README + 3 mockup + 8 localStorage） 1h
P4b KnockWise 应改（scripts PID/log + docker-compose + FastAPI title + Skill） 1h
P4c KnockWise 可改（40 logger + 30 测试同步 + 4 注释）           1.5h
  ↓
P5 playwright 装 + 25 截图测试 + 真起 next dev 比对 mockup      3h
```

### 方案 B：一次性大重构（~17h · ❌ 不推荐）

| 维度 | 描述 |
|---|---|
| **思路** | 1 个 PR 改完所有 17 + 新建 14 + 同步 30 测试 |
| **范围** | 同 A，但同 PR |
| **风险** | 🔴 高（git diff ~3000 行 · code review 困难 · merge 冲突概率高）|
| **兼容性** | ❌ 必须一次到位 |
| **测试影响** | 现有 154 测试可能大面积 break |
| **工作量** | ~17h（一次提交）|

**不推荐原因**：
1. **违反 CLAUDE.md 强制约束**："≤ 1h AI 工作量原子任务，可独立 commit"
2. **可回滚性差**：单 PR 出问题 → 整 PR revert
3. **测试分阶段失效**：所有测试一起跑，看不出哪阶段引入 regression
4. **code review 困难**：3000 行 diff 难以一次性 review

### 方案 C：最小可用（6h · 🟡 应急备选）

| 维度 | 描述 |
|---|---|
| **思路** | 只做 P1 Sidebar + P2 Dashboard 重写，其他 P3-P5 后做 |
| **范围** | 2 阶段 11h（实际估 6h，因不打 playwright 减 3h）|
| **风险** | 🟢 低（最关键 2 个改动）|
| **兼容性** | ✅ 完全兼容 |
| **测试影响** | 现有 154 测试不破；新增 27 测试（Sidebar 18 + Hero 9）|
| **工作量** | **6h** |

**适用场景**：用户拍 "先做最小可用看效果，其他后做"

### 方案对比矩阵

| 维度 | A 渐进 17h | B 一次性 17h | C 最小 6h |
|---|---|---|---|
| 单 PR 大小 | ≤ 500 行 | ~3000 行 | ≤ 500 行 |
| 回滚成本 | 单 PR | 整 PR | 单 PR |
| 测试分阶段 | ✅ 5 阶段 | ❌ 1 阶段 | ✅ 2 阶段 |
| 5 新路由可达 | ✅ | ✅ | ❌ 暂缺 |
| KnockWise 改名 | ✅ 全 | ✅ 全 | ❌ 暂缺 |
| playwright 视觉验证 | ✅ 25 截图 | ✅ 25 截图 | ❌ 暂缺 |
| 推荐 | ✅ **默认** | ❌ | 🟡 应急 |

### 推荐方案

**推荐：方案 A（渐进 17h）**

**理由**：
1. CLAUDE.md 强制约束（≤ 1h 原子任务）—— B 违反
2. 用户决策已锁（17h 路径）—— C 是应急备选
3. P1-P5 各阶段可单独 PR + 单独 revert
4. 测试分阶段（每阶段 ~10-15 测试）
5. L5 真实跑（playwright 截图 baseline = mockup）

---

## 2. 5 阶段任务清单（CLAUDE.md § 一.三 阶段 2 必填）

### P1 · Sidebar 6 组件 + _app.tsx 注入（3h）

| # | 任务 | 文件 | 工时 | 测试 |
|---|---|---|---|---|
| 1.1 | 写 Sidebar 6 组件测试（mock 渲染 + 折叠 + active + badge）| `frontend/__tests__/components/v3/Sidebar.test.tsx` | 1h | 6 组件 × 3 = 18 测试 |
| 1.2 | 写 Sidebar 6 组件实现（Sidebar / SidebarHeader / SidebarSearch / SidebarGroup / SidebarItem / SidebarDivider）| `frontend/components/v3/Sidebar/*.tsx` | 1h | （测试先红后绿）|
| 1.3 | 写 Layout 组件（注入 Sidebar + TopNav + main-content）| `frontend/components/v3/Layout/Layout.tsx` | 0.5h | 2-3 测试 |
| 1.4 | _app.tsx 加 Layout 包裹 | `frontend/pages/_app.tsx` | 0.25h | smoke |
| 1.5 | 给 interview/room.tsx 加 2-3 烟雾测试（Sidebar 注入前 baseline）| `frontend/__tests__/pages/interview-room.test.tsx` | 0.25h | 2-3 测试 |
| 1.6 | npm run dev 启动 + 浏览器逐 page 截图确认 Sidebar 不破坏 | 手动验证 | 0h | — |

**commit message**：`feat(sidebar): V3.8 P1 Sidebar 6 组件 + _app.tsx 注入 (#N)`

### P2 · Dashboard 重写 + HeroCard 5 状态（3h）

| # | 任务 | 文件 | 工时 | 测试 |
|---|---|---|---|---|
| 2.1 | 写 HeroCard 5 状态测试（full / partial / empty / loading / error）| `frontend/__tests__/components/v3/HeroCard.test.tsx` | 0.5h | 5 测试 |
| 2.2 | 写 HeroCard 组件实现（5 状态机 + useAsyncData hook）| `frontend/components/v3/HeroCard/HeroCard.tsx` | 0.5h | — |
| 2.3 | 写 StatsBar 组件 + 测试 | `frontend/components/v3/StatsBar/StatsBar.tsx` + test | 0.25h | 4 测试 |
| 2.4 | 写 RadarMini 组件 + 测试 | `frontend/components/v3/RadarMini/RadarMini.tsx` + test | 0.25h | 4 测试 |
| 2.5 | 重写 dashboard.tsx（用 HeroCard + StatsBar + 3 核心卡 + 5 入口）| `frontend/pages/dashboard.tsx` | 1h | 4-5 测试 |
| 2.6 | npm run dev 启动 + 截图 5 状态对比 mockup | 手动验证 | 0.25h | — |

**commit message**：`feat(dashboard): V3.8 P2 Dashboard 重写 + HeroCard 5 状态 (#N)`

### P3 · 5 新路由壳 + 后端 /recent（4h）

| # | 任务 | 文件 | 工时 | 测试 |
|---|---|---|---|---|
| 3.1 | 后端 InterviewRecentItem schema | `backend/schemas/interview.py` | 0.25h | — |
| 3.2 | 后端 list_recent_interviews service 方法 | `backend/services/interview_service.py` | 0.5h | — |
| 3.3 | 后端 /api/interviews/recent 端点 + 9 测试 | `backend/api/interview.py` + `backend/tests/test_interview_recent_endpoint.py` | 1h | 9 测试 |
| 3.4 | 前端 InterviewRecentItem TS type | `frontend/types/interview.ts` | 0.25h | — |
| 3.5 | 前端 5 个新路由壳（admin/questions, admin/sync, ai/today, ai/history, settings）| `frontend/pages/{admin,ai,settings}/*.tsx` | 1h | 5 烟雾测试 |
| 3.6 | Sidebar 加 5 个新路由入口 + 验证 active 态 | `frontend/components/v3/Sidebar/SidebarItem.tsx` | 0.25h | — |
| 3.7 | npm run dev 启动 + 5 路由壳 EmptyState 显示正确 | 手动验证 | 0.25h | — |

**commit message**：
- `feat(api): 新增 /api/interviews/recent (#N)`
- `feat(pages): V3.8 P3 5 新路由壳 + Sidebar 集成 (#N)`

### P4a · KnockWise 必改（1h）

| # | 任务 | 文件 | 工时 |
|---|---|---|---|
| 4a.1 | 改 dashboard.tsx DevBrain → KnockWise | `frontend/pages/dashboard.tsx:57` | 0.05h |
| 4a.2 | 改 profile.tsx DevBrain → KnockWise | `frontend/pages/profile.tsx:156` | 0.05h |
| 4a.3 | 改 index.tsx CodeMock → KnockWise + SVG 文案 | `frontend/pages/index.tsx:79` | 0.1h |
| 4a.4 | 改 interview.tsx CodeMock → KnockWise | `frontend/pages/interview.tsx:215` | 0.05h |
| 4a.5 | 改 package.json + package-lock.json codemock-frontend → knockwise-frontend | 2 文件 | 0.1h |
| 4a.6 | 改 README.md # CodeMock → # KnockWise | `README.md:1` | 0.05h |
| 4a.7 | 改 mockup.html 3 处 Intervue → KnockWise | `v3-mockup.html` 714,743,948 | 0.1h |
| 4a.8 | 改 lib/api.ts localStorage token 双 key fallback | `frontend/lib/api.ts:57,64,102` | 0.15h |
| 4a.9 | 改 VoiceRoom.tsx + lib/livekit.ts localStorage 双 key fallback | 2 文件 | 0.1h |
| 4a.10 | 改 setup.tsx + report.tsx + interview.tsx setup 双 key fallback | 3 文件 | 0.15h |
| 4a.11 | npm test 跑通现有 154 测试不破 | 手动验证 | 0.1h |

**commit message**：`feat(refactor): V3.8 P4a KnockWise 必改（19 处用户可见）(#N)`

### P4b · KnockWise 应改（1h）

| # | 任务 | 文件 | 工时 |
|---|---|---|---|
| 4b.1 | 改 scripts/start.sh PID/log path | `scripts/start.sh:23,90,97,119,126,143,150` | 0.15h |
| 4b.2 | 改 scripts/stop.sh PID path | `scripts/stop.sh:18` | 0.05h |
| 4b.3 | 改 docker-compose.yml DB 名（不改真 DB）| `docker-compose.yml:6,7,8,49` | 0.1h |
| 4b.4 | 改 backend/main.py FastAPI title + logger | `backend/main.py:23,26,223` | 0.1h |
| 4b.5 | 改 backend/cli/sync_questions.py 注释 | `backend/cli/sync_questions.py:28` | 0.05h |
| 4b.6 | 改 .claude/skills/intervue-dev/SKILL.md 6 处 | `SKILL.md` | 0.15h |
| 4b.7 | 改 docs/api/README.md 标题 | `docs/api/README.md:1` | 0.05h |
| 4b.8 | 改 CLAUDE.md 项目名（路径不动）| `CLAUDE.md` 多处 | 0.15h |
| 4b.9 | 跑 pytest + npm test 确认现有测试不破 | 手动验证 | 0.2h |

**commit message**：`feat(refactor): V3.8 P4b KnockWise 应改（15 处一致性）(#N)`

### P4c · KnockWise 可改 + 30 logger 测试同步（1.5h）

| # | 任务 | 文件 | 工时 |
|---|---|---|---|
| 4c.1 | 改 backend/main.py logger "codemock" → "knockwise" | 1 文件 | 0.05h |
| 4c.2 | 改 backend/core/{database,cache,dependencies}.py logger | 3 文件 | 0.1h |
| 4c.3 | 改 backend/api/{auth,interview,admin,learn,profile,analytics,v2_settlement,voice_ws}.py logger | 8 文件 | 0.25h |
| 4c.4 | 改 backend/services/*.py logger (20 文件) | 20 文件 | 0.5h |
| 4c.5 | 改 backend/voice/*.py logger (5 文件) | 5 文件 | 0.15h |
| 4c.6 | 改 backend/tests/* 30 个 logger 断言同步 | grep + sed | 0.3h |
| 4c.7 | 改 backend/{tests/test_core,test_agent,agents/followup_agent,models/__init__}.py 注释 | 4 文件 | 0.1h |
| 4c.8 | 跑 pytest 确认 519 测试全过 | 手动验证 | 0.05h |

**commit message**：`feat(refactor): V3.8 P4c KnockWise 可改（40 logger + 30 测试同步）(#N)`

### P5 · playwright + 真起 next dev 比对（3h）

| # | 任务 | 文件 | 工时 |
|---|---|---|---|
| 5.1 | 装 @playwright/test devDep + Chromium 浏览器 | `frontend/package.json` | 0.25h |
| 5.2 | 写 playwright.config.ts（baseURL + webServer）| `frontend/playwright.config.ts` | 0.25h |
| 5.3 | 写 25 截图测试（17 page + Sidebar 折叠 + Dashboard 6 组件）| `frontend/tests/e2e/*.spec.ts` | 1.5h |
| 5.4 | 跑 playwright + 手动确认 baseline 截图 | 手动验证 | 0.5h |
| 5.5 | 写 verify.md L5 staging 段（5 流程实际跑）| `verify.md` | 0.5h |

**commit message**：`feat(test): V3.8 P5 playwright 25 截图测试 + L5 staging (#N)`

---

## 3. 总测试数变化（CLAUDE.md § 六 单测强制）

| 阶段 | 新增测试 | 累计 |
|---|---|---|
| 现有 baseline | — | 154（既有）|
| P1 | +23（Sidebar 18 + Layout 2-3 + interview-room 2-3）| 177 |
| P2 | +17（HeroCard 5 + StatsBar 4 + RadarMini 4 + dashboard 4-5）| 194 |
| P3 | +14（后端 /recent 9 + 5 路由壳 5）| 208 |
| P4c | +30（logger 测试同步，断言改不改逻辑）| 208（断言同步不动逻辑）|
| P5 | +25（playwright 截图）| 233 |
| **总计** | **+79** | **233**（含 30 同步断言）|

---

## 4. 阶段依赖图

```
P1 (Sidebar) ──→ P2 (Dashboard 重写) ──→ P3 (5 路由 + /recent)
                                            ↓
                                       P4a (必改) ──→ P4b (应改) ──→ P4c (可改 + 30 测试同步)
                                                                          ↓
                                                                       P5 (playwright)
                                                                          ↓
                                                                       verify.md L5
```

- **P1 独立**：可单独发版（仅 Sidebar）
- **P2 依赖 P1**：Dashboard 重写需要 Layout/Sidebar 已注入（main-content margin-left 适配）
- **P3 部分依赖 P1**：5 路由壳本身可独立，但 Sidebar 加入口要 P1 完成
- **P4 依赖 P1-P3**：KnockWise 改名涉及已实施的组件
- **P5 依赖全部**：playwright 截图测试需要所有 V3.8 视觉到位

**回滚策略**：
- P1-P5 各自独立 PR → 任意阶段 revert 不影响其他
- P5 可最后做（如果时间紧，P1-P4 完成即可发版）

---

## 5. 风险预案（CLAUDE.md § 一.三 阶段 2 必填 · ≥ 2 风险点）

| 风险 | 等级 | 预案 |
|---|---|---|
| **Sidebar 全局注入破坏 8 page 布局** | 🔴 高 | P1 阶段先用 `position: fixed` 不推 main-content；逐 page 截图对比 mockup；用 `data-testid` 锚定测试内容 |
| **HeroCard /recent API 超 200ms** | 🟡 中 | 走 `idx_user_status` 索引 + mock 测试；若仍慢加 Redis 缓存 60s |
| **KnockWise localStorage 改名用户掉登录** | 🔴 高 | 双 key fallback + 监控 `/api/auth` 失败率；> 5% 自动告警 |
| **后端 40 logger 改名 + 30 测试同步** | 🟡 中 | 写脚本批量改 `codemock\.` → `knockwise.` + grep 验证；pytest 跑通 |
| **scripts 改名后老 PID 文件残留** | 🟢 低 | 保留 30 天兼容期：stop.sh 同时读老 `/tmp/intervue-pids.txt` |
| **playwright baseline 误报** | 🟡 中 | 首次 baseline 用户手动确认 25 张截图；后续阈值 0.1% |
| **5 路由壳 EmptyState 误导** | 🟢 低 | spec.md §7.3 + design-spec.md §3.8.2 已明确文案 + CTA "返回 Dashboard" |
| **测试覆盖不达标** | 🟡 中 | 6 核心 service 覆盖率 ≥ 80%（DOD · CLAUDE.md § 1.8）已通过 V2 验证；V3.8 新增组件覆盖率 ≥ 80% 写测试时锁定 |

---

## 6. DOD（阶段 4 完成定义 · CLAUDE.md § 1.8）

### 6.1 V3.8 重构完成 DOD

- [ ] P1-P5 全部 5 阶段完成 + commit
- [ ] 总测试数 ≥ 200（实际 233）
- [ ] 现有 154 测试不破
- [ ] 30 个 logger 测试断言同步完成
- [ ] playwright 25 截图测试 baseline 人工确认
- [ ] verify.md L5 staging 真起 next dev + 浏览器逐 page 比对 mockup
- [ ] 用户口头确认 "verify 完成"

### 6.2 DOD 验收清单

| 项 | 验证方法 | 通过标准 |
|---|---|---|
| Sidebar 5 大分组 + Admin | 浏览器 + playwright 截图 | 16 入口全可见 + 折叠/展开正常 |
| Dashboard HeroCard 5 状态 | 浏览器手动切换 + playwright | 5 状态视觉区分明显 |
| StatsBar 5 列 | 浏览器 | 数字对齐 + 等宽 |
| RadarMini 3 色 | 浏览器 | 粉/紫/蓝梯度正确 |
| KnockWise 品牌统一 | grep `DevBrain\|CodeMock\|Intervue` | 0 处用户可见（注释除外）|
| localStorage 迁移 | 浏览器 + 单元测试 | 双 key fallback 正常 |
| 5 路由壳 EmptyState | 浏览器 + playwright | 占位文案 + CTA 正确 |
| 后端 /recent | curl + pytest | 9 测试全过 |

### 6.3 verify.md 必含

按 CLAUDE.md § 一 L1-L5：
- L1 静态检查（pre-commit hook）· tsc + ruff 全绿
- L2 单元测试 · 233 passed
- L3 集成测试 · 5 流程实际跑
- L4 性能验证 · /recent P95 < 50ms
- L5 staging · playwright 25 截图 + 真实 next dev

---

## 7. 与 mockup 对照清单（P5 verify 用）

> 打开 mockups/v38-mockup.html + 真前端，对照以下 17 项：

| # | 项 | mockup | 真前端 | 验收 |
|---|---|---|---|---|
| 1 | KnockWise logo + 文字 | ✅ | ⏳ 待 P4a | P4a 后 |
| 2 | Sidebar 5 大分组 + Admin | ✅ | ⏳ 待 P1 | P1 后 |
| 3 | Sidebar 折叠 240/64 | ✅ | ⏳ 待 P1 | P1 后 |
| 4 | Sidebar 搜索框 | ✅ | ⏳ 待 P1 | P1 后 |
| 5 | Dashboard HeroCard full | ✅ | ⏳ 待 P2 | P2 后 |
| 6 | HeroCard partial | ✅ | ⏳ 待 P2 | P2 后 |
| 7 | HeroCard empty | ✅ | ⏳ 待 P2 | P2 后 |
| 8 | HeroCard loading | ✅ | ⏳ 待 P2 | P2 后 |
| 9 | HeroCard error | ✅ | ⏳ 待 P2 | P2 后 |
| 10 | StatsBar 5 列 | ✅ | ⏳ 待 P2 | P2 后 |
| 11 | 3 核心卡 (AI/每日/计划) | ✅ | ⏳ 待 P2 | P2 后 |
| 12 | 5 module-quick-link | ✅ | ⏳ 待 P2 | P2 后 |
| 13 | /admin/questions EmptyState | ✅ | ⏳ 待 P3 | P3 后 |
| 14 | /admin/sync EmptyState | ✅ | ⏳ 待 P3 | P3 后 |
| 15 | /ai/today EmptyState | ✅ | ⏳ 待 P3 | P3 后 |
| 16 | /ai/history EmptyState | ✅ | ⏳ 待 P3 | P3 后 |
| 17 | /settings EmptyState | ✅ | ⏳ 待 P3 | P3 后 |

---

## 8. 文件清单（V3.8 任务最终交付物）

```
docs/tasks/2026-07-11-refactor-v3-mockup-align/
├── research.md         (11 章节调研 · 17h 路径)
├── product-doc.md      (用户视角 · 4 场景 · KnockWise 品牌 brief)
├── design-spec.md      (10 章节视觉规范)
├── spec.md             (技术契约 · 架构 · 兼容矩阵 · KnockWise 迁移)
├── ue-brief.md         (12 张图 brief)
├── plan.md             (本文件 · 方案对比 · 5 阶段)
├── db-design.md        (无 DB 变更说明)
├── api-spec.md         (/recent 详细 Request/Response + 9 测试)
├── component-spec.md   (9 组件 Props 详细 + 测试矩阵)
├── mockups/
│   └── v38-mockup.html (1491 行可点击 SPA)
└── tasks.md            (5 阶段拆 30-40 原子任务 · 阶段 3 写)
```

---

## 9. 关联文档

- [research.md](research.md) §3 方案对比 · §5 推荐 · §9 补调研
- [product-doc.md](product-doc.md) 用户视角 + KnockWise 品牌 brief
- [design-spec.md](design-spec.md) 视觉规范 10 章节
- [spec.md](spec.md) 技术契约 + 兼容矩阵 + KnockWise 迁移
- [ue-brief.md](ue-brief.md) UE 同事出图清单
- CLAUDE.md § 一.三 阶段 2 必填 · § 一.7 重构路径 · § 1.8 DOD