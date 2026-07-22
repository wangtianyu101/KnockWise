#!/usr/bin/env python3
"""Enforce global and file-specific thresholds from coverage.py JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


def evaluate_coverage(
    report: dict[str, Any],
    *,
    global_lines: float,
    file_path: str,
    file_lines: float,
    file_branches: float,
) -> list[str]:
    errors: list[str] = []
    totals = report.get("totals", {})
    actual_global = float(totals.get("percent_statements_covered", 0.0))
    if actual_global < global_lines:
        errors.append(
            f"global line coverage {actual_global:.2f}% is below {global_lines:.2f}%"
        )

    file_report = report.get("files", {}).get(file_path)
    if file_report is None:
        errors.append(f"coverage report is missing {file_path}")
        return errors

    summary = file_report.get("summary", {})
    actual_lines = float(summary.get("percent_statements_covered", 0.0))
    actual_branches = float(summary.get("percent_branches_covered", 0.0))
    if actual_lines < file_lines:
        errors.append(
            f"{file_path} line coverage {actual_lines:.2f}% is below {file_lines:.2f}%"
        )
    if actual_branches < file_branches:
        errors.append(
            f"{file_path} branch coverage {actual_branches:.2f}% is below "
            f"{file_branches:.2f}%"
        )
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enforce coverage JSON thresholds.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--global-lines", type=float, required=True)
    parser.add_argument("--file", dest="file_path", required=True)
    parser.add_argument("--file-lines", type=float, required=True)
    parser.add_argument("--file-branches", type=float, required=True)
    args = parser.parse_args(argv)

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"cannot read coverage report: {error}")

    errors = evaluate_coverage(
        report,
        global_lines=args.global_lines,
        file_path=args.file_path,
        file_lines=args.file_lines,
        file_branches=args.file_branches,
    )
    if errors:
        for error in errors:
            print(f"coverage-error: {error}")
        return 1

    totals = report["totals"]
    summary = report["files"][args.file_path]["summary"]
    print(
        "coverage gate passed: "
        f"global lines={totals['percent_statements_covered']:.2f}%, "
        f"{args.file_path} lines={summary['percent_statements_covered']:.2f}%, "
        f"branches={summary['percent_branches_covered']:.2f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
