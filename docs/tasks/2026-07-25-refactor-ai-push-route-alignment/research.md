# Research · AI 推送路由对齐 v2 设计

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [tasks.md](tasks.md)
> 模板：[docs/templates/research-refactor.md](../../templates/research-refactor.md)

---

## 0 · 任务理解（自述）

用户原话："AI 推送这个板块和我最新的设计不太一样呀"。

我的理解：用户在视觉/路由层面对当前 `/ai/*` 实现不满意，要求与 v2 设计文档（`docs/tasks/2026-07-17-new-feature-ai-push/`）对齐。

## 1 · 触发与背景

| 项 | 内容 |
|---|---|
| **触发** | 用户口头反馈 |
| **关联设计** | docs/tasks/2026-07-17-new-feature-ai-push/{spec,component-spec,mockups} |
| **当前分支** | feature/v39-ci-autofix |
| **历史 commit** | 最近 fix(profile-settlement)、docs(precommit-p0-gates) 等 · 与本任务无关 |

## 2 · 现状（关键证据）

### 2.1 文件分布

```bash
$ ls frontend/pages/ai/
bookmarks.tsx history.tsx settings.tsx sources.tsx today.tsx

$ grep "/ai\b" frontend/components/v3/Layout/Layout.tsx | head
L142: { page: '/ai/today', href: '/ai/today', label: '今日推荐', icon: ICON.ai, badge: 'v3' },
L143: { page: '/ai/history', href: '/ai/history', label: '推送历史', icon: ICON.history },
L176: '/ai/today': '今日推荐',
L177: '/ai/history': '推送历史',
```

### 2.2 设计契约（v2 component-spec.md § 1）

| 路径 | 用途 | mockup |
|---|---|---|
| `/push` | 今日 digest 主入口 | `mockups/01-today.html` |
| `/push/daily/[date]` | 日报详情页 | `mockups/02-daily-detail.html` |
| `/push/bookmarks` | 我的收藏 | `mockups/03-bookmarks.html` |
| `/push/settings` | 推送设置 | `mockups/04-settings.html` |
| `/push/sources` | 信源管理 | `mockups/05-sources.html` |

### 2.3 API + 工具现状

| 工具 | 状态 | 位置 |
|---|---|---|
| `GET /api/digest/today` | ✅ 存在 | `lib/api.ts:241` |
| `GET /api/digest/daily/{date}` | ✅ 存在 | `lib/api.ts:245` |
| `getDailyDigest(date)` 函数 | ✅ 存在 | `lib/api.ts:244` |
| `useDigestToday()` hook | ✅ 存在 | `hooks/useDigest.ts:78` |
| `useDigestDate(date)` hook | ❌ **缺失** | 需新建 |
| `HideDialog` 组件 | ✅ 存在可复用 | `components/digest/HideDialog.tsx` |
| `DigestCard` 组件 | ✅ 存在可复用 | `components/digest/DigestCard.tsx` |

## 3 · 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| Sidebar 高亮失效 | 🟡 中 | Layout.tsx 同步改 3 处 |
| E2E/Visual test 全挂 | 🟡 中 | 同步改 3 个 spec 文件 |
| `/ai/*` 旧链接 404 | 🟢 低 | 接受 · 后续可加 redirect |
| type error 累计 | 🟡 中 | commit 前 `tsc --noEmit` 比对 |
| useDigestDate 与 today 行为差异 | 🟡 中 | 404 时 page 显示 EmptyState |
| related items 当前可能为空 | 🟢 低 | 显示"暂无相关历史" |

## 4 · 设计意图（v2 spec 已确定）

- 5 个 page · 路由 `/push/*`（mockup 路径一致）
- 详情页 `/push/daily/[date]` 是按日期查看单条 digest
- history 概念被 daily 替代 · history.tsx 是 V3.8 残留（"推送历史"占位页 · 与 daily detail 无关）
- mockup 02 完整要素：返回今日 link + 双轴标签 + 元信息行 + 标题 + 摘要 + 原文来源块 + 三按钮 + 相关历史 + HideDialog

## 5 · 依赖与影响面

### 5.1 依赖图

```
v2 设计文档（已存在）
  ├─ component-spec.md § 1.5 Page 2（详情页 ASCII wireframe）
  ├─ mockups/02-daily-detail.html（详情页 mockup）
  ├─ api-spec.md § 132（GET /api/digest/daily/{date}）
  └─ types/digest.ts（v2 模型已声明）

依赖文件
  ├─ frontend/lib/api.ts:245（getDailyDigest 已存在）
  ├─ frontend/components/digest/HideDialog.tsx（可复用）
  ├─ frontend/components/digest/DigestCard.tsx（可复用 · 注：接口与 spec 略有不符）
  └─ frontend/hooks/useDigest.ts（hook 模式参照）

影响文件
  ├─ frontend/pages/ai/{today,bookmarks,settings,sources}.tsx（迁移源）
  ├─ frontend/components/v3/Layout/Layout.tsx（导航同步）
  ├─ frontend/tests/{e2e/pages,e2e/a11y,visual/digest}.spec.ts（路由引用）
  └─ frontend/__tests__/（vitest snapshot）
```

### 5.2 不影响

- backend（API 不动 · DB 不动）
- 其他 frontend 模块（learn / interview / admin / knowledge / etc.）

## 6 · 范围（plan § 1 已定）

### 6.1 做（P0）

- 4 个 page 文件迁移（/ai/* → /push/*）
- Layout sidebar 同步
- 3 个 spec 文件路由引用更新
- 新建 useDigestDate hook
- 新建 /push/daily/[date].tsx（mockup 02 完整实现）
- 验证：build / typecheck / vitest / Playwright

### 6.2 不做（标 ⏸）

- DigestCard 接口对齐 spec § 2.1（🟡 P1 follow-up）
- components/digest/<Name>/ 目录拆分（🟢 P2 follow-up）
- DailyCard.tsx 残留组件删除（🟢 P2 follow-up）
- 旧 /ai/* → /push/* redirect（🟢 P1 follow-up）

## 7 · 历史 commit 检索

```bash
$ git log --oneline --all | grep -i "ai.push\|/ai/\|/push" | head
# 检索结果：当前未发现专门处理 /ai/* → /push/* 的历史 commit
# 与本任务无冲突 · 可干净实施
```

## 8 · 完整调研发现（plan 已采纳）

详见 [plan.md § 0](plan.md)

## 9 · 元信息

- **调研日期**：2026-07-25
- **调研耗时**：~30 min（含 chat 内交互）
- **调研作者**：Claude
- **下一步**：[plan.md](plan.md) → [tasks.md](tasks.md) → 实施 T1-T13