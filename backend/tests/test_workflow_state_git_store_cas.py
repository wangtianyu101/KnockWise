"""Atomic local workflow-state append and CAS tests."""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.canonical import canonical_json, event_hash  # noqa: E402
from scripts.workflow_state.git_store import (  # noqa: E402
    STATE_REF,
    GitStateStore,
    StateStoreError,
)
from scripts.workflow_state.models import ActorKind, EventType, TaskEvent  # noqa: E402
from scripts.workflow_state.projector import PROJECTION_FILENAMES  # noqa: E402


def _git(repo: Path, *args: str) -> str:
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
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env=environment,
        text=True,
    ).stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Workflow State Tests")
    _git(repo, "config", "user.email", "workflow-state@example.invalid")
    (repo / "business.txt").write_text("business\n")
    _git(repo, "add", "business.txt")
    _git(repo, "commit", "-qm", "business root")
    return repo


def _event(
    *,
    sequence: int = 1,
    previous_event_hash=None,
    event_id: str = "evt-001",
) -> TaskEvent:
    return TaskEvent.model_validate(
        {
            "schema_version": "task-event/v1",
            "event_id": event_id,
            "idempotency_key": f"key-{sequence}",
            "task_id": "2026-07-30-cas",
            "sequence": sequence,
            "event_type": (
                EventType.TASK_CREATED
                if sequence == 1
                else EventType.STEP_STARTED
            ),
            "occurred_at": f"2026-07-30T04:00:0{sequence}Z",
            "actor": {"kind": ActorKind.WRITER, "id": "writer-1"},
            "subject": {},
            "payload": {} if sequence == 1 else {"phase": "implementation"},
            "previous_event_hash": previous_event_hash,
        }
    )


def test_append_commits_event_and_projection_atomically_without_touching_business(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    old_state = store.bootstrap()
    business_head = _git(repo, "rev-parse", "HEAD")
    (repo / "business.txt").write_text("dirty business\n")

    result = store.append_event(_event())

    assert result.old_commit == old_state
    assert result.new_commit == _git(repo, "rev-parse", STATE_REF)
    assert _git(repo, "rev-parse", f"{result.new_commit}^") == old_state
    changed = set(
        _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", result.new_commit)
        .splitlines()
    )
    event_path = "tasks/2026-07-30-cas/events/000001-evt-001.json"
    expected = {event_path}
    expected.update(
        f"tasks/2026-07-30-cas/projection/{name}"
        for name in PROJECTION_FILENAMES
    )
    assert changed == expected
    assert store.load_snapshot().files[event_path] == canonical_json(_event()) + b"\n"
    assert _git(repo, "rev-parse", "HEAD") == business_head
    assert (repo / "business.txt").read_text() == "dirty business\n"


def test_second_append_preserves_first_event_and_rebuilds_projection(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    store.bootstrap()
    first = _event()
    first_result = store.append_event(first)
    second = _event(
        sequence=2,
        previous_event_hash=event_hash(first),
        event_id="evt-002",
    )

    result = store.append_event(second)
    snapshot = store.load_snapshot()

    assert result.old_commit == first_result.new_commit
    assert snapshot.files[
        "tasks/2026-07-30-cas/events/000001-evt-001.json"
    ] == canonical_json(first) + b"\n"
    projection = json.loads(
        snapshot.files["tasks/2026-07-30-cas/projection/task.json"]
    )
    assert projection["source_sequence"] == 2
    assert projection["source_hash"] == event_hash(second)


@pytest.mark.parametrize(
    "event",
    [
        _event(sequence=2, previous_event_hash="sha256:" + "0" * 64),
        _event(event_id="../escape"),
    ],
)
def test_invalid_sequence_hash_or_path_does_not_move_state_ref(tmp_path, event):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    old_state = store.bootstrap()

    with pytest.raises((StateStoreError, ValueError)):
        store.append_event(event)

    assert _git(repo, "rev-parse", STATE_REF) == old_state


def test_projection_drift_blocks_append_without_moving_ref(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    store.bootstrap()
    first = _event()
    first_result = store.append_event(first)
    projection_path = "tasks/2026-07-30-cas/projection/task.json"
    with store.temporary_worktree(first_result.new_commit) as worktree:
        (worktree / projection_path).write_text("{}\n")
        _git(worktree, "add", projection_path)
        _git(worktree, "commit", "-qm", "inject drift")
        drift_commit = _git(worktree, "rev-parse", "HEAD")
    _git(repo, "update-ref", STATE_REF, drift_commit, first_result.new_commit)
    second = _event(
        sequence=2,
        previous_event_hash=event_hash(first),
        event_id="evt-002",
    )

    with pytest.raises(StateStoreError) as exc_info:
        store.append_event(second)

    assert exc_info.value.code == "projection_drift"
    assert _git(repo, "rev-parse", STATE_REF) == drift_commit


def test_lock_contention_returns_blocked_and_does_not_move_ref(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    old_state = store.bootstrap()
    lock_path = Path(_git(repo, "rev-parse", "--git-common-dir")) / "taskctl.lock"
    if not lock_path.is_absolute():
        lock_path = repo / lock_path

    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(StateStoreError) as exc_info:
            store.append_event(_event())

    assert exc_info.value.code == "lock_unavailable"
    assert _git(repo, "rev-parse", STATE_REF) == old_state


def test_compare_and_swap_failure_never_overwrites_competing_ref(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    old_state = store.bootstrap()

    def reject_cas(old_commit, new_commit):
        assert old_commit == old_state
        assert new_commit != old_commit
        return False

    monkeypatch.setattr(store, "_compare_and_swap", reject_cas)

    with pytest.raises(StateStoreError) as exc_info:
        store.append_event(_event())

    assert exc_info.value.code == "concurrent_update"
    assert _git(repo, "rev-parse", STATE_REF) == old_state
