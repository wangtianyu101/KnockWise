"""LLM mock tests (T22) - DeepSeek API mock + prompt content validation."""
from __future__ import annotations

import pytest


class TestSelectTopNPrompt:
    def test_prompt_contains_user_prefs(self): pass
    def test_prompt_contains_sources(self): pass


class TestSummaryPrompt:
    def test_summary_prompt_filters_scope(self): pass
    def test_summary_length_constraint(self): pass
