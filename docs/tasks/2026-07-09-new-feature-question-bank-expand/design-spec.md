---
title: 设计文档 · V3 题库扩量 + 多维分类 + LeetCode 三件套
date: 2026-07-09
status: v1
tags: [design-spec, 1步, 设计脑, v3, 题库扩量, 多维分类, LeetCode三件套]
related:
  - [product-doc.md](product-doc.md) — 上游产品脑
  - [spec.md](spec.md) — 下游技术脑翻译
  - [research.md](research.md) — 0/0.5/0.6 调研（G3 + I1 已拍）
---

# 设计文档：V3 题库扩量 + 多维分类 + LeetCode 三件套

> **一句话**：把"200 题 + 多维分类 + 学习计划 + 精选题单 + 每日一题"变成用户**看得见摸得着**的 UI — 3 个新页面 + 1 个新 nav 入口 + 1 个新 dashboard 卡 + TagFilter 筛选器。
>
> **作者**：AI 起草（设计脑），用户决策已拍（G3 + I1）

---

## 0. 调研偏差修正

| 调研原写 | 实际情况 | 处置 |
|---|---|---|
| `/pages/plan/` ✅ 在 | ❌ **目录不存在**，nav 也没计划入口 | **V3.0 新建** `/pages/plan/index.tsx` + nav 加"计划"（用户已点痛点） |
| `/pages/collections/` ✅ 在 | ❌ **目录不存在** | **V3.1 新建** `/pages/collections/index.tsx` + `/pages/collections/[id].tsx` |
| DailyChallengeCard 在 dashboard | ❌ **不存在** | **V3.2 新建** DailyChallengeCard + 嵌入 dashboard.tsx 顶部（DailyChallengeCard 在 DailySummaryCard 上方） |
| /learn 有 TagFilter | ⚠️ /learn 有 topic/difficulty/q 筛选，**没** tags= 多选筛选 | **V3.x 增** TagFilter 组件（多选 QuestionTag 系统标签） |

> 🔴 **已确认**：用户痛点 #1（学习计划找不到） = 后端 5 端点全实装、前端 0 暴露。V3.0 必须建 `/pages/plan/index.tsx`。

---

## 1. 用户旅程（必填 · 4 个完整流程）

### 场景 1：每天打开看每日一题（高频）

```
1. 用户早上 9 点打开 /dashboard
2. 看到顶部 DailyChallengeCard（新）：
   ┌──────────────────────────────────────┐
   │ ✨ 今日 1 题（2026-07-09）            │
   │ 算法 · 难度 3                        │
   │ "请描述 LRU 缓存的实现思路..."        │
   │ 预计 5 分钟   [开始答 →]              │
   │ 连续 7 天 🔥                          │
   └──────────────────────────────────────┘
3. 点"开始答" → 跳 /learn/[qid] 答题
4. 答完后回 dashboard → 卡显示"✅ 今日完成 + 连续 8 天"
5. 关闭（明日再开）
```

### 场景 2：周末看学习计划（中频 · 用户痛点 #1 修复）

```
1. 用户周六打开 /plan（新页）
2. 看到 3 个区块：
   - 当前活跃计划卡片（带进度条）
   - 历史计划列表
   - "+ 创建新计划" 按钮
3. 选中当前计划 → 看详情（目标 / 周目标 / 完成度 / 弱项剩余）
4. 点"+ 创建新计划" → 表单（name / start_date / end_date / weekly_target）
5. 创建后回 /plan → 新计划出现 + dashboard 顶部出现"当前计划进度"卡
```

### 场景 3：跟刷算法题单（中频 · LeetCode 风格）

```
1. 用户打开 /collections（新页）
2. 看到 5-8 个官方题单卡片：
   - 算法入门 50 题（25/50 完成）⭐
   - 系统设计 30 题（0/30）
   - 字节前端 50 题（待建设）
   - 字节考过 100 题（待建设）
3. 点"算法入门 50 题" → 进 /collections/algorithms_100
4. 看到题单详情：题单介绍 + 25 题列表（按 position 排序）+ 进度
5. 点第 1 题 → 跳 /learn/[qid] 答题
6. 答完回题单详情 → 第 1 题标 ✅ + 进度 1/25
```

### 场景 4：按多维标签筛题（低频 · V3 主线）

```
1. 用户打开 /learn
2. 顶部筛选区：
   - Topic（V1 已有下拉）
   - Difficulty（V1 已有）
   - 🔥 Tags（V3 新增多选）: [算法] [系统设计] [Python] [字节-二面] ...
3. 选"算法" + "Python" + "字节-二面" → 实时筛选
4. 看到 8 道命中题（algorithms.json 25 题中带 Python + bytedance_r2 标签的）
5. 点题进 /learn/[qid] 答题
```

---

## 2. 页面地图（必填 · V3.6 Sidebar 多级菜单重构）

> **V3.6 重构（用户 2026-07-10 拍方案 C）**：原顶部 nav 4 tab 改为**左侧 Sidebar 5 大分组多级菜单**（14 个 page）。理由：① 面试作为 V1 第 1 核心需要突出 ② 多核心功能需要清晰分组 ③ 顶部 nav 空间不够。

### 2.1 整体架构 · 14 个 page × 5 大分组

| 分组 | 子菜单（page） | 角色 | 视觉标识 |
|---|---|---|---|
| **概览** | 今日概览 | dashboard 入口 | 4 方块图标 |
| **面试** 🔥 V1 第 1 核心 | 今日面试（🔖 新）/ 历史报告 / 面试配置 | Mock Interview 3 子页 | 🎤 矩形图标 + 粉色高亮 |
| **学习复习** V1 第 2 核心 | 题目浏览 / 复习中心 / 学习计划（🔖 V3）/ 精选题单（🔖 V3） | V3 扩展 4 子页 | 📚 文件图标 + 蓝色 |
| **知识库** V1 第 3 核心 | 笔记浏览 / 问答社区 / 报告中心 | V1 既有 3 子页 | 📁 文件夹图标 + 绿色 |
| **AI 推送** V3 新增 | 今日推荐（🔖 V3）/ 推送历史 | V3.7 集成 2 子页 | ✨ Sparkles 图标 + 紫色 |
| **我的**（分隔线下方） | 我的画像 / 设置 | V2 沉淀层 + 偏好 | 👤 头像 + ⚙ 齿轮 |

### 2.2 Sidebar 设计规范

| 维度 | 规范 |
|---|---|
| 宽度 | 默认 `240px` · 折叠 `64px`（仅图标） |
| 位置 | `position: fixed` · `top: 56px`（紧贴 top nav 下方） · `left: 0` |
| 背景 | `rgba(8, 12, 24, 0.85)` + `backdrop-filter: blur(24px)` · 1px 右侧边框 |
| 圆角 | 无（占满高度） |
| 折叠 | localStorage 记忆 · 跨 session 保留 |
| 搜索 | 顶部固定搜索框 · 实时过滤 sidebar 项 + 分组标题 |
| 响应式 | < 1024px 自动隐藏（drawer 模式） |

### 2.3 Sidebar 交互规范

| 元素 | 行为 |
|---|---|
| **分组标题** | 不可点击 · 仅标题 + 小图标 · V2 视觉（11px uppercase） |
| **菜单项** | 点击 → `showPage(name)` · 当前 page 高亮（左侧 2px indigo 边 + 半透明背景） |
| **菜单项徽章** | 🔖 V3 / 新 等 · 6-7px 字号 · 紫蓝渐变 |
| **悬停** | 背景 `rgba(255,255,255,0.04)` + 文字色变亮 |
| **折叠按钮** | sidebar 顶部右侧 ↤ 图标 · 点击切换 240↔64px |

### 2.4 顶 nav 极简化（V3.6 改造后）

```
[Intervue logo]   今日概览 / 当前页标题    📅 2026-07-09    👤 开发者 ▼
```

- ❌ 删除原 4 个 nav tab（仪表盘/学习计划/精选题单/题库浏览）
- ✅ logo 移入 sidebar · 顶部 nav 简化为 logo + breadcrumb + 日期 + 用户菜单

### 2.5 V1 → V3.6 路由映射（已实施 / 待实施）

| V3.6 page | V1 路由 | V3.6 状态 |
|---|---|---|
| dashboard | /dashboard | ✅ 完整内容 |
| interview-today | /interview (主页面) | ✅ 完整 Hero |
| interview-history | /interview/history | 🔒 占位 · V3.7 实施 |
| interview-setup | /interview/setup | 🔒 占位 · V3.7 实施 |
| learn | /learn | ✅ 完整内容 |
| review | /review | 🔒 占位 · V3.7 实施 |
| plan | /plan (V3.0 新建) | ✅ 完整内容 |
| collections | /collections (V3.1 新建) | ✅ 完整内容 |
| knowledge | /knowledge | 🔒 占位 · V3.7 实施 |
| qa | /qa | 🔒 占位 · V4+ 实施（议題 D） |
| report | /report | 🔒 占位 · V1 已实装 backend |
| ai-today | /ai-today (V3.7 新建) | 🔒 占位 · V3.7 实施 |
| ai-history | /ai-history | 🔒 占位 · V3.5 实施 |
| profile | /profile (V2 新建) | 🔒 占位 · V2 沉淀层已实装 |
| settings | /settings | 🔒 占位 · V3.7 实施 |

### 2.6 V3.6 决策（用户 2026-07-10 拍板）

| 决策 | 选项 | 状态 |
|---|---|---|
| **L** = 整体架构改为 Sidebar 多级菜单 | ✅ 方案 C（用户拍板 2026-07-10） | 已实施 |
| **M** = 5 大分组依据 | V1 4 大模块 + V3 新增 AI 推送 | 已拍 |

---

## 3. 页面线框（必填 · 4 个关键页 · JSX 结构 + 视觉 mockup + Figma 提示）

> 用户决策（2026-07-09）：**升级到 HTML/JSX 结构 + 视觉 mockup**，让 UE 同事能直接拿去 Figma。
> 格式约定：每页 3 段（HTML/JSX 结构树 → 视觉 mockup → 给 UE 同事的 Figma 提示）。

---

### 3.1 `/plan` 页（V3.0 · 用户已点痛点 · 关键页）

#### 3.1.1 HTML/JSX 结构树

```jsx
<main className="min-h-screen bg-[#050914] px-6 py-8">
  {/* Header */}
  <header className="flex items-center gap-3 mb-8">
    <button className="text-gray-400 hover:text-white">← 返回</button>
    <h1 className="text-2xl font-bold text-white">学习计划</h1>
  </header>

  {/* 当前活跃计划卡（渐变背景） */}
  <Card className="!bg-gradient-to-br !from-emerald-500/10 !to-cyan-500/10 
                    !border-emerald-500/30 mb-6">
    <div className="flex items-center gap-2 mb-4">
      <TrophyOutlined className="text-emerald-400 text-xl" />
      <h2 className="text-lg font-semibold text-white">当前活跃计划</h2>
    </div>

    {/* 计划名 + 日期范围 + 目标 */}
    <div className="mb-6">
      <h3 className="text-xl font-bold text-white mb-1">"2 周算法冲刺"</h3>
      <p className="text-sm text-gray-400">
        2026-07-09 ~ 2026-07-23  •  目标：掌握 algorithms 50%
      </p>
    </div>

    {/* 进度条（antd Progress） */}
    <div className="mb-4">
      <div className="flex justify-between mb-2">
        <span className="text-sm text-gray-300">总体进度</span>
        <span className="text-sm font-semibold text-emerald-400">5/10  (50%)</span>
      </div>
      <Progress percent={50} strokeColor="#34d399" showInfo={false} 
                className="!mb-2" />
    </div>

    {/* 周进度（次级） */}
    <div className="mb-4">
      <div className="flex justify-between mb-2">
        <span className="text-xs text-gray-400">周 1 进度</span>
        <span className="text-xs text-gray-400">5/10</span>
      </div>
      <Progress percent={50} strokeColor="#10b981" showInfo={false} size="small" />
    </div>

    {/* 弱项剩余 */}
    <div className="mb-6">
      <span className="text-sm text-gray-300">弱项剩余：</span>
      <span className="text-sm text-emerald-400">[]  ✓</span>
    </div>

    {/* 操作按钮组 */}
    <Space>
      <Button type="primary" icon={<EyeOutlined />}>查看详情</Button>
      <Button icon={<ReloadOutlined />} onClick={refresh}>刷新进度</Button>
      <Button danger icon={<StopOutlined />}>结束计划</Button>
    </Space>
  </Card>

  {/* 历史计划列表 */}
  <section className="mb-6">
    <h2 className="text-base font-semibold text-white mb-3">历史计划</h2>
    <Card>
      <List
        dataSource={historyPlans}
        renderItem={plan => (
          <List.Item>
            <span>• "{plan.name}"  {plan.dateRange}</span>
            <span className="text-emerald-400">✅ 已完成 {plan.done}/{plan.target}</span>
          </List.Item>
        )}
      />
    </Card>
  </section>

  {/* 创建按钮（右下浮动） */}
  <Button type="primary" size="large" icon={<PlusOutlined />}
          className="!fixed !bottom-8 !right-8 !h-14 !px-6 !text-base 
                     !shadow-[0_4px_16px_rgba(99,102,241,0.4)]"
          onClick={openCreateModal}>
    创建新计划
  </Button>

  {/* 创建表单 Modal */}
  <Modal title="创建学习计划" open={isCreateOpen} onOk={handleCreate}>
    <Form layout="vertical">
      <Form.Item label="计划名称" required>
        <Input maxLength={50} placeholder="如：2 周算法冲刺" />
      </Form.Item>
      <Form.Item label="日期范围" required>
        <RangePicker />
      </Form.Item>
      <Form.Item label="目标">
        <Input.TextArea maxLength={200} rows={2} />
      </Form.Item>
      <Form.Item label="周目标">
        <WeeklyTargetEditor />
      </Form.Item>
    </Form>
  </Modal>
</main>
```

#### 3.1.2 视觉 mockup（UE 拿去 Figma 用）

| 区块 | antd 组件 | 关键 token |
|---|---|---|
| **页面背景** | `<body>` | `bg-[#050914]` (深蓝黑) · `min-h-screen` |
| **当前计划卡** | `<Card>` | `bg-gradient-to-br from-emerald-500/10 to-cyan-500/10` · 圆角 `12px` · 边框 `border-emerald-500/30` · 内边距 `24px` |
| **进度条** | `<Progress percent={50}>` | `strokeColor="#34d399"` (emerald-400) · 高度 `8px` · 圆角 `4px` |
| **操作按钮** | `<Button type="primary">` | 主题色 `#6366f1` · 圆角 `8px` · 字号 `14px` · hover 加深 5% |
| **结束按钮** | `<Button danger>` | 红色 `#ef4444` · 圆角 `8px` |
| **历史列表** | `<List>` | 背景透明 · 行间距 `12px` · 字号 `14px` · 副文本 `#8b8fa3` |
| **创建按钮（右下）** | `<Button>` | `fixed bottom-8 right-8` · 高度 `56px` · 阴影 `0 4px 16px rgba(99,102,241,0.4)` · 字号 `16px` |
| **表单 Modal** | `<Modal>` | 居中弹出 · 宽度 `600px` · 圆角 `12px` · 遮罩 `rgba(0,0,0,0.7)` |

#### 3.1.3 给 UE 同事的 Figma 工作流提示

1. **Frame 尺寸**：1440 × 900 (桌面) · 375 × 812 (移动 · V3.x 再做)
2. **使用 antd Design Kit**：Figma Community → 搜 "Ant Design 5" → 直接拖组件
3. **关键自画**：
   - 进度条视觉 → antd 有，但**进度数字 + 标签**要自画（`flex justify-between`）
   - 创建按钮的阴影 → antd 默认阴影不够亮，**自画阴影** `0 4px 16px rgba(99,102,241,0.4)`
4. **复用 V2 沉淀层**：DailySummaryCard / ProfilePage 的卡片风格（圆角 12px + 半透明深色）
5. **导出**：导出 React + Tailwind 类名（已写在 §3.1.1），研发可直接对号入座

---

### 3.2 `/collections` 页（V3.1 · LeetCode 风格 · 关键页）

#### 3.2.1 HTML/JSX 结构树

```jsx
<main className="min-h-screen bg-[#050914] px-6 py-8">
  {/* Header */}
  <header className="flex items-center gap-3 mb-8">
    <button className="text-gray-400 hover:text-white">← 返回</button>
    <h1 className="text-2xl font-bold text-white">精选题单</h1>
  </header>

  {/* 筛选标签栏 */}
  <div className="flex items-center gap-3 mb-6">
    <span className="text-sm text-gray-400">筛选：</span>
    <Tag.CheckableTag checked={filter === 'all'} onChange={() => setFilter('all')}>
      全部
    </Tag.CheckableTag>
    <Tag.CheckableTag checked={filter === 'subscribed'} 
                       onChange={() => setFilter('subscribed')}
                       className="!text-amber-400">
      ⭐ 已订阅
    </Tag.CheckableTag>
    <Tag.CheckableTag checked={filter === 'algo'} onChange={() => setFilter('algo')}>
      算法
    </Tag.CheckableTag>
    <Tag.CheckableTag checked={filter === 'sys'} onChange={() => setFilter('sys')}>
      系统设计
    </Tag.CheckableTag>
    <Tag.CheckableTag checked={filter === 'fe'} onChange={() => setFilter('fe')}>
      前端
    </Tag.CheckableTag>
    <Tag.CheckableTag checked={filter === 'bytedance'} 
                       onChange={() => setFilter('bytedance')}
                       className="!text-amber-400">
      字节
    </Tag.CheckableTag>
  </div>

  {/* 题单卡片网格（响应式：桌面 3 列 / 平板 2 列 / 移动 1 列） */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {collections.map(collection => (
      <CollectionCard key={collection.id} collection={collection} />
    ))}
  </div>

  {/* 0 题单空状态 */}
  {collections.length === 0 && (
    <Empty description={
      <span className="text-gray-400">题单建设中，敬请期待</span>
    } />
  )}
</main>
```

#### 3.2.2 视觉 mockup（UE 拿去 Figma 用）

**CollectionCard 子组件**（独立组件 / 复用 V2 GlassCard 风格）：

```jsx
function CollectionCard({ collection }) {
  return (
    <Card hoverable className={`
      !bg-gradient-to-br !from-blue-500/10 !to-purple-500/10
      !border-blue-500/30
      !transition-all !duration-200
      hover:!-translate-y-1 hover:!shadow-[0_8px_24px_rgba(99,102,241,0.3)]
    `}>
      {/* 已订阅标记 */}
      {collection.subscribed && (
        <span className="absolute top-3 left-3 text-amber-400 text-lg">⭐</span>
      )}

      {/* 标题区 */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">{collection.icon}</span>  {/* 📘 🏗️ 🎨 🏢 🚀 */}
        <h3 className="text-lg font-semibold text-white">{collection.name}</h3>
      </div>

      {/* 难度 + 完成度 */}
      <div className="mb-4">
        <p className="text-sm text-gray-400 mb-2">
          难度 {collection.difficultyRange}
        </p>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-400">{collection.done}/{collection.total}</span>
          <span className="text-xs font-semibold text-blue-400">
            {Math.round(collection.done / collection.total * 100)}%
          </span>
        </div>
        <Progress percent={collection.done / collection.total * 100} 
                  strokeColor="#60a5fa" showInfo={false} size="small" />
      </div>

      {/* 操作按钮 */}
      <Button type="primary" block 
              icon={collection.done > 0 ? <PlayCircleOutlined /> : <PlayCircleOutlined />}>
        {collection.done > 0 ? '继续刷 →' : '开始 →'}
      </Button>
    </Card>
  );
}
```

#### 3.2.3 给 UE 同事的 Figma 工作流提示

1. **Frame 尺寸**：1440 × 900 (桌面 3 列) · 768 × 1024 (平板 2 列) · 375 × 812 (移动 1 列)
2. **关键自画**：
   - 题单卡的**渐变背景**（蓝色 → 紫色） → antd Card 不支持多色渐变，**自画**用 Tailwind `bg-gradient-to-br from-blue-500/10 to-purple-500/10`
   - **⭐ 已订阅标记**位置（卡片左上角，绝对定位）
   - hover 阴影加深效果 → Tailwind `hover:shadow-[0_8px_24px_rgba(99,102,241,0.3)]`
3. **进度条**：antd `<Progress>` + 自定义 strokeColor
4. **图标**：用 emoji（📘 🏗️ 🎨 🏢 🚀）作为占位，UE 同事可换成自定义 SVG
5. **响应式断点**：md = 768px · lg = 1024px · 移动端 1 列堆叠

---

### 3.3 `DailyChallengeCard`（V3.2 · dashboard 顶部新卡 · 关键卡）

#### 3.3.1 HTML/JSX 结构树

```jsx
// dashboard.tsx 顶部（在 DailySummaryCard 上方）
function Dashboard() {
  return (
    <main className="min-h-screen bg-[#050914] px-6 py-8">
      {/* 🆕 V3.2 DailyChallengeCard（在 V2 DailySummaryCard 上方） */}
      <DailyChallengeCard />

      {/* V2 已有的 DailySummaryCard */}
      <DailySummaryCard />

      {/* 4 模块入口卡（V1 已有） */}
      <ModuleCards />
    </main>
  );
}

// DailyChallengeCard.tsx
function DailyChallengeCard() {
  const { data, loading, error } = useDailyChallenge();
  
  if (loading) return <SkeletonCard />;
  if (error) return <ErrorCard onRetry={refetch} />;
  if (!data) return null;  // 当日无题时隐藏
  
  const { question, completed, streakDays } = data;
  
  return (
    <Card className={`
      !bg-gradient-to-br !from-amber-500/10 !to-orange-500/10
      !border-amber-500/30 mb-6
      !shadow-[0_2px_8px_rgba(245,158,11,0.15)]
    `}>
      <div className="flex items-start justify-between mb-4">
        {/* 左：标题 + 日期 */}
        <div className="flex items-center gap-2">
          <FireOutlined className="text-amber-400 text-xl" />
          <h2 className="text-lg font-semibold text-white">
            今日 1 题
            <span className="text-sm text-gray-400 ml-2">({data.date})</span>
          </h2>
        </div>
        
        {/* 右：streak 徽章 */}
        <Tag className="!bg-amber-500/20 !border-amber-500/40 !text-amber-300">
          <FireOutlined /> 连续 {streakDays} 天
        </Tag>
      </div>

      {/* 题目元数据 */}
      <div className="flex items-center gap-3 mb-3">
        <Tag color="violet">{question.topic}</Tag>
        <Tag color="blue">{question.sub_topic}</Tag>
        <Tag className="!bg-amber-500/20 !border-amber-500/40 !text-amber-300">
          难度 {question.difficulty}
        </Tag>
      </div>

      {/* 题目文本（截断 200 字） */}
      <p className="text-base text-gray-200 mb-4 line-clamp-3">
        {truncate(question.question_text, 200)}
      </p>

      {/* 底部：预计时间 + 操作按钮 */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">
          <ClockCircleOutlined /> 预计 {question.estimated_minutes} 分钟
        </span>
        
        {/* 完成态切换按钮 */}
        {completed ? (
          <span className="text-emerald-400">
            <CheckCircleFilled /> 今日完成
          </span>
        ) : (
          <Button type="primary" icon={<ArrowRightOutlined />}
                  onClick={() => router.push(`/learn/${question.question_id}`)}>
            开始答 →
          </Button>
        )}
      </div>
    </Card>
  );
}
```

#### 3.3.2 视觉 mockup（UE 拿去 Figma 用）

| 区块 | antd 组件 | 关键 token |
|---|---|---|
| **卡片背景** | `<Card>` | `bg-gradient-to-br from-amber-500/10 to-orange-500/10` · 圆角 `12px` · 边框 `border-amber-500/30` · 阴影 `0 2px 8px rgba(245,158,11,0.15)` |
| **标题** | `<h2>` + `<FireOutlined />` | `text-lg font-semibold text-white` · 图标 `text-amber-400 text-xl` |
| **streak 徽章** | `<Tag>` | `bg-amber-500/20` · 边框 `border-amber-500/40` · 文字 `text-amber-300` |
| **题目元数据 Tag** | `<Tag color>` | violet `#a78bfa` · blue `#60a5fa` · amber `#f59e0b` · 圆角 `6px` |
| **题目文本** | `<p>` | `text-base text-gray-200` · `line-clamp-3`（最多 3 行）· 行高 `1.5` |
| **开始按钮** | `<Button type="primary">` | 主题色 `#6366f1` · 圆角 `8px` · 字号 `14px` |
| **完成态** | `<CheckCircleFilled />` | 绿色 `#34d399` · 字号 `14px` |
| **预计时间** | `<ClockCircleOutlined />` | 灰色 `#8b8fa3` · 字号 `12px` |

#### 3.3.3 给 UE 同事的 Figma 工作流提示

1. **Frame 尺寸**：与 dashboard 同宽 1440px，卡片高度自适应（min 200px / max 280px）
2. **关键自画**：
   - **渐变背景**（amber → orange） → Tailwind 自定义类，**不**用 antd 默认
   - **streak 徽章**放右上角（绝对定位或 flex justify-between）
   - 题目文本**截断 3 行**（line-clamp-3）→ Figma 用 "Auto Layout: Vertical · max 3 lines" 实现
3. **复用 V2 沉淀层**：与 DailySummaryCard 风格保持一致（圆角 12px + 半透明深色 + 渐变）
4. **动画建议**：每日 0 点切换题目时，卡片淡出 → 新题目淡入（300ms）

---

### 3.4 `/learn` 顶部新 TagFilter（V3.x）

#### 3.4.1 HTML/JSX 结构树

```jsx
// /pages/learn/index.tsx 顶部筛选区
function LearnPage() {
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  
  return (
    <main className="min-h-screen bg-[#050914] px-6 py-8">
      {/* 🆕 V3.x 筛选区（在题目列表上方） */}
      <Card className="!bg-white/[0.02] !border-white/10 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Topic 下拉（V1 已有） */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">Topic</label>
            <Select value={topic} onChange={setTopic} className="!w-32">
              <Option value="all">全部</Option>
              <Option value="algorithms">算法</Option>
              <Option value="system_design">系统设计</Option>
              ...
            </Select>
          </div>

          {/* 难度下拉（V1 已有） */}
          <div>
            <label className="text-xs text-gray-400 block mb-1">难度</label>
            <Select value={difficulty} onChange={setDifficulty} className="!w-24">
              <Option value="all">全部</Option>
              <Option value={2}>2</Option>
              <Option value={3}>3</Option>
              <Option value={4}>4</Option>
              <Option value={5}>5</Option>
            </Select>
          </div>

          {/* 🔥 V3.x Tag 多选（按维度分组） */}
          <div className="flex-1 min-w-[300px]">
            <label className="text-xs text-gray-400 block mb-1">
              <TagOutlined /> 标签：
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(systemTagsByDimension).map(([dim, tags]) => (
                <div key={dim} className="flex items-center gap-1">
                  <span className="text-xs text-gray-500">{dim}:</span>
                  {tags.map(tag => (
                    <Tag.CheckableTag
                      key={tag.id}
                      checked={selectedTags.includes(tag.id)}
                      onChange={checked => toggleTag(tag.id, checked)}
                      className={selectedTags.includes(tag.id) 
                        ? getTagColor(tag.dimension)  // 高亮用维度色
                        : ''}
                    >
                      {tag.name}
                    </Tag.CheckableTag>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* 搜索框（V1 已有） */}
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs text-gray-400 block mb-1">搜索</label>
            <Input value={query} onChange={e => setQuery(e.target.value)} 
                   placeholder="关键词…" />
          </div>

          {/* 只看收藏（V1 已有） */}
          <Checkbox checked={bookmarkedOnly} onChange={e => setBookmarkedOnly(e.target.checked)}>
            <span className="text-sm">只看收藏</span>
          </Checkbox>
        </div>
      </Card>

      {/* 题目列表（V1 已有） */}
      <QuestionList questions={filteredQuestions} loading={loading} />
    </main>
  );
}
```

#### 3.4.2 视觉 mockup（UE 拿去 Figma 用）

| 区块 | antd 组件 | 关键 token |
|---|---|---|
| **筛选区卡片** | `<Card>` | `bg-white/[0.02]` · 边框 `border-white/10` · 圆角 `12px` · 内边距 `24px` |
| **下拉选择** | `<Select>` | `bg-white/[0.04]` · 边框 `border-gray-700/30` · 圆角 `8px` · 字号 `14px` |
| **标签维度标签** | `<span>` | `text-xs text-gray-500` · 文字垂直居中 |
| **可勾选标签** | `<Tag.CheckableTag>` | 未选：`bg-white/5 text-gray-400` · 已选：`bg-{dim}-500/20 text-{dim}-300 border-{dim}-500/40` |
| **标签维度配色** | — | A 面试方向（方向色） · B 技术栈（紫 `#a78bfa`） · C 公司轮次（amber `#f59e0b`） |
| **搜索框** | `<Input>` | `bg-white/[0.04]` · 边框 `border-gray-700/30` · 圆角 `8px` |
| **只看收藏复选框** | `<Checkbox>` | antd 默认 · 标签字号 `14px` |
| **分隔间距** | — | 区块之间 `16px` · Tag 之间 `8px` |

#### 3.4.3 给 UE 同事的 Figma 工作流提示

1. **Frame 尺寸**：1440 × 80 (筛选区高度)
2. **关键自画**：
   - **3 个维度的颜色区分** → A 面试方向色（vary by topic）/ B 技术栈紫 / C 公司 amber
   - 标签的**未选/已选两态** → Figma 用 Component + Variant 实现
   - **横向 flex-wrap** 自动换行（窄屏自动堆叠）
3. **响应式**：< 768px 时 5 个筛选器（Topic/难度/Tags/搜索/收藏）改成 2 行堆叠
4. **动态数据**：标签列表从 `GET /api/learn/tags` 拉，V3 增 **系统标签预填** ~50 条
5. **筛选逻辑**：tags= 多个值用"任一命中"（OR 关系）

---

### 3.5 `AIRecommendationCard`（V3.7 · 🆕 AI 推送模块集成 · 用户 2026-07-10 拍 A 极简）

> **背景**：V1 阶段 4.2 已决定 AI 推送独立成模块，V1 后端 `recommendations_service.py:18` `get_recommendations` + `/api/analytics/recommendations` 已实装，但前端 0 暴露。V3.7 = dashboard 加 1 个"今日 AI 推荐"玻璃卡，调 V1 已实装的 endpoint，不建独立页（用户 2026-07-10 拍 A 极简 · 估时 2-3h）。

#### 3.5.1 HTML/JSX 结构树

```jsx
// dashboard.tsx 顶部（DailyChallengeCard 上方）
function Dashboard() {
  return (
    <main className="min-h-screen bg-[#050914] px-8 py-10">
      {/* 🆕 V3.7 AIRecommendationCard（最顶部 · 在 stat 卡下方、DailyChallenge 上方） */}
      <AIRecommendationCard />

      {/* V3.2 DailyChallengeCard */}
      <DailyChallengeCard />

      {/* V2 DailySummaryCard */}
      <DailySummaryCard />

      {/* 4 模块入口卡 */}
      <ModuleCards />
    </main>
  );
}

// AIRecommendationCard.tsx
function AIRecommendationCard() {
  const { data, loading, error } = useAIRecommendations();
  
  if (loading) return <SkeletonCard />;
  if (error || !data || data.recommendations.length === 0) return null;  // 失败 / 无数据隐藏
  
  return (
    <div className="glass-card-static bg-grad-summary mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style="background: linear-gradient(135deg, #6366f1, #a78bfa); box-shadow: 0 4px 12px rgba(99,102,241,0.3);">
            {/* Sparkles SVG icon */}
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L11 6L15 7L11 8L10 12L9 8L5 7L9 6L10 2Z" fill="white"/>
              <path d="M16 12L16.5 13.5L18 14L16.5 14.5L16 16L15.5 14.5L14 14L15.5 13.5L16 12Z" fill="white"/>
              <path d="M4 13L4.5 14L5.5 14.5L4.5 15L4 16L3.5 15L2.5 14.5L3.5 14L4 13Z" fill="white"/>
            </svg>
          </div>
          <div>
            <h2 className="text-base font-semibold">今日 AI 推荐</h2>
            <p className="text-xs text-gray-400">基于你的薄弱点 · V1 recommendations_service 实装</p>
          </div>
        </div>
        <button className="btn btn-ghost text-xs" onclick="showToast('查看更多')">
          查看全部 →
        </button>
      </div>

      {/* 推荐列表 · 3-4 条 · 横向 grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.recommendations.slice(0, 4).map((rec, idx) => (
          <button key={idx} className="recommendation-item text-left" onclick="clickRecommendation(this)">
            <div className="flex items-center gap-2 mb-2">
              {/* 类型 tag（[补] / [练] / [读]） */}
              <span className={`tag tag-${getRecTypeColor(rec.type)}`}>
                {rec.prefix}  {/* "[补]" / "[练]" / "[读]" */}
              </span>
              <span className="text-xs text-gray-500 stat-num">{rec.priority}</span>
            </div>
            <p className="text-sm text-gray-100 font-medium mb-1">{rec.title}</p>
            <p className="text-xs text-gray-400 line-clamp-2">{rec.description}</p>
            <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>{rec.action}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Footer · 引导用户产生更多数据 */}
      {data.recommendations.length < 4 && (
        <p className="text-xs text-gray-500 mt-4 text-center">
          💡 完成更多面试 + 答题后，AI 推荐会越来越精准
        </p>
      )}
    </div>
  );
}
```

#### 3.5.2 视觉 mockup（UE 拿去 Figma 用）

| 区块 | antd 组件 / Tailwind | 关键 token |
|---|---|---|
| **卡片背景** | `<Card>` + glass 拟态 | `bg-gradient-to-br from-indigo-500/8 to-violet-500/8` · 圆角 `16px` · 边框 `border-white/8` · 阴影 `0 4px 12px rgba(0,0,0,0.25)` |
| **图标方块** | `<div>` 渐变方块 | `bg-gradient-to-br from-indigo-500 to-violet-500` · 圆角 `12px` · 阴影 `0 4px 12px rgba(99,102,241,0.3)` · 内嵌 Sparkles SVG |
| **标题** | `<h2>` | `text-base font-semibold text-white` |
| **副标题** | `<p>` | `text-xs text-gray-400` · 字号 `12px` |
| **推荐条目** | `<button>` hover 卡片 | 背景 `rgba(255,255,255,0.02)` → hover `rgba(255,255,255,0.06)` · 圆角 `10px` · padding `14px` · 边框 `1px solid transparent` → hover `border-color: rgba(99,102,241,0.2)` |
| **类型 Tag**（[补]/[练]/[读]） | `<Tag>` | [补] 红色 `#f87171` · [练] 蓝色 `#60a5fa` · [读] 紫色 `#a78bfa` · 圆角 `6px` · 字号 `12px` |
| **推荐标题** | `<p>` | `text-sm font-medium text-gray-100` |
| **推荐描述** | `<p>` | `text-xs text-gray-400` · `line-clamp-2`（最多 2 行） |
| **操作行** | `<div>` | `text-xs text-gray-500` · "→ 立即练习" / "→ 查看笔记" |

#### 3.5.3 推荐条目 4 种类型配色（UE Figma 直接复制）

| 类型 | Prefix | 配色 | 典型 title |
|---|---|---|---|
| **补盲点** | [补] | `#f87171` (red-400) | "[补] 系统设计 · 缓存一致性" |
| **练习题** | [练] | `#60a5fa` (blue-400) | "[练] LRU 缓存" |
| **读笔记** | [读] | `#a78bfa` (violet-400) | "[读] 字节面试经验总结" |
| **复盘** | [盘] | `#f59e0b` (amber-400) | "[盘] 上周错题复盘" |

#### 3.5.4 给 UE 同事的 Figma 工作流提示

1. **Frame 尺寸**：与 dashboard 同宽 1440px，卡片高度自适应（min 280px / max 380px）
2. **关键自画**：
   - **Sparkles SVG 图标**（3 个星形 + 渐变方块背景）— Figma 用 Component + Variant
   - **4 种类型配色**作为 4 个 Tag 变体（Component Variants）
   - **推荐条目**的 hover 状态（背景 + 边框 + 阴影加深）
3. **数据来源**：从 `GET /api/analytics/recommendations` 拉，V1 已实装 `recommendations_service.get_recommendations`，无需新后端
4. **空状态处理**：失败 / 无数据时**隐藏整张卡**（不显示骨架不报错，决策 7A 不阻塞）
5. **埋点**：每个推荐条目点击触发 `data-action="click_recommend"` + 推荐 ID，用于产品指标 5 统计

#### 3.5.5 数据契约（前端用 · 后端零改动）

```typescript
// 来自 /api/analytics/recommendations（V1 已实装）
interface AIRecommendation {
  type: 'practice' | 'knowledge' | 'review' | 'interview';  // 4 类
  prefix: string;        // "[练]" / "[读]" / "[盘]" / "[补]"
  title: string;         // "LRU 缓存"
  description: string;   // "补系统设计薄弱点，重点在分布式缓存"
  priority: number;      // 1-5
  action: string;        // "立即练习" / "查看笔记"
  link: string;          // "/learn/algo_005" / "/knowledge/..."
}

interface AIRecommendationsResponse {
  recommendations: AIRecommendation[];
  message?: string;      // 无数据时的友好提示
}
```

---

### 3.6 `Sidebar`（V3.6 · 🆕 整体架构重构 · 用户 2026-07-10 拍方案 C · 14 page × 5 大分组）

> **背景**：原顶部 nav 4 tab 不够清晰，面试作为 V1 第 1 核心需要独立突出，多核心功能需要分组管理。V3.6 改为**左侧固定 Sidebar · 5 大分组多级菜单**（240px / 可折叠 64px）。

#### 3.6.1 HTML/JSX 结构树

```jsx
// app/layout.tsx（app shell）
function AppShell() {
  return (
    <div className="app-layout">
      {/* 顶部 nav 极简化 */}
      <TopNav>
        <Logo />
        <Breadcrumb />  {/* 当前页标题 */}
        <UserMenu />
      </TopNav>

      {/* 左侧 Sidebar · 5 大分组 */}
      <Sidebar>
        <SidebarHeader>
          <Logo />
          <ToggleButton />  {/* 折叠 / 展开 */}
        </SidebarHeader>
        <SidebarSearch />  {/* 搜索框 + 实时过滤 */}
        <SidebarNav>
          <SidebarGroup title="概览" icon="4方块">
            <SidebarItem page="dashboard" icon="4方块" label="今日概览" active />
          </SidebarGroup>
          <SidebarGroup title="面试" icon="🎤" highlight>  {/* V1 第 1 核心 */}
            <SidebarItem page="interview-today" icon="时钟" label="今日面试" badge="新" />
            <SidebarItem page="interview-history" icon="历史" label="历史报告" />
            <SidebarItem page="interview-setup" icon="配置" label="面试配置" />
          </SidebarGroup>
          <SidebarGroup title="学习复习" icon="📚">  {/* V1 第 2 核心 */}
            <SidebarItem page="learn" icon="书" label="题目浏览" />
            <SidebarItem page="review" icon="刷新" label="复习中心" />
            <SidebarItem page="plan" icon="学习路径" label="学习计划" badge="V3" />
            <SidebarItem page="collections" icon="书堆" label="精选题单" badge="V3" />
          </SidebarGroup>
          <SidebarGroup title="知识库" icon="📁">  {/* V1 第 3 核心 */}
            <SidebarItem page="knowledge" icon="文件夹" label="笔记浏览" />
            <SidebarItem page="qa" icon="聊天" label="问答社区" />
            <SidebarItem page="report" icon="图表" label="报告中心" />
          </SidebarGroup>
          <SidebarGroup title="AI 推送" icon="✨">  {/* V3 新增 */}
            <SidebarItem page="ai-today" icon="sparkles" label="今日推荐" badge="V3" />
            <SidebarItem page="ai-history" icon="列表" label="推送历史" />
          </SidebarGroup>
          <SidebarDivider />
          <SidebarGroup title="我的">
            <SidebarItem page="profile" icon="头像" label="我的画像" />
            <SidebarItem page="settings" icon="齿轮" label="设置" />
          </SidebarGroup>
        </SidebarNav>
        <SidebarFooter>
          <V3Status />  {/* "V3 沉淀层 · ● 启用" */}
        </SidebarFooter>
      </Sidebar>

      {/* 主内容区 · 让位 240px */}
      <MainContent>
        {/* 根据 sidebar 选中 page 切换 */}
        <CurrentPage />
      </MainContent>
    </div>
  );
}

// SidebarItem.tsx
function SidebarItem({ page, icon, label, badge, active, onClick }) {
  return (
    <button
      className={`sidebar-item ${active ? 'active' : ''}`}
      data-page={page}
      onClick={() => onClick(page)}
    >
      <Icon name={icon} />
      <span>{label}</span>
      {badge && <span className="sidebar-badge">{badge}</span>}
    </button>
  );
}
```

#### 3.6.2 视觉 mockup（UE 拿去 Figma 用）

**整体布局**：

```
┌──────────────────────────────────────────────────────────────────┐
│  [Intervue]   今日概览        📅 2026-07-09   👤 开发者 ▼        │ ← top nav 56px
├─────────────┬────────────────────────────────────────────────────┤
│ 240px       │                                                    │
│ ┌─────────┐ │                                                    │
│ │ ◀ Logo  │ │                                                    │
│ └─────────┘ │                                                    │
│             │                                                    │
│ 🔍 搜索...  │                                                    │
│             │                                                    │
│ 概览        │                                                    │
│ ▸ 今日概览  │           主内容区（max-w-7xl · 24px padding）       │
│             │                                                    │
│ 面试 🔥     │           根据 sidebar 选中 page 切换                │
│ ▸ 今日面试  │           默认显示 dashboard                         │
│   面试报告  │                                                    │
│   面试配置  │                                                    │
│             │                                                    │
│ 学习复习    │                                                    │
│ ▸ 题目浏览  │                                                    │
│ ▸ 复习中心  │                                                    │
│ ▸ 学习计划V3│                                                    │
│ ▸ 精选题单V3│                                                    │
│             │                                                    │
│ 知识库      │                                                    │
│ ▸ 笔记浏览  │                                                    │
│ ▸ 问答社区  │                                                    │
│ ▸ 报告中心  │                                                    │
│             │                                                    │
│ AI 推送     │                                                    │
│ ▸ 今日推荐V3│                                                    │
│ ▸ 推送历史  │                                                    │
│             │                                                    │
│ ─────       │                                                    │
│ 👤 我的画像  │                                                    │
│ ⚙ 设置     │                                                    │
│             │                                                    │
│ V3 ●启用   │                                                    │
└─────────────┴────────────────────────────────────────────────────┘
```

**关键元素 token**：

| 元素 | 规范 |
|---|---|
| **Sidebar 整体** | 240px 宽 · `bg: rgba(8,12,24,0.85)` + `backdrop-filter: blur(24px)` · 1px 右侧边框 |
| **折叠态** | 64px 宽 · 只显示图标 · 文字/徽章 `display: none` |
| **Sidebar Header** | logo + 折叠按钮 · 12px padding-bottom · 1px 底边 |
| **搜索框** | 圆角 8px · 11px 高 · focus 时 indigo 边框 + 4% 紫背景 |
| **分组标题** | 11px uppercase · 字间距 0.08em · `text-tertiary` 色 |
| **菜单项** | 圆角 8px · 高 36px · 8/10px padding · `text-secondary` 色 |
| **菜单项 hover** | 背景 `rgba(255,255,255,0.04)` · 文字 `text-primary` |
| **菜单项 active** | 左侧 2px indigo 边 · 背景 `rgba(99,102,241,0.12)` · 文字白 |
| **菜单项图标** | 16px · `opacity: 0.8` → hover/active 1.0 |
| **菜单项徽章** | 6-7px 高 · `bg: rgba(99,102,241,0.2)` · 文字 `#c7d2fe` · 圆角 4px |
| **分组分隔线** | 1px `bg: var(--color-border)` · 8px margin |
| **Footer** | 1px 顶边 · "V3 沉淀层 · ● 启用" 状态指示 |
| **top nav breadcrumb** | text-base font-semibold · ml-6 缩进 |
| **主内容 margin** | `margin-left: 240px` · 折叠时 `64px` · 24px/32px padding |

#### 3.6.3 交互规范

| 操作 | 行为 |
|---|---|
| **点击菜单项** | `showPage(name)` · 隐藏其他 13 page · sidebar 高亮 · breadcrumb 切换 · 主区域滚动到顶 |
| **折叠按钮** | `toggleSidebar()` · 240 ↔ 64px · localStorage 持久化 |
| **搜索框输入** | `filterSidebar(query)` · 实时隐藏不匹配项 · 空匹配时隐藏整个分组 |
| **响应式（< 1024px）** | sidebar 抽屉模式 · 默认隐藏 · 顶部 nav 加汉堡按钮 toggle |
| **持久化** | localStorage `sidebar-collapsed` · 跨 session 保留 |

#### 3.6.4 给 UE 同事的 Figma 工作流提示

1. **Frame 尺寸**：1440 × 900（桌面） · sidebar 240px + 主内容 1200px · 折叠时 64 + 1336px
2. **关键自画**：
   - **折叠/展开动画** · 用 Figma Smart Animate · 240px → 64px · 文字/徽章 fade out
   - **菜单项 active 状态** · 左侧 2px 边 + 半透明背景
   - **分组折叠展开**（可选） · 如需节省空间，分组标题可点击折叠子项
3. **复用 antd**：`<Menu>` 组件支持多级 · `<Tooltip>` 用于折叠态图标 hover 提示
4. **导出**：Figma 链接发研发，研发对照 §3.6.1 JSX 类名 + Tailwind 实现
5. **响应式设计**：< 1024px 时 sidebar 改 drawer 模式（Mask 遮罩 + slide in）

#### 3.6.5 V3.6 决策（用户 2026-07-10 拍板）

| 决策 | 选项 | 状态 |
|---|---|---|
| **L** = 整体架构改为 Sidebar 多级菜单 | 方案 A 顶 Tab / 方案 B Dashboard 内 Tab / **方案 C 侧边栏 Sidebar** | ✅ **方案 C**（用户拍） |
| **M** = 5 大分组依据 | V1 4 大模块 + V3 新增 AI 推送 | ✅ 已定 |
| **N** = 14 page 路由映射 | 5 分组 + 14 子项 | ✅ 已定 |

---

## 6. 视觉 token 速查表（UE 同事复用）

> 整本 design-spec.md 共用的视觉 token，让 UE 同事画 Figma 时直接复制。

### 6.1 颜色

```css
/* 主色（V1 既有） */
--color-primary: #6366f1;        /* indigo-500 */
--color-primary-hover: #4f46e5;  /* indigo-600 */
--color-bg-page: #050914;        /* 页面深蓝黑 */
--color-bg-card: #0c1024;        /* 卡片深蓝灰 · opacity 80% */
--color-text-primary: #f1f5f9;   /* 主要文字 */
--color-text-secondary: #8b8fa3; /* 辅助文字 */

/* V2 既有 */
--color-summary-gradient: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%);

/* 🆕 V3 新增 */
--color-plan-gradient: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(6,182,212,0.1) 100%);
  /* 学习计划：emerald → cyan */
--color-collection-gradient: linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(168,85,247,0.1) 100%);
  /* 题单：blue → purple */
--color-daily-gradient: linear-gradient(135deg, rgba(245,158,11,0.1) 0%, rgba(249,115,22,0.1) 100%);
  /* 每日一题：amber → orange */
--color-streak-badge: #f59e0b;   /* 连续天数徽章 */

/* V3 标签维度配色 */
--color-tag-direction: #60a5fa;  /* A 面试方向：blue */
--color-tag-stack: #a78bfa;      /* B 技术栈：violet */
--color-tag-company: #f59e0b;    /* C 公司轮次：amber */

/* 状态色 */
--color-success: #34d399;        /* emerald-400 */
--color-warning: #fbbf24;        /* amber-400 */
--color-error: #ef4444;          /* red-500 */
```

### 6.2 字号 / 字重

```
H1（页面标题）：24px / 700
H2（卡片标题）：18px / 600
H3（小标题）：16px / 600
正文：14px / 400
辅助：12px / 400
统计数字：36px / 700（Stat 卡）
按钮：14px / 500
进度数字：14px / 600
```

### 6.3 间距

```
页面 padding: 24px (px-6 py-8)
卡片 padding: 24px (p-6)
卡片之间: 16px (gap-4) / 24px (gap-6)
区块之间: 32px (mb-8)
Tag 之间: 8px (gap-2)
按钮组之间: 12px (Space size="middle")
```

### 6.4 圆角 / 阴影

```
卡片圆角: 12px
按钮圆角: 8px
Tag 圆角: 6px
输入框圆角: 8px

阴影:
- 卡片默认: 0 2px 8px rgba(0,0,0,0.2)
- 卡片 hover: 0 8px 24px rgba(99,102,241,0.3)
- 创建按钮: 0 4px 16px rgba(99,102,241,0.4)
- 计划卡: 0 2px 8px rgba(16,185,129,0.15)
- 每日一题卡: 0 2px 8px rgba(245,158,11,0.15)
```

### 6.5 组件库

```
UI 组件: Antd 5 (V2 已装, commit 9631d2d)
图标: @ant-design/icons (V2 已装)
图表: recharts (V2 已装)
样式: Tailwind CSS (V1 既有) + CSS Variables (V2 v2-settlement.css)
状态管理: React useState / useEffect (V1 模式)
服务端状态: fetch + useEffect (V1 模式)
测试: Vitest + RTL + happy-dom (V1 既有)
```

---

## 7. 给 UE 同事的 Figma 工作流提示（汇总）

### 7.1 Figma 文件结构建议

```
📁 Intervue V3 Design (新文件)
├── 📄 Cover
├── 🎨 Tokens (复用 §6 视觉 token)
├── 🧩 Components (复用 V2 DailySummaryCard + ProfilePage 风格)
├── 📱 Frames
│   ├── 🖥️ Desktop 1440
│   │   ├── /plan
│   │   ├── /plan/[id]
│   │   ├── /collections
│   │   ├── /collections/[id]
│   │   ├── /dashboard (DailyChallengeCard 在顶部)
│   │   ├── /learn (TagFilter)
│   │   └── /review (TagFilter)
│   └── 📱 Mobile 375 (V3.x 后续)
└── 🔄 Flows (用户旅程)
```

### 7.2 Figma 操作清单

1. **拉 antd Design Kit** → Figma Community → 搜 "Ant Design 5"
2. **创建 Tokens 文件** → 把 §6.1 颜色 / §6.2 字号 / §6.3 间距 全复制为 Figma Variables
3. **创建组件**：
   - `<CollectionCard>` 通用题单卡（3 列响应式）
   - `<DailyChallengeCard>` 每日一题卡（amber 渐变）
   - `<PlanCard>` 当前活跃计划卡（emerald 渐变）
   - `<TagFilter>` 标签筛选器（3 维度分组）
4. **画 4 个 Frame**：参照 §3.1-§3.4 的 JSX 结构 + 视觉 mockup 表
5. **加交互**：hover / focus / active / disabled / loading 5 状态（每组件 × 5 状态 = 20-30 variants）
6. **导出**：把 Figma 链接发给研发，研发对照 §3.1-§3.4 的 JSX 类名实现

### 7.3 与研发的协作约定

- **研发实现的 Tailwind 类名**已经写在 §3.1.1 / §3.2.1 / §3.3.1 / §3.4.1，UE 可以直接对照
- **每个 antd 组件的 props**（如 `<Progress strokeColor>` / `<Tag color>`）已标注，UE 画 mockup 时用同样参数
- **视觉 token 已统一**（§6.1 / §6.4），UE 不需要重复定义

### 7.4 设计交付检查清单

- [ ] §3.1 /plan Frame（桌面 + 移动）
- [ ] §3.2 /collections Frame（桌面 + 平板 + 移动）
- [ ] §3.3 DailyChallengeCard Frame（dashboard 内嵌）
- [ ] §3.4 /learn TagFilter Frame（5 状态变体）
- [ ] §6 视觉 token 已复制为 Figma Variables
- [ ] 每个组件 ≥ 3 个状态变体（default / hover / loading）
- [ ] 与 V2 沉淀层 DailySummaryCard 风格一致（圆角 12px + 半透明深色）

---

## 4. 交互细节（必填 · 状态机）

### 4.1 `/plan` 关键状态表（6 状态）

| 状态 | 触发 | 视觉反馈 | 用户可操作 |
|---|---|---|---|
| **加载中** | 进入页面 | 当前计划卡显示 skeleton + 历史列表 skeleton | 等 |
| **正常（无计划）** | 新用户没创建过计划 | Empty 插画 + "创建你的第一个学习计划" CTA | 点 CTA → 打开创建表单 |
| **正常（有计划）** | 当前活跃计划存在 | 完整 6 区块渲染 | 详情 / 刷新 / 结束 |
| **创建中** | 点"+ 创建新计划" | 模态弹出表单（name / date / weekly_target） | 填表 → 提交 / 取消 |
| **创建失败** | 表单字段错 / 同名冲突 | 表单字段红框 + 错误提示 | 改字段 → 重提交 |
| **刷新中** | 点"刷新进度"按钮 | 按钮变 loading + "刷新成功" toast | 不可重复点 |

### 4.2 `/collections` 关键状态表（5 状态）

| 状态 | 触发 | 视觉反馈 | 用户可操作 |
|---|---|---|---|
| **加载中** | 进入页面 | 5 个题单卡 skeleton | 等 |
| **正常** | 列表加载成功 | 5-8 个题单卡 + 完成度进度条 | 进详情 / 订阅 |
| **已订阅高亮** | 已订阅题单 | 卡左上角 ⭐ 图标 + 进度条 | 继续刷 / 取消订阅 |
| **筛选中** | 点筛选标签 | 列表实时筛选 + skeleton 过渡 | 选其他标签 |
| **0 题单** | 后端返空 | Empty "题单建设中，敬请期待" | — |

### 4.3 `DailyChallengeCard` 关键状态表（6 状态）

| 状态 | 触发 | 视觉反馈 | 用户可操作 |
|---|---|---|---|
| **加载中** | dashboard fetch | 卡显示 skeleton | 等 |
| **正常（未完成）** | 当日未答 | 完整题目 + "开始答"按钮 + 连续天数 | 点"开始答" |
| **正常（已完成）** | 当日已答 | ✅ 图标 + "今日完成" + 连续天数 | 看历史 / 关闭 |
| **跨日 23:59→0:00** | 0 点切换 | 题目自动换 + streak 重置（如未连续） | — |
| **当日无题** | DB 故障 / 200 题 < 当日 hash | 隐藏卡片（dashboard 正常显示其他卡） | — |
| **错误** | API 504 | "今日题目加载失败" + "重试"按钮 | 点重试 |

### 4.4 `/learn` TagFilter 关键状态表（5 状态）

| 状态 | 触发 | 视觉反馈 | 用户可操作 |
|---|---|---|---|
| **未选** | 默认 | 标签灰色未选中 | 点选 |
| **单选** | 点 1 个标签 | 标签高亮 + 列表实时筛选 | 取消 / 加选 |
| **多选** | 选 ≥ 2 个标签 | 标签全高亮 + 列表"任一命中"筛选 | 取消 / 加选 |
| **0 命中** | 选中标签组合无题 | Empty "无匹配题目，试试其他标签" | 取消标签 |
| **加载中** | 防抖 300ms 后 | 列表 skeleton 0.3s | 等 |

---

## 5. 视觉规范（必填）

### 5.1 颜色（复用 V1 + V2，新增 V3 配色）

| 用途 | 色值 | 说明 |
|---|---|---|
| 主题色 | `#6366f1` (indigo-500) | V1 既有色 |
| V3 题单卡背景 | `bg-gradient-to-br from-blue-500/10 to-purple-500/10` | V3 新增，让题单有"系列"感 |
| V3 计划卡背景 | `bg-gradient-to-br from-emerald-500/10 to-cyan-500/10` | V3 新增，让计划有"目标"感 |
| DailyChallenge 渐变 | `bg-gradient-to-br from-amber-500/10 to-orange-500/10` | V3 新增，每日一题特殊感 |
| 标签 - 算法 | `#a78bfa` (violet-400) | V3 系统标签配色 |
| 标签 - 系统设计 | `#34d399` (emerald-400) | V3 系统标签配色 |
| 标签 - 前端 | `#60a5fa` (blue-400) | V3 系统标签配色 |
| 标签 - 字节/阿里 | `#f59e0b` (amber-400) | V3 公司标签配色 |
| 文字主色 | `#f1f5f9` | V1 既有 |
| 文字辅助 | `#8b8fa3` | V1 既有 |
| 卡片背景 | `bg-[#0c1024]/80` | V1 既有 |
| 页面背景 | `bg-[#050914]` | V1 既有 |

### 5.2 字体（复用 V1）

- 标题（H1）：24px / 700 字重
- 副标题（卡片标题）：16px / 600 字重
- 标签（TagFilter）：14px / 500 字重
- 进度数字：24px / 700 字重
- 正文：14px / 400 字重
- 辅助：12px / 400 字重
- 行高：1.5

### 5.3 间距（复用 V1）

- 卡片内边距：24px
- 卡片之间：16px
- 区块之间：32px
- Tag 间距：8px

### 5.4 组件库（复用 V1 + V2，0 新增依赖）

| 资源 | 来源 | 说明 |
|---|---|---|
| UI 组件 | antd 5（V2 装好） | Card / Skeleton / Progress / Button / Modal / Form |
| 图标 | @ant-design/icons（V2 装好） | PlusOutlined / ReloadOutlined / FireOutlined / BookOutlined |
| 图表 | recharts（V2 装好） | 题单进度条 / 学习计划进度 |
| 状态管理 | React useState / useEffect | 无 Redux 引入 |
| 服务端状态 | fetch + useEffect + 自定义 hooks | 无 SWR / React Query |
| 样式 | Tailwind（V1 既有）+ CSS Variables（V2 新增） | 0 新增 styled-components |

**结论**：V3 前端**0 新增依赖**，与 V1 + V2 完全一致。

### 5.5 圆角 / 阴影（复用 V1 + V2）

- 卡片圆角：12px
- 按钮圆角：8px
- Tag 圆角：6px
- 进度条阴影：`0 2px 8px rgba(99, 102, 241, 0.2)`（V3 新增紫色微光）

---

## AI vs 人分工

| 人（你）适合做 | AI 适合做 |
|---|---|
| ✅ 改"计划"在 nav 的位置 | ✅ 列用户旅程（4 个场景） |
| ✅ 改"题单"卡是渐变色还是纯色 | ✅ 画线框初稿（4 张） |
| ✅ 改 DailyChallengeCard 渐变方向 | ✅ 校验状态机完整性（每页 5-6 状态） |
| ✅ 改 Empty 插画文案 | ✅ 生成视觉规范 5 段 |
| ❌ 不必写组件代码（4 步再做） | ❌ 不必选 antd（V2 已装） |

**核心**：**视觉判断归你，结构化内容 AI 辅助**。

---

## 🎯 硬性 DOD（design-spec.md 完成必须全过）

- [x] 5 段齐全（用户旅程 / 页面地图 / 页面线框 / 交互细节 / 视觉规范）
- [x] ≥ 1 个完整用户旅程（实际 4 个：每日一题 / 学习计划 / 题单跟刷 / 多维筛选）
- [x] ≥ 1 个页面线框图（实际 4 个：/plan /collections /dashboard DailyChallengeCard /learn TagFilter）
- [x] 交互细节 ≥ 5 种状态（实际 4 页 × 5-6 状态 = 22 状态，远超）
- [x] 视觉规范 5 方面齐全（颜色 / 字体 / 间距 / 组件库 / 圆角阴影）
- [ ] **用户验收签字**：待你 review 改视觉判断后写"已验收：<name> <date>"

---

## 📚 相关文档

- [product-doc.md](product-doc.md) — 上游产品意图
- [spec.md](spec.md) — 下游技术脑翻译
- [research.md](research.md) — 0/0.5/0.6 调研（G3 + I1 已拍）
- [V1 母模块 design-spec](../2026-06-22-new-feature-question-bank/design-spec.md)
- [V2 沉淀层 design-spec](../2026-06-28-new-feature-v2-smart-sediment/design-spec.md)

---

## 🔴 触发条件

- 类型：new-feature（V3 全新 UI + 改 /learn + 加 nav）
- 是否涉及 UI 改动：**是**（3 新页 + 1 新卡 + 1 改 + 1 加 nav 入口）
- 必填：**是**
- 已触发：✅
