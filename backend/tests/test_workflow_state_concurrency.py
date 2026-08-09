"""Idempotent remote workflow-state retry tests with real Git remotes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.canonical import event_hash  # noqa: E402
from scripts.workflow_state.git_store import (  # noqa: E402
    STATE_REF,
    GitStateStore,
    StateStoreError,
)
from scripts.workflow_state.models import ActorKind, EventType, TaskEvent  # noqa: E402


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


def _repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.name", "Workflow State Tests")
    _git(path, "config", "user.email", "workflow-state@example.invalid")
    (path / "business.txt").write_text("business\n")
    _git(path, "add", "business.txt")
    _git(path, "commit", "-qm", "business root")
    return path


def _remote_pair(tmp_path: Path):
    remote = tmp_path / "remote.git"
    remote.mkdir()
    _git(remote, "init", "--bare", "-q")
    repo = _repo(tmp_path / "writer")
    _git(repo, "remote", "add", "origin", str(remote))
    store = GitStateStore(repo)
    store.bootstrap()
    _git(repo, "push", "-q", "origin", f"{STATE_REF}:{STATE_REF}")
    return remote, repo, store


def _event(
    *,
    event_id: str,
    idempotency_key: str,
    sequence: int = 1,
    previous_event_hash=None,
    phase: str = "research",
) -> TaskEvent:
    return TaskEvent.model_validate(
        {
            "schema_version": "task-event/v1",
            "event_id": event_id,
            "idempotency_key": idempotency_key,
            "task_id": "2026-08-09-concurrency",
            "sequence": sequence,
            "event_type": (
                EventType.TASK_CREATED
                if event_id == "evt-create"
                else EventType.STEP_STARTED
            ),
            "occurred_at": "2026-08-09T04:00:00Z",
            "actor": {"kind": ActorKind.WRITER, "id": "writer-1"},
            "subject": {},
            "payload": {} if event_id == "evt-create" else {"phase": phase},
            "previous_event_hash": previous_event_hash,
        }
    )


def test_same_idempotency_retry_returns_existing_event_without_new_commit(tmp_path):
    remote, repo, store = _remote_pair(tmp_path)
    event = _event(event_id="evt-create", idempotency_key="create")
    first = store.append_event_with_retry(event)
    remote_after_first = _git(remote, "rev-parse", STATE_REF)

    second = store.append_event_with_retry(event)

    assert first.idempotent is False
    assert second.idempotent is True
    assert second.new_commit == remote_after_first
    assert _git(remote, "rev-parse", STATE_REF) == remote_after_first
    assert _git(repo, "rev-list", "--count", STATE_REF) == "2"
    event_files = [
        name
        for name in store.load_snapshot().files
        if "/events/" in name and name.endswith(".json")
    ]
    assert event_files == [
        "tasks/2026-08-09-concurrency/events/000001-evt-create.json"
    ]


def test_same_idempotency_with_changed_payload_fails_closed(tmp_path):
    remote, repo, store = _remote_pair(tmp_path)
    event = _event(event_id="evt-create", idempotency_key="create")
    store.append_event_with_retry(event)
    old_remote = _git(remote, "rev-parse", STATE_REF)
    conflict = event.model_copy(
        update={"occurred_at": datetime(2026, 8, 9, 5, tzinfo=timezone.utc)}
    )

    with pytest.raises(StateStoreError) as exc_info:
        store.append_event_with_retry(conflict)

    assert exc_info.value.code == "idempotency_conflict"
    assert _git(remote, "rev-parse", STATE_REF) == old_remote
    assert _git(repo, "rev-parse", STATE_REF) == old_remote


def test_stale_actor_replays_on_remote_head_without_losing_either_event(tmp_path):
    remote, repo_a, store_a = _remote_pair(tmp_path)
    create = _event(event_id="evt-create", idempotency_key="create")
    store_a.append_event_with_retry(create)
    repo_b = _repo(tmp_path / "writer-b")
    _git(repo_b, "remote", "add", "origin", str(remote))
    _git(repo_b, "fetch", "-q", "origin", STATE_REF)
    _git(repo_b, "update-ref", STATE_REF, "FETCH_HEAD")
    store_b = GitStateStore(repo_b)
    stale_hash = event_hash(create)
    event_a = _event(
        event_id="evt-a",
        idempotency_key="actor-a",
        sequence=2,
        previous_event_hash=stale_hash,
        phase="plan",
    )
    event_b = _event(
        event_id="evt-b",
        idempotency_key="actor-b",
        sequence=2,
        previous_event_hash=stale_hash,
        phase="implementation",
    )

    store_a.append_event_with_retry(event_a)
    result_b = store_b.append_event_with_retry(event_b)

    _git(repo_a, "fetch", "-q", "origin", STATE_REF)
    _git(repo_a, "update-ref", STATE_REF, "FETCH_HEAD")
    events = [
        json.loads(content)
        for path, content in store_a.load_snapshot().files.items()
        if "/events/" in path and path.endswith(".json")
    ]
    assert result_b.attempts <= 3
    assert [event["idempotency_key"] for event in events] == [
        "create",
        "actor-a",
        "actor-b",
    ]
    assert [event["sequence"] for event in events] == [1, 2, 3]


def test_push_rejection_replays_and_succeeds_by_third_attempt(tmp_path, monkeypatch):
    remote, repo, store = _remote_pair(tmp_path)
    calls = {"count": 0}
    real_push = store._push_state_ref

    def reject_twice(commit, remote_name):
        calls["count"] += 1
        if calls["count"] < 3:
            return False
        return real_push(commit, remote_name)

    monkeypatch.setattr(store, "_push_state_ref", reject_twice)

    result = store.append_event_with_retry(
        _event(event_id="evt-create", idempotency_key="create")
    )

    assert calls["count"] == 3
    assert result.attempts == 3
    assert _git(remote, "rev-parse", STATE_REF) == result.new_commit


def test_three_push_rejections_return_blocked_and_restore_remote_head(
    tmp_path,
    monkeypatch,
):
    remote, repo, store = _remote_pair(tmp_path)
    remote_head = _git(remote, "rev-parse", STATE_REF)
    monkeypatch.setattr(store, "_push_state_ref", lambda commit, remote_name: False)

    with pytest.raises(StateStoreError) as exc_info:
        store.append_event_with_retry(
            _event(event_id="evt-create", idempotency_key="create")
        )

    assert exc_info.value.code == "retry_exhausted"
    assert exc_info.value.blocked is True
    assert _git(remote, "rev-parse", STATE_REF) == remote_head
    assert _git(repo, "rev-parse", STATE_REF) == remote_head


def test_unavailable_event_authority_blocks_before_local_append(tmp_path):
    remote, repo, store = _remote_pair(tmp_path)
    local_head = _git(repo, "rev-parse", STATE_REF)
    _git(repo, "remote", "set-url", "origin", str(tmp_path / "missing.git"))

    with pytest.raises(StateStoreError) as exc_info:
        store.append_event_with_retry(
            _event(event_id="evt-create", idempotency_key="create")
        )

    assert exc_info.value.code == "event_authority_unavailable"
    assert exc_info.value.blocked is True
    assert _git(repo, "rev-parse", STATE_REF) == local_head


def test_remote_push_uses_plain_fast_forward_refspec(tmp_path, monkeypatch):
    remote, repo, store = _remote_pair(tmp_path)
    commands = []
    real_run = store._run

    def record(args, **kwargs):
        commands.append(list(args))
        return real_run(args, **kwargs)

    monkeypatch.setattr(store, "_run", record)
    store.append_event_with_retry(
        _event(event_id="evt-create", idempotency_key="create")
    )
    pushes = [command for command in commands if command[0] == "push"]

    assert len(pushes) == 1
    assert "--force" not in pushes[0]
    assert "-f" not in pushes[0]
    assert not pushes[0][-1].startswith("+")


def test_option_like_remote_name_is_rejected_before_git_execution(tmp_path):
    remote, repo, store = _remote_pair(tmp_path)
    local_head = _git(repo, "rev-parse", STATE_REF)

    with pytest.raises(StateStoreError) as exc_info:
        store.append_event_with_retry(
            _event(event_id="evt-create", idempotency_key="create"),
            remote="--upload-pack=attacker",
        )

    assert exc_info.value.code == "unsafe_remote_name"
    assert _git(remote, "rev-parse", STATE_REF) == local_head
    assert _git(repo, "rev-parse", STATE_REF) == local_head
