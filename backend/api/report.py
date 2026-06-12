from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from models import User, Interview, Report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/interview/{interview_id}")
async def get_report(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Report).where(
            Report.interview_id == str(interview_id),
            Report.user_id == user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/interview/{interview_id}")
async def generate_report(
    interview_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a report for a completed interview. Placeholder — Agent will replace this."""
    # Verify interview belongs to user
    result = await db.execute(
        select(Interview).where(
            Interview.id == str(interview_id),
            Interview.user_id == user.id,
        )
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if interview.status != "completed":
        raise HTTPException(status_code=400, detail="Interview not yet completed")

    # Check if report already exists
    existing = await db.execute(
        select(Report).where(Report.interview_id == str(interview_id))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Report already exists")

    # Stub report
    report = Report(
        interview_id=str(interview_id),
        user_id=user.id,
        radar_data={
            "agent_architecture": 3,
            "tool_use": 3,
            "memory": 3,
            "mcp": 3,
            "retrieval": 3,
            "chunking": 3,
            "advanced_rag": 3,
            "rag_evaluation": 3,
            "langchain": 3,
            "langgraph": 3,
            "java": 3,
        },
        top_blind_spots=[],
        improvement_plan=[],
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
