"""Regression tests for the JSON coverage threshold gate."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "check_coverage.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_coverage", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return _load_checker()


def make_report(*, global_lines=61.4, file_lines=85.5, file_branches=82.0):
    return {
        "totals": {"percent_statements_covered": global_lines},
        "files": {
            "services/digest_service.py": {
                "summary": {
                    "percent_statements_covered": file_lines,
                    "percent_branches_covered": file_branches,
                }
            }
        },
    }


def test_accepts_current_global_and_digest_baselines(checker):
    errors = checker.evaluate_coverage(
        make_report(),
        global_lines=61.0,
        file_path="services/digest_service.py",
        file_lines=80.0,
        file_branches=70.0,
    )

    assert errors == []


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"global_lines": 60.9}, "global line coverage"),
        ({"file_lines": 79.9}, "services/digest_service.py line coverage"),
        ({"file_branches": 69.9}, "services/digest_service.py branch coverage"),
    ],
)
def test_rejects_each_threshold_regression(checker, overrides, expected):
    errors = checker.evaluate_coverage(
        make_report(**overrides),
        global_lines=61.0,
        file_path="services/digest_service.py",
        file_lines=80.0,
        file_branches=70.0,
    )

    assert len(errors) == 1
    assert expected in errors[0]


def test_rejects_missing_digest_file(checker):
    report = make_report()
    report["files"] = {}

    errors = checker.evaluate_coverage(
        report,
        global_lines=61.0,
        file_path="services/digest_service.py",
        file_lines=80.0,
        file_branches=70.0,
    )

    assert errors == ["coverage report is missing services/digest_service.py"]


def test_cli_returns_zero_for_baseline_and_one_for_regression(tmp_path):
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(make_report()), encoding="utf-8")
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        str(report_path),
        "--global-lines",
        "61",
        "--file",
        "services/digest_service.py",
        "--file-lines",
        "80",
        "--file-branches",
        "70",
    ]

    passed = subprocess.run(command, capture_output=True, text=True, check=False)
    report_path.write_text(
        json.dumps(make_report(global_lines=60.0)),
        encoding="utf-8",
    )
    failed = subprocess.run(command, capture_output=True, text=True, check=False)

    assert passed.returncode == 0
    assert "coverage gate passed" in passed.stdout
    assert failed.returncode == 1
    assert "global line coverage" in failed.stdout
