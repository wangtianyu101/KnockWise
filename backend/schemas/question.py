from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class QuestionOut(BaseModel):
    id: UUID
    topic: str
    sub_topic: str
    difficulty: int
    round: str
    question_text: str
    answer_key_points: list
    followup_tree: dict

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    questions: list[QuestionOut]
    total: int
