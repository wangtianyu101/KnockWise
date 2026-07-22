#!/usr/bin/env python3
"""Sanitize CI log before passing to Claude (Decision 10 / R9).

Decision 10 / R9 require:
- ONLY pass failed_job_name (allowlist), error_code (allowlist), truncated key strings (<=200 chars)
- NEVER pass raw CI logs, PR titles, or commit messages to Claude (prompt injection prevention)

Usage:
    python sanitize_ci_log.py < log.txt
    cat log.txt | python sanitize_ci_log.py
    python sanitize_ci_log.py --log-file path/to/log.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Iterable


# Allowlist of CI jobs (whitelist pattern: only extract known job names)
JOB_PATTERNS = [
    r"##\[error\]([a-zA-Z][\w-]+)",  # GitHub Actions step failure (allow hyphens)
    r"Job\s+'([^']+)'\s+failed",  # Generic
]

# Allowlist of error codes (only known structured errors)
ERROR_CODE_PATTERNS = [
    r"\b(TypeScriptError|TypeError|SyntaxError|ImportError|PropertyDoesNotExist)\b",
    r"\b(CoverageBelowThreshold|CoverageThresholdFailure)\b",
    r"\b(PlaceholderViolation|TestQualityViolation)\b",
    r"\b(PytestFailure|TestFailure|AssertionError)\b",
    r"Property\s+(?:\S+\s+)?does\s+not\s+exist",  # TS: "Property 'X' does not exist" -> "PropertyDoesNotExist"
]

MAX_KEY_STRING_LEN = 200
UNKNOWN = "unknown"


def _first_match(patterns: Iterable[str], text: str, default: str = UNKNOWN) -> str:
    """Return the first match across patterns, or default.

    For patterns WITHOUT capture groups, normalize to a canonical name.
    For patterns WITH capture groups, return group(1).
    """
    # Normalization: when a pattern has no capture group, map the match to a canonical name
    NORMALIZE_MAP = {
        r"Property\s+(?:\S+\s+)?does\s+not\s+exist": "PropertyDoesNotExist",
    }
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            if m.groups():
                return m.group(1)
            # No capture group → use canonical name if mapped, else the raw match
            return NORMALIZE_MAP.get(pat, m.group(0))
    return default


def sanitize(raw_log: str) -> dict:
    """Sanitize raw CI log into a structured summary.

    Returns dict with ONLY allowlisted fields. NEVER includes raw_log,
    pr_title, or commit_msg (those would be prompt injection vectors).
    """
    if not raw_log:
        raw_log = ""

    failed_job = _first_match(JOB_PATTERNS, raw_log, UNKNOWN)
    error_code = _first_match(ERROR_CODE_PATTERNS, raw_log, "UnknownError")
    # Truncate to first MAX_KEY_STRING_LEN chars (prevents massive payloads)
    key_string = raw_log[:MAX_KEY_STRING_LEN]

    return {
        "failed_job": failed_job,
        "error_code": error_code,
        "key_string": key_string,
        "key_string_truncated": len(raw_log) > MAX_KEY_STRING_LEN,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize CI log for Claude")
    parser.add_argument("--log-file", help="Path to log file (default: stdin)")
    args = parser.parse_args()

    if args.log_file:
        with open(args.log_file) as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    result = sanitize(raw)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())