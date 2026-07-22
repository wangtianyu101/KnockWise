"""Scheduler contracts for clock handling and durable digest deduplication."""
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.digest_scheduler import DigestScheduler


def settings_for(user_id: str):
    return SimpleNamespace(
        user_id=user_id,
        email_enabled=True,
        push_hour=8,
        push_minute=0,
        push_timezone="Asia/Shanghai",
    )


@pytest.mark.asyncio
async def test_scheduler_uses_injected_clock_and_service():
    fixed_now = datetime(2026, 7, 22, 0, 0, tzinfo=timezone.utc)
    service = AsyncMock()
    service.push_daily.return_value = {"daily_id": "daily-1"}
    scheduler = DigestScheduler(service=service, now_provider=lambda: fixed_now)
    settings_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: [settings_for("user-1")])
    )
    no_daily_result = SimpleNamespace(scalar_one_or_none=lambda: None)
    db = AsyncMock()
    db.execute.side_effect = [settings_result, no_daily_result]

    result = await scheduler.check_and_push(db)

    assert result == {"checked": 1, "pushed": 1, "skipped": 0, "errors": 0}
    service.push_daily.assert_awaited_once()
    assert service.push_daily.await_args.kwargs["target_date"].isoformat() == "2026-07-22"


@pytest.mark.asyncio
async def test_scheduler_skips_digest_already_persisted_for_date():
    fixed_now = datetime(2026, 7, 22, 0, 0, tzinfo=timezone.utc)
    service = AsyncMock()
    scheduler = DigestScheduler(service=service, now_provider=lambda: fixed_now)
    settings_result = SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: [settings_for("user-1")])
    )
    existing_result = SimpleNamespace(scalar_one_or_none=lambda: "daily-existing")
    db = AsyncMock()
    db.execute.side_effect = [settings_result, existing_result]

    result = await scheduler.check_and_push(db)

    assert result == {"checked": 1, "pushed": 0, "skipped": 1, "errors": 0}
    service.push_daily.assert_not_awaited()
