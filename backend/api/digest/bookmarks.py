"""Bookmark API (T11: 2026-07-17 实施).

GET    /api/digest/bookmarks
POST   /api/digest/bookmarks
DELETE /api/digest/bookmarks/{item_id}

配套 api-spec.md § 3.B + spec.md R10
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user
from models import User
from schemas.digest import (
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
)

router = APIRouter(prefix="/api/digest", tags=["digest-bookmarks"])


@router.get("/bookmarks", response_model=BookmarkListResponse)
async def list_bookmarks(
    type: str | None = Query(default=None),
    sort: str = Query(default="bookmarked_desc"),
    user: User = Depends(get_current_user),
):
    """我的收藏列表。"""
    return BookmarkListResponse(total=0, items=[])


@router.post("/bookmarks", response_model=BookmarkResponse, status_code=201)
async def create_bookmark(
    body: BookmarkCreate,
    user: User = Depends(get_current_user),
):
    """收藏某条 digest。"""
    # spec R10: 409 if already bookmarked
    raise HTTPException(status_code=409, detail="待实现 · 检查重复 + 写 DB")


@router.delete("/bookmarks/{item_id}", status_code=204)
async def delete_bookmark(
    item_id: str,
    user: User = Depends(get_current_user),
):
    """取消收藏。404 if not bookmarked."""
    raise HTTPException(status_code=404, detail="待实现")
