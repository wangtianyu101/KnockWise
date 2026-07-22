"""Email provider boundary contract tests."""
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
