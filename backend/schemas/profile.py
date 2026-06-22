from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    id: str
    github_username: str
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileOut(BaseModel):
    id: str
    user_id: str
    tech_stack: list[str] = Field(default_factory=list)
    years_of_exp: int = 0
    current_level: str = "mid"
    target_companies: list[str] = Field(default_factory=list)
    resume_summary: Optional[str] = None
    skill_map: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    tech_stack: Optional[list[str]] = None
    years_of_exp: Optional[int] = None
    current_level: Optional[str] = None
    target_companies: Optional[list[str]] = None
    resume_text: Optional[str] = None
    skill_map: Optional[dict] = None
