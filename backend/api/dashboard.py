"""Dashboard API — aggregated cross-module overview data."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import User, Interview

from services.obsidian_service import obsidian
from services.news_service import news_service
from services.recommendations_service import get_recommendations

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated cross-module dashboard data."""

    # ── Interview ──
    result = await db.execute(
        select(Interview).where(Interview.user_id == user.id)
        .order_by(Interview.started_at.desc())
    )
    interviews = result.scalars().all()
    completed = [i for i in interviews if i.status == "completed"]
    scores = [i.overall_score for i in completed if i.overall_score is not None]
    latest_score = scores[0] if scores else None
    trend = "up" if len(scores) >= 2 and scores[0] > scores[-1] else "flat"

    # ── Knowledge ──
    try: kstats = obsidian.get_stats()
    except Exception: kstats = {"total_notes": 0, "total_words": 0}

    # ── News / Stats ──
    try: cstats = news_service.get_code_stats(days=7)
    except Exception: cstats = {"summary": {}, "daily": []}

    cs = cstats.get("summary", {})

    # ── Recommendations ──
    try: recs = await get_recommendations(user, db)
    except Exception: recs = []

    return {
        "interview": {
            "total": len(interviews),
            "completed": len(completed),
            "in_progress": len([i for i in interviews if i.status == "in_progress"]),
            "latest_score": latest_score,
            "score_trend": trend,
        },
        "knowledge": {
            "total_notes": kstats["total_notes"],
            "total_words": kstats["total_words"],
        },
        "stats": {
            "total_tokens": cs.get("total_tokens", 0),
            "total_code": cs.get("total_code", 0),
            "total_days": cs.get("total_days", 0),
        },
        "recommendations": recs,
    }
