#!/usr/bin/env python3
"""Inspect the staged auto-fix patch and enforce diff policy.

Decision 4 (R4): backend/services/*.py changes MUST trigger NEEDS_REVIEW=true
Decision 5 (R3): [NO-TEST-NEEDED] self-attestation is FORBIDDEN (must use external check)
P0 AF-03: inspect the current Git index, never a previous commit diff; reject
the patch transport file if it is staged.

Exit codes:
- 0: diff is OK (may have needs_review=true)
- 1: diff REJECTED (e.g. self-attestation)

Stdout:
- needs_review: true/false
- service_files: comma-separated
- test_files: comma-separated

When ``GITHUB_OUTPUT`` is set, only the safe boolean ``needs_review`` is
persisted for later workflow steps.
"""
from __future__ import annotations

import os
import subprocess
import sys


SERVICE_PATH_PREFIX = "backend/services/"
NO_TEST_MARKER = "[NO-TEST-NEEDED]"
FORBIDDEN_STAGED_FILES = {"patch.diff"}


def get_changed_files() -> list[str]:
    """Get files in the current staged patch."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
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

    forbidden = sorted(FORBIDDEN_STAGED_FILES.intersection(changed))
    if forbidden:
        print(
            "::error::auto-fix transport files must not be staged: "
            + ",".join(forbidden)
        )
        sys.exit(1)

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
    needs_review = str(result["needs_review"]).lower()
    print(f"needs_review={needs_review}")
    print(f"service_files={','.join(result['service_files'])}")
    print(f"test_files={','.join(result['test_files'])}")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        # Only persist the boolean consumed after commit. File names remain
        # stdout-only because Git paths may contain workflow-command delimiters.
        with open(github_output, "a", encoding="utf-8") as output:
            output.write(f"needs_review={needs_review}\n")
    if not result["test_files"]:
        print("::warning::no test_*.py files in diff — pytest will catch real failures (R3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
