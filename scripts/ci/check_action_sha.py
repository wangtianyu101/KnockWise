#!/usr/bin/env python3
"""Reject moving tags (@beta, @main, @v1) in workflow YAMLs (Decision 7 / R8).

Decision 7 / R8 require pinning third-party Actions to full 40-character SHA.
This script scans all .github/workflows/*.yml and exits 1 if any uses:
- Uses a moving tag (beta/main/v1/latest/etc.)
- Uses a non-40-char SHA

Usage:
    python check_action_sha.py
    python check_action_sha.py --workflows-dir .github/workflows
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml


MOVING_TAGS = {
    "beta", "main", "master", "v1", "v2", "v3", "v4", "v5",
    "latest", "next", "edge", "stable", "nightly",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _walk(obj, path: str, violations: list) -> None:
    """Recursively find `uses:` entries in workflow YAML."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if k == "uses" and isinstance(v, str):
                ref = v.split("@")[-1] if "@" in v else ""
                is_local = v.startswith("./")
                if not is_local and (ref in MOVING_TAGS or not SHA_PATTERN.match(ref)):
                    violations.append((new_path, v))
            _walk(v, new_path, violations)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _walk(item, f"{path}[{i}]", violations)


def check_workflow(workflow_path: Path) -> list[tuple[str, str]]:
    """Check a single workflow YAML for moving tags."""
    try:
        with open(workflow_path) as f:
            wf = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [(workflow_path.name, f"YAML parse error: {e}")]
    if not wf:
        return []
    violations: list[tuple[str, str]] = []
    _walk(wf, "", violations)
    return [(workflow_path.name, path, v) for path, v in violations]


def check_workflows(workflows_dir: Path) -> list[tuple]:
    """Check all workflows in the directory."""
    all_violations = []
    for wf in sorted(workflows_dir.glob("*.yml")):
        all_violations.extend(check_workflow(wf))
    # Also check .yaml files
    for wf in sorted(workflows_dir.glob("*.yaml")):
        all_violations.extend(check_workflow(wf))
    return all_violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Reject moving tags in workflow Actions")
    parser.add_argument("--workflows-dir", default=".github/workflows", help="Path to workflows directory")
    args = parser.parse_args()

    workflows_dir = Path(args.workflows_dir)
    if not workflows_dir.exists():
        print(f"Workflows directory not found: {workflows_dir}")
        return 1

    violations = check_workflows(workflows_dir)
    if violations:
        print(f"❌ {len(violations)} moving tag / invalid SHA found:")
        for entry in violations:
            if len(entry) == 3:
                file, path, uses = entry
                print(f"  - {file} :: {path} = {uses}")
            else:
                file, err = entry
                print(f"  - {file} :: {err}")
        print("\nDecision 7 / R8: third-party Actions MUST pin to full 40-character SHA")
        print("Fix: replace @beta/@main/@v1 with @<40-char-sha>")
        return 1
    print("✅ All third-party Actions pinned to full SHA")
    return 0


if __name__ == "__main__":
    sys.exit(main())