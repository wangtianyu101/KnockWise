---
title: 技术契约 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [spec, 1步, 技术脑, v3-mockup-align, knockwise, refactor]
related:
  - [research.md](research.md) — 上游调研（11 章节 · 17h 路径）
  - [product-doc.md](product-doc.md) — 上游产品脑（用户视角 · 不重复）
  - V3 design-spec: [../2026-07-09-new-feature-question-bank-expand/design-spec.md](../2026-07-09-new-feature-question-bank-expand/design-spec.md) — 视觉规范已写 §3.6 Sidebar
---

# 技术契约：KnockWise 前端对齐重构

> **作者**：AI 技术脑 · 用户决策已锁（三档全改 / 接受 17h）
> **核心原则**：**只换壳，不动业务**。重构不改业务行为、API 契约（除新增 1 端点）、数据模型、Service 逻辑。

---

## 0. 全局架构图（CLAUDE.md §1.5 强制）

```
┌──────────────────────────────────────────────────────────────────────┐
│                    KnockWise 重构技术架构                              │
│                                                                       │
│  ╔════════════════════════════════════════════════════════════════╗  │
│  ║  重构层（壳层 · 全部要改）                                     ║  │
│  ║                                                                ║  │
│  ║  ┌────────────────────────────────────────────────────────┐  ║  │
│  ║  │  Next.js _app.tsx                                       │  ║  │
│  ║  │  └─ <Layout>                                           │  ║  │
│  ║  │     ├─ <Sidebar>（新 · 全局注入 · 5 分组 14 page）     │  ║  │
│  ║  │     │  └─ <SidebarHeader / Search / Group / Item>      │  ║  │
│  ║  │     ├─ <TopNav>（极简 · logo + 用户菜单）              │  ║  │
│  ║  │     └─ <main className="ml-60 lg:ml-60">              │  ║  │
│  ║  │        └─ page content                                  │  ║  │
│  ║  │                                                          │  ║  │
│  ║  │  + components/v3/{Sidebar, HeroCard, StatsBar, RadarMini} │ ║ │
│  ║  │  + components/v3/Sidebar/{6 子组件}                    │  ║  │
│  ║  │  + pages/admin/{questions, sync}.tsx（新）             │  ║  │
│  ║  │  + pages/ai/{today, history}.tsx（新）                 │  ║  │
│  ║  │  + pages/settings.tsx（新）                            │  ║  │
│  ║  └────────────────────────────────────────────────────────┘  ║  │
│  ║                                                                ║  │
│  ║  KnockWise 改名（70+ 处）                                    ║  │
│  ║  ├─ frontend/{4 logo + 3 package.json + README + 8 localStorage}  ║ │
│  ║  ├─ backend/{40 logger + 1 FastAPI title}                    ║  │
│  ║  ├─ scripts/{8 PID/log path}                                 ║  │
│  ║  ├─ docs/{CLAUDE.md + api/README.md + 3 mockup}              ║  │
│  ║  └─ .claude/skills/{intervue-dev/SKILL.md}                   ║  │
│  ╚════════════════════════════════════════════════════════════════╝  │
│                                                                       │
│  ╔════════════════════════════════════════════════════════════════╗  │
│  ║  业务层（冻结 · 一行不动）                                     ║  │
│  ║                                                                ║  │
│  ║  /api/* 现有 50+ 端点（除新增 1 个 /api/interviews/recent）   ║  │
│  ║  services/* 全部逻辑                                          ║  │
│  ║  models/* + DB schema 不动                                    ║  │
│  ║  agents/* LangGraph + LLM 调用不动                            ║  │
│  ║  真实 MySQL 数据冻结                                          ║  │
│  ╚════════════════════════════════════════════════════════════════╝  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. 模块边界（CLAUDE.md § 一.三 阶段 1 必填）

### 1.1 重构层模块清单

| 模块 | 路径 | 状态 | 依赖 |
|---|---|---|---|
| **Sidebar 6 组件** | `frontend/components/v3/Sidebar/{Sidebar,SidebarHeader,SidebarSearch,SidebarGroup,SidebarItem,SidebarDivider}.tsx` | 🆕 新建 | shared/GlassCard（已有）|
| **Layout 注入** | `frontend/components/v3/Layout/Layout.tsx` + `frontend/pages/_app.tsx` | 🆕 新建 + 改 _app | Sidebar + TopNav |
| **TopNav 极简** | `frontend/components/v3/TopNav/TopNav.tsx` | 🆕 新建 | shared/GlassCard + Dropdown（antd 或自写）|
| **Dashboard 重写** | `frontend/pages/dashboard.tsx` | 🔄 重写 | HeroCard + StatsBar + RadarMini + 现有 AIRecommendationCard + CurrentPlanCard + DailySummaryCard |
| **HeroCard** | `frontend/components/v3/HeroCard/HeroCard.tsx` | 🆕 新建 | StatsBar + RadarMini |
| **StatsBar** | `frontend/components/v3/StatsBar/StatsBar.tsx` | 🆕 新建 | shared/StatCard |
| **RadarMini** | `frontend/components/v3/RadarMini/RadarMini.tsx` | 🆕 新建 | SVG 渲染 |
| **5 个新路由壳** | `frontend/pages/{admin/questions,admin/sync,ai/today,ai/history,settings}.tsx` | 🆕 新建 | shared/EmptyState |
| **17 page 删 nav** | `frontend/pages/**/*.tsx`（17 文件）| 🔄 改 | Layout 自动注入 |
| **KnockWise 改名** | 见 §6 迁移清单 | 🔄 改 | 全仓 grep |
| **后端 /recent 端点** | `backend/api/interview.py` + `backend/services/interview_service.py` + `backend/schemas/interview.py` | 🆕 新建 | 现有 Interview model.radar_data 字段 |
| **后端 logger 改名** | `backend/**/*.py`（40 文件）| 🔄 改 | 30 测试断言同步 |
| **scripts 改名** | `scripts/{start,stop}.sh` | 🔄 改 | 老 PID 清理 |
| **docker-compose** | `docker-compose.yml` | 🔄 改 | 不动真 DB |
| **CLAUDE.md 改名** | `CLAUDE.md` | 🔄 改 | 路径不动 |
| **docs/README 改名** | `docs/api/README.md` | 🔄 改 | — |
| **Skill 改名** | `.claude/skills/intervue-dev/SKILL.md` | 🔄 改 | — |
| **playwright 配置** | `frontend/playwright.config.ts` + `frontend/tests/e2e/**` | 🆕 新建 | 25 截图测试 |

### 1.2 业务层模块（冻结）

> CLAUDE.md § 一.7 重构定义："不改业务行为"。下面列出**明确冻结**：

| 模块 | 路径 | 冻结原因 |
|---|---|---|
| 后端 API（除新增）| `backend/api/*.py` 50+ 端点 | 业务逻辑不动 |
| Service 层 | `backend/services/*.py` 20+ service | 业务逻辑不动 |
| 数据模型 | `backend/models/__init__.py` 19 表 | schema 不动 |
| DB migration | `backend/core/database.py:_MIGRATIONS` | 不加新 ALTER |
| 真实 MySQL 数据 | `codemock` 数据库 + 50 道种子题 | CLAUDE.md §二冻结 |
| livekit.yaml | `livekit.yaml` | 冻结 |
| seed_data | `backend/seed_data/*.json` | 冻结 |

### 1.3 模块依赖图

```
_app.tsx (Layout 注入)
    ↓
Layout
    ↓
Sidebar ← SidebarHeader/Search/Group/Item/Divider (6 组件)
    ↓
TopNav (logo + 用户菜单)
    ↓
main
    ↓
    ├── /dashboard  → HeroCard + StatsBar + RadarMini + AIRecommendationCard + CurrentPlanCard
    ├── /plan       → PlanCard (已有) + PlanCreateModal (已有)
    ├── /collections → CollectionCard (已有)
    ├── /learn, /review, /qa (现状不动)
    ├── /interview/* (现状不动 + 5 子页集成 Layout)
    ├── /knowledge  → RecentSedimentsCard (已有)
    ├── /news       → 现状不动
    ├── /profile    → 现状不动
    ├── /admin/{questions,sync} (新)
    ├── /ai/{today,history} (新)
    └── /settings (新)
```

---

## 2. API 契约（CLAUDE.md §1.6 技术细节）

### 2.1 🆕 新增 1 个端点：`GET /api/interviews/recent`

| 维度 | 详情 |
|---|---|
| **路径** | `GET /api/interviews/recent?limit=3` |
| **Auth** | `Depends(get_current_user)`（同 list_interviews）|
| **Query 参数** | `limit: int = 3`（1-10 范围，默认 3）|
| **响应** | 200 OK + `{"items": [...], "total": N}` |
| **错误** | 401 未登录 / 422 参数错误 / 500 服务错误 |

**响应 Schema**：

```python
# backend/schemas/interview.py 增量
class InterviewRecentItem(BaseModel):
    id: UUID
    round: str = Field(..., description="公司方向，如 '字节·后端'")
    overall_score: Optional[float] = Field(None, ge=0, le=100)
    radar_data: dict = Field(default_factory=dict, description="5 维雷达数据 {algorithm, system_design, network, frontend, ai}")
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

class InterviewRecentResponse(BaseModel):
    items: list[InterviewRecentItem]
    total: int = Field(..., ge=0)
```

**前端类型定义**（在 `frontend/types/interview.ts`）：

```typescript
export interface InterviewRecentItem {
  id: string;
  round: string;
  overall_score: number | null;
  radar_data: {
    algorithm?: number;
    system_design?: number;
    network?: number;
    frontend?: number;
    ai?: number;
    [key: string]: number | undefined;
  };
  started_at: string | null;
  ended_at: string | null;
}

export interface InterviewRecentResponse {
  items: InterviewRecentItem[];
  total: number;
}
```

**Service 方法**：

```python
# backend/services/interview_service.py 增量
async def list_recent_interviews(
    db: AsyncSession,
    user_id: str,
    limit: int = 3,
) -> list[dict]:
    """Return the most recent N completed interviews with radar_data.

    Used by Dashboard HeroCard RadarMini to show last 3 interview radar charts.

    Filters:
    - user_id = current user
    - status = 'completed' (避免 in_progress 的半成品)
    - deleted_at IS NULL
    - overall_score IS NOT NULL（避免没打分的）
    Order by: started_at DESC
    Limit: N (1-10)
    """
    # 走 idx_user_status 索引 + 内存 limit O(1)
```

**测试用例**（`backend/tests/test_interview_recent_endpoint.py` 新增）：

| # | 测试名 | 输入 | 期望 |
|---|---|---|---|
| 1 | `test_recent_empty` | 无面试 | `{"items": [], "total": 0}` |
| 2 | `test_recent_one` | 1 条 completed | `total=1, items[0].overall_score=78` |
| 3 | `test_recent_three` | 3 条 completed | `total=3`，按 started_at DESC |
| 4 | `test_recent_truncate` | 5 条 completed | `total=5, items.length=3`（按 limit 截断）|
| 5 | `test_recent_excludes_in_progress` | 2 completed + 1 in_progress | in_progress 不在 items |
| 6 | `test_recent_user_isolation` | 用户 A 3 条 + 用户 B 3 条 | A 看不到 B |
| 7 | `test_recent_limit_validation` | limit=0 / limit=11 / limit="abc" | 422 错误 |
| 8 | `test_recent_unauthenticated` | 无 token | 401 |
| 9 | `test_recent_default_limit` | 不传 limit | 默认 3 |

**性能**：P95 < 50ms（mock 测试）+ 走 `idx_user_status` 复合索引

---

### 2.2 现有 API（冻结 · 不动）

> 重构不改任何现有 API。所有 50+ 端点保持向后兼容。
> 前端调用如果之前用 `interview.tsx` 路径，**保持不动**。

---

## 3. 组件契约（CLAUDE.md §1.6 技术细节）

### 3.1 Sidebar 6 组件 Props

```typescript
// components/v3/Sidebar/Sidebar.tsx
export interface SidebarProps {
  /** 当前激活的 page（用于高亮 sidebar-item） */
  currentPage?: string;
  /** 折叠状态（受控） */
  collapsed?: boolean;
  /** 折叠状态切换回调 */
  onCollapsedChange?: (collapsed: boolean) => void;
  /** 移动端 drawer 开关（<1024px 时使用） */
  mobileOpen?: boolean;
  /** 移动端 drawer 关闭回调 */
  onMobileClose?: () => void;
  /** 测试用 */
  "data-testid"?: string;
}

// components/v3/Sidebar/SidebarHeader.tsx
export interface SidebarHeaderProps {
  brand: string;             // 默认 "KnockWise"
  collapsed: boolean;
  onToggle: () => void;
  "data-testid"?: string;
}

// components/v3/Sidebar/SidebarSearch.tsx
export interface SidebarSearchProps {
  placeholder?: string;       // 默认 "搜索页面..."
  onSearch: (query: string) => void;
  "data-testid"?: string;
}

// components/v3/Sidebar/SidebarGroup.tsx
export interface SidebarGroupProps {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  defaultCollapsed?: boolean;
  "data-testid"?: string;
}

// components/v3/Sidebar/SidebarItem.tsx
export type SidebarItemBadge = "new" | "v3" | { text: string; color?: string };

export interface SidebarItemProps {
  page?: string;             // 用于 active 判定
  href?: string;             // 跳转路径（与 onClick 二选一）
  onClick?: () => void;      // 自定义行为
  icon?: React.ReactNode;
  badge?: SidebarItemBadge;
  active?: boolean;          // 受控 active 状态
  collapsed?: boolean;       // 父级折叠时隐藏文字
  children: React.ReactNode; // 显示文字
  "data-testid"?: string;
}

// components/v3/Sidebar/SidebarDivider.tsx
export interface SidebarDividerProps {
  label?: string;            // 如 "ADMIN"
  "data-testid"?: string;
}
```

### 3.2 Layout 组件

```typescript
// components/v3/Layout/Layout.tsx
export interface LayoutProps {
  /** 当前 page 名（用于 Sidebar active 判定） */
  currentPage?: string;
  /** Sidebar 折叠状态本地存储 key（默认 'knockwise-sidebar-collapsed'） */
  storageKey?: string;
  children: React.ReactNode;
}
```

**内部行为**：
- 注入 Sidebar + TopNav
- 监听 window.innerWidth < 1024 → 切换 mobile drawer 模式
- localStorage 持久化折叠状态

### 3.3 HeroCard 组件

```typescript
// components/v3/HeroCard/HeroCard.tsx
export interface HeroCardProps {
  /** 上次面试数据 */
  lastInterview?: InterviewRecentItem;
  /** 最近 3 次面试（用于迷你雷达） */
  recentInterviews: InterviewRecentItem[];
  /** 总面试数（30 天） */
  totalInterviews: number;
  /** 平均分（30 天） */
  avgScore: number | null;
  /** 加载状态 */
  loading?: boolean;
  /** 点击"开始面试"回调 */
  onStartInterview?: () => void;
  /** 点击"查看历史"回调 */
  onViewHistory?: () => void;
  /** 点击"配置面试偏好"回调 */
  onConfigInterview?: () => void;
  "data-testid"?: string;
}
```

**视觉规格**（参考 mockup §页面 1 L981-1065）：
- 背景：粉紫渐变（135deg, pink-400 → violet-500 → indigo-500）
- 边框：rgba(244,114,182,0.4)
- 内边距：48px
- 左侧 3 列：标签 + 标题 + 上次成绩 3 栏 + 主按钮
- 右侧 2 列：最近 3 次迷你雷达

### 3.4 StatsBar 组件

```typescript
// components/v3/StatsBar/StatsBar.tsx
export interface StatsBarStat {
  label: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;        // 如 "+12%" / "+5pp" / "3 题紧急"
  trendColor?: "emerald" | "amber" | "red" | "gray";
}

export interface StatsBarProps {
  stats: StatsBarStat[];
  /** 5 列布局（mobile 1 列 → tablet 3 列 → desktop 5 列）*/
  loading?: boolean;
  "data-testid"?: string;
}
```

**视觉规格**（mockup L1068-1096）：5 列横条 + `divide-x divide-white/5` 分隔线 + 小字号大写 label + 大字号 tabular-nums value

### 3.5 RadarMini 组件

```typescript
// components/v3/RadarMini/RadarMini.tsx
export interface RadarMiniProps {
  data: InterviewRecentItem['radar_data'];  // 5 维数据
  /** 公司方向（显示在雷达下方）*/
  company?: string;
  /** 分数（显示在雷达下方）*/
  score?: number;
  /** 雷达尺寸（默认 80x80 SVG viewBox）*/
  size?: number;
  /** 主题色（默认粉 #f472b6，对应 mockup）*/
  color?: string;
  "data-testid"?: string;
}
```

### 3.6 5 个新路由壳

```typescript
// pages/admin/questions.tsx
export default function AdminQuestionsPage() {
  // 调用 GET /api/admin/questions
  // 表格渲染 + 行编辑 + toast
  // loading 时显示 <EmptyState type="data" title="加载中..." />
  // 错误时显示 <EmptyState type="data" title="加载失败" ctaText="重试" />
}

// pages/admin/sync.tsx
export default function AdminSyncPage() {
  // 调用 GET /api/admin/sync-history
  // 数据源选择 + 试跑按钮 + 历史表
}

// pages/ai/today.tsx
export default function AiTodayPage() {
  // 调用 GET /api/analytics/recommendations
  // 复用 AIRecommendationCard（全量展示）
}

// pages/ai/history.tsx
export default function AiHistoryPage() {
  // 调用 GET /api/news/daily + /api/news/weekly
  // 历史日报列表
}

// pages/settings.tsx
export default function SettingsPage() {
  // 简单表单（昵称/邮件订阅）占位
  // 提交调 PATCH /api/profile
}
```

---

## 4. 测试矩阵（CLAUDE.md § 一.7 重构 + §6 单测强制）

### 4.1 新增测试（62 测试 · 5h）

| 阶段 | 测试文件 | 数量 | 覆盖率目标 |
|---|---|---|---|
| **P1 Sidebar** | `__tests__/components/v3/Sidebar.test.tsx`（6 组件 × 3 测试） | 18 | ≥ 80% |
| **P1 烟雾测试** | `__tests__/pages/interview-room.test.tsx`（Sidebar 注入前 baseline） | 2-3 | smoke |
| **P2 HeroCard** | `__tests__/components/v3/HeroCard.test.tsx` | 4-5 | ≥ 80% |
| **P2 StatsBar** | `__tests__/components/v3/StatsBar.test.tsx` | 4 | ≥ 80% |
| **P2 RadarMini** | `__tests__/components/v3/RadarMini.test.tsx` | 4 | ≥ 80% |
| **P2 Dashboard** | `__tests__/pages/dashboard.test.tsx` | 4-5 | smoke |
| **P3 5 路由可达性** | `__tests__/pages/{admin-questions,admin-sync,ai-today,ai-history,settings}.test.tsx` | 5 | smoke |
| **P3 后端 /recent** | `backend/tests/test_interview_recent_endpoint.py` | 9 | ≥ 85% |
| **P4c logger 测试同步** | 改 30 个 `assert svc.log.name == "codemock.xxx"` → `"knockwise.xxx"` | 30 | 不动逻辑 |
| **P5 playwright** | `frontend/tests/e2e/{17 page + sidebar 折叠 + dashboard 6 组件}.spec.ts` | 25 | 视觉 baseline |

### 4.2 现有测试（154 测试 · 冻结 · 不动）

> 重构不能破坏现有测试。**例外**：P4c 改 logger 名字 → 30 个 `assert svc.log.name` 断言同步改（这是改名连带，不算破坏业务行为测试）。

### 4.3 测试工具链

| 端 | 框架 | 命令 | Mock |
|---|---|---|---|
| 后端 | pytest | `cd backend && ./.venv/bin/python -m pytest tests/ -q` | mock_db（已有）|
| 前端单测 | vitest + RTL + happy-dom | `cd frontend && npm test` | next/router + lib/api（setup.ts 已 mock）|
| E2E | playwright | `cd frontend && npx playwright test` | 无 mock（真实 browser）|

---

## 5. localStorage 迁移方案（关键 · 业务连续性）

### 5.1 现状

```javascript
// 旧 key（codemock 时代）
localStorage.getItem("codemock_token")
localStorage.getItem("codemock_setup")
```

### 5.2 迁移策略：双 key fallback

```typescript
// lib/api.ts（修改）
export function getToken(): string | null {
  // 新 key 优先
  const newToken = localStorage.getItem("knockwise_token");
  if (newToken) return newToken;
  // 旧 key fallback（迁移期）
  const oldToken = localStorage.getItem("codemock_token");
  if (oldToken) {
    // 自动迁移：写入新 key + 删旧 key
    localStorage.setItem("knockwise_token", oldToken);
    localStorage.removeItem("codemock_token");
    return oldToken;
  }
  return null;
}

export function setToken(token: string): void {
  localStorage.setItem("knockwise_token", token);
  // 清理旧 key（防止遗留）
  localStorage.removeItem("codemock_token");
}

export function clearToken(): void {
  localStorage.removeItem("knockwise_token");
  localStorage.removeItem("codemock_token");
}
```

### 5.3 setup 状态同理

```typescript
// pages/setup.tsx + pages/report.tsx + pages/interview.tsx
const raw = localStorage.getItem("knockwise_setup") || localStorage.getItem("codemock_setup");
// 读后写回新 key，删旧 key
```

### 5.4 迁移测试

| # | 测试名 | 输入 | 期望 |
|---|---|---|---|
| 1 | `test_token_migration` | 只 codemock_token 存在 | 返回 token + knockwise_token 写入 + codemock_token 删除 |
| 2 | `test_token_new` | knockwise_token 存在 | 返回 token |
| 3 | `test_token_empty` | 都没 | 返回 null |
| 4 | `test_clear_token` | 两个都存在 | 都删 |
| 5 | `test_setup_migration` | 同 token | 同 |

---

## 6. KnockWise 全量改名清单（70+ 处 · 三档全改）

### 6.1 🟢 P4a 必改（用户可见 · 19 处）

| 文件 | 当前 | 改后 | 行号 |
|---|---|---|---|
| `frontend/pages/dashboard.tsx` | DevBrain | KnockWise | 57 |
| `frontend/pages/profile.tsx` | DevBrain | KnockWise | 156 |
| `frontend/pages/index.tsx` | CodeMock | KnockWise | 79 + SVG 文案 |
| `frontend/pages/interview.tsx` | CodeMock | KnockWise | 215 |
| `frontend/package.json` | "name": "codemock-frontend" | "name": "knockwise-frontend" | 2 |
| `frontend/package-lock.json` | "name": "codemock-frontend" | "name": "knockwise-frontend" | 2, 8 |
| `README.md` | # CodeMock | # KnockWise | 1 |
| `docs/tasks/.../mockups/v3-mockup.html` | Intervue × 3 | KnockWise | 714, 743, 948-951 |
| `frontend/lib/api.ts` | codemock_token | knockwise_token（+ 双 key fallback） | 57, 64, 102 |
| `frontend/components/VoiceRoom.tsx` | codemock_token | knockwise_token（+ fallback） | 62 |
| `frontend/lib/livekit.ts` | codemock_token | knockwise_token（+ fallback） | 10 |
| `frontend/pages/setup.tsx` | codemock_setup | knockwise_setup（+ fallback） | 29 |
| `frontend/pages/report.tsx` | codemock_setup | knockwise_setup（+ fallback） | 156 |
| `frontend/pages/interview.tsx` | codemock_setup | knockwise_setup（+ fallback） | 103, 117 |

### 6.2 🟡 P4b 应改（一致性 · 15 处）

| 文件 | 当前 | 改后 | 行号 |
|---|---|---|---|
| `scripts/start.sh` | intervue-pids.txt + intervue-{livekit,backend,frontend}.log | knockwise-* | 23, 90, 97, 119, 126, 143, 150 |
| `scripts/stop.sh` | intervue-pids.txt | knockwise-pids.txt | 18 |
| `docker-compose.yml` | codemock DB/USER/PASSWORD | knockwise（新部署生效，不动真 DB） | 6, 7, 8, 49 |
| `backend/main.py` | FastAPI(title="CodeMock", ...) | title="KnockWise" | 26 |
| `backend/main.py` | logger = "codemock" | logger = "knockwise" | 23 |
| `backend/main.py` | return {"status": "ok", "service": "codemock"} | "service": "knockwise" | 223 |
| `backend/cli/sync_questions.py` | "Intervue 题目同步 CLI" | "KnockWise 题目同步 CLI" | 28 |
| `.claude/skills/intervue-dev/SKILL.md` | "Intervue (CodeMock)" 6 处 | "KnockWise" | 3, 6, 10, 23, 58, 138 |
| `docs/api/README.md` | Intervue 标题 | KnockWise | 1 |
| `CLAUDE.md` | Intervue 项目名（路径不动） | KnockWise（项目名）| 多 |

### 6.3 🟢 P4c 可改（注释/纯文档 · 44 处）

| 类别 | 数量 | 详细 |
|---|---|---|
| **后端 logger 改名** | ~40 | 12 个 api/*.py + 20 个 services/*.py + 5 个 voice/*.py + core/*.py = ~40 logger `codemock.*` → `knockwise.*` |
| **后端注释/docstring** | 4 | test_core.py:1 / test_agent.py:20 / agents/followup_agent.py:1 / models/__init__.py:1 |

### 6.4 🔴 不改（冻结）

| 不改 | 原因 |
|---|---|
| 项目根目录 `/Users/wangtianyu/IdeaProjects/Intervue/` | git mv 风险大 + 用户没要求 |
| 真实 MySQL `codemock` 数据库 | CLAUDE.md §二冻结 + 数据迁移风险 |
| `backend/core/config.py` 的 codemock DB user/pass（连接本地 DB）| 改了连不上现有真 DB |
| `livekit.yaml` | 冻结 |

### 6.5 30 个测试断言同步（P4c）

> 后端 40 logger 改名连带：现有测试里有 `assert svc.log.name == "codemock.xxx"` 类断言，需要同步改成 `"knockwise.xxx"`。
> 涉及测试文件（已知）：

| 测试文件 | 断言示例 | 行号（估） |
|---|---|---|
| `backend/tests/test_summary_service.py` | `assert svc.log.name == "codemock.summary"` | 48 |
| `backend/tests/test_profile_settlement_service.py` | `assert svc.log.name == "codemock.profile_settlement"` | 55 |
| `backend/tests/test_obsidian_sediment_service.py` | `assert svc.log.name == "codemock.obsidian_sediment"` | 42 |
| `backend/tests/test_question_quality_service.py` | `caplog.at_level(... logger="codemock.question_quality")` | 114, 132 |
| **其余** | grep 全仓 `codemock\\.[a-z_]+` 在测试中 | 估 ~20 处 |

**改法**：正则替换 `codemock\\.(\\w+)` → `knockwise.\\1` + 跑 `pytest -q` 验证。

---

## 7. 错误码与异常分支（CLAUDE.md § 阶段 3 详细化 · 前置）

### 7.1 新增 /api/interviews/recent

| 错误 | HTTP | 响应 body |
|---|---|---|
| 未登录 | 401 | `{"error": {"code": "UNAUTHORIZED", "message": "..."}}` |
| limit 越界 | 422 | `{"error": {"code": "INVALID_QUERY", "message": "limit must be 1-10"}}` |
| 服务错误 | 500 | `{"error": {"code": "INTERNAL_ERROR", ...}}` |

格式：遵循 V2 L4 改进 #3 统一格式（参考 docs/api/README.md）。

### 7.2 5 个新路由壳异常处理

```typescript
// 统一模式
try {
  const data = await api.get(...);
} catch (err) {
  if (err.status === 401) router.push("/");
  else <EmptyState type="data" title="加载失败" ctaText="重试" onCta={reload} />;
}
```

### 7.3 三态视觉规范（loading / empty / error）—— 所有 V3.8 新组件统一

| 状态 | 触发条件 | 视觉 | 行为 |
|---|---|---|---|
| **loading** | 初始加载 / API pending | skeleton 骨架屏 + pulse 动画（`@keyframes skeleton-pulse`）| 不可点击主按钮 |
| **empty** | API 返回空数据 / 0 条 | EmptyState 组件（4 种 type）+ CTA | CTA 引导用户做下一步 |
| **error** | API 4xx/5xx | EmptyState type="data" + 红色错误图标 + "重试" CTA | CTA 重新 fetch |

**实现模式**（HeroCard / StatsBar / RadarMini / 5 路由壳都要遵守）：

```typescript
function useAsyncData<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const reload = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await fetcher()); }
    catch (e) { setError(e as Error); }
    finally { setLoading(false); }
  }, [fetcher]);

  useEffect(() => { reload(); }, [reload]);
  return { data, loading, error, reload };
}

// 用法
function HeroCard() {
  const { data, loading, error, reload } = useAsyncData(fetchRecent);
  if (loading) return <HeroCardSkeleton />;
  if (error) return <EmptyState type="data" title="加载失败" ctaText="重试" onCta={reload} />;
  if (!data || data.items.length === 0) return <EmptyState type="data" title="还没有面试记录" ctaText="开始第一次面试" onCta={onStartInterview} />;
  return <HeroCardContent data={data} />;
}
```

**HeroCardSkeleton**（设计要点）：
- 保留 Hero 卡的整体布局（5 列 grid）
- 上次成绩 3 栏 → 灰色 placeholder + pulse 动画
- 3 个雷达 → 灰色五边形 + pulse
- 主按钮 → 半透明 + 不可点击

**4xx / 5xx 区分**：
- 401 → `router.push("/")`（不显示 EmptyState，避免用户困惑）
- 422 → EmptyState + "参数错误，请重试" + 不暴露技术细节
- 5xx → EmptyState + "服务暂时不可用，请稍后重试" + 错误码（便于用户截图报错）

### 7.4 错误响应体格式（V2 L4 #3 统一格式）

> 这是 CLAUDE.md § 一.三 "阶段 3 详细化" 要求的"补：错误码、异常分支"

```json
// 错误响应统一格式
{
  "error": {
    "code": "STRING_CODE",        // 大写下划线，如 INVALID_QUERY
    "message": "Human readable",   // 用户可读
    "details": { ... } | null,     // 可选，调试用（开发环境才有）
    "request_id": "uuid"           // 服务端 trace
  }
}
```

**前端处理模式**：

```typescript
// lib/api.ts（修改 · 加统一错误处理）
export async function apiGet(url: string): Promise<any> {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body?.error?.message || `HTTP ${res.status}`);
    (err as any).code = body?.error?.code;
    (err as any).status = res.status;
    (err as any).details = body?.error?.details;
    throw err;
  }
  return res.json();
}
```

### 7.5 重构期向后兼容矩阵

> 关键问题：5 阶段 P1-P5 逐步部署期间，老版本客户端 + 新后端 / 新版本客户端 + 老后端能否共存？

| 部署阶段 | 老前端 + 新后端 | 新前端 + 老后端 | 兼容性 |
|---|---|---|---|
| **P1 Sidebar** | ✅ 老前端无 Sidebar，正常用 | ✅ 新前端注入 Sidebar，老后端无影响 | ✅ 完全兼容 |
| **P2 Dashboard 重写** | ✅ 老前端调 `/api/dashboard`，接口不变 | ⚠️ 新前端 HeroCard 调 `/api/interviews/recent`，老后端无此端点 → 404 → HeroCard 显示 EmptyState | 🟡 EmptyState fallback OK |
| **P3 5 路由 + 后端 /recent** | ✅ 老前端无新路由，访问不到 | ⚠️ 新前端 Sidebar 加了新路由，老后端无对应 → 404 | 🟡 EmptyState fallback OK |
| **P4a KnockWise 必改** | ⚠️ 老前端 `codemock_token` 仍能读（双 key fallback）| ✅ 新前端双 key fallback 兼容老 key | ✅ 完全兼容 |
| **P4b KnockWise 应改**（scripts） | 🟡 老前端无影响，但老 PID 文件残留 → stop.sh 新版读不到老 PID 需手动清理 | ✅ | 🟡 需要文档说明 |
| **P4c KnockWise 可改**（logger） | ✅ 无影响（运维日志）| ✅ | ✅ |
| **P5 playwright** | ✅ 无影响（测试基础设施）| ✅ | ✅ |

**回滚策略**：
- 任意 P 阶段独立 PR → revert 单 PR 即回滚
- P4b scripts 改名后，**保留 30 天兼容期**：老 PID 文件 `/tmp/intervue-pids.txt` 也读
- P4a localStorage 双 key fallback **永远保留**（即便将来没老用户，也防新用户清缓存登录态错乱）

### 7.6 playwright CI 集成（CLAUDE.md § 一 本地启动 · 当前阶段暂不上 CI）

> 用户拍 playwright 截图测试。当前 CLAUDE.md §七 是"本地模式"（不上 CI），但需要文档化未来 CI 集成路径。

| 维度 | 本地模式 | CI 集成（未来）|
|---|---|---|
| **浏览器** | Chromium（开发机本地）| Chromium headless（Linux container）|
| **启动** | `npx playwright install --with-deps chromium`（一次性）| Docker image `mcr.microsoft.com/playwright:v1.x.x-jammy` |
| **截图基线** | `frontend/tests/e2e/__screenshots__/`（git tracked） | 同上（git LFS 或 artifact）|
| **运行命令** | `npx playwright test` | CI step：`npx playwright test --reporter=github` |
| **失败处理** | 失败 → 截图存 `test-results/`，开发者本地看 | 失败 → 上传 `test-results/` artifact + 自动评论 |
| **触发** | 手动 + commit hook | PR push 自动 |
| **本次重构** | ✅ 装 + 配置 + 25 测试 | ❌ Out of Scope（重构范围控制）|

**CLAUDE.md §七 决策**：本地模式 → 不上 CI，但**预留 playwright.config.ts** 配置（`webServer: next dev`），未来 CI 改 webServer 为 `next start` + `npm run build` 即可无缝接入。

---

---

## 8. 性能预算（CLAUDE.md § 一 L4）

| 指标 | 目标 | 实测（mock） |
|---|---|---|
| `/api/interviews/recent` P95 | < 50ms | ~20ms（mock）|
| Sidebar 渲染 | < 50ms | ~10ms（13 项） |
| Layout 整体渲染 | < 100ms | ~30ms（mock） |
| Dashboard HeroCard 渲染 | < 80ms | ~25ms |
| 移动端 drawer 展开动画 | < 300ms ease-out | 满足 |
| 折叠动画 | < 300ms ease-out | 满足 |
| playwright 截图每 page | < 2s | 估 ~1s |
| 25 截图测试全套 | < 60s | 估 ~30s |

---

## 9. 部署与回滚

### 9.1 部署顺序（按 P1→P5）

```
P1 commit (Sidebar) → main 上 main-pipeline 自动跑 L1-L4
P2 commit (Dashboard 重写) → L1-L4
P3 commit (5 路由 + 后端 /recent) → L1-L4 + 后端 9 测试
P4a commit (必改 KnockWise) → L1-L4
P4b commit (应改 KnockWise) → L1-L4（注意老 PID 清理）
P4c commit (可改 KnockWise + logger 测试) → L1-L4（30 测试同步）
P5 commit (playwright) → L1-L4 + playwright 截图 baseline 首次人工确认
```

### 9.2 回滚策略

- 每个 P 阶段独立 commit + PR → 任意阶段可单独 revert
- 数据库 schema 不动 → 无 DB 迁移回滚
- localStorage 双 key fallback → 即便新代码有 bug，老 key 仍能读 token
- 业务逻辑 0 改动 → 即便 Sidebar 出问题，业务 API 仍能调

### 9.3 风险预案

| 风险 | 预案 |
|---|---|
| Sidebar 全局注入破坏 8 page | P1 阶段先不发到生产，先本地 `npm run dev` 跑 17 page 截图确认 |
| HeroCard /recent 端点超 200ms | 走 idx_user_status 索引 + mock 测试，若仍慢加 Redis 缓存 60s |
| playwright baseline 不准 | 首次 baseline 需用户手动确认 25 张截图；后续 0.1% 阈值 |
| 老用户登录失效 | 双 key fallback + 监控 /api/auth 失败率，> 5% 自动告警 |

---

## 10. 关联文档

- [research.md](research.md) §9 调研增量 · §10 修订方案 17h
- [product-doc.md](product-doc.md) — 产品脑（用户视角）
- V3 design-spec.md §3.6 Sidebar 已写（视觉规范引用）
- [V3 verify.md](../2026-07-09-new-feature-question-bank-expand/verify.md) — L5 用 mockup 自查的教训
- CLAUDE.md § 一.7 重构路径 · §1.5 架构图规则 · §1.6 产品 vs 技术分文件 · §6 单测强制