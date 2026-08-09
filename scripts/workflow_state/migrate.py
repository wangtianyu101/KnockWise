"""T16 · legacy snapshot migration (REQ-011 / SCN-018 / SCN-019).

Imports active legacy tasks into the workflow-state authority as a single
``legacy_snapshot_imported`` event authored by the dedicated ``MIGRATION``
actor.  Archived tasks are detected and skipped to keep their on-disk
artefacts read-only.

The migration is intentionally narrow:

* No historical test / verifier / acceptance events are fabricated; active
  legacy tasks stay ``LEGACY_UNVERIFIED`` until they re-run the new pipeline.
* Re-importing the same task is idempotent — the migration append is keyed
  on ``(task_id, "legacy_snapshot_imported")`` so a second call observes the
  existing event instead of appending a duplicate.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from .actors import is_actor_allowed
from .canonical import event_hash
from .git_store import GitStateStore, StateStoreError
from .models import (
    AcceptanceState,
    ActorKind,
    EventActor,
    EventSubject,
    EventType,
    EvidenceState,
    LegacyTrust,
    TaskEvent,
    TaskProjection,
    WorkflowPhase,
)
from .reducer import reduce_events


class LegacyMigrationError(Exception):
    """Raised when a legacy task cannot be imported."""

    def __init__(self, code: str, message: str, *, blocked: bool = True) -> None:
        super().__init__(message)
        self.code = code
        self.blocked = blocked


_LEGACY_TASK_PREFIX = "docs/tasks/"
_LEGACY_ARCHIVE_MARKER = "ARCHIVED"


def _clean_env() -> dict[str, str]:
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
    environment["LC_ALL"] = "C"
    return environment


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        raise LegacyMigrationError(
            "git_command_failed",
            f"git {' '.join(args)} failed (rc={result.returncode}): {stderr}",
        )
    return result.stdout.decode().strip()


def _commit_on_default_branch(repo: Path, task_id: str, default_branch_ref: str) -> bool:
    rel = f"{_LEGACY_TASK_PREFIX}{task_id}"
    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            "HEAD",
            default_branch_ref,
        ],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=False,
    )
    if ancestor.returncode != 0:
        return False
    listed = subprocess.run(
        ["git", "ls-tree", "HEAD", "--", rel],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=False,
    )
    if listed.returncode != 0:
        return False
    return bool(listed.stdout.strip())


def _has_archive_marker(repo: Path, task_id: str) -> bool:
    rel = f"{_LEGACY_TASK_PREFIX}{task_id}/{_LEGACY_ARCHIVE_MARKER}"
    result = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{rel}"],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=False,
    )
    return result.returncode == 0


def should_skip_archived(repo: Path, task_id: str) -> bool:
    """Return ``True`` when the legacy task is archived and must be skipped."""

    return _has_archive_marker(repo, task_id)


def _build_migration_event(
    *,
    task_id: str,
    repo_path: str,
    legacy_trust: LegacyTrust,
    now: _dt.datetime,
    previous_event_hash: Optional[str],
    idempotency_key: str,
    event_id: str,
) -> TaskEvent:
    if not is_actor_allowed(EventType.LEGACY_SNAPSHOT_IMPORTED, ActorKind.MIGRATION):
        raise LegacyMigrationError(
            "actor_migration_not_allowed",
            "migration actor is not authorized for legacy_snapshot_imported",
        )
    actor = EventActor(
        kind=ActorKind.MIGRATION,
        id="migration:bootstrap",
    )
    subject = EventSubject(
        commit=None,
        spec_hash=None,
    )
    payload = {
        "legacy_trust": legacy_trust.value,
        "snapshot_source": "taskctl_import_legacy_snapshot",
        "imported_at": now.isoformat(),
    }
    return TaskEvent(
        schema_version="task-event/v1",
        event_id=event_id,
        idempotency_key=idempotency_key,
        task_id=task_id,
        sequence=2,
        event_type=EventType.LEGACY_SNAPSHOT_IMPORTED,
        occurred_at=now,
        actor=actor,
        subject=subject,
        payload=payload,
        previous_event_hash=previous_event_hash,
    )


def _load_existing_events(repo: Path, store: GitStateStore, task_id: str) -> list:
    snapshot = store.load_snapshot()
    events: list = []
    for path, blob in snapshot.files.items():
        if not path.startswith(f"tasks/{task_id}/events/"):
            continue
        if not path.endswith(".json"):
            continue
        try:
            payload = json.loads(blob.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        events.append(TaskEvent.model_validate(payload))
    return sorted(events, key=lambda ev: ev.sequence)


def _empty_projection(task_id: str) -> TaskProjection:
    return TaskProjection(
        schema_version="task-projection/v1",
        task_id=task_id,
        source_sequence=1,
        source_hash=("sha256:" + "0" * 64),
        workflow_phase=WorkflowPhase.RESEARCH,
        implementation_state=EvidenceState.NOT_RUN,
        test_state=EvidenceState.NOT_RUN,
        verifier_state=EvidenceState.NOT_RUN,
        acceptance_state=AcceptanceState.PENDING,
        merge_gate_state=EvidenceState.NOT_RUN,
        active_commit=None,
        active_spec_hash=None,
        legacy_trust=LegacyTrust.LEGACY_UNVERIFIED,
    )


def import_legacy_snapshot(
    repo: Path | str,
    task_id: str,
    default_branch_ref: str = "refs/heads/main",
) -> TaskProjection:
    """Import a single legacy task into the workflow-state authority.

    The migration is idempotent: a second call observes the existing
    ``legacy_snapshot_imported`` event and re-derives the projection rather
    than appending a duplicate.
    """
    repo = Path(repo)

    if not default_branch_ref.startswith("refs/heads/"):
        raise LegacyMigrationError(
            "untrusted_default_branch_ref",
            f"default_branch_ref {default_branch_ref!r} must be a refs/heads/* branch",
        )

    if not _commit_on_default_branch(repo, task_id, default_branch_ref):
        raise LegacyMigrationError(
            "legacy_task_not_on_default_branch",
            f"legacy task {task_id!r} is not reachable from {default_branch_ref}",
        )

    if should_skip_archived(repo, task_id):
        # Archived tasks stay read-only; no events are appended.  The
        # returned projection is the empty LEGACY_UNVERIFIED skeleton so
        # callers can treat active and archived tasks uniformly.
        return _empty_projection(task_id)

    store = GitStateStore(repo)

    existing_events = _load_existing_events(repo, store, task_id)
    legacy_event_exists = any(
        event.event_type is EventType.LEGACY_SNAPSHOT_IMPORTED
        for event in existing_events
    )

    if not legacy_event_exists:
        previous_event_hash = (
            "sha256:" + existing_events[-1].previous_event_hash.split("sha256:")[-1]
            if existing_events and existing_events[-1].previous_event_hash
            else None
        )
        # Use the last existing event_id as the hash link target (sha256:hex64).
        if existing_events:
            previous_event_hash = (
                "sha256:" + hashlib.sha256(
                    existing_events[-1].event_id.encode()
                ).hexdigest()
            )

        now = _dt.datetime.now(_dt.timezone.utc)

        task_created_idempotency = f"{task_id}:task_created:legacy"
        task_created_event_id = hashlib.sha256(
            task_created_idempotency.encode()
        ).hexdigest()
        task_created = TaskEvent(
            schema_version="task-event/v1",
            event_id=task_created_event_id,
            idempotency_key=task_created_idempotency,
            task_id=task_id,
            sequence=1,
            event_type=EventType.TASK_CREATED,
            occurred_at=now,
            actor=EventActor(kind=ActorKind.MIGRATION, id="migration:bootstrap"),
            subject=EventSubject(),
            payload={
                "legacy_trust": LegacyTrust.LEGACY_UNVERIFIED.value,
                "snapshot_source": "taskctl_import_legacy_snapshot",
            },
            previous_event_hash=previous_event_hash,
        )
        try:
            store.append_event(task_created)
        except StateStoreError as exc:
            raise LegacyMigrationError(exc.code, str(exc)) from exc

        idempotency_key = f"{task_id}:legacy_snapshot_imported"
        event_id = hashlib.sha256(idempotency_key.encode()).hexdigest()
        event = _build_migration_event(
            task_id=task_id,
            repo_path=str(repo.resolve()),
            legacy_trust=LegacyTrust.LEGACY_UNVERIFIED,
            now=now,
            previous_event_hash=event_hash(task_created),
            idempotency_key=idempotency_key,
            event_id=event_id,
        )
        try:
            store.append_event(event)
        except StateStoreError as exc:
            raise LegacyMigrationError(exc.code, str(exc)) from exc

    events = _load_existing_events(repo, store, task_id)
    if events:
        projection = reduce_events(events)
        projection_dict = projection.model_dump()
    else:
        projection_dict = _empty_projection(task_id).model_dump()
    projection_dict["legacy_trust"] = LegacyTrust.LEGACY_UNVERIFIED
    projection_dict["implementation_state"] = EvidenceState.NOT_RUN
    projection_dict["test_state"] = EvidenceState.NOT_RUN
    projection_dict["verifier_state"] = EvidenceState.NOT_RUN
    projection_dict["acceptance_state"] = AcceptanceState.PENDING
    projection_dict["merge_gate_state"] = EvidenceState.NOT_RUN

    return TaskProjection.model_validate(projection_dict)