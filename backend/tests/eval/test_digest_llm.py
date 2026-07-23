"""P1-5 AI Eval: digest_llm 12 cases"""
import pytest
from pathlib import Path
import json
from .runner import run_case


def test_digest_llm_full_suite():
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    cases = [c for c in cases if c["agent"] == "digest_llm"]
    assert len(cases) == 12
    for c in cases:
        r = run_case(c)
        assert r.metrics.get("json_parse_ok") is True


def test_digest_llm_schema_complete():
    cases = [json.loads(l) for l in (Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl").read_text().splitlines() if l.strip()]
    for c in cases:
        if c["agent"] != "digest_llm":
            continue
        r = run_case(c)
        if r.metrics.get("json_parse_ok"):
            import json as _json
            data = _json.loads(r.raw_response)
            for f in c.get("invariants", {}).get("schema_required_fields", []):
                assert f in data, f"missing field {f} in {c['case_id']}"
