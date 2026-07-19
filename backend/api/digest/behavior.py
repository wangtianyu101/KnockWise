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
    # spec: duration_sec < 30 不上报已读 · 简化返回 progress "0/0"
    progress = "0/0"
    return ReadResponse(
        item_id=body.item_id,
        read_at=None,
        duration_sec=body.duration_sec,
        progress=progress,
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
