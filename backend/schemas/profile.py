from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserOut(BaseModel):
    id: str
    github_username: str
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileOut(BaseModel):
    id: str
    user_id: str
    tech_stack: list[str] = []
    years_of_exp: int = 0
    current_level: str = "mid"
    target_companies: list[str] = []
    resume_summary: Optional[str] = None
    skill_map: dict = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    tech_stack: Optional[list[str]] = None
    years_of_exp: Optional[int] = None
    current_level: Optional[str] = None
    target_companies: Optional[list[str]] = None
    resume_text: Optional[str] = None
