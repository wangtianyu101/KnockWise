# AI 推送 技术设计

> 阶段 4.2 · 状态：📋 技术设计
> 配套：[`./AI推送设计.md`](./AI推送设计.md) · [`./AI推送-页面规划.md`](./AI推送-页面规划.md)

---

## 一、技术架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                   AI 推送子系统（技术）                              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Cron (每分钟)                                             │    │
│  │  → 检查当前时间 = 用户推送时间?                             │    │
│  │  → 是 → 抓 RSS → LLM 选题 → LLM 摘要 → 写 DB → 发推送   │    │
│  └────────────────────────┬───────────────────────────────┘    │
│                           │                                      │
│  ┌────────────────────────▼───────────────────────────────┐      │
│  │  RSS 抓取（feedparser）                                    │      │
│  │  • 4 个源（量子位 / 36氪 / HF Papers / arXiv）            │      │
│  │  • 每源每天 1 次                                          │      │
│  └────────────────────────┬───────────────────────────────┘      │
│                           │ 50+ 条原始                            │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  LLM 选题（DeepSeek V3）                                   │    │
│  │  Input: 用户偏好（关注/屏蔽标签） + 50 条原始 + 互动历史    │    │
│  │  Output: 10 条精选（按用户兴趣权重排序）                    │    │
│  └────────────────────────┬───────────────────────────────┘      │
│                           │ 10 条                                │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  LLM 摘要（DeepSeek V3）                                   │    │
│  │  Input: 10 条原始                                          │    │
│  │  Output: 每条 3-5 行摘要（核心事实 + 数字 + 影响）         │    │
│  └────────────────────────┬───────────────────────────────┘      │
│                           │ 10 条带摘要                         │
│                           ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  推送渠道                                                  │    │
│  │  • 写 DB (digest_daily / weekly / monthly 表)             │    │
│  │  • 发邮件（SMTP / Resend / SendGrid）                     │    │
│  │  • macOS notification（用户开启时，本地 cron 拉 DB）       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  数据存储：MySQL 8.4                                                │
│  LLM：DeepSeek V3（via api.minimax.chat）                          │
│  Obsidian：~/Obsidian/coding/ai/                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、数据模型

### 2.1 新增 7 张表

| 表 | 字段数 | 用途 |
|---|---|---|
| `digest_source` | 8 | RSS 信源配置（启停） |
| `digest_daily` | 12 | 每日日报存档 |
| `digest_daily_item` | 10 | 日报中的一条 |
| `digest_weekly` | 12 | 每周周报存档 |
| `digest_monthly` | 12 | 每月月报存档 |
| `digest_read` | 6 | 阅读记录（已读 / 阅读时长） |
| `digest_bookmark` | 6 | 收藏 |
| `digest_hide` | 6 | 屏蔽记录（"🔇 不再推类似"） |

### 2.2 digest_source 字段

```python
class DigestSource(Base):
    __tablename__ = "digest_source"
    id = Column(String(36), primary_key=True)
    name = Column(String(128), NOT NULL)             # 量子位 / 36氪 / HF / arXiv
    url = Column(String(512), NOT NULL)              # RSS URL
    category = Column(String(32))                     # 大模型 / 应用 / 论文
    enabled = Column(Boolean, default=True, NOT NULL)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_item_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
```

### 2.3 digest_daily 字段

```python
class DigestDaily(Base):
    __tablename__ = "digest_daily"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), NOT NULL, INDEX)
    date = Column(Date, NOT NULL)
    title = Column(String(256))                       # "AI 日报 2026-06-22"
    intro = Column(Text)                              # LLM 生成的简短引言
    item_ids = Column(JSON, default=list)             # 10 条 item_id（按顺序）
    pushed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    UNIQUE(user_id, date)
```

### 2.4 digest_daily_item 字段

```python
class DigestDailyItem(Base):
    __tablename__ = "digest_daily_item"
    id = Column(String(36), primary_key=True)
    daily_id = Column(String(36), ForeignKey("digest_daily.id"), NOT NULL, INDEX)
    rank = Column(Integer)                            # 1-10
    category = Column(String(32))                     # 头条 / 商业 / 论文 / 工程 / 观点
    title = Column(String(512), NOT NULL)
    summary = Column(Text)                            # 3-5 行 LLM 摘要
    quality_score = Column(Float)                     # LLM 评估 1-5
    source_name = Column(String(128))                 # 量子位 / 36氪 / HF / arXiv
    source_url = Column(String(1024))                 # 原文链接
    estimated_minutes = Column(Integer)                # 1-5
    created_at = Column(DateTime(timezone=True), default=_utcnow)
```

### 2.5 digest_weekly / monthly 字段

```python
class DigestWeekly(Base):
    __tablename__ = "digest_weekly"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), NOT NULL, INDEX)
    year = Column(Integer, NOT NULL)
    week = Column(Integer, NOT NULL)                  # ISO 周数
    title = Column(String(256))                       # "AI 周报 2026-W25"
    top5_events = Column(JSON, default=list)          # 5 大事件（按影响力）
    trends = Column(JSON, default=list)               # 3 个趋势（LLM 分析）
    outlook = Column(Text)                            # 下周展望
    item_ids = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    UNIQUE(user_id, year, week)
```

### 2.6 digest_read / bookmark / hide 字段

```python
class DigestRead(Base):
    __tablename__ = "digest_read"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), NOT NULL, INDEX)
    item_id = Column(String(36), ForeignKey("digest_daily_item.id"), NOT NULL)
    read_at = Column(DateTime(timezone=True), default=_utcnow)
    duration_sec = Column(Integer, default=0)         # 用户在页面停留时长
    UNIQUE(user_id, item_id)


class DigestBookmark(Base):
    __tablename__ = "digest_bookmark"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), NOT NULL, INDEX)
    item_id = Column(String(36), ForeignKey("digest_daily_item.id"), NOT NULL)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    UNIQUE(user_id, item_id)


class DigestHide(Base):
    __tablename__ = "digest_hide"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), NOT NULL, INDEX)
    item_id = Column(String(36), ForeignKey("digest_daily_item.id"), NOT NULL)
    reason = Column(String(32))                        # not_interested / low_quality / already_seen
    topic_keywords = Column(JSON, default=list)         # LLM 提取的关键词
    expires_at = Column(DateTime(timezone=True))        # 7 天后自动失效
    created_at = Column(DateTime(timezone=True), default=_utcnow)
```

### 2.7 Profile 字段扩展

```python
# profiles 表新增
digest_stats = Column(JSON, default=dict)
# 内容：{
#   "total_reads": 123,
#   "total_bookmarks": 18,
#   "total_minutes": 580,
#   "last_pushed_at": "2026-06-22T08:00:00+08:00"
# }
```

### 2.8 索引

```sql
-- digest_daily
CREATE INDEX idx_dd_user_date ON digest_daily(user_id, date DESC);

-- digest_daily_item
CREATE INDEX idx_ddi_daily_rank ON digest_daily_item(daily_id, rank);

-- digest_weekly / monthly
CREATE INDEX idx_dw_user_year_week ON digest_weekly(user_id, year, week);
CREATE INDEX idx_dm_user_year_month ON digest_monthly(user_id, year, month);

-- digest_bookmark
CREATE INDEX idx_db_user_created ON digest_bookmark(user_id, created_at DESC);

-- digest_hide（按 topic 关键词 + 时间查询）
CREATE INDEX idx_dh_user_expires ON digest_hide(user_id, expires_at);
```

---

## 三、迁移 SQL

```sql
-- 7 张新表
CREATE TABLE digest_source (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    url VARCHAR(512) NOT NULL,
    category VARCHAR(32),
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    last_fetched_at DATETIME(6) NULL,
    last_item_count INT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_daily (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    title VARCHAR(256),
    intro TEXT,
    item_ids JSON NOT NULL,
    pushed_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_date (user_id, date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_daily_item (
    id VARCHAR(36) PRIMARY KEY,
    daily_id VARCHAR(36) NOT NULL,
    `rank` INT NOT NULL,
    category VARCHAR(32),
    title VARCHAR(512) NOT NULL,
    summary TEXT,
    quality_score FLOAT,
    source_name VARCHAR(128),
    source_url VARCHAR(1024),
    estimated_minutes INT,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (daily_id) REFERENCES digest_daily(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_weekly (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    year INT NOT NULL,
    week INT NOT NULL,
    title VARCHAR(256),
    top5_events JSON NOT NULL,
    trends JSON NOT NULL,
    outlook TEXT,
    item_ids JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_year_week (user_id, year, week)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_monthly (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    title VARCHAR(256),
    top3_events JSON NOT NULL,
    trends JSON NOT NULL,
    paper_summaries JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_year_month (user_id, year, month),
    CHECK (month BETWEEN 1 AND 12)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_read (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    item_id VARCHAR(36) NOT NULL,
    read_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    duration_sec INT NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES digest_daily_item(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_item (user_id, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_bookmark (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    item_id VARCHAR(36) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES digest_daily_item(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_bookmark (user_id, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE digest_hide (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    item_id VARCHAR(36) NOT NULL,
    reason VARCHAR(32),
    topic_keywords JSON NOT NULL,
    expires_at DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES digest_daily_item(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 索引
CREATE INDEX idx_dd_user_date ON digest_daily(user_id, date DESC);
CREATE INDEX idx_ddi_daily_rank ON digest_daily_item(daily_id, `rank`);
CREATE INDEX idx_dw_user_year_week ON digest_weekly(user_id, year, week);
CREATE INDEX idx_dm_user_year_month ON digest_monthly(user_id, year, month);
CREATE INDEX idx_db_user_created ON digest_bookmark(user_id, created_at DESC);
CREATE INDEX idx_dh_user_expires ON digest_hide(user_id, expires_at);

-- profiles 扩字段
ALTER TABLE profiles
    ADD COLUMN digest_stats JSON NOT NULL DEFAULT (JSON_OBJECT());

-- 默认信源
INSERT INTO digest_source (id, name, url, category, enabled) VALUES
    (UUID(), '量子位', 'https://www.qbitai.com/feed', '大模型', 1),
    (UUID(), '36氪', 'https://36kr.com/feed', '应用', 1),
    (UUID(), 'HuggingFace Papers', 'https://huggingface.co/api/daily_papers', '论文', 1),
    (UUID(), 'arXiv cs.AI', 'https://rss.arxiv.org/rss/cs.AI', '论文', 1);
```

---

## 四、关键 Service

### 4.1 DigestService — 推送核心

```python
# backend/services/digest_service.py
class DigestService:
    async def fetch_all_sources(self) -> list[dict]:
        """抓所有启用的 RSS 源。返回 50+ 条原始。"""
        ...

    async def select_top10(
        self, user_id: UUID, raw_items: list[dict], user_prefs: dict
    ) -> list[dict]:
        """LLM 选题：基于用户偏好 + 互动历史，从 50+ 条选 10 条。"""
        # LLM prompt: 包含用户关注标签 + 屏蔽标签 + 已屏蔽的 topic + 50 条原始
        # 输出: 10 条（按用户兴趣权重排序）
        ...

    async def generate_summary(
        self, items: list[dict]
    ) -> list[dict]:
        """LLM 摘要：每条 3-5 行。"""
        prompt = """为每条新闻生成 3-5 行摘要：
        - 第 1 句：核心事实
        - 第 2-3 句：关键数字 / 数据
        - 第 4-5 句：对谁有影响
        不要客套话，不要 emoji。"""
        ...

    async def push_daily(
        self, user_id: UUID, date: date
    ) -> bool:
        """主入口：抓 → 选题 → 摘要 → 写 DB → 发邮件 → macOS notification。"""
        raw = await self.fetch_all_sources()
        prefs = await self.get_user_prefs(user_id)
        top10 = await self.select_top10(user_id, raw, prefs)
        items = await self.generate_summary(top10)
        daily = await self.save_to_db(user_id, date, items)
        await self.send_email(user_id, daily)
        await self.send_macos_notification(user_id, daily)
        await self.update_profile_stats(user_id)
        return True
```

### 4.2 DigestScheduler — 定时任务

```python
# backend/services/digest_scheduler.py
class DigestScheduler:
    async def check_and_push(self):
        """每分钟跑一次（cron / asyncio sleep）。"""
        for user in self.get_users_with_push_enabled():
            now_in_user_tz = self.now_in_tz(user.timezone)
            if now_in_user_tz.hour == user.push_hour and not self.pushed_today(user.id):
                await DigestService().push_daily(user.id, date.today())
                self.mark_pushed_today(user.id)
```

### 4.3 DigestPreferenceService — 偏好管理

```python
class DigestPreferenceService:
    async def get_user_prefs(self, user_id: UUID) -> dict:
        """从 profiles.digest_stats + 用户关注/屏蔽标签 → 返回选题权重。"""
        return {
            "interested_tags": ["Agent", "RAG", "国产模型"],
            "blocked_tags": ["元宇宙", "区块链"],
            "blocked_topics": [...],  # 来自 digest_hide 表，7 天内的 topic
            "preferred_sources": ["量子位", "HuggingFace Papers"],
            "history_bookmarks": [...],  # 用户收藏过的 keywords
        }
```

---

## 五、LLM Prompt 设计

### 5.1 选题 prompt

```
你是 AI 推送编辑。从 50+ 条原始资讯中选 10 条给用户。

用户偏好：
- 关注标签：{interested_tags}
- 屏蔽标签：{blocked_tags}
- 屏蔽 topic（7 天内）：{blocked_topics}
- 历史收藏关键词：{history_bookmarks}

要求：
1. 严格排除屏蔽标签 / topic
2. 优先匹配关注标签
3. 平衡分类（🔥 头条 3 / 🏢 商业 2 / 📚 论文 2 / 🛠 工程 2 / 💡 观点 1）
4. 不要重复（用户已读过的标题不选）

输出 JSON：
{
  "selected": [
    {"rank": 1, "title": "...", "source": "...", "category": "头条", "reason": "匹配 Agent 标签"}
  ]
}
```

### 5.2 摘要 prompt

```
为每条新闻生成 3-5 行摘要：

输入：{title}, {original_content}
输出要求：
- 第 1 句：核心事实（who/what/when）
- 第 2-3 句：关键数字 / 数据（带 %、$、数字）
- 第 4-5 句：对谁有影响（开发者 / 投资人 / PM / 学术）
- 不要客套话（"据悉"、"有消息称"）
- 不要 emoji
- 不要标题重复

输出 JSON：
{
  "summaries": [
    {"title": "...", "summary": "...", "quality_score": 4.5, "category": "头条", "estimated_minutes": 3}
  ]
}
```

---

## 六、API 详细

### 6.1 主要 endpoint

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/digest/today` | 今日日报详情 |
| GET | `/api/digest/daily/[date]` | 某天日报 |
| GET | `/api/digest/weekly/[week]` | 某周周报 |
| GET | `/api/digest/monthly/[month]` | 某月月报 |
| GET | `/api/digest/dailies?limit=7` | 最近 7 天列表 |
| GET | `/api/digest/bookmarks` | 我的收藏 |
| POST | `/api/digest/bookmarks` | 收藏 |
| DELETE | `/api/digest/bookmarks/[id]` | 取消收藏 |
| POST | `/api/digest/read` | 标记已读（含阅读时长） |
| POST | `/api/digest/hide` | "🔇 不再推类似" |
| POST | `/api/digest/sync-to-obsidian` | 写回 Obsidian |
| GET | `/api/digest/sources` | 信源列表 |
| POST | `/api/digest/sources` | 添加信源 |
| PATCH | `/api/digest/sources/[id]` | 启停信源 |
| GET | `/api/digest/settings` | 推送设置 |
| PATCH | `/api/digest/settings` | 保存设置 |

### 6.2 POST /api/digest/read 样例

```json
// Request
{
  "item_id": "uuid",
  "duration_sec": 180
}
// Response 200
{
  "item_id": "uuid",
  "read_at": "2026-06-22T14:30:00+08:00",
  "duration_sec": 180,
  "progress": "5/10"  // 当天已读数
}
```

### 6.3 POST /api/digest/hide 样例

```json
// Request
{
  "item_id": "uuid",
  "reason": "not_interested"  // not_interested / low_quality / already_seen
}
// Response 200
{
  "hide_id": "uuid",
  "topic_keywords": ["元宇宙", "Web3"],
  "expires_at": "2026-06-29T14:30:00+08:00",  // 7 天后
  "message": "7 天内同类型 -50% 权重"
}
```

### 6.4 PATCH /api/digest/settings 样例

```json
// Request
{
  "push_hour": 7,
  "push_minute": 30,
  "channels": {
    "in_app": true,
    "email": true,
    "macos": false
  },
  "frequency": {
    "daily": true,
    "weekly": true,
    "monthly": true,
    "weekend_pause": false
  },
  "interested_tags": ["Agent", "RAG", "国产模型"],
  "blocked_tags": ["元宇宙", "区块链"],
  "daily_count": 10
}
// Response 200
{
  "updated_at": "2026-06-22T14:30:00+08:00",
  "next_push": "2026-06-23T07:30:00+08:00"
}
```

---

## 七、推送渠道实现

### 7.1 站内（默认）

写 DB → 用户访问 /push 页面时显示。

### 7.2 邮件

```python
# backend/services/email_service.py
class EmailService:
    async def send_daily_digest(self, user: User, daily: DigestDaily):
        """发邮件。用 Resend / SendGrid（推荐 Resend 免费 100 封/天）。"""
        html = self.render_email_template(daily)
        await self.resend_client.send(
            to=user.email,
            subject=f"AI 日报 {daily.date} · {len(daily.item_ids)} 条精选",
            html=html,
        )
```

### 7.3 macOS notification

通过本地客户端（macOS 菜单栏 app）轮询 `/api/digest/today`，有新内容时弹通知。本期**暂不做**（P1 阶段）。

---

## 八、关键错误码

| 码 | HTTP | 触发 | 处理 |
|---|---|---|---|
| `RSS_FETCH_FAILED` | 502 | 某个 RSS 源抓取失败 | 静默用缓存，标 "X 源失败" |
| `LLM_SELECTION_FAILED` | 502 | LLM 选题失败 | 退回到按时间前 10 条 |
| `LLM_SUMMARY_FAILED` | 502 | LLM 摘要失败 | 显示原文标题 + 链接 |
| `EMAIL_SEND_FAILED` | 502 | 邮件发送失败 | 重试 3 次（5/15/60 分钟） |
| `NO_NEW_CONTENT` | 200 | 当天 0 条新内容 | 返回空，邮件写"今日无新内容" |
| `SOURCE_DISABLED` | 200 | 用户禁用某信源 | 静默跳过 |

---

## 九、依赖

### 9.1 新增 Python 包

```txt
feedparser>=6.0          # RSS 解析
resend>=2.0            # 邮件发送（推荐，免费 100 封/天）
```

### 9.2 不需要

- macOS notification 库（暂不做）
- 向量数据库（LLM 选题够用，不上 embedding）

---

## 十、相关文档

- [`./AI推送设计.md`](./AI推送设计.md) — 产品文档
- [`./AI推送-页面规划.md`](./AI推送-页面规划.md) — 页面规划
- [`../designs/AI推送-页面设计.html`](../designs/AI推送-页面设计.html) — 可打开设计图
- [`../20-参考/接口文档.md`](../20-参考/接口文档.md) — REST API 详情
- [`../00-入门/应用说明.md`](../00-入门/应用说明.md) — 启动 + 运行
