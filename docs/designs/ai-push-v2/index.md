# AI 推送 · 设计索引（v2）

> **本目录仅存链接 · 不存实际设计文件**
>
> 实际设计产物（HTML mockup · 组件规格）都在对应的 task 目录下。
> 这里只放**指针**，方便从 designs/ 这个全局入口访问。

---

## 任务上下文

- **Task 目录**：[`docs/tasks/2026-07-17-new-feature-ai-push/`](../../tasks/2026-07-17-new-feature-ai-push/)
- **设计版本**：v2（基于 spec.md 重新设计 · 替代 2026-06-22 旧版）
- **设计日期**：2026-07-17

## 📄 HTML 页面 mockup（standalone · 可打开看）

> 5 页 5 个 standalone HTML · 含完整 inline CSS · 真实 AI 内容 · 移动端响应式
>
> **打开方式**：`open docs/tasks/2026-07-17-new-feature-ai-push/mockups/01-today.html`

| # | 路径 | 页面 | 设计要点 |
|---|---|---|---|
| 1 | [`mockups/01-today.html`](../../tasks/2026-07-17-new-feature-ai-push/mockups/01-today.html) | `/push` 今日主入口 | vibe badge · 5 cards · 双轴标签 · 收藏/屏蔽 |
| 2 | [`mockups/02-daily-detail.html`](../../tasks/2026-07-17-new-feature-ai-push/mockups/02-daily-detail.html) | `/push/daily/[date]` 详情 | 完整摘要 · 原文溯源 · 相关历史 · HideDialog modal |
| 3 | [`mockups/03-bookmarks.html`](../../tasks/2026-07-17-new-feature-ai-push/mockups/03-bookmarks.html) | `/push/bookmarks` 我的收藏 | 筛选 tabs · 排序 · 4 条预览 |
| 4 | [`mockups/04-settings.html`](../../tasks/2026-07-17-new-feature-ai-push/mockups/04-settings.html) | `/push/settings` 推送设置 | 时间 · 渠道 · 关注/屏蔽标签 · 实时保存 |
| 5 | [`mockups/05-sources.html`](../../tasks/2026-07-17-new-feature-ai-push/mockups/05-sources.html) | `/push/sources` 信源管理 | 4 stat cards · 启停 Switch · AddSource modal |

## 📋 相关规格文档（也是链接）

| 文档 | 用途 | 路径 |
|---|---|---|
| spec.md | 技术契约（10 Requirements + 34 Scenarios）| [`../../tasks/2026-07-17-new-feature-ai-push/spec.md`](../../tasks/2026-07-17-new-feature-ai-push/spec.md) |
| component-spec.md | 5 组件详细规格（Props/State/Events/测试）| [`../../tasks/2026-07-17-new-feature-ai-push/component-spec.md`](../../tasks/2026-07-17-new-feature-ai-push/component-spec.md) |
| db-design.md | 9 表 schema + 迁移 SQL | [`../../tasks/2026-07-17-new-feature-ai-push/db-design.md`](../../tasks/2026-07-17-new-feature-ai-push/db-design.md) |
| product-doc.md | 产品意图（人主导）| [`../../tasks/2026-07-17-new-feature-ai-push/product-doc.md`](../../tasks/2026-07-17-new-feature-ai-push/product-doc.md) |
| research.md | 0 步调研 | [`../../tasks/2026-07-17-new-feature-ai-push/research.md`](../../tasks/2026-07-17-new-feature-ai-push/research.md) |

## 🆚 对比 · 旧版设计（v1）

> 旧 spec（2026-06-22）的设计在 [`../AI推送-页面设计.html`](../AI推送-页面设计.html) · scope 较宽（含商业/投资/PM）· free-form 散文 spec
>
> 本 v2 版本基于用户 2026-07-17 反馈重设计：**scope 收窄为 AI/LLM/Agent** · 双轴标签 · pull-based 主路径 · 5 条固定（不是 1-5 可变）

## 设计理念

1. **Pull-based 主路径** — 主体验在 KnockWise 内 · 邮件/微信退化通知 · 减少推送疲劳
2. **双轴标签** — type (模型/应用) × region (国内/国外) · 4 种 badge 一眼可分
3. **多源入 · 少条出** — 30+ 信号池 → 5 维综合打分 → 输出固定 5 条
4. **每条 digest 必须有 source_url + related_item_ids** — 反 LLM 幻觉 · 信任基础

## 元信息

- **本目录结构**：仅 `index.md`（指针）· 不存实际设计文件
- **指针维护规则**：每次 task 目录设计文件变更后 · 同步更新本 index.md 的链接
- **不存 git 跟踪**：本目录及 mockup 文件不进 git · 是设计展示用
