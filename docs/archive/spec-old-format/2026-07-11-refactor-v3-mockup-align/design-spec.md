---
title: 设计文档 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [design-spec, 1步, 设计脑, v3-mockup-align, knockwise, refactor]
related:
  - [research.md](research.md) — 上游调研（11 章节 · 17h 路径）
  - [product-doc.md](product-doc.md) — 上游产品脑（用户视角）
  - [spec.md](spec.md) — 下游技术契约（架构 / Props / API Schema）
  - [ue-brief.md](ue-brief.md) — 给 UE 同事的 12 张图 brief
  - [mockups/v38-mockup.html](mockups/v38-mockup.html) — 可点击 SPA mockup（1491 行 · 73KB）
  - V3 design-spec §3.6 Sidebar: [../2026-07-09-new-feature-question-bank-expand/design-spec.md#sidebar-设计规范](../2026-07-09-new-feature-question-bank-expand/design-spec.md) — 已写，本文档不重复
---

# 设计文档：KnockWise 前端对齐重构

> **一句话**：把当前"4 套品牌名 + 8 处横向 nav + 17 page 视觉各异"的前端，重构成"统一 KnockWise 品牌 + 左侧 Sidebar 5 大分组 + Dashboard Hero/雷达/stats 三态切换 + 5 个新路由 EmptyState 占位"的视觉。
>
> **作者**：设计脑 · 用户决策已锁（三档全改 / 接受 17h / KnockWise 品牌 / playwright 截图验证）
> **核心定位**：**只换壳**。视觉重构不改业务行为、API 契约、数据模型。
> **重要参照**：[mockups/v38-mockup.html](mockups/v38-mockup.html) 是本文档的可点击 SPA 版本 —— 所有视觉规范都能在 mockup 里直接看到 + 切换状态。

---

## 0. 全局架构图（CLAUDE.md §1.5 强制 · 用户视角）

```
┌────────────────────────────────────────────────────────────────────────┐
│                          KnockWise 视觉目标（V3.8）                      │
│                                                                        │
│   ┌──顶部 nav（极简）──────────────────────────────┐                  │
│   │  [🚪 KnockWise]                  [👤 开发者]  │                  │
│   └──────────────────────────────────────────────────┘                  │
│   ┌──────┬─────────────────────────────────────────────────────┐      │
│   │      │                                                     │      │
│   │ 左   │   主内容区（17 page · 信息密度递增）                  │      │
│   │ 侧   │                                                     │      │
│   │ Side │   ┌──────────────────────────────────────────────┐   │      │
│   │ bar  │   │ Hero（粉紫 · 60% 视觉权重 · 5 状态可切）    │   │      │
│   │ 240  │   │  主任务 + 上次成绩 3 栏 + 3 雷达 + 主按钮   │   │      │
│   │ px   │   └──────────────────────────────────────────────┘   │      │
│   │      │   ┌──────────────────────────────────────────────┐   │      │
│   │ 5 大 │   │ StatsBar（5 列横条 · 等宽数字）               │   │      │
│   │ 分组 │   └──────────────────────────────────────────────┘   │      │
│   │ +    │   ┌──────────────────────────────────────────────┐   │      │
│   │ Admin│   │ 3 核心卡（AI 紫/每日橙/计划绿青 · 压缩）      │   │      │
│   │ 🆕   │   └──────────────────────────────────────────────┘   │      │
│   │      │   ┌──────────────────────────────────────────────┐   │      │
│   │      │   │ 5 列 module-quick-link（学/复习/计划/画像/题单）│   │      │
│   │      │   └──────────────────────────────────────────────┘   │      │
│   └──────┴─────────────────────────────────────────────────────┘      │
│                                                                        │
│   16 入口 Sidebar（5 分组 + Admin）：                                     │
│     概览 / 面试 / 学习复习 / 知识库 / AI 推送 / 我的 / Admin 🆕           │
└────────────────────────────────────────────────────────────────────────┘
```

**视觉 4 层信息密度**（自上而下）：
1. **Hero 卡 60%**（最高密度 · 主任务 + 雷达 + 主按钮）
2. **StatsBar 5 列**（中密度 · 数字横条）
3. **3 核心卡**（中密度 · AI/挑战/计划）
4. **5 module-quick-link**（低密度 · 入口导航）

---

## 1. 用户旅程（CLAUDE.md § 阶段 1 必填 · 视觉视角）

> 完整场景见 [product-doc.md §2](product-doc.md)。本节只关注**视觉变化**。

### 1.1 重构前后对比（用户视觉感知）

| 时刻 | 重构前视觉 | 重构后视觉 |
|---|---|---|
| **打开 dashboard** | 顶部 7 tab 横条 + "KnockWise" logo + 4 模块卡 | 左 Sidebar 5 分组 + 顶部"KnockWise" + Hero 卡 + 雷达 |
| **找 AI 推送** | ❌ 找不到 | ✅ Sidebar "AI 推送" 分组 · 今日推荐 + 推送历史 |
| **找题库管理** | ❌ 找不到 | ✅ Sidebar 底部 "ADMIN" 分组 · 题库管理 + 手动同步 |
| **首次加载 dashboard** | 看到空白 0.5s | ✅ HeroCardSkeleton + StatsBarSkeleton + RadarMiniSkeleton pulse |
| **API 失败** | 报错弹窗 / 白屏 | ✅ ErrorState 红色三角 + 错误码 + 重试 CTA |
| **新用户 0 面试** | 4 模块卡占位 | ✅ HeroCard empty 状态 · "开始第一次面试" 大按钮 |
| **看历史成绩** | 进 /interview/history 翻列表 | ✅ HeroCard 直接展示 3 雷达 + 上次成绩 3 栏 |
| **移动端访问** | 顶部 7 tab 挤一行 | ✅ Sidebar 隐藏 + 汉堡按钮 + drawer 滑入 |

---

## 2. 页面地图（CLAUDE.md § 阶段 1 必填）

### 2.1 17 page（5 大分组 + Admin）

| Sidebar 分组 | Page | 路由 | V3.8 状态 | 视觉规格 |
|---|---|---|---|---|
| 概览 | 今日概览 | `/dashboard` | 🔄 重写 | §3 Hero + StatsBar + 3 卡 + 5 入口 |
| 面试 | 今日面试 🆕 | `/interview/profile` | ✅ V1 既有 | V1 风格 + KnockWise 主题 |
| 面试 | 历史报告 | `/interview/history` | ✅ V1 既有 | 沿用 |
| 面试 | 面试配置 | `/interview/setup` | ✅ V1 既有 | 沿用 |
| 学习复习 | 题目浏览 | `/learn` | ✅ V1 + V3 TagFilter | 沿用 |
| 学习复习 | 复习中心 | `/review` | ✅ V1 + V3 TagFilter | 沿用 |
| 学习复习 | 学习计划 V3 | `/plan` | ✅ V3.0 已实装 | PlanCard 4 子卡 |
| 学习复习 | 精选题单 V3 | `/collections` | ✅ V3.1 已实装 | CollectionCard |
| 知识库 | 笔记浏览 | `/knowledge` | ✅ V1 既有 | 沿用 |
| 知识库 | 问答社区 | `/qa` | ✅ V1 既有 | 沿用 |
| 知识库 | 报告中心 | `/report` | ✅ V1 既有 | 沿用 |
| AI 推送 | 今日推荐 V3 | `/ai/today` | 🆕 新路由壳 | §4 EmptyState 占位 |
| AI 推送 | 推送历史 | `/ai/history` | 🆕 新路由壳 | §4 EmptyState 占位 |
| 我的 | 我的画像 | `/profile` | ✅ V2.3 已实装 | recharts 折线图 + 弱项列表 |
| 我的 | 设置 | `/settings` | 🆕 新路由壳 | §4 EmptyState 占位 |
| Admin 🆕 | 题库管理 | `/admin/questions` | 🆕 新路由壳 | §4 EmptyState 占位 |
| Admin 🆕 | 手动同步 | `/admin/sync` | 🆕 新路由壳 | §4 EmptyState 占位 |

### 2.2 折叠/移动端行为

| 视口 | Sidebar 状态 | 触发 |
|---|---|---|
| ≥ 1024px desktop | 展开 240px（可折叠 64px）| 折叠按钮切换 |
| < 1024px mobile/tablet | 默认隐藏 + 汉堡按钮唤出 | 浏览器自动 + 汉堡按钮 |

---

## 3. V3.8 新组件视觉规范

> Sidebar 视觉规范已写在 V3 design-spec §3.6（[链接](../2026-07-09-new-feature-question-bank-expand/design-spec.md)），本文档不重复。
> 下面是 V3.8 新增的 5 个组件视觉。

### 3.1 HeroCard（V3.8 核心 · Dashboard 顶部 60% 视觉权重）

#### 3.1.1 容器样式

```css
background: linear-gradient(135deg, 
  rgba(244,114,182,0.15) 0%, 
  rgba(236,72,153,0.12) 50%, 
  rgba(168,85,247,0.15) 100%);
border: 1px solid rgba(244,114,182,0.4);
box-shadow: 0 0 0 1px rgba(244,114,182,0.15), 0 16px 48px rgba(244,114,182,0.3);
border-radius: 16px;
padding: 48px;
```

#### 3.1.2 内部布局（5 列 grid）

```
┌─────────────────────────────────────────────────────────────────┐
│  grid-cols-1 md:grid-cols-5 gap-8                               │
│                                                                 │
│  ┌──── 左 3 列 ─────────────────────┐ ┌──── 右 2 列 ─────────┐ │
│  │ 🎤 今日主任务  [未完成]            │ │  最近 3 次雷达        │ │
│  │                                  │ │  ┌──┐ ┌──┐ ┌──┐     │ │
│  │ 开始一场 Mock 面试              │ │  │雷│ │雷│ │雷│     │ │
│  │ (渐变文字 pink→violet→indigo)   │ │  │达│ │达│ │达│     │ │
│  │                                  │ │  └──┘ └──┘ └──┘     │ │
│  │ 系统会根据你的薄弱点...          │ │   78    68    62     │ │
│  │ (text-gray-300 · line-height 1.7)│ │  字节  阿里  腾讯   │ │
│  │                                  │ │                       │ │
│  │ 上次面试   │ 已面试  │  平均分   │ │  查看全部 12 场 →    │ │
│  │ [3 栏等宽 · tabular-nums 数字]   │ │                       │ │
│  │                                  │ │                       │ │
│  │ [开始面试 →]  [查看历史]  [⚙]    │ │                       │ │
│  └──────────────────────────────────┘ └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.3 5 状态视觉规范

| 状态 | 触发条件 | 视觉 | 主按钮 | 雷达区 |
|---|---|---|---|---|
| **full** | 3+ 面试 completed | 粉紫渐变 + 完整 3 雷达 + 上次成绩 3 栏 | "开始面试 →" indigo 主按钮 | 3 个 RadarMini（粉/紫/蓝）|
| **partial** | 1-2 面试 | 粉紫渐变 + 已有雷达 + 灰色虚线五边形占位 | "开始第 N 次 →" | N 个实 + (3-N) 个虚 |
| **empty** | 0 面试（新用户）| 粉紫渐变 + EmptyState 紫色虚线圆 + "?" 图标 | "开始第一次面试 →" | 全部隐藏 |
| **loading** | API pending | 粉紫渐变 + skeleton 占位（pulse 动画 1.8s）| 半透明 + 不可点击 | 3 个灰色 80×80 占位 |
| **error** | API 4xx/5xx（非 401）| 粉紫渐变 + 红色三角警告 + 错误码 | "重试" 红色按钮 | 隐藏 |

**5 状态切换器**：Dashboard 顶部右侧有 `<state-switcher>` UI（full/partial/empty/loading/error），开发期间人工切换 + playwright 截图测试基线。

#### 3.1.4 关键 token

- **渐变文字**：`bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-violet-400 to-indigo-400`
- **标签**：背景 `rgba(244,114,182,0.2)` + 文字 `#fbcfe8` + 边框 `rgba(244,114,182,0.4)` + padding `6px 14px` + 字号 `13px` + 字重 `600`
- **主按钮**：padding `14px 32px` + 字号 `16px` + 字重 `600` + 阴影 `0 8px 24px rgba(99,102,241,0.4)`
- **上次成绩数字**：`text-2xl font-bold stat-num`（tabular-nums 等宽）

### 3.2 StatsBar（5 列横条统计）

```
┌─────────────────────────────────────────────────────────────────┐
│  background: linear-gradient(135deg, rgba(99,102,241,0.04), rgba(168,85,247,0.04))│
│  padding: 18px 24px · 圆角 16px · 不悬浮                        │
├─────────────────────────────────────────────────────────────────┤
│  flex divide-x divide-white/5                                    │
│                                                                 │
│  本周答题    命中率     待复习     连续打卡    已完成              │
│  28         82%        14         7天         56/200              │
│  +12% ↑     +5pp ↑     3 题紧急   个人最佳    28% · 详情 →       │
└─────────────────────────────────────────────────────────────────┘
```

**每列规范**：

| 元素 | 样式 |
|---|---|
| **label** | `text-xs uppercase tracking-wider text-gray-500 mb-1` |
| **value** | `text-2xl font-bold stat-num text-white`（数字等宽）|
| **trend 上** | `text-xs text-emerald-400 mt-0.5`（如 `+12%`）|
| **trend 警告** | `text-xs text-amber-400 mt-0.5`（如 `3 题紧急`）|
| **trend 灰** | `text-xs text-gray-400 mt-0.5`（如 `个人最佳`）|

**分隔线**：用 `divide-x divide-white/5`（每列间 1px 5% 白线）

**数据示例**（来自 V3 mockup §页面 1 L1068-1096）：
- 本周答题 28 (+12%)
- 命中率 82% (+5pp)
- 待复习 14 (3 题紧急)
- 连续打卡 7 天 (个人最佳)
- 已完成 56/200 (28%)

### 3.3 RadarMini（80×80 SVG · 5 维迷你雷达）

#### 3.3.1 配色梯度（3 个雷达并排）

| 顺序 | 公司 | 主题色 | 描边色 | 填充透明度 |
|---|---|---|---|---|
| 1 | 字节（最近）| `#f472b6`（pink-400）| `rgba(244,114,182,1)` | 0.25 |
| 2 | 阿里 | `#a78bfa`（violet-400）| `rgba(167,139,250,1)` | 0.25 |
| 3 | 腾讯 | `#60a5fa`（blue-400）| `rgba(96,165,250,1)` | 0.25 |

外框 5 边形统一：`fill="none" stroke="rgba(<theme>,0.15)" stroke-width="1"`

#### 3.3.2 SVG 模板

```svg
<svg viewBox="0 0 80 80" style="width: 100%; height: auto;">
  <!-- 5 边形外框 -->
  <polygon points="40,8 70,28 60,68 20,68 10,28"
           fill="none" stroke="rgba(244,114,182,0.15)" stroke-width="1"/>
  <!-- 数据多边形（不规则反映各公司雷达差异）-->
  <polygon points="40,12 64,30 56,62 22,64 14,32"
           fill="rgba(244,114,182,0.25)" stroke="#f472b6" stroke-width="1.5"/>
</svg>
<p class="text-xs text-gray-400 mt-1 stat-num">78</p>
<p class="text-xs text-gray-500">字节</p>
```

#### 3.3.3 partial 状态视觉

未达到的雷达用虚线占位：

```svg
<svg viewBox="0 0 80 80" style="width: 80px; height: 80px;">
  <polygon points="40,8 70,28 60,68 20,68 10,28"
           fill="none" stroke="rgba(255,255,255,0.1)" 
           stroke-width="1" stroke-dasharray="3 3"/>
</svg>
<p class="text-xs text-gray-600 ml-2">?</p>
```

### 3.4 TopNav（极简版 · V3.8 重构）

```
┌─────────────────────────────────────────────────────────────────┐
│  height: 56px · background: rgba(5,9,20,0.85) + backdrop-blur  │
│  border-bottom: 1px solid rgba(148,163,184,0.08)               │
├─────────────────────────────────────────────────────────────────┤
│  [🚪 Logo] KnockWise  V3.8 mockup    今日概览                    │
│                            [📅 2026-07-11] [用户头像]            │
│                            [👤 开发者]                          │
└─────────────────────────────────────────────────────────────────┘
```

**vs V1 顶部 nav（7 tab 横条）**：

| 元素 | V1 | V3.8 |
|---|---|---|
| 横向 tab | 7 个（仪表盘/面试/学/复习/计划🆕/知识库/信息流）| ❌ 全部移到 Sidebar |
| Logo | "KnockWise" / "KnockWise" | **"KnockWise" + 敲门图标 SVG** |
| 中间区 | 无 | **breadcrumb**（当前 page 名）|
| 右侧 | 用户头像 + 退出 | 用户头像 + 用户名（退出移 Sidebar）|
| 移动端 | 7 tab 挤一行 | **汉堡按钮**（唤出 Sidebar drawer）|

### 3.5 5 个 module-quick-link（学/复习/计划/画像/题单）

```
┌─────────────────────────────────────────────────────────────────┐
│  background: glass-card-static · padding: 20px 24px            │
│  grid-cols-2 md:grid-cols-5 gap-2                               │
├─────────────────────────────────────────────────────────────────┤
│  [📚]      [🔄]      [📋]      [👤]      [📚]                  │
│   学习      复习      计划      画像      题单                   │
│  (蓝)    (紫)    (绿)    (粉)    (蓝)                          │
└─────────────────────────────────────────────────────────────────┘
```

每格规范：
- 容器：背景 `rgba(255,255,255,0.02)` + 边框 1px + 圆角 10px
- icon：24×24 SVG（学=蓝/复习=紫/计划=绿/画像=粉/题单=蓝）
- 文字：12px + 中等字重 + 主题色（计划绿/题单蓝）或灰色

### 3.6 Sidebar 折叠态 + 移动端 drawer

**折叠态**：

```
展开（240px）：                折叠（64px）：
┌──────────────────────┐    ┌────┐
│ [logo] KnockWise  [⊏]│    │[l] │⊏  ← 仅图标
├──────────────────────┤    ├────┤
│ [🔍 搜索...]         │    │[🔍]│  ← 搜索图标
├──────────────────────┤    ├────┤
│ ▼ 概览               │    │[▼] │  ← 仅折叠图标
│   • 今日概览         │    │[•] │  ← 仅图标
│   ...                │    │... │
└──────────────────────┘    └────┘

过渡动画：width 0.3s cubic-bezier(0.16, 1, 0.3, 1)
```

**移动端 drawer（< 1024px）**：

```
默认隐藏：
┌────────────────────────────────────────┐
│ [☰]  [🚪 KnockWise]   [👤 用户]      │  ← 顶部 nav 含汉堡按钮
├────────────────────────────────────────┤
│                                        │
│         主内容（无左边距）              │
│         padding: 16px 20px             │
│                                        │
└────────────────────────────────────────┘

点 [☰] 后：
┌────────────────────────────────────────┐
│ ▓▓▓▓ 背景半透明 black/50               │
│ ┌──────┐                                │
│ │ 侧栏 │  ← transform: translateX(0)   │
│ │ 从左 │     240px 宽                  │
│ │ 滑入 │     backdrop-blur-2xl         │
│ │      │                                │
│ └──────┘                                │
│                                        │
└────────────────────────────────────────┘
```

**交互**：
- 点 ☰ → 唤出 drawer
- 点背景 / ESC → 关闭 drawer
- lock body scroll while open

### 3.7 KnockWise Logo（3 候选 + 多尺寸）

> 用户拍板决定选哪个之前，3 候选同时存在。UE 同事按 [ue-brief.md §1.1](ue-brief.md) 出图。

#### 3.7.1 候选 A：敲门图标（默认）

```svg
<svg width="28" height="28" viewBox="0 0 28 28">
  <defs>
    <linearGradient id="logo-grad" x1="0" y1="0" x2="28" y2="28">
      <stop stop-color="#6366f1"/>
      <stop offset="1" stop-color="#a78bfa"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="24" height="24" rx="7" fill="url(#logo-grad)"/>
  <!-- 主敲门（实） -->
  <path d="M10 8L10 20M10 20L13 17M10 20L13 23" 
        stroke="white" stroke-width="2" stroke-linecap="round"/>
  <!-- 回敲门（虚，呼应） -->
  <path d="M17 11L17 17M17 17L20 14M17 17L20 20" 
        stroke="white" stroke-width="2" opacity="0.5" stroke-linecap="round"/>
</svg>
```

**含义**：主敲门（实）+ 回敲门（虚 50%）= 双向交流，呼应 "Knock" 关键词。

#### 3.7.2 候选 B：答题卡 + 闪烁

```svg
<rect ... rx="24" fill="url(#logo-grad)"/>
<rect x="32" y="34" width="56" height="52" rx="6" fill="white" opacity="0.95"/>
<path d="M40 50h40M40 60h32M40 70h28" stroke="#6366f1" stroke-width="3"/>
<!-- 右上角闪烁 -->
<path d="M88 30L94 36M94 30L88 36" stroke="white" stroke-width="2.5"/>
<circle cx="91" cy="33" r="3" fill="white"/>
```

**含义**：答题卡 + 闪光 = 面试瞬间 + 知识可视化。

#### 3.7.3 候选 C：几何 K

```svg
<rect ... rx="24" fill="url(#logo-grad)"/>
<path d="M40 28L40 92M40 60L72 28M40 60L72 92" 
      stroke="white" stroke-width="9" stroke-linecap="round"/>
<circle cx="84" cy="60" r="5" fill="white"/>
```

**含义**：K 字母几何 + 装饰圆 = 简洁国际化。

#### 3.7.4 多尺寸规格

| 尺寸 | 用途 | 边框圆角 |
|---|---|---|
| 28×28 | favicon | rx=7 |
| 56×56 | Sidebar | rx=14 |
| 200×200 | 登录页 | rx=50 |
| 单色版 | 任意深色背景 | 透明背景 |

### 3.8 三态视觉（loading / empty / error）

> spec.md §7.3 已规定三态处理模式（loading skeleton / EmptyState / error state）。本节规定视觉。

#### 3.8.1 Loading skeleton（pulse 动画 1.8s）

**4 类组件 skeleton 设计**：

**HeroCardSkeleton**（保留 5 列 grid 布局）：
```
[▓▓▓▓] 🎤 主任务    [▓▓▓▓]
[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]    [▓▓▓▓]
[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]   [▓▓▓▓]
上次 78 │ 12 次 │ 72      [▓▓▓▓]
[▓▓▓▓▓▓]  [▓▓▓▓▓]        [▓▓▓▓]
```

**StatsBarSkeleton**：
```
本周答题    命中率    待复习    连续打卡    已完成
[▓▓▓▓]   [▓▓▓▓]   [▓▓▓▓]   [▓▓▓▓]   [▓▓▓▓]
```

**RadarMiniSkeleton**：
```
[▓▓▓]    [▓▓▓]    [▓▓▓]
```

**AIRecommendationCardSkeleton**：
```
[▓▓▓▓▓▓▓▓▓▓▓▓▓▓]
[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]
[▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]
```

**Skeleton 通用样式**：
```css
.skeleton {
  background: linear-gradient(90deg,
    rgba(148, 163, 184, 0.04) 0%,
    rgba(148, 163, 184, 0.08) 50%,
    rgba(148, 163, 184, 0.04) 100%);
  background-size: 200% 100%;
  animation: skeleton-pulse 1.8s ease-in-out infinite;
  border-radius: 6px;
}
@keyframes skeleton-pulse {
  0%, 100% { background-position: 200% 0; opacity: 1; }
  50% { background-position: -200% 0; opacity: 0.6; }
}
```

#### 3.8.2 Empty 状态（4 种 type · 沿用 V1 closure EmptyState）

| type | SVG | 适用场景 |
|---|---|---|
| `knowledge` | 笔记本紫色渐变 | 学习/笔记类空数据 |
| `progress` | 进度环空心 | 进度/成就类空数据 |
| `data` | 数据库/数据流 | 通用数据空（最常用）|
| `vault` | 保险柜/仓库 | 资源/题库类空数据 |

**5 个新路由壳的 EmptyState 选择**：

| 路由 | type | 标题 | CTA |
|---|---|---|---|
| `/admin/questions` | `data` | "题库管理 · 即将上线" | 返回 Dashboard |
| `/admin/sync` | `data` | "手动同步 · 即将上线" | 返回 Dashboard |
| `/ai/today` | `data` | "AI 今日推荐" | 查看 Dashboard AI 卡 |
| `/ai/history` | `vault` | "推送历史" | 返回 Dashboard |
| `/settings` | `data` | "设置" | 返回 Dashboard |

#### 3.8.3 Error 状态

```
┌────────────────────────────────────┐
│            ⚠️                       │
│        加载失败                      │
│   服务暂时不可用，请稍后重试          │
│        [重试]                       │
│  （错误码：INTERNAL_ERROR · 0x1a2b3c）│
└────────────────────────────────────┘
```

- **图标**：红色三角警告 SVG
- **标题**：`text-red-300` `text-2xl font-bold`
- **描述**：`text-gray-400`
- **CTA**：`bg-red-500/10 text-red-300 border-red-500/20`（区别于普通 EmptyState）
- **错误码**：5xx 显示（便于用户截图报错），4xx 不显示（避免暴露内部细节）

---

## 4. KnockWise 品牌 token（V3.8 新增 · 替换旧品牌）

### 4.1 品牌名变更

| 元素 | V1/V3 旧品牌 | V3.8 新品牌 |
|---|---|---|
| 登录页标题 | "KnockWise" | "KnockWise" |
| Dashboard 顶部 logo | "KnockWise" | "KnockWise" |
| Profile 顶部 logo | "KnockWise" | "KnockWise" |
| interview top bar | "KnockWise" | "KnockWise" |
| mockup.html 全部 logo | "Intervue" × 3 | "KnockWise" × 3 |
| README.md H1 | "# KnockWise" | "# KnockWise" |
| package.json `name` | "knockwise-frontend" | "knockwise-frontend" |
| localStorage key | `knockwise_token` / `knockwise_setup` | `knockwise_token` / `knockwise_setup`（+ 双 key fallback） |
| 后端 logger 名字 | `knockwise.*` (40 处) | `knockwise.*` |
| 后端 FastAPI title | "KnockWise" | "KnockWise" |
| docker-compose DB | knockwise | knockwise（新部署生效） |
| scripts PID/log 文件 | `/tmp/intervue-*` | `/tmp/knockwise-*` |
| CLAUDE.md 项目名 | "Intervue" | "KnockWise"（路径不动）|
| Skill 文档 | "Intervue (KnockWise)" | "KnockWise" |

**完整 70+ 处清单**见 [spec.md §6](spec.md)。

### 4.2 视觉 token 不变（沿用 V3）

> ⚠️ KnockWise 是**纯文案改名**，视觉风格（颜色/布局/动效）完全沿用 V3 已建立的 token。

| Token | 值 | 备注 |
|---|---|---|
| 主色 | `#6366f1`（indigo-500）| V3 既有 |
| 强调色 | `#a78bfa`（violet-400）| V3 既有 |
| 警告色 | `#f59e0b`（amber-500）| V3 既有 |
| 错误色 | `#f87171`（red-400）| V3 既有 |
| 背景深蓝黑 | `#050914` | V3 既有 |
| 玻璃拟态 | `rgba(15, 20, 40, 0.7)` + `backdrop-filter: blur(20px) saturate(180%)` | V3 既有 |
| 字号 / 字重 / 间距 | V3 design-spec §6.2-§6.3 | V3 既有 |

**UE 同事无需重画 Figma**，只改 logo 文字。

### 4.3 Admin 分组视觉（V3.8 新增）

**与其他分组的差异**：

| 维度 | 5 大分组（普通） | Admin 分组（V3.8 新增）|
|---|---|---|
| 标题颜色 | `--color-text-tertiary`（灰）| `#f59e0b`（琥珀色）|
| 徽章 | `sidebar-badge`（indigo 半透明）| `tag-admin`（amber 半透明）|
| 入口图标颜色 | 灰白 | **琥珀色描边**（`#f59e0b`）|
| 可见性 | 所有登录用户可见 | **仅 user_id=1 admin 可见**（产品视角）|

---

## 5. 视觉规范汇总（UE 同事复用）

### 5.1 颜色

```css
/* 品牌色（V3 既有 · 不变） */
--color-primary: #6366f1;        /* 主色 indigo-500 */
--color-primary-hover: #4f46e5;  /* 主色 hover indigo-600 */
--color-knockwise: #6366f1;       /* KnockWise 主色（同主色）*/
--color-knockwise-accent: #a78bfa; /* KnockWise 辅色 violet-400 */

/* 文字层级 */
--color-text-primary: #f8fafc;
--color-text-secondary: #94a3b8;
--color-text-tertiary: #64748b;

/* Hero 卡渐变（V3.8 新增）*/
--grad-hero: linear-gradient(135deg, rgba(244,114,182,0.15) 0%, rgba(236,72,153,0.12) 50%, rgba(168,85,247,0.15) 100%);

/* StatsBar 渐变（V3.8 新增）*/
--grad-stats: linear-gradient(135deg, rgba(99,102,241,0.04) 0%, rgba(168,85,247,0.04) 100%);

/* 状态色（V3 既有）*/
--color-success: #34d399;
--color-warning: #fbbf24;
--color-error: #f87171;
```

### 5.2 字号 / 字重（V3 既有 + V3.8 新增）

```
H1（页面标题）：24px / 700
H2（卡片标题）：18px / 600
H3（小标题）：16px / 600
正文：14px / 400
辅助：12px / 400
统计数字：36px / 700（Stat 卡）

🆕 V3.8 新增：
HeroCard 大标题：30px / 700（text-3xl font-bold）
HeroCard 主按钮文字：16px / 600
StatsBar 数值：24px / 700（text-2xl font-bold stat-num）
breadcrumb：16px / 600
```

### 5.3 间距（V3 既有）

```
卡内边距：28px（玻璃卡） / 48px（Hero 大卡）
卡间距：32px（垂直）
行间距：8px / 16px / 24px
```

### 5.4 动效（V3 既有 · V3.8 沿用）

```
ease-out: cubic-bezier(0.16, 1, 0.3, 1)        /* 0.3s */
ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1)  /* 弹性 */

skeleton-pulse: 1.8s ease-in-out infinite
```

---

## 6. 交互细节（CLAUDE.md § 阶段 1 必填 · 状态机）

### 6.1 HeroCard 状态机（5 状态）

```
[initial]
   ↓
[loading] ←── API 调用中
   ↓
   ├─→ [full]   ← API 返回 ≥3 面试 completed
   ├─→ [partial] ← API 返回 1-2 面试
   ├─→ [empty]  ← API 返回 0 面试
   └─→ [error]  ← API 返回 4xx/5xx（非 401）

任意状态 → [loading]（点击"重试"或刷新页面）
[error] → [loading]（点击"重试"）
```

### 6.2 Sidebar 状态机

```
[desktop expanded 240px] ← 初始（>1024px）
   ↓ 点击折叠按钮
[desktop collapsed 64px]
   ↓ 点击展开按钮
[desktop expanded 240px]

[mobile hidden] ← 初始（<1024px）
   ↓ 点击汉堡按钮
[mobile drawer open 240px]
   ↓ 点背景 / ESC / 点菜单（路由切换）
[mobile hidden]
```

### 6.3 5 个新路由壳状态机

```
[loading]  ← 进入页面
   ↓
   ├─→ [empty] ← API 返回 0 数据（如题库为空）
   ├─→ [data]  ← API 返回数据
   └─→ [error] ← API 失败
```

---

## 7. 视觉规范验证（CLAUDE.md § 阶段 2 · 阶段 4 完成定义）

### 7.1 视觉自检清单

- [ ] Sidebar 5 大分组 + Admin 分组颜色区分清晰
- [ ] HeroCard 5 状态视觉区分明显（full/partial/empty/loading/error）
- [ ] StatsBar 5 列对齐整齐 + tabular-nums 等宽数字
- [ ] RadarMini 3 色梯度清晰（粉/紫/蓝）+ partial 占位虚线
- [ ] TopNav 极简 · 无 7 tab 横条 · KnockWise logo + breadcrumb + 用户
- [ ] 移动端 < 1024px Sidebar 默认隐藏 + 汉堡按钮可唤出
- [ ] KnockWise logo 3 候选可点击选中 + 多尺寸预览清晰
- [ ] 5 个新路由壳 EmptyState 视觉一致 + CTA 都返回 Dashboard
- [ ] Error 状态红色三角 + 错误码 + 重试按钮
- [ ] Skeleton pulse 1.8s 动画流畅（pulse 50% 透明度）
- [ ] 折叠动画 0.3s ease-out 过渡平滑

### 7.2 与 v3-mockup.html 对照（参考标准）

- V3.0 mockup 17 page 视觉 ✅ 全部对齐
- V3.6 Sidebar 视觉（V3 design-spec §3.6 已写）✅ 沿用
- V3.8 HeroCard + StatsBar + RadarMini（本文档新加）✅ 完整定义

### 7.3 与 mockup/v38-mockup.html 一致性

- 所有 V3.8 视觉规范都已在 mockup 中实现
- 5 状态切换器可在 mockup 顶部交互切换
- Logo 3 候选可点击选中
- 移动端 drawer 缩小浏览器窗口可见

---

## 8. AI vs 人分工（CLAUDE.md § 设计阶段）

### 8.1 AI 负责（本次设计阶段已完成）

- ✅ HeroCard / StatsBar / RadarMini / 5 路由壳 EmptyState / 移动端 drawer 视觉规范
- ✅ 5 状态机定义
- ✅ 视觉 token 沿用 V3
- ✅ 可点击 mockup（v38-mockup.html · 1491 行）
- ✅ KnockWise 品牌资产 brief（ue-brief.md §1.1）

### 8.2 UE 同事负责（待办 · [ue-brief.md](ue-brief.md) 12 张图）

- 🔴 P0 4 张：Logo 3 候选 / Dashboard 重构后完整预览 / Sidebar 全景 / 折叠双态
- 🟡 P1 6 张：HeroCard 5 态 / StatsBar / RadarMini / 5 路由壳 / Dashboard 三态对比 / TopNav
- 🟢 P2 2 张：品牌系统 / 错误流程

### 8.3 UE 出图后 AI 实施

按 [ue-brief.md §5.1 出图顺序](ue-brief.md) 排优先级 → UE 出图 → AI 按图实施 → playwright 截图测试基线 = UE 图

---

## 9. 🎯 硬性 DOD（design-spec.md 完成必须全过）

- [x] §0 全局架构图（CLAUDE.md §1.5 强制 ✅）
- [x] §1 用户旅程（视觉视角）
- [x] §2 页面地图 17 page 全列出 + 路由映射
- [x] §3 V3.8 新组件视觉规范（HeroCard / StatsBar / RadarMini / TopNav / 5 入口 / 折叠 drawer / Logo 3 候选）
- [x] §4 KnockWise 品牌 token 替换方案
- [x] §5 视觉规范汇总（UE 同事复用）
- [x] §6 交互细节状态机（HeroCard 5 态 + Sidebar 折叠 + 路由壳）
- [x] §7 视觉自检清单
- [x] §8 AI vs 人分工
- [x] 可点击 mockup（mockups/v38-mockup.html）
- [x] UE brief（ue-brief.md 12 张图）
- [x] 引用 V3 design-spec §3.6 Sidebar 不重复

---

## 10. 📚 相关文档

- [research.md](research.md) — 11 章节调研 · 修订方案 17h · 7 项补调研
- [product-doc.md](product-doc.md) — 用户视角 · 4 场景 · 业务规则 · KnockWise 品牌 brief
- [spec.md](spec.md) — 技术契约 · 6 组件 Props · /recent API · KnockWise 迁移 70+ 处
- [ue-brief.md](ue-brief.md) — 12 张图 brief · UE 同事出图清单
- [mockups/v38-mockup.html](mockups/v38-mockup.html) — 1491 行可点击 SPA mockup
- V3 design-spec §3.6 — Sidebar 视觉规范（已写，本文不重复）
- V3 mockup `../2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html` — V3 既有视觉参照
- CLAUDE.md §1.5 架构图 · §1.6 产品/技术分文件 · § 一.三 阶段 1 必填 · § 一.7 重构路径