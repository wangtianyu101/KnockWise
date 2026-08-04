"""Reducer tests for orthogonal workflow-state evidence semantics."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.canonical import event_hash  # noqa: E402
from scripts.workflow_state.models import (  # noqa: E402
    AcceptanceState,
    ActorKind,
    EventType,
    EvidenceState,
    TaskEvent,
    WorkflowPhase,
)
from scripts.workflow_state.reducer import ReducerError, reduce_events  # noqa: E402


C1 = "1" * 40
C2 = "2" * 40
S1 = "sha256:" + "a" * 64
S2 = "sha256:" + "b" * 64


def _append(
    events: List[TaskEvent],
    event_type: EventType,
    actor: ActorKind,
    *,
    subject: Optional[Dict] = None,
    payload: Optional[Dict] = None,
) -> TaskEvent:
    sequence = len(events) + 1
    event = TaskEvent.model_validate(
        {
            "schema_version": "task-event/v1",
            "event_id": f"evt-{sequence:03d}",
            "idempotency_key": f"idem-{sequence:03d}",
            "task_id": "2026-07-30-example",
            "sequence": sequence,
            "event_type": event_type,
            "occurred_at": f"2026-07-30T04:{sequence:02d}:00Z",
            "actor": {"kind": actor, "id": f"{actor.value}-1"},
            "subject": subject or {},
            "payload": payload or {},
            "previous_event_hash": event_hash(events[-1]) if events else None,
        }
    )
    events.append(event)
    return event


def _created_events() -> List[TaskEvent]:
    events: List[TaskEvent] = []
    _append(
        events,
        EventType.TASK_CREATED,
        ActorKind.WRITER,
        payload={"mode": "refactor-6"},
    )
    return events


def _start_implementation(events: List[TaskEvent], spec_hash: str = S1) -> None:
    _append(
        events,
        EventType.STEP_STARTED,
        ActorKind.WRITER,
        subject={"spec_hash": spec_hash},
        payload={"phase": WorkflowPhase.IMPLEMENTATION.value},
    )


def _implementation(events: List[TaskEvent], commit: str = C1) -> None:
    _append(
        events,
        EventType.IMPLEMENTATION_COMMITTED,
        ActorKind.GIT_OBSERVER,
        subject={"commit": commit},
    )


def _tests(
    events: List[TaskEvent],
    result: str = EvidenceState.PASS.value,
    commit: str = C1,
) -> None:
    _append(
        events,
        EventType.TESTS_OBSERVED,
        ActorKind.TEST_RUNNER,
        subject={"commit": commit},
        payload={"result": result},
    )


def _verifier(
    events: List[TaskEvent],
    result: str = EvidenceState.PASS.value,
    commit: str = C1,
    spec_hash: str = S1,
) -> None:
    _append(
        events,
        EventType.VERIFIER_OBSERVED,
        ActorKind.VERIFIER,
        subject={"commit": commit, "spec_hash": spec_hash},
        payload={"result": result},
    )


def test_test_pass_does_not_infer_verifier_or_acceptance_completed():
    events = _created_events()
    _start_implementation(events)
    _implementation(events)
    _tests(events)

    projection = reduce_events(events)

    assert projection.workflow_phase is WorkflowPhase.IMPLEMENTATION
    assert projection.implementation_state is EvidenceState.PASS
    assert projection.test_state is EvidenceState.PASS
    assert projection.verifier_state is EvidenceState.NOT_RUN
    assert projection.acceptance_state is AcceptanceState.PENDING
    assert projection.merge_gate_state is EvidenceState.NOT_RUN
    assert not hasattr(projection, "completed")


def test_verifier_fail_does_not_rewrite_implementation_test_or_acceptance():
    events = _created_events()
    _start_implementation(events)
    _implementation(events)
    _tests(events)
    _verifier(events, result=EvidenceState.FAIL.value)

    projection = reduce_events(events)

    assert projection.implementation_state is EvidenceState.PASS
    assert projection.test_state is EvidenceState.PASS
    assert projection.verifier_state is EvidenceState.FAIL
    assert projection.acceptance_state is AcceptanceState.PENDING


def test_new_commit_invalidates_old_test_and_verifier_evidence_to_not_run():
    events = _created_events()
    _start_implementation(events)
    _implementation(events, C1)
    _tests(events, commit=C1)
    _verifier(events, commit=C1)
    _implementation(events, C2)

    projection = reduce_events(events)

    assert projection.active_commit == C2
    assert projection.test_state is EvidenceState.NOT_RUN
    assert projection.verifier_state is EvidenceState.NOT_RUN


def test_old_commit_verifier_event_is_retained_but_does_not_apply_to_new_commit():
    events = _created_events()
    _start_implementation(events)
    _implementation(events, C1)
    _implementation(events, C2)
    _verifier(events, commit=C1)

    projection = reduce_events(events)

    assert projection.active_commit == C2
    assert projection.verifier_state is EvidenceState.NOT_RUN


def test_spec_hash_change_marks_existing_verifier_evidence_stale():
    events = _created_events()
    _start_implementation(events, S1)
    _implementation(events)
    _verifier(events, spec_hash=S1)
    _start_implementation(events, S2)

    projection = reduce_events(events)

    assert projection.active_spec_hash == S2
    assert projection.verifier_state is EvidenceState.STALE


def test_spec_hash_change_keeps_never_run_verifier_not_run():
    events = _created_events()
    _start_implementation(events, S1)
    _implementation(events)
    _start_implementation(events, S2)

    assert reduce_events(events).verifier_state is EvidenceState.NOT_RUN


def test_test_observation_for_non_active_commit_does_not_apply():
    events = _created_events()
    _start_implementation(events)
    _implementation(events, C2)
    _tests(events, commit=C1)

    assert reduce_events(events).test_state is EvidenceState.NOT_RUN


def test_user_acceptance_requires_and_matches_active_spec_hash():
    events = _created_events()
    _start_implementation(events, S1)
    _append(
        events,
        EventType.STEP_ACCEPTED,
        ActorKind.USER,
        subject={"spec_hash": S1},
    )

    assert reduce_events(events).acceptance_state is AcceptanceState.ACCEPTED

    mismatch = _created_events()
    _start_implementation(mismatch, S1)
    _append(
        mismatch,
        EventType.STEP_ACCEPTED,
        ActorKind.USER,
        subject={"spec_hash": S2},
    )
    with pytest.raises(ReducerError) as exc_info:
        reduce_events(mismatch)
    assert exc_info.value.code == "acceptance_spec_mismatch"


def test_invalid_observation_result_fails_closed():
    events = _created_events()
    _start_implementation(events)
    _implementation(events)
    _tests(events, result="DONE")

    with pytest.raises(ReducerError) as exc_info:
        reduce_events(events)

    assert exc_info.value.code == "invalid_evidence_result"


@pytest.mark.parametrize(
    ("event_type", "actor", "subject", "error_code"),
    [
        (
            EventType.TESTS_OBSERVED,
            ActorKind.TEST_RUNNER,
            {},
            "tests_missing_commit",
        ),
        (
            EventType.VERIFIER_OBSERVED,
            ActorKind.VERIFIER,
            {"commit": C1},
            "verifier_missing_spec",
        ),
        (
            EventType.MERGE_GATE_OBSERVED,
            ActorKind.CI_GATE,
            {},
            "merge_gate_missing_commit",
        ),
    ],
)
def test_commit_bound_observation_requires_its_subject_fields(
    event_type,
    actor,
    subject,
    error_code,
):
    events = _created_events()
    _start_implementation(events)
    _implementation(events)
    _append(
        events,
        event_type,
        actor,
        subject=subject,
        payload={"result": EvidenceState.PASS.value},
    )

    with pytest.raises(ReducerError) as exc_info:
        reduce_events(events)

    assert exc_info.value.code == error_code


@pytest.mark.parametrize(
    ("event_type", "actor", "subject"),
    [
        (
            EventType.TESTS_OBSERVED,
            ActorKind.TEST_RUNNER,
            {"commit": C1},
        ),
        (
            EventType.VERIFIER_OBSERVED,
            ActorKind.VERIFIER,
            {"commit": C1, "spec_hash": S1},
        ),
        (
            EventType.MERGE_GATE_OBSERVED,
            ActorKind.CI_GATE,
            {"commit": C1},
        ),
    ],
)
def test_evidence_cannot_precede_first_implementation_commit(
    event_type,
    actor,
    subject,
):
    events = _created_events()
    _start_implementation(events)
    _append(
        events,
        event_type,
        actor,
        subject=subject,
        payload={"result": EvidenceState.PASS.value},
    )

    with pytest.raises(ReducerError) as exc_info:
        reduce_events(events)

    assert exc_info.value.code == "evidence_before_implementation"


def test_first_event_must_be_task_created():
    events: List[TaskEvent] = []
    _append(
        events,
        EventType.STEP_STARTED,
        ActorKind.WRITER,
        subject={"spec_hash": S1},
        payload={"phase": WorkflowPhase.SPEC.value},
    )

    with pytest.raises(ReducerError) as exc_info:
        reduce_events(events)

    assert exc_info.value.code == "first_event_not_task_created"


def test_reduction_is_deterministic_for_identical_event_stream():
    events = _created_events()
    _start_implementation(events)
    _implementation(events)
    _tests(events)
    _verifier(events)

    first = reduce_events(events).model_dump_json()
    second = reduce_events(list(events)).model_dump_json()

    assert first == second
