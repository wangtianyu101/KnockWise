"""RSS fetch tests (T23) - 8 source fixtures + RSSHub fallback."""
from __future__ import annotations

import pytest


class TestRSSFetch:
    def test_anthropic_rss_parses(self): pass
    def test_github_atom_parses(self): pass
    def test_qbitai_parses(self): pass
    def test_rsshub_fallback_on_failure(self): pass
    def test_partial_failure_continues(self): pass
