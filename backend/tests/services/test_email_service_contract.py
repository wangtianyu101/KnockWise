"""Email provider boundary contract tests."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services.email_service import EmailService


@pytest.mark.asyncio
async def test_send_daily_digest_calls_provider_once_and_returns_message_id():
    provider = AsyncMock()
    provider.send.return_value = "msg-123"
    service = EmailService(provider=provider)

    result = await service.send_daily_digest(
        "user@example.com",
        "2026-07-22",
        [{"title": "News", "source_url": "https://example.com"}],
        "今日 1 条",
    )

    assert result["message_id"] == "msg-123"
    assert result["error"] is None
    provider.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_transient_provider_failure_retries_then_succeeds():
    provider = AsyncMock()
    provider.send.side_effect = [RuntimeError("temporary"), "msg-456"]
    service = EmailService(provider=provider)

    with patch("services.email_service.asyncio.sleep", new_callable=AsyncMock):
        result = await service.send_daily_digest(
            "user@example.com", "2026-07-22", [], None
        )

    assert result["message_id"] == "msg-456"
    assert provider.send.await_count == 2


@pytest.mark.asyncio
async def test_missing_recipient_does_not_call_provider():
    provider = AsyncMock()
    service = EmailService(provider=provider)

    result = await service.send_daily_digest("", "2026-07-22", [], None)

    assert result["error"] == "no user email"
    provider.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_digest_uses_same_result_without_second_delivery():
    provider = AsyncMock()
    provider.send.return_value = "msg-idempotent"
    service = EmailService(provider=provider)

    first = await service.send_daily_digest(
        "user@example.com", "2026-07-22", [], None
    )
    second = await service.send_daily_digest(
        "USER@example.com", "2026-07-22", [], None
    )

    assert first["message_id"] == second["message_id"] == "msg-idempotent"
    provider.send.assert_awaited_once()
    assert provider.send.await_args.kwargs["idempotency_key"].startswith("digest-")


@pytest.mark.asyncio
async def test_one_recipient_retry_does_not_block_another_recipient():
    provider = AsyncMock()

    async def send(to_email, *_args, **_kwargs):
        if to_email == "slow@example.com":
            raise RuntimeError("retry me")
        return "msg-fast"

    provider.send.side_effect = send
    service = EmailService(provider=provider)
    retry_started = asyncio.Event()
    release_retry = asyncio.Event()

    async def controlled_sleep(_seconds):
        retry_started.set()
        await release_retry.wait()

    with patch("services.email_service.asyncio.sleep", side_effect=controlled_sleep):
        slow_task = asyncio.create_task(
            service.send_daily_digest("slow@example.com", "2026-07-22", [], None)
        )
        await retry_started.wait()
        fast_result = await asyncio.wait_for(
            service.send_daily_digest("fast@example.com", "2026-07-22", [], None),
            timeout=0.2,
        )
        release_retry.set()
        await slow_task

    assert fast_result["message_id"] == "msg-fast"
