"""Sources API (T13: 2026-07-17 stub → 2026-07-25 实现).

GET    /api/digest/sources
POST   /api/digest/sources
PATCH  /api/digest/sources/{id}

配套 api-spec.md § 3.D + spec.md R5

2026-07-25 stub 修复:
- GET 改为 DB query（替换 hardcoded 返回）
- POST/PATCH 改为真实 DB insert/update
"""
import logging
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select

from core.database import async_session
from core.dependencies import get_current_user
from models import DigestSource as DigestSourceModel
from models import User
from schemas.digest import (
    DigestSource,
    DigestSourceCreate,
    DigestSourceListResponse,
    DigestSourceUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/digest", tags=["digest-sources"])

RSS_HEAD_TIMEOUT_SEC = 5.0


async def _validate_rss_url(url: str) -> None:
    """HEAD 请求校验 RSS URL 可达 · spec R5。

    失败抛 400。timeout 5s。
    """
    try:
        async with httpx.AsyncClient(timeout=RSS_HEAD_TIMEOUT_SEC) as client:
            resp = await client.head(url, follow_redirects=True)
            if resp.status_code >= 400:
                raise HTTPException(status_code=400, detail=f"RSS URL 不可达: HTTP {resp.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail=f"RSS URL 超时（>{RSS_HEAD_TIMEOUT_SEC}s）")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"RSS URL 请求失败: {e}")


@router.get("/sources", response_model=DigestSourceListResponse)
async def list_sources(
    enabled: bool | None = Query(default=None),
    include_system: bool = Query(default=True),
    user: User = Depends(get_current_user),
):
    """信源列表（系统 + 自定义）。"""
    async with async_session() as db:
        # system_count / user_count
        system_count = await db.scalar(
            select(func.count(DigestSourceModel.id)).where(DigestSourceModel.is_default.is_(True))
        ) or 0
        user_count = await db.scalar(
            select(func.count(DigestSourceModel.id)).where(
                DigestSourceModel.user_id == str(user.id),
                DigestSourceModel.is_default.is_(False),
            )
        ) or 0

        # items
        conditions = [DigestSourceModel.user_id == str(user.id)]
        if include_system:
            conditions.append(DigestSourceModel.is_default.is_(True))
        stmt = select(DigestSourceModel).where(or_(*conditions))
        if enabled is not None:
            stmt = stmt.where(DigestSourceModel.enabled.is_(enabled))
        result = await db.execute(stmt)
        items = list(result.scalars().all())

    return DigestSourceListResponse(
        system_count=system_count,
        user_count=user_count,
        items=items,
    )


@router.post("/sources", response_model=DigestSource, status_code=201)
async def create_source(
    body: DigestSourceCreate,
    user: User = Depends(get_current_user),
):
    """添加自定义 RSS 源。"""
    url_str = str(body.url)
    await _validate_rss_url(url_str)

    async with async_session() as db:
        # UNIQUE(user_id, url) 重复检查
        existing = await db.scalar(
            select(DigestSourceModel.id).where(
                DigestSourceModel.user_id == str(user.id),
                DigestSourceModel.url == url_str,
            )
        )
        if existing:
            raise HTTPException(status_code=409, detail="该 URL 已存在")

        new_source = DigestSourceModel(
            id=str(uuid4()),
            user_id=str(user.id),
            name=body.name,
            url=url_str,
            category=body.category,
            type=body.type,
            region=body.region,
            enabled=True,
            is_default=False,
            last_item_count=0,
        )
        db.add(new_source)
        await db.commit()
        await db.refresh(new_source)

    return new_source


@router.patch("/sources/{source_id}", response_model=DigestSource)
async def patch_source(
    source_id: str,
    body: DigestSourceUpdate,
    user: User = Depends(get_current_user),
):
    """部分更新 (启停 / 改名)。403 if other user's source."""
    async with async_session() as db:
        source = await db.scalar(
            select(DigestSourceModel).where(DigestSourceModel.id == source_id)
        )
        if source is None:
            raise HTTPException(status_code=404, detail="信源不存在")

        # 所有权：仅自定义源允许 PATCH（系统默认 is_default=True 不能改）
        if source.is_default or source.user_id != str(user.id):
            raise HTTPException(status_code=403, detail="无权修改此信源")

        if body.enabled is not None:
            source.enabled = body.enabled
        if body.name is not None:
            source.name = body.name

        await db.commit()
        await db.refresh(source)

    return source
