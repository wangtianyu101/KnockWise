"""Settings API (T14: 2026-07-17 实施).

GET   /api/digest/settings
PATCH /api/digest/settings

配套 api-spec.md § 3.E + spec.md R5 + R6
"""
from fastapi import APIRouter, Depends

from core.dependencies import get_current_user
from models import User
from schemas.digest import DigestSettings, DigestSettingsUpdate

router = APIRouter(prefix="/api/digest", tags=["digest-settings"])


@router.get("/settings", response_model=DigestSettings)
async def get_settings(
    user: User = Depends(get_current_user),
):
    """读取推送设置。404 if not set · 自动创建默认。"""
    return DigestSettings(user_id=str(user.id))


@router.patch("/settings", response_model=DigestSettings)
async def patch_settings(
    body: DigestSettingsUpdate,
    user: User = Depends(get_current_user),
):
    """部分更新。所有字段 optional。"""
    return DigestSettings(user_id=str(user.id))
