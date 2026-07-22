"""Contract boundary between the digest pipeline and the configured LLM."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class DigestLLMService:
    """Generate bounded, structured summaries without leaking application data."""

    MAX_CANDIDATES = 20
    MAX_TITLE_CHARS = 300
    MAX_SUMMARY_CHARS = 2_000
    MAX_OUTPUT_SUMMARY_CHARS = 600
    TIMEOUT_SECONDS = 20

    def __init__(self, llm: Any | None = None) -> None:
        self._llm = llm

    def _get_llm(self) -> Any:
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            from core.config import settings

            self._llm = ChatOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                temperature=0,
            )
        return self._llm

    async def enrich_items(
        self,
        items: list[dict[str, Any]],
        user_prefs: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Return LLM summaries, or the original summaries on any contract error."""
        result = [dict(item) for item in items]
        if not result:
            return result

        prompt_payload = {
            "preferences": self._safe_preferences(user_prefs or {}),
            "candidates": [
                {
                    "index": index,
                    "title": str(item.get("title") or "")[: self.MAX_TITLE_CHARS],
                    "summary": str(item.get("summary") or "")[: self.MAX_SUMMARY_CHARS],
                    "url": str(item.get("url") or item.get("source_url") or "")[:2_000],
                    "source_name": str(item.get("source_name") or "")[:200],
                }
                for index, item in enumerate(result[: self.MAX_CANDIDATES])
            ],
        }
        messages = [
            SystemMessage(
                content=(
                    "Summarize only the supplied candidates. Return strict JSON as "
                    '{"items":[{"index":0,"summary":"..."}]}. Do not add facts.'
                )
            ),
            HumanMessage(content=json.dumps(prompt_payload, ensure_ascii=False)),
        ]

        try:
            response = await asyncio.wait_for(
                self._get_llm().ainvoke(messages),
                timeout=self.TIMEOUT_SECONDS,
            )
            updates = self._parse_response(getattr(response, "content", ""))
            for index, summary in updates.items():
                result[index]["summary"] = summary
                result[index]["llm_fallback"] = False
            return result
        except Exception as exc:
            logger.warning("digest LLM fallback: %s", type(exc).__name__)
            for item in result:
                item["llm_fallback"] = True
            return result

    def _safe_preferences(self, preferences: dict[str, Any]) -> dict[str, list[str]]:
        safe: dict[str, list[str]] = {}
        for key in ("interested_tags", "blocked_tags"):
            value = preferences.get(key, [])
            if not isinstance(value, list):
                value = []
            safe[key] = [str(tag)[:100] for tag in value[:50]]
        return safe

    def _parse_response(self, content: Any) -> dict[int, str]:
        if not isinstance(content, str):
            raise ValueError("LLM content must be text")
        normalized = content.strip()
        if normalized.startswith("```"):
            lines = normalized.splitlines()
            if lines and lines[-1].strip() == "```":
                normalized = "\n".join(lines[1:-1])
        payload = json.loads(normalized)
        raw_items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(raw_items, list):
            raise ValueError("LLM output must contain an items list")

        updates: dict[int, str] = {}
        for item in raw_items:
            if not isinstance(item, dict):
                raise ValueError("LLM item must be an object")
            index = item.get("index")
            summary = item.get("summary")
            if (
                not isinstance(index, int)
                or isinstance(index, bool)
                or index < 0
                or index >= self.MAX_CANDIDATES
                or not isinstance(summary, str)
                or not summary.strip()
            ):
                raise ValueError("LLM item has an invalid index or summary")
            updates[index] = summary.strip()[: self.MAX_OUTPUT_SUMMARY_CHARS]
        return updates


digest_llm_service = DigestLLMService()
