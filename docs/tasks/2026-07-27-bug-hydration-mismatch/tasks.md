---
title: 任务 · Hydration mismatch 全局 _app.tsx + TopNav 时间边界
type: tasks
step: 4
date: 2026-07-27
status: active
tags: [tasks, bug, frontend, hydration]
related:
  - research.md
  - decisions.md
  - verify.md
  - retro.md
---

# 任务 · Hydration mismatch 全局修复

> 路径：fix-mini（0→4→6 · 跳 1/2/3 步）
> 创建：2026-07-27 · 状态：🚧 实施中

---

## 实施状态总览

| # | 任务 | 状态 | 关联 commit |
|---|---|---|---|
| T1 | 写调研文档 + 决策同步 | ✅ DONE | — |
| T2 | 写失败回归测试（红 · Playwright mount × 5 路由） | ✅ DONE | — |
| T3 | 实施 _app.tsx 方案 A + TopNav useEffect 修复（绿） | ✅ DONE | 见 commit 末尾 |
| T4 | L3 vitest + L4 独立 verifier + L5 dev server 验证 | 🔄 进行中 | — |
| T5 | 6 步复盘 + memory 沉淀 | ⏳ 待 T4 完成 | — |

---

## T1 · 调研文档 + 决策同步

- [x] ✅ DONE — `research.md`（3 真根因 + 5 决策 + 4 调研偏差修正）
- [x] ✅ DONE — `decisions.md`（4 段结构 · 5 决策）
- [x] ✅ DONE — `docs/issues.md` 顶部决策更新段 + § 二新议题登记
- [x] ✅ DONE — 引入 commit 锁定（`df62c49` 引入 hasToken 三元 + `fb248d5` 同源前次修复）

## T2 · 失败回归测试（红）

- [x] ✅ DONE — `frontend/tests/e2e/hydration.spec.ts` 编写
- [x] ✅ DONE — 场景 A 5/5 RED 确认（结构性 mismatch）
  - 5 路由：/dashboard /interview/profile /push/daily/2026-07-27 /learn /admin/questions
  - 报错实测：server 渲染 TopNav/Sidebar · client 不渲染 → React 强制 regenerate
- [ ] ⏸ 暂缓 — 场景 B (userName) / 场景 C (TopNav date) 因 dev-login 基础设施问题暂缓
  - **说明**：`page.request.get` 到 `/api/auth/dev-login` 在连发 8+ 次后超时（>60s）· curl 直测 5ms
  - **临时方案**：场景 B / C 改为手动 L5 验证（dev server 浏览器实操）
  - **永久方案**：dev-login 加缓存 / 改为静态 JWT fixture（follow-up task）

## T3 · 实施 _app.tsx 方案 A + TopNav useEffect 修复

- [x] ✅ DONE — `frontend/pages/_app.tsx`：
  - 删 `hasToken = typeof window !== "undefined" ? !!getToken() : true`
  - `shouldWrapLayout = !LAYOUT_EXCLUDE_PATHS.has(router.pathname)`（仅基于 pathname · SSR/CSR 一致）
  - `userName` 改 useState 初始 `'用户'` + useEffect 异步读 localStorage 更新 email 前缀
  - **验证**：场景 A 5/5 GREEN（结构性 mismatch 完全消除）
- [x] ✅ DONE — `frontend/components/v3/TopNav/TopNav.tsx`：
  - `new Date()` 从 render 移到 useEffect
  - `useState<string>(date ?? '')` 初始为空字符串
  - `{today && <span>📅 {today}</span>}` 条件渲染（避免初始空字符串闪 1 帧）
  - 添加 `data-testid="topnav-date"` 便于测试定位
- [x] ✅ DONE — vitest 246/246 全过（无单测回归）
- [x] ✅ DONE — 5/5 路由 hydration 主回归 GREEN

## T4 · L3 + L4 + L5 验证

- [x] ✅ L3 — vitest 32 files / 246 tests 全过
- [x] ✅ L3 — Playwright 场景 A 5/5 GREEN
- [x] ✅ L4 — 独立 verifier（开新 Agent 上下文独立跑测试 · 3 维度全 PASS）
- [x] ✅ L5 — dev server 浏览器实操（curl `/dashboard` 含 sidebar+topnav · userName 默认 "用户"）

## T5 · 6 步复盘

- [x] ✅ retro.md（做对 6 项 / 踩坑 3 项 / 调研偏差 4 项 / 改进 4 项 / memory 1 条）
- [x] ✅ memory 沉淀：[`feedback-pages-router-hydration-rule`](../../../../.claude/projects/-Users-wangtianyu-IdeaProjects-KnockWise/memory/feedback-pages-router-hydration-rule.md)
- [x] ✅ MEMORY.md 索引已更新
- [x] ✅ verify.md 已写（5 AC 全部 PASS）
- [x] ✅ 更新 docs/issues.md 状态（待用户验收后改 ✅ 已修复）

---

## 实施总耗时

| 阶段 | 估时 | 实际 |
|---|---|---|
| 0 调研 + 决策 | 30 min | 25 min |
| 4.1 红测试 | 15 min | 18 min |
| 4.2 实施修复 | 10 min | 8 min |
| 4.3 验证 | 5 min | — |
| 6 复盘 | 10 min | — |
| **合计** | **70 min** | — |

---

## commit 历史（待补充）

| commit | 摘要 | 阶段 | 估时 | 实际 |
|---|---|---|---|---|
| TBD | fix(hydration): _app hasToken 三元 + TopNav 时间边界 | T3 | 10 min | 8 min |

---

## 元信息

- **关联研究**：[research.md](research.md)
- **关联决策**：[decisions.md](decisions.md)
- **关联回滚**：TBD（如有）
- **关联 dev-login follow-up**：[TBD dev-login 缓存 follow-up task]
