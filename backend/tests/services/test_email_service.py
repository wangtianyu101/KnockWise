"""Tests for EmailService (T15)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.email_service import EmailService


class TestSendDailyDigest:
    @pytest.mark.asyncio
    async def test_returns_message_id_on_success(self):
        """成功发送 → 返回 message_id + sent_at + no error。"""
        provider = AsyncMock()
        provider.send.return_value = "msg-123"
        svc = EmailService(provider=provider)
        items = [{
            "title": "Claude 4.7", "summary": "s", "type": "model",
            "region": "overseas", "source_name": "Anthropic",
            "source_url": "https://x", "estimated_minutes": 3,
        }]
        result = await svc.send_daily_digest(
            "u@x.com", "2026-07-17", items, vibe="今日 5 条"
        )

        assert result["message_id"] == "msg-123"
        assert result["sent_at"] is not None
        assert result["error"] is None
        args = provider.send.await_args
        assert args.args[1] == "KnockWise · 今日 5 条 AI 推送"
        assert "/ai/today?date=2026-07-17" in args.args[2]
        assert args.kwargs["idempotency_key"].startswith("digest-")

    @pytest.mark.asyncio
    async def test_retries_3_times_then_fails(self):
        """Initial attempt plus 3 retries → terminal error."""
        provider = AsyncMock()
        provider.send.side_effect = Exception("5xx")
        svc = EmailService(provider=provider)
        with patch("services.email_service.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await svc.send_daily_digest("u@x.com", "2026-07-17", [], vibe="x")

        assert result["message_id"] is None
        assert result["error"] == "max retries exceeded"
        assert provider.send.await_count == 4
        assert [call.args[0] for call in sleep.await_args_list] == [300, 900, 3600]

    @pytest.mark.asyncio
    async def test_no_email_returns_error(self):
        """user_email=None → 返回 error='no user email'。"""
        svc = EmailService()
        result = await svc.send_daily_digest(None, "2026-07-17", [])
        assert result["error"] == "no user email"

    @pytest.mark.asyncio
    async def test_succeeds_on_third_attempt(self):
        """前 2 次失败 · 第 3 次成功 → 返回 message_id（spec § 7.2 重试逻辑）。"""
        provider = AsyncMock()
        provider.send.side_effect = [Exception("5xx"), Exception("5xx"), "msg-ok"]
        svc = EmailService(provider=provider)

        with patch("services.email_service.asyncio.sleep", new_callable=AsyncMock):
            result = await svc.send_daily_digest("u@x.com", "2026-07-17", [])

        assert result["message_id"] == "msg-ok"
        assert provider.send.await_count == 3
