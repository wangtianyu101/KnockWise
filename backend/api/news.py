"""News API — AI daily/weekly reports, code stats, source management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import User
from services.news_service import news_service

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/daily")
async def list_dailies(user: User = Depends(get_current_user)):
    return news_service.list_dailies()


@router.get("/daily/latest")
async def latest_daily(date: str | None = None, user: User = Depends(get_current_user)):
    report = news_service.get_daily(date)
    if not report:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return report


@router.get("/weekly")
async def list_weeklies(user: User = Depends(get_current_user)):
    return news_service.list_weeklies()


@router.get("/weekly/latest")
async def latest_weekly(week: str | None = None, user: User = Depends(get_current_user)):
    report = news_service.get_weekly(week)
    if not report:
        raise HTTPException(status_code=404, detail="Weekly report not found")
    return report


@router.get("/stats")
async def code_stats(days: int = 7, user: User = Depends(get_current_user)):
    return news_service.get_code_stats(days)


@router.get("/sources")
async def list_sources(user: User = Depends(get_current_user)):
    return news_service.get_sources()
