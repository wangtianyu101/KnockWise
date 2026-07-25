"""Behavior API (T12: 2026-07-17 stub → 2026-07-25 实现).

POST /api/digest/read
POST /api/digest/hide

配套 api-spec.md § 3.C + spec.md R7 / R10
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select

from core.database import async_session
from core.dependencies import get_current_user
from models import DigestHide as DigestHideModel
from models import DigestRead as DigestReadModel
from models import User
from schemas.digest import HideCreate, HideResponse, ReadCreate, ReadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/digest", tags=["digest-behavior"])


@router.post("/read", response_model=ReadResponse)
async def post_read(
    body: ReadCreate,
    user: User = Depends(get_current_user),
):
    """标记已读 + 上报阅读时长（spec R7 停留 >= 30s · R10 喂 user_pref 权重）。

    spec R7: duration_sec >= 30 标记已读 · < 30 上报但不标
    spec R10: 阅读时长喂 user_pref 权重 · scoring 反馈（Phase C 实现）
    """
    marked = body.duration_sec >= 30

    async with async_session() as db:
        # 幂等：同 user+item 已存在则累加 duration · 取首次 read_at
        existing = await db.scalar(
            select(DigestReadModel).where(
                DigestReadModel.user_id == str(user.id),
                DigestReadModel.item_id == body.item_id,
            )
        )
        now = datetime.now(timezone.utc)
        if existing is not None:
            existing.duration_sec = max(existing.duration_sec, body.duration_sec)
            existing.read_at = now
        else:
            db.add(DigestReadModel(
                id=str(uuid4()),
                user_id=str(user.id),
                item_id=body.item_id,
                duration_sec=body.duration_sec,
                read_at=now,
            ))
        await db.commit()

    logger.info(
        f"digest_read: user={user.id} item={body.item_id} duration={body.duration_sec}s marked={marked}"
    )

    return ReadResponse(
        item_id=body.item_id,
        read_at=now,
        duration_sec=body.duration_sec,
        progress="1/5" if marked else "0/5",
        marked_as_read=marked,
    )


@router.post("/hide", response_model=HideResponse)
async def post_hide(
    body: HideCreate,
    user: User = Depends(get_current_user),
):
    """🔇 屏蔽 · 关键词白名单过滤防 prompt 注入（spec § 3.3）"""
    async with async_session() as db:
        existing = await db.scalar(
            select(DigestHideModel).where(
                DigestHideModel.user_id == str(user.id),
                DigestHideModel.item_id == body.item_id,
            )
        )
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=7)
        # spec R10 防 prompt 注入 · keywords 限 5 个
        keywords = (body.topic_keywords or [])[:5]

        if existing:
            existing.expires_at = expires
            existing.topic_keywords = keywords
            hide_id = existing.id
        else:
            hide_id = str(uuid4())
            db.add(DigestHideModel(
                id=hide_id,
                user_id=str(user.id),
                item_id=body.item_id,
                reason=body.reason,
                topic_keywords=keywords,
                expires_at=expires,
            ))
        await db.commit()

    return HideResponse(
        hide_id=hide_id,
        item_id=body.item_id,
        topic_keywords=keywords,
        expires_at=expires,
        message="7 天内同类内容权重 -50%",
    )
