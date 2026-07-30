"""Typed contracts for immutable workflow events and derived projections."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


COMMIT_PATTERN = r"^[0-9a-f]{40}$"
SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"


class EventType(str, Enum):
    TASK_CREATED = "task_created"
    SCOPE_CONFIRMED = "scope_confirmed"
    STEP_STARTED = "step_started"
    STEP_ACCEPTED = "step_accepted"
    IMPLEMENTATION_COMMITTED = "implementation_committed"
    TESTS_OBSERVED = "tests_observed"
    VERIFIER_OBSERVED = "verifier_observed"
    PHASE_ACCEPTED = "phase_accepted"
    MERGE_GATE_OBSERVED = "merge_gate_observed"
    LEGACY_SNAPSHOT_IMPORTED = "legacy_snapshot_imported"


class ActorKind(str, Enum):
    USER = "user"
    WRITER = "writer"
    GIT_OBSERVER = "git_observer"
    TEST_RUNNER = "test_runner"
    VERIFIER = "verifier"
    CI_GATE = "ci_gate"
    MIGRATION = "migration"


class WorkflowPhase(str, Enum):
    RESEARCH = "research"
    SPEC = "spec"
    PLAN = "plan"
    TASKS = "tasks"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    RETRO = "retro"


class EvidenceState(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    STALE = "STALE"


class AcceptanceState(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class LegacyTrust(str, Enum):
    NATIVE = "NATIVE"
    LEGACY_UNVERIFIED = "LEGACY_UNVERIFIED"


class StrictModel(BaseModel):
    """Fail closed when a producer sends fields outside the versioned schema."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class EventActor(StrictModel):
    kind: ActorKind
    id: str = Field(min_length=1, max_length=200)

    @field_validator("id")
    @classmethod
    def identity_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("actor id must not be blank")
        return value


class EventSubject(StrictModel):
    commit: Optional[str] = Field(default=None, pattern=COMMIT_PATTERN)
    spec_hash: Optional[str] = Field(default=None, pattern=SHA256_PATTERN)


class TaskEvent(StrictModel):
    schema_version: Literal["task-event/v1"]
    event_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=1, max_length=200)
    task_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=1)
    event_type: EventType
    occurred_at: datetime
    actor: EventActor
    subject: EventSubject
    payload: Dict[str, Any]
    previous_event_hash: Optional[str] = Field(
        default=None,
        pattern=SHA256_PATTERN,
    )

    @field_validator("event_id", "idempotency_key", "task_id")
    @classmethod
    def identifiers_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identifier must not be blank")
        return value

    @field_validator("occurred_at")
    @classmethod
    def timestamp_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include an explicit timezone")
        return value


class TaskProjection(StrictModel):
    schema_version: Literal["task-projection/v1"]
    task_id: str = Field(min_length=1, max_length=200)
    source_sequence: int = Field(ge=1)
    source_hash: str = Field(pattern=SHA256_PATTERN)
    workflow_phase: WorkflowPhase
    implementation_state: EvidenceState
    test_state: EvidenceState
    verifier_state: EvidenceState
    acceptance_state: AcceptanceState
    merge_gate_state: EvidenceState
    active_commit: Optional[str] = Field(default=None, pattern=COMMIT_PATTERN)
    active_spec_hash: Optional[str] = Field(default=None, pattern=SHA256_PATTERN)
    legacy_trust: LegacyTrust

    @field_validator("task_id")
    @classmethod
    def task_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task_id must not be blank")
        return value
