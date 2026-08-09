"""Stable command-line boundary for workflow-state core operations."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

from pydantic import ValidationError

from .canonical import event_hash
from .git_store import GitStateStore, StateSnapshot, StateStoreError
from .models import ActorKind, EventType, TaskEvent, WorkflowPhase
from .observers import command_digest, observe_test, resolve_commit
from .projector import render_projection_files, validate_projection_files
from .reducer import ReducerError, reduce_events


EXIT_OK = 0
EXIT_INVALID = 1
EXIT_BLOCKED = 2
EXIT_USAGE = 3
EXIT_CONFLICT = 4

_MODES = ("full-6", "fix-mini", "refactor-6", "timebox")
_STEP_PHASES = {
    0: WorkflowPhase.RESEARCH,
    1: WorkflowPhase.SPEC,
    2: WorkflowPhase.PLAN,
    3: WorkflowPhase.TASKS,
    4: WorkflowPhase.IMPLEMENTATION,
    5: WorkflowPhase.VERIFICATION,
    6: WorkflowPhase.RETRO,
}


class TaskctlParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"taskctl: error: {message}\n")


def _parser() -> TaskctlParser:
    parser = TaskctlParser(prog="taskctl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init = subcommands.add_parser("init")
    init.add_argument("--task", required=True)
    init.add_argument("--mode", required=True, choices=_MODES)

    start = subcommands.add_parser("start")
    start.add_argument("--task", required=True)
    start.add_argument("--step", required=True, type=int, choices=range(0, 7))

    show = subcommands.add_parser("show")
    show.add_argument("--task", required=True)
    show.add_argument("--format", choices=("json", "yaml", "markdown"), default="json")

    observe_commit = subcommands.add_parser("observe-commit")
    observe_commit.add_argument("--task", required=True)
    observe_commit.add_argument("--commit", required=True)

    run_test = subcommands.add_parser("run-test")
    run_test.add_argument("--task", required=True)
    run_test.add_argument("--commit", required=True)
    run_test.add_argument("argv", nargs=argparse.REMAINDER)

    for name in ("project", "check"):
        command = subcommands.add_parser(name)
        selector = command.add_mutually_exclusive_group(required=True)
        selector.add_argument("--task")
        selector.add_argument("--all", action="store_true")

    return parser


def _json_output(value: object, *, stream=sys.stdout) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _writer_identity(store: GitStateStore) -> str:
    result = store._run(["config", "--get", "user.email"])
    identity = result.stdout.decode("utf-8").strip()
    if result.returncode != 0 or not identity:
        raise StateStoreError(
            "writer_identity_unavailable",
            "Git user.email is required for local writer identity",
            blocked=True,
        )
    return identity


def _event(
    *,
    task_id: str,
    sequence: int,
    event_id: str,
    idempotency_key: str,
    event_type: EventType,
    writer_identity: str,
    payload: Dict[str, object],
    previous_hash: str = None,
) -> TaskEvent:
    return TaskEvent.model_validate(
        {
            "schema_version": "task-event/v1",
            "event_id": event_id,
            "idempotency_key": idempotency_key,
            "task_id": task_id,
            "sequence": sequence,
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc),
            "actor": {"kind": ActorKind.WRITER, "id": writer_identity},
            "subject": {},
            "payload": payload,
            "previous_event_hash": previous_hash,
        }
    )


def _observer_event(
    *,
    task_id: str,
    sequence: int,
    event_id: str,
    idempotency_key: str,
    event_type: EventType,
    actor_kind: ActorKind,
    actor_id: str,
    commit: str,
    payload: Dict[str, object],
    previous_hash: str,
) -> TaskEvent:
    return TaskEvent.model_validate(
        {
            "schema_version": "task-event/v1",
            "event_id": event_id,
            "idempotency_key": idempotency_key,
            "task_id": task_id,
            "sequence": sequence,
            "event_type": event_type,
            "occurred_at": datetime.now(timezone.utc),
            "actor": {"kind": actor_kind, "id": actor_id},
            "subject": {"commit": commit},
            "payload": payload,
            "previous_event_hash": previous_hash,
        }
    )


def _task_events(
    store: GitStateStore,
    snapshot: StateSnapshot,
    task_id: str,
) -> List[TaskEvent]:
    store._safe_identifier(task_id, "task_id")
    events = store._existing_events(snapshot, task_id)
    if not events:
        raise StateStoreError("task_not_found", f"task {task_id!r} does not exist")
    store._validate_existing_projection(snapshot, task_id, events)
    return events


def _task_ids(snapshot: StateSnapshot) -> List[str]:
    suffix = "/projection/task.json"
    task_ids = {
        path[len("tasks/") : -len(suffix)]
        for path in snapshot.files
        if path.startswith("tasks/") and path.endswith(suffix)
    }
    return sorted(task_ids)


def _selected_tasks(snapshot: StateSnapshot, args: argparse.Namespace) -> List[str]:
    return _task_ids(snapshot) if args.all else [args.task]


def _init(store: GitStateStore, args: argparse.Namespace) -> None:
    writer_identity = _writer_identity(store)
    store.bootstrap()
    snapshot = store.load_snapshot()
    if store._existing_events(snapshot, args.task):
        raise StateStoreError("task_already_exists", f"task {args.task!r} already exists")
    event = _event(
        task_id=args.task,
        sequence=1,
        event_id="task-created",
        idempotency_key=f"task:{args.task}:created",
        event_type=EventType.TASK_CREATED,
        writer_identity=writer_identity,
        payload={"mode": args.mode},
    )
    result = store.append_event(event)
    _json_output(
        {
            "event_type": event.event_type.value,
            "source_sequence": result.projection.source_sequence,
            "task_id": args.task,
        }
    )


def _start(store: GitStateStore, args: argparse.Namespace) -> None:
    snapshot = store.load_snapshot()
    events = _task_events(store, snapshot, args.task)
    sequence = len(events) + 1
    phase = _STEP_PHASES[args.step]
    event = _event(
        task_id=args.task,
        sequence=sequence,
        event_id=f"step-{args.step}-started",
        idempotency_key=f"task:{args.task}:step:{args.step}:start",
        event_type=EventType.STEP_STARTED,
        writer_identity=_writer_identity(store),
        payload={"phase": phase.value, "step": args.step},
        previous_hash=event_hash(events[-1]),
    )
    result = store.append_event(event)
    _json_output(
        {
            "event_type": event.event_type.value,
            "source_sequence": result.projection.source_sequence,
            "task_id": args.task,
            "workflow_phase": result.projection.workflow_phase.value,
        }
    )


def _show(store: GitStateStore, args: argparse.Namespace) -> None:
    snapshot = store.load_snapshot()
    _task_events(store, snapshot, args.task)
    filename = {
        "json": "task.json",
        "yaml": "task.yaml",
        "markdown": "tasks-status.md",
    }[args.format]
    path = f"tasks/{args.task}/projection/{filename}"
    sys.stdout.buffer.write(snapshot.files[path])


def _observe_commit(store: GitStateStore, args: argparse.Namespace) -> None:
    snapshot = store.load_snapshot()
    events = _task_events(store, snapshot, args.task)
    commit = resolve_commit(store, args.commit)
    event = _observer_event(
        task_id=args.task,
        sequence=len(events) + 1,
        event_id=f"implementation-{commit[:12]}",
        idempotency_key=(
            "implementation-observation:"
            + command_digest([args.task, commit])
        ),
        event_type=EventType.IMPLEMENTATION_COMMITTED,
        actor_kind=ActorKind.GIT_OBSERVER,
        actor_id="taskctl:git-object-observer",
        commit=commit,
        payload={"verification": "git cat-file -e <sha>^{commit}"},
        previous_hash=event_hash(events[-1]),
    )
    result = store.append_event(event)
    _json_output(
        {
            "commit": commit,
            "event_type": event.event_type.value,
            "source_sequence": result.projection.source_sequence,
            "task_id": args.task,
        }
    )


def _run_test(store: GitStateStore, args: argparse.Namespace) -> None:
    snapshot = store.load_snapshot()
    events = _task_events(store, snapshot, args.task)
    commit = resolve_commit(store, args.commit)
    projection = reduce_events(events)
    if projection.active_commit != commit:
        raise StateStoreError(
            "active_commit_mismatch",
            f"test commit {commit} is not active implementation {projection.active_commit}",
        )
    argv = list(args.argv)
    if argv[:1] == ["--"]:
        argv = argv[1:]
    observation = observe_test(store.repository, argv)
    digest = command_digest(observation.command)
    sequence = len(events) + 1
    event = _observer_event(
        task_id=args.task,
        sequence=sequence,
        event_id=f"tests-{sequence:06d}-{digest[:8]}",
        idempotency_key=(
            "test-observation:"
            + command_digest([args.task, commit, str(sequence), digest])
        ),
        event_type=EventType.TESTS_OBSERVED,
        actor_kind=ActorKind.TEST_RUNNER,
        actor_id="taskctl:direct-test-runner",
        commit=commit,
        payload=observation.payload(),
        previous_hash=event_hash(events[-1]),
    )
    result = store.append_event(event)
    _json_output(
        {
            "event_type": event.event_type.value,
            "result": observation.result,
            "source_sequence": result.projection.source_sequence,
            "task_id": args.task,
            "test_command_rc": observation.exit_code,
        }
    )


def _project(store: GitStateStore, args: argparse.Namespace) -> None:
    snapshot = store.load_snapshot()
    rendered = {}
    for task_id in _selected_tasks(snapshot, args):
        events = _task_events(store, snapshot, task_id)
        files = render_projection_files(reduce_events(events))
        value = {name: content.decode("utf-8") for name, content in files.items()}
        if args.all:
            rendered[task_id] = value
        else:
            rendered = value
    _json_output(rendered)


def _check(store: GitStateStore, args: argparse.Namespace) -> None:
    snapshot = store.load_snapshot()
    task_ids = _selected_tasks(snapshot, args)
    for task_id in task_ids:
        events = _task_events(store, snapshot, task_id)
        projection = reduce_events(events)
        prefix = f"tasks/{task_id}/projection/"
        actual = {
            path[len(prefix) :]: content
            for path, content in snapshot.files.items()
            if path.startswith(prefix)
        }
        validate_projection_files(projection, actual)
    output = {"status": "PASS", "tasks": task_ids}
    _json_output(output)


def run(argv: Sequence[str] = None, *, repository: Path = None) -> int:
    args = _parser().parse_args(argv)
    repo = (repository or Path.cwd()).resolve()
    store = GitStateStore(repo)
    handlers = {
        "init": lambda: _init(store, args),
        "start": lambda: _start(store, args),
        "show": lambda: _show(store, args),
        "observe-commit": lambda: _observe_commit(store, args),
        "run-test": lambda: _run_test(store, args),
        "project": lambda: _project(store, args),
        "check": lambda: _check(store, args),
    }
    try:
        handlers[args.command]()
        return EXIT_OK
    except StateStoreError as error:
        if error.code in {"retry_exhausted", "concurrent_update"}:
            exit_code = EXIT_CONFLICT
        elif error.blocked or error.code in {
            "state_ref_missing",
            "not_git_repository",
            "lock_unavailable",
        }:
            exit_code = EXIT_BLOCKED
        else:
            exit_code = EXIT_INVALID
        _json_output(
            {
                "code": error.code,
                "message": str(error),
                "status": "BLOCKED" if exit_code in {EXIT_BLOCKED, EXIT_CONFLICT} else "FAIL",
            },
            stream=sys.stderr,
        )
        return exit_code
    except (ReducerError, ValidationError, ValueError, KeyError) as error:
        _json_output(
            {"code": "invalid_state", "message": str(error), "status": "FAIL"},
            stream=sys.stderr,
        )
        return EXIT_INVALID


def main() -> None:
    raise SystemExit(run())
