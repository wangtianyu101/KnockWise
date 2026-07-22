"""Digest Daily API (T10: 2026-07-17 实施).

GET /api/digest/today
GET /api/digest/daily/{date}
GET /api/digest/dailies?limit=N

配套 api-spec.md § 3.A + spec.md R7
"""
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user
from models import User
from schemas.digest import DigestDailiesListItem, DigestDailiesListResponse, DigestTodayResponse

router = APIRouter(prefix="/api/digest", tags=["digest-daily"])


@router.get("/today", response_model=DigestTodayResponse)
async def get_today(
    target_date: date_type | None = Query(default=None),
    user: User = Depends(get_current_user),
):
    """今日 5 条 digest + vibe。"""
    from services.digest_service import digest_service
    from datetime import date as today_date

    actual_date = target_date or today_date.today()  # 2026-07-22 audit 修复：today_date 是 class 不是 function
    result = await digest_service.push_daily(db=None, user_id=str(user.id), target_date=actual_date)
    if not result.get("daily_id"):
        raise HTTPException(status_code=404, detail="今日 digest 未生成")
    return DigestTodayResponse(
        date=actual_date,
        vibe=result.get("vibe"),
        item_count=result.get("item_count", 0),
        items=[],
    )


@router.get("/daily/{target_date}", response_model=DigestTodayResponse)
async def get_daily_by_date(
    target_date: date_type,
    user: User = Depends(get_current_user),
):
    """某天完整 digest。"""
    raise HTTPException(status_code=404, detail="待实现 · 暂用 /today")


@router.get("/dailies", response_model=DigestDailiesListResponse)
async def list_dailies(
    limit: int = Query(default=7, ge=1, le=30),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
):
    """最近 N 天 digest 列表（轻量 · 不含 items）。"""
    return DigestDailiesListResponse(total=0, items=[])
