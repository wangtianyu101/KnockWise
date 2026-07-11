---
title: 产品文档 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [product-doc, 1步, 产品脑, v3-mockup-align, knockwise, refactor]
related:
  - [research.md](research.md) — 上游调研（11 章节 · 17h 路径）
  - [spec.md](spec.md) — 下游技术契约（同目录）
  - V3 design-spec: [../2026-07-09-new-feature-question-bank-expand/design-spec.md](../2026-07-09-new-feature-question-bank-expand/design-spec.md) — V3.6 Sidebar 设计（已写，本文档不重复）
---

# 产品文档：KnockWise 前端对齐重构

> **一句话**：把当前"4 套品牌名 + 8 处横向 nav + 17 page"的前端，重构成"统一 KnockWise 品牌 + 1 套左侧 Sidebar 导航 + 17 page 视觉一致"。
>
> **作者**：产品脑（用户视角 · 不写技术）· 用户决策已锁（三档全改 / 接受 17h / 进 1 规格）
> **重要前提**：**重构不改业务行为**。所有 API、数据流、用户旅程、权限模型不变 —— 只换壳（导航 + 视觉 + 品牌）。

---

## 0. 全局架构图（CLAUDE.md §1.5 强制）

```
                    用户视角：4 个核心场景
                    ┌─────────────────────────┐
                    │ 1. 打开看仪表盘（高频） │
                    │ 2. 开始一次面试         │
                    │ 3. 刷题/复习            │
                    │ 4. 后台管理（admin）    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────┐
                  │     KnockWise 统一壳（重构后）    │
                  │                                  │
                  │  ┌────────────────────────────┐  │
                  │  │ 顶部 nav（极简）            │  │
                  │  │  logo + 用户菜单            │  │
                  │  └────────────────────────────┘  │
                  │  ┌──────┐ ┌──────────────────┐  │
                  │  │      │ │                  │  │
                  │  │ 左   │ │   主内容区        │  │
                  │  │ 侧   │ │   (17 page)       │  │
                  │  │ Side │ │                  │  │
                  │  │ bar  │ │                  │  │
                  │  │      │ │                  │  │
                  │  │ 5 大 │ │                  │  │
                  │  │ 分组 │ │                  │  │
                  │  └──────┘ └──────────────────┘  │
                  └──────────────────────────────────┘
                                 │
                                 ▼
                  现有业务能力（API + 数据 + 权限）
                  （不重构 · 数据流不变）
```

**核心定位**：壳层（导航/视觉/品牌）重建，业务（API/数据/逻辑）一行不动。

---

## 1. 重构目标（用户视角）

### 1.1 用户原话
> "你验证下目前的前端 和这个差距很大呀"
> "改成 KnockWise 现在整个项目都叫这个 相关的全改掉"

### 1.2 用户能感知到的变化

| 场景 | 重构前 | 重构后 |
|---|---|---|
| **打开应用第一眼** | 顶部 7 个横向 tab + 混乱品牌（DevBrain / CodeMock / Intervue） | 左侧 Sidebar 5 大分组 + 顶部极简 + 统一 KnockWise |
| **找 AI 推送历史** | ❌ 找不到（无入口） | ✅ Sidebar "AI 推送 → 推送历史" |
| **找题库管理** | ❌ 找不到（admin 无入口） | ✅ Sidebar 底部 "Admin → 题库管理" |
| **找设置** | ❌ 找不到（无入口） | ✅ Sidebar "我的 → 设置" |
| **看仪表盘"最近 3 次面试"** | 只能去"面试历史"翻列表 | ✅ Dashboard Hero 卡直接显示 3 个迷你雷达 |
| **登录页品牌** | CodeMock 标题 + CodeMock logo | KnockWise 标题 + KnockWise logo |
| **退出登录** | 顶部右侧小红字"退出" | Sidebar 底部用户菜单 → 退出 |

### 1.3 用户感知不到的变化（技术性，不进 product-doc）

> 这些是实现细节，不写进 product-doc.md（按 CLAUDE.md §1.6 产品 vs 技术分文件规则）。
> - localStorage key 从 `codemock_token` → `knockwise_token`（双 key fallback，用户无感）
> - 后端 logger 从 `codemock.xxx` → `knockwise.xxx`（运维日志，技术细节）
> - 5 个新页面用 EmptyState 占位（用户看到的是"建设中"提示，不进 product-doc 解释 EmptyState 实现）

---

## 2. 用户旅程（CLAUDE.md § 阶段 1 强制）

### 场景 1：第一次登录看仪表盘（高频 · 重构首日验证）

```
1. 用户在 / 登录页输入邮箱密码
   → 看到品牌名 "KnockWise"（之前是 CodeMock）
   → 看到 SVG logo 已更新
2. 登录成功跳 /dashboard
3. 用户看到新 Dashboard：
   ┌────────────────────────────────────────────────┐
   │ 顶部 nav：[KnockWise logo]              [用户]  │
   ├──────┬─────────────────────────────────────────┤
   │ 侧栏  │ "下午好，开发者"                       │
   │ 5 分组 │  ┌─────────────────────────────────┐  │
   │      │  │ 🔥 Hero: 开始 Mock 面试 (粉紫)    │  │
   │ 概览  │  │ 上次 78分 + 3 个迷你雷达(字节/阿里/腾讯) │
   │ 面试  │  │ [开始面试 →]  [查看历史]         │  │
   │ 学习  │  └─────────────────────────────────┘  │
   │ 知识库│  ┌─────────────────────────────────┐  │
   │ AI 推送│ │ AI 推荐卡 (4 条 [补][练][读][盘]) │  │
   │ 我的  │  └─────────────────────────────────┘  │
   │      │  ┌─────────────────────────────────┐  │
   │ Admin│  │ 5 列横条统计 (答题/命中率/复习/打卡/进度)│  │
   │  🆕  │  └─────────────────────────────────┘  │
   └──────┴─────────────────────────────────────────┘
4. 用户点 Sidebar "面试 → 今日面试" → 跳 /interview/profile
5. 用户点 Sidebar "AI 推送 → 推送历史" → 跳 /ai/history（**之前找不到的入口**）
6. 用户点 Sidebar 底部用户菜单 → 退出登录
```

### 场景 2：admin 用户管题库（低频 · 重构价值最大的"找不到入口"修复）

```
1. admin 登录 → /dashboard
2. Sidebar 滚到底部，看到 "Admin" 分组：
   - 🆕 题库管理 → /admin/questions
   - 🆕 手动同步 → /admin/sync
3. 点"题库管理" → 表格列出题库，可改 topic/difficulty
4. 点"手动同步" → 选数据源 → 试跑 → 看历史
5. 之前：用户根本找不到这两个功能
```

### 场景 3：移动端访问（<1024px 屏幕）

```
1. 用户在手机打开 /dashboard
2. Sidebar 默认隐藏（抽屉模式）
3. 顶部 nav 出现汉堡按钮
4. 点汉堡 → Sidebar 从左滑入 + 背景半透明
5. 点背景 → 关闭抽屉
6. ESC 键 → 关闭（桌面浏览器）
```

### 场景 4：老用户升级（KnockWise 改名迁移）

```
1. 老用户浏览器 localStorage 有 `codemock_token`（旧版登录留下的）
2. 重构部署后，用户刷新页面
3. 前端代码检测到 `codemock_token` 存在 → 自动迁移到 `knockwise_token`（双 key fallback）
4. 用户不掉登录，感知 0
5. 第二次刷新：旧 key 已清，只剩新 key
```

> ⚠️ 老用户登录的兼容是技术细节，本节只是为了让 product-doc 覆盖完整用户体验。

---

## 3. 业务规则（产品边界）

### 3.1 改什么

| 改什么 | 范围 | 业务影响 |
|---|---|---|
| 品牌名 | 全部 70+ 处统一为 KnockWise | 0（纯文案） |
| 顶部 nav | 8 个 page 删 nav → 顶部极简 + 用户菜单 | 0（只是换位置）|
| 左 Sidebar | 新增 240px 固定 Sidebar | 0（新增导航，不删任何功能） |
| Dashboard Hero | 新增粉紫渐变卡 + 3 迷你雷达 + 5 列 stats | 0（信息密度更高，不是新增功能）|
| 5 个新路由 | admin / ai / settings 入口 | **+5 个用户原本找不到的功能入口** |
| localStorage key | 改名 + 双 key fallback | 0（迁移机制）|

### 3.2 不改什么（业务行为冻结）

> CLAUDE.md §1.7 重构定义："不改业务行为"。下面是**明确不改**的范围：

| 不改 | 文件 / 模块 |
|---|---|
| API 端点（除新增 1 个 `/api/interviews/recent`）| `backend/api/*.py` 全部 |
| 数据模型 / DB schema / migration | `backend/models/` + `backend/core/database.py:_MIGRATIONS` |
| 服务层逻辑 | `backend/services/*.py` 全部 |
| 业务规则 | SM-2 算法 / 评分逻辑 / 追问引擎 |
| 现有 17 page 的核心交互 | dashboard / learn / review / qa / interview 业务流 |
| 现有测试 | 154 测试不动（logger 改名那 30 个断言同步改，逻辑测试不动）|
| 真实 MySQL 数据 | CLAUDE.md §二"绝对不能动"· 冻结 |
| livekit.yaml / 启动脚本业务部分 | 冻结 |
| 项目根目录路径 | `/Users/wangtianyu/IdeaProjects/Intervue/`（git mv 风险大）|

### 3.3 业务边界争议（用户决策已锁）

| 争议点 | 用户拍板 | 产品边界影响 |
|---|---|---|
| 后端 logger 改名（40 处）| 三档全改 | 不影响产品功能，但日志关键字变了（运维搜日志要改 `grep codemock → grep knockwise`）|
| docker-compose DB 名（codemock → knockwise）| 三档全改但**不动真 DB** | docker-compose 改了，新部署用新 DB 名；老部署继续用旧 DB（不影响）|
| 路径 /Users/.../Intervue/ | 不改 | 项目根目录路径保留 Intervue，但 CLAUDE.md 文档里写"项目叫 KnockWise" |

### 3.4 权限模型（Sidebar Admin 分组可见性规则）

**产品定位**：KnockWise 是**单用户产品**（每个用户看自己的数据），但**预留 admin 角色**给将来的多用户/团队场景。

| 用户角色 | Sidebar Admin 分组可见 | 进入 /admin/* | 当前状态 |
|---|---|---|---|
| **普通用户**（dev_user / GitHub 注册）| ❌ 不显示 | 403 | 当前所有用户都属此类 |
| **admin**（预留 role=admin）| ✅ 显示 🆕 徽章 | 200 + 表格 | **后端当前无 admin role 字段**，前端按"当前用户 ID = 1 即 admin"临时判定 |
| **未登录** | ❌ 整个 Sidebar 不渲染 | 跳 / | `getToken()` 返回 null 时 |

**admin 临时判定逻辑**（前端，写在 `Sidebar.tsx`）：

```typescript
const isAdmin = useMemo(() => {
  const token = getToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.user_id === '1' || payload.role === 'admin';
  } catch { return false; }
}, []);
```

**产品边界**：
- 当前阶段 admin = 用户 ID 1（开发者本人）即可，无需后端 role 字段
- 未来要做多用户时，把"用户 ID = 1"改成后端 `user.role === 'admin'` 即可，Sidebar 不用改

### 3.5 KnockWise 品牌资产 brief（给 UE 同事）

> 用户原话："改成 KnockWise 现在整个项目都叫这个" —— KnockWise 命名已锁定，下面是品牌资产的视觉 brief：

| 资产 | 当前状态 | 需求 | 优先级 |
|---|---|---|---|
| **Logo SVG** | 登录页用 `<path d="M8.625 12a.375...>` SVG（对话气泡 + 感叹号，紫色渐变）| 重新设计一个 KnockWise 专属 logo · 候选元素：① 敲门图标（呼应 Knock）② 大脑 + 击打 ③ 答题卡 + 闪烁 | 🔴 P0 |
| **品牌色** | 主色 `#6366f1` indigo | **沿用 V3 主色不变**（UE 不要改色，只改 logo）| 🟢 |
| **品牌字体** | Inter + 系统字体 | **沿用**（UE 不要换字体）| 🟢 |
| **Favicon** | 无 | 加 KnockWise logo 缩略图 | 🟡 P1 |
| **OG 分享图** | 无 | 1200×630 含 KnockWise 品牌 + "AI 面试官" 标语 | 🟡 P2 |
| **404/500 页** | 无 | EmptyState + KnockWise logo | 🟡 P2 |
| **Email 模板** | 无 | 欢迎邮件用 KnockWise 品牌 | ❌ Out of Scope |

**Logo 设计候选**（UE 自选）：
- ① **敲门图标**：门 + 击打波纹 + 渐变（呼应 "Knock"）
- ② **答题卡 + 闪烁**：模拟面试瞬间 + 知识可视化
- ③ **几何抽象**：K 字母 + 几何线 + 紫色渐变

**品牌色不变**：
- 主色 `#6366f1`（indigo-500）
- 强调色 `#a78bfa`（violet-400）
- 警告色 `#f59e0b`（amber-500）
- 背景 `#050914`（深蓝黑）

**Skill（UE 同事参考）**：
- Logo 应在 28×28 / 56×56 / 200×200 三档尺寸下都清晰
- 单色版（白色剪影）也要能识别
- 暗黑背景下用渐变彩色，亮色背景下用深色

### 3.6 域名 / 部署（产品视角 · 待用户拍）

| 项 | 现状 | 用户拍板 | 备注 |
|---|---|---|---|
| **生产域名** | localhost:3000（前端） + localhost:8000（后端）| 🟡 未拍 | 如果是 knockwise.app / knockwise.io 等需注册 |
| **API 路径前缀** | `/api/*` | 🟢 不改 | `/api/*` 是稳定的 API 契约 |
| **登录页 URL** | `/`（首页） | 🟢 不改 | 已合理 |
| **Dashboard 默认 URL** | `/dashboard` | 🟢 不改 | 已合理 |

> 这些是产品/运维决策，不是技术决策。如果用户有域名意向需要在 2 计划阶段落地。

---

---

## 4. 信息架构（Sidebar 5 大分组）

### 4.1 Sidebar 内容（按 mockup §sidebar 锁定）

```
┌─────────────────────────┐
│ [logo] KnockWise  [折叠] │  ← SidebarHeader
├─────────────────────────┤
│ [🔍 搜索页面...]         │  ← SidebarSearch
├─────────────────────────┤
│ ▼ 概览                   │  ← SidebarGroup
│   • 今日概览             │  ← SidebarItem (active)
│                          │
│ ▼ 面试                   │
│   • 今日面试       [新]   │
│   • 历史报告             │
│   • 面试配置             │
│                          │
│ ▼ 学习复习               │
│   • 题目浏览             │
│   • 复习中心             │
│   • 学习计划       [V3]   │
│   • 精选题单       [V3]   │
│                          │
│ ▼ 知识库                 │
│   • 笔记浏览             │
│   • 问答社区             │
│   • 报告中心             │
│                          │
│ ▼ AI 推送                │
│   • 今日推荐       [V3]   │
│   • 推送历史             │
│                          │
│ ─────────                │
│ • 我的画像               │
│ • 设置                   │
│                          │
│ ─────────                │
│ ADMIN                    │
│ • 题库管理         🆕    │
│ • 手动同步         🆕    │
├─────────────────────────┤
│ V3 沉淀层       ● 启用   │  ← SidebarFooter
└─────────────────────────┘
```

### 4.2 视觉规范（产品视角，不写代码）

| 元素 | 视觉 | 用户体验意义 |
|---|---|---|
| Sidebar 宽度 | 240px（可折叠 64px） | 默认展开看得见全部入口；折叠节省屏幕给主内容 |
| 5 大分组标题 | 小字大写 + 灰色 + 上间距 | 视觉分组，不喧宾夺主 |
| 当前页 | 左侧 indigo 边条 + 浅紫背景 | 用户永远知道自己在哪 |
| 新功能/V3 徽章 | 右上小标签 + 半透明 indigo 边框 | 引导用户发现新功能（不刺眼）|
| Admin 徽章 🆕 | 琥珀色背景 + 白字 | 强调这是 admin 专属，避免普通用户困惑 |
| 移动端 <1024px | 默认隐藏 + 汉堡按钮 | 不挤压主内容 |
| 折叠动画 | 300ms ease-out | 给"专业"感（用户感知不到但潜意识加分）|

---

## 5. 5 个新路由（用户视角 · 不写实现）

| 路由 | 目标用户 | 进入路径 | 视觉 |
|---|---|---|---|
| `/admin/questions` | admin（自己） | Sidebar 底部 Admin → 题库管理 | 表格 + 行编辑 + toast 反馈 |
| `/admin/sync` | admin（自己） | Sidebar 底部 Admin → 手动同步 | 数据源选择 + 试跑 + 历史表 |
| `/ai/today` | 所有用户 | Sidebar AI 推送 → 今日推荐 | **当前 dashboard 顶部已有 AI 推荐卡，独立页是"全部推荐"** |
| `/ai/history` | 所有用户 | Sidebar AI 推送 → 推送历史 | 历史日报列表 |
| `/settings` | 所有用户 | Sidebar 我的 → 设置 | 简单表单（昵称/邮件订阅/主题）占位 |

**EmptyState 占位**：用户进 `/admin/questions` 等 5 个新页面，看到"建设中 · 该模块即将上线"插画 + 返回 Dashboard 按钮 —— 不误导，不 404，不空白。

---

## 6. 范围（In Scope / Out of Scope）

### 6.1 ✅ In Scope（17h 重构内做）

| 项 | 来源 |
|---|---|
| Sidebar 6 组件 + _app.tsx 注入 | research.md §2.1 P1 |
| Dashboard 重写（Hero + 3 雷达 + 5 列 stats + 3 卡） | P2 |
| 5 个新路由壳（ai-today / ai-history / admin-questions / admin-sync / settings） | P3 |
| 后端 `/api/interviews/recent` 端点 | P3 |
| 17 page 删原 nav | P4a |
| KnockWise 三档全改（70+ 处 + 40 logger + 30 测试同步）| P4a + P4b + P4c |
| scripts 改名（PID/log）| P4b |
| docker-compose 改名（不改真 DB）| P4b |
| playwright 装 + 25 截图测试 + 真起 next dev 比对 | P5 |

### 6.2 ❌ Out of Scope（这次不做）

| 不做 | 原因 |
|---|---|
| 业务功能新增（如 AI 推送真有"历史"，admin 真接 sync-history）| CLAUDE.md §1.7 重构不改业务行为 |
| 项目根目录 git mv（/Intervue/ → /KnockWise/）| 用户没拍板 git mv；且风险大 |
| 真实 MySQL 数据迁移（codemock DB → knockwise DB）| CLAUDE.md §二冻结 + 用户没要求 |
| V3.7 DailyChallengeCard（mockup 有，V3 暂缓）| plan.md V3.2 已暂缓 |
| 模块快捷链接 5 入口（mockup 有 V3.4 重构）| plan.md V3.4 未拍 |
| learn/review/qa 详情页 TagFilter | V3.x 已拍延后 |
| 多端响应式深度优化（仅做 < 1024px 折叠）| 重构范围控制 |
| E2E 测试覆盖率提升（除 playwright 截图外）| 工时限制 |

---

## 7. 验收标准（产品视角 · 用户能验证的）

### 7.1 视觉验收（用户打开页面就能看）

- [ ] 顶部 nav 不再有 7 个 tab（只剩 logo + 用户菜单）
- [ ] 左侧 240px Sidebar 出现，5 大分组可见
- [ ] Sidebar 当前页有 indigo 左边条
- [ ] Dashboard Hero 卡是粉紫渐变 + "开始 Mock 面试" 大按钮
- [ ] Dashboard 显示 3 个迷你雷达（字节/阿里/腾讯）
- [ ] Dashboard 5 列横条统计（答题/命中率/复习/打卡/进度）
- [ ] 全部 logo/标题/文档/SVG logo 文案统一为 KnockWise（无 DevBrain/CodeMock/Intervue 残留）
- [ ] Sidebar 底部有 "题库管理 / 手动同步" admin 入口
- [ ] 移动端 <1024px Sidebar 默认隐藏 + 汉堡按钮可唤出

### 7.2 行为验收（用户操作能验证）

- [ ] 点 Sidebar 每个菜单能跳到正确 page
- [ ] 5 个新路由壳显示 "EmptyState 建设中" 占位
- [ ] 老用户刷新不掉登录（localStorage 双 key fallback）
- [ ] Sidebar 折叠按钮可切换 240/64px
- [ ] Sidebar 搜索框输入文字实时过滤菜单
- [ ] 现有 154 测试全部通过 + 新增 62 测试全过
- [ ] playwright 25 截图测试 baseline 比对通过

### 7.3 验收后用户拍 "verify 通过"

按 CLAUDE.md § 一.三 阶段 5：用户口头确认（或明确说"verify 完成"）才能进 6 复盘。

---

## 8. 关联文档

- [research.md](research.md) — 调研（含 §9 补调研 7 项全部 + §10 修订路径 17h）
- [spec.md](spec.md) — 技术契约（架构 / 组件 Props / API Schema / 测试矩阵 / KnockWise 迁移）
- [V3 design-spec §3.6](../2026-07-09-new-feature-question-bank-expand/design-spec.md) — Sidebar 设计已写（视觉规范）
- [V3 mockup](../2026-07-09-new-feature-question-bank-expand/mockups/v3-mockup.html) — 视觉参照
- [CLAUDE.md §1.5 架构图规则](../../CLAUDE.md) · [§1.6 产品 vs 技术分文件](../../CLAUDE.md) · [§1.7 重构路径](../../CLAUDE.md)