# Retro · AI 推送今日主入口 mockup 对齐

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [tasks.md](tasks.md) · [research.md](research.md)

---

## 1 · 做对了什么

| # | 决策 / 执行 | 效果 |
|---|---|---|
| ✅ | T1-T4 一个 commit · 都在 DigestCard + index.tsx 范围 | 改动集中 · 风险小 |
| ✅ | T1 中文标签用 Record 映射表（与 TYPE_COLORS 同结构）| 一致 · 易扩展 |
| ✅ | T2 主题标签颜色按 mockup 表（头条粉/工程蓝/论文紫/观点琥珀）| 视觉对齐 |
| ✅ | T3 状态栏直接 inline 在 index.tsx · 不抽组件 | 简单 · 1 处用 |
| ✅ | T4 用 `data-testid` 给 DigestCard（扩展 e2e 可用）| 顺便给未来测试铺路 |
| ✅ | 顺手修 auth bug（fetch 不带 Authorization）· 用户能真正看到推送 | 隐藏关键 bug 一起治 |

## 2 · 踩了什么坑

| # | 坑 | 解决 |
|---|---|---|
| 🕳️ | vitest 找不到 `@/pages/push` 解析（无 extension 配置）| 改用 `@/pages/push/index` |
| 🕳️ | 新 useDigest* 用 getToken · 测试需要 mock | 加 `vi.mock('@/lib/api', () => ({ getToken: () => null }))` |

## 3 · 调研偏差修正

| # | research 声称 | 实际 | 修正 |
|---|---|---|---|
| 1 | "category 是 headline/paper/engineering/opinion" | ✅ 准确 · DB 用 Literal | — |
| 2 | "i18n 内联函数即可" | ✅ 准确 | — |
| 3 | "底部状态栏在 section 后加 p" | ✅ 准确 | — |
| 4 | "已读样式 opacity + border-l 灰" | ✅ 准确 · 与 mockup 一致 | — |

## 4 · 下次该改什么

| # | 改进项 | 类别 | 优先级 |
|---|---|---|---|
| 1 | **vitest resolve.extensions** 加 `['.ts', '.tsx', ...]` · `@/pages/push` 就不需要 `/index` | 工程 | 🟢 P2 |
| 2 | **i18n 抽到 `lib/i18n.ts`** · 后续 books/settings 也用 | 重构 | 🟡 P1 |
| 3 | **状态栏增加 "查看全部 →" 链接到 daily detail** | UX | 🟢 P2 |
| 4 | **主题标签加 hover tooltip 显示完整说明** | UX | 🟢 P2 |
| 5 | **P1 范围（bookmarks/settings/sources 补齐）** | 重构 | 🟡 P1 |

## 5 · memory 更新清单

| # | 类型 | 摘要 |
|---|---|---|
| 1 | feedback | **hooks 直接用 `fetch()` 不带 Authorization 是常见坑** · 应统一走 `lib/api.ts:request()` 或 `authHeaders(getToken())` |
| 2 | feedback | **vitest `@/pages/foo` 不自动解析 `index.tsx`** · 配置 `resolve.extensions` 或 import 时带 `/index` |

---

## 6 · 任务元数据

| 字段 | 值 |
|---|---|
| 任务 ID | `2026-07-25-refactor-today-page-mockup-align` |
| commit | `04294f4` |
| 文件改动 | 5 files · +153/-22 |
| 估时 vs 实际 | 估 30 min → 实际 ~25 min |
| 测试覆盖 | vitest 1/1 · e2e 7/7 |

---

## 元信息

- **路径**：`docs/tasks/2026-07-25-refactor-today-page-mockup-align/retro.md`
- **下一步**：用户确认闭环 → 浏览器访问 `/push` 看效果