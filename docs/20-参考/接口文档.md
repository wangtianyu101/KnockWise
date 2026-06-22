# DevBrain — 接口文档

> Base URL: `http://localhost:8000` | Auth: `Bearer <JWT>` | Content-Type: `application/json`

---

## 1. 认证 `/api/auth`

### `POST /api/auth/register`
注册新用户（邮箱 + 密码）。

```json
// Request
{ "email": "user@example.com", "password": "123456", "display_name": "用户名" }
// Response 200
{ "access_token": "eyJ...", "token_type": "bearer", "user": { "id": "uuid", "email": "...", "display_name": "用户名", "avatar_url": null } }
// Errors: 400 (invalid email/short password), 409 (email exists)
```

### `POST /api/auth/login`
邮箱 + 密码登录。

```json
// Request
{ "email": "user@example.com", "password": "123456" }
// Response 200 — same as register
// Errors: 401 (invalid credentials)
```

### `GET /api/auth/github/url`
获取 GitHub OAuth 授权 URL。

```json
// Response 200
{ "url": "https://github.com/login/oauth/authorize?..." }
```

### `GET /api/auth/github/callback?code=`
GitHub OAuth 回调，用 code 换 JWT。

```json
// Response 200 — same token format as register
```

### `GET /api/auth/dev-login?username=`
开发环境绕过认证。

```json
// Response 200 — token + user (no password required)
```

---

## 2. 仪表盘 `/api/dashboard`

### `GET /api/dashboard`
跨模块聚合数据。

```json
// Response 200
{
  "interview": { "total": 0, "completed": 0, "in_progress": 0, "latest_score": null, "score_trend": "flat" },
  "knowledge": { "total_notes": 49, "total_words": 47234 },
  "stats": { "total_tokens": 1658635, "total_code": 8999, "total_days": 6 },
  "recommendations": [
    { "type": "interview", "title": "...", "detail": "...", "priority": "high" }
  ]
}
```

---

## 3. 个人信息 `/api/profile`

### `GET /api/profile/me`
获取当前用户画像。

```json
// Response 200
{ "id": "uuid", "user_id": "uuid", "tech_stack": ["Python"], "years_of_exp": 3, "current_level": "mid", "target_companies": [], "resume_summary": null, "skill_map": {} }
```

### `PUT /api/profile/me`
更新用户画像。

```json
// Request (all fields optional)
{ "tech_stack": ["Python","Java"], "years_of_exp": 3, "current_level": "mid", "target_companies": ["字节跳动"], "resume_text": "简历文本..." }
// Response 200 — updated profile
```

### `POST /api/profile/resume`
上传简历 PDF（multipart form）。

```json
// Response — placeholder (use PUT /me with resume_text)
```

---

## 4. 面试 `/api/interviews`

### `GET /api/interviews?status=&page=1&size=20`
面试列表（分页 + 筛选）。

```json
// Response 200
{ "items": [{ "id": "uuid", "round": "round1", "status": "completed", "overall_score": 3.8, "started_at": "..." }], "total": 3, "page": 1, "size": 20 }
```

### `POST /api/interviews`
创建新面试。

```json
// Request
{ "round": "round1", "style": "standard" }
// Response 200 — Interview object
```

### `GET /api/interviews/{id}`
获取单个面试。

### `GET /api/interviews/{id}/records`
获取面试的所有答题记录。

```json
// Response 200
[{ "id": "uuid", "question_text": "...", "user_answer": "...", "score": 4, "blind_spots": [] }]
```

### `POST /api/interviews/{id}/next-question`
获取下一题（Agent 选题引擎）。

```json
// Response 200
{ "record_id": "uuid", "question_id": "agent_001", "question_text": "...", "topic": "agent_architecture", "followup_tree": {...}, "asked_count": 3 }
```

### `POST /api/interviews/records/{id}/answer`
提交答案（Agent 评估 + 追问判断）。

```json
// Request
{ "user_answer": "ReAct 模式是...", "time_spent": 45 }
// Response 200
{ "status": "ok", "score": 4, "feedback": "...", "blind_spots": [], "action": "next_question", "has_followup": false }
```

### `POST /api/interviews/transcribe`
语音转文字（上传 webm/wav）。

```json
// Request — multipart audio file
// Response 200
{ "text": "转录的文字..." }
```

### `POST /api/interviews/livekit-token`
生成 LiveKit 语音房间 token。

```json
// Request
{ "room_name": "interview-xxx", "participant_name": "user" }
// Response 200
{ "token": "eyJ..." }
```

---

## 5. 报告 `/api/reports`

### `GET /api/reports/interview/{id}`
获取面试报告。

### `POST /api/reports/interview/{id}`
生成面试报告（需面试状态为 completed）。

```json
// Response 200
{ "id": "uuid", "radar_data": { "agent_architecture": 3, ... }, "top_blind_spots": [], "improvement_plan": [] }
```

---

## 6. 能力分析 `/api/analytics`

### `GET /api/analytics/overview`
综合统计。

```json
// Response 200
{ "total_interviews": 3, "overall_score": 3.6, "score_trend": "up", "latest_score": 3.8, "weak_topics": [{ "topic": "memory", "count": 3 }] }
```

### `GET /api/analytics/radar`
11 维度雷达图数据。

```json
// Response 200
{ "radar": [{ "topic": "agent_architecture", "label": "Agent架构", "score": 4.2, "count": 3 }] }
```

### `GET /api/analytics/trends`
各 topic 首末对比趋势。

```json
// Response 200
{ "trends": [{ "date": "...", "score": 3.5 }], "topic_deltas": [{ "topic": "memory", "label": "记忆管理", "delta": 0.4 }] }
```

### `GET /api/analytics/recommendations`
AI 练习推荐。

```json
// Response 200
{ "recommendations": [{ "topic": "memory", "label": "Memory", "frequency": 3, "priority": "high" }] }
```

---

## 7. 知识管理 `/api/knowledge`

### `GET /api/knowledge/browse?subdir=`
文件浏览。subdir 为空时浏览根目录。

```json
// Response 200
[{ "name": "agent", "type": "directory", "path": "agent", "children_count": 18 }, { "name": "README.md", "type": "file", "path": "README.md", "size": 1024 }]
```

### `GET /api/knowledge/search?q=&limit=20`
全文检索。

```json
// Response 200
[{ "path": "agent/xxx.md", "name": "xxx.md", "snippet": "...匹配上下文...", "score": 5 }]
```

### `GET /api/knowledge/note?path=`
读取笔记。

```json
// Response 200
{ "path": "agent/xxx.md", "name": "xxx.md", "content": "# Title\n\n...", "frontmatter": { "tags": ["ai"] }, "links": ["OtherNote"], "size": 1024 }
// Error: 404
```

### `PUT /api/knowledge/note?path=&content=`
创建/更新笔记。

```json
// Response 200
{ "path": "...", "status": "saved" }
```

### `GET /api/knowledge/graph`
知识图谱。

```json
// Response 200
{ "nodes": [{ "id": 0, "path": "agent/xxx.md", "label": "Title", "group": "agent", "size": 12 }], "edges": [{ "source": 0, "target": 1, "label": "wikilink" }], "stats": { "total_nodes": 48, "total_edges": 35 } }
```

### `GET /api/knowledge/stats`
写作统计。

```json
// Response 200
{ "total_notes": 49, "total_words": 47234, "total_chars": 439086, "by_folder": { "agent": { "notes": 18, "words": 23119 } } }
```

### `GET /api/knowledge/backlinks?path=`
反向链接。

```json
// Response 200
[{ "path": "other.md", "name": "other.md", "link_text": "TargetNote" }]
```

### `GET /api/knowledge/daily?date=`
每日笔记（自动创建）。

---

## 8. 信息推送 `/api/news`

### `GET /api/news/daily`
日报列表。

```json
// Response 200
[{ "name": "AI 日报 2026-06-13.md", "date": "2026-06-13", "size": 4731 }]
```

### `GET /api/news/daily/latest?date=`
获取指定日期日报（不传 date 取最新）。

```json
// Response 200
{ "name": "AI 日报 2026-06-13.md", "date": "2026-06-13", "content": "# AI 日报\n\n...", "size": 4731 }
```

### `GET /api/news/weekly`
周报列表。

### `GET /api/news/weekly/latest?week=`
获取指定周报。

### `GET /api/news/stats?days=7`
代码统计。

```json
// Response 200
{ "daily": [{ "date": "2026-06-13", "tokens_in": 100000, "tokens_out": 20000, "code_added": 500, "commits": 2 }], "summary": { "total_days": 6, "total_tokens": 1658635 } }
```

### `GET /api/news/sources`
信源列表。

```json
// Response 200
[{ "name": "量子位", "url": "https://www.qbitai.com/feed", "category": "大模型", "enabled": true }]
```

---

## 通用

### `GET /api/health`
健康检查。

```json
{ "status": "ok", "service": "codemock" }
```

### 认证方式

所有 `/api/*` 路由（除 auth 和 health）需要：

```text
Authorization: Bearer <JWT>
```

JWT 通过 `POST /api/auth/login` 或 `POST /api/auth/register` 获取，7 天过期。

### 错误格式

```json
{ "detail": "Error message" }
```

---

## 12. 面试题库（新增模块，2026-06-18 设计）

> 配套产品文档：[`../10-架构/面试题库设计.md`](../10-架构/面试题库设计.md)
> 配套技术文档：[`../10-架构/面试题库-技术设计.md`](../10-架构/面试题库-技术设计.md)
> 配套页面规划：[`../10-架构/面试题库-页面规划.md`](../10-架构/面试题库-页面规划.md)
> 配套 HTML 设计图：[`../designs/面试题库-页面设计.html`](../designs/面试题库-页面设计.html)
>
> ⚠️ **阶段 4.1 重构（2026-06-18）**：4 大独立模块拆分。
> - `/api/practice/*` → `/api/learn/*`（重命名，待实施时同步改）
> - `/api/learning/*` → `/api/review/*`（重命名）
> - 新增 `/api/qa/*`（AI 问答）
> - `/api/summary/*` → `/api/digest/*`（重命名）
> - 现有 §12.1-§12.5 内容**待重写**，下文先保留旧版作为参考

### 12.1 学习复习 - 学 `/api/learn`（旧名 `/api/practice`，待重命名）

#### `GET /api/practice/questions`

#### `GET /api/practice/questions`

题目列表（筛选/分页/排序）。

**Query 参数**：`topic` / `difficulty` (1-5) / `status` (new/learning/mastered/skipped) / `source` / `bookmarked` / `q` (关键词) / `sort` (id/difficulty/last_practiced/random) / `page` (默认 1) / `size` (默认 20, 最大 100)

**Response 200**：
```json
{
  "items": [
    {
      "id": "q_agent_001",
      "topic": "agent_architecture",
      "sub_topic": "ReAct",
      "difficulty": 3,
      "question_text": "ReAct 模式的核心循环是什么？",
      "source": "seed",
      "progress": {
        "status": "learning",
        "practice_count": 2,
        "correct_count": 1,
        "next_review_at": "2026-06-20T10:00:00+08:00",
        "is_bookmarked": false
      }
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20
}
```

#### `GET /api/practice/questions/{qid}`

题目详情。

**Response 200**：
```json
{
  "id": "q_agent_001",
  "topic": "agent_architecture",
  "sub_topic": "ReAct",
  "difficulty": 3,
  "question_text": "ReAct 模式的核心循环是什么？",
  "answer_key_points": ["Thought → Action → Observation 循环"],
  "followup_tree": {},
  "source": "seed",
  "tags": ["Agent", "Reasoning"],
  "progress": {
    "status": "learning",
    "last_practiced_at": "2026-06-15T14:30:00+08:00"
  },
  "related_notes": [
    {"path": "agent/ReAct模式.md", "title": "ReAct 模式"}
  ]
}
```

**错误码**：404 (`QUESTION_NOT_FOUND`)

#### `POST /api/practice/questions/{qid}/answer`

提交答案 → 自动评分 + 更新 progress + SRS。

**Request**：
```json
{
  "user_answer": "ReAct 是 Reasoning + Acting 循环...",
  "time_spent_sec": 45,
  "session_id": "uuid-or-null"
}
```

**Response 200**：
```json
{
  "score": 4,
  "feedback": "基本正确",
  "blind_spots": [],
  "progress": {
    "status": "mastered",
    "practice_count": 3,
    "correct_count": 3,
    "review_count": 1,
    "next_review_at": "2026-06-19T10:00:00+08:00"
  },
  "srs": {
    "previous_interval_days": 1,
    "new_interval_days": 3,
    "ease_factor": 2.6
  }
}
```

**错误码**：400 (`ANSWER_TOO_SHORT`) / 404 / 500 (`LLM_PARSE_FAILED`)

#### `PATCH /api/practice/progress/{qid}`

手动改掌握度。

**Request**：
```json
{ "status": "mastered", "is_bookmarked": true }
```

**Response 200**：
```json
{
  "qid": "q_agent_001",
  "status": "mastered",
  "is_bookmarked": true,
  "updated_at": "2026-06-18T12:00:00+08:00"
}
```

**错误码**：400 (`STATUS_INVALID`) / 404

#### `GET /api/practice/progress`

我的所有 progress。

**Query**：`status` / `topic`

**Response 200**：
```json
{
  "items": [
    {
      "qid": "q_agent_001",
      "topic": "agent_architecture",
      "difficulty": 3,
      "status": "mastered",
      "practice_count": 3,
      "correct_count": 3,
      "next_review_at": "2026-06-19T10:00:00+08:00",
      "is_bookmarked": true,
      "source": "seed"
    }
  ],
  "summary": {
    "total": 12,
    "by_status": {"new": 5, "learning": 4, "mastered": 3, "skipped": 0}
  }
}
```

#### `GET /api/practice/recommend`

今日推荐（基于盲点 + 复习队列 + 未练习题）。

**Query**：`n` (int, 默认 3)

**Response 200**：
```json
{
  "items": [
    {
      "qid": "q_mcp_001",
      "topic": "mcp",
      "difficulty": 4,
      "reason": "weak_spot",
      "reason_detail": "你在 blind_spots 中 3 次提到 'MCP'"
    },
    {
      "qid": "q_rag_004",
      "topic": "rag",
      "difficulty": 3,
      "reason": "due_review",
      "reason_detail": "上次答对在 6-15，3 天后该复习"
    }
  ]
}
```

#### `GET /api/practice/review-queue`

今日到期复习题。

**Response 200**：
```json
{
  "items": [
    {
      "qid": "q_rag_004",
      "topic": "rag",
      "next_review_at": "2026-06-18T10:00:00+08:00",
      "review_count": 1,
      "interval_days": 1
    }
  ],
  "count": 1
}
```

### 12.2 学习复习 - 复习 `/api/review`（旧学习系统）

#### `POST /api/learning/sessions`

开始学习会话。

**Request**：
```json
{
  "type": "practice",
  "planned_items": ["q_agent_001", "q_rag_004"]
}
```

**Response 201**：
```json
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "type": "practice",
  "started_at": "2026-06-18T14:00:00+08:00",
  "duration_sec": 0
}
```

#### `PATCH /api/learning/sessions/{id}`

结束会话。

**Request**：
```json
{
  "ended_at": "2026-06-18T14:32:00+08:00",
  "items": [
    {"kind": "question", "qid": "q_agent_001", "score": 4},
    {"kind": "question", "qid": "q_rag_004", "score": 2}
  ]
}
```

**Response 200**：
```json
{
  "id": "session-uuid",
  "duration_sec": 1920,
  "items_count": 2
}
```

**错误码**：404 / 409 (`SESSION_ALREADY_ENDED`)

#### `GET /api/learning/sessions/recent`

最近会话。

**Query**：`days` (int, 默认 7)

**Response 200**：
```json
{
  "items": [
    {
      "id": "session-uuid",
      "type": "practice",
      "started_at": "2026-06-18T14:00:00+08:00",
      "duration_sec": 1920,
      "items_count": 2
    }
  ],
  "summary": {
    "total_sessions": 8,
    "total_minutes": 145,
    "by_type": {"practice": 5, "review": 2, "mock_interview": 1}
  }
}
```

#### `GET /api/learning/plans`

我的学习计划列表。

**Response 200**：
```json
{
  "items": [
    {
      "id": "plan-uuid",
      "name": "MCP 4 周冲刺",
      "goal": "4 周后 MCP 拿 4+ 分",
      "start_date": "2026-06-01",
      "end_date": "2026-06-28",
      "status": "active",
      "progress": {
        "completed_questions": 8,
        "total_questions": 20,
        "percent": 40
      }
    }
  ]
}
```

#### `POST /api/learning/plans`

新建学习计划。

**Request**：
```json
{
  "name": "MCP 4 周冲刺",
  "description": "针对 MCP 协议薄弱点",
  "goal": "4 周后 MCP 拿 4+ 分",
  "start_date": "2026-06-18",
  "end_date": "2026-07-15",
  "weekly_target": [
    {"week": 1, "questions": ["q_mcp_001", "q_mcp_002"], "notes": []}
  ]
}
```

**Response 201**：返回创建的 plan（结构同 GET 列表项）

**错误码**：400 (`PLAN_DATE_INVALID`)

#### `PATCH /api/learning/plans/{id}`

调整计划。

**Request**：`status` / `name` / `weekly_target` 任意字段可选。

**Response 200**：返回更新后的 plan

#### `GET /api/learning/plans/{id}/progress`

计划进度详情。

**Response 200**：
```json
{
  "plan_id": "plan-uuid",
  "by_week": [
    {
      "week": 1,
      "target_questions": ["q_mcp_001", "q_mcp_002"],
      "completed_questions": ["q_mcp_001"],
      "percent": 50
    }
  ],
  "overall": {
    "completed": 8,
    "total": 20,
    "percent": 40,
    "days_remaining": 14
  }
}
```

### 12.3 学习复习 - 问答 `/api/qa`（新）+ 12.4 AI 推送 `/api/digest`（旧应用层）

#### `GET /api/summary/daily?date=`

**Response 200**：
```json
{
  "date": "2026-06-18",
  "stats": {
    "questions_attempted": 3,
    "questions_mastered": 1,
    "interview_count": 0,
    "study_minutes": 45,
    "new_blind_spots": ["MCP 协议"],
    "resolved_blind_spots": ["Reranker 选型"]
  },
  "narrative": "今天你做了 3 道题，掌握了 1 道 MCP 协议...",
  "obsidian_synced": true,
  "obsidian_path": "daily/2026-06-18.md"
}
```

#### `GET /api/summary/weekly?week=`

**Response 200**：
```json
{
  "week": "2026-W25",
  "date_range": {"start": "2026-06-16", "end": "2026-06-22"},
  "stats": {
    "questions_attempted": 18,
    "questions_mastered": 5,
    "interview_count": 1,
    "interview_score": 3.4,
    "study_minutes": 320,
    "top_blind_spots": ["MCP 协议", "RAG 评估指标"]
  },
  "vs_last_week": {
    "questions_attempted": "+30%",
    "interview_score": "+0.4"
  },
  "narrative": "本周你练习 18 题...",
  "obsidian_synced": false
}
```

#### `GET /api/summary/monthly?month=`

**Response 200**：
```json
{
  "month": "2026-06",
  "stats": {
    "questions_attempted": 80,
    "questions_mastered": 22,
    "interview_count": 3,
    "avg_interview_score": 3.4,
    "study_minutes": 1200,
    "by_topic": {"agent_architecture": 25, "rag": 30, "langgraph": 15, "java": 10}
  },
  "learning_trajectory": {
    "interview_count": 3,
    "avg_score": 3.4,
    "first_score": 2.5,
    "latest_score": 3.0,
    "improvement": 0.5,
    "trend": "up"
  },
  "narrative": "...",
  "obsidian_synced": false
}
```

#### `POST /api/summary/daily/{date}/sync-to-obsidian`

**Response 200**：
```json
{
  "obsidian_path": "daily/2026-06-18.md",
  "synced_at": "2026-06-18T15:00:00+08:00",
  "size_bytes": 1024
}
```

**错误码**：404 / 503 (`OBSIDIAN_VAULT_NOT_FOUND` / `OBSIDIAN_WRITE_FAILED`)

#### `GET /api/summary/dashboard`

升级版 dashboard（整合三模块 + 题库 + 学习）。

**Response 200**：
```json
{
  "interview": {"total": 5, "completed": 3, "in_progress": 0, "latest_score": 3.0, "score_trend": "up"},
  "practice": {
    "questions_attempted": 80,
    "by_status": {"new": 30, "learning": 25, "mastered": 22, "skipped": 3},
    "by_topic": {"agent_architecture": 25, "rag": 30, "langgraph": 15, "java": 10},
    "due_today": 5
  },
  "knowledge": {"total_notes": 64, "total_words": 52823},
  "stats": {"total_tokens": 33421092, "total_code": 9138, "total_days": 11},
  "recommendations": [...],
  "growth": {
    "this_week": {"questions": 18, "minutes": 320, "mastered": 5},
    "streak_days": 7
  }
}
```

### 12.4 Profile 沉淀 `/api/profile/settlement`

#### `GET /api/profile/settlement`

**Response 200**：
```json
{
  "user_id": "user-uuid",
  "tech_stack": [...],
  "years_of_exp": 3,
  "current_level": "mid",
  "weak_topics": [
    {"topic": "MCP", "count": 3, "first_seen": "2026-06-10", "last_seen": "2026-06-17"}
  ],
  "mastered_topics": [
    {"topic": "agent_architecture", "mastered_at": "2026-06-15"}
  ],
  "learning_trajectory": {
    "interview_count": 5,
    "avg_score": 3.4,
    "first_score": 2.5,
    "latest_score": 3.0,
    "improvement": 0.5,
    "trend": "up"
  },
  "last_active_at": "2026-06-18T14:30:00+08:00"
}
```

#### `POST /api/profile/settlement/refresh`

**Response 200**：
```json
{
  "updated_at": "2026-06-18T15:00:00+08:00",
  "diff": {
    "weak_topics_added": ["MCP"],
    "weak_topics_resolved": [],
    "mastered_topics_added": ["agent_architecture"],
    "trajectory_updated": true
  }
}
```

### 12.5 面试模块改造 `/api/interviews`

#### `POST /api/interviews` (改造)

新增 `practice_mode` 参数（题库刷题模式，不开语音、不存为正式面试记录）。

**Request**（原有 + 新字段）：
```json
{
  "round": "round1",
  "style": "standard",
  "practice_mode": true,
  "practice_topic": "mcp",
  "practice_count": 5
}
```

**Response 201**（原有 + 新字段）：
```json
{
  "id": "interview-uuid",
  "round": "round1",
  "style": "standard",
  "status": "in_progress",
  "practice_mode": true,
  "is_practice": true,
  "started_at": "2026-06-18T14:00:00+08:00"
}
```

**降级策略**：`practice_mode=true` 但没传 `practice_topic` 时，从 `recommend()` 返回的题里抽

#### `POST /api/interviews/{id}/next-question` (改造)

**改动**：当 `interview.is_practice=true` 时，从题库抽题（不调 LLM 选题引擎），返回的题直接是 question_id

**Response 200**（practice_mode）：
```json
{
  "record_id": "record-uuid",
  "question_id": "q_mcp_001",
  "question_text": "MCP 协议的架构是什么？",
  "topic": "mcp",
  "difficulty": 4,
  "asked_count": 1,
  "is_practice": true
}
```

#### `POST /api/interviews/{id}/complete` (改造)

**改动**（不破坏现有 API）：
- 新增：调 `PracticeService.record_interview_results()` 把本次面试的题目回写到 `question_progress`（更新 practice_count / correct_count / SRS 状态）
- 新增：调 `ProfileSettlementService.settle_after_interview()` 触发轻量沉淀

