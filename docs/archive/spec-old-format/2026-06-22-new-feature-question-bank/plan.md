# KnockWise 实施计划 ✅ 已落地

> 5 阶段全部完成。架构演进过程见 [`架构演进.md`(../10-架构/架构演进.md)。
>
> 原描述：基于三模块架构，从当前 KnockWise 代码库出发，分 5 阶段推进。

---

## 当前状态盘点

| 资产 | 位置 | 状态 |
|---|---|---|
| ORM Models (6个) | `backend/models/__init__.py` | ✅ 已完成 |
| Session 持久化 | `backend/services/interview_service.py` | ✅ 已完成 |
| LangGraph 面试引擎 | `backend/agents/` | ✅ 已完成 |
| API 路由 (auth/interview/report/profile) | `backend/api/` | ✅ 已完成 |
| 前端 6 页面 (Next.js) | `frontend/pages/` | ⚠️ 旧版，需升级 |
| AI 日报脚本 | `agent-memory/scripts/ai_news.py` | ✅ 独立运行 |
| 统计脚本 | `agent-memory/scripts/stats.py` | ✅ 独立运行 |
| Obsidian 同步脚本 | `agent-memory/scripts/sync_obsidian.py` | ✅ 独立运行 |
| macOS 定时任务 | `~/Library/LaunchAgents/` | ✅ 已配置 |
| Python 3.12 venv | `Intervue/backend/.venv/` | ✅ 已配置 |
| MySQL 8.4 | Docker Compose | ✅ 已配置 |

---

## Phase 1: 基础设施统一 (2-3天)

### 1.1 邮箱密码登录

**后端：**
- [ ] `User` 模型新增字段：`password_hash` (String(256), nullable), `display_name` (String(128))
- [ ] 新增 `POST /api/auth/register` — 邮箱 + 密码 + 昵称注册，bcrypt 哈希
- [ ] 新增 `POST /api/auth/login` — 邮箱 + 密码登录，返回 JWT
- [ ] 新增 `POST /api/auth/refresh` — JWT 刷新
- [ ] `dependencies.py` `get_current_user` 支持从邮箱密码 JWT 解析用户

**前端：**
- [ ] `pages/login.tsx` 改造：双 Tab（邮箱登录 / GitHub 登录）
- [ ] 新增 `pages/register.tsx` 注册页
- [ ] `lib/api.ts` 新增 `login()`, `register()` 方法

**依赖：**
```bash
pip install bcrypt==4.2.0
```

### 1.2 统一配置管理

- [ ] 创建 `backend/.env.example` 模板
- [ ] `core/config.py` 新增：`SMTP_*`, `JWT_REFRESH_EXPIRE_MINUTES`
- [ ] 统一 agent-memory 脚本的 API 配置路径（指向 codemoss config）

### 1.3 项目迁移准备

- [ ] 将 `ai_news.py`, `stats.py` 从 agent-memory 复制到 `Intervue/backend/services/`
- [ ] 适配路径：Obsidian 目录、CLAUDE_DIR、REPO_DIR 改为 config 可配
- [ ] 原有 agent-memory 脚本保留（向后兼容）

---

## Phase 2: 面试模块完善 (3-4天)

### 2.1 后端增强

- [ ] `GET /api/interviews?status=&round=&topic=&page=&size=` — 面试列表分页 + 筛选
- [ ] `GET /api/analytics/overview` — 综合得分、趋势、面试次数
- [ ] `GET /api/analytics/radar?range=3month` — 雷达图数据（按 topic 聚合 score）
- [ ] `GET /api/analytics/trends` — 各 topic 得分趋势（首末对比）
- [ ] `GET /api/analytics/recommendations` — AI 推荐练习（薄弱 × 高频）
- [ ] `POST /api/profile/resume` — 简历上传 → pypdf 提取 → LLM 自动填 tech_stack/years/level
- [ ] `PUT /api/profile/me` — 已实现，确保前端对接无误

### 2.2 前端升级

- [ ] 复用 `index.html` 设计稿，改造 `pages/`：
  - [ ] `pages/dashboard.tsx` — 三模块卡片仪表盘
  - [ ] `pages/interview/profile.tsx` — 个人信息 + 简历上传
  - [ ] `pages/interview/history.tsx` — 面试记录列表 + 筛选
  - [ ] `pages/interview/analytics.tsx` — 能力分析（雷达 + 趋势 + 推荐）
  - [ ] `pages/interview/setup.tsx` — 面试配置（保留原有，样式升级）
  - [ ] `pages/interview/room.tsx` — 面试中（保留原有，样式升级）
  - [ ] `pages/interview/report.tsx` — 面试报告（保留原有，样式升级）

- [ ] 共享组件：
  - [ ] `components/Layout.tsx` — 顶部导航 + 面试子导航
  - [ ] `components/GlassCard.tsx` — 通用玻璃卡片
  - [ ] `components/ProgressBar.tsx` — 渐变进度条
  - [ ] `components/StatCard.tsx` — 统计数字卡片

### 2.3 报告真实数据接入

- [ ] `report_agent.py` 生成真实雷达数据（当前写死 3 分）
- [ ] `POST /api/reports/interview/{id}` 调用 agent 生成完整报告
- [ ] 前端 `report.tsx` 对接真实数据

---

## Phase 3: 知识管理模块 (3-4天)

### 3.1 后端 — Obsidian 集成

**文件：`backend/services/obsidian_service.py`**
- [ ] `ObsidianService` 类，封装 vault 读写：
  - [ ] `list_files(path)` — 递归列出所有 .md 文件
  - [ ] `read_note(rel_path)` — 读单篇，解析 frontmatter
  - [ ] `write_note(rel_path, content)` — 写/更新笔记
  - [ ] `search_notes(query)` — 全文搜索 (遍历 + 字符串匹配)
  - [ ] `parse_links(content)` — 提取 `[[wikilinks]]`
  - [ ] `build_graph()` — 构建知识图谱（节点=文件，边=wikilink）
  - [ ] `get_stats()` — 笔记数、字数、文件夹分布
  - [ ] `get_backlinks(rel_path)` — 反向链接
  - [ ] `get_daily_note(date)` — 每日笔记

**API：`backend/api/knowledge.py`**
- [ ] `GET /api/knowledge/tree` — 文件树
- [ ] `GET /api/knowledge/search?q=` — 全文检索
- [ ] `GET /api/knowledge/note?path=` — 读笔记（渲染 markdown → HTML 或返回 raw）
- [ ] `PUT /api/knowledge/note?path=` — 创建/更新
- [ ] `GET /api/knowledge/graph` — 知识图谱 (nodes + edges JSON)
- [ ] `GET /api/knowledge/stats` — 写作统计
- [ ] `GET /api/knowledge/backlinks?path=` — 反向链接
- [ ] `GET /api/knowledge/daily?date=` — 每日笔记

**注册路由：** `main.py` 中 `app.include_router(knowledge_router)`

### 3.2 前端

- [ ] `pages/knowledge/browse.tsx` — 文件树浏览 + 搜索
- [ ] `pages/knowledge/note.tsx` — 单篇笔记阅读（markdown 渲染）
- [ ] `pages/knowledge/graph.tsx` — 知识图谱可视化（D3.js force graph）
- [ ] `pages/knowledge/stats.tsx` — 写作统计面板

**依赖：**
```bash
npm install d3 @types/d3 react-markdown remark-gfm
```

### 3.3 双链解析工具

- [ ] `backend/services/markdown_utils.py` — wikilink 解析、frontmatter 解析
- [ ] 支持格式：`[[page]]`, `[[page|alias]]`, `[[page#heading]]`

---

## Phase 4: 信息推送模块 (3-4天)

### 4.1 后端 — 迁移脚本逻辑

**文件：`backend/services/news_service.py`**
- [ ] 从 `ai_news.py` 迁移核心函数：
  - [ ] `fetch_rss_sources()` — RSS 抓取
  - [ ] `summarize_articles()` — LLM 摘要
  - [ ] `generate_daily_report()` — 生成日报
  - [ ] `generate_weekly_report()` — 生成周报
- [ ] 从 `stats.py` 迁移核心函数：
  - [ ] `parse_jsonl_tokens()` — token 统计
  - [ ] `parse_git_stats()` — 代码量统计
  - [ ] `get_daily_stats()` — 日统计查询

**API：`backend/api/news.py`**
- [ ] `GET /api/news/daily?date=` — 获取日报 markdown
- [ ] `GET /api/news/weekly?week=` — 获取周报 markdown
- [ ] `GET /api/news/sources` — RSS 源列表
- [ ] `PUT /api/news/sources` — 更新源配置
- [ ] `POST /api/news/trigger/daily` — 手动触发生成
- [ ] `POST /api/news/trigger/weekly` — 手动触发周报
- [ ] `GET /api/news/history` — 日报/周报历史列表
- [ ] `GET /api/news/stats/summary` — 代码统计摘要
- [ ] `GET /api/news/stats/daily?days=7` — 日统计明细

### 4.2 前端

- [ ] `pages/news/daily.tsx` — 日报浏览（渲染 markdown）
- [ ] `pages/news/weekly.tsx` — 周报浏览
- [ ] `pages/news/sources.tsx` — RSS 源管理
- [ ] `pages/news/stats.tsx` — 代码统计（SVG 图表 + 表格）
- [ ] 复用 `stats.py` 的 SVG 生成逻辑（`svg_daily_chart`, `svg_monthly_chart`）

### 4.3 定时任务保持

- [ ] macOS launchd 脚本不变，仍然直接调 Python 生成 Obsidian 文件
- [ ] Web 端只做**读取和展示**，不触发定时任务
- [ ] 手动触发功能仅调用后端 API → 后端执行并写 Obsidian

---

## Phase 5: 跨模块联动 + 打磨 (2-3天)

### 5.1 AI 跨模块推荐

- [ ] `GET /api/recommendations` — 综合推荐
  - [ ] 面试薄弱项 ∩ 知识库相关笔记
  - [ ] AI 日报热点 ∩ 面试题库
  - [ ] 本周高产出日 vs 低产出日 → 节奏建议
- [ ] 仪表盘 "AI 智能推荐" 卡片对接真实数据

### 5.2 仪表盘数据聚合

- [ ] `GET /api/dashboard` — 一次返回所有概览数据：
  ```json
  {
    "interview": {"total": 3, "latest_score": 3.8, "trend": "up"},
    "knowledge": {"total_notes": 38, "topics": 5, "recent": 3},
    "news": {"latest_daily": "2026-06-12", "unread": 4},
    "stats": {"total_tokens": 686000, "total_code": 6808, "active_days": 5},
    "recommendations": [...]
  }
  ```

### 5.3 体验打磨

- [ ] 全局 Loading 状态 (skeleton screen)
- [ ] 错误边界 (ErrorBoundary)
- [ ] Toast 通知组件
- [ ] 空状态占位图
- [ ] 移动端响应式（≤768px）
- [ ] 暗色模式唯一（不做亮色切换）

---

## 技术规范

### 后端约定
- 所有 API 返回 JSON，markdown 内容用字符串字段返回
- 异步 SQLAlchemy 2.0，不用同步 session
- 新 service 用单例模式（与 `InterviewSessionManager` 一致）
- 配置用 `pydantic-settings`，环境变量覆盖

### 前端约定
- Next.js Pages Router（保持现有架构）
- Tailwind CSS 4（保持现有）
- 颜色变量集中定义在 `tailwind.config.js`
- Glass 卡片用 CSS `backdrop-filter` 实现
- SVG 图标优先用内联 `<svg>`，避免额外依赖
- Fira Code + Fira Sans 字体（从 Google Fonts 加载）

### 数据库
- 新表通过 SQLAlchemy ORM 定义
- `Base.metadata.create_all` 自动建表
- 暂不引入 Alembic migration（MVP 阶段）

---

## 时间线

```text
Week 1: Phase 1 (基础设施) + Phase 2 (面试模块完善)
        ├── Day 1-2: 邮箱登录 + 配置统一
        ├── Day 3-4: 面试 API 增强 + 前端仪表盘
        └── Day 5-7: 面试子页面 + 报告真实数据

Week 2: Phase 3 (知识管理)
        ├── Day 1-2: ObsidianService + API
        ├── Day 3-4: 前端浏览 + 搜索 + 图谱
        └── Day 5: 测试 + 联调

Week 3: Phase 4 (信息推送)
        ├── Day 1-2: 迁移 ai_news/stats 到后端
        ├── Day 3-4: 前端日报/周报/统计页
        └── Day 5: 定时任务联调

Week 4: Phase 5 (联动 + 打磨)
        ├── Day 1-2: AI 推荐 + 仪表盘聚合
        └── Day 3-5: 体验打磨 + 测试 + 部署
```

## 风险 & 应对

| 风险 | 应对 |
|---|---|
| Next.js 页面过多，编译变慢 | 按模块 lazy load，非活跃页面 dynamic import |
| Obsidian vault 文件量大，搜索慢 | 用 SQLite FTS5 建索引，定时增量更新 |
| LLM API 调用成本 | 日报/周报的 LLM 调用不变（已有），推荐系统用规则+缓存 |
| 前后端联调时间不够 | Phase 1-4 每阶段结束时做一次端到端验证 |
