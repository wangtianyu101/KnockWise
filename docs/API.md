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

```
Authorization: Bearer <JWT>
```

JWT 通过 `POST /api/auth/login` 或 `POST /api/auth/register` 获取，7 天过期。

### 错误格式

```json
{ "detail": "Error message" }
```
