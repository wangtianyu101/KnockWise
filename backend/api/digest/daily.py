"""Digest Daily API (T10: 2026-07-17 实施).

GET /api/digest/today
GET /api/digest/daily/{date}
GET /api/digest/dailies?limit=N

配套 api-spec.md § 3.A + spec.md R7
"""
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models import DigestDaily as DigestDailyModel
from models import DigestDailyItem as DigestDailyItemModel
from models import User
from schemas.digest import (
    DigestDailiesListItem,
    DigestDailiesListResponse,
    DigestDailyItem as DigestDailyItemSchema,
    DigestTodayResponse,
)

router = APIRouter(prefix="/api/digest", tags=["digest-daily"])


@router.get("/today", response_model=DigestTodayResponse)
async def get_today(
    target_date: date_type | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """今日 5 条 digest + vibe。"""
    from datetime import date as today_date

    actual_date = target_date or today_date.today()
    return await _load_daily(db, str(user.id), actual_date)


@router.get("/daily/{target_date}", response_model=DigestTodayResponse)
async def get_daily_by_date(
    target_date: date_type,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """某天完整 digest。"""
    return await _load_daily(db, str(user.id), target_date)


@router.get("/dailies", response_model=DigestDailiesListResponse)
async def list_dailies(
    limit: int = Query(default=7, ge=1, le=30),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """最近 N 天 digest 列表（轻量 · 不含 items）。"""
    user_id = str(user.id)
    total_result = await db.execute(
        select(func.count(DigestDailyModel.id)).where(
            DigestDailyModel.user_id == user_id
        )
    )
    total = int(total_result.scalar_one() or 0)
    rows_result = await db.execute(
        select(DigestDailyModel)
        .where(DigestDailyModel.user_id == user_id)
        .order_by(DigestDailyModel.date.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = list(rows_result.scalars().all())
    return DigestDailiesListResponse(
        total=total,
        items=[
            DigestDailiesListItem(
                date=row.date,
                vibe=row.vibe,
                item_count=len(row.item_ids or []),
            )
            for row in rows
        ],
    )


async def _load_daily(
    db: AsyncSession,
    user_id: str,
    target_date: date_type,
) -> DigestTodayResponse:
    daily_result = await db.execute(
        select(DigestDailyModel).where(
            DigestDailyModel.user_id == user_id,
            DigestDailyModel.date == target_date,
        )
    )
    daily = daily_result.scalar_one_or_none()
    if daily is None:
        raise HTTPException(status_code=404, detail="今日 digest 未生成")

    items_result = await db.execute(
        select(DigestDailyItemModel)
        .where(DigestDailyItemModel.daily_id == daily.id)
        .order_by(DigestDailyItemModel.rank)
    )
    rows = list(items_result.scalars().all())
    items = [
        DigestDailyItemSchema(
            id=row.id,
            rank=row.rank,
            title=row.title,
            summary=row.summary,
            quality_score=row.quality_score,
            type=row.type,
            region=row.region,
            category=row.category,
            source_name=row.source_name,
            source_url=row.source_url,
            published_at=row.published_at,
            estimated_minutes=row.estimated_minutes,
            related_item_ids=list(row.related_item_ids or []),
            is_read=False,
            is_bookmarked=False,
        )
        for row in rows
    ]
    return DigestTodayResponse(
        date=daily.date,
        vibe=daily.vibe,
        item_count=len(items),
        items=items,
    )
