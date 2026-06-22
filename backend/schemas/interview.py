from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InterviewStart(BaseModel):
    round: str = "round1"
    style: str = "standard"


class InterviewOut(BaseModel):
    id: str
    user_id: str
    profile_id: str
    round: str
    style: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_questions: int = 0
    overall_score: Optional[float] = None
    is_favorite: bool = False

    model_config = ConfigDict(from_attributes=True)


class QuestionRecordOut(BaseModel):
    id: str
    interview_id: str
    question_id: Optional[str] = None
    question_text: str
    user_answer: Optional[str] = None
    followup_chain: list = Field(default_factory=list)
    score: Optional[int] = None
    blind_spots: list = Field(default_factory=list)
    time_spent: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerSubmit(BaseModel):
    user_answer: str
    time_spent: int = 0
