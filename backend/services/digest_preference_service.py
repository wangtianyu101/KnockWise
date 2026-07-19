"""DigestPreferenceService (T9: 2026-07-17 实施).

整合用户偏好供 composite_score 使用:
- interested_tags / blocked_tags from digest_settings
- hide_topics from digest_hide (7 天内 expire, spec R5)
- source_authority_bias (默认 1.0, 用户可调)

配套 docs/tasks/2026-07-17-new-feature-ai-push/spec.md § R5 + R10 + api-spec.md § 3.E
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import DigestHide, DigestSettings


# hide topic_keywords 7 天后失效 (spec R5)
HIDE_EXPIRY_DAYS = 7


class DigestPreferenceService:
    """AI 推送给 composite_score 用的用户偏好整合。"""

    async def get_user_prefs(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> dict[str, Any]:
        """返回 composite_score 用的偏好 dict。

        Returns:
            {
                "interested_tags": list[str],   # 关注标签
                "blocked_tags": list[str],       # 屏蔽标签
                "hide_topics": list[str],        # 7 天内屏蔽过的 topic 关键词
                "source_authority_bias": float,  # 1.0 默认
            }

        逻辑:
        1. 查 digest_settings · 取 interested_tags / blocked_tags
        2. 查 digest_hide · 过滤 expires_at > now · 提取 topic_keywords
        3. 默认值: settings 不存在 → 空 list + 1.0 bias
        """
        # 1. settings
        settings = await self._get_settings(db, user_id)

        # 2. active hide topics (7 天内)
        hide_topics = await self._get_active_hide_topics(db, user_id)

        return {
            "interested_tags": settings.get("interested_tags", []),
            "blocked_tags": settings.get("blocked_tags", []),
            "hide_topics": hide_topics,
            "source_authority_bias": 1.0,  # 未来扩展
        }

    async def _get_settings(
        self, db: AsyncSession, user_id: str
    ) -> dict[str, Any]:
        """查 digest_settings · 不存在返回默认值。"""
        stmt = select(DigestSettings).where(DigestSettings.user_id == user_id)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if settings is None:
            return {"interested_tags": [], "blocked_tags": []}

        return {
            "interested_tags": list(settings.interested_tags or []),
            "blocked_tags": list(settings.blocked_tags or []),
        }

    async def _get_active_hide_topics(
        self, db: AsyncSession, user_id: str
    ) -> list[str]:
        """查 7 天内未过期的 hide 记录 · 提取所有 topic_keywords。"""
        now = datetime.now(timezone.utc)
        stmt = (
            select(DigestHide)
            .where(
                DigestHide.user_id == user_id,
                DigestHide.expires_at > now,
            )
        )
        result = await db.execute(stmt)
        hides = result.scalars().all()

        # 合并所有 keywords 去重
        all_keywords: set[str] = set()
        for hide in hides:
            if hide.topic_keywords:
                for kw in hide.topic_keywords:
                    if kw:
                        all_keywords.add(kw)
        return list(all_keywords)
