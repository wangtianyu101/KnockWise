"""Subprocess contract tests for the core taskctl commands."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKCTL = REPO_ROOT / "scripts" / "taskctl.py"
STATE_REF = "refs/heads/workflow-state"
TASK_ID = "2026-08-09-cli"


def _clean_env():
    environment = os.environ.copy()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
    ):
        environment.pop(key, None)
    return environment


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env=_clean_env(),
        text=True,
    ).stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Taskctl Tests")
    _git(repo, "config", "user.email", "taskctl@example.invalid")
    (repo / "business.txt").write_text("business\n")
    _git(repo, "add", "business.txt")
    _git(repo, "commit", "-qm", "business root")
    return repo


def _taskctl(repo: Path, *args: str, extra_env=None):
    environment = _clean_env()
    environment.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(TASKCTL), *args],
        cwd=repo,
        capture_output=True,
        env=environment,
        text=True,
    )


def _init(repo: Path):
    result = _taskctl(repo, "init", "--task", TASK_ID, "--mode", "refactor-6")
    assert result.returncode == 0, result.stderr
    return result


def test_init_and_start_write_typed_events_without_free_actor_flags(tmp_path):
    repo = _repo(tmp_path)

    initialized = _init(repo)
    started = _taskctl(repo, "start", "--task", TASK_ID, "--step", "4")

    assert started.returncode == 0, started.stderr
    assert json.loads(initialized.stdout)["event_type"] == "task_created"
    start_output = json.loads(started.stdout)
    assert start_output["event_type"] == "step_started"
    assert start_output["workflow_phase"] == "implementation"
    event_names = _git(repo, "ls-tree", "-r", "--name-only", STATE_REF).splitlines()
    assert f"tasks/{TASK_ID}/events/000001-task-created.json" in event_names
    assert f"tasks/{TASK_ID}/events/000002-step-4-started.json" in event_names
    help_result = _taskctl(repo, "init", "--help")
    assert "--actor" not in help_result.stdout
    assert "--result" not in help_result.stdout


def test_show_supports_json_yaml_and_markdown_from_state_projection(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)

    as_json = _taskctl(repo, "show", "--task", TASK_ID, "--format", "json")
    as_yaml = _taskctl(repo, "show", "--task", TASK_ID, "--format", "yaml")
    as_markdown = _taskctl(
        repo,
        "show",
        "--task",
        TASK_ID,
        "--format",
        "markdown",
    )

    assert as_json.returncode == as_yaml.returncode == as_markdown.returncode == 0
    json_projection = json.loads(as_json.stdout)
    assert yaml.safe_load(as_yaml.stdout) == json_projection
    assert f"task={TASK_ID}" in as_markdown.stdout
    assert "| workflow | research |" in as_markdown.stdout


def test_project_and_check_are_read_only_and_byte_consistent(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    state_before = _git(repo, "rev-parse", STATE_REF)
    head_before = _git(repo, "rev-parse", "HEAD")
    status_before = _git(repo, "status", "--porcelain=v1")

    projected = _taskctl(repo, "project", "--task", TASK_ID)
    checked = _taskctl(repo, "check", "--task", TASK_ID)

    assert projected.returncode == 0, projected.stderr
    assert checked.returncode == 0, checked.stderr
    rendered = json.loads(projected.stdout)
    assert set(rendered) == {
        "task.json",
        "task.yaml",
        "tasks-status.md",
        "verify-status.md",
    }
    assert json.loads(rendered["task.json"]) ["task_id"] == TASK_ID
    assert json.loads(checked.stdout)["status"] == "PASS"
    assert _git(repo, "rev-parse", STATE_REF) == state_before
    assert _git(repo, "rev-parse", "HEAD") == head_before
    assert _git(repo, "status", "--porcelain=v1") == status_before


def test_all_selector_checks_and_projects_every_task(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    second = _taskctl(
        repo,
        "init",
        "--task",
        "2026-08-09-cli-two",
        "--mode",
        "full-6",
    )
    assert second.returncode == 0, second.stderr

    checked = _taskctl(repo, "check", "--all")
    projected = _taskctl(repo, "project", "--all")

    assert checked.returncode == projected.returncode == 0
    assert json.loads(checked.stdout)["tasks"] == [TASK_ID, "2026-08-09-cli-two"]
    assert sorted(json.loads(projected.stdout)) == [TASK_ID, "2026-08-09-cli-two"]


def test_unknown_schema_fails_closed_and_preserves_state_snapshot(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    good_state = _git(repo, "rev-parse", STATE_REF)
    event_path = f"tasks/{TASK_ID}/events/000001-task-created.json"
    worktree = tmp_path / "state-worktree"
    _git(repo, "worktree", "add", "--detach", "-q", str(worktree), good_state)
    event = json.loads((worktree / event_path).read_text())
    event["schema_version"] = "task-event/v999"
    (worktree / event_path).write_text(json.dumps(event) + "\n")
    _git(worktree, "add", event_path)
    _git(worktree, "commit", "-qm", "inject unknown schema")
    bad_state = _git(worktree, "rev-parse", "HEAD")
    _git(repo, "worktree", "remove", "--force", str(worktree))
    _git(repo, "update-ref", STATE_REF, bad_state, good_state)

    result = _taskctl(repo, "check", "--task", TASK_ID)

    assert result.returncode == 1
    error = json.loads(result.stderr)
    assert error["code"] == "event_history_invalid"
    assert _git(repo, "rev-parse", STATE_REF) == bad_state


def test_missing_state_ref_is_blocked_and_usage_errors_return_three(tmp_path):
    repo = _repo(tmp_path)

    blocked = _taskctl(repo, "show", "--task", TASK_ID)
    bad_step = _taskctl(repo, "start", "--task", TASK_ID, "--step", "7")
    missing_selector = _taskctl(repo, "check")

    assert blocked.returncode == 2
    assert json.loads(blocked.stderr)["status"] == "BLOCKED"
    assert bad_step.returncode == 3
    assert missing_selector.returncode == 3


def test_missing_writer_identity_does_not_partially_bootstrap_state_ref(tmp_path):
    repo = _repo(tmp_path)
    _git(repo, "config", "user.email", "")

    result = _taskctl(repo, "init", "--task", TASK_ID, "--mode", "refactor-6")

    assert result.returncode == 2
    assert json.loads(result.stderr)["code"] == "writer_identity_unavailable"
    assert (
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", STATE_REF],
            cwd=repo,
            env=_clean_env(),
        ).returncode
        != 0
    )


def test_cli_ignores_foreign_git_hook_environment(tmp_path):
    target = _repo(tmp_path / "target")
    foreign = _repo(tmp_path / "foreign")
    result = _taskctl(
        target,
        "init",
        "--task",
        TASK_ID,
        "--mode",
        "refactor-6",
        extra_env={
            "GIT_DIR": str(foreign / ".git"),
            "GIT_WORK_TREE": str(foreign),
            "GIT_INDEX_FILE": str(foreign / ".git" / "index"),
        },
    )

    assert result.returncode == 0, result.stderr
    assert _git(target, "show-ref", "--verify", STATE_REF)
    assert (
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", STATE_REF],
            cwd=foreign,
            env=_clean_env(),
        ).returncode
        != 0
    )
