#!/usr/bin/env python3
"""Reject moving tags and optionally verify Action commit provenance.

Decision 7 / R8 require pinning third-party Actions to full 40-character SHA.
This script scans all .github/workflows/*.yml and exits 1 if any uses:
- Uses a moving tag (beta/main/v1/latest/etc.)
- Uses a non-40-char SHA
- Uses a SHA that does not exist in the referenced owner/repository

Usage:
    python check_action_sha.py
    python check_action_sha.py --workflows-dir .github/workflows
    python check_action_sha.py --verify-remote
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


MOVING_TAGS = {
    "beta", "main", "master", "v1", "v2", "v3", "v4", "v5",
    "latest", "next", "edge", "stable", "nightly",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ACTION_SLUG_PATTERN = re.compile(
    r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})$"
)
MAX_API_RESPONSE_BYTES = 256 * 1024


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


def _collect_action_refs(obj, path: str, refs: list[tuple[str, str]]) -> None:
    """Collect non-local `uses:` entries with their YAML path."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            if (
                key == "uses"
                and isinstance(value, str)
                and not value.startswith("./")
            ):
                refs.append((new_path, value))
            _collect_action_refs(value, new_path, refs)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            _collect_action_refs(item, f"{path}[{index}]", refs)


def collect_workflow_action_refs(workflow_path: Path) -> list[tuple[str, str, str]]:
    """Return (filename, YAML path, owner/repo@sha) entries."""
    try:
        with open(workflow_path, encoding="utf-8") as workflow_file:
            workflow = yaml.safe_load(workflow_file)
    except yaml.YAMLError:
        return []
    if not workflow:
        return []
    refs: list[tuple[str, str]] = []
    _collect_action_refs(workflow, "", refs)
    return [(workflow_path.name, path, uses) for path, uses in refs]


def collect_action_refs(workflows_dir: Path) -> list[tuple[str, str, str]]:
    """Collect Action refs from .yml and .yaml workflows."""
    refs: list[tuple[str, str, str]] = []
    for pattern in ("*.yml", "*.yaml"):
        for workflow_path in sorted(workflows_dir.glob(pattern)):
            refs.extend(collect_workflow_action_refs(workflow_path))
    return refs


def verify_action_ref(
    uses: str,
    *,
    api_base: str,
    token: str | None,
    timeout: float,
) -> str | None:
    """Return a fail-closed reason, or None when repo + commit are proven."""
    match = ACTION_SLUG_PATTERN.fullmatch(uses)
    if not match:
        return "invalid owner/repo@40-character-sha"

    owner = match.group("owner")
    repo = match.group("repo")
    expected_sha = match.group("sha")
    url = (
        f"{api_base.rstrip('/')}/repos/{owner}/{repo}"
        f"/git/commits/{expected_sha}"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "KnockWise-action-provenance-checker",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_API_RESPONSE_BYTES + 1)
    except HTTPError as error:
        if error.code == 404:
            return "commit not found in referenced repository"
        return f"BLOCKED: GitHub API returned HTTP {error.code}"
    except (URLError, TimeoutError, OSError) as error:
        return f"BLOCKED: provenance API unavailable ({type(error).__name__})"

    if len(body) > MAX_API_RESPONSE_BYTES:
        return "BLOCKED: provenance API response exceeds size limit"
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "BLOCKED: provenance API returned invalid JSON"
    observed_sha = payload.get("sha") if isinstance(payload, dict) else None
    if observed_sha != expected_sha:
        return f"commit SHA mismatch (observed {observed_sha!r})"
    return None


def check_remote_provenance(
    workflows_dir: Path,
    *,
    api_base: str,
    token: str | None,
    timeout: float,
) -> list[tuple[str, str, str, str]]:
    """Verify each distinct owner/repo@sha; cache key includes the repository."""
    violations: list[tuple[str, str, str, str]] = []
    cache: dict[str, str | None] = {}
    for filename, path, uses in collect_action_refs(workflows_dir):
        if uses not in cache:
            cache[uses] = verify_action_ref(
                uses,
                api_base=api_base,
                token=token,
                timeout=timeout,
            )
        reason = cache[uses]
        if reason:
            violations.append((filename, path, uses, reason))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reject moving tags and verify workflow Action provenance"
    )
    parser.add_argument("--workflows-dir", default=".github/workflows", help="Path to workflows directory")
    parser.add_argument(
        "--verify-remote",
        action="store_true",
        help="Fail closed unless every owner/repo@sha exists in that repository",
    )
    parser.add_argument(
        "--api-base",
        default="https://api.github.com",
        help="GitHub API base URL (overridable for deterministic tests)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-request provenance timeout in seconds",
    )
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
    if args.verify_remote:
        provenance_violations = check_remote_provenance(
            workflows_dir,
            api_base=args.api_base,
            token=os.environ.get("GITHUB_TOKEN"),
            timeout=args.timeout,
        )
        if provenance_violations:
            print(
                f"❌ {len(provenance_violations)} Action provenance "
                "violation(s) found:"
            )
            for file, path, uses, reason in provenance_violations:
                print(f"  - {file} :: {path} = {uses} :: {reason}")
            return 1
        print("✅ All third-party Action provenance verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
