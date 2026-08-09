"""Read-only Git storage primitives for the workflow-state control plane."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Iterator, Mapping, Optional, Sequence


STATE_REF = "refs/heads/workflow-state"
FORMAT_CONTENT = b"workflow-state/v1\n"
_ZERO_OID = "0" * 40
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
    def temporary_worktree(self) -> Iterator[Path]:
        """Yield a detached state checkout and remove it on every exit path."""

        self._ensure_repository()
        commit = self._ref_commit()
        self._validate_format(commit)
        temp_root = Path(tempfile.mkdtemp(prefix="taskctl-worktree-"))
        worktree = temp_root / "checkout"
        added = False
        try:
            result = self._run(
                ["worktree", "add", "--detach", "--quiet", str(worktree), commit]
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
