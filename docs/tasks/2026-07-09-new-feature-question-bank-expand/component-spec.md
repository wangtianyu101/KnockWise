---
title: 组件设计 · V3 题库扩量 + 多维分类 + LeetCode 三件套
date: 2026-07-09
status: v1
tags: [component-spec, 2步, 组件, v3, React, TypeScript]
related:
  - [api-spec.md](api-spec.md) — 2 步 API
  - [design-spec.md](design-spec.md) — 1 步设计脑
  - V2 沉淀层 component-spec: `../2026-06-28-new-feature-v2-smart-sediment/component-spec.md`
  - V1 learn 组件现状：`frontend/components/learn/`（已存在）
---

# 组件设计：V3 题库扩量 + 多维分类 + LeetCode 三件套

> **目标**：V3 新增 3 个核心组件（TagFilter / CollectionCard / DailyChallengeCard）+ 复用 V1/V2 既有组件。
> **风格**：V2 沉淀层 + V3 视觉层次（玻璃拟态 · 渐变 · glow · 弹簧动效）。
> **技术栈**：React 18 + TypeScript 5 + Tailwind CSS 3 + antd 5（V2 已装）+ recharts 2.15（V2 已装）。

---

## 0. 组件清单总览

| 组件 | 状态 | 路径 | 视觉文件 | 复用 V1/V2 |
|---|---|---|---|---|
| **`<TagFilter>`** | 🆕 V3 新增 | `frontend/components/v3/TagFilter/` | design-spec §3.4 | ❌ 全新 |
| **`<CollectionCard>`** | 🆕 V3 新增 | `frontend/components/v3/CollectionCard/` | design-spec §3.2 | ❌ 全新 |
| **`<DailyChallengeCard>`** | 🆕 V3 新增 | `frontend/components/v3/DailyChallengeCard/` | design-spec §3.3 | ❌ 全新 |
| `<PlanCard>` | V3 复用 | `frontend/components/learn/PlanCard/` | V1 既有 | ✅ 复用 V1 |
| `<AIRecommendationCard>` | V3 复用 | `frontend/components/v2-settlement/AIRecommendationCard/` | design-spec §3.5 | ✅ 复用 V2 |
| `<GlassCard>` `<StatCard>` | V3 复用 | `frontend/components/shared/` | V1 既有 | ✅ 复用 V1 |

**V3 新增：3 组件 · 复用 V1/V2：6 组件**

---

## 1. `<TagFilter>`（V3 新增 · 多维标签筛选器）

### 1.1 用途
- 用于 `/learn` 和 `/review` 页面顶部
- 支持 A（面试方向）+ B（技术栈）+ C（公司轮次）三维多选
- 实时调用 `/api/learn/questions?tags=...` 筛选

### 1.2 Props

```typescript
interface TagFilterProps {
  /** 当前已选中的标签 ID 列表（受控） */
  selectedTags: string[];

  /** 标签变更回调（多选 OR 逻辑） */
  onChange: (tags: string[]) => void;

  /** A 维度标签（面试方向）· 默认 4 个 */
  directionTags?: TagOption[];

  /** B 维度标签（技术栈）· 默认 6 个 */
  stackTags?: TagOption[];

  /** C 维度标签（公司轮次）· 默认 4 个 */
  companyTags?: TagOption[];

  /** 是否折叠（移动端默认 true） */
  collapsed?: boolean;
}

interface TagOption {
  id: string;           // 'sys_algorithm' / 'sys_python' / 'sys_bytedance_r2'
  label: string;        // '算法' / 'Python' / '字节-二面'
  count?: number;       // 可选：标签下题目数（性能优化用 cache）
}
```

### 1.3 State

```typescript
interface TagFilterState {
  // 内部状态：无（完全受控）
}
```

### 1.4 Events

| 事件 | 触发 | 携带 |
|---|---|---|
| `onChange` | 用户点击 tag | `string[]` — 更新后的 tag ID 列表 |
| `onClear` | 用户点"清空" | `void` — 触发 `onChange([])` |

### 1.5 依赖

```typescript
// 标签数据：useSWR 调 GET /api/learn/tags?is_system=true
// 题目列表：父组件调 GET /api/learn/questions?tags=...
// 实时筛选：onChange → 父组件 setSelectedTags → SWR mutate
```

### 1.6 视觉规范（设计 token）

| 元素 | 规范 |
|---|---|
| 容器 | `flex flex-wrap gap-2` · padding `0` |
| 维度分组标签 | `text-xs text-gray-500 mr-1` · 11px 字 |
| Tag 默认 | `bg: rgba(148,163,184,0.06)` · `text-secondary` · 圆角 6px · 4-10px padding |
| Tag A 维度选中 | `bg: rgba(96,165,250,0.2)` · `text: #93c5fd` · `border: rgba(96,165,250,0.5)` |
| Tag B 维度选中 | `bg: rgba(167,139,250,0.2)` · `text: #c4b5fd` · `border: rgba(167,139,250,0.5)` |
| Tag C 维度选中 | `bg: rgba(245,158,11,0.2)` · `text: #fcd34d` · `border: rgba(245,158,11,0.5)` |
| 计数 | 字号 11px · `text-tertiary` |
| hover | `bg` 提升 50% 透明度 · transform translateY(-1px) |
| 清空按钮 | `btn-ghost` · 12px 文字 |

### 1.7 5 状态 + 边界 case

| 状态 | 视觉反馈 |
|---|---|
| 默认（无选中） | 全部 tag 灰色 |
| 单选 1 个 tag | 该 tag 高亮 + 列表实时筛 |
| 多选 N 个 tag | 多个 tag 高亮 + 列表"任一命中"筛 |
| 折叠态（移动） | 维度标签默认隐藏 · 只显示"标签筛选"按钮 |
| 0 命中 | 父组件显示 Empty · TagFilter 仍正常 |

边界：
- tags 字符串格式错 → 422（V2 L4 错误格式）
- API 504 → TagFilter 不显示骨架不报错（决策 7A）

### 1.8 测试要点（9 测试点）

- [ ] 默认渲染 14 个 tag（4 方向 + 6 栈 + 4 公司）
- [ ] 点击 tag 高亮 + onChange 触发
- [ ] 多选 OR 命中
- [ ] A/B/C 三维配色正确
- [ ] 折叠态切回展开态保留选中
- [ ] 计数显示（如果有）
- [ ] 清空按钮触发 onChange([])
- [ ] 0 命中不报错
- [ ] 504 时不显示错误 UI

---

## 2. `<CollectionCard>`（V3 新增 · 精选题单卡片）

### 2.1 用途
- 用于 `/collections` 列表页
- 显示题单封面 + 完成度环形进度 + 操作按钮
- 点击进 `/collections/[id]` 详情

### 2.2 Props

```typescript
interface CollectionCardProps {
  /** 题单数据 */
  collection: QuestionCollection;

  /** 当前用户是否已订阅（决定按钮状态） */
  subscribed: boolean;

  /** 当前用户的完成度（0-1） */
  completionRate: number;

  /** 点击"开始"按钮回调 */
  onStart: (collectionId: string) => void;

  /** 点击"订阅"按钮回调 */
  onSubscribe: (collectionId: string) => void;

  /** 取消订阅回调 */
  onUnsubscribe: (collectionId: string) => void;

  /** 点击卡片整体进详情（可选） */
  onClick?: (collectionId: string) => void;
}

interface QuestionCollection {
  id: string;
  name: string;
  description?: string;
  cover_color: string;          // '#60a5fa'
  icon_emoji: string;            // '📘'
  question_count: number;        // 50
  is_system: boolean;
}
```

### 2.3 State

```typescript
interface CollectionCardState {
  // 内部状态：无（完全受控）
}
```

### 2.4 Events

| 事件 | 触发 | 携带 |
|---|---|---|
| `onStart` | 点击"开始"或"继续"按钮 | `collectionId: string` |
| `onSubscribe` | 点击"订阅 + 开始" | `collectionId: string` |
| `onUnsubscribe` | 点击"已订阅" toggle | `collectionId: string` |
| `onClick` | 点击卡片整体 | `collectionId: string`（可选） |

### 2.5 依赖

```typescript
// 完成度：completionRate prop 传入
// 订阅状态：subscribed prop 传入
// 按钮状态：done_count > 0 → "继续刷"，done_count == 0 → "开始"
// 调 API: POST /api/learn/collections/{id}/subscribe
// 调 API: DELETE /api/learn/collections/{id}/subscribe
```

### 2.6 视觉规范

| 元素 | 规范 |
|---|---|
| 卡片 | `glass-card` 玻璃拟态 + 圆角 16px |
| 已订阅标记 | `absolute top-3 left-3` · ⭐ emoji |
| 图标方块 | `w-11 h-11 rounded-xl` · 渐变背景（每题单不同色） |
| 标题 | `text-base font-semibold text-white` |
| 难度 + tag | 小尺寸 12px · 圆角 6px |
| 环形进度 | SVG 56x56 + stroke-dasharray + drop-shadow glow |
| 进度数字 | 居中 14px font-bold stat-num |
| 按钮 | 主按钮全宽 · `text-sm font-medium` |
| hover | `transform: translateY(-1px) + glow` |

### 2.7 5 状态 + 边界

| 状态 | 视觉反馈 |
|---|---|
| 未订阅 + 0 进度 | 灰色"订阅 + 开始" |
| 未订阅 + 有历史 | 灰色"订阅 + 开始"（subscribe 是新增操作） |
| 已订阅 + 0 进度 | 主按钮"开始 →" |
| 已订阅 + 有进度 | 主按钮"继续刷 →" + 进度环 |
| 加载中 | 骨架屏（不显示进度环） |

边界：
- 订阅失败 409 → toast "已订阅" + 切换按钮
- 网络断开 → 卡片正常显示，不显示错误

### 2.8 测试要点（8 测试点）

- [ ] 默认渲染封面 + 标题 + 进度环
- [ ] 未订阅点击"订阅"调用 onSubscribe
- [ ] 已订阅 + 有进度显示"继续刷"
- [ ] 已订阅 + 0 进度显示"开始"
- [ ] 进度环 stroke-dasharray 正确
- [ ] hover 阴影 + translateY
- [ ] 点击卡片进详情
- [ ] 409 错误 toast

---

## 3. `<DailyChallengeCard>`（V3 新增 · 每日一题卡）

### 3.1 用途
- 用于 `/dashboard` 顶部（V3.2）
- 显示今日 1 道固定推送题
- 含 streak 徽章 + 7 天热力图

### 3.2 Props

```typescript
interface DailyChallengeCardProps {
  /** 今日挑战数据（含题目 + 完成状态） */
  data: DailyChallengeStatus | null;

  /** 加载状态 */
  loading?: boolean;

  /** 错误状态（null = 隐藏卡） */
  error?: Error | null;

  /** 点击"开始答"回调 */
  onStart: (questionId: string) => void;

  /** 点击"完成"回调（用户答题完调） */
  onComplete: (questionId: string, score: number) => void;
}

interface DailyChallengeStatus {
  date: string;             // '2026-07-09'
  question: DailyChallengeQuestion;
  completed: boolean;       // 今日是否已答
  streak_days: number;      // 连续天数
}

interface DailyChallengeQuestion {
  id: string;
  topic: string;
  sub_topic: string;
  difficulty: number;       // 2-5
  question_text: string;
  estimated_minutes: number;
}
```

### 3.3 State

```typescript
interface DailyChallengeCardState {
  // 内部状态：score input (1-5) · 用户答题后输入
  pendingScore: number | null;
}
```

### 3.4 Events

| 事件 | 触发 | 携带 |
|---|---|---|
| `onStart` | 点击"开始答 →" | `questionId: string` |
| `onComplete` | 答题后点击"完成" | `{questionId, score}` |
| `onDismiss` | （可选）点击"×" | `void` |

### 3.5 依赖

```typescript
// 数据：useSWR 调 GET /api/learn/daily-challenge
// 完成：mutate() 调 POST /api/learn/daily-challenge/complete
// 跳转：router.push(`/learn/${questionId}`) 答完回 dashboard
```

### 3.6 视觉规范

| 元素 | 规范 |
|---|---|
| 卡片 | `glass-card` + amber 渐变 `bg: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(249,115,22,0.12))` |
| 边框 | `border-color: rgba(245, 158, 11, 0.3)` |
| 阴影 | `box-shadow: 0 0 0 1px rgba(245,158,11,0.15), 0 12px 40px rgba(245,158,11,0.2)` |
| 标题区 | 28px SVG icon + 文字 + 右上 streak 徽章 |
| streak 徽章 | `🔥 连续 N 天` · amber 渐变 + padding `6px 14px` |
| 题目标签 | topic / sub_topic / difficulty / 2 个系统 tag（V1 + V3） |
| 题目文本 | `text-lg leading-relaxed text-gray-100` · 1.7 行高 |
| 7 天热力图 | 7 个 18x18 圆角方块 · 4 档颜色（data-level） |
| 开始按钮 | `btn-primary` + `padding: 11px 22px` + `text-15 font-semibold` |
| 完成态 | `✅ 今日完成 · 连续 N+1 天` 替换按钮区 |

### 3.7 6 状态 + 边界

| 状态 | 视觉反馈 |
|---|---|
| 加载中 | 卡片骨架 + 闪烁 |
| 正常（未完成） | 完整题目 + 7 天热力图 + "开始答" |
| 正常（已完成） | ✅ 今日完成 · streak+1 |
| 跨日 23:59→0:00 | 题目自动换（按 date 切换） |
| 当日无题 | **隐藏整张卡**（V1 503 降级） |
| API 错误 | **隐藏整张卡**（决策 7A） |

边界：
- streak 跨天重置（断 1 天 → streak=0）
- 重复 complete 409 → toast"今日已答"
- 跨天题目不变（date 不变）

### 3.8 测试要点（10 测试点）

- [ ] 默认渲染题目 + streak + 7 天热力图
- [ ] 加载中显示骨架
- [ ] 点击"开始答"跳答题页
- [ ] 答题完成刷新显示 ✅
- [ ] 跨日题目切换
- [ ] 0 题时隐藏卡
- [ ] API 错误时隐藏卡
- [ ] streak 自增 +1
- [ ] streak 跨天重置
- [ ] 重复点击 complete → 409 toast

---

## 4. 复用组件（V1/V2 既有 · V3 不动）

| 组件 | 文件 | 复用方式 |
|---|---|---|
| `<PlanCard>` | `frontend/components/learn/PlanCard/` | V3.0 学习计划补全 · 复用完整 |
| `<AIRecommendationCard>` | `frontend/components/v2-settlement/AIRecommendationCard/` | V3.7 dashboard 推荐卡 · 复用完整 |
| `<GlassCard>` | `frontend/components/shared/GlassCard/` | V3 卡片基类 · 复用 |
| `<StatCard>` | `frontend/components/shared/StatCard/` | V3 dashboard stat · 复用 |
| `<EmptyState>` | `frontend/components/shared/EmptyState/` | V3 0 命中空状态 · 复用 |
| `<Sidebar>` | `frontend/components/v3/Sidebar/` | V3.6 整体架构 · 复用 design-spec §3.6 |

---

## 5. 目录结构（V3 新增）

```
frontend/components/
├── v3/                              # V3 新增组件（3 个 + Sidebar）
│   ├── TagFilter/
│   │   ├── index.tsx
│   │   ├── TagFilter.test.tsx
│   │   ├── types.ts                 # TagFilterProps / TagOption
│   │   └── hooks.ts                 # useTagFilter 内部状态
│   ├── CollectionCard/
│   │   ├── index.tsx
│   │   ├── CollectionCard.test.tsx
│   │   ├── types.ts                 # CollectionCardProps / QuestionCollection
│   │   └── hooks.ts                 # useSubscribeToggle
│   ├── DailyChallengeCard/
│   │   ├── index.tsx
│   │   ├── DailyChallengeCard.test.tsx
│   │   ├── types.ts                 # DailyChallengeCardProps / DailyChallengeStatus
│   │   └── hooks.ts                 # useStreak
│   └── Sidebar/                     # V3.6 整体架构
│       └── (见 design-spec §3.6)
├── v2-settlement/                   # V2 沉淀层（复用）
│   ├── DailySummaryCard/
│   ├── ProfilePage/
│   ├── RecentSedimentsCard/
│   └── AIRecommendationCard/        # V3.7 复用
├── learn/                           # V1 既有（V3 复用）
│   ├── PlanCard/                    # V3.0 复用
│   ├── QuestionCard/
│   ├── TagFilter/                   # V1 旧版（V3 新版在 v3/ 目录）
│   └── ...
└── shared/                          # 共享组件
    ├── GlassCard/
    ├── StatCard/
    └── EmptyState/
```

---

## 6. 共享类型（V1 models + V3 扩展）

```typescript
// frontend/types/v3-question-bank.ts
export interface QuestionCollection {
  id: string;
  name: string;
  description?: string;
  cover_color: string;
  icon_emoji: string;
  question_count: number;
  is_system: boolean;
  subscribed: boolean;
  progress?: {
    done_count: number;
    completion_rate: number;
    last_question_id: string;
  };
}

export interface CollectionQuestion {
  id: string;
  topic: string;
  sub_topic: string;
  difficulty: number;
  position: number;
  completed: boolean;
}

export interface DailyChallengeStatus {
  date: string;
  question: DailyChallengeQuestion;
  completed: boolean;
  streak_days: number;
}

export interface DailyChallengeQuestion {
  id: string;
  topic: string;
  sub_topic: string;
  difficulty: number;
  question_text: string;
  estimated_minutes: number;
  tags: string[];  // V3 系统标签
}

export interface TagOption {
  id: string;
  label: string;
  count?: number;
  dimension: 'direction' | 'stack' | 'company';  // V3 A/B/C
}
```

---

## 7. 🎯 硬性 DOD（component-spec.md 完成必须全过）

- [x] 组件清单完整（3 V3 新增 + 6 复用）
- [x] 每个组件 8 段齐全（用途 / Props / State / Events / 依赖 / 视觉规范 / 状态机 / 边界 case / 测试要点）
- [x] 交互状态 ≥ 5 种（TagFilter 5 / CollectionCard 5 / DailyChallengeCard 6 = 16 状态）
- [x] 边界 case 覆盖异常路径
- [x] 测试要点明确（27 测试点 = 9+8+10）
- [x] 共享类型完整
- [x] 目录结构清晰
- [x] 复用 V1/V2 组件不重复造轮

> ✅ 工具校验：`python3 scripts/check-step.py component-spec <file>`

---

## 8. 📚 相关文档

- [plan.md](plan.md) — 2 步方案
- [api-spec.md](api-spec.md) — 2 步 API
- [db-design.md](db-design.md) — 2 步数据库
- [design-spec.md](design-spec.md) — 1 步设计脑（§3.1/§3.2/§3.3 详细 mockup）
- V1 既有 learn 组件：`frontend/components/learn/`
- V2 沉淀层组件：`frontend/components/v2-settlement/`
- 共享组件：`frontend/components/shared/`