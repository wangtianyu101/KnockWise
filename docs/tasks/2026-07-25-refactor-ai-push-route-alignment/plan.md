# Plan · AI 推送路由对齐 v2 设计

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 路径模式：refactor-6（调研已完成 · 0 步见下方"调研摘要"）
> 配套：[research.md](research.md) · [tasks.md](tasks.md)

---

## 0 · 调研摘要（chat 内已完成 · 完整版见 research.md）

### 0.1 核心 gap（v2 设计 vs 实际实现）

| # | 设计 | 实际 | 优先级 |
|---|---|---|---|
| R1-R4 | `/push/{today,bookmarks,settings,sources}` | `/ai/{today,bookmarks,settings,sources}` | 🔴 P0 |
| R5 | `/push/daily/[date]`（mockup 02 · 单条详情）| 不存在（history.tsx 是另一回事）| 🔴 P0 |

### 0.2 文件清单（受影响）

```
frontend/pages/ai/today.tsx          → pages/push/index.tsx
frontend/pages/ai/bookmarks.tsx      → pages/push/bookmarks.tsx
frontend/pages/ai/settings.tsx       → pages/push/settings.tsx
frontend/pages/ai/sources.tsx        → pages/push/sources.tsx
frontend/pages/ai/history.tsx        → 保留（暂不动 · 是"历史推送"占位页 · 与 daily/[date] 不同概念）
frontend/components/v3/Layout/Layout.tsx  → sidebar /ai/* → /push/* (3 处)
frontend/hooks/useDigest.ts          → 新增 useDigestDate hook
frontend/tests/e2e/pages.spec.ts     → 更新 /ai/* → /push/*
frontend/tests/visual/digest.spec.ts  → 更新 /ai/* → /push/*
frontend/tests/e2e/a11y.spec.ts      → 更新 /ai/* → /push/*
```

### 0.3 已有 API + 工具

- ✅ `GET /api/digest/daily/{date}` 存在（`lib/api.ts:245` `getDailyDigest`）
- ✅ `lib/api.ts` 已有 `getDailyDigest(date)` 封装
- ❌ `hooks/useDigest.ts` 缺 `useDigestDate(date)` hook
- ✅ `HideDialog` 已实现可复用
- ⚠️ `types/digest.ts` 是 V3.8 旧模型（`DigestDailyItem`）vs `useDigest.ts` 是 v2 模型（`DigestItem`）—— **类型两套并存** · 本任务优先满足 v2（v2 是更新设计）

### 0.4 风险等级

| 风险 | 等级 | 缓解 |
|---|---|---|
| Sidebar 高亮失效 | 🟡 | Layout.tsx 同步改 |
| E2E/Visual test 全挂 | 🟡 | 同步改 3 个 spec 文件 |
| `/ai/*` 旧链接 404 | 🟢 | 可选 · 加 redirect 到 /push/* |
| useDigestDate 与 today 行为差异（404 时空状态）| 🟡 | hook 抛 error · page 接 error → 显示 404 EmptyState |
| mockup 02 涉及 related items · 后端是否真返回 `related_item_ids` | 🟡 | hook 类型已声明 `related_item_ids: string[]`（已存在）· 真实数据待验证 |

---

## 1 · 范围

### 1.1 本次做（P0）

| 项 | 内容 |
|---|---|
| **路由迁移** | 4 个 page · /ai/* → /push/* |
| **新增 daily detail 页** | /push/daily/[date].tsx（mockup 02 完整版）|
| **新增 useDigestDate hook** | 包装 GET /api/digest/daily/{date} |
| **更新 Layout 导航** | sidebar 3 处链接 |
| **更新测试** | 3 个 spec 文件（pages/visual/a11y）|

### 1.2 本次不做（标 ⏸ follow-up）

| 项 | 原因 |
|---|---|
| `DigestCard` 接口对齐 spec § 2.1（mode/userId/isRead/showRelated...）| 范围外 · 🟡 P1 单独排期 |
| 拆 `components/digest/<Name>/` 目录结构 | 范围外 · 🟢 P2 |
| 删除 `DailyCard.tsx` 残留组件 | 范围外 · 🟢 P2 |
| 修正 `component-spec.md § 2.1` 视觉规格（dark vs light 自相矛盾）| 范围外 · 文档维护 |
| `/ai/*` redirect 兼容 | 范围外 · 加为可选项（见方案 A/B） |

---

## 2 · 方案（路由迁移 + daily detail 实现）

### 方案 A · 直接重命名 + 旧链接 404（推荐）

```
pages/ai/today.tsx → mv pages/push/index.tsx（保留 import 不变）
pages/ai/{bookmarks,settings,sources}.tsx → mv pages/push/{...}.tsx
pages/push/daily/[date].tsx → 新建
```

**优点**：简单 · 仓库干净 · 链接直接对齐设计
**缺点**：旧 /ai/* 链接 404 · 已分享的 URL 失效

### 方案 B · 重命名 + /ai/* 永久 redirect 到 /push/*

方案 A + `next.config.ts` 或 `_app.tsx` 层加 redirect table。

**优点**：旧链接不失效
**缺点**：维护成本 · 不在 v2 设计里 · 偏离 spec

### ✅ 推荐：方案 A

理由：
1. v2 spec 明确 `/push/*` · spec 是权威主账
2. 项目用户量小 · 旧 /ai/* 链接失效影响小
3. 如有需要可后续加 B · 不阻塞本次

### daily detail 实现要点

```typescript
// pages/push/daily/[date].tsx
import { useRouter } from 'next/router';
import { useDigestDate, useAddBookmark, useRemoveBookmark, useHideItem } from '@/hooks/useDigest';
import { HideDialog } from '@/components/digest/HideDialog';

export default function DailyDetailPage() {
  const router = useRouter();
  const date = router.query.date as string;
  const { data, isLoading, error } = useDigestDate(date);
  // ... 按 mockup 02 渲染：标签 + 标题 + 摘要 + 原文来源块 + 三个按钮 + 相关历史 + HideDialog
}
```

要点：
- 标题：`# Claude 4.7 Sonnet 发布...`
- 双轴标签：[模型][国外]
- 元信息行：来源 · 时间前 · ⭐4.9 · ⏱4 分钟
- 摘要：完整 summary
- 原文来源块（📰）：source_name + URL + 发布时间
- 三个按钮：[✓ 已收藏] [📤 分享] [🔇 不再推送类似]
- 相关历史 digest 列表（3-5 条 related items · 来自 `related_item_ids`）
- HideDialog 复用 · 关联 hide 操作
- Loading: 5 个 Skeleton
- Error 404: EmptyState "当日无 digest · 返回今日"
- Error 其他: 红 banner + 重试

---

## 3 · 任务清单（见 tasks.md）

13 个 T 任务 · 5 阶段 · 总估时 ~3.5h AI

---

## 4 · 验收（DOD）

### 4.1 必跑

- [ ] `cd frontend && npm run build` 全绿
- [ ] `cd frontend && npx tsc --noEmit` 全绿（注意：当前有 10 个 type error 既有 · 本任务不引入新 error）
- [ ] `cd frontend && npm test -- --run` 全绿（vitest · 不引入新 fail）
- [ ] `cd frontend && npx playwright test e2e/digest.spec.ts` 5+ scenario 全过（含新增的 daily detail scenario）
- [ ] `curl http://localhost:3000/push` 返回 200
- [ ] `curl http://localhost:3000/push/bookmarks` 返回 200
- [ ] `curl http://localhost:3000/push/settings` 返回 200
- [ ] `curl http://localhost:3000/push/sources` 返回 200
- [ ] `curl http://localhost:3000/push/daily/2026-07-17` 返回 200
- [ ] `curl http://localhost:3000/ai/today` 返回 404（旧链接已废弃 · 符合方案 A）

### 4.2 验证清单（需观察）

- [ ] Sidebar 高亮：访问 `/push` 时"今日推荐" active
- [ ] Sidebar 高亮：访问 `/push/bookmarks` 时"我的收藏" active
- [ ] daily detail 页：相关历史列表显示 ≥ 1 条 related item（or 空状态）
- [ ] daily detail 页：点击"不再推送类似"打开 HideDialog
- [ ] daily detail 页：404 时显示空状态 + 返回今日按钮

---

## 5 · 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| type error 累计（既有 10 个 + 新增可能） | commit 前 `tsc --noEmit` 比对前后 · 不变差 |
| 旧 `/ai/*` 用户书签失效 | 后续 P1 加 redirect · 本次接受 404 |
| 相关历史 items 当前可能为空 | 页面对 0 条 related 显示"暂无相关历史" |
| mockup 02 与 v2 spec 视觉风格差异（dark glassmorphism 已成事实）| 实现按 mockup 02 · 与 today/bookmarks 风格统一 |

---

## 6 · 关联文档

- [`research.md`](research.md) — 完整调研（含历史 commit / 全文件清单）
- [`tasks.md`](tasks.md) — 13 任务 DAG
- `docs/tasks/2026-07-17-new-feature-ai-push/component-spec.md` § 1.5 Page 2 — 详情页 ASCII wireframe
- `docs/tasks/2026-07-17-new-feature-ai-push/mockups/02-daily-detail.html` — 详情页 mockup
- `docs/tasks/2026-07-17-new-feature-ai-push/api-spec.md` § 132 — daily endpoint 契约

---

## 元信息

- **路径模式**：refactor-6（路径全 6 步）
- **范围**：P0（路由 + daily detail 整页）
- **估时**：~3.5h AI（含验证）
- **commit 计划**：每 T1 commit · 13 commit 总数预期
- **回滚预案**：git revert 各 commit · 不改 DB · 不改 API