"""Security-contract tests for workflow event actor authorization."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.actors import (  # noqa: E402
    ACTOR_EVENT_POLICY,
    ActorAuthorizationError,
    allowed_actors,
    authorize_event_type,
    is_actor_allowed,
)
from scripts.workflow_state.models import ActorKind, EventType  # noqa: E402


EXPECTED_POLICY = {
    EventType.TASK_CREATED: {
        ActorKind.USER,
        ActorKind.WRITER,
        ActorKind.MIGRATION,
    },
    EventType.SCOPE_CONFIRMED: {
        ActorKind.USER,
        ActorKind.MIGRATION,
    },
    EventType.STEP_STARTED: {
        ActorKind.USER,
        ActorKind.WRITER,
        ActorKind.MIGRATION,
    },
    EventType.STEP_ACCEPTED: {ActorKind.USER},
    EventType.IMPLEMENTATION_COMMITTED: {
        ActorKind.GIT_OBSERVER,
        ActorKind.MIGRATION,
    },
    EventType.TESTS_OBSERVED: {
        ActorKind.TEST_RUNNER,
        ActorKind.MIGRATION,
    },
    EventType.VERIFIER_OBSERVED: {
        ActorKind.VERIFIER,
        ActorKind.MIGRATION,
    },
    EventType.PHASE_ACCEPTED: {ActorKind.USER},
    EventType.MERGE_GATE_OBSERVED: {
        ActorKind.CI_GATE,
        ActorKind.MIGRATION,
    },
    EventType.LEGACY_SNAPSHOT_IMPORTED: {ActorKind.MIGRATION},
}


def test_actor_event_policy_covers_every_enum_exactly_once():
    assert set(ACTOR_EVENT_POLICY) == set(EventType)
    assert {
        event_type: set(actor_kinds)
        for event_type, actor_kinds in ACTOR_EVENT_POLICY.items()
    } == EXPECTED_POLICY


@pytest.mark.parametrize(
    ("event_type", "actor_kind"),
    [
        (event_type, actor_kind)
        for event_type in EventType
        for actor_kind in ActorKind
    ],
)
def test_actor_permission_matrix_is_fail_closed_for_all_70_cells(
    event_type,
    actor_kind,
):
    expected = actor_kind in EXPECTED_POLICY[event_type]

    assert is_actor_allowed(event_type, actor_kind) is expected

    if expected:
        authorize_event_type(event_type, actor_kind)
    else:
        with pytest.raises(ActorAuthorizationError) as exc_info:
            authorize_event_type(event_type, actor_kind)
        assert exc_info.value.code == "actor_not_allowed"
        assert exc_info.value.event_type is event_type
        assert exc_info.value.actor_kind is actor_kind


@pytest.mark.parametrize(
    ("event_type", "actor_kind"),
    [
        (EventType.STEP_ACCEPTED, ActorKind.WRITER),
        (EventType.PHASE_ACCEPTED, ActorKind.WRITER),
        (EventType.VERIFIER_OBSERVED, ActorKind.WRITER),
        (EventType.MERGE_GATE_OBSERVED, ActorKind.WRITER),
        (EventType.TESTS_OBSERVED, ActorKind.WRITER),
    ],
)
def test_writer_cannot_self_attest_other_actor_facts(event_type, actor_kind):
    with pytest.raises(ActorAuthorizationError):
        authorize_event_type(event_type, actor_kind)


@pytest.mark.parametrize(
    ("event_type", "actor_kind", "error_code"),
    [
        ("writer_claimed_pass", "writer", "unknown_event_type"),
        ("step_started", "administrator", "unknown_actor_kind"),
    ],
)
def test_unknown_event_or_actor_is_rejected_instead_of_defaulting_allow(
    event_type,
    actor_kind,
    error_code,
):
    with pytest.raises(ActorAuthorizationError) as exc_info:
        authorize_event_type(event_type, actor_kind)

    assert exc_info.value.code == error_code


def test_allowed_actors_returns_immutable_policy_view():
    actors = allowed_actors(EventType.TASK_CREATED)

    assert actors == frozenset(EXPECTED_POLICY[EventType.TASK_CREATED])
    with pytest.raises(AttributeError):
        actors.add(ActorKind.CI_GATE)
