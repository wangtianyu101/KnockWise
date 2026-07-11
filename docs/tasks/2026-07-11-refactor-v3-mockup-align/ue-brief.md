---
title: UE 同事出图 brief · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [ue-brief, 设计协作, v3-mockup-align, knockwise]
related:
  - [research.md](research.md) — 上游调研（11 章节 · 17h 路径）
  - [product-doc.md](product-doc.md) — 上游产品脑（用户视角）
  - [spec.md](spec.md) — 上游技术契约
  - V3 design-spec: [../2026-07-09-new-feature-question-bank-expand/design-spec.md](../2026-07-09-new-feature-question-bank-expand/design-spec.md) — 视觉规范
  - V3 mockup: [../2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html](../2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html) — 现有 mockup HTML
---

# UE 同事出图 brief · KnockWise 前端对齐重构

> **目的**：本次重构涉及 ~9 个新组件 + 全局导航 + KnockWise 品牌资产，需要 UE 同事出一组设计图供 AI 开发对齐 + UE 设计师后续打磨。
>
> **AI 能力边界**：本仓库由单人独立开发者 + AI 承担 PM/研发/设计（见 [user-team-structure.md](../../CLAUDE.md)），UE 同事支援出图。如果用户已有 UE 工具（Figma / Sketch / 即时设计）可直接按本 brief 出图；若没有，本 brief 也可作为 AI 用 ASCII art / SVG 实现视觉的参照。
>
> **优先级**：🔴 P0 必出 4 张 / 🟡 P1 应出 6 张 / 🟢 P2 可出 2 张

---

## 0. 全局规范（所有图都要遵守）

### 0.1 品牌

- **品牌名**：KnockWise（统一文案，无 Intervue / DevBrain / CodeMock 残留）
- **品牌色**：主色 `#6366f1`（indigo-500）+ 强调色 `#a78bfa`（violet-400）+ 警告色 `#f59e0b`（amber-500）
- **背景**：深蓝黑 `#050914` + 玻璃拟态（`rgba(15, 20, 40, 0.7)` + `backdrop-filter: blur(20px) saturate(180%)`）

### 0.2 视觉 token 引用

> 全部 token 见 V3 design-spec §6.1-§6.4。**不要新创色 / 字号 / 间距**，沿用 V3 已建立的 token。

### 0.3 输出格式

| 资产 | 格式 | 尺寸 |
|---|---|---|
| Logo | SVG + PNG（多尺寸）| 28×28 / 56×56 / 200×200 / 1200×630（OG 图）|
| Page mockup | Figma frame 或 PNG | 1440×900（desktop）/ 768×1024（tablet）/ 375×812（mobile）|
| 组件细节 | Figma frame 或 SVG | 800×600（HeroCard）/ 600×200（StatsBar）/ 240×240（RadarMini）|
| 状态图 | Figma frame | 4 个状态并排：loading / empty / error / success |

### 0.4 交付方式

- Figma 文件：新建 `KnockWise 设计系统 v1` 文件，所有图放进 `Refactor V3.8` page
- 导出 PNG：放到 `docs/tasks/2026-07-11-refactor-v3-mockup-align/mockups/` 目录
- 文件命名：`v38-<component>-<state>.png`（如 `v38-hero-card-desktop.png`）

---

## 1. 🔴 P0 必出（4 张 · 阻塞重构 P1-P3 实施）

### 图 1.1：KnockWise Logo 设计（3 候选）

**用途**：登录页 + Sidebar 顶部 + favicon + OG 图通用

**要求**：
- 3 个候选方向（让用户拍板）：
  - 候选 A：**敲门图标**——门 + 击打波纹 + 紫色渐变（呼应 "Knock"）
  - 候选 B：**答题卡 + 闪烁**——模拟面试瞬间 + 知识可视化
  - 候选 C：**几何抽象 K**——K 字母 + 几何线 + 紫色渐变
- 尺寸要求：每个候选出 4 个尺寸：28×28（favicon）、56×56（Sidebar）、200×200（登录页）、1200×630（OG 图）
- 单色版：白色剪影也要能识别
- 暗黑背景下用渐变彩色，亮色背景下用深色

**token 引用**：
- 主色：`#6366f1`（indigo-500）→ `#a78bfa`（violet-400）渐变
- 背景：透明（用于覆盖）

**参考**：
- 当前 login 页 SVG（code path `M8.625 12a.375...`，对话气泡 + 感叹号）—— 不要沿用，新设计

### 图 1.2：Dashboard 重构后完整预览（desktop 1440×900）

**用途**：AI 实施 Dashboard 重写（P2）时的视觉参照 · 用户验收对比

**要求**：
- 完整 Dashboard 页面：顶部 nav + 左侧 Sidebar（240px 展开）+ 主内容
- 主内容区从上到下依次：
  1. Hero 卡（粉紫渐变 · 占顶部 60% 视觉权重 · 含"开始 Mock 面试"主按钮 + 上次成绩 3 栏 + 3 个迷你雷达）
  2. 5 列横条统计（本周答题/命中率/待复习/连续打卡/已完成）
  3. 3 列核心卡：AI 推荐（粉紫）+ 每日挑战（橙黄）+ 当前计划（绿青）
  4. 5 列 module-quick-link（学/复习/计划/画像/题单）
- 所有数据填示例数据（如"78/100 · 字节 · 后端"等）
- 标注 5 大信息密度层次（Hero > 横条 > 核心卡 > 入口 > 边角）
- 标出当前 active 的 Sidebar 项（"今日概览"）

**token 引用**：
- 全部 token 见 V3 design-spec §6
- 渐变参考：mockup L981 (`linear-gradient(135deg, rgba(244,114,182,0.15) 0%, rgba(236,72,153,0.12) 50%, rgba(168,85,247,0.15) 100%)`)

### 图 1.3：Sidebar 5 大分组 + 17 page 全景图（desktop 1440×900 + 200px 切片）

**用途**：AI 实施 Sidebar 6 组件（P1）时的导航结构参照

**要求**：
- 左侧 Sidebar 完整展开（240px），含 5 大分组 + Admin 分组 + 分隔线
- 当前激活项高亮（indigo 左边条 + 浅紫背景）
- 显示 V3 徽章：今日面试 [新] / 学习计划 [V3] / 精选题单 [V3] / 今日推荐 [V3]
- 显示 Admin 徽章：题库管理 🆕 / 手动同步 🆕
- 顶部 logo + 折叠按钮 + 搜索框
- 底部 V3 沉淀层状态
- 列出全部 14 个主菜单项 + 2 个 Admin 项 = 16 个可见入口（mockup §sidebar 锁定）

**标注要求**：
- 用箭头标注每个菜单对应的 page URL（如 `/dashboard`、`/interview/profile` 等）
- 用颜色标注分组归属（5 色：概览蓝 / 面试粉 / 学习紫 / 知识库绿 / AI 推送橙 / Admin 琥珀）

### 图 1.4：Sidebar 折叠态 + 移动端 drawer 双状态对比（1200×600）

**用途**：AI 实施 Sidebar 折叠 + drawer 切换（P1）时的状态参照

**要求**：
- **左侧**：desktop 折叠态（64px，仅图标）
- **右侧**：mobile < 1024px drawer（汉堡按钮唤出 + 半透明背景）
- 标注动画曲线（`cubic-bezier(0.16, 1, 0.3, 1)`）+ 时长 0.3s
- 标注折叠/展开过渡的 width 变化（240px ↔ 64px）
- drawer 模式标注 `transform: translateX(-100%) ↔ translateX(0)`
- 显示 ESC 关闭 + 点背景关闭 + lock body scroll 三种交互

---

## 2. 🟡 P1 应出（6 张 · 阻塞 P2/P3 视觉细节）

### 图 2.1：HeroCard 5 状态变体（800×600 · 5 个 160×120 子图）

**用途**：AI 实现 HeroCard 三态视觉（loading/empty/error/partial/full）

**5 个状态**：
1. **loading**：骨架屏（灰色 pulse 占位框 + 保留 5 列 grid 布局）
2. **empty**：新用户 0 面试 → "还没有面试记录" EmptyState + "开始第一次面试" CTA
3. **partial**：1-2 次面试 → 显示 1-2 个雷达 + "上次 78分" + 空位用灰色五边形占位
4. **full**：3+ 次面试 → 完整 3 个雷达（粉/紫/蓝）+ 上次成绩 + 主按钮
5. **error**：API 5xx → 红色感叹号 + "服务暂时不可用" + "重试" CTA

### 图 2.2：StatsBar 5 列数据可视化（800×200）

**用途**：AI 实施 StatsBar 组件的视觉对齐

**要求**：
- 5 列横条（本周答题/命中率/待复习/连续打卡/已完成）
- 每列显示：label（小写大灰） + value（大字号等宽数字） + trend（绿色/琥珀色/灰色 + 文字）
- 中间用 `divide-x divide-white/5` 分隔线
- 标注每个数值的 tabular-nums 等宽字体特性
- 数据示例：28 / 82% / 14 / 7天 / 56/200

### 图 2.3：RadarMini 3 色对比（600×200 · 3 个 200×200）

**用途**：AI 实施 RadarMini SVG 的视觉对齐

**要求**：
- 3 个 80×80 SVG 雷达并排
- 颜色梯度：粉（`#f472b6` 字节）/ 紫（`#a78bfa` 阿里）/ 蓝（`#60a5fa` 腾讯）
- 每个雷达显示：5 边形外框（15% 透明度灰）+ 数据多边形（25% 透明度填充 + 1.5px 描边）
- 数据差异：78 / 68 / 62（雷达多边形大小不同）
- 下方分数（tabular-nums）+ 公司名

### 图 2.4：5 个新路由壳 EmptyState 占位（1200×400 · 5 个 240×400）

**用途**：AI 实施 5 个新路由壳（P3）的 EmptyState 视觉对齐

**要求**：
- 5 个新路由：/admin/questions · /admin/sync · /ai/today · /ai/history · /settings
- 每个路由显示：EmptyState type + 标题 + 描述 + CTA 按钮
- 类型选择：
  - `/admin/questions` type=data 标题="题库管理 · 即将上线"
  - `/admin/sync` type=data 标题="手动同步 · 即将上线"
  - `/ai/today` type=data 标题="AI 今日推荐"
  - `/ai/history` type=vault 标题="推送历史"
  - `/settings` type=data 标题="设置"
- CTA 都是"返回 Dashboard" 按钮（indigo 主题）

### 图 2.5：Dashboard 三态对比图（1200×900 · 3 个 400×900）

**用途**：AI 实施 useAsyncData Hook 模式 + 错误处理（spec §7.3）的视觉对齐

**要求**：
- 完整 Dashboard 在 3 种状态下的截图：loading / error / success
- loading 状态：所有卡显示 skeleton（HeroCardSkeleton / StatsBarSkeleton / RadarMiniSkeleton）
- error 状态：所有卡显示 EmptyState（4xx/5xx 区分文案）
- success 状态：完整内容（如 §1.2）
- 标注每种状态下的可点击元素（如 error 时主按钮禁用）

### 图 2.6：TopNav 极简版（1440×56）

**用途**：AI 实施 TopNav 极简化的视觉对齐

**要求**：
- 横向 nav 高度 56px，背景 `rgba(5, 9, 20, 0.85)` + backdrop-blur
- 左侧：KnockWise logo + 当前 page 名（如"今日概览"）
- 右侧：用户头像 + 用户名 + 退出按钮
- 不再有 7 tab 横向菜单（全部移到 Sidebar）
- 移动端 < 1024px 时额外显示汉堡按钮（用于唤出 Sidebar drawer）

---

## 3. 🟢 P2 可出（2 张 · 不阻塞 · 锦上添花）

### 图 3.1：KnockWise 完整品牌系统（1200×800）

**用途**：项目 README + 文档封面 + OG 分享图通用

**要求**：
- 品牌资产一图汇总：logo + 主色 + 辅助色 + 字体示例 + KnockWise 标语
- 标语候选：
  - "Knock on AI, master the interview"（英文）
  - "敲开 AI 大门，掌握每一次面试"（中文）
- 排版：12 列 grid，logo 占左上，标语占中央，色板占右下
- 1200×630 尺寸另出一版作为 OG 分享图

### 图 3.2：错误状态完整流程图（1200×600 · 流程图）

**用途**：spec §7.3 三态视觉规范的补充 · 团队理解错误处理路径

**要求**：
- 流程图：用户操作 → API 调用 → 4 种响应分支
  - 200 OK → 渲染数据
  - 401 → router.push("/")
  - 422 → EmptyState + 参数错误
  - 5xx → EmptyState + 服务错误 + 重试 CTA
  - 网络断开 → EmptyState + 网络错误
- 标注每种分支对应的代码（apiGet 抛错模式）
- 标注每种分支对应的视觉（EmptyState type / 文案 / CTA 颜色）

---

## 4. 输出清单汇总

| # | 图名 | 尺寸 | 优先级 | 阻塞阶段 |
|---|---|---|---|---|
| 1.1 | KnockWise Logo × 3 候选 × 4 尺寸 | SVG + PNG | 🔴 P0 | P1 Sidebar + P2 Dashboard |
| 1.2 | Dashboard 重构后完整预览（desktop） | 1440×900 | 🔴 P0 | P2 Dashboard |
| 1.3 | Sidebar 5 大分组 + 16 入口全景 | 1440×900 + 200px 切片 | 🔴 P0 | P1 Sidebar |
| 1.4 | Sidebar 折叠 + drawer 双状态 | 1200×600 | 🔴 P0 | P1 Sidebar |
| 2.1 | HeroCard 5 状态变体 | 800×600 | 🟡 P1 | P2 HeroCard |
| 2.2 | StatsBar 5 列数据 | 800×200 | 🟡 P1 | P2 StatsBar |
| 2.3 | RadarMini 3 色对比 | 600×200 | 🟡 P1 | P2 RadarMini |
| 2.4 | 5 个新路由壳 EmptyState | 1200×400 | 🟡 P1 | P3 5 路由 |
| 2.5 | Dashboard 三态对比 | 1200×900 | 🟡 P1 | P2 useAsyncData |
| 2.6 | TopNav 极简版 | 1440×56 | 🟡 P1 | P4 去 nav |
| 3.1 | KnockWise 完整品牌系统 | 1200×800 | 🟢 P2 | 文档/分享 |
| 3.2 | 错误状态完整流程图 | 1200×600 | 🟢 P2 | 团队理解 |

**总计**：4 P0 + 6 P1 + 2 P2 = **12 张图**

---

## 5. 协作流程

### 5.1 出图顺序（按 P1 → P2 → P3 实施依赖）

```
P0 图 1.1 Logo ──────────┐
                          ├─→ P1 Sidebar 实施（P1 PR）
P0 图 1.3 Sidebar 全景 ──┤
P0 图 1.4 Sidebar 双态 ──┘

                          ┌─→ P2 Dashboard 实施（P2 PR）
P0 图 1.2 Dashboard ─────┤
                          │
P1 图 2.1 HeroCard 5 态 ─┤
P1 图 2.2 StatsBar ─────┤
P1 图 2.3 RadarMini ────┤
P1 图 2.5 三态对比 ─────┘

                          ┌─→ P3 5 路由实施（P3 PR）
P1 图 2.4 EmptyState 5 路由 ─┘
```

### 5.2 反馈机制

- UE 出图后 → 放入 `docs/tasks/.../mockups/` 目录 → AI 评审（核对 token 一致性）
- 不一致处打回重出（避免视觉漂移）
- 一致处 → AI 按图实施（Playwright 截图测试基线 = UE 图）

### 5.3 时间预算

- 🔴 P0 4 张：UE ~2 天
- 🟡 P1 6 张：UE ~3 天
- 🟢 P2 2 张：UE ~1 天（可与开发并行）
- **总 ~6 天**

如用户无 UE 资源：本 brief 同时作为 AI 用 ASCII art / SVG 实现的视觉参照（每个 ASCII 块都可直接翻译为 JSX）。

---

## 6. 引用

- [product-doc.md](product-doc.md) §3.5 KnockWise 品牌资产 brief
- [spec.md](spec.md) §3 组件契约 + §7.3 三态视觉
- V3 design-spec §3.7 + §6.4 视觉规范
- V3 mockup §页面 1 (`../2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html` L981-1321)
- CLAUDE.md §四"个人独立开发者 + 同事出 UE"