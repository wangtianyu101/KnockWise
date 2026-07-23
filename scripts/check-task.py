#!/usr/bin/env python3
"""
check-task.py - Task directory contract validator (per P0-7 spec)

Usage:
    python3 scripts/check-task.py --dir <task_dir> [--view {index,worktree}]

Exit code:
    0 - task.yaml valid (or dir is exempt)
    1 - validation errors found
    2 - task.yaml not found (treated as error)
    3 - invocation error
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Constants per spec § 3
SCHEMA_VERSION = "task/v1"
ALLOWED_MODES = {"full-6", "fix-mini", "refactor-6", "timebox"}
ALLOWED_STEP_STATES = {"in_progress", "accepted", "failed", "blocked"}
ALLOWED_EVIDENCE_TYPES = {"pending", "code", "tasks-inline", "standalone", "e2e"}

# Mode → allowed current_step values (per spec § 1 REQ-2)
MODE_STEPS = {
    "full-6": {0, 1, 2, 3, 4, 5, 6},
    "fix-mini": {0, 4, 6},
    "refactor-6": {0, 1, 2, 3, 4, 5, 6},
    "timebox": {0},  # not in scope for this task
}

# Trigger → required artifacts (per spec § 3.2)
TRIGGER_ARTIFACTS = {
    "ui_design": ["design-spec.md", "mockups/index.html"],
    "ui_components": ["component-spec.md"],
    "api_change": ["api-spec.md"],
    "db_change": ["db-design.md"],
}

# EXEMPT_PATHS (per spec § 1 REQ-8)
# - 12 老任务目录（2026-07-XX，LEGACY_UNVERIFIED）
# - docs/archive/ 全豁免
EXEMPT_PATTERNS = [
    # Legacy 2026-07-01 to 2026-07-22 tasks (LEGACY_UNVERIFIED)
    re.compile(r"^docs/tasks/2026-07-(0[1-9]|1\d|2[0-2])-"),
    re.compile(r"^docs/archive/"),
]


def is_exempt(path: str) -> bool:
    """Check if a path is exempt from task.yaml contract."""
    for pattern in EXEMPT_PATTERNS:
        if pattern.match(path):
            return True
    return False


def read_task_yaml(task_dir: str, view: str = "index") -> str:
    """
    Read task.yaml content.

    view=index: use git show :path (only available in git repo)
    view=worktree: use regular Path.read_text()
    """
    task_yaml_path = Path(task_dir) / "task.yaml"

    if not task_yaml_path.exists():
        raise FileNotFoundError(f"task.yaml not found in {task_dir}")

    if view == "worktree":
        return task_yaml_path.read_text()

    if view == "index":
        # Use git show :path to read staged version
        rel_path = str(task_yaml_path)
        result = subprocess.run(
            ["git", "show", f":{rel_path}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            # Not in git or not staged - fall back to worktree
            return task_yaml_path.read_text()
        return result.stdout

    raise ValueError(f"Invalid view: {view}")


def parse_yaml(content: str) -> dict:
    """Parse YAML content, handling empty or invalid gracefully."""
    try:
        return yaml.safe_load(content) or {}
    except yaml.YAMLError:
        return {}


def validate_yaml(data: dict, dir_name: str) -> list:
    """
    Validate task.yaml content per spec § 1.

    Returns list of error codes/messages.
    """
    errors = []

    # E008: schema must be task/v1
    if data.get("schema") != SCHEMA_VERSION:
        errors.append(
            f"E008: schema must be {SCHEMA_VERSION} (got: {data.get('schema')!r})"
        )
        # If schema is wrong, don't validate further
        return errors

    # E007: task_id must match dir name
    if data.get("task_id") != dir_name:
        errors.append(
            f"E007: task_id must match dir name (expected: {dir_name!r}, got: {data.get('task_id')!r})"
        )

    # E001: mode must be in ALLOWED_MODES
    mode = data.get("mode")
    if mode not in ALLOWED_MODES:
        errors.append(
            f"E001: mode must be one of {sorted(ALLOWED_MODES)} (got: {mode!r})"
        )

    # E002: current_step must be in MODE_STEPS[mode]
    current_step = data.get("current_step")
    if mode in MODE_STEPS:
        if current_step not in MODE_STEPS[mode]:
            errors.append(
                f"E002: current_step {current_step!r} not valid for mode {mode!r} "
                f"(allowed: {sorted(MODE_STEPS[mode])})"
            )
    else:
        # mode invalid - already reported in E001
        if not isinstance(current_step, int) or not (0 <= current_step <= 6):
            errors.append(
                f"E002: current_step must be 0-6 int (got: {current_step!r})"
            )

    # E003: step_state must be in ALLOWED_STEP_STATES
    step_state = data.get("step_state")
    if step_state not in ALLOWED_STEP_STATES:
        errors.append(
            f"E003: step_state must be one of {sorted(ALLOWED_STEP_STATES)} "
            f"(got: {step_state!r})"
        )

    # E004: triggers.* required (4 fields)
    triggers = data.get("triggers", {})
    for field in ["ui_design", "ui_components", "api_change", "db_change"]:
        if field not in triggers:
            errors.append(
                f"E004: triggers.{field} required (true or false)"
            )

    # E005: test_evidence.type required + correct
    test_ev = data.get("test_evidence", {})
    if not test_ev.get("type"):
        errors.append("E005: test_evidence.type required")
    elif test_ev["type"] not in ALLOWED_EVIDENCE_TYPES:
        errors.append(
            f"E005: test_evidence.type must be one of {sorted(ALLOWED_EVIDENCE_TYPES)} "
            f"(got: {test_ev['type']!r})"
        )

    # REQ-4 enforcement: test_evidence.type=pending requires current_step < 4
    # And step_state=accepted requires type != pending
    if (current_step in MODE_STEPS.get(mode, set()) and current_step >= 4
            and test_ev.get("type") == "pending"):
        errors.append(
            f"test_evidence.type=pending requires current_step < 4 "
            f"(got: current_step={current_step})"
        )

    # test_evidence.path required when type != pending
    if test_ev.get("type") != "pending" and not test_ev.get("path"):
        errors.append(
            "test_evidence.path required when test_evidence.type != pending"
        )

    return errors


def list_dir_artifacts(task_dir: str, view: str = "worktree") -> set:
    """
    List files in task directory.

    view=worktree: use os.listdir
    view=index: use git ls-tree
    """
    if view == "worktree":
        task_path = Path(task_dir)
        if not task_path.exists():
            return set()
        return {str(p.relative_to(task_path)) for p in task_path.rglob("*")}

    if view == "index":
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", task_dir],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return set()
        # Strip task_dir prefix
        return {
            line[len(task_dir) + 1:]
            for line in result.stdout.splitlines()
            if line.startswith(task_dir + "/")
        }

    raise ValueError(f"Invalid view: {view}")


def validate_dir(task_dir: str, view: str = "worktree") -> list:
    """
    Validate task directory per spec § 1.

    Returns list of error messages.
    """
    task_path = Path(task_dir)
    if not task_path.exists():
        return [f"Task directory not found: {task_dir}"]

    # Load task.yaml
    try:
        content = read_task_yaml(task_dir, view=view)
    except FileNotFoundError:
        return [f"task.yaml not found in {task_dir}"]

    data = parse_yaml(content)
    dir_name = task_path.name

    # Schema validation
    errors = validate_yaml(data, dir_name)

    # If schema is wrong, skip further validation
    if any("E008" in e for e in errors):
        return errors

    # Trigger closure (per spec § 1 REQ-3)
    triggers = data.get("triggers", {})
    artifacts = list_dir_artifacts(task_dir, view=view)

    for trigger, required_artifacts in TRIGGER_ARTIFACTS.items():
        if triggers.get(trigger) is True:
            for req in required_artifacts:
                if req not in artifacts:
                    errors.append(
                        f"trigger {trigger}=true requires artifact: {req}"
                    )

    # step_state=accepted requires verify.md (per spec § 1 REQ-7)
    if data.get("step_state") == "accepted" and "verify.md" not in artifacts:
        errors.append("step_state=accepted requires verify.md")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Task directory contract validator")
    parser.add_argument("--dir", required=True, help="Task directory path")
    parser.add_argument(
        "--view", choices=["index", "worktree"], default="worktree",
        help="File view (index uses git show :path; default: worktree)"
    )
    args = parser.parse_args()

    task_dir = args.dir.rstrip("/")

    # Check exempt
    if is_exempt(task_dir):
        print(f"::warning::task.yaml exempt for {task_dir} (LEGACY_UNVERIFIED or archive)")
        sys.exit(0)

    errors = validate_dir(task_dir, view=args.view)

    if errors:
        for e in errors:
            print(f"::error file={task_dir}/task.yaml::{e}")
        print(f"\n❌ {len(errors)} validation error(s) found for {task_dir}")
        sys.exit(1)
    else:
        print(f"✅ {task_dir} task.yaml valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
