"""Settings API (T14: 2026-07-17 stub → 2026-07-25 实现).

GET   /api/digest/settings
PATCH /api/digest/settings

配套 api-spec.md § 3.E + spec.md R5 + R6
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.database import async_session
from core.dependencies import get_current_user
from models import DigestSettings as DigestSettingsModel
from models import User
from schemas.digest import DigestSettings, DigestSettingsUpdate

router = APIRouter(prefix="/api/digest", tags=["digest-settings"])


def _model_to_schema(m: DigestSettingsModel) -> DigestSettings:
    return DigestSettings(
        user_id=str(m.user_id),
        push_hour=m.push_hour,
        push_minute=m.push_minute,
        push_timezone=m.push_timezone or "Asia/Shanghai",
        email_enabled=m.email_enabled,
        interested_tags=list(m.interested_tags or []),
        blocked_tags=list(m.blocked_tags or []),
    )


@router.get("/settings", response_model=DigestSettings)
async def get_settings(
    user: User = Depends(get_current_user),
):
    """读取推送设置。无记录则自动创建默认（spec R6 scenario 21）。"""
    async with async_session() as db:
        result = await db.scalar(
            select(DigestSettingsModel).where(DigestSettingsModel.user_id == str(user.id))
        )
        if result is None:
            result = DigestSettingsModel(
                user_id=str(user.id),
                push_hour=8,
                push_minute=0,
                push_timezone="Asia/Shanghai",
                email_enabled=True,
                interested_tags=[],
                blocked_tags=[],
            )
            db.add(result)
            await db.commit()
            await db.refresh(result)
        return _model_to_schema(result)


@router.patch("/settings", response_model=DigestSettings)
async def patch_settings(
    body: DigestSettingsUpdate,
    user: User = Depends(get_current_user),
):
    """部分更新。所有字段 optional。

    spec R5 scenario 34: tags 超过 10 → 422 TAGS_LIMIT_EXCEEDED
    spec R6 scenario 22: push_hour 改 → 下次按新时间触发
    spec R6 scenario 23: 时区改 → 按新时区计算下次推送
    """
    # spec R5: tags 超过 10
    if body.interested_tags is not None and len(body.interested_tags) > 10:
        raise HTTPException(status_code=422, detail="TAGS_LIMIT_EXCEEDED: interested_tags 上限 10")
    if body.blocked_tags is not None and len(body.blocked_tags) > 10:
        raise HTTPException(status_code=422, detail="TAGS_LIMIT_EXCEEDED: blocked_tags 上限 10")

    # spec R6 scenario 23: 校验时区是有效 IANA
    if body.push_timezone is not None:
        try:
            ZoneInfo(body.push_timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise HTTPException(status_code=400, detail=f"无效时区: {body.push_timezone}")

    async with async_session() as db:
        result = await db.scalar(
            select(DigestSettingsModel).where(DigestSettingsModel.user_id == str(user.id))
        )
        if result is None:
            result = DigestSettingsModel(user_id=str(user.id))
            db.add(result)

        if body.push_hour is not None:
            result.push_hour = body.push_hour
        if body.push_minute is not None:
            result.push_minute = body.push_minute
        if body.push_timezone is not None:
            result.push_timezone = body.push_timezone
        if body.email_enabled is not None:
            result.email_enabled = body.email_enabled
        if body.interested_tags is not None:
            result.interested_tags = body.interested_tags
        if body.blocked_tags is not None:
            result.blocked_tags = body.blocked_tags

        await db.commit()
        await db.refresh(result)
        return _model_to_schema(result)