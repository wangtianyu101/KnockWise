"""学习复习模块 Pydantic schemas (Phase 1c · 配套 docs/10-架构/面试题库-技术设计.md)。

约定:
- 所有 datetime → ISO 字符串
- 所有 optional 字段默认 None
- input / output / list / detail 命名分清
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
#  题目 / 进度 (基础类型)
# ════════════════════════════════════════════════════════════

MasteryStatus = Literal["new", "learning", "mastered", "skipped"]
QuestionSource = Literal["seed", "user_note", "news", "mock_interview"]
RecommendReason = Literal["weak_spot", "due_review", "untouched", "bookmark", "random"]


class QuestionProgressOut(BaseModel):
    id: str
    status: MasteryStatus
    practice_count: int
    correct_count: int
    bookmarked: bool
    ease_factor: float
    interval_days: int
    next_review_at: Optional[str]
    last_practiced_at: Optional[str]
    user_answer: Optional[str] = None
    notes_path: Optional[str] = None


class QuestionListItem(BaseModel):
    id: str
    topic: str
    sub_topic: str
    difficulty: int
    question_text: str
    source: QuestionSource
    progress: Optional[QuestionProgressOut] = None
    tags: list[str] = []


class RelatedNote(BaseModel):
    path: str
    title: str


class QuestionDetail(BaseModel):
    id: str
    topic: str
    sub_topic: str
    difficulty: int
    question_text: str
    answer_key_points: list[str] = []
    followup_tree: dict[str, Any] = {}
    source: QuestionSource
    tags: list[str] = []
    progress: Optional[QuestionProgressOut] = None
    note: Optional["UserNoteOut"] = None
    related_notes: list[RelatedNote] = []


class QuestionListResponse(BaseModel):
    items: list[QuestionListItem]
    total: int
    page: int
    size: int


class QuestionListFilter(BaseModel):
    topic: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    source: Optional[QuestionSource] = None
    bookmarked: Optional[bool] = None
    q: Optional[str] = None
    sort: Literal["id", "difficulty", "last_practiced", "random"] = "id"
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# ════════════════════════════════════════════════════════════
#  答题 / 进度更新
# ════════════════════════════════════════════════════════════


class SubmitAnswerInput(BaseModel):
    user_answer: str
    score: int = Field(..., ge=0, le=5, description="0=完全不会, 5=完美")
    blind_spots: list[str] = []
    duration_sec: int = 0
    source: Optional[QuestionSource] = "practice"


class SubmitAnswerResponse(BaseModel):
    progress: QuestionProgressOut
    next_question_id: Optional[str] = None
    review_queue_remaining: int = 0


class UpdateProgressInput(BaseModel):
    bookmarked: Optional[bool] = None
    status: Optional[MasteryStatus] = None
    notes_path: Optional[str] = None


class UpdateProgressResponse(BaseModel):
    progress: QuestionProgressOut


class ProgressListResponse(BaseModel):
    items: list[QuestionProgressOut]
    total: int
    page: int
    size: int


# ════════════════════════════════════════════════════════════
#  推荐 / 复习队列
# ════════════════════════════════════════════════════════════


class RecommendItem(BaseModel):
    id: str
    topic: str
    sub_topic: str
    difficulty: int
    question_text: str
    source: QuestionSource
    reason: RecommendReason = "random"


class RecommendResponse(BaseModel):
    items: list[RecommendItem]


class ReviewQueueItem(BaseModel):
    question_id: str
    status: MasteryStatus
    ease_factor: float
    interval_days: int
    next_review_at: Optional[str]


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]
    total: int


# ════════════════════════════════════════════════════════════
#  Session (练习会话)
# ════════════════════════════════════════════════════════════


class StartSessionInput(BaseModel):
    type: Literal["practice", "review", "qa"] = "practice"


class StartSessionResponse(BaseModel):
    session_id: str
    type: str
    started_at: str


class SessionItem(BaseModel):
    question_id: str
    status: MasteryStatus
    duration_sec: int = 0
    score: Optional[int] = None


class EndSessionInput(BaseModel):
    items: list[SessionItem]


class EndSessionResponse(BaseModel):
    session_id: str
    duration_sec: int
    item_count: int


class RecentSessionItem(BaseModel):
    id: str
    type: str
    started_at: Optional[str]
    ended_at: Optional[str]
    duration_sec: int
    item_count: int


class RecentSessionsResponse(BaseModel):
    items: list[RecentSessionItem]


# ════════════════════════════════════════════════════════════
#  学习计划
# ════════════════════════════════════════════════════════════


class WeeklyTarget(BaseModel):
    week_idx: int
    target_count: int = 0
    target_topics: list[str] = []


class StudyPlan(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    goal: Optional[str] = None
    start_date: str
    end_date: str
    status: Literal["active", "completed", "archived"] = "active"
    weekly_target: list[WeeklyTarget] = []
    progress: dict[str, Any] = {}


class CreateStudyPlanInput(BaseModel):
    name: str
    description: Optional[str] = None
    goal: Optional[str] = None
    start_date: str  # ISO date
    end_date: str
    status: Literal["active", "completed", "archived"] = "active"
    weekly_target: list[WeeklyTarget] = []


class UpdateStudyPlanInput(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[Literal["active", "completed", "archived"]] = None
    weekly_target: Optional[list[WeeklyTarget]] = None


class StudyPlanProgressResponse(BaseModel):
    total_target: int
    mastered: int
    learning: int
    new_count: int
    completion_rate: float
    weak_topics_remaining: list[str]


# ════════════════════════════════════════════════════════════
#  QA session (LLM 问答)
# ════════════════════════════════════════════════════════════


class QAMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    ts: str


class QASession(BaseModel):
    id: str
    question_id: str
    created_at: Optional[str]
    message_count: int = 0


class QASessionDetail(BaseModel):
    id: str
    question_id: str
    created_at: Optional[str]
    messages: list[QAMessage] = []


class QASessionListResponse(BaseModel):
    items: list[QASession]


class CreateQASessionInput(BaseModel):
    question_id: str


class QAChatInput(BaseModel):
    question_id: str
    session_id: Optional[str] = None
    message: str


class QAChatResponse(BaseModel):
    session_id: Optional[str]
    reply: str
    messages: list[QAMessage] = []


# ════════════════════════════════════════════════════════════
#  Tag / Note / UserQuestion / Stats
# ════════════════════════════════════════════════════════════


class TagOut(BaseModel):
    id: str
    name: str
    color: Optional[str] = None
    is_system: bool
    user_id: Optional[str] = None


class CreateTagInput(BaseModel):
    name: str
    color: Optional[str] = None
    is_system: bool = False


class UserNoteOut(BaseModel):
    id: str
    content_md: str
    updated_at: Optional[str] = None


class UpsertUserNoteInput(BaseModel):
    content_md: str


class CreateUserQuestionInput(BaseModel):
    question_text: str
    answer: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    difficulty: int = Field(default=3, ge=1, le=5)
    tags: list[str] = []
    source: QuestionSource = "user_note"


class UpdateUserQuestionInput(BaseModel):
    question_text: Optional[str] = None
    answer: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)
    tags: Optional[list[str]] = None


class LearnStatsResponse(BaseModel):
    total_practice: int
    total_correct: int
    accuracy: float
    by_status: dict[str, int]
    bookmarked: int
    week_session_sec: int


# Resolve forward references
QuestionDetail.model_rebuild()