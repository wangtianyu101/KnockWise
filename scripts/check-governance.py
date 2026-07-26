#!/usr/bin/env python3
"""Validate changed workflow artifacts in CI.

This is the CI counterpart of scripts/pre-commit. It reads a Git diff,
requires task.yaml for newly added task directories, and runs the same
repository checkers against the checked-out commit.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DOC_STEPS = {
    "research.md": "research",
    "spec.md": "spec",
    "plan.md": "plan",
    "tasks.md": "tasks",
    "test-cases.md": "implement",
    "verify.md": "verify",
    "retro.md": "retro",
}
ZERO_SHA = "0" * 40


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def commit_exists(ref: str) -> bool:
    if not ref or ref == ZERO_SHA:
        return False
    result = git("cat-file", "-e", f"{ref}^{{commit}}", check=False)
    return result.returncode == 0


def resolve_base(requested: str | None) -> str:
    if requested and commit_exists(requested):
        return requested

    default_branch = os.environ.get("GITHUB_DEFAULT_BRANCH", "main")
    remote_ref = f"origin/{default_branch}"
    if commit_exists(remote_ref):
        merged = git("merge-base", "HEAD", remote_ref, check=False)
        if merged.returncode == 0 and merged.stdout.strip():
            return merged.stdout.strip()

    if commit_exists("HEAD^"):
        return "HEAD^"

    empty_tree = git("hash-object", "-t", "tree", "/dev/null")
    return empty_tree.stdout.strip()


def changed_paths(base: str, head: str, diff_filter: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "-z",
            f"--diff-filter={diff_filter}",
            base,
            head,
        ],
        capture_output=True,
        check=True,
    )
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    ]


def task_root(path: str) -> str | None:
    parts = Path(path).parts
    if len(parts) < 4 or parts[0:2] != ("docs", "tasks"):
        return None
    return str(Path(*parts[:3]))


def task_root_exists_at(ref: str, root: str) -> bool:
    result = git("ls-tree", "-r", "--name-only", ref, "--", root, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def path_exists_at(ref: str, path: str) -> bool:
    result = git("cat-file", "-e", f"{ref}:{path}", check=False)
    return result.returncode == 0


def run_checker(args: list[str]) -> bool:
    result = subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode == 0


def validate(base: str, head: str = "HEAD") -> list[str]:
    errors: list[str] = []
    changed = changed_paths(base, head, "ACMRD")
    candidate_added_roots = {
        root for path in changed if (root := task_root(path))
    }
    added_roots = {
        root
        for root in candidate_added_roots
        if not task_root_exists_at(base, root) and task_root_exists_at(head, root)
    }

    for root in sorted(added_roots):
        manifest = Path(root) / "task.yaml"
        if not manifest.is_file():
            errors.append(f"new task directory requires {manifest}")

    task_yaml_roots = {
        root
        for path in changed
        if path.endswith("/task.yaml") and (root := task_root(path))
    }
    for root in sorted(added_roots | task_yaml_roots):
        manifest_path = str(Path(root) / "task.yaml")
        if not path_exists_at(head, manifest_path):
            if path_exists_at(base, manifest_path):
                errors.append(f"task manifest deleted: {manifest_path}")
            continue
        if not run_checker(["scripts/check-task.py", "--dir", root, "--view", "worktree"]):
            errors.append(f"task contract failed: {root}")

    for path in changed:
        step = DOC_STEPS.get(Path(path).name)
        if step and Path(path).is_file():
            if not run_checker(["scripts/check-step.py", step, path]):
                errors.append(f"{step} DOD failed: {path}")

    state_roots = {
        root
        for path in changed
        if Path(path).name in {"tasks.md", "verify.md"}
        and (root := task_root(path))
    }
    for root in sorted(state_roots):
        tasks_path = Path(root) / "tasks.md"
        if tasks_path.is_file() and not run_checker(
            ["scripts/check_task_state.py", str(tasks_path), "--view", "worktree"]
        ):
            errors.append(f"task state failed: {tasks_path}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.environ.get("GOVERNANCE_BASE_SHA"))
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()

    base = resolve_base(args.base)
    print(f"Governance diff: {base}..{args.head}")
    errors = validate(base, args.head)
    if errors:
        for error in errors:
            print(f"::error::{error}")
        print(f"❌ governance gate failed ({len(errors)} error(s))")
        return 1
    print("✅ governance gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
