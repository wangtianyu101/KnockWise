"""minimax LLM client (OpenAI-compatible chat completions).

按用户偏好（2026-07-27）：所有 LLM 调用统一用 minimax · 不用 deepseek 或其他。

配置通过 core.config.settings:
  - llm_api_key:    minimax API key
  - llm_base_url:   https://api.minimax.chat/v1 (OpenAI-compatible)
  - llm_model:      MiniMax-Text-01 (default)

用法:
    from services.minimax_client import get_minimax_client, minimax_chat
    client = get_minimax_client()
    resp = await client.chat(messages=[{"role": "user", "content": "..."}])

设计要点:
- 懒加载 singleton · 避免每次调用重建 client
- 失败 fallback 抛 MinimaxError · caller 决定 fallback 到 mock
- 支持 prompt 注入防护：长度限制 + JSON mode
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class MinimaxError(Exception):
    """minimax API 调用失败（网络/超时/非 2xx/JSON 解析失败）"""


class MinimaxClient:
    """minimax 客户端 · OpenAI-compatible chat completions 协议"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        # 显式传 api_key（包括空字符串）就用传的；不传才 fallback 到 settings
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.base_url = (base_url if base_url is not None else settings.llm_base_url).rstrip("/")
        self.model = model if model is not None else settings.llm_model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) and (self.api_key or "").startswith("sk-")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        response_format: dict | None = None,
    ) -> str:
        """chat completion · 返回 content 字符串。

        Args:
            messages: [{"role": "user"/"system"/"assistant", "content": "..."}]
            temperature: 0-1 · 默认 0.3（低温度稳定）
            max_tokens: 最大输出 tokens
            response_format: e.g. {"type": "json_object"} 强制 JSON 输出
        """
        if not self.is_configured:
            raise MinimaxError("minimax 未配置（缺少 API key）")

        # spec § 3.3 prompt 注入防护：限制单条消息长度
        for m in messages:
            if isinstance(m.get("content"), str) and len(m["content"]) > 32_000:
                raise MinimaxError(f"单条消息超过 32k 字符限制（{len(m['content'])} chars）")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        client = await self._get_client()
        try:
            resp = await client.post("/chat/completions", json=payload)
        except httpx.TimeoutException as e:
            raise MinimaxError(f"minimax 超时（>{self.timeout}s）: {e}")
        except httpx.RequestError as e:
            raise MinimaxError(f"minimax 网络失败: {type(e).__name__}: {e}")

        if resp.status_code != 200:
            # spec § 3.8 失败恢复：失败不阻塞主流程
            logger.warning(f"minimax HTTP {resp.status_code}: {resp.text[:200]}")
            raise MinimaxError(f"minimax HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise MinimaxError(f"minimax 响应解析失败: {e}")

        return content

    async def chat_json(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> dict:
        """chat completion + 强制 JSON 解析。

        使用 response_format={"type": "json_object"} 强制 JSON 输出。
        返回 parsed dict · 解析失败抛 MinimaxError。
        """
        content = await self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"minimax JSON 解析失败: {content[:200]}")
            raise MinimaxError(f"minimax JSON 解析失败: {e}")

    def chat_sync(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        response_format: dict | None = None,
    ) -> str:
        """同步版 chat · 供 sync context（composite_score）调用。

        性能：~500ms-3s 一次 LLM call · batch 评分 N 条要 N * latency
        生产环境：应该 batch 评分（一次 prompt 评多条）· 本期先 1 条 1 次

        注：minimax 不支持 OpenAI 的 response_format=json_object（API 400）·
        改用 prompt 强 JSON 输出（system 指令 + 解析 fallback）
        """
        if not self.is_configured:
            raise MinimaxError("minimax 未配置（缺少 API key）")
        for m in messages:
            if isinstance(m.get("content"), str) and len(m["content"]) > 32_000:
                raise MinimaxError(f"单条消息超过 32k 字符限制（{len(m['content'])} chars）")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        # 注：minimax 不支持 OpenAI response_format 参数 · 强 JSON 走 prompt
        # if response_format:
        #     payload["response_format"] = response_format

        with httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        ) as client:
            try:
                resp = client.post("/chat/completions", json=payload)
            except httpx.TimeoutException as e:
                raise MinimaxError(f"minimax 超时（>{self.timeout}s）: {e}")
            except httpx.RequestError as e:
                raise MinimaxError(f"minimax 网络失败: {type(e).__name__}: {e}")

            if resp.status_code != 200:
                logger.warning(f"minimax HTTP {resp.status_code}: {resp.text[:200]}")
                raise MinimaxError(f"minimax HTTP {resp.status_code}: {resp.text[:200]}")

            try:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise MinimaxError(f"minimax 响应解析失败: {e}")

    def chat_json_sync(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 200,
    ) -> dict:
        """同步 chat + JSON 解析（minimax 不支持 response_format · 强 prompt JSON）。

        解析策略：
        1. 直接 json.loads
        2. 失败时尝试提取 markdown ```json 块
        3. 失败时尝试提取第一个 {...} 子串
        """
        content = self.chat_sync(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = content.strip()
        # 1. 直接 parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        # 2. markdown ```json ... ``` 块
        import re
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # 3. 第一个 {...} 子串
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError as e:
                pass
        logger.warning(f"minimax JSON 解析失败 · content[:200]: {content[:200]}")
        raise MinimaxError(f"minimax JSON 解析失败: 无法从响应提取 JSON")


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_client: MinimaxClient | None = None


def get_minimax_client() -> MinimaxClient:
    """获取 minimax singleton client（懒加载）"""
    global _client
    if _client is None:
        _client = MinimaxClient()
    return _client


def reset_minimax_client() -> None:
    """测试用：重置 singleton（让测试注入 mock config）"""
    global _client
    _client = None
