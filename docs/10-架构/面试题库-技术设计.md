# 面试题库 技术设计（4 大独立模块）

> 阶段 4.1 重构 · 状态：📋 技术设计
> 配套产品文档：[`./面试题库设计.md`](./面试题库设计.md)
> 配套页面规划：[`./面试题库-页面规划.md`](./面试题库-页面规划.md)
> 配套 HTML 设计图：[`./面试题库-页面设计.html`](./面试题库-页面设计.html)
>
> **核心变化**：4 大模块完全独立。API 路径按模块前缀分组（`/api/learn/*` `/api/review/*` `/api/qa/*` `/api/digest/*`）。
> 本文档**只放技术细节**（数据模型 / Service / 错误码 / 迁移 / 索引）。
> API 详情见 [`../20-参考/接口文档.md`](../20-参考/接口文档.md)。

---

## 一、技术架构总览（4 大独立模块）

```
┌─────────────────────────────────────────────────────────────────────────┐
│                面试题库子系统（4 大独立模块 · 技术）                     │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ ① 面试（不变） │  │ ② 学习复习      │  │ ③ 知识库   │  │ ④ AI 推送   │  │
│  │                │  │                │  │  (不变)    │  │ (独立化)   │  │
│  │ /api/interview │  │ /api/learn/*   │  │/api/know-  │  │ /api/digest │  │
│  │ (已有 8 个)    │  │ /api/review/*  │  │  ledge     │  │ /api/digest │  │
│  │                │  │ /api/qa/*      │  │ (已有 7 个)│  │ /sources    │  │
│  └────────────────┘  └────────────────┘  └────────────┘  └────────────┘  │
│                                                                         │
│  互相独立：                                                             │
│  · 服务层不调对方的 service                                              │
│  · API 不查对方的表                                                      │
│  · 数据层各自写自己的表                                                  │
│  · Profile 沉淀按模块分开（interview_stats / learn_stats / ...）          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.1 与现有架构的关系

- **API 路由**：新增 5 个 router（practice / learning / summary / profile/settlement / interview-改造），不破坏现有 9 个
- **Service**：6 个新 service，复用 `session_manager` / `obsidian_service` / `recommendations_service`
- **数据**：5 新表 + 1 改表，全部走现有 `Base.metadata.create_all` + `_MIGRATIONS` 启动 ALTER
- **LangGraph**：不重写，继续用 `question_engine`（只在 `practice_mode` 路径上短路）

---

## 二、数据模型

### 2.1 设计原则

- PK 用 `String(36)`（UUID-as-string），跟项目其他 model 一致
- 枚举用 `String(N)` 不用 MySQL ENUM
- JSON 列用 `sqlalchemy.JSON`（MySQL 8.4 原生支持）
- 时间戳统一 `DateTime(timezone=True)`
- 软删除用 `deleted_at`（本设计内 question_progress 不软删）

### 2.2 5 新表概览

| 表 | 字段数 | 索引数 | UNIQUE |
|---|---|---|---|
| `question_progress` | 18 | 4 | (user_id, question_id) |
| `learning_session` | 7 | 2 | — |
| `review_schedule` | 9 | 1 | (user_id, item_type, item_id) |
| `study_plan` | 10 | 2 | — |
| `monthly_report` | 8 | 1 | (user_id, year, month) |

### 2.3 question_progress 详细字段

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | String(36) | PK | UUID |
| user_id | String(36) | FK → users.id, NOT NULL, INDEX | 用户 |
| question_id | String(64) | NOT NULL, INDEX | 题目 ID |
| status | String(16) | NOT NULL, default 'new' | new/learning/mastered/skipped |
| practice_count | Integer | NOT NULL, default 0 | 练习次数 |
| correct_count | Integer | NOT NULL, default 0 | 答对次数 |
| bookmarked | Boolean | NOT NULL, default False | 收藏 |
| source | String(32) | NULL | seed/user_note/news/mock_interview |
| last_review_at | DateTime(timezone=True) | NULL | 最近复习时间 |
| next_review_at | DateTime(timezone=True) | NULL, INDEX | 下次应复习（SRS 核心） |
| review_count | Integer | NOT NULL, default 0 | 复习次数 |
| ease_factor | Float | NOT NULL, default 2.5 | SM-2 难度系数 |
| interval_days | Integer | NOT NULL, default 0 | 当前间隔天数 |
| first_practiced_at | DateTime(timezone=True) | NULL | 首次练习 |
| last_practiced_at | DateTime(timezone=True) | NULL | 最近练习 |
| user_answer | Text | NULL | 题库模式用户答案 |
| notes_path | String(256) | NULL | Obsidian 笔记路径 |
| created_at | DateTime(timezone=True) | NOT NULL, default utcnow | |
| updated_at | DateTime(timezone=True) | NOT NULL, default utcnow, onupdate utcnow | |

**索引**：
- `(user_id, status)` —— 列表筛选
- `(user_id, next_review_at, status)` —— 复习队列
- `(user_id, source)` —— 题源统计
- `(user_id, bookmarked, status)` —— 收藏列表

### 2.4 learning_session 字段

| 字段 | 类型 | 约束 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | FK, NOT NULL, INDEX |
| started_at | DateTime(timezone=True) | NOT NULL, default utcnow |
| ended_at | DateTime(timezone=True) | NULL |
| duration_sec | Integer | NOT NULL, default 0 |
| type | String(16) | NOT NULL, default 'practice' |
| items | JSON | default list |
| created_at | DateTime(timezone=True) | NOT NULL, default utcnow |

**索引**：`(user_id, started_at DESC)` / `(user_id, type, started_at DESC)`

### 2.5 review_schedule 字段

| 字段 | 类型 | 约束 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | FK, NOT NULL, INDEX |
| item_type | String(16) | NOT NULL (question/note/resource) |
| item_id | String(64) | NOT NULL |
| last_reviewed_at | DateTime(timezone=True) | NULL |
| next_review_at | DateTime(timezone=True) | NOT NULL, INDEX |
| interval_days | Integer | NOT NULL, default 1 |
| ease_factor | Float | NOT NULL, default 2.5 |
| repetition_count | Integer | NOT NULL, default 0 |
| created_at | DateTime(timezone=True) | NOT NULL, default utcnow |

**唯一约束**：`(user_id, item_type, item_id)`

### 2.6 study_plan 字段

| 字段 | 类型 | 约束 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | FK, NOT NULL, INDEX |
| name | String(128) | NOT NULL |
| description | Text | NULL |
| goal | String(256) | NULL |
| start_date | Date | NOT NULL |
| end_date | Date | NOT NULL |
| status | String(16) | NOT NULL, default 'active' |
| weekly_target | JSON | default list |
| progress | JSON | default dict |
| created_at / updated_at | DateTime(timezone=True) | NOT NULL |

**索引**：`(user_id, status)` / `(user_id, end_date)`

### 2.7 monthly_report 字段

| 字段 | 类型 | 约束 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | FK, NOT NULL, INDEX |
| year | Integer | NOT NULL |
| month | Integer | NOT NULL, CHECK (1-12) |
| content_md | Text | NOT NULL |
| summary_stats | JSON | NOT NULL |
| obsidian_synced_at | DateTime(timezone=True) | NULL |
| obsidian_path | String(256) | NULL |
| created_at | DateTime(timezone=True) | NOT NULL |

**唯一约束**：`(user_id, year, month)`

### 2.8 Profile 扩字段

| 字段 | 类型 | 默认 |
|---|---|---|
| `weak_topics` | JSON | list |
| `mastered_topics` | JSON | list |
| `learning_trajectory` | JSON | dict |
| `last_active_at` | DateTime(timezone=True) | NULL |

### 2.9 Interview 表扩字段

| 字段 | 类型 | 默认 |
|---|---|---|
| `is_practice` | Boolean | False |
| `practice_topic` | String(64) | NULL |
| `practice_count` | Integer | NULL |

---

## 三、迁移 SQL（MySQL 8.4）

### 3.1 新增 5 张表

```sql
-- question_progress
CREATE TABLE question_progress (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    question_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'new',
    practice_count INT NOT NULL DEFAULT 0,
    correct_count INT NOT NULL DEFAULT 0,
    bookmarked TINYINT(1) NOT NULL DEFAULT 0,
    source VARCHAR(32) NULL,
    last_review_at DATETIME(6) NULL,
    next_review_at DATETIME(6) NULL,
    review_count INT NOT NULL DEFAULT 0,
    ease_factor FLOAT NOT NULL DEFAULT 2.5,
    interval_days INT NOT NULL DEFAULT 0,
    first_practiced_at DATETIME(6) NULL,
    last_practiced_at DATETIME(6) NULL,
    user_answer TEXT NULL,
    notes_path VARCHAR(256) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_question (user_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- learning_session
CREATE TABLE learning_session (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    started_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    ended_at DATETIME(6) NULL,
    duration_sec INT NOT NULL DEFAULT 0,
    type VARCHAR(16) NOT NULL DEFAULT 'practice',
    items JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- review_schedule
CREATE TABLE review_schedule (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    item_type VARCHAR(16) NOT NULL,
    item_id VARCHAR(64) NOT NULL,
    last_reviewed_at DATETIME(6) NULL,
    next_review_at DATETIME(6) NOT NULL,
    interval_days INT NOT NULL DEFAULT 1,
    ease_factor FLOAT NOT NULL DEFAULT 2.5,
    repetition_count INT NOT NULL DEFAULT 0,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_item (user_id, item_type, item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- study_plan
CREATE TABLE study_plan (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(128) NOT NULL,
    description TEXT NULL,
    goal VARCHAR(256) NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    weekly_target JSON NOT NULL,
    progress JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- monthly_report
CREATE TABLE monthly_report (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    content_md TEXT NOT NULL,
    summary_stats JSON NOT NULL,
    obsidian_synced_at DATETIME(6) NULL,
    obsidian_path VARCHAR(256) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uniq_user_year_month (user_id, year, month),
    CHECK (month BETWEEN 1 AND 12)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.2 改动 profiles + interviews

```sql
-- profiles +4 字段 + 1 索引
ALTER TABLE profiles
    ADD COLUMN weak_topics JSON NOT NULL DEFAULT (JSON_ARRAY()),
    ADD COLUMN mastered_topics JSON NOT NULL DEFAULT (JSON_ARRAY()),
    ADD COLUMN learning_trajectory JSON NOT NULL DEFAULT (JSON_OBJECT()),
    ADD COLUMN last_active_at DATETIME(6) NULL;

CREATE INDEX idx_profiles_last_active ON profiles(last_active_at);

-- interviews +3 字段 + 1 索引
ALTER TABLE interviews
    ADD COLUMN is_practice TINYINT(1) NOT NULL DEFAULT 0,
    ADD COLUMN practice_topic VARCHAR(64) NULL,
    ADD COLUMN practice_count INT NULL;

CREATE INDEX idx_interview_is_practice ON interviews(user_id, is_practice, started_at DESC);
```

### 3.3 索引

```sql
-- question_progress
CREATE INDEX idx_qp_user_status ON question_progress(user_id, status);
CREATE INDEX idx_qp_user_next_review ON question_progress(user_id, next_review_at, status);
CREATE INDEX idx_qp_user_source ON question_progress(user_id, source);
CREATE INDEX idx_qp_user_bookmarked ON question_progress(user_id, bookmarked, status);

-- learning_session
CREATE INDEX idx_ls_user_started ON learning_session(user_id, started_at DESC);
CREATE INDEX idx_ls_user_type ON learning_session(user_id, type, started_at DESC);

-- review_schedule
CREATE INDEX idx_rs_user_next_review ON review_schedule(user_id, next_review_at);

-- study_plan
CREATE INDEX idx_sp_user_status ON study_plan(user_id, status);
CREATE INDEX idx_sp_user_end_date ON study_plan(user_id, end_date);

-- monthly_report
CREATE INDEX idx_mr_user_year_month ON monthly_report(user_id, year, month);
```

### 3.4 兼容旧数据

```sql
UPDATE interviews SET is_practice = 0 WHERE is_practice IS NULL;
UPDATE profiles SET weak_topics = JSON_ARRAY() WHERE weak_topics IS NULL;
UPDATE profiles SET mastered_topics = JSON_ARRAY() WHERE mastered_topics IS NULL;
UPDATE profiles SET learning_trajectory = JSON_OBJECT() WHERE learning_trajectory IS NULL;
```

### 3.5 实施机制

**短期（MVP）**：扩展现有 `core/database.py:_MIGRATIONS` 列表，添加上述 ALTER，启动时自动跑。

**长期（P3 阶段）**：迁移到 Alembic（见 [`../40-追踪/目前缺陷.md`](../40-追踪/目前缺陷.md) 债务 4）。

---

## 四、SRS 算法

### 4.1 SM-2 简化版

```python
# backend/services/srs.py
class SrsService:
    DEFAULT_EASE = 2.5
    MIN_EASE = 1.3

    def calculate_next(
        current_interval_days: int,
        current_ease_factor: float,
        review_count: int,
        is_correct: bool,
    ) -> dict:
        """
        纯函数。返回：
        {
            new_interval_days: int,
            new_ease_factor: float,
            next_review_at: datetime,
        }
        """
        if is_correct:
            if review_count == 0:
                new_interval = 1
            elif review_count == 1:
                new_interval = 3
            elif review_count == 2:
                new_interval = 7
            else:
                new_interval = round(current_interval_days * current_ease_factor)
            new_ease = max(self.MIN_EASE, current_ease_factor + 0.1)
        else:
            new_interval = 1
            new_ease = max(self.MIN_EASE, current_ease_factor - 0.2)
            review_count = max(0, review_count - 1)

        return {
            "new_interval_days": new_interval,
            "new_ease_factor": new_ease,
            "next_review_at": datetime.now(timezone.utc) + timedelta(days=new_interval),
        }
```

### 4.2 触发时机

- 每次 `POST /api/practice/questions/{qid}/answer`
- 每次 `POST /api/interviews/{id}/complete`（实战回写）
- 触发：调 `SrsService.apply_after_answer(user_id, qid, is_correct)`

### 4.3 自动 mastered 判定

```python
def auto_master_check(self, progress: dict) -> bool:
    """correct_count >= 2 → mastered。"""
    return progress["correct_count"] >= 2
```

---

## 五、Service 方法签名

### 5.1 PracticeService — 题库核心

```python
# backend/services/practice_service.py
class PracticeService:
    async def list_questions(
        user_id: UUID,
        *,
        topic: str | None = None,
        difficulty: int | None = None,
        status: str | None = None,
        source: str | None = None,
        bookmarked: bool | None = None,
        q: str | None = None,
        sort: str = "id",
        page: int = 1,
        size: int = 20,
        db: AsyncSession,
    ) -> dict: ...

    async def get_question(user_id: UUID, qid: str, db: AsyncSession) -> dict: ...

    async def submit_answer(
        user_id: UUID, qid: str,
        user_answer: str,
        time_spent_sec: int,
        session_id: UUID | None,
        db: AsyncSession,
    ) -> dict:
        """调 evaluate_agent → 更新 progress → 调 SrsService → 返回 score/feedback/srs。"""
        ...

    async def update_progress(
        user_id: UUID, qid: str,
        status: str | None = None,
        is_bookmarked: bool | None = None,
        db: AsyncSession,
    ) -> dict: ...

    async def get_my_progress(
        user_id: UUID,
        *,
        status: str | None = None,
        topic: str | None = None,
        db: AsyncSession,
    ) -> dict: ...

    async def recommend(user_id: UUID, n: int = 3, db: AsyncSession) -> list[dict]:
        """弱项 > 复习 > 未练 > 收藏 > 随机。"""
        ...

    async def review_queue(user_id: UUID, db: AsyncSession) -> list[dict]: ...
```

### 5.2 SrsService — 间隔重复

见 §4.1。

### 5.3 LearningService — 学习系统

```python
class LearningService:
    async def start_session(
        user_id: UUID, type: str, planned_items: list[str], db: AsyncSession
    ) -> dict: ...

    async def end_session(
        user_id: UUID, session_id: UUID,
        ended_at: datetime, items: list[dict], db: AsyncSession
    ) -> dict: ...

    async def recent_sessions(
        user_id: UUID, days: int = 7, db: AsyncSession
    ) -> dict: ...

    async def list_plans(self, user_id: UUID, db: AsyncSession) -> list[dict]: ...
    async def create_plan(self, user_id: UUID, plan_data: dict, db: AsyncSession) -> dict: ...
    async def update_plan(self, user_id: UUID, plan_id: UUID, updates: dict, db: AsyncSession) -> dict: ...
    async def get_plan_progress(self, user_id: UUID, plan_id: UUID, db: AsyncSession) -> dict: ...
```

### 5.4 SummaryService — 总结生成

```python
class SummaryService:
    async def daily(self, user_id: UUID, date: date, db: AsyncSession) -> dict: ...
    async def weekly(self, user_id: UUID, week: str, db: AsyncSession) -> dict: ...
    async def monthly(self, user_id: UUID, month: str, db: AsyncSession) -> dict: ...
    async def sync_daily_to_obsidian(self, user_id: UUID, date: date, db: AsyncSession) -> dict: ...
    async def dashboard(self, user_id: UUID, db: AsyncSession) -> dict: ...

    def _generate_narrative(self, stats: dict, template: str) -> str:
        """LLM 生成自然语言叙述（调 DeepSeek）。"""
        ...
```

### 5.5 ProfileSettlementService — 画像沉淀

```python
class ProfileSettlementService:
    async def settle_after_interview(
        self, user_id: UUID, interview_id: UUID, db: AsyncSession
    ) -> dict:
        """轻量：聚合本场盲点 → 更新 weak_topics + last_active_at。"""
        ...

    async def settle_after_practice(
        self, user_id: UUID, qid: str, score: int, db: AsyncSession
    ) -> dict: ...

    async def weekly_full_refresh(self, user_id: UUID, db: AsyncSession) -> dict:
        """深度：重算 learning_trajectory。"""
        ...

    async def manual_refresh(self, user_id: UUID, db: AsyncSession) -> dict: ...
```

### 5.6 ObsidianSedimentService — Obsidian 写回

```python
class ObsidianSedimentService:
    VAULT_ROOT = Path.home() / "Obsidian" / "coding"

    def _write(self, rel_path: str, content: str) -> str | None:
        """
        容错关键：vault 不存在 / 写失败 → log warning + 返回 None，不抛异常。
        """
        try:
            if not self.VAULT_ROOT.exists():
                log.warning(f"Obsidian vault not found: {self.VAULT_ROOT}")
                return None
            full = self.VAULT_ROOT / rel_path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
            return str(full)
        except Exception as e:
            log.warning(f"Obsidian write failed: {rel_path} → {e}")
            return None

    def write_daily(self, date: date, content: str) -> str | None: ...
    def write_weekly(self, week: str, content: str) -> str | None: ...
    def write_monthly(self, month: str, content: str) -> str | None: ...
    def write_mastered_dump(self, user_id: UUID, topics: list[dict]) -> str | None: ...
    def write_practice_log(self, session_id: UUID, content: str) -> str | None: ...
```

---

## 六、错误码

### 6.1 通用

| 码 | HTTP | 含义 |
|---|---|---|
| `UNAUTHORIZED` | 401 | 未登录 |
| `FORBIDDEN` | 403 | 不是资源所有者 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 422 | 请求字段校验失败 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `SERVICE_UNAVAILABLE` | 503 | 依赖服务（LLM / Obsidian）不可用 |

### 6.2 业务

| 码 | HTTP | 触发 | 处理 |
|---|---|---|---|
| `QUESTION_NOT_FOUND` | 404 | GET .../questions/{qid} | 重试或忽略 |
| `ANSWER_TOO_SHORT` | 400 | POST .../answer user_answer < 10 字符 | 前端校验 |
| `STATUS_INVALID` | 400 | PATCH .../progress status 不在枚举 | 前端限定 |
| `PLAN_DATE_INVALID` | 400 | POST .../plans end_date < start_date | 前端校验 |
| `SESSION_ALREADY_ENDED` | 409 | PATCH .../sessions 重复结束 | 静默忽略 |
| `OBSIDIAN_VAULT_NOT_FOUND` | 503 | vault 不存在 | 静默降级 |
| `OBSIDIAN_WRITE_FAILED` | 503 | 文件 IO 失败 | 同上 |
| `LLM_TIMEOUT` | 504 | LLM 调用超时 >30s | 重试 1 次 |
| `LLM_PARSE_FAILED` | 500 | LLM 返回非 JSON / 缺字段 | 降级：score=3 占位 |
| `SRS_INVALID_STATE` | 500 | question_progress 状态字段被破坏 | log + 返回当前状态 |

### 6.3 异常分支

| 接口 | 异常 | 策略 |
|---|---|---|
| GET /api/practice/questions | DB 慢 | `.limit(100)` 兜底 |
| POST .../answer | LLM 失败 | `LLM_PARSE_FAILED` 降级 |
| PATCH .../progress | 并发更新 | 乐观锁（version 字段，阶段 6 实施时加） |
| POST .../summary/.../sync | vault 不存在 | 静默降级 |
| POST /api/interviews/{id}/complete | DB 写失败 | interview 表优先 |
| GET /api/learning/plans | plan 被改 | 返回 stale，提示刷新 |

---

## 七、依赖与配置

### 7.1 Python 包（无需新增）

项目已有依赖足够：
- `sqlalchemy[asyncio]` 2.0+ — 5 新表 + Profile 4 字段
- `pydantic` 2.0+ — Request/Response schema
- `langchain_openai` — DeepSeek V3 评分 + 叙述生成

### 7.2 环境变量

无需新增环境变量。复用现有：
- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`（DeepSeek）
- `DATABASE_URL`（MySQL）

### 7.3 文件系统

- `~/Obsidian/coding/` — 已存在，路径在 `obsidian_service.py:VAULT_ROOT`
- 阶段 6 实施时改成从 `core/config.py:OBSIDIAN_VAULT_PATH` 读（见 [`../40-追踪/目前缺陷.md`](../40-追踪/目前缺陷.md) 债务 6）

---

## 八、与现有代码的集成点

| 文件 | 改动 |
|---|---|
| `backend/main.py` | 注册 5 个新 router |
| `backend/api/interview.py:241` `start_interview` | 加 `practice_mode` 参数分支 |
| `backend/api/interview.py:347` `next-question` | practice_mode 短路：直接走 `PracticeService.recommend` |
| `backend/api/interview.py:438` `complete` | 调 `PracticeService.record_interview_results` + `ProfileSettlementService.settle_after_interview` |
| `backend/core/database.py:_MIGRATIONS` | 加 5 新表 + 2 改表 + 10 索引的 ALTER |
| `backend/models/__init__.py` | 加 5 新 class + Profile 4 字段 + Interview 3 字段 |

---

## 九、相关文档

- [`./面试题库设计.md`](./面试题库设计.md) — 产品文档（功能架构 / 用户旅程 / 业务规则）
- [`../20-参考/接口文档.md`](../20-参考/接口文档.md) — REST API 详情
- [`../40-追踪/目前缺陷.md`](../40-追踪/目前缺陷.md) — 议题 D（本设计的实现）
- [`./项目说明.md`](./项目说明.md) / [`./技术文档.md`](./技术文档.md) — 项目架构
