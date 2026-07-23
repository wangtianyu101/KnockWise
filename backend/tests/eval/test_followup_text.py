"""P1-5 AI Eval: followup_text 15 cases"""
import pytest
from pathlib import Path
import json
from .runner import run_case


def test_followup_text_full_suite():
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    cases = [c for c in cases if c["agent"] == "followup_text"]
    assert len(cases) == 15
    for c in cases:
        r = run_case(c)
        # has_keyword metric > 0 means template matched expected keyword
        assert r.metrics.get("has_keyword") is True
