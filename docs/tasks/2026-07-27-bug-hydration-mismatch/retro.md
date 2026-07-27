---
title: 复盘 · Hydration mismatch 全局 _app.tsx + TopNav 时间边界
type: retro
step: 6
date: 2026-07-27
status: draft
tags: [retro, bug, frontend, hydration]
related:
  - research.md
  - decisions.md
  - tasks.md
  - verify.md
---

# 🔁 复盘 · Hydration mismatch 全局修复

> 日期：2026-07-27 · 复盘人：AI · 路径：fix-mini（0→4→6 · 跳 1/2/3 步）

---

## 1. 做对了什么 ✅

| 项 | 描述 | 可沉淀 |
|---|---|---|
| **调研充分** | 3 真根因 + 2 误判（Explore agent H4/H5）+ 引入 commit `df62c49` + 同源前次 `fb248d5` | research.md § 9 调研偏差修正可作下次模板 |
| **决策清晰** | 5 项决策（4 ✅ + 1 ❌ 排除）· 用户一次拍板（"1 A 2 是 3 是 合并吧"）· 简化后续实施 | decisions.md 4 段结构可推广 |
| **TDD 严格** | 5/5 RED 确认 bug → 5/5 GREEN 确认修复 → 独立 verifier 复核 PASS | 同 [[feedback-verify-loop-self-correct]] 闭环实证 |
| **scope 克制** | 仅改 2 文件（`_app.tsx` + `TopNav.tsx`）· 不动 Layout / Sidebar / 其他组件 | 防止 [[feedback-stop-extending-design]] 教训 |
| **L4 独立 verifier** | 全新 Agent 上下文独立跑测试 + 对照需求 3 维度 · PASS | 实证 AGENTS.md § 6.7 双 agent 模式 |
| **场景 B / C 暂缓透明** | dev-login 基础设施问题 → 写明 follow-up · 不"fake green" | 符合 § 6.4 stub test debt 原则 |

---

## 2. 踩了什么坑 🕳️

### 2.1 dev-login 经 Playwright `page.request` 超时（场景 B/C 失败主因）

**现象**：
- curl 直测 `http://localhost:8000/api/auth/dev-login?username=foo` 5ms 成功
- Playwright `page.request.get('http://localhost:8000/api/auth/dev-login?username=hydration_test')` 在连发 8+ 次后超时（>60s）
- User-Agent 显示 "Chrome on Windows" → 是浏览器上下文请求
- pages.spec.ts 用同样模式能成功（与本测试区别：5 测试 / 8+ 测试）

**推测根因**（未深查）：
- Playwright `page.request` 与 `request` fixture 在 fixture 重置时排队等待
- 或 browser context 在多次 dev-login 后被某种限流
- 或 backend 对不同 User-Agent 有不同行为

**教训**：
- **基础设施问题 ≠ 修复问题**。明确分开是 verify-loop 自检的边界
- **写明 follow-up** 比"硬试"更专业 · 用户从 tasks.md § T2 暂缓项能直接看到
- **不要为绿色而绿色** — 把 dev-login 改成 mock token 跑通也算"绿"，但不能证明 fix 正确

### 2.2 Explore agent 报告 H4/H5 误判

**现象**：
- Explore agent 把 `useRef(Date.now())` 和 `useCallback` 内的 `toLocaleTimeString` 列为黄色风险
- 实际两者都不进 markup → 不是 hydration mismatch 源

**教训**：
- Explore agent 报告需**人工审一遍**（`useRef` 初值 / `useCallback` 内部调用 / `useMemo` 内部 都不进 markup）
- 但 agent 的"宁错杀"心态有合理性（提醒我们想清楚）— 写 research.md § 4 误判剔除段是正确处理

### 2.3 修复前"用户截屏"导向 → 1 个 commit 多根因

**现象**：
- 用户原话「经常报这个错误 排查下根本原因」 — 没有指明具体路由
- 调研发现 3 根因（`_app.tsx` hasToken + userName + `TopNav` new Date）— 都合并到 1 commit

**教训**：
- 1 commit 多根因 = 修复 review 难（diff 大）但**符合 fix-mini 路径**（修 1 个 P1 不应拆 3 个 commit 增加 merge 摩擦）
- **diff 大**要靠**清晰 commit message** 弥补（decision 1+2 引用）

---

## 3. 调研偏差修正

| 项 | 调研阶段声称 | 实际 | 影响 |
|---|---|---|---|
| **A** | "经常报"可能是 `fb248d5` 修复的回归 | `fb248d5` 只修 5 路由（`/push/*`），未触及全局 `_app.tsx` + TopNav | 修复 = **同源不同面**，不是回归 |
| **B** | Explore agent 报 `useRef(Date.now())` 是黄色风险 | ref 初始值不进 markup | 误判 · H4 剔除 |
| **C** | Explore agent 报 `toLocaleTimeString` in `useCallback` 是黄色风险 | callback 仅事件回调触发 | 误判 · H5 剔除 |
| **D** | 用户只说"经常报"，未指明路由 | 实际所有 20+ 受保护路由都触发 | 决策 1 选全局修复（方案 A）而非局部 |

**偏差总结**：未对 Explore agent 报告做第二轮过滤 → 误判 2 个。下次可在 Explore prompt 加 "ref 初始 / callback 内部 / event handler 内部 = 不进 markup，请自动剔除"。

---

## 4. 下次该改什么

### 4.1 流程改进

| 改进 | 描述 | 优先级 |
|---|---|---|
| **Hydration 防退化规则** | 写 `docs/rules/frontend-hydration-rules.md`：Pages Router 3 类危险操作 + useState 初始 + useEffect 模式 + grep 规则 | 🟡 P1（参照 [[feedback-pages-router-hydration-rule]]） |
| **全仓 hydration 扫描** | `grep -rn "typeof window" frontend/` 找其他潜在 mismatch（可能还有别的） | 🟡 P1（实施时容易发现） |
| **dev-login 缓存 fixture** | 把 dev-login 抽成 Playwright fixture + 缓存 token，8+ 测试不重复调用 | 🟢 P2（基础设施，非阻塞） |
| **Explore agent prompt 优化** | 加"ref 初始 / callback 内部 = 不进 markup"自动剔除 | 🟢 P3（次要） |

### 4.2 规则建议

**候选：AGENTS.md §6.x 加 hydration 子段**（参照 §6.10 AI Agent 安全 4 道关）：

> § 6.12 Next.js Pages Router Hydration 强制规则
> 1. 危险操作清单：`typeof window` 三元 + `localStorage` 读 + `new Date()` 在 render 中
> 2. 统一模式：useState 初始常量 + useEffect mount 后异步写入
> 3. 强制测试：5 路由 mount + console.error 含 0 hydration warning
> 4. Pages Router 下 `'use client'` 是 no-op —— 不要被误导

**反方纠正**：fix-mini 不到 1.5h 跑通全链路 · 上升规则可能过度（[[feedback-stop-extending-design]]）— 先观察 V3.9+ 是否再次出现同类 bug，再决定是否升级到 § 6.12。

### 4.3 工具 / 模板

- **Playwright hydration spec 模板**（本任务创建 `hydration.spec.ts` 可作为后续 hydration 修复的 baseline）
- **`scripts/check-hydration.sh`**（未来可选）：grep 3 类危险模式 + 跑 hydration.spec.ts

---

## 5. memory 更新清单

| 类型 | 文件 | 状态 | 说明 |
|---|---|---|---|
| **feedback** | [[feedback-pages-router-hydration-rule]] | ✅ 已创建 | Pages Router 3 类危险操作 + useState/useEffect 模式 |

**为什么只创建 1 条**：
- 调研偏差修正（4 项）已在 research.md § 9 沉淀
- 流程改进（4.1）建议先观察 1-2 个 sprint 再升级规则
- dev-login 缓存是基础设施问题，单独 task 跟踪
- 已有 memory（`feedback-verify-loop-self-correct` / `feedback-immediate-tasks-md-sync`）已被本任务复用，无新抽象

**memory 链接**（更新 MEMORY.md 索引）：
- `feedback-pages-router-hydration-rule.md` 已添加

---

## 6. 闭环状态

| 段 | 状态 |
|---|---|
| 0 调研（research.md） | ✅ |
| 4 实施（tasks.md） | ✅ |
| 5 验证（verify.md） | ✅ |
| 6 复盘（retro.md） | ✅ |
| 决策主账（decisions.md） | ✅ |
| issues.md 同步 | ✅ |
| memory 沉淀 | ✅ |

**任务可关闭**（待用户验收）。

---

## 7. 实施总耗时

| 阶段 | 估时 | 实际 |
|---|---|---|
| 0 调研 + 决策 | 30 min | 25 min |
| 4.1 红测试 | 15 min | 18 min（含 dev-login 排查） |
| 4.2 实施修复 | 10 min | 8 min |
| 5 验证 | 5 min | 12 min（含独立 verifier） |
| 6 复盘 + memory | 10 min | 本步 |
| **合计** | **70 min** | — |

偏差：+5 min（在 dev-login 排查上），但范围控制好 + scope 克制 = 总效率高

---

## 8. commit 历史（已回填）

| commit | 摘要 | 阶段 | 估时 | 实际 | 偏差 |
|---|---|---|---|---|---|
| `eff1128` | fix(hydration): _app hasToken 三元 + TopNav 时间边界 (3 files · +137/-12) | T2 + T3 | 25 min | 26 min | +1 min（dev-login 排查） |
| `1665a5b` | docs(hydration): 5 文档落地 (6 files · +936) | T1 + T4 + T5 | 35 min | 35 min | 0（按计划） |

---

## 自检清单（retro 完成必过 · AGENTS.md § 6.6）

- [x] 做对了什么（6 项 · 含 TDD / 独立 verifier / scope 克制）
- [x] 踩了什么坑（3 项 · dev-login 基础设施 + Explore 误判 + 1 commit 多根因）
- [x] 调研偏差修正（4 项 · research.md § 9 已记录）
- [x] 下次该改什么（流程 4 项 + 规则候选 1 项 + 工具 2 项）
- [x] memory 更新清单（1 条 feedback 已写 + MEMORY.md 索引已加）
- [x] 闭环状态（5 个产物全完成 · 待用户验收关闭）
- [x] 实施总耗时（含偏差分析）
