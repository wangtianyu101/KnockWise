"""Behavior tests for canonical workflow-event hashing and history integrity."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Dict, Optional

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.canonical import (  # noqa: E402
    ChainValidationError,
    assert_history_prefix,
    canonical_json,
    event_hash,
    validate_event_chain,
)
from scripts.workflow_state.models import ActorKind, EventType, TaskEvent  # noqa: E402


def _event(
    *,
    sequence: int = 1,
    event_id: str = "evt-001",
    idempotency_key: str = "create",
    previous_event_hash: Optional[str] = None,
    payload: Optional[Dict] = None,
    task_id: str = "2026-07-30-example",
) -> TaskEvent:
    return TaskEvent.model_validate(
        {
            "schema_version": "task-event/v1",
            "event_id": event_id,
            "idempotency_key": idempotency_key,
            "task_id": task_id,
            "sequence": sequence,
            "event_type": EventType.TASK_CREATED
            if sequence == 1
            else EventType.STEP_STARTED,
            "occurred_at": "2026-07-30T04:00:00Z",
            "actor": {"kind": ActorKind.WRITER, "id": "codex-local"},
            "subject": {},
            "payload": payload or {},
            "previous_event_hash": previous_event_hash,
        }
    )


def _append(previous: TaskEvent, **overrides) -> TaskEvent:
    return _event(
        sequence=previous.sequence + 1,
        event_id=f"evt-{previous.sequence + 1:03d}",
        idempotency_key=f"step-{previous.sequence + 1}",
        previous_event_hash=event_hash(previous),
        **overrides,
    )


def test_canonical_json_is_stable_utf8_compact_and_key_sorted():
    first = _event(payload={"z": "中文", "a": {"y": 2, "x": 1}})
    second = _event(payload={"a": {"x": 1, "y": 2}, "z": "中文"})

    encoded = canonical_json(first)

    assert encoded == canonical_json(second)
    assert b" " not in encoded
    assert "\\u4e2d" not in encoded.decode("utf-8")
    assert encoded.decode("utf-8").index('"a"') < encoded.decode("utf-8").index('"z"')


def test_event_hash_is_prefixed_sha256_of_canonical_bytes():
    event = _event(payload={"answer": 42})

    expected = hashlib.sha256(canonical_json(event)).hexdigest()

    assert event_hash(event) == f"sha256:{expected}"


def test_validate_event_chain_accepts_contiguous_linked_events():
    first = _event()
    second = _append(first)
    third = _append(second)

    result = validate_event_chain([first, second, third])

    assert result.task_id == first.task_id
    assert result.last_sequence == 3
    assert result.last_hash == event_hash(third)
    assert result.event_count == 3


@pytest.mark.parametrize(
    ("mutate", "error_code"),
    [
        (lambda first, second: [second], "first_sequence"),
        (
            lambda first, second: [
                first,
                second.model_copy(update={"sequence": 3}),
            ],
            "sequence_gap",
        ),
        (
            lambda first, second: [
                first,
                second.model_copy(update={"previous_event_hash": "sha256:" + "0" * 64}),
            ],
            "previous_hash_mismatch",
        ),
        (
            lambda first, second: [
                first,
                second.model_copy(update={"task_id": "another-task"}),
            ],
            "task_id_mismatch",
        ),
        (
            lambda first, second: [
                first,
                second.model_copy(update={"event_id": first.event_id}),
            ],
            "duplicate_event_id",
        ),
        (
            lambda first, second: [
                first,
                second.model_copy(update={"idempotency_key": first.idempotency_key}),
            ],
            "duplicate_idempotency_key",
        ),
    ],
)
def test_validate_event_chain_rejects_integrity_violations(mutate, error_code):
    first = _event()
    second = _append(first)

    with pytest.raises(ChainValidationError) as exc_info:
        validate_event_chain(mutate(first, second))

    assert exc_info.value.code == error_code


def test_validate_event_chain_rejects_empty_history():
    with pytest.raises(ChainValidationError) as exc_info:
        validate_event_chain([])

    assert exc_info.value.code == "empty_chain"


def test_assert_history_prefix_allows_append_without_rewriting_existing_events():
    first = _event()
    second = _append(first)
    third = _append(second)

    assert_history_prefix([first, second], [first, second, third])


def test_assert_history_prefix_allows_initial_creation_from_empty_history():
    first = _event()

    assert_history_prefix([], [first])


@pytest.mark.parametrize("candidate_kind", ["deleted", "rewritten"])
def test_assert_history_prefix_rejects_deletion_or_overwrite(candidate_kind):
    first = _event()
    second = _append(first)
    existing = [first, second]
    if candidate_kind == "deleted":
        candidate = [first]
    else:
        rewritten = second.model_copy(update={"payload": {"rewritten": True}})
        candidate = [first, rewritten]

    with pytest.raises(ChainValidationError) as exc_info:
        assert_history_prefix(existing, candidate)

    assert exc_info.value.code == f"history_{candidate_kind}"
