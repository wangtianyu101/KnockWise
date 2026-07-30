"""Contract tests for the workflow-state event and projection schemas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.models import (  # noqa: E402
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


COMMIT_SHA = "a" * 40
SPEC_HASH = "sha256:" + "b" * 64
EVENT_HASH = "sha256:" + "c" * 64


def _event_data(**overrides):
    data = {
        "schema_version": "task-event/v1",
        "event_id": "evt-001",
        "idempotency_key": "task-1:create",
        "task_id": "2026-07-30-example",
        "sequence": 1,
        "event_type": EventType.TASK_CREATED,
        "occurred_at": "2026-07-30T12:00:00+08:00",
        "actor": {"kind": ActorKind.WRITER, "id": "codex-local"},
        "subject": {},
        "payload": {"mode": "refactor-6"},
        "previous_event_hash": None,
    }
    data.update(overrides)
    return data


def _projection_data(**overrides):
    data = {
        "schema_version": "task-projection/v1",
        "task_id": "2026-07-30-example",
        "source_sequence": 1,
        "source_hash": EVENT_HASH,
        "workflow_phase": WorkflowPhase.RESEARCH,
        "implementation_state": EvidenceState.NOT_RUN,
        "test_state": EvidenceState.NOT_RUN,
        "verifier_state": EvidenceState.NOT_RUN,
        "acceptance_state": AcceptanceState.PENDING,
        "merge_gate_state": EvidenceState.NOT_RUN,
        "active_commit": None,
        "active_spec_hash": None,
        "legacy_trust": LegacyTrust.NATIVE,
    }
    data.update(overrides)
    return data


def test_task_event_accepts_v1_contract_and_preserves_stable_values():
    event = TaskEvent.model_validate(_event_data())

    assert event.schema_version == "task-event/v1"
    assert event.event_type is EventType.TASK_CREATED
    assert event.actor == EventActor(kind=ActorKind.WRITER, id="codex-local")
    assert event.subject == EventSubject()
    assert event.occurred_at.isoformat() == "2026-07-30T12:00:00+08:00"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "task-event/v2"),
        ("event_id", ""),
        ("idempotency_key", ""),
        ("task_id", ""),
        ("sequence", 0),
        ("event_type", "writer_claimed_pass"),
        ("occurred_at", "2026-07-30T12:00:00"),
        ("occurred_at", "not-a-timestamp"),
        ("previous_event_hash", "sha256:short"),
    ],
)
def test_task_event_rejects_unknown_or_malformed_core_fields(field, value):
    with pytest.raises(ValidationError):
        TaskEvent.model_validate(_event_data(**{field: value}))


def test_task_event_rejects_unknown_fields_fail_closed():
    with pytest.raises(ValidationError):
        TaskEvent.model_validate(_event_data(secret="must-not-be-accepted"))


@pytest.mark.parametrize(
    "actor",
    [
        {"kind": "administrator", "id": "alice"},
        {"kind": "user", "id": ""},
        {"kind": "user", "id": "x" * 201},
    ],
)
def test_event_actor_rejects_unknown_kind_or_invalid_identity(actor):
    with pytest.raises(ValidationError):
        TaskEvent.model_validate(_event_data(actor=actor))


@pytest.mark.parametrize(
    "subject",
    [
        {"commit": "abc"},
        {"commit": "A" * 40},
        {"spec_hash": "sha256:xyz"},
        {"unexpected": "field"},
    ],
)
def test_event_subject_rejects_malformed_or_unknown_fields(subject):
    with pytest.raises(ValidationError):
        TaskEvent.model_validate(_event_data(subject=subject))


def test_task_projection_accepts_orthogonal_v1_state():
    projection = TaskProjection.model_validate(
        _projection_data(
            implementation_state=EvidenceState.PASS,
            test_state=EvidenceState.PASS,
            verifier_state=EvidenceState.NOT_RUN,
            acceptance_state=AcceptanceState.PENDING,
            active_commit=COMMIT_SHA,
            active_spec_hash=SPEC_HASH,
        )
    )

    assert projection.implementation_state is EvidenceState.PASS
    assert projection.test_state is EvidenceState.PASS
    assert projection.verifier_state is EvidenceState.NOT_RUN
    assert projection.acceptance_state is AcceptanceState.PENDING


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "task-projection/v2"),
        ("task_id", ""),
        ("source_sequence", 0),
        ("source_hash", "sha256:short"),
        ("workflow_phase", "shipping"),
        ("implementation_state", "DONE"),
        ("acceptance_state", "PASS"),
        ("active_commit", "deadbeef"),
        ("active_spec_hash", "sha256:short"),
        ("legacy_trust", "TRUSTED"),
    ],
)
def test_task_projection_rejects_unknown_schema_or_invalid_state(field, value):
    with pytest.raises(ValidationError):
        TaskProjection.model_validate(_projection_data(**{field: value}))


def test_task_projection_rejects_unknown_fields_fail_closed():
    with pytest.raises(ValidationError):
        TaskProjection.model_validate(_projection_data(overall_completed=True))
