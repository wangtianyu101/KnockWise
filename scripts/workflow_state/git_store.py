"""Read-only Git storage primitives for the workflow-state control plane."""

from __future__ import annotations

import fcntl
import json
import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Iterator, List, Mapping, Optional, Sequence

from .canonical import canonical_json, validate_event_chain
from .models import TaskEvent, TaskProjection
from .projector import (
    PROJECTION_FILENAMES,
    ProjectionDriftError,
    render_projection_files,
    validate_projection_files,
)
from .reducer import reduce_events


STATE_REF = "refs/heads/workflow-state"
FORMAT_CONTENT = b"workflow-state/v1\n"
_ZERO_OID = "0" * 40
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_GIT_LOCAL_ENV_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_DIR",
    "GIT_GRAFT_FILE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_WORK_TREE",
}


class StateStoreError(RuntimeError):
    """A stable fail-closed state-store failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class StateSnapshot:
    commit: str
    files: Mapping[str, bytes]


@dataclass(frozen=True)
class AppendResult:
    old_commit: str
    new_commit: str
    event_path: str
    projection: TaskProjection


class GitStateStore:
    """Access the isolated workflow-state ref without switching business HEAD."""

    def __init__(self, repository: Path) -> None:
        self.repository = Path(repository).resolve()

    def _run(
        self,
        args: Sequence[str],
        *,
        input_bytes: Optional[bytes] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        environment = os.environ.copy()
        for key in _GIT_LOCAL_ENV_KEYS:
            environment.pop(key, None)
        if env is not None:
            environment.update(env)
        return subprocess.run(
            ["git", *args],
            cwd=self.repository,
            input=input_bytes,
            capture_output=True,
            env=environment,
        )

    def _ensure_repository(self) -> None:
        result = self._run(["rev-parse", "--is-inside-work-tree"])
        if result.returncode != 0 or result.stdout.strip() != b"true":
            raise StateStoreError(
                "not_git_repository",
                f"{self.repository} is not a Git worktree",
            )

    def _ref_commit(self) -> str:
        result = self._run(["rev-parse", "--verify", f"{STATE_REF}^{{commit}}"])
        if result.returncode != 0:
            raise StateStoreError(
                "state_ref_missing",
                f"required state ref {STATE_REF} does not exist",
            )
        return result.stdout.decode("ascii").strip()

    def _validate_format(self, commit: str) -> None:
        result = self._run(["show", f"{commit}:FORMAT"])
        if result.returncode != 0:
            raise StateStoreError(
                "format_missing",
                f"{STATE_REF} commit {commit} has no FORMAT file",
            )
        if result.stdout != FORMAT_CONTENT:
            raise StateStoreError(
                "format_unsupported",
                "workflow-state FORMAT is not exactly workflow-state/v1",
            )

    def bootstrap(self) -> str:
        """Create the orphan state ref once, or validate the existing ref."""

        self._ensure_repository()
        try:
            existing = self._ref_commit()
        except StateStoreError as error:
            if error.code != "state_ref_missing":
                raise
        else:
            self._validate_format(existing)
            return existing

        blob_result = self._run(["hash-object", "-w", "--stdin"], input_bytes=FORMAT_CONTENT)
        if blob_result.returncode != 0:
            raise StateStoreError("bootstrap_failed", "could not write FORMAT blob")
        blob = blob_result.stdout.decode("ascii").strip()

        tree_entry = f"100644 blob {blob}\tFORMAT\n".encode("ascii")
        tree_result = self._run(["mktree"], input_bytes=tree_entry)
        if tree_result.returncode != 0:
            raise StateStoreError("bootstrap_failed", "could not create state tree")
        tree = tree_result.stdout.decode("ascii").strip()

        commit_result = self._run(
            ["commit-tree", tree],
            input_bytes=b"Initialize workflow-state format\n",
            env=self._commit_identity_environment(),
        )
        if commit_result.returncode != 0:
            raise StateStoreError(
                "bootstrap_failed",
                "could not create initial state commit",
            )
        commit = commit_result.stdout.decode("ascii").strip()

        update_result = self._run(["update-ref", STATE_REF, commit, _ZERO_OID])
        if update_result.returncode != 0:
            # A concurrent initializer may have won. Its result is authoritative
            # only after the same fail-closed format validation.
            existing = self._ref_commit()
            self._validate_format(existing)
            return existing

        self._validate_format(commit)
        return commit

    @staticmethod
    def _commit_identity_environment() -> Mapping[str, str]:
        return {
            "GIT_AUTHOR_NAME": os.environ.get("GIT_AUTHOR_NAME", "taskctl"),
            "GIT_AUTHOR_EMAIL": os.environ.get(
                "GIT_AUTHOR_EMAIL",
                "taskctl@localhost",
            ),
            "GIT_COMMITTER_NAME": os.environ.get("GIT_COMMITTER_NAME", "taskctl"),
            "GIT_COMMITTER_EMAIL": os.environ.get(
                "GIT_COMMITTER_EMAIL",
                "taskctl@localhost",
            ),
        }

    def load_snapshot(self) -> StateSnapshot:
        """Read every state file from the ref without checking it out."""

        self._ensure_repository()
        commit = self._ref_commit()
        self._validate_format(commit)
        tree_result = self._run(["ls-tree", "-r", "-z", "--name-only", commit])
        if tree_result.returncode != 0:
            raise StateStoreError("state_read_failed", "could not list state tree")

        files: Dict[str, bytes] = {}
        for raw_path in tree_result.stdout.split(b"\0"):
            if not raw_path:
                continue
            try:
                path = raw_path.decode("utf-8")
            except UnicodeDecodeError as error:
                raise StateStoreError(
                    "path_encoding_invalid",
                    "state tree contains a non-UTF-8 path",
                ) from error
            blob_result = self._run(["show", f"{commit}:{path}"])
            if blob_result.returncode != 0:
                raise StateStoreError(
                    "state_read_failed",
                    f"could not read state path {path!r}",
                )
            files[path] = blob_result.stdout

        return StateSnapshot(commit=commit, files=MappingProxyType(files))

    @contextmanager
    def temporary_worktree(self, commit: Optional[str] = None) -> Iterator[Path]:
        """Yield a detached state checkout and remove it on every exit path."""

        self._ensure_repository()
        selected_commit = commit or self._ref_commit()
        self._validate_format(selected_commit)
        temp_root = Path(tempfile.mkdtemp(prefix="taskctl-worktree-"))
        worktree = temp_root / "checkout"
        added = False
        try:
            result = self._run(
                [
                    "worktree",
                    "add",
                    "--detach",
                    "--quiet",
                    str(worktree),
                    selected_commit,
                ]
            )
            if result.returncode != 0:
                raise StateStoreError(
                    "worktree_create_failed",
                    "could not create detached state worktree",
                )
            added = True
            yield worktree
        finally:
            if added:
                self._run(["worktree", "remove", "--force", str(worktree)])
            shutil.rmtree(temp_root, ignore_errors=True)

    def _lock_path(self) -> Path:
        result = self._run(["rev-parse", "--git-common-dir"])
        if result.returncode != 0:
            raise StateStoreError("lock_unavailable", "could not locate Git common dir")
        common_dir = Path(result.stdout.decode("utf-8").strip())
        if not common_dir.is_absolute():
            common_dir = self.repository / common_dir
        return common_dir.resolve() / "taskctl.lock"

    @contextmanager
    def _state_lock(self) -> Iterator[None]:
        try:
            lock_file = self._lock_path().open("a+b")
        except OSError as error:
            raise StateStoreError(
                "lock_unavailable",
                "could not open taskctl state lock",
            ) from error
        with lock_file:
            try:
                fcntl.flock(
                    lock_file.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            except BlockingIOError as error:
                raise StateStoreError(
                    "lock_unavailable",
                    "another local taskctl writer holds the state lock",
                ) from error
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _safe_identifier(value: str, field: str) -> None:
        if _SAFE_IDENTIFIER.fullmatch(value) is None:
            raise StateStoreError(
                "unsafe_path_identifier",
                f"{field} is not safe for a state-tree path",
            )

    @staticmethod
    def _event_path(event: TaskEvent) -> str:
        return (
            f"tasks/{event.task_id}/events/"
            f"{event.sequence:06d}-{event.event_id}.json"
        )

    def _existing_events(
        self,
        snapshot: StateSnapshot,
        task_id: str,
    ) -> List[TaskEvent]:
        prefix = f"tasks/{task_id}/events/"
        candidates = sorted(
            path
            for path in snapshot.files
            if path.startswith(prefix) and path.endswith(".json")
        )
        events = []
        for path in candidates:
            try:
                raw = json.loads(snapshot.files[path])
                event = TaskEvent.model_validate(raw)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                raise StateStoreError(
                    "event_history_invalid",
                    f"could not validate persisted event {path}",
                ) from error
            expected_path = self._event_path(event)
            if path != expected_path:
                raise StateStoreError(
                    "event_filename_mismatch",
                    f"persisted event path {path!r} should be {expected_path!r}",
                )
            events.append(event)
        if events:
            try:
                validate_event_chain(events)
            except ValueError as error:
                raise StateStoreError(
                    "event_history_invalid",
                    "persisted event chain failed validation",
                ) from error
        return events

    def _validate_existing_projection(
        self,
        snapshot: StateSnapshot,
        task_id: str,
        events: Sequence[TaskEvent],
    ) -> None:
        prefix = f"tasks/{task_id}/projection/"
        actual = {
            path[len(prefix) :]: content
            for path, content in snapshot.files.items()
            if path.startswith(prefix)
        }
        if not events:
            if actual:
                raise StateStoreError(
                    "projection_drift",
                    "projection exists without an event history",
                )
            return
        expected_projection = reduce_events(events)
        try:
            validate_projection_files(expected_projection, actual)
        except ProjectionDriftError as error:
            raise StateStoreError(
                "projection_drift",
                f"persisted projection failed validation: {error.code}",
            ) from error

    def _compare_and_swap(self, old_commit: str, new_commit: str) -> bool:
        result = self._run(
            ["update-ref", STATE_REF, new_commit, old_commit],
        )
        return result.returncode == 0

    def append_event(self, event: TaskEvent) -> AppendResult:
        """Atomically append one validated event and its derived projection.

        Actor authentication belongs to the trusted adapter boundary. This
        storage method validates structure/history but never treats the
        event's self-declared actor as authentication.
        """

        validated = (
            event
            if isinstance(event, TaskEvent)
            else TaskEvent.model_validate(event)
        )
        self._safe_identifier(validated.task_id, "task_id")
        self._safe_identifier(validated.event_id, "event_id")
        with self._state_lock():
            snapshot = self.load_snapshot()
            existing = self._existing_events(snapshot, validated.task_id)
            self._validate_existing_projection(
                snapshot,
                validated.task_id,
                existing,
            )
            candidate = [*existing, validated]
            projection = reduce_events(candidate)
            event_path = self._event_path(validated)
            task_root = f"tasks/{validated.task_id}"

            with self.temporary_worktree(snapshot.commit) as worktree:
                target = worktree / event_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(canonical_json(validated) + b"\n")
                projection_root = worktree / task_root / "projection"
                projection_root.mkdir(parents=True, exist_ok=True)
                for filename, content in render_projection_files(projection).items():
                    (projection_root / filename).write_bytes(content)

                add_result = self._run(
                    ["-C", str(worktree), "add", "--", task_root],
                )
                if add_result.returncode != 0:
                    raise StateStoreError(
                        "state_commit_failed",
                        "could not stage event and projection",
                    )
                commit_result = self._run(
                    [
                        "-C",
                        str(worktree),
                        "commit",
                        "--quiet",
                        "-m",
                        (
                            f"workflow-state: {validated.task_id} "
                            f"event {validated.sequence}"
                        ),
                    ],
                    env=self._commit_identity_environment(),
                )
                if commit_result.returncode != 0:
                    raise StateStoreError(
                        "state_commit_failed",
                        "could not commit event and projection",
                    )
                new_result = self._run(
                    ["-C", str(worktree), "rev-parse", "HEAD"],
                )
                if new_result.returncode != 0:
                    raise StateStoreError(
                        "state_commit_failed",
                        "could not resolve new state commit",
                    )
                new_commit = new_result.stdout.decode("ascii").strip()
                if not self._compare_and_swap(snapshot.commit, new_commit):
                    raise StateStoreError(
                        "concurrent_update",
                        "state ref changed before local compare-and-swap",
                    )

            return AppendResult(
                old_commit=snapshot.commit,
                new_commit=new_commit,
                event_path=event_path,
                projection=projection,
            )
