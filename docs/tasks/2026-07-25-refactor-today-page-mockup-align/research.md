# Research · AI 推送今日主入口 mockup 对齐

> 日期：2026-07-25 · 作者：Claude · 版本：v1
> 配套：[plan.md](plan.md) · [tasks.md](tasks.md)

---

## 0 · 任务理解

用户原话："你看看现在的这个 和设计图是不是差距不小？"

我的理解：当前 `/push` 今日主入口实现与 v2 设计 mockup `01-today.html` 在视觉 / 信息密度上有 4 处显著偏差：中文标签、主题标签、底部状态栏、已读样式。

## 1 · 设计 vs 实现 gap（today 主入口）

### 1.1 完整 mockup 01-today.html 要点

| 元素 | mockup 写法 | 当前实现 |
|---|---|---|
| type tag | "模型" / "应用" | "model" / "application" |
| region tag | "国内" / "国外" | "domestic" / "overseas" |
| 主题 tag | "头条" / "工程" / "论文" | **缺**（不显示） |
| 已读样式 | opacity 0.6 + 灰 border-left | **缺**（无视觉降级）|
| 底部状态栏 | "2/5 已读 · 剩余 3 分钟 · 推送时间 08:00" | **缺**（无） |

### 1.2 颜色（mockup 提供）

| 主题 | 背景 | 字色 |
|---|---|---|
| 头条 | `rgba(244,114,182,0.18)` | `#fbcfe8` |
| 工程 | `rgba(96,165,250,0.12)` | `#93c5fd` |
| 论文 | `rgba(167,139,250,0.18)` | `#c4b5fd` |

## 2 · 范围

### 2.1 做（P0）

| T# | 任务 |
|---|---|
| T1 | 加 i18n 映射函数（type/region/category → 中文） |
| T2 | DigestCard 显示主题标签（头条/工程/论文）· 颜色按 category |
| T3 | today 主入口加底部状态栏 "N/5 已读 · 剩余 N 分钟 · 推送时间 08:00" |
| T4 | DigestCard 加已读视觉降级（opacity + border-left 灰） |

### 2.2 不做（标 ⏸）

| 项 | 原因 |
|---|---|
| bookmarks / settings / sources 补齐 | 用户未选 P1 |
| daily 相关历史真实数据 | 需后端 endpoint · P2 |

## 3 · 关键决策

| # | 决策 | 选择 |
|---|---|---|
| 1 | i18n 实现位置 | 内联函数 `formatType()` / `formatRegion()` / `formatCategory()`（与现有 `TYPE_COLORS` 同样位置）|
| 2 | 主题标签样式 | 复用 type/region 的玻璃胶囊样式（边框+背景+11px字号） |
| 3 | 底部状态栏 | 在 today.tsx `<section>` 后加 `<p>` · 简单不抽组件 |
| 4 | 已读样式 | `item.is_read` → opacity 0.6 + border-l 灰（与 mockup `.digest-card.read` 一致）|

## 4 · 风险

| 风险 | 缓解 |
|---|---|
| 现有 e2e scenario 断言改后挂 | 同步更新断言用 formatText 后字符串 |
| category 是 free string 但 DB 里是 headline/paper/engineering/opinion | 加映射表覆盖 + 默认 "其他" |
| 新视觉与既有暗色主题不协调 | 复用既有的 glassmorphism 色板 |

## 元信息

- **调研日期**：2026-07-25
- **路径模式**：refactor-6
- **范围**：P0
- **下次**：[plan.md](plan.md) → [tasks.md](tasks.md) → 实施