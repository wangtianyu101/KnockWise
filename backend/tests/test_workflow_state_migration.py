"""T16 · legacy snapshot migration (REQ-011 / SCN-018 / SCN-019 / TC-018 / TC-019).

Contract:
  - Active legacy tasks must produce exactly one ``legacy_snapshot_imported``
    event whose projection carries ``LegacyTrust.LEGACY_UNVERIFIED``.
  - The migration must NOT fabricate historical test/verifier/acceptance
    events for the legacy task; the projection must keep those evidence
    dimensions in their pre-migration state (typically ``None``/``PENDING``).
  - Archived legacy tasks (``LEGACY_UNVERIFIED`` already, no active
    writers) must NOT be re-imported and must keep their file system state
    read-only.
  - All migration events must be authored by the dedicated ``MIGRATION``
    actor and bound to the canonical ``migration`` event namespace.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.models import (  # noqa: E402
    AcceptanceState,
    ActorKind,
    EventType,
    EvidenceState,
    LegacyTrust,
    TaskProjection,
)
from scripts.workflow_state.migrate import (  # noqa: E402
    LegacyMigrationError,
    import_legacy_snapshot,
    should_skip_archived,
)
from scripts.workflow_state.git_store import GitStateStore  # noqa: E402


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
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout.decode().strip()


def _init_state_branch(repo: Path) -> Path:
    """Create a real ``workflow-state`` branch in ``repo`` and init it."""
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Migration Tests")
    _git(repo, "config", "user.email", "migration@example.invalid")
    GitStateStore(repo).bootstrap()
    return Path(repo)


def _write_legacy_task(repo: Path, task_id: str, *, archived: bool = False) -> Path:
    legacy = repo / "docs" / "tasks" / task_id
    legacy.mkdir(parents=True)
    (legacy / "tasks.md").write_text(
        f"# {task_id}\n\n> Legacy task fixture.\n",
        encoding="utf-8",
    )
    if archived:
        (legacy / "ARCHIVED").write_text("archived=2026-08-01\n", encoding="utf-8")
    _git(repo, "add", str(legacy.relative_to(repo)))
    _git(repo, "commit", "-qm", f"legacy fixture: {task_id}")
    return legacy


def test_import_active_legacy_emits_exactly_one_event_with_unverified_trust(
    tmp_path: Path,
):
    repo = _init_state_branch(tmp_path)
    _write_legacy_task(repo, "2026-08-01-active")

    projection = import_legacy_snapshot(
        repo,
        task_id="2026-08-01-active",
        default_branch_ref="refs/heads/main",
    )

    assert projection.legacy_trust is LegacyTrust.LEGACY_UNVERIFIED
    # The migration must NOT fabricate historical evidence.
    assert projection.implementation_state in (EvidenceState.NOT_RUN,)
    assert projection.test_state in (EvidenceState.NOT_RUN,)
    assert projection.verifier_state in (EvidenceState.NOT_RUN,)
    assert projection.acceptance_state in (AcceptanceState.PENDING,)
    # The branch ref must now expose two events for the imported task.
    state_log = _git(
        repo,
        "log",
        "--format=%H %s",
        "refs/heads/workflow-state",
        "--",
        "tasks/2026-08-01-active/events/",
    )
    assert state_log.count("\n") == 1, state_log


def test_migration_event_is_authored_by_migration_actor(tmp_path: Path):
    repo = _init_state_branch(tmp_path)
    _write_legacy_task(repo, "2026-08-02-actor")

    projection = import_legacy_snapshot(
        repo,
        task_id="2026-08-02-actor",
        default_branch_ref="refs/heads/main",
    )

    # Read the canonical event written to the state branch.
    event_log = _git(
        repo,
        "log",
        "--format=%H",
        "refs/heads/workflow-state",
        "--",
        "tasks/2026-08-02-actor/events/",
    )
    # Two commits (TASK_CREATED + LEGACY_SNAPSHOT_IMPORTED).
    assert event_log.count("\n") == 1, event_log

    # The two events are stored as separate files; read the legacy one.
    event_files = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "refs/heads/workflow-state",
         "--", "tasks/2026-08-02-actor/events/"],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=True,
    ).stdout.decode().splitlines()
    assert len(event_files) == 2, event_files
    # Identify the legacy event by sequence number 2 (TASK_CREATED is 1).
    legacy_path = next(
        name for name in event_files
        if name.endswith(".json") and name.rsplit("/", 1)[1].startswith("000002-")
    )
    payload = json.loads(
        subprocess.run(
            ["git", "show", f"refs/heads/workflow-state:{legacy_path}"],
            cwd=repo,
            capture_output=True,
            env=_clean_env(),
            check=True,
        ).stdout
    )

    assert payload["actor"]["kind"] == ActorKind.MIGRATION.value
    assert payload["event_type"] == EventType.LEGACY_SNAPSHOT_IMPORTED.value
    # Idempotent re-import keeps the single migration event intact.
    second_projection = import_legacy_snapshot(
        repo,
        task_id="2026-08-02-actor",
        default_branch_ref="refs/heads/main",
    )
    assert second_projection.legacy_trust is LegacyTrust.LEGACY_UNVERIFIED


def test_archived_legacy_tasks_are_skipped(tmp_path: Path):
    repo = _init_state_branch(tmp_path)
    archived = _write_legacy_task(repo, "2026-08-03-archived", archived=True)
    legacy_mtime = archived.stat().st_mtime

    skip = should_skip_archived(repo, task_id="2026-08-03-archived")
    assert skip is True

    # Archived legacy files must remain read-only on disk; the migration
    # call must be a no-op (no events written, no errors raised).
    projection = import_legacy_snapshot(
        repo,
        task_id="2026-08-03-archived",
        default_branch_ref="refs/heads/main",
    )
    assert projection.legacy_trust is LegacyTrust.LEGACY_UNVERIFIED
    assert archived.stat().st_mtime == legacy_mtime
    # No events were appended for the archived task.
    log = _git(
        repo,
        "log",
        "--format=%H",
        "refs/heads/workflow-state",
        "--",
        "tasks/2026-08-03-archived/",
    )
    assert log == ""


def test_migration_rejects_unknown_legacy_trust_with_error(tmp_path: Path):
    repo = _init_state_branch(tmp_path)

    with pytest.raises(LegacyMigrationError):
        import_legacy_snapshot(
            repo,
            task_id="not-found",
            default_branch_ref="refs/heads/main",
        )


def test_projection_for_active_legacy_keeps_evidence_dimensions_pending(tmp_path: Path):
    repo = _init_state_branch(tmp_path)
    _write_legacy_task(repo, "2026-08-04-pending")

    projection = import_legacy_snapshot(
        repo,
        task_id="2026-08-04-pending",
        default_branch_ref="refs/heads/main",
    )

    # Active legacy tasks MUST stay LEGACY_UNVERIFIED and MUST NOT inherit
    # any non-pending evidence from prior tooling.  We assert the structural
    # contract; specific reasons live in tasks.md § 4.1 (REQ-011).
    assert isinstance(projection, TaskProjection)
    assert projection.legacy_trust is LegacyTrust.LEGACY_UNVERIFIED
    assert projection.implementation_state is EvidenceState.NOT_RUN
    assert projection.test_state is EvidenceState.NOT_RUN
    assert projection.verifier_state is EvidenceState.NOT_RUN
    assert projection.acceptance_state is AcceptanceState.PENDING
    assert projection.merge_gate_state is EvidenceState.NOT_RUN