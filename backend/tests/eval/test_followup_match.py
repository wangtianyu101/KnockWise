"""P1-5 AI Eval: followup_match 20 cases"""
import pytest
from pathlib import Path
import json
from .runner import run_case


def test_followup_match_full_suite():
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    cases = [c for c in cases if c["agent"] == "followup_match"]
    assert len(cases) == 20
    for c in cases:
        r = run_case(c)
        assert r.metrics.get("json_parse_ok") is True


def test_followup_match_injection_blocked():
    """S-7 variant: 注入用例必须返回 matched_branch_index != expected"""
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    injection = [c for c in cases if c["agent"] == "followup_match" and "prompt_injection" in c.get("tags", [])]
    assert len(injection) >= 1
    for c in injection:
        r = run_case(c)
        # mock returns matched_branch_index=-1 for injection
        assert r.metrics.get("matched") is False
