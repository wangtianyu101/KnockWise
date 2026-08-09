"""Trusted adapters for observing Git commits and test-process results."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Sequence

from .git_store import GitStateStore, StateStoreError


_FULL_COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")
_COUNT = re.compile(r"(?<!\w)(\d+)\s+(passed|failed|skipped|xfailed)\b")
_SUMMARY_LIMIT_BYTES = 2048
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


@dataclass(frozen=True)
class TestObservation:
    """Bounded, persistable evidence from one directly executed process."""

    command: List[str]
    cwd: str
    environment: Mapping[str, object]
    exit_code: int
    counts: Mapping[str, int]
    stdout_digest: str
    stderr_digest: str
    stdout_summary: str
    stderr_summary: str
    stdout_truncated: bool
    stderr_truncated: bool

    @property
    def result(self) -> str:
        return "PASS" if self.exit_code == 0 else "FAIL"

    def payload(self) -> Dict[str, object]:
        return {
            "command": self.command,
            "counts": dict(self.counts),
            "cwd": self.cwd,
            "environment": dict(self.environment),
            "exit_code": self.exit_code,
            "result": self.result,
            "stderr_digest": self.stderr_digest,
            "stderr_summary": self.stderr_summary,
            "stderr_truncated": self.stderr_truncated,
            "stdout_digest": self.stdout_digest,
            "stdout_summary": self.stdout_summary,
            "stdout_truncated": self.stdout_truncated,
        }


def resolve_commit(store: GitStateStore, revision: str) -> str:
    """Resolve one already-created commit to its immutable full object id."""

    if _FULL_COMMIT.fullmatch(revision) is None:
        raise StateStoreError(
            "commit_sha_invalid",
            "--commit must be exactly 40 hexadecimal characters",
        )
    normalized = revision.lower()
    exists = store._run(["cat-file", "-e", f"{normalized}^{{commit}}"])
    if exists.returncode != 0:
        raise StateStoreError(
            "commit_not_found",
            f"Git object {normalized} does not resolve to a commit",
            blocked=True,
        )
    resolved = store._run(["rev-parse", "--verify", f"{normalized}^{{commit}}"])
    if resolved.returncode != 0:
        raise StateStoreError(
            "commit_not_found",
            f"Git object {normalized} does not resolve to a commit",
            blocked=True,
        )
    commit = resolved.stdout.decode("ascii").strip().lower()
    if _FULL_COMMIT.fullmatch(commit) is None:
        raise StateStoreError(
            "commit_resolution_invalid",
            "Git returned an invalid commit object id",
            blocked=True,
        )
    return commit


def _child_environment() -> Dict[str, str]:
    environment = os.environ.copy()
    for key in _GIT_LOCAL_ENV_KEYS:
        environment.pop(key, None)
    return environment


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _bounded_summary(content: bytes) -> tuple:
    truncated = len(content) > _SUMMARY_LIMIT_BYTES
    summary = content[:_SUMMARY_LIMIT_BYTES].decode("utf-8", errors="replace")
    while len(summary.encode("utf-8")) > _SUMMARY_LIMIT_BYTES:
        summary = summary[:-1]
    return summary, truncated


def _classified_counts(stdout: bytes, stderr: bytes) -> Dict[str, int]:
    counts = {"failed": 0, "passed": 0, "skipped": 0, "xfail": 0}
    combined = (stdout + b"\n" + stderr).decode("utf-8", errors="replace")
    for raw_count, label in _COUNT.findall(combined):
        key = "xfail" if label == "xfailed" else label
        counts[key] = int(raw_count)
    return counts


def observe_test(repository: Path, argv: Sequence[str]) -> TestObservation:
    """Run argv without a shell and return bounded, classified evidence."""

    command = list(argv)
    if not command or not command[0]:
        raise StateStoreError(
            "test_command_missing",
            "run-test requires a command after --",
        )
    environment = _child_environment()
    try:
        completed = subprocess.run(
            command,
            cwd=repository,
            capture_output=True,
            env=environment,
            shell=False,
        )
    except OSError as error:
        raise StateStoreError(
            "test_command_unavailable",
            f"could not execute test command {command[0]!r}: {error}",
        ) from error
    stdout_summary, stdout_truncated = _bounded_summary(completed.stdout)
    stderr_summary, stderr_truncated = _bounded_summary(completed.stderr)
    return TestObservation(
        command=command,
        cwd=str(Path(repository).resolve()),
        environment={
            "CI": environment.get("CI"),
            "PYTHONHASHSEED": environment.get("PYTHONHASHSEED"),
        },
        exit_code=completed.returncode,
        counts=_classified_counts(completed.stdout, completed.stderr),
        stdout_digest=_digest(completed.stdout),
        stderr_digest=_digest(completed.stderr),
        stdout_summary=stdout_summary,
        stderr_summary=stderr_summary,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
    )


def command_digest(command: Sequence[str]) -> str:
    """Return a stable digest used only to identify an observation event."""

    encoded = json.dumps(
        list(command),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
