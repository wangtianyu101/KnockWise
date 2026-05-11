from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import User, Profile
from schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.put("/me", response_model=ProfileOut)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)

    if data.tech_stack is not None:
        profile.tech_stack = data.tech_stack
    if data.years_of_exp is not None:
        profile.years_of_exp = data.years_of_exp
    if data.current_level is not None:
        profile.current_level = data.current_level
    if data.target_companies is not None:
        profile.target_companies = data.target_companies
    if data.resume_text is not None:
        profile.resume_summary = _extract_resume_summary(data.resume_text)

    await db.commit()
    await db.refresh(profile)
    return profile


def _extract_resume_summary(resume_text: str) -> str:
    """Stub — will use LLM extraction in Week 2"""
    # Keep first 2000 chars as raw summary until we wire LLM
    return resume_text[:2000]
