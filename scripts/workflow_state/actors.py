"""Fail-closed actor authorization for workflow event types.

The ``actor_kind`` accepted by this module must come from a trusted adapter.
The event JSON's self-declared ``actor.kind`` is data, not authentication.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, FrozenSet, Mapping

from .models import ActorKind, EventType


_POLICY = {
    EventType.TASK_CREATED: frozenset(
        {ActorKind.USER, ActorKind.WRITER, ActorKind.MIGRATION}
    ),
    EventType.SCOPE_CONFIRMED: frozenset(
        {ActorKind.USER, ActorKind.MIGRATION}
    ),
    EventType.STEP_STARTED: frozenset(
        {ActorKind.USER, ActorKind.WRITER, ActorKind.MIGRATION}
    ),
    EventType.STEP_ACCEPTED: frozenset({ActorKind.USER}),
    EventType.IMPLEMENTATION_COMMITTED: frozenset(
        {ActorKind.GIT_OBSERVER, ActorKind.MIGRATION}
    ),
    EventType.TESTS_OBSERVED: frozenset(
        {ActorKind.TEST_RUNNER, ActorKind.MIGRATION}
    ),
    EventType.VERIFIER_OBSERVED: frozenset(
        {ActorKind.VERIFIER, ActorKind.MIGRATION}
    ),
    EventType.PHASE_ACCEPTED: frozenset({ActorKind.USER}),
    EventType.MERGE_GATE_OBSERVED: frozenset(
        {ActorKind.CI_GATE, ActorKind.MIGRATION}
    ),
    EventType.LEGACY_SNAPSHOT_IMPORTED: frozenset({ActorKind.MIGRATION}),
}

ACTOR_EVENT_POLICY: Mapping[EventType, FrozenSet[ActorKind]] = MappingProxyType(
    _POLICY
)


class ActorAuthorizationError(PermissionError):
    """Stable authorization failure without interpreting untrusted payload."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        event_type: Any = None,
        actor_kind: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.event_type = event_type
        self.actor_kind = actor_kind


def _event_type(value: Any) -> EventType:
    try:
        return value if isinstance(value, EventType) else EventType(value)
    except (TypeError, ValueError) as exc:
        raise ActorAuthorizationError(
            "unknown_event_type",
            f"unknown event type: {value!r}",
            event_type=value,
        ) from exc


def _actor_kind(value: Any) -> ActorKind:
    try:
        return value if isinstance(value, ActorKind) else ActorKind(value)
    except (TypeError, ValueError) as exc:
        raise ActorAuthorizationError(
            "unknown_actor_kind",
            f"unknown actor kind: {value!r}",
            actor_kind=value,
        ) from exc


def allowed_actors(event_type: Any) -> FrozenSet[ActorKind]:
    """Return the immutable allowlist for one known event type."""

    normalized_event = _event_type(event_type)
    return ACTOR_EVENT_POLICY[normalized_event]


def is_actor_allowed(event_type: Any, actor_kind: Any) -> bool:
    """Return False for denied or unknown input; never default to allow."""

    try:
        normalized_event = _event_type(event_type)
        normalized_actor = _actor_kind(actor_kind)
    except ActorAuthorizationError:
        return False
    return normalized_actor in ACTOR_EVENT_POLICY[normalized_event]


def authorize_event_type(event_type: Any, trusted_actor_kind: Any) -> None:
    """Authorize an event using actor identity resolved outside event payload."""

    normalized_event = _event_type(event_type)
    normalized_actor = _actor_kind(trusted_actor_kind)
    if normalized_actor not in ACTOR_EVENT_POLICY[normalized_event]:
        raise ActorAuthorizationError(
            "actor_not_allowed",
            (
                f"actor {normalized_actor.value!r} cannot write "
                f"event {normalized_event.value!r}"
            ),
            event_type=normalized_event,
            actor_kind=normalized_actor,
        )
