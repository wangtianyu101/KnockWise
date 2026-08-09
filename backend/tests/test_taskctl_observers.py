"""Subprocess contracts for Git commit and test-runner observations."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TASKCTL = REPO_ROOT / "scripts" / "taskctl.py"
STATE_REF = "refs/heads/workflow-state"
TASK_ID = "2026-08-09-observers"


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


def _init(repo: Path) -> None:
    result = _taskctl(repo, "init", "--task", TASK_ID, "--mode", "refactor-6")
    assert result.returncode == 0, result.stderr


def _observe_commit(repo: Path, commit: str):
    return _taskctl(
        repo,
        "observe-commit",
        "--task",
        TASK_ID,
        "--commit",
        commit,
    )


def _event(repo: Path, sequence: int):
    prefix = f"tasks/{TASK_ID}/events/{sequence:06d}-"
    paths = _git(repo, "ls-tree", "-r", "--name-only", STATE_REF).splitlines()
    matches = [path for path in paths if path.startswith(prefix)]
    assert len(matches) == 1
    return json.loads(_git(repo, "show", f"{STATE_REF}:{matches[0]}"))


def _projection(repo: Path):
    result = _taskctl(repo, "show", "--task", TASK_ID, "--format", "json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_observe_commit_records_verified_full_sha_without_touching_business_head(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    business_head = _git(repo, "rev-parse", "HEAD")
    business_status = _git(repo, "status", "--porcelain=v1")

    result = _observe_commit(repo, business_head)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["commit"] == business_head
    assert output["event_type"] == "implementation_committed"
    assert len(output["commit"]) == 40
    event = _event(repo, 2)
    assert event["actor"]["kind"] == "git_observer"
    assert event["subject"]["commit"] == business_head
    assert event["payload"] == {"verification": "git cat-file -e <sha>^{commit}"}
    assert _projection(repo)["active_commit"] == business_head
    assert _projection(repo)["implementation_state"] == "PASS"
    assert _git(repo, "rev-parse", "HEAD") == business_head
    assert _git(repo, "status", "--porcelain=v1") == business_status


def test_observe_commit_rejects_missing_and_non_commit_objects_without_state_change(
    tmp_path,
):
    repo = _repo(tmp_path)
    _init(repo)
    state_before = _git(repo, "rev-parse", STATE_REF)
    missing = "f" * 40
    blob = _git(repo, "hash-object", "business.txt")

    malformed_result = _observe_commit(repo, "abc123")
    missing_result = _observe_commit(repo, missing)
    blob_result = _observe_commit(repo, blob)

    assert malformed_result.returncode == 1
    assert json.loads(malformed_result.stderr)["code"] == "commit_sha_invalid"
    assert missing_result.returncode == 2
    assert json.loads(missing_result.stderr)["code"] == "commit_not_found"
    assert json.loads(missing_result.stderr)["status"] == "BLOCKED"
    assert blob_result.returncode == 2
    assert json.loads(blob_result.stderr)["code"] == "commit_not_found"
    assert _git(repo, "rev-parse", STATE_REF) == state_before
    assert _projection(repo)["implementation_state"] == "NOT_RUN"


def test_markdown_pass_text_does_not_create_test_evidence(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    commit = _git(repo, "rev-parse", "HEAD")
    observed = _observe_commit(repo, commit)
    assert observed.returncode == 0, observed.stderr
    (repo / "tasks.md").write_text("tests: PASS, all green\n")

    projection = _projection(repo)

    assert projection["test_state"] == "NOT_RUN"
    assert len(
        [
            path
            for path in _git(repo, "ls-tree", "-r", "--name-only", STATE_REF).splitlines()
            if "/events/" in path
        ]
    ) == 2


def test_run_test_executes_argv_directly_and_records_complete_pass_evidence(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    commit = _git(repo, "rev-parse", "HEAD")
    assert _observe_commit(repo, commit).returncode == 0
    injection_target = repo / "must-not-exist"
    literal_argument = f"; touch {injection_target}"
    program = (
        "import os, sys; assert os.environ.get('GIT_DIR') is None; "
        "print(sys.argv[1]); print('2 passed, 1 skipped, 3 xfailed')"
    )

    result = _taskctl(
        repo,
        "run-test",
        "--task",
        TASK_ID,
        "--commit",
        commit,
        "--",
        sys.executable,
        "-c",
        program,
        literal_argument,
        extra_env={
            "CI": "observer-contract",
            "GIT_DIR": str(repo / "foreign.git"),
            "GIT_WORK_TREE": str(repo / "foreign-worktree"),
        },
    )

    assert result.returncode == 0, result.stderr
    assert not injection_target.exists()
    output = json.loads(result.stdout)
    assert output["event_type"] == "tests_observed"
    assert output["result"] == "PASS"
    assert output["test_command_rc"] == 0
    event = _event(repo, 3)
    payload = event["payload"]
    expected_stdout = f"{literal_argument}\n2 passed, 1 skipped, 3 xfailed\n".encode()
    assert event["actor"]["kind"] == "test_runner"
    assert event["subject"]["commit"] == commit
    assert payload["result"] == "PASS"
    assert payload["command"] == [sys.executable, "-c", program, literal_argument]
    assert payload["cwd"] == str(repo)
    assert payload["environment"] == {
        "CI": "observer-contract",
        "PYTHONHASHSEED": None,
    }
    assert payload["exit_code"] == 0
    assert payload["counts"] == {
        "failed": 0,
        "passed": 2,
        "skipped": 1,
        "xfail": 3,
    }
    assert payload["stdout_digest"] == "sha256:" + hashlib.sha256(
        expected_stdout
    ).hexdigest()
    assert payload["stderr_digest"] == "sha256:" + hashlib.sha256(b"").hexdigest()
    assert literal_argument in payload["stdout_summary"]
    assert payload["stderr_summary"] == ""
    assert _projection(repo)["test_state"] == "PASS"


def test_run_test_records_fail_and_bounds_output_summaries(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    commit = _git(repo, "rev-parse", "HEAD")
    assert _observe_commit(repo, commit).returncode == 0
    program = "import sys; print('x' * 5000); print('4 failed', file=sys.stderr); sys.exit(7)"

    result = _taskctl(
        repo,
        "run-test",
        "--task",
        TASK_ID,
        "--commit",
        commit,
        "--",
        sys.executable,
        "-c",
        program,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["result"] == "FAIL"
    event = _event(repo, 3)
    payload = event["payload"]
    assert payload["result"] == "FAIL"
    assert payload["exit_code"] == 7
    assert payload["counts"] == {
        "failed": 4,
        "passed": 0,
        "skipped": 0,
        "xfail": 0,
    }
    assert len(payload["stdout_summary"].encode("utf-8")) <= 2048
    assert payload["stdout_truncated"] is True
    assert payload["stderr_summary"] == "4 failed\n"
    assert payload["stderr_truncated"] is False
    assert _projection(repo)["test_state"] == "FAIL"


def test_run_test_rejects_commit_mismatch_before_executing_command(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    active_commit = _git(repo, "rev-parse", "HEAD")
    assert _observe_commit(repo, active_commit).returncode == 0
    (repo / "business.txt").write_text("second\n")
    _git(repo, "add", "business.txt")
    _git(repo, "commit", "-qm", "second business commit")
    other_commit = _git(repo, "rev-parse", "HEAD")
    state_before = _git(repo, "rev-parse", STATE_REF)
    marker = repo / "must-not-run"

    result = _taskctl(
        repo,
        "run-test",
        "--task",
        TASK_ID,
        "--commit",
        other_commit,
        "--",
        sys.executable,
        "-c",
        f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')",
    )

    assert result.returncode == 1
    assert json.loads(result.stderr)["code"] == "active_commit_mismatch"
    assert not marker.exists()
    assert _git(repo, "rev-parse", STATE_REF) == state_before


def test_run_test_rejects_missing_command_without_writing_evidence(tmp_path):
    repo = _repo(tmp_path)
    _init(repo)
    commit = _git(repo, "rev-parse", "HEAD")
    assert _observe_commit(repo, commit).returncode == 0
    state_before = _git(repo, "rev-parse", STATE_REF)

    result = _taskctl(
        repo,
        "run-test",
        "--task",
        TASK_ID,
        "--commit",
        commit,
        "--",
    )

    assert result.returncode == 1
    assert json.loads(result.stderr)["code"] == "test_command_missing"
    assert _git(repo, "rev-parse", STATE_REF) == state_before


def test_observer_commands_expose_no_self_attestation_flags(tmp_path):
    repo = _repo(tmp_path)

    observe_help = _taskctl(repo, "observe-commit", "--help")
    test_help = _taskctl(repo, "run-test", "--help")

    assert observe_help.returncode == test_help.returncode == 0
    for help_text in (observe_help.stdout, test_help.stdout):
        assert "--actor" not in help_text
        assert "--result" not in help_text
