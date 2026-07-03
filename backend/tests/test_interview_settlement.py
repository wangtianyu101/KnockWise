"""单测: services/interview_settlement.py

V2.1 T7: 3 个 trigger 函数测试。
- trigger_settle_after_interview (调 ProfileSettlementService.settle_after_interview)
- trigger_write_practice_log (V2.2 T14 接入前的占位)
- trigger_v2_summary_invalidate (V2.3 接入前的占位)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import interview_settlement as svc


# ─── T7: trigger_settle_after_interview ──────────────────────

class TestTriggerSettleAfterInterview:
    async def test_calls_settle_after_interview(self):
        from uuid import uuid4
        from types import SimpleNamespace

        user_id = uuid4()
        interview_id = uuid4()
        mock_db = AsyncMock()

        with patch(
            "services.profile_settlement_service.ProfileSettlementService"
        ) as MockSettle:
            mock_instance = MockSettle.return_value
            mock_instance.settle_after_interview = AsyncMock(
                return_value=SimpleNamespace(user_id=user_id)
            )

            result = await svc.trigger_settle_after_interview(
                user_id, interview_id, mock_db,
            )

            mock_instance.settle_after_interview.assert_awaited_once()
            assert result is not None

    async def test_does_not_throw_on_failure(self):
        """决策 7A：失败 log + return None，**不抛**。"""
        from uuid import uuid4

        user_id = uuid4()
        interview_id = uuid4()
        mock_db = AsyncMock()

        with patch(
            "services.profile_settlement_service.ProfileSettlementService"
        ) as MockSettle:
            mock_instance = MockSettle.return_value
            mock_instance.settle_after_interview = AsyncMock(
                side_effect=Exception("boom")
            )

            # 关键：不抛
            result = await svc.trigger_settle_after_interview(
                user_id, interview_id, mock_db,
            )
            assert result is None


# ─── T7: trigger_write_practice_log（占位）─────────────

class TestTriggerWritePracticeLog:
    async def test_placeholder_returns_none(self):
        from uuid import uuid4
        user_id = uuid4()
        interview_id = uuid4()
        mock_db = AsyncMock()

        result = await svc.trigger_write_practice_log(user_id, interview_id, mock_db)
        assert result is None


# ─── T7: trigger_v2_summary_invalidate（占位）─────────

class TestTriggerV2SummaryInvalidate:
    async def test_clears_3_cache_keys(self, mock_cache):
        from uuid import uuid4
        user_id = uuid4()
        mock_db = AsyncMock()

        result = await svc.trigger_v2_summary_invalidate(user_id, mock_db)

        assert result is True
        # 3 个 key 被删
        assert mock_cache.delete.await_count == 3
