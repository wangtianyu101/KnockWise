# CodeMock → 个人 AI 工作台 重构方案 V1.0

> 现状：CodeMock 是 AI 面试练习平台。
> 目标：扩展为三模块个人 AI 工作台 — 面试练习 + Obsidian 知识管理 + AI 信息推送。

---

## 一、产品定位

```
                    ┌─────────────────────────────────┐
                    │      个人 AI 工作台              │
                    │   Developer AI Workspace         │
                    └──────────────┬──────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
    ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
    │  🎯 面试练习 │        │  📚 知识管理 │        │  📡 信息推送 │
    │  Interview  │        │  Knowledge  │        │  News Feed  │
    │            │        │            │        │            │
    │ AI 追问引擎 │        │ Obsidian   │        │ AI 日报     │
    │ 能力雷达图  │        │ 知识图谱    │        │ 周报分析    │
    │ 面试历史    │        │ 智能检索    │        │ 代码统计    │
    │ 简历管理    │        │ 写作统计    │        │ 自定义源    │
    └─────────────┘        └─────────────┘        └─────────────┘
```

**一句话定位**：程序员的 AI 副脑 —— 帮你准备面试、管理知识、追踪信息。

---

## 二、三模块设计

### 模块 A：面试练习（已有基础，持续增强）

```
功能：
├── 实时语音面试（LiveKit + Whisper + Piper TTS）
├── LangGraph 追问引擎（核心差异化）
├── 50+ 种子题库（AI Agent / RAG / LangGraph / Java）
├── 能力雷达图（11 维度）
├── 面试历史 + 趋势分析
├── 简历上传 + LLM 技能提取
└── AI 推荐练习计划

数据流：
用户语音 → LiveKit → WhisperLive STT → LangGraph Agent
                                            ├── question_agent (选题)
                                            ├── followup_agent (追问)
                                            ├── evaluate_agent (评分)
                                            └── report_agent (报告)
                                         → Piper TTS → 语音输出
```

### 模块 B：Obsidian 知识管理（新增）

```
功能：
├── 📂 Vault Browser        → 浏览 Obsidian 文件树
├── 🔍 全文检索             → 搜索所有笔记内容
├── 🕸 知识图谱             → 基于 [[双链]] 的可视化图
├── 📊 写作统计             → 笔记数量、字数、更新频率
├── 🔗 反向链接面板         → 查看哪些笔记引用了当前笔记
├── ✍️ 快速笔记             → 从 Web 直接创建 Obsidian 笔记
├── 📅 每日笔记             → 查看/编辑 daily notes
└── 🤖 AI 关联推荐          → "你正在准备面试，这里有一些相关笔记"

技术方案：
- 后端直接读写 ~/Obsidian/coding/ 文件系统
- 解析 markdown frontmatter + [[wikilinks]]
- 构建内存索引（SQLite FTS5 全文搜索）
- 知识图谱用 D3.js/vis.js 渲染
- 复用现有 sync_obsidian.py 的同步逻辑
```

**Obsidian 集成 API：**

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/knowledge/tree` | 文件树结构 |
| `GET` | `/api/knowledge/search?q=` | 全文检索 |
| `GET` | `/api/knowledge/note?path=` | 读取单篇笔记 |
| `PUT` | `/api/knowledge/note?path=` | 创建/更新笔记 |
| `GET` | `/api/knowledge/graph` | 知识图谱数据（节点+边） |
| `GET` | `/api/knowledge/stats` | 写作统计 |
| `GET` | `/api/knowledge/backlinks?path=` | 反向链接 |
| `GET` | `/api/knowledge/daily?date=` | 每日笔记 |
| `POST` | `/api/knowledge/recommend` | AI 关联推荐 |

**知识图谱数据模型：**

```json
{
  "nodes": [
    {"id": "agent/Agent记忆系统设计.md", "label": "Agent 记忆系统设计", "size": 15, "group": "agent"},
    {"id": "database/Redis核心体系.md", "label": "Redis 核心体系", "size": 12, "group": "database"}
  ],
  "edges": [
    {"source": "agent/Agent记忆系统设计.md", "target": "database/Redis核心体系.md", "label": "缓存层"}
  ]
}
```

边来自 `[[wikilinks]]` 解析。

### 模块 C：AI 信息推送（已有脚本，接入 Web）

```
功能：
├── 📰 AI 日报         → 量子位 + 36氪 + HF Papers + arXiv
├── 📊 AI 周报         → LLM 深度分析 + 趋势总结
├── 📈 代码统计         → Claude Code token 消耗 + git 代码量
├── ⚙️ 信源管理         → 添加/删除/启停 RSS 源
├── ⏰ 推送时间设置     → 配置日报/周报生成时间
└── 📋 历史归档         → 浏览往期日报/周报

技术方案：
- 复用 ai_news.py 的 RSS 抓取 + LLM 摘要
- 复用 stats.py 的 JSONL 解析
- 前端做一个配置面板 + 历史浏览页面
- macOS launchd 定时任务不变（后端提供 API 查询历史数据）
```

**信息推送 API：**

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/news/daily?date=` | 获取某天日报 |
| `GET` | `/api/news/weekly?week=` | 获取某周周报 |
| `GET` | `/api/news/sources` | 信源列表 |
| `PUT` | `/api/news/sources` | 更新信源配置 |
| `POST` | `/api/news/trigger/daily` | 手动触发日报生成 |
| `POST` | `/api/news/trigger/weekly` | 手动触发周报 |
| `GET` | `/api/news/history` | 日报/周报历史列表 |
| `GET` | `/api/news/stats` | 代码统计摘要 |

---

## 三、统一仪表盘

```
┌──────────────────────────────────────────────────────────┐
│  👋 欢迎回来，王天宇                     Pro · 在线  [王] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 🎯       │  │ 📚       │  │ 📡       │              │
│  │ 面试练习  │  │ 知识管理  │  │ 信息推送  │              │
│  │          │  │          │  │          │              │
│  │ 3次面试  │  │ 38篇笔记  │  │ 4条待读  │              │
│  │ 得分3.8  │  │ 5个领域  │  │ 今日更新 │              │
│  │ [进入]   │  │ [进入]   │  │ [进入]   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                          │
│  ┌────────────────────┐ ┌────────────────────────────┐  │
│  │ 📊 本周概览         │ │ 📡 最新信息                 │  │
│  │                    │ │                            │  │
│  │ 面试: 1次 (3.8)    │ │ 06-12 AI日报 · 50条       │  │
│  │ 笔记: +3篇         │ │ 06-12 Claude统计 · 686K   │  │
│  │ Token: 686K        │ │ 小米1T大模型吞吐量破千     │  │
│  │ 代码: +6.8K行      │ │ 3D创作Agent发布...        │  │
│  └────────────────────┘ └────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 🧠 AI 今日推荐                                   │   │
│  │ • 面试薄弱项「记忆管理」— 你的笔记里有3篇相关文章   │   │
│  │ • arXiv 新论文「Contextual Memory for Agents」     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**关键设计**：三个模块不是孤立的，AI 推荐系统会跨模块关联。比如 "你要面试了，你的笔记里有一些相关内容可以复习" 或者 "今天 AI 日报提到的新技术，在你的知识库里有相关文章"。

---

## 四、路由表

| 路径 | 页面 | 模块 |
|---|---|---|
| `/login` | 登录 | 通用 |
| `/dashboard` | 统一仪表盘 | 通用 |
| `/interview/setup` | 面试配置 | A |
| `/interview/{id}` | 面试中 | A |
| `/interview/history` | 面试历史 | A |
| `/interview/report/{id}` | 面试报告 | A |
| `/interview/analytics` | 能力分析 | A |
| `/knowledge/browse` | 知识库浏览 | B |
| `/knowledge/note?path=` | 笔记阅读 | B |
| `/knowledge/graph` | 知识图谱 | B |
| `/knowledge/stats` | 写作统计 | B |
| `/news/daily` | AI 日报 | C |
| `/news/weekly` | AI 周报 | C |
| `/news/sources` | 信源管理 | C |
| `/news/stats` | 代码统计 | C |
| `/profile` | 个人信息 | 通用 |

---

## 五、技术架构

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                 │
│  3 modules: interview / knowledge / news            │
│  Shared: dashboard / profile / auth                 │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                 Backend (FastAPI)                    │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ interview│  │knowledge │  │  news    │          │
│  │ router   │  │ router   │  │ router   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│  ┌────▼─────┐  ┌─────▼──────┐  ┌───▼───────┐       │
│  │LangGraph │  │Obsidian    │  │RSS + LLM  │       │
│  │Agents    │  │FS Reader   │  │Summarizer │       │
│  └──────────┘  │+ FTS5      │  └───────────┘       │
│                └────────────┘                       │
│                                                     │
│  ┌──────────────────────────────────────────┐       │
│  │         Shared: MySQL + Auth + Profile    │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │              │              │
    ┌────▼───┐   ┌─────▼────┐  ┌─────▼─────┐
    │ MySQL  │   │ Obsidian │  │ macOS     │
    │ 8.4    │   │ Vault    │  │ launchd   │
    └────────┘   └──────────┘  └───────────┘
```

---

## 六、实施计划

| 阶段 | 内容 | 工作量 |
|---|---|---|
| **Phase 1** | 统一仪表盘（三模块入口 + 概览卡片） | 2-3 天 |
| **Phase 2** | 知识管理模块：文件浏览 + 笔记阅读 + 搜索 | 3-4 天 |
| **Phase 3** | 信息推送模块：日报/周报 Web 查看 + 配置面板 | 2-3 天 |
| **Phase 4** | 知识图谱可视化 + AI 跨模块推荐 | 3-4 天 |
| **Phase 5** | 邮箱密码登录 + 统一用户体系 | 2-3 天 |

**总计**：~3-4 周，可与现有面试模块并行开发。

---

## 七、与现有资产的复用

| 已有资产 | 复用方式 |
|---|---|
| `ai_news.py` (agent-memory/scripts) | → 后端 `/api/news/` 直接调其核心函数 |
| `stats.py` (agent-memory/scripts) | → 后端 `/api/news/stats` 读取 SQLite + 展示 |
| `sync_obsidian.py` (agent-memory/scripts) | → 后端 `/api/knowledge/` 复用文件遍历 + frontmatter 解析逻辑 |
| `Claude Code 统计.md` (Obsidian) | → 信息推送模块直接渲染已有 markdown |
| `AI 日报 *.md` (Obsidian) | → 信息推送模块的历史数据源 |
| Intervue ORM models | → 扩展 User/Profile 模型，新增模块无关 |
| Intervue 前端 dashboard | → 从 3 卡片扩展到 3 模块 |
| macOS launchd jobs | → 保持不变，后端提供数据查询接口 |

---

## 八、命名建议

当前项目名 `Intervue` 只涵盖面试。扩展后的名字建议：

| 名称 | 含义 | 评分 |
|---|---|---|
| **DevBrain** | 开发者的 AI 副脑 | ⭐⭐⭐⭐⭐ |
| CodeMind | 代码 + 思维 | ⭐⭐⭐⭐ |
| DevForge | 开发者锻造台 | ⭐⭐⭐ |
| AI Workbench | AI 工作台 | ⭐⭐⭐ |
