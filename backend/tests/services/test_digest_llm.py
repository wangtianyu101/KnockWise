"""Digest LLM contract tests: input scope, structured output and fallback."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.digest_llm_service import DigestLLMService


def candidate(**overrides):
    data = {
        "title": "Agent framework release",
        "summary": "Original source summary",
        "url": "https://example.com/release",
        "source_name": "Example",
        "secret_internal": "must-not-enter-prompt",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_prompt_contains_preferences_and_allowed_candidate_fields_only():
    llm = AsyncMock()
    llm.ainvoke.return_value = SimpleNamespace(
        content='{"items":[{"index":0,"summary":"结构化摘要"}]}'
    )
    service = DigestLLMService(llm=llm)

    result = await service.enrich_items(
        [candidate()],
        {"interested_tags": ["Agent"], "blocked_tags": ["crypto"], "email": "private@example.com"},
    )

    prompt = llm.ainvoke.await_args.args[0][1].content
    assert "Agent" in prompt
    assert "crypto" in prompt
    assert "Agent framework release" in prompt
    assert "must-not-enter-prompt" not in prompt
    assert "private@example.com" not in prompt
    assert result[0]["summary"] == "结构化摘要"


@pytest.mark.asyncio
async def test_invalid_json_falls_back_to_original_summary():
    llm = AsyncMock()
    llm.ainvoke.return_value = SimpleNamespace(content="not-json")
    service = DigestLLMService(llm=llm)

    result = await service.enrich_items([candidate()], {})

    assert result[0]["summary"] == "Original source summary"
    assert result[0]["llm_fallback"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [TimeoutError("timeout"), RuntimeError("rate limited"), ValueError("model failed")],
)
async def test_model_errors_fall_back_without_escaping(error):
    llm = AsyncMock()
    llm.ainvoke.side_effect = error
    service = DigestLLMService(llm=llm)

    result = await service.enrich_items([candidate()], {})

    assert result[0]["summary"] == "Original source summary"
    assert result[0]["llm_fallback"] is True


@pytest.mark.asyncio
async def test_input_is_bounded_before_prompting():
    llm = AsyncMock()
    llm.ainvoke.return_value = SimpleNamespace(content='{"items":[]}')
    service = DigestLLMService(llm=llm)
    items = [candidate(title=f"item-{index}-" + "x" * 500) for index in range(30)]

    await service.enrich_items(items, {})

    prompt = llm.ainvoke.await_args.args[0][1].content
    assert "item-19" in prompt
    assert "item-20" not in prompt
    assert "x" * 301 not in prompt

