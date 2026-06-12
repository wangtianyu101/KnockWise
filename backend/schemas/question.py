from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionOut(BaseModel):
    id: str  # semantic IDs like 'agent_001', NOT UUIDs
    topic: str
    sub_topic: str
    difficulty: int
    round: str
    question_text: str
    answer_key_points: list = Field(default_factory=list)
    followup_tree: dict = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

    @field_validator('answer_key_points', 'followup_tree', mode='before')
    @classmethod
    def coerce_none(cls, v, info):
        """SQLAlchemy defaults may not be applied before flush — coerce None."""
        if v is None:
            return [] if info.field_name == 'answer_key_points' else {}
        return v


class QuestionListResponse(BaseModel):
    questions: list[QuestionOut]
    total: int
