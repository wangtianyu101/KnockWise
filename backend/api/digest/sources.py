"""Sources API (T13: 2026-07-17 实施).

GET    /api/digest/sources
POST   /api/digest/sources
PATCH  /api/digest/sources/{id}

配套 api-spec.md § 3.D + spec.md R5
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from core.dependencies import get_current_user
from models import User
from schemas.digest import (
    DigestSource,
    DigestSourceCreate,
    DigestSourceListResponse,
    DigestSourceUpdate,
)

router = APIRouter(prefix="/api/digest", tags=["digest-sources"])


@router.get("/sources", response_model=DigestSourceListResponse)
async def list_sources(
    enabled: bool | None = Query(default=None),
    include_system: bool = Query(default=True),
    user: User = Depends(get_current_user),
):
    """信源列表（系统 + 自定义）。"""
    return DigestSourceListResponse(system_count=8, user_count=0, items=[])


@router.post("/sources", response_model=DigestSource, status_code=201)
async def create_source(
    body: DigestSourceCreate,
    user: User = Depends(get_current_user),
):
    """添加自定义 RSS 源。"""
    # spec: HEAD request 校验 RSS 可达 · 409 if duplicate
    raise HTTPException(status_code=400, detail="待实现 · 校验 RSS + 写 DB")


@router.patch("/sources/{source_id}", response_model=DigestSource)
async def patch_source(
    source_id: str,
    body: DigestSourceUpdate,
    user: User = Depends(get_current_user),
):
    """部分更新 (启停 / 改名)。403 if other user's source."""
    # spec: 403 FORBIDDEN if not owner
    raise HTTPException(status_code=403, detail="待实现 · 验证所有权")
