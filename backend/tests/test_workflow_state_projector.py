"""Deterministic workflow-state projection and drift detection tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.models import (  # noqa: E402
    AcceptanceState,
    EvidenceState,
    LegacyTrust,
    TaskProjection,
    WorkflowPhase,
)
from scripts.workflow_state.projector import (  # noqa: E402
    ProjectionDriftError,
    materialize_projection,
    render_projection_files,
    validate_projection_files,
)


SOURCE_HASH = "sha256:" + "a" * 64
COMMIT_SHA = "1" * 40
SPEC_HASH = "sha256:" + "b" * 64


def _projection(**overrides) -> TaskProjection:
    data = {
        "schema_version": "task-projection/v1",
        "task_id": "2026-07-30-example",
        "source_sequence": 7,
        "source_hash": SOURCE_HASH,
        "workflow_phase": WorkflowPhase.IMPLEMENTATION,
        "implementation_state": EvidenceState.PASS,
        "test_state": EvidenceState.PASS,
        "verifier_state": EvidenceState.NOT_RUN,
        "acceptance_state": AcceptanceState.PENDING,
        "merge_gate_state": EvidenceState.NOT_RUN,
        "active_commit": COMMIT_SHA,
        "active_spec_hash": SPEC_HASH,
        "legacy_trust": LegacyTrust.NATIVE,
    }
    data.update(overrides)
    return TaskProjection.model_validate(data)


def test_projection_render_is_byte_deterministic_and_has_fixed_file_set():
    projection = _projection()

    first = render_projection_files(projection)
    second = render_projection_files(projection.model_copy())

    assert first == second
    assert set(first) == {
        "task.json",
        "task.yaml",
        "tasks-status.md",
        "verify-status.md",
    }
    assert all(content.endswith(b"\n") for content in first.values())


def test_json_and_yaml_round_trip_to_same_projection_contract():
    projection = _projection()
    files = render_projection_files(projection)

    from_json = json.loads(files["task.json"])
    from_yaml = yaml.safe_load(files["task.yaml"])

    assert from_json == projection.model_dump(mode="json")
    assert from_yaml == from_json


@pytest.mark.parametrize("filename", ["tasks-status.md", "verify-status.md"])
def test_markdown_views_include_exact_source_marker(filename):
    projection = _projection()

    content = render_projection_files(projection)[filename].decode("utf-8")

    expected = (
        "<!-- workflow-state:begin "
        f"task={projection.task_id} "
        f"source_sequence={projection.source_sequence} "
        f"source_hash={projection.source_hash} -->"
    )
    assert content.startswith(expected + "\n")
    assert content.rstrip().endswith("<!-- workflow-state:end -->")


def test_materialize_projection_writes_once_then_produces_zero_diff(tmp_path):
    projection = _projection()

    first_changed = materialize_projection(tmp_path, projection)
    first_mtimes = {
        path.name: path.stat().st_mtime_ns for path in tmp_path.iterdir()
    }
    second_changed = materialize_projection(tmp_path, projection)
    second_mtimes = {
        path.name: path.stat().st_mtime_ns for path in tmp_path.iterdir()
    }

    assert first_changed == tuple(sorted(render_projection_files(projection)))
    assert second_changed == ()
    assert second_mtimes == first_mtimes


def test_materialize_repairs_only_the_manually_modified_view(tmp_path):
    projection = _projection()
    materialize_projection(tmp_path, projection)
    drifted = tmp_path / "tasks-status.md"
    drifted.write_text(drifted.read_text() + "manual PASS\n")

    changed = materialize_projection(tmp_path, projection)

    assert changed == ("tasks-status.md",)
    validate_projection_files(
        projection,
        {path.name: path.read_bytes() for path in tmp_path.iterdir()},
    )


def test_validate_projection_files_accepts_exact_regeneration():
    projection = _projection()

    validate_projection_files(projection, render_projection_files(projection))


def test_source_marker_mismatch_reports_expected_and_actual_hash():
    projection = _projection()
    files = dict(render_projection_files(projection))
    files["tasks-status.md"] = files["tasks-status.md"].replace(
        SOURCE_HASH.encode(),
        ("sha256:" + "0" * 64).encode(),
        1,
    )

    with pytest.raises(ProjectionDriftError) as exc_info:
        validate_projection_files(projection, files)

    assert exc_info.value.code == "source_marker_mismatch"
    assert exc_info.value.filename == "tasks-status.md"
    assert exc_info.value.expected_source_hash == SOURCE_HASH
    assert exc_info.value.actual_source_hash == "sha256:" + "0" * 64


def test_generated_content_edit_with_unchanged_marker_is_detected():
    projection = _projection()
    files = dict(render_projection_files(projection))
    files["verify-status.md"] = files["verify-status.md"].replace(
        b"| verifier | NOT_RUN |",
        b"| verifier | PASS |",
    )

    with pytest.raises(ProjectionDriftError) as exc_info:
        validate_projection_files(projection, files)

    assert exc_info.value.code == "content_mismatch"
    assert exc_info.value.filename == "verify-status.md"


def test_missing_or_unexpected_projection_file_fails_closed():
    projection = _projection()
    missing = dict(render_projection_files(projection))
    missing.pop("task.json")

    with pytest.raises(ProjectionDriftError) as missing_error:
        validate_projection_files(projection, missing)
    assert missing_error.value.code == "file_set_mismatch"

    unexpected = dict(render_projection_files(projection))
    unexpected["manual.json"] = b"{}\n"
    with pytest.raises(ProjectionDriftError) as unexpected_error:
        validate_projection_files(projection, unexpected)
    assert unexpected_error.value.code == "file_set_mismatch"


def test_governance_dependency_pins_runtime_pyyaml_603():
    requirement = (REPO_ROOT / "scripts" / "requirements-governance.txt").read_text()

    assert requirement.strip() == "PyYAML==6.0.3"
    assert yaml.__version__ == "6.0.3"
