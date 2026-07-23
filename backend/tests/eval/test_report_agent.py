"""P1-5 AI Eval: report_agent 10 cases"""
import pytest
from pathlib import Path
import json
from .runner import run_case, run_suite


def test_report_agent_full_suite():
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    cases = [c for c in cases if c["agent"] == "report_agent"]
    assert len(cases) == 10
    for c in cases:
        r = run_case(c)
        assert r.metrics.get("json_parse_ok") is True


def test_report_agent_score_in_range():
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    for c in cases:
        if c["agent"] != "report_agent":
            continue
        r = run_case(c)
        assert 1.0 <= r.metrics["score"] <= 5.0
