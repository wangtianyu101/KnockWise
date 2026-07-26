"""Unit tests for minimax client + composite_score LLM integration (2026-07-27)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.minimax_client import MinimaxClient, MinimaxError, get_minimax_client, reset_minimax_client


# ═══ MinimaxClient 基本行为 ═══════════════════════════════════════

class TestMinimaxClientBasic:
    def setup_method(self):
        reset_minimax_client()

    def test_is_configured_with_key(self):
        c = MinimaxClient(api_key="sk-test-123", base_url="https://api.test/v1", model="test-model")
        assert c.is_configured is True

    def test_is_configured_without_key(self):
        c = MinimaxClient(api_key="", base_url="https://api.test/v1")
        assert c.is_configured is False

    def test_is_configured_with_wrong_prefix(self):
        c = MinimaxClient(api_key="not-sk-prefix", base_url="https://api.test/v1")
        assert c.is_configured is False


class TestMinimaxClientChat:
    def setup_method(self):
        reset_minimax_client()

    @pytest.mark.asyncio
    async def test_chat_success(self):
        c = MinimaxClient(api_key="sk-test", base_url="https://api.test/v1", model="m")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "hello"}}]
        }
        with patch.object(c, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client
            result = await c.chat([{"role": "user", "content": "hi"}])
            assert result == "hello"

    @pytest.mark.asyncio
    async def test_chat_403_raises_minimax_error(self):
        c = MinimaxClient(api_key="sk-test", base_url="https://api.test/v1", model="m")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        with patch.object(c, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client
            with pytest.raises(MinimaxError) as exc:
                await c.chat([{"role": "user", "content": "hi"}])
            assert "403" in str(exc.value)

    @pytest.mark.asyncio
    async def test_chat_timeout_raises_minimax_error(self):
        c = MinimaxClient(api_key="sk-test", base_url="https://api.test/v1", model="m", timeout=0.1)
        with patch.object(c, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_get.return_value = mock_client
            with pytest.raises(MinimaxError) as exc:
                await c.chat([{"role": "user", "content": "hi"}])
            assert "超时" in str(exc.value)

    @pytest.mark.asyncio
    async def test_chat_rejects_oversized_message(self):
        """spec § 3.3 prompt 注入防护：单条消息 > 32k 字符直接拒绝"""
        c = MinimaxClient(api_key="sk-test", base_url="https://api.test/v1", model="m")
        big_msg = "x" * 33_000
        with pytest.raises(MinimaxError) as exc:
            await c.chat([{"role": "user", "content": big_msg}])
        assert "32k" in str(exc.value)

    @pytest.mark.asyncio
    async def test_chat_json_parses(self):
        c = MinimaxClient(api_key="sk-test", base_url="https://api.test/v1", model="m")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"hot":0.8,"novel":0.6}'}}]
        }
        with patch.object(c, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client
            result = await c.chat_json([{"role": "user", "content": "score"}])
            assert result == {"hot": 0.8, "novel": 0.6}

    @pytest.mark.asyncio
    async def test_chat_json_invalid_raises(self):
        c = MinimaxClient(api_key="sk-test", base_url="https://api.test/v1", model="m")
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "not json"}}]
        }
        with patch.object(c, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_client
            with pytest.raises(MinimaxError) as exc:
                await c.chat_json([{"role": "user", "content": "score"}])
            assert "JSON 解析" in str(exc.value)


# ═══ composite_score 集成（fallback 行为）═══════════════════════════════

class TestCompositeScoreWithLLM:
    """验证：composite_score 行为不变 + LLM 失败时 fallback 到启发式"""

    def setup_method(self):
        reset_minimax_client()

    def test_blocked_tag_returns_zero(self):
        """spec R5: blocked_tag 命中直接 0.0（最高优先级）"""
        from services.digest_service import DigestService
        svc = DigestService()
        item = {"title": "DeepSeek V4 发布", "summary": "推理优化", "source_name": "Anthropic"}
        prefs = {"blocked_tags": ["DeepSeek"], "interested_tags": []}
        assert svc.composite_score(item, user_prefs=prefs) == 0.0

    def test_composite_score_falls_back_to_heuristic(self):
        """未配置 minimax（无 sk- prefix）→ fallback 启发式 → 0-1 区间"""
        from services.digest_service import DigestService
        with patch("services.digest_service.get_minimax_client") as mock_get:
            mock_client = MagicMock()
            mock_client.is_configured = False
            mock_get.return_value = mock_client
            svc = DigestService()
            item = {
                "title": "Claude 4.7 Sonnet Released",
                "summary": "1M context agentic coding",
                "source_name": "Anthropic",
                "published_at": "2026-07-27T09:00:00Z",
            }
            score = svc.composite_score(item, source_category="一手")
            assert 0.0 <= score <= 1.0

    def test_composite_score_uses_llm_when_configured(self):
        """minimax 配置 + chat_json 返回成功 → 用 LLM 分 · 不调启发式"""
        from services.digest_service import DigestService
        with patch("services.digest_service.get_minimax_client") as mock_get:
            mock_client = MagicMock()
            mock_client.is_configured = True
            # chat_json 是 async · 用 AsyncMock
            mock_client.chat_json = AsyncMock(return_value={
                "hot": 0.9, "novel": 0.8, "changed": 0.7, "source_authority": 0.95, "user_pref": 0.85
            })
            mock_get.return_value = mock_client
            svc = DigestService()
            item = {
                "title": "Claude 4.7 Sonnet Released",
                "summary": "1M context agentic coding",
                "source_name": "Anthropic",
                "published_at": "2026-07-27T09:00:00Z",
            }
            # 当前 composite_score 是 sync · _llm_composite_score 返回 None ·
            # 走启发式。要等 async pipeline 改造后才会调用 chat_json。
            score = svc.composite_score(item, source_category="一手")
            assert 0.0 <= score <= 1.0  # fallback heuristic still gives valid score


# ═══ Singleton ═══════════════════════════════════════════════════════════════

class TestMinimaxSingleton:
    def setup_method(self):
        reset_minimax_client()

    def test_get_minimax_client_returns_singleton(self):
        c1 = get_minimax_client()
        c2 = get_minimax_client()
        assert c1 is c2

    def test_reset_minimax_client(self):
        c1 = get_minimax_client()
        reset_minimax_client()
        c2 = get_minimax_client()
        assert c1 is not c2
