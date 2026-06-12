from typing import Any

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

    @field_validator('answer_key_points', mode='before')
    @classmethod
    def _coerce_answer_key_points(cls, v: Any) -> Any:
        """SQLAlchemy default may not be applied before flush — coerce None → []."""
        return [] if v is None else v

    @field_validator('followup_tree', mode='before')
    @classmethod
    def _coerce_followup_tree(cls, v: Any) -> Any:
        """SQLAlchemy default may not be applied before flush — coerce None → {}."""
        return {} if v is None else v


class QuestionListResponse(BaseModel):
    questions: list[QuestionOut]
    total: int
