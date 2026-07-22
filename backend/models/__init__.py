"""SQLAlchemy ORM models for KnockWise.

All primary keys are String(36) to match the existing UUID-as-string pattern
used throughout the API layer (str(uuid4()), str(interview.id), etc.).

JSON columns use SQLAlchemy's JSON type, which maps to MySQL 8.4 JSON.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Computed,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from core.database import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    github_id = Column(String(64), unique=True, nullable=True)       # nullable for email-password users
    github_username = Column(String(128), nullable=True)              # nullable for email-password users
    avatar_url = Column(String(512), nullable=True)
    email = Column(String(256), nullable=True, unique=True)           # unique — used as login credential
    password_hash = Column(String(256), nullable=True)                # PBKDF2-SHA256 (600k iters), nullable for GitHub OAuth users
    display_name = Column(String(128), nullable=True)                 # user-chosen display name
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    profiles = relationship("Profile", back_populates="user")
    interviews = relationship("Interview", back_populates="user", foreign_keys="Interview.user_id")
    reports = relationship("Report", back_populates="user", foreign_keys="Report.user_id")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    tech_stack = Column(JSON, default=list)
    years_of_exp = Column(Integer, default=0)
    current_level = Column(String(32), default="mid")
    target_companies = Column(JSON, default=list)
    resume_summary = Column(Text, nullable=True)
    skill_map = Column(JSON, default=dict)
    # Phase 1a · 学习复习模块扩字段 (面试题库-技术设计.md 2.8)
    weak_topics = Column(JSON, default=list)
    mastered_topics = Column(JSON, default=list)
    learning_trajectory = Column(JSON, default=dict)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="profiles")
    interviews = relationship("Interview", back_populates="profile")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    profile_id = Column(String(36), ForeignKey("profiles.id"), nullable=False)
    round = Column(String(32), default="round1")
    style = Column(String(32), default="standard")
    status = Column(String(32), default="in_progress")
    started_at = Column(DateTime(timezone=True), default=_utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_questions = Column(Integer, default=0)
    overall_score = Column(Float, nullable=True)
    # P0-2: Session persistence — serialized InterviewState snapshot
    state_snapshot = Column(JSON, nullable=True)
    # User actions: bookmark + soft delete. Nullable defaults so existing
    # dev.db rows stay valid; new rows get the proper defaults.
    is_favorite = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # 注: 面试题库-技术设计.md 2.9 列出 is_practice/practice_topic/practice_count,
    # stage 5 决策 D3 (b) 不动 interviews 表 → 不加这些字段

    # Relationships
    user = relationship("User", back_populates="interviews", foreign_keys=[user_id])
    profile = relationship("Profile", back_populates="interviews")
    question_records = relationship("QuestionRecord", back_populates="interview")
    reports = relationship("Report", back_populates="interview")


class QuestionRecord(Base):
    __tablename__ = "question_records"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    question_id = Column(String(64), nullable=True)  # nullable: seed data uses semantic IDs
    question_text = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=True)
    followup_chain = Column(JSON, default=list)
    score = Column(Integer, nullable=True)
    blind_spots = Column(JSON, default=list)
    time_spent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    interview = relationship("Interview", back_populates="question_records")


class Question(Base):
    """Seed question bank. IDs are semantic (not UUIDs), e.g. 'agent_001'."""

    __tablename__ = "questions"

    id = Column(String(64), primary_key=True)
    topic = Column(String(64), nullable=False)
    sub_topic = Column(String(64), nullable=False)
    difficulty = Column(Integer, default=3)
    round = Column(String(32), default="round1")
    question_text = Column(Text, nullable=False)
    answer_key_points = Column(JSON, default=list)
    followup_tree = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    radar_data = Column(JSON, default=dict)
    top_blind_spots = Column(JSON, default=list)
    improvement_plan = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    interview = relationship("Interview", back_populates="reports")
    user = relationship("User", back_populates="reports", foreign_keys=[user_id])


# ╔════════════════════════════════════════════════════════════════════╗
# ║  Phase 1a · 学习复习模块（5 新表）                                  ║
# ║  配套设计: docs/10-架构/面试题库-技术设计.md 2.3-2.7                ║
# ╚════════════════════════════════════════════════════════════════════╝


class QuestionProgress(Base):
    """题库题目的用户掌握度 (SRS / SM-2)。每对 (user_id, question_id) 一行。

    注: user_id 没有 FK (MySQL 8 分区表不允许 FK)。应用层保证 referential integrity
    (所有写入都从已认证 user_id 出发, 删除 user 用 soft delete 或 CASCADE 在 user 表层做)。
    """

    __tablename__ = "question_progress"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    question_id = Column(String(64), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="new")  # new/learning/mastered/skipped
    practice_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    bookmarked = Column(Boolean, nullable=False, default=False)
    source = Column(String(32), nullable=True)  # seed/user_note/news/mock_interview
    last_review_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), nullable=True, index=True)
    review_count = Column(Integer, nullable=False, default=0)
    ease_factor = Column(Float, nullable=False, default=2.5)
    interval_days = Column(Integer, nullable=False, default=0)
    first_practiced_at = Column(DateTime(timezone=True), nullable=True)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    user_answer = Column(Text, nullable=True)
    notes_path = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uniq_user_question"),
        Index("idx_qp_user_status", "user_id", "status"),
        Index("idx_qp_user_next_review", "user_id", "next_review_at", "status"),
        Index("idx_qp_user_source", "user_id", "source"),
        Index("idx_qp_user_bookmarked", "user_id", "bookmarked", "status"),
    )


class LearningSession(Base):
    """题库练习 session。每次 /learn 进入算一次。"""

    __tablename__ = "learning_sessions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_sec = Column(Integer, nullable=False, default=0)
    type = Column(String(16), nullable=False, default="practice")  # practice/review/qa
    items = Column(JSON, default=list)  # [{question_id, status, duration_sec, score}]
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_ls_user_started", "user_id", "started_at"),
        Index("idx_ls_user_type", "user_id", "type", "started_at"),
    )


class ReviewSchedule(Base):
    """SRS 复习调度。复用 question_progress 的 SRS，但允许指向其他类型 (note/resource)。"""

    __tablename__ = "review_schedules"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(16), nullable=False)  # question/note/resource
    item_id = Column(String(64), nullable=False)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), nullable=False, index=True)
    interval_days = Column(Integer, nullable=False, default=1)
    ease_factor = Column(Float, nullable=False, default=2.5)
    repetition_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "item_type", "item_id", name="uniq_user_item"),
        Index("idx_rs_user_next_review", "user_id", "next_review_at"),
    )


class StudyPlan(Base):
    """学习计划。每条计划含 N 周的 weekly_target + 进度。"""

    __tablename__ = "study_plans"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(String(256), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(16), nullable=False, default="active")  # active/completed/archived
    weekly_target = Column(JSON, default=list)  # [{week_idx, target_count, target_topics}]
    progress = Column(JSON, default=dict)  # {done_count, mastered_count, weak_topics_remaining}
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("idx_sp_user_status", "user_id", "status"),
        Index("idx_sp_user_end_date", "user_id", "end_date"),
    )


class MonthlyReport(Base):
    """学习月报。每对 (user_id, year, month) 一行，content_md 是 LLM 生成的报告。"""

    __tablename__ = "monthly_reports"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    content_md = Column(Text, nullable=False)
    summary_stats = Column(JSON, nullable=False)
    obsidian_synced_at = Column(DateTime(timezone=True), nullable=True)
    obsidian_path = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uniq_user_year_month"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_mr_month_range"),
        Index("idx_mr_user_year_month", "user_id", "year", "month"),
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  Phase 1a · 候选 A-E (5 张) + 归档表 (1 张)                         ║
# ║  配套: docs/10-架构/面试题库-技术设计.md 阶段 4.1 + 用户反馈         ║
# ╚════════════════════════════════════════════════════════════════════╝


class QuestionTag(Base):
    """灵活标签。is_system=True = 系统预设（如 "高频"/"字节考过"），user_id=NULL；
    user_id 非空 = 用户自定义标签。

    唯一性约束 (MySQL 不支持 partial unique):
    - 系统标签 (user_id IS NULL): name 全局唯一
    - 用户标签 (user_id IS NOT NULL): (user_id, name) 唯一
    用 generated column trick: NULL user_id 映射为特殊字符串 '__system__'，
    然后 UNIQUE (user_id_key, name) 一条搞定。

    注: user_id 无 FK (MySQL 9 + GENERATED column + FK 三者不兼容)。
    Cascade delete 由应用层处理 (见 docs/40-追踪/目前缺陷.md 债务 8)。
    """

    __tablename__ = "question_tags"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    name = Column(String(64), nullable=False)
    color = Column(String(16), nullable=True)  # e.g. '#ff5577' / 'indigo'
    is_system = Column(Boolean, nullable=False, default=False)
    user_id = Column(String(36), nullable=True, index=True)
    # Generated column: NULL → '__system__', other → user_id 本身
    # 这样所有行都参与 UNIQUE, NULL 不再走 SQL "NULL != NULL" 漏洞
    user_id_key = Column(
        String(64),
        Computed("COALESCE(user_id, '__system__')", persisted=True),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id_key", "name", name="uniq_qt_userid_key_name"),
    )


class QuestionTagMap(Base):
    """Tag ↔ Question 多对多映射。"""

    __tablename__ = "question_tag_maps"

    question_id = Column(String(64), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(String(36), ForeignKey("question_tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_qtm_tag_question", "tag_id", "question_id"),
    )


class UserQuestionNote(Base):
    """用户对某题的笔记（题库内联 markdown，不依赖 Obsidian）。"""

    __tablename__ = "user_question_notes"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(64), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    content_md = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uniq_uqn_user_question"),
    )


class BookmarkCollection(Base):
    """收藏夹分组。QuestionProgress.collection_id FK 过来。"""

    __tablename__ = "bookmark_collections"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    color = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uniq_bc_user_name"),
    )


class QuestionAnswerLog(Base):
    """答题明细（每题每次的分数/盲点/停留时间）。用于分数曲线分析。"""

    __tablename__ = "question_answer_logs"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(64), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=True)  # 1-5
    blind_spots = Column(JSON, default=list, nullable=False)
    duration_sec = Column(Integer, nullable=False, default=0)
    source = Column(String(32), nullable=True)  # practice / review / mock_interview
    answered_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_qal_user_question_time", "user_id", "question_id", "answered_at"),
    )


class UserQuestion(Base):
    """用户自建题。题源 user_note 走这里。"""

    __tablename__ = "user_questions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)  # 用户写的参考回答
    topic = Column(String(64), nullable=True)
    sub_topic = Column(String(64), nullable=True)
    difficulty = Column(Integer, default=3)
    tags = Column(JSON, default=list, nullable=False)  # 用户标签 (字符串数组)
    source = Column(String(32), nullable=False, default="user_note")  # user_note/news/...
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("idx_uq_user_topic", "user_id", "topic"),
    )


class QuestionProgressArchive(Base):
    """question_progress 冷数据归档表。

    与 QuestionProgress 同 schema (无外键约束, 避免被原表 FK 反向引用)。
    archive_service.py 月度 cron 把 mastered > 1Y 的行迁到这里。
    """

    __tablename__ = "question_progress_archive"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    question_id = Column(String(64), nullable=False, index=True)
    status = Column(String(16), nullable=False)
    practice_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    bookmarked = Column(Boolean, nullable=False, default=False)
    source = Column(String(32), nullable=True)
    last_review_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), nullable=True)
    review_count = Column(Integer, nullable=False, default=0)
    ease_factor = Column(Float, nullable=False, default=2.5)
    interval_days = Column(Integer, nullable=False, default=0)
    first_practiced_at = Column(DateTime(timezone=True), nullable=True)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    user_answer = Column(Text, nullable=True)
    notes_path = Column(String(256), nullable=True)
    archived_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)  # 归档时间
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_qpa_user_status", "user_id", "status"),
    )


class QASession(Base):
    """题库问答 session。每个 session 针对一道题, 含多轮 user/assistant 消息。

    设计决策: 消息存 JSON (不分子表), 因为:
    - 单 session 消息数 < 100 (1v1 模拟面试场景)
    - JSON 让 history 1 次 round-trip 拉完
    """

    __tablename__ = "qa_sessions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(64), nullable=False, index=True)
    messages = Column(JSON, default=list, nullable=False)
    # [{role: user/assistant, content, ts: iso}, ...]
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_qas_user_question", "user_id", "question_id"),
        Index("idx_qas_user_created", "user_id", "created_at"),
    )


# ════════════════════════════════════════════════════════════
# V3.1 · 精选题单 Collections（PR 2 · 系统题单）
# ════════════════════════════════════════════════════════════


class QuestionCollection(Base):
    """精选题单（系统题单 / 官方精选）。"""

    __tablename__ = "question_collections"

    id = Column(String(64), primary_key=True)  # 'algorithms_50' / 'system_design_30'
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    cover_color = Column(String(16), default="#6366f1", nullable=False)
    icon_emoji = Column(String(16), default="📘", nullable=False)
    is_system = Column(Boolean, default=True, nullable=False)  # V3 仅系统题单
    question_count = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_qc_system_order", "is_system", "sort_order"),
    )


class QuestionCollectionMap(Base):
    """题单 ↔ 题目 多对多关联。"""

    __tablename__ = "question_collection_maps"

    collection_id = Column(String(64), primary_key=True)
    question_id = Column(String(64), primary_key=True)
    position = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_qcm_collection_pos", "collection_id", "position"),
        Index("idx_qcm_question", "question_id"),
    )


class CollectionSubscribe(Base):
    """用户题单订阅 + 进度。"""

    __tablename__ = "collection_subscribes"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(64), ForeignKey("question_collections.id", ondelete="CASCADE"), nullable=False)
    progress_json = Column(JSON, default=dict, nullable=False)  # {done_count, total_count, completion_rate, last_question_id}
    subscribed_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_active_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "collection_id", name="uniq_cs_user_collection"),
        Index("idx_cs_user_active", "user_id", "last_active_at"),
        Index("idx_cs_collection", "collection_id"),
    )


# ═══════════════════════════════════════════════════════════════════
# AI 推送模块 (T1: 2026-07-17 实施)
# 配套 docs/tasks/2026-07-17-new-feature-ai-push/
# ── db-design.md §2.1-2.9
# ─────────────────────────────────────────────────────────────────


class DigestSource(Base):
    """AI 推送信源配置（系统默认 8 + 用户自定义 N）。

    user_id = NULL 表示系统默认源（spec R5 独立性）。
    category 区分来源类别，type/region 为内容双轴标签。
    """

    __tablename__ = "digest_sources"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)  # NULL = 系统默认
    name = Column(String(128), nullable=False)
    url = Column(String(512), nullable=False)
    category = Column(String(32), nullable=False, comment="来源类别")
    type = Column(String(16), nullable=False, index=True, comment="model|application")
    region = Column(String(16), nullable=False, index=True, comment="domestic|overseas")
    enabled = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False, index=True, comment="TRUE=系统默认 8 源")
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_item_count = Column(Integer, default=0, nullable=False)
    last_error = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uniq_ds_user_url"),
        Index("idx_ds_user_enabled", "user_id", "enabled"),
        Index("idx_ds_default_enabled", "is_default", "enabled"),
        Index("idx_ds_region_type", "region", "type"),
    )


class DigestDaily(Base):
    """每日日报存档（每用户 + 每天 1 条）。"""

    __tablename__ = "digest_daily"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, comment="用户本地时区的日期")
    vibe = Column(String(256), nullable=True, comment="今日 1-5 条数量标注等")
    item_ids = Column(JSON, nullable=False, default=list, comment="5 个 item_id（按 rank 顺序）")
    pushed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uniq_dd_user_date"),
        Index("idx_dd_user_date", "user_id", "date"),
    )


class DigestDailyItem(Base):
    """日报条目（每条 digest 卡片）。

    type/region 为内容双轴标签（spec R5 决策）。
    related_item_ids 指向历史同类 digest（spec R9 引用溯源）。
    """

    __tablename__ = "digest_daily_item"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    daily_id = Column(String(36), ForeignKey("digest_daily.id", ondelete="CASCADE"), nullable=False, index=True)
    rank = Column(Integer, nullable=False, comment="1-5")
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=False, comment="0.0-1.0 综合打分")
    type = Column(String(16), nullable=False, index=True, comment="model|application")
    region = Column(String(16), nullable=False, index=True, comment="domestic|overseas")
    category = Column(String(32), nullable=False, comment="headline|paper|engineering|opinion")
    source_id = Column(String(36), ForeignKey("digest_sources.id", ondelete="SET NULL"), nullable=True)
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(1024), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    related_item_ids = Column(JSON, nullable=False, default=list, comment="≤5 个相关历史 item_id")
    estimated_minutes = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("daily_id", "rank", name="uniq_ddi_daily_rank"),
        Index("idx_ddi_source", "source_id"),
        Index("idx_ddi_type_region", "type", "region"),
        Index("idx_ddi_published", "published_at"),
    )


class DigestRead(Base):
    """阅读记录（spec R10 · duration 喂 LLM prompt）。"""

    __tablename__ = "digest_read"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("digest_daily_item.id", ondelete="CASCADE"), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    duration_sec = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uniq_dr_user_item"),
        Index("idx_dr_user_read_at", "user_id", "read_at"),
    )


class DigestBookmark(Base):
    """收藏（spec R10 行为反馈）。"""

    __tablename__ = "digest_bookmark"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("digest_daily_item.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uniq_db_user_item"),
        Index("idx_db_user_created", "user_id", "created_at"),
    )


class DigestHide(Base):
    """屏蔽记录 · 7 天后 -50% 权重（spec R5 hide scenario）。

    topic_keywords 必走白名单过滤防 prompt 注入。
    """

    __tablename__ = "digest_hide"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("digest_daily_item.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(32), nullable=False, comment="not_interested|low_quality|already_seen")
    topic_keywords = Column(JSON, nullable=False, default=list, comment="LLM 提取的关键词数组(≤5)")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="created_at+7days")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    __table_args__ = (
        Index("idx_dh_user_item", "user_id", "item_id"),
        Index("idx_dh_user_expires", "user_id", "expires_at"),
    )


class DigestSettings(Base):
    """用户推送设置（spec R5 + R6 · 1-to-1 with users）。"""

    __tablename__ = "digest_settings"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    push_hour = Column(Integer, default=8, nullable=False, comment="0-23 用户本地时区")
    push_minute = Column(Integer, default=0, nullable=False, comment="0-59")
    push_timezone = Column(String(64), default="Asia/Shanghai", nullable=False, comment="IANA 时区名")
    email_enabled = Column(Boolean, default=True, nullable=False)
    macos_enabled = Column(Boolean, default=False, nullable=False)
    interested_tags = Column(JSON, nullable=False, default=list, comment="≤10 个 string")
    blocked_tags = Column(JSON, nullable=False, default=list, comment="≤10 个 string")
    daily_count = Column(Integer, default=5, nullable=False, comment="MVP 固定 5")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
