"""Deterministic event encoding and immutable hash-chain validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, Sequence

from pydantic import BaseModel

from .models import TaskEvent


class ChainValidationError(ValueError):
    """A stable, machine-readable workflow history integrity failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ChainValidationResult:
    task_id: str
    event_count: int
    last_sequence: int
    last_hash: str


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError("canonical_json requires a Pydantic model or mapping")


def canonical_json(value: Any) -> bytes:
    """Return compact, sorted UTF-8 JSON bytes for hashing and persistence."""

    return json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def event_hash(event: TaskEvent) -> str:
    """Return the versioned digest used by the next event in the chain."""

    return "sha256:" + hashlib.sha256(canonical_json(event)).hexdigest()


def _as_events(events: Iterable[TaskEvent]) -> List[TaskEvent]:
    return [
        event if isinstance(event, TaskEvent) else TaskEvent.model_validate(event)
        for event in events
    ]


def validate_event_chain(events: Sequence[TaskEvent]) -> ChainValidationResult:
    """Validate one task's complete, contiguous, append-only event chain."""

    ordered = _as_events(events)
    if not ordered:
        raise ChainValidationError("empty_chain", "event chain must not be empty")

    first = ordered[0]
    if first.sequence != 1:
        raise ChainValidationError(
            "first_sequence",
            f"first event sequence must be 1, got {first.sequence}",
        )
    if first.previous_event_hash is not None:
        raise ChainValidationError(
            "first_previous_hash",
            "first event must not reference a previous hash",
        )

    task_id = first.task_id
    seen_event_ids = set()
    seen_idempotency_keys = set()
    previous_hash = None

    for expected_sequence, event in enumerate(ordered, start=1):
        if event.sequence != expected_sequence:
            raise ChainValidationError(
                "sequence_gap",
                f"expected sequence {expected_sequence}, got {event.sequence}",
            )
        if event.task_id != task_id:
            raise ChainValidationError(
                "task_id_mismatch",
                f"event {event.sequence} belongs to {event.task_id}, expected {task_id}",
            )
        if event.event_id in seen_event_ids:
            raise ChainValidationError(
                "duplicate_event_id",
                f"event_id {event.event_id!r} occurs more than once",
            )
        if event.idempotency_key in seen_idempotency_keys:
            raise ChainValidationError(
                "duplicate_idempotency_key",
                f"idempotency_key {event.idempotency_key!r} occurs more than once",
            )
        if event.previous_event_hash != previous_hash:
            raise ChainValidationError(
                "previous_hash_mismatch",
                f"event {event.sequence} does not reference the prior canonical hash",
            )

        seen_event_ids.add(event.event_id)
        seen_idempotency_keys.add(event.idempotency_key)
        previous_hash = event_hash(event)

    return ChainValidationResult(
        task_id=task_id,
        event_count=len(ordered),
        last_sequence=ordered[-1].sequence,
        last_hash=previous_hash,
    )


def assert_history_prefix(
    existing: Sequence[TaskEvent],
    candidate: Sequence[TaskEvent],
) -> None:
    """Reject deletion or rewriting of already-persisted history."""

    old_events = _as_events(existing)
    new_events = _as_events(candidate)
    validate_event_chain(new_events)
    if not old_events:
        return
    validate_event_chain(old_events)

    if len(new_events) < len(old_events):
        raise ChainValidationError(
            "history_deleted",
            "candidate history deletes one or more existing events",
        )

    for index, old_event in enumerate(old_events):
        if canonical_json(old_event) != canonical_json(new_events[index]):
            raise ChainValidationError(
                "history_rewritten",
                f"candidate rewrites existing event at sequence {index + 1}",
            )
