#!/usr/bin/env python3
"""Detect service file changes for NEEDS_REVIEW + reject [NO-TEST-NEEDED] (Decision 4+5 / R3+R4).

Decision 4 (R4): backend/services/*.py changes MUST trigger NEEDS_REVIEW=true
Decision 5 (R3): [NO-TEST-NEEDED] self-attestation is FORBIDDEN (must use external check)

Exit codes:
- 0: diff is OK (may have needs_review=true)
- 1: diff REJECTED (e.g. self-attestation)

Outputs (for workflow `set-output`):
- needs_review: true/false
- service_files: comma-separated
- test_files: comma-separated
"""
from __future__ import annotations

import subprocess
import sys


SERVICE_PATH_PREFIX = "backend/services/"
NO_TEST_MARKER = "[NO-TEST-NEEDED]"


def get_changed_files() -> list[str]:
    """Get changed files from HEAD~1 (or empty list if not enough history)."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "--name-only"],
            capture_output=True, text=True, check=True,
        )
        return [f for f in result.stdout.splitlines() if f]
    except subprocess.CalledProcessError:
        return []


def get_commit_msg() -> str:
    """Get last commit message."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def check() -> dict:
    """Check the diff and return results."""
    changed = get_changed_files()
    commit_msg = get_commit_msg()

    # Decision 5 (R3): reject self-attestation
    if NO_TEST_MARKER in commit_msg:
        print(f"::error::{NO_TEST_MARKER} self-attestation not allowed (Decision 5 / R3)")
        print("External check via T33 + pytest is required, NOT commit message marker")
        sys.exit(1)

    service_files = [f for f in changed if f.startswith(SERVICE_PATH_PREFIX)]
    test_files = [f for f in changed if "test_" in f and f.endswith(".py")]

    needs_review = bool(service_files)

    return {
        "needs_review": needs_review,
        "service_files": service_files,
        "test_files": test_files,
        "all_changed": changed,
    }


def main() -> int:
    result = check()
    # GitHub Actions set-output format (legacy)
    print(f"needs_review={str(result['needs_review']).lower()}")
    print(f"service_files={','.join(result['service_files'])}")
    print(f"test_files={','.join(result['test_files'])}")
    if not result["test_files"]:
        print("::warning::no test_*.py files in diff — pytest will catch real failures (R3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())