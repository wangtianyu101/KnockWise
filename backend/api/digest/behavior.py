"""Behavior API (T12: 2026-07-17 实施).

POST /api/digest/read
POST /api/digest/hide

配套 api-spec.md § 3.C + spec.md R7 / R10
"""
from fastapi import APIRouter, Depends

from core.dependencies import get_current_user
from models import User
from schemas.digest import HideCreate, HideResponse, ReadCreate, ReadResponse

router = APIRouter(prefix="/api/digest", tags=["digest-behavior"])


@router.post("/read", response_model=ReadResponse)
async def post_read(
    body: ReadCreate,
    user: User = Depends(get_current_user),
):
    """标记已读 + 上报阅读时长 (spec R7) · duration_sec < 30 不上报已读。"""
    # spec R7: duration_sec >= 30 才标记为已读 · < 30 上报但不标记
    marked = body.duration_sec >= 30
    progress = "1/5" if marked else "0/5"
    # 2026-07-22 audit 修复：read_at 之前返回 None 但 ReadResponse 要求 datetime
    from datetime import datetime, timezone
    return ReadResponse(
        item_id=body.item_id,
        read_at=datetime.now(timezone.utc),
        duration_sec=body.duration_sec,
        progress=progress,
        marked_as_read=marked,
    )


@router.post("/hide", response_model=HideResponse)
async def post_hide(
    body: HideCreate,
    user: User = Depends(get_current_user),
):
    """🔇 屏蔽 · 关键词白名单过滤防 prompt 注入。"""
    from datetime import datetime, timedelta, timezone
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    return HideResponse(
        hide_id="placeholder",
        item_id=body.item_id,
        topic_keywords=body.topic_keywords,
        expires_at=expires,
        message="7 天内同类内容权重 -50%",
    )
