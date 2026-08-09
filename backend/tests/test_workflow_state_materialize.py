"""T17 · generated marker publication (REQ-008 / SCN-001 / SCN-012 / SCN-013).

Contract:
  - ``materialize_task_documents`` rewrites only the
    ``<!-- workflow-state:begin ... end -->`` marker block, preserving all
    human-authored prose around the block.
  - Re-materialization with the same projection must be a zero-byte diff
    (TC-012 idempotency).
  - If a user hand-edits the generated table inside the marker block, the
    next materialize call detects the source_hash mismatch, raises
    ``MarkerHandEditError`` and leaves the file untouched (TC-013 failure).
  - ``dry_run=True`` returns the planned file changes without writing.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.workflow_state.materialize import (  # noqa: E402
    MarkerHandEditError,
    PlannedChange,
    materialize_task_documents,
)


def _write_task_md(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _projection_dict(task_id: str = "2026-08-09-t17") -> dict:
    return {
        "schema_version": "task-projection/v1",
        "task_id": task_id,
        "source_sequence": 1,
        "source_hash": ("sha256:" + "a" * 64),
        "workflow_phase": "research",
        "implementation_state": "NOT_RUN",
        "test_state": "NOT_RUN",
        "verifier_state": "NOT_RUN",
        "acceptance_state": "PENDING",
        "merge_gate_state": "NOT_RUN",
        "active_commit": None,
        "active_spec_hash": None,
        "legacy_trust": "LEGACY_UNVERIFIED",
    }


def test_materialize_creates_marker_when_file_missing(tmp_path: Path):
    projection = _projection_dict()
    planned = materialize_task_documents(
        task_root=tmp_path,
        projection=projection,
        dry_run=False,
    )

    task_md = (tmp_path / "tasks.md").read_text(encoding="utf-8")
    assert "<!-- workflow-state:begin" in task_md
    assert "<!-- workflow-state:end -->" in task_md
    assert "implementation" in task_md
    assert planned == (
        PlannedChange(filename="tasks.md", changed=True),
        PlannedChange(filename="verify.md", changed=True),
    )


def test_materialize_preserves_human_prose_around_marker(tmp_path: Path):
    body = (
        "# T17 fixture\n\n"
        "Owner notes\n"
        "<!-- workflow-state:begin task=2026-08-09-t17 source_sequence=0 "
        "source_hash=sha256:0000000000000000000000000000000000000000000000000000000000000000 -->\n"
        "| stale | row |\n"
        "<!-- workflow-state:end -->\n\n"
        "Closing prose\n"
    )
    _write_task_md(tmp_path / "tasks.md", body)

    projection = _projection_dict()
    materialize_task_documents(
        task_root=tmp_path,
        projection=projection,
        dry_run=False,
    )

    rewritten = (tmp_path / "tasks.md").read_text(encoding="utf-8")
    assert "# T17 fixture" in rewritten
    assert "Owner notes" in rewritten
    assert "Closing prose" in rewritten
    assert "stale" not in rewritten
    assert "implementation" in rewritten


def test_materialize_is_idempotent_when_projection_unchanged(tmp_path: Path):
    projection = _projection_dict()
    materialize_task_documents(task_root=tmp_path, projection=projection, dry_run=False)

    before_bytes = (tmp_path / "tasks.md").read_bytes()
    planned = materialize_task_documents(
        task_root=tmp_path,
        projection=projection,
        dry_run=False,
    )
    after_bytes = (tmp_path / "tasks.md").read_bytes()

    assert before_bytes == after_bytes
    assert all(not change.changed for change in planned)


def test_materialize_detects_hand_edit_inside_marker(tmp_path: Path):
    projection = _projection_dict()
    materialize_task_documents(task_root=tmp_path, projection=projection, dry_run=False)
    original_bytes = (tmp_path / "tasks.md").read_bytes()

    tampered = original_bytes.replace(
        b"| implementation | NOT_RUN |",
        b"| implementation | PASS (hand-edit) |",
        1,
    )
    (tmp_path / "tasks.md").write_bytes(tampered)

    with pytest.raises(MarkerHandEditError):
        materialize_task_documents(
            task_root=tmp_path,
            projection=projection,
            dry_run=False,
        )

    assert (tmp_path / "tasks.md").read_bytes() == tampered


def test_materialize_dry_run_does_not_write(tmp_path: Path):
    projection = _projection_dict()
    planned = materialize_task_documents(
        task_root=tmp_path,
        projection=projection,
        dry_run=True,
    )

    assert all(change.changed for change in planned)
    assert not (tmp_path / "tasks.md").exists()
    assert not (tmp_path / "verify.md").exists()