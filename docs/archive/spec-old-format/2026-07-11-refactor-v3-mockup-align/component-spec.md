---
title: 组件详细规范 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [component-spec, 2步, 组件, v3-mockup-align, knockwise]
related:
  - [research.md](research.md) — 上游调研
  - [plan.md](plan.md) — 实施计划（P1+P2 阶段）
  - [design-spec.md](design-spec.md) — 视觉规范
  - [spec.md](spec.md) — 技术契约（Props 概览）
  - [api-spec.md](api-spec.md) — /recent 端点详细
  - 现有 shared 组件: [../../../components/shared/](../../../components/shared/) — GlassCard / StatCard / EmptyState
---

# 组件详细规范：KnockWise 前端对齐重构

> **核心结论**：**本次重构新建 9 个组件** + **新建 Layout 1 个** = **10 个新组件**。
> 全部基于现有 `shared/GlassCard`、`shared/StatCard`、`shared/EmptyState` 等 9 个共享组件复用。

---

## 0. 全局结论（CLAUDE.md §1.5 全局图）

```
┌──────────────────────────────────────────────────────────────────────┐
│                 本次重构新建组件清单（10 个）                          │
│                                                                       │
│  P1 Sidebar 6 组件                                                    │
│  ├─ Sidebar.tsx（容器 · 状态管理）                                    │
│  ├─ SidebarHeader.tsx（logo + 折叠按钮）                              │
│  ├─ SidebarSearch.tsx（搜索框 + 实时过滤）                            │
│  ├─ SidebarGroup.tsx（分组标题 + 折叠）                               │
│  ├─ SidebarItem.tsx（单项 · 含 badge + active + icon）               │
│  └─ SidebarDivider.tsx（分隔线 · 配合 Admin 分组）                    │
│                                                                       │
│  P1 Layout 1 组件                                                     │
│  └─ Layout.tsx（注入 Sidebar + TopNav + main-content）                │
│                                                                       │
│  P2 Dashboard 重写 3 组件                                             │
│  ├─ HeroCard.tsx（5 状态机 · 占 60% 视觉权重）                       │
│  ├─ StatsBar.tsx（5 列横条 · 等宽数字）                               │
│  └─ RadarMini.tsx（80×80 SVG · 5 维雷达）                             │
│                                                                       │
│  复用现有 9 个 shared 组件（不新建）：                                │
│  GlassCard / StatCard / EmptyState / CategoryBadge / MasteryBadge     │
│  ProgressBar / QualityBadge / StatusSwitcher                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. P1 Sidebar 6 组件（spec.md §3.1 概览 · 详细版）

### 1.1 `Sidebar.tsx`（容器）

#### Props

```typescript
// frontend/components/v3/Sidebar/Sidebar.tsx
export interface SidebarMenuItem {
  /** 唯一 page key，用于 active 判定 */
  page: string;
  /** 路由路径（与 onClick 二选一）*/
  href?: string;
  /** 自定义点击行为 */
  onClick?: () => void;
  /** 图标（24×24 SVG JSX）*/
  icon: React.ReactNode;
  /** 显示文字 */
  label: string;
  /** 徽章 */
  badge?: 'new' | 'v3' | { text: string; color?: string };
}

export interface SidebarMenuGroup {
  /** 分组标题（如 "概览" / "面试" / "ADMIN"）*/
  title: string;
  /** 分组图标（可选）*/
  icon?: React.ReactNode;
  /** 分组内菜单项 */
  items: SidebarMenuItem[];
  /** 文字颜色主题（默认 gray）*/
  titleColor?: string;
  /** 默认折叠 */
  defaultCollapsed?: boolean;
}

export interface SidebarProps {
  /** 当前激活的 page（用于高亮 sidebar-item）*/
  currentPage?: string;
  /** 折叠状态（受控）*/
  collapsed?: boolean;
  /** 折叠状态切换回调 */
  onCollapsedChange?: (collapsed: boolean) => void;
  /** 移动端 drawer 开关（<1024px 时使用）*/
  mobileOpen?: boolean;
  /** 移动端 drawer 关闭回调 */
  onMobileClose?: () => void;
  /** Sidebar 菜单配置 */
  groups: SidebarMenuGroup[];
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 行为

1. **折叠状态持久化**：本地存储 key `knockwise-sidebar-collapsed`（如不存在则 fallback 到 `intervue-sidebar-collapsed`）
2. **移动端 drawer 切换**：监听 `window.innerWidth < 1024` 自动切换模式
3. **键盘 ESC 关闭 drawer**：监听 keydown
4. **lock body scroll while drawer open**：drawer 打开时禁用 body 滚动

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 渲染 16 菜单项 | DOM 含 16 个 `.sidebar-item` |
| 2 | active page 高亮 | currentPage='dashboard' → 对应 item 有 `.active` class |
| 3 | 折叠按钮点击切换 collapsed | onCollapsedChange 被调用，width 变化 |
| 4 | 搜索框输入过滤 | 输入 "面试" → 只显示含 "面试" 的菜单项 |
| 5 | Admin 徽章 🆕 显示 | admin-questions/admin-sync 有 amber 色徽章 |
| 6 | 移动端 drawer 切换 | width < 1024 → 默认 transform: translateX(-100%) |

### 1.2 `SidebarHeader.tsx`

#### Props

```typescript
export interface SidebarHeaderProps {
  /** 品牌名（默认 "KnockWise"）*/
  brand?: string;
  /** Logo SVG JSX */
  logo?: React.ReactNode;
  /** 折叠状态 */
  collapsed: boolean;
  /** 折叠按钮点击 */
  onToggle: () => void;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 渲染 logo + brand 文字 | DOM 含 SVG + "KnockWise" |
| 2 | collapsed=true 时 brand 隐藏 | `.sidebar-logo` `display: none` |
| 3 | 点击折叠按钮 onToggle 被调用 | 1 次 |

### 1.3 `SidebarSearch.tsx`

#### Props

```typescript
export interface SidebarSearchProps {
  /** placeholder 文案 */
  placeholder?: string;
  /** 搜索回调（实时）*/
  onSearch: (query: string) => void;
  /** 默认值 */
  defaultValue?: string;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 输入文字触发 onSearch | 每次 input 事件 1 次调用 |
| 2 | placeholder 默认值 | "搜索页面..." |
| 3 | 清空后回到全部显示 | onSearch('') 触发 |

### 1.4 `SidebarGroup.tsx`

#### Props

```typescript
export interface SidebarGroupProps {
  /** 分组标题 */
  title: string;
  /** 分组图标 */
  icon?: React.ReactNode;
  /** 标题颜色（如 amber for Admin）*/
  titleColor?: string;
  /** 分组内容 */
  children: React.ReactNode;
  /** 默认折叠 */
  defaultCollapsed?: boolean;
  /** 受控折叠状态 */
  collapsed?: boolean;
  /** 折叠回调 */
  onCollapsedChange?: (collapsed: boolean) => void;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 渲染标题 + 子项 | DOM 含 title + children |
| 2 | 标题颜色自定义 | titleColor='#f59e0b' → 样式生效 |
| 3 | 折叠切换隐藏子项 | collapsed=true → children `display: none` |

### 1.5 `SidebarItem.tsx`（最复杂 · 含 badge + active + icon）

#### Props

```typescript
export type SidebarItemBadge = 
  | 'new'           // 预设：蓝色 "新"
  | 'v3'            // 预设：indigo 半透明 "V3"
  | 'admin'         // 预设：amber 半透明 "🆕"
  | { text: string; color?: string };  // 自定义

export interface SidebarItemProps {
  /** page key 用于 active 判定 */
  page?: string;
  /** 受控 active 状态 */
  active?: boolean;
  /** 路由路径（与 onClick 二选一）*/
  href?: string;
  /** 自定义点击 */
  onClick?: () => void;
  /** 图标 */
  icon?: React.ReactNode;
  /** 徽章 */
  badge?: SidebarItemBadge;
  /** 父级折叠时隐藏文字（仅图标）*/
  collapsed?: boolean;
  /** 显示文字 */
  children: React.ReactNode;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 行为

1. **active 判定**：
   - 受控：`active={true}` 直接加 `.active` class
   - 自动：`page === currentPage` 加 `.active` class（来自 Sidebar 上下文）
2. **路由跳转**：
   - `href` + `useRouter().push(href)`（用 Next.js Link 组件）
   - `onClick` 自定义（如打开 modal）
3. **badge 渲染**：
   - `'new'` → 蓝色徽章 "新"
   - `'v3'` → indigo 半透明 "V3"
   - `'admin'` → amber 半透明 "🆕"
   - `{ text, color }` → 自定义
4. **collapsed=true**：隐藏 `<span>` 文字 + badge，只留 icon

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | active=true → 高亮 class | `.active` 存在 |
| 2 | 点击触发 href 跳转 | router.push 被调用 |
| 3 | 点击触发 onClick | onClick 被调用 |
| 4 | badge='v3' 显示 | DOM 含 "V3" 文字 |
| 5 | badge='admin' 显示 | DOM 含 "🆕" + amber 色 |
| 6 | collapsed=true 时文字隐藏 | `<span>` `display: none` |

### 1.6 `SidebarDivider.tsx`

#### Props

```typescript
export interface SidebarDividerProps {
  /** 可选文字标签（如 "ADMIN"）*/
  label?: string;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 单纯分隔线 | DOM 含 1px 高 + bg var(--color-border) |
| 2 | 带 label | 文字显示在分隔线中 |
| 3 | label 颜色主题 | amber for Admin |

---

## 2. P1 Layout 组件

### 2.1 `Layout.tsx`

#### Props

```typescript
// frontend/components/v3/Layout/Layout.tsx
export interface LayoutProps {
  /** 当前 page 名（用于 Sidebar active 判定）*/
  currentPage?: string;
  /** Sidebar 折叠状态 localStorage key */
  storageKey?: string;
  /** 自定义 Sidebar 配置（默认用 mockup 16 入口）*/
  sidebarGroups?: SidebarMenuGroup[];
  /** 子内容 */
  children: React.ReactNode;
}
```

#### 行为

1. **全局注入 Sidebar + TopNav + main**：
   ```tsx
   <div>
     <TopNav />
     <Sidebar currentPage={currentPage} groups={sidebarGroups || DEFAULT_GROUPS} />
     <main className="main-content ml-60 lg:ml-60">
       {children}
     </main>
   </div>
   ```
2. **Sidebar 折叠状态管理**：localStorage 持久化
3. **响应式**：< 1024px 自动切 drawer 模式
4. **登录页不渲染 Layout**：用 `if (!getToken()) return <>{children}</>` 短路（详情见 §2.3）

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 渲染 Sidebar + TopNav + main | DOM 包含 3 个区域 |
| 2 | currentPage 传给 Sidebar | Sidebar 接收 prop |
| 3 | localStorage 持久化折叠 | 刷新后保持 collapsed 状态 |
| 4 | 未登录不渲染 Layout | `getToken()` null → 只渲染 children |

### 2.2 _app.tsx 修改（注入 Layout）

```tsx
// frontend/pages/_app.tsx
import type { AppProps } from "next/app";
import "@/styles/globals.css";
import { useRouter } from "next/router";
import { getToken } from "@/lib/api";
import { Layout } from "@/components/v3/Layout/Layout";

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const isAuthPage = router.pathname === "/" || router.pathname === "/onboarding";

  if (isAuthPage || !getToken()) {
    // 未登录或登录/注册页：不渲染 Layout
    return <Component {...pageProps} />;
  }

  return (
    <Layout currentPage={router.pathname}>
      <Component {...pageProps} />
    </Layout>
  );
}
```

**关键决策**：用 `router.pathname` 而非 `useEffect` 检测，避免 hydration mismatch。

### 2.3 不渲染 Layout 的路由

| 路由 | 原因 |
|---|---|
| `/`（登录页）| 独立设计，无 nav |
| `/onboarding` | 引导流程，无 nav |
| 未登录（任意路由）| 跳 `/` 之前不渲染 Layout |

---

## 3. P2 Dashboard 重写 3 组件

### 3.1 `HeroCard.tsx`

#### Props

```typescript
// frontend/components/v3/HeroCard/HeroCard.tsx
import type { InterviewRecentItem } from '@/types/interview';

export type HeroState = 'full' | 'partial' | 'empty' | 'loading' | 'error';

export interface HeroCardProps {
  /** 上次面试数据（最高分的那条）*/
  lastInterview?: InterviewRecentItem;
  /** 最近 N 次面试（用于迷你雷达）*/
  recentInterviews: InterviewRecentItem[];
  /** 总面试数（近 30 天）*/
  totalInterviews: number;
  /** 平均分（近 30 天）*/
  avgScore: number | null;
  /** 当前状态（覆盖自动判定）*/
  state?: HeroState;
  /** 加载状态 */
  loading?: boolean;
  /** 点击"开始面试"回调 */
  onStartInterview?: () => void;
  /** 点击"查看历史"回调 */
  onViewHistory?: () => void;
  /** 点击"配置面试偏好"回调 */
  onConfigInterview?: () => void;
  /** 点击"重试"回调（error 状态）*/
  onRetry?: () => void;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 状态自动判定逻辑

```typescript
function determineHeroState(props: HeroCardProps): HeroState {
  if (props.state) return props.state;
  if (props.loading) return 'loading';
  if (props.recentInterviews.length === 0) return 'empty';
  if (props.recentInterviews.length < 3) return 'partial';
  return 'full';
}
```

#### 5 状态视觉对应（spec.md §7.3 + design-spec.md §3.1.3）

| state | 视觉 | 主按钮 |
|---|---|---|
| `full` | 3 雷达 + 上次成绩 3 栏 | "开始面试 →" |
| `partial` | N 雷达 + 虚线占位 | "开始第 N 次 →" |
| `empty` | EmptyState 紫色虚线圆 | "开始第一次面试 →" |
| `loading` | skeleton pulse | 半透明 + disabled |
| `error` | 红色三角 + 错误码 | "重试" |

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | full 状态渲染 3 雷达 | DOM 含 3 个 RadarMini |
| 2 | partial 状态显示虚线占位 | DOM 含 虚线 5 边形 |
| 3 | empty 状态显示 EmptyState | 文本含 "还没有面试记录" |
| 4 | loading 状态显示 skeleton | DOM 含 `.skeleton` class |
| 5 | error 状态显示重试按钮 | 点击触发 onRetry |
| 6 | 点击"开始面试"触发 onStartInterview | 1 次回调 |
| 7 | 自动 state 判定 | recentInterviews.length 决定 full vs partial vs empty |

### 3.2 `StatsBar.tsx`

#### Props

```typescript
// frontend/components/v3/StatsBar/StatsBar.tsx
export interface StatsBarStat {
  /** 标签（如 "本周答题"）*/
  label: string;
  /** 值（如 "28" / "82%"）*/
  value: string | number;
  /** 单位（如 "次" / "天"）*/
  unit?: string;
  /** 趋势方向 */
  trend?: 'up' | 'down' | 'neutral';
  /** 趋势文字（如 "+12%" / "3 题紧急"）*/
  trendValue?: string;
  /** 趋势颜色 */
  trendColor?: 'emerald' | 'amber' | 'red' | 'gray';
  /** 趋势箭头 */
  trendArrow?: '↑' | '↓' | '→';
}

export interface StatsBarProps {
  /** 5 列数据 */
  stats: StatsBarStat[];
  /** 加载状态（显示 skeleton）*/
  loading?: boolean;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 渲染 5 列 | DOM 含 5 个 `.flex-1` |
| 2 | 数字等宽（tabular-nums） | `<p>` 含 `stat-num` class |
| 3 | trend up + emerald 色 | `<span>` class `text-emerald-400` |
| 4 | trend 警告 + amber 色 | class `text-amber-400` |
| 5 | 分隔线渲染 | `divide-x divide-white/5` |
| 6 | loading 显示 skeleton | 5 个 skeleton 占位 |

### 3.3 `RadarMini.tsx`

#### Props

```typescript
// frontend/components/v3/RadarMini/RadarMini.tsx
export type RadarColor = 'pink' | 'violet' | 'blue' | 'emerald' | 'amber';

export interface RadarMiniProps {
  /** 5 维数据（如 {algorithm: 78, system_design: 75, ...}）*/
  data: Record<string, number | undefined>;
  /** 公司名（显示在雷达下方）*/
  company?: string;
  /** 分数（显示在雷达下方）*/
  score?: number;
  /** 雷达尺寸（默认 80x80 viewBox）*/
  size?: number;
  /** 主题色 */
  color?: RadarColor;
  /** 是否占位（虚线，用于 partial 状态）*/
  placeholder?: boolean;
  /** 测试用 */
  "data-testid"?: string;
}
```

#### 颜色映射

```typescript
const COLOR_MAP: Record<RadarColor, { stroke: string; fill: string }> = {
  pink:    { stroke: '#f472b6', fill: 'rgba(244,114,182,0.25)' },
  violet:  { stroke: '#a78bfa', fill: 'rgba(167,139,250,0.25)' },
  blue:    { stroke: '#60a5fa', fill: 'rgba(96,165,250,0.25)'  },
  emerald: { stroke: '#34d399', fill: 'rgba(52,211,153,0.25)'  },
  amber:   { stroke: '#fbbf24', fill: 'rgba(251,191,36,0.25)'  },
};
```

#### 5 维顺序（与后端约定）

```typescript
const RADAR_DIMENSIONS_ORDER = ['algorithm', 'system_design', 'network', 'frontend', 'ai'] as const;
```

#### 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 渲染 5 边形外框 + 数据多边形 | SVG 含 2 个 polygon |
| 2 | color=pink 使用粉色调色 | stroke="#f472b6" |
| 3 | placeholder=true 显示虚线 | stroke-dasharray="3 3" |
| 4 | company + score 显示 | DOM 含对应文字 |
| 5 | data 为空时不渲染数据多边形 | 只渲染外框 |
| 6 | 5 维顺序固定 | polygon points 按 algorithm → ai 顺序计算 |

---

## 4. useAsyncData Hook（spec.md §7.3 详细）

### 4.1 实现

```typescript
// frontend/hooks/useAsyncData.ts（新增）
import { useState, useEffect, useCallback } from 'react';

export interface AsyncDataState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  reload: () => Promise<void>;
}

export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: any[] = []
): AsyncDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}
```

### 4.2 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | fetcher 成功返回 data | data = result |
| 2 | fetcher 抛错 error | error = Error |
| 3 | loading 初始为 true | useEffect 后变为 false |
| 4 | reload 重新触发 fetcher | 调用 2 次 |
| 5 | deps 变化重新触发 | fetcher 重新调用 |
| 6 | 组件卸载不泄漏 | cleanup 正常 |

---

## 5. 5 个新路由壳（spec.md §3.6 · 视觉详细）

### 5.1 `/admin/questions` 页

```tsx
// frontend/pages/admin/questions.tsx
export default function AdminQuestionsPage() {
  return (
    <div className="min-h-screen">
      <header className="mb-8 mt-8">
        <span className="tag tag-admin">🆕 ADMIN</span>
        <h1 className="text-3xl font-bold mb-2 mt-3">题库管理</h1>
        <p className="text-sm text-gray-400">/admin/questions · admin 后台正在开发中</p>
      </header>
      <EmptyState
        type="data"
        title="题库管理 · 即将上线"
        description="admin 后台正在开发中。届时可在此处浏览题目、改 topic / difficulty / round，配合 V3.7 题库质量监控使用。"
        ctaText="返回 Dashboard"
        onCta={() => router.push('/dashboard')}
      />
    </div>
  );
}
```

### 5.2 其他 4 路由壳（同模式）

| 路由 | type | 标题 | 描述 | CTA |
|---|---|---|---|---|
| `/admin/questions` | data | 题库管理 · 即将上线 | admin 后台正在开发中... | 返回 Dashboard |
| `/admin/sync` | data | 手动同步 · 即将上线 | 数据源同步功能即将开放... | 返回 Dashboard |
| `/ai/today` | data | AI 今日推荐 | Dashboard 顶部已有 AI 推荐卡预览... | 查看 Dashboard AI 卡 |
| `/ai/history` | vault | 推送历史 | 完成更多面试 + 答题后... | 返回 Dashboard |
| `/settings` | data | 设置 | 用户偏好设置正在开发中... | 返回 Dashboard |

### 5.3 测试矩阵

| # | 测试 | 期望 |
|---|---|---|
| 1 | 5 路由可达 | 5 个 URL 都 200 |
| 2 | EmptyState 渲染正确 | DOM 含对应标题 + CTA |
| 3 | CTA 点击跳转 Dashboard | router.push('/dashboard') 调用 |
| 4 | Sidebar active 正确 | 对应 menu item `.active` class |
| 5 | KnockWise logo 一致 | 顶部 logo + brand 都是 KnockWise |

---

## 6. 组件复用矩阵（spec.md § 1.1 · 新建组件依赖）

| 新组件 | 依赖现有 shared 组件 | 依赖新组件 |
|---|---|---|
| `Sidebar` | — | SidebarHeader/Search/Group/Item/Divider |
| `SidebarHeader` | — | — |
| `SidebarSearch` | — | — |
| `SidebarGroup` | — | — |
| `SidebarItem` | — | — |
| `SidebarDivider` | — | — |
| `Layout` | — | Sidebar |
| `HeroCard` | — | RadarMini |
| `StatsBar` | `shared/StatCard`（部分）| — |
| `RadarMini` | — | — |
| `useAsyncData` | — | — |
| `EmptyState` 复用 | `shared/EmptyState` | — |

**新建组件总依赖**：Sidebar 6 + Layout 1 + HeroCard 1 + StatsBar 1 + RadarMini 1 + useAsyncData 1 = **11 个文件**（含 1 个 hook）

**复用现有**：shared/EmptyState 5 次（5 路由壳）+ shared/StatCard 部分（StatsBar）

---

## 7. 组件文件结构

```
frontend/
├── components/
│   ├── shared/                           # 9 个 V1 closure 既有
│   │   ├── GlassCard.tsx
│   │   ├── StatCard.tsx
│   │   ├── EmptyState.tsx               # 5 路由壳复用
│   │   └── ...
│   └── v3/
│       ├── Sidebar/                      # 🆕 P1
│       │   ├── Sidebar.tsx
│       │   ├── SidebarHeader.tsx
│       │   ├── SidebarSearch.tsx
│       │   ├── SidebarGroup.tsx
│       │   ├── SidebarItem.tsx
│       │   └── SidebarDivider.tsx
│       ├── Layout/                       # 🆕 P1
│       │   └── Layout.tsx
│       ├── HeroCard/                     # 🆕 P2
│       │   └── HeroCard.tsx
│       ├── StatsBar/                     # 🆕 P2
│       │   └── StatsBar.tsx
│       ├── RadarMini/                    # 🆕 P2
│       │   └── RadarMini.tsx
│       ├── PlanCard/                     # V3.0 既有
│       ├── AIRecommendationCard/         # V3.7 既有
│       └── CollectionCard/               # V3.1 既有
├── hooks/
│   └── useAsyncData.ts                   # 🆕 P2
├── pages/
│   ├── _app.tsx                          # 🔄 P1 注入 Layout
│   ├── dashboard.tsx                     # 🔄 P2 重写
│   ├── admin/
│   │   ├── questions.tsx                 # 🆕 P3
│   │   └── sync.tsx                      # 🆕 P3
│   ├── ai/
│   │   ├── today.tsx                     # 🆕 P3
│   │   └── history.tsx                   # 🆕 P3
│   └── settings.tsx                      # 🆕 P3
└── types/
    └── interview.ts                      # 🆕 P3 InterviewRecentItem
```

---

## 8. 测试覆盖矩阵（CLAUDE.md § 一.7 重构 + § 六 单测强制）

| 组件 | 测试文件 | 测试数 | 覆盖率目标 |
|---|---|---|---|
| Sidebar | `__tests__/components/v3/Sidebar.test.tsx` | 6 | ≥ 80% |
| SidebarHeader | 同上（6 组件共 18 测试）| 3 | ≥ 80% |
| SidebarSearch | 同上 | 3 | ≥ 80% |
| SidebarGroup | 同上 | 3 | ≥ 80% |
| SidebarItem | 同上 | 3 | ≥ 80% |
| SidebarDivider | 同上 | 3 | ≥ 80% |
| Layout | `__tests__/components/v3/Layout.test.tsx` | 4 | ≥ 80% |
| HeroCard | `__tests__/components/v3/HeroCard.test.tsx` | 7 | ≥ 80% |
| StatsBar | `__tests__/components/v3/StatsBar.test.tsx` | 6 | ≥ 80% |
| RadarMini | `__tests__/components/v3/RadarMini.test.tsx` | 6 | ≥ 80% |
| useAsyncData | `__tests__/hooks/useAsyncData.test.ts` | 6 | ≥ 85% |
| 5 路由壳 | 5 个 test 文件 × 1 | 5 | smoke |
| **总计** | **13 文件** | **+62 测试** | — |

---

## 9. 状态管理决策

### 9.1 全局状态（Context）— **不引入**

**理由**：
- 当前 Sidebar 状态简单（折叠 + drawer），localStorage 持久化足够
- 不需要 Redux / Zustand
- Layout 用受控 props 即可（外部传入 currentPage）

### 9.2 局部状态（useState）— 够用

- Sidebar 折叠：`useState<boolean>` + localStorage
- HeroCard 状态：`useState<HeroState>` 或自动判定
- 表单输入：每个表单组件独立 useState

### 9.3 数据获取（useAsyncData）— 复用

- HeroCard 的 /recent 调用
- 5 路由壳的 future API 调用（暂不调）
- 任何"loading + error + data"模式

---

## 10. 风险评估

| 风险 | 等级 | 缓解 |
|---|---|---|
| Sidebar 6 组件 props 设计过度 | 🟡 中 | spec.md §3.1 已规定最小集；新增需求时再扩展 |
| HeroCard 5 状态视觉区分不明显 | 🟡 中 | design-spec.md §3.1.3 + mockup §hero-container 5 状态可点切换 |
| RadarMini 5 维顺序与后端不一致 | 🔴 高 | api-spec.md §2.1 规定 RADAR_DIMENSIONS 常量，前后端共用 |
| Layout 注入破坏 useRouter hook | 🟡 中 | 用 router.pathname 而非 useEffect，避免 hydration mismatch |
| 5 路由壳误导用户 | 🟢 低 | EmptyState 文案明确"即将上线" |

---

## 11. 关联文档

- [research.md](research.md) §9.2 17 page 业务逻辑 + §9.4 测试覆盖缺口
- [plan.md](plan.md) P1 + P2 阶段任务清单
- [design-spec.md](design-spec.md) 视觉规范（HeroCard 5 态 / Sidebar / RadarMini 等）
- [spec.md](spec.md) §3 组件 Props 概览 + §7 三态视觉
- [api-spec.md](api-spec.md) /recent 端点 + 前端类型
- [ue-brief.md](ue-brief.md) HeroCard 5 状态 / RadarMini / StatsBar 等 UE 出图 brief
- 现有 shared 组件: [frontend/components/shared/](../../../components/shared/)
- CLAUDE.md § 一.三 阶段 2/3· § 一.7 重构路径· § 六 单测强制