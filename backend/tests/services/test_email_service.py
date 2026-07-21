"""Tests for EmailService (T15)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.email_service import EmailService


class TestSendDailyDigest:
    @pytest.mark.asyncio
    async def test_returns_message_id_on_success(self):
        """成功发送 → 返回 message_id + sent_at + no error。"""
        svc = EmailService()
        items = [{
            "title": "Claude 4.7", "summary": "s", "type": "model",
            "region": "overseas", "source_name": "Anthropic",
            "source_url": "https://x", "estimated_minutes": 3,
        }]
        with patch.object(svc, "_send_via_resend", AsyncMock(return_value="msg-123")):
            result = await svc.send_daily_digest("u@x.com", "2026-07-17", items, vibe="今日 5 条")

        assert result["message_id"] == "msg-123"
        assert result["sent_at"] is not None
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_retries_3_times_then_fails(self):
        """3 次都失败 → 返回 error='max retries exceeded'。"""
        svc = EmailService()
        with patch.object(svc, "_send_via_resend", AsyncMock(side_effect=Exception("5xx"))), \
             patch("asyncio.sleep", AsyncMock()):
            result = await svc.send_daily_digest("u@x.com", "2026-07-17", [], vibe="x")

        assert result["message_id"] is None
        assert result["error"] == "max retries exceeded"

    @pytest.mark.asyncio
    async def test_no_email_returns_error(self):
        """user_email=None → 返回 error='no user email'。"""
        svc = EmailService()
        result = await svc.send_daily_digest(None, "2026-07-17", [])
        assert result["error"] == "no user email"

    @pytest.mark.asyncio
    async def test_succeeds_on_third_attempt(self):
        """前 2 次失败 · 第 3 次成功 → 返回 message_id（spec § 7.2 重试逻辑）。"""
        svc = EmailService()
        call_count = {"n": 0}

        async def flaky(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise Exception("5xx")
            return "msg-ok"

        with patch.object(svc, "_send_via_resend", side_effect=flaky), \
             patch("asyncio.sleep", AsyncMock()):
            result = await svc.send_daily_digest("u@x.com", "2026-07-17", [])

        assert result["message_id"] == "msg-ok"
        assert call_count["n"] == 3
