"""interview_settlement — V2 面试触发链（决策 4A 派生）

V2.1 T7：从 interview.py:complete 拆出的 3 个触发函数。

模块拆分目的（决策 4A：顺手拆 interview.py 803 行）：
- 触发逻辑与业务逻辑解耦
- 3 个函数各自有明确的失败兜底（决策 7A — log + 不抛 + 不阻塞主业务）
- V2 三个 service 共享同一触发入口

函数：
- trigger_settle_after_interview  → ProfileSettlementService.settle_after_interview（T7 实施）
- trigger_write_practice_log       → ObsidianSedimentService.write_practice_log（V2.2 T14 接入）
- trigger_v2_summary_invalidate    → Redis DEL summary cache（V2.3 接入）
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger("codemock.interview_settlement")


async def trigger_settle_after_interview(
    user_id: UUID, interview_id: UUID, db: AsyncSession
) -> Optional["SettlementResult"]:
    """面试完成触发 → ProfileSettlementService.settle_after_interview。

    决策 7A 派生：失败 log + return None，**不抛** + 不阻塞 interview 完成响应。

    V2.1 T7 实施：调 V2.1 settle_after_interview。
    V2.2 T14 接入：同时调 ObsidianSedimentService.write_practice_log（先放 stub）。
    """
    try:
        from services.profile_settlement_service import ProfileSettlementService
        result = await ProfileSettlementService().settle_after_interview(
            user_id=user_id, interview_id=interview_id, db=db,
        )
        log.info(
            f"trigger_settle_after_interview: user={user_id} interview={interview_id} "
            f"result={'ok' if result else 'none'}"
        )
        return result
    except Exception as e:
        log.warning(
            f"trigger_settle_after_interview failed: user={user_id} "
            f"interview={interview_id} error={e}"
        )
        return None


async def trigger_write_practice_log(
    user_id: UUID, interview_id: UUID, db: AsyncSession
) -> Optional[str]:
    """面试完成触发 → ObsidianSedimentService.write_practice_log。

    T7 占位：V2.2 T14 实施。失败 log + return None，**不抛**。
    """
    try:
        # V2.2 T14 接入：from services.obsidian_sediment_service import ObsidianSedimentService
        # return await ObsidianSedimentService().write_practice_log(...)
        log.debug(
            f"trigger_write_practice_log placeholder: user={user_id} interview={interview_id}"
        )
        return None
    except Exception as e:
        log.warning(
            f"trigger_write_practice_log failed: user={user_id} "
            f"interview={interview_id} error={e}"
        )
        return None


async def trigger_v2_summary_invalidate(
    user_id: UUID, db: AsyncSession
) -> bool:
    """面试完成触发 → Redis DEL summary cache 3 个 key。

    T7 占位：V2.3 接入。失败 log + return False，**不抛**。
    """
    try:
        from core.cache import cache
        await cache.delete(f"summary:dashboard:{user_id}")
        await cache.delete(f"summary:profile:{user_id}")
        await cache.delete(f"profile:{user_id}")
        log.debug(
            f"trigger_v2_summary_invalidate: cleared 3 cache keys for user={user_id}"
        )
        return True
    except Exception as e:
        log.warning(
            f"trigger_v2_summary_invalidate failed: user={user_id} error={e}"
        )
        return False
