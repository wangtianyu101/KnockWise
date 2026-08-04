"""Pure ordered-events to TaskProjection reducer."""

from __future__ import annotations

from typing import Optional, Sequence

from .canonical import validate_event_chain
from .models import (
    AcceptanceState,
    EventType,
    EvidenceState,
    LegacyTrust,
    TaskEvent,
    TaskProjection,
    WorkflowPhase,
)


class ReducerError(ValueError):
    """A stable semantic state-transition failure."""

    def __init__(self, code: str, message: str, *, sequence: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.sequence = sequence


_OBSERVABLE_RESULTS = {
    EvidenceState.PASS,
    EvidenceState.FAIL,
    EvidenceState.BLOCKED,
}


def _evidence_result(event: TaskEvent) -> EvidenceState:
    raw_result = event.payload.get("result")
    try:
        result = EvidenceState(raw_result)
    except (TypeError, ValueError) as exc:
        raise ReducerError(
            "invalid_evidence_result",
            f"event {event.sequence} has invalid result {raw_result!r}",
            sequence=event.sequence,
        ) from exc
    if result not in _OBSERVABLE_RESULTS:
        raise ReducerError(
            "invalid_evidence_result",
            f"event {event.sequence} cannot observe result {result.value}",
            sequence=event.sequence,
        )
    return result


def _workflow_phase(event: TaskEvent) -> WorkflowPhase:
    raw_phase = event.payload.get("phase")
    try:
        return WorkflowPhase(raw_phase)
    except (TypeError, ValueError) as exc:
        raise ReducerError(
            "invalid_workflow_phase",
            f"event {event.sequence} has invalid phase {raw_phase!r}",
            sequence=event.sequence,
        ) from exc


def _require_commit(event: TaskEvent, code: str) -> str:
    commit = event.subject.commit
    if commit is None:
        raise ReducerError(
            code,
            f"event {event.sequence} must bind a commit",
            sequence=event.sequence,
        )
    return commit


def _require_active_implementation(
    active_commit: Optional[str],
    event: TaskEvent,
) -> None:
    if active_commit is None:
        raise ReducerError(
            "evidence_before_implementation",
            f"event {event.sequence} precedes the first implementation commit",
            sequence=event.sequence,
        )


def reduce_events(events: Sequence[TaskEvent]) -> TaskProjection:
    """Derive current orthogonal facts from one validated event stream.

    Actor authentication is intentionally outside this pure reducer. Callers
    must authorize each event with a trusted adapter before reducing it.
    """

    chain = validate_event_chain(events)
    ordered = [
        event if isinstance(event, TaskEvent) else TaskEvent.model_validate(event)
        for event in events
    ]
    if ordered[0].event_type is not EventType.TASK_CREATED:
        raise ReducerError(
            "first_event_not_task_created",
            "the first event must be task_created",
            sequence=ordered[0].sequence,
        )

    workflow_phase = WorkflowPhase.RESEARCH
    implementation_state = EvidenceState.NOT_RUN
    test_state = EvidenceState.NOT_RUN
    verifier_state = EvidenceState.NOT_RUN
    acceptance_state = AcceptanceState.PENDING
    merge_gate_state = EvidenceState.NOT_RUN
    active_commit = None
    active_spec_hash = None
    legacy_trust = LegacyTrust.NATIVE

    for event in ordered:
        event_type = event.event_type

        if event_type is EventType.STEP_STARTED:
            workflow_phase = _workflow_phase(event)
            acceptance_state = AcceptanceState.PENDING
            new_spec_hash = event.subject.spec_hash
            if new_spec_hash is not None and new_spec_hash != active_spec_hash:
                if verifier_state is not EvidenceState.NOT_RUN:
                    verifier_state = EvidenceState.STALE
                active_spec_hash = new_spec_hash

        elif event_type in {
            EventType.STEP_ACCEPTED,
            EventType.PHASE_ACCEPTED,
        }:
            accepted_spec_hash = event.subject.spec_hash
            if accepted_spec_hash is None:
                raise ReducerError(
                    "acceptance_missing_spec",
                    f"event {event.sequence} must bind a spec hash",
                    sequence=event.sequence,
                )
            if accepted_spec_hash != active_spec_hash:
                raise ReducerError(
                    "acceptance_spec_mismatch",
                    (
                        f"event {event.sequence} accepts {accepted_spec_hash}, "
                        f"active spec is {active_spec_hash}"
                    ),
                    sequence=event.sequence,
                )
            acceptance_state = AcceptanceState.ACCEPTED

        elif event_type is EventType.IMPLEMENTATION_COMMITTED:
            commit = _require_commit(event, "implementation_missing_commit")
            if commit != active_commit:
                active_commit = commit
                test_state = EvidenceState.NOT_RUN
                verifier_state = EvidenceState.NOT_RUN
                merge_gate_state = EvidenceState.NOT_RUN
            implementation_state = EvidenceState.PASS

        elif event_type is EventType.TESTS_OBSERVED:
            commit = _require_commit(event, "tests_missing_commit")
            _require_active_implementation(active_commit, event)
            result = _evidence_result(event)
            if commit == active_commit:
                test_state = result

        elif event_type is EventType.VERIFIER_OBSERVED:
            commit = _require_commit(event, "verifier_missing_commit")
            spec_hash = event.subject.spec_hash
            if spec_hash is None:
                raise ReducerError(
                    "verifier_missing_spec",
                    f"event {event.sequence} must bind a spec hash",
                    sequence=event.sequence,
                )
            _require_active_implementation(active_commit, event)
            result = _evidence_result(event)
            if commit != active_commit:
                continue
            if spec_hash != active_spec_hash:
                if verifier_state is not EvidenceState.NOT_RUN:
                    verifier_state = EvidenceState.STALE
                continue
            verifier_state = result

        elif event_type is EventType.MERGE_GATE_OBSERVED:
            commit = _require_commit(event, "merge_gate_missing_commit")
            _require_active_implementation(active_commit, event)
            result = _evidence_result(event)
            if commit == active_commit:
                merge_gate_state = result

        elif event_type is EventType.LEGACY_SNAPSHOT_IMPORTED:
            legacy_trust = LegacyTrust.LEGACY_UNVERIFIED

    return TaskProjection(
        schema_version="task-projection/v1",
        task_id=chain.task_id,
        source_sequence=chain.last_sequence,
        source_hash=chain.last_hash,
        workflow_phase=workflow_phase,
        implementation_state=implementation_state,
        test_state=test_state,
        verifier_state=verifier_state,
        acceptance_state=acceptance_state,
        merge_gate_state=merge_gate_state,
        active_commit=active_commit,
        active_spec_hash=active_spec_hash,
        legacy_trust=legacy_trust,
    )
