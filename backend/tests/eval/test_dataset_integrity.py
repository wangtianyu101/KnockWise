"""Integrity checks for the offline AI-eval JSONL dataset."""
from __future__ import annotations

import json
from pathlib import Path


DATASET = Path(__file__).parent / "datasets" / "interview_eval_v1.jsonl"


def _parse_cases() -> list[dict]:
    cases: list[dict] = []
    errors: list[str] = []
    for line_number, raw_line in enumerate(
        DATASET.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue
        try:
            cases.append(json.loads(raw_line))
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: {exc.msg} at column {exc.colno}")
    assert not errors, "invalid JSONL:\n" + "\n".join(errors)
    return cases


def test_all_eval_dataset_lines_are_valid_json():
    cases = _parse_cases()

    assert len(cases) == 107
    case_ids = [case["case_id"] for case in cases]
    assert len(case_ids) == len(set(case_ids))


def test_prompt_injection_expected_branch_is_null():
    cases = _parse_cases()

    injection_case = next(
        case for case in cases if case["case_id"] == "fmatch-017"
    )
    assert injection_case["expected"]["matched_branch_index"] is None
