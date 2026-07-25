"""Bookmark API (T11: 2026-07-17 stub → 2026-07-25 实现).

GET    /api/digest/bookmarks
POST   /api/digest/bookmarks
DELETE /api/digest/bookmarks/{item_id}

配套 api-spec.md § 3.B + spec.md R10
"""
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from core.database import async_session
from core.dependencies import get_current_user
from models import DigestBookmark as DigestBookmarkModel
from models import DigestDailyItem as DigestDailyItemModel
from models import User
from schemas.digest import (
    BookmarkCreate,
    BookmarkListItem,
    BookmarkListResponse,
    BookmarkResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/digest", tags=["digest-bookmarks"])


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def list_bookmarks(
    type: str | None = Query(default=None, pattern="^(model|application)$"),
    sort: str = Query(default="bookmarked_desc", pattern="^(bookmarked_desc|quality_desc|published_desc)$"),
    user: User = Depends(get_current_user),
):
    """我的收藏列表 · JOIN digest_daily_item 返回完整字段。

    sort 选项（spec api-spec.md §3.B）：
      - bookmarked_desc: 收藏时间最新
      - quality_desc: 质量分高 → 低
      - published_desc: 原文发布最新
    """
    async with async_session() as db:
        # JOIN bookmark + item
        stmt = (
            select(DigestBookmarkModel, DigestDailyItemModel)
            .join(
                DigestDailyItemModel,
                DigestDailyItemModel.id == DigestBookmarkModel.item_id,
            )
            .where(DigestBookmarkModel.user_id == str(user.id))
        )
        if type is not None:
            stmt = stmt.where(DigestDailyItemModel.type == type)

        # sort
        if sort == "quality_desc":
            stmt = stmt.order_by(DigestDailyItemModel.quality_score.desc())
        elif sort == "published_desc":
            stmt = stmt.order_by(DigestDailyItemModel.published_at.desc().nullslast())
        else:
            stmt = stmt.order_by(DigestBookmarkModel.created_at.desc())

        rows = (await db.execute(stmt)).all()
        total = await db.scalar(
            select(func.count(DigestBookmarkModel.id)).where(
                DigestBookmarkModel.user_id == str(user.id)
            )
        )

        items = [
            BookmarkListItem(
                item_id=item.id,
                title=item.title,
                summary=item.summary,
                type=item.type,
                region=item.region,
                source_name=item.source_name,
                source_url=item.source_url,
                quality_score=item.quality_score,
                bookmarked_at=bm.created_at,
                published_at=item.published_at,
            )
            for bm, item in rows
        ]

    return BookmarkListResponse(total=total or 0, items=items)


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    body: BookmarkCreate,
    user: User = Depends(get_current_user),
):
    """收藏某条 digest。spec R10: 409 if 已收藏 · 幂等返回已存在。"""
    async with async_session() as db:
        existing = await db.scalar(
            select(DigestBookmarkModel).where(
                DigestBookmarkModel.user_id == str(user.id),
                DigestBookmarkModel.item_id == body.item_id,
            )
        )
        if existing:
            return BookmarkResponse(
                id=existing.id,
                user_id=str(user.id),
                item_id=body.item_id,
                created_at=existing.created_at,
            )

        # spec R9: item 必须存在
        item = await db.scalar(
            select(DigestDailyItemModel).where(DigestDailyItemModel.id == body.item_id)
        )
        if item is None:
            raise HTTPException(status_code=404, detail="ITEM_NOT_FOUND")

        bm = DigestBookmarkModel(
            id=str(uuid4()),
            user_id=str(user.id),
            item_id=body.item_id,
        )
        db.add(bm)
        await db.commit()
        await db.refresh(bm)

    logger.info(f"bookmark: user={user.id} item={body.item_id}")
    return BookmarkResponse(
        id=bm.id,
        user_id=str(user.id),
        item_id=bm.item_id,
        created_at=bm.created_at,
    )


@router.delete("/bookmarks/{item_id}", status_code=204)
async def delete_bookmark(
    item_id: str,
    user: User = Depends(get_current_user),
):
    """取消收藏。404 if 未收藏。"""
    async with async_session() as db:
        existing = await db.scalar(
            select(DigestBookmarkModel).where(
                DigestBookmarkModel.user_id == str(user.id),
                DigestBookmarkModel.item_id == item_id,
            )
        )
        if existing is None:
            raise HTTPException(status_code=404, detail="BOOKMARK_NOT_FOUND")
        await db.delete(existing)
        await db.commit()