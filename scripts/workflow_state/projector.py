"""Deterministic workflow-state file projections and drift checks."""

from __future__ import annotations

import re
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple

import yaml

from .canonical import canonical_json
from .models import TaskProjection


PROJECTION_FILENAMES = (
    "task.json",
    "task.yaml",
    "tasks-status.md",
    "verify-status.md",
)

_MARKER_RE = re.compile(
    rb"^<!-- workflow-state:begin "
    rb"task=(?P<task>[^\s]+) "
    rb"source_sequence=(?P<sequence>\d+) "
    rb"source_hash=(?P<source_hash>sha256:[0-9a-f]{64}) -->$"
)


class ProjectionDriftError(ValueError):
    """A generated view differs from deterministic event-derived output."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        filename: str = "",
        expected_source_hash: str = "",
        actual_source_hash: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.filename = filename
        self.expected_source_hash = expected_source_hash
        self.actual_source_hash = actual_source_hash


def _marker(projection: TaskProjection) -> str:
    return (
        "<!-- workflow-state:begin "
        f"task={projection.task_id} "
        f"source_sequence={projection.source_sequence} "
        f"source_hash={projection.source_hash} -->"
    )


def _tasks_markdown(projection: TaskProjection) -> str:
    rows = (
        ("workflow", projection.workflow_phase.value),
        ("implementation", projection.implementation_state.value),
        ("test", projection.test_state.value),
        ("verifier", projection.verifier_state.value),
        ("acceptance", projection.acceptance_state.value),
        ("merge_gate", projection.merge_gate_state.value),
        ("active_commit", projection.active_commit or "—"),
        ("active_spec_hash", projection.active_spec_hash or "—"),
        ("legacy_trust", projection.legacy_trust.value),
    )
    table = "\n".join(f"| {name} | {value} |" for name, value in rows)
    return (
        f"{_marker(projection)}\n"
        "| fact | state |\n"
        "|---|---|\n"
        f"{table}\n"
        "<!-- workflow-state:end -->\n"
    )


def _verify_markdown(projection: TaskProjection) -> str:
    rows = (
        ("implementation", projection.implementation_state.value),
        ("test", projection.test_state.value),
        ("verifier", projection.verifier_state.value),
        ("acceptance", projection.acceptance_state.value),
        ("merge_gate", projection.merge_gate_state.value),
    )
    table = "\n".join(f"| {name} | {value} |" for name, value in rows)
    return (
        f"{_marker(projection)}\n"
        "| evidence | state |\n"
        "|---|---|\n"
        f"{table}\n"
        "<!-- workflow-state:end -->\n"
    )


def render_projection_files(
    projection: TaskProjection,
) -> Mapping[str, bytes]:
    """Render the complete fixed projection set without filesystem access."""

    data: Dict[str, Any] = projection.model_dump(mode="json")
    files = {
        "task.json": canonical_json(data) + b"\n",
        "task.yaml": yaml.safe_dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True,
            width=4096,
        ).encode("utf-8"),
        "tasks-status.md": _tasks_markdown(projection).encode("utf-8"),
        "verify-status.md": _verify_markdown(projection).encode("utf-8"),
    }
    return MappingProxyType(files)


def _marker_metadata(content: bytes) -> Optional[Dict[str, str]]:
    first_line = content.splitlines()[0] if content else b""
    match = _MARKER_RE.match(first_line)
    if match is None:
        return None
    return {
        key: value.decode("utf-8")
        for key, value in match.groupdict().items()
    }


def validate_projection_files(
    projection: TaskProjection,
    actual_files: Mapping[str, bytes],
) -> None:
    """Fail closed when a generated file is missing, extra, or edited."""

    expected_files = render_projection_files(projection)
    if set(actual_files) != set(expected_files):
        raise ProjectionDriftError(
            "file_set_mismatch",
            (
                f"expected files {sorted(expected_files)}, "
                f"got {sorted(actual_files)}"
            ),
            expected_source_hash=projection.source_hash,
        )

    for filename in PROJECTION_FILENAMES:
        actual = actual_files[filename]
        expected = expected_files[filename]
        if filename.endswith(".md"):
            metadata = _marker_metadata(actual)
            if (
                metadata is None
                or metadata["task"] != projection.task_id
                or metadata["sequence"] != str(projection.source_sequence)
                or metadata["source_hash"] != projection.source_hash
            ):
                raise ProjectionDriftError(
                    "source_marker_mismatch",
                    f"{filename} source marker does not match active projection",
                    filename=filename,
                    expected_source_hash=projection.source_hash,
                    actual_source_hash=(
                        metadata["source_hash"] if metadata is not None else None
                    ),
                )
        if actual != expected:
            raise ProjectionDriftError(
                "content_mismatch",
                f"{filename} differs from deterministic regeneration",
                filename=filename,
                expected_source_hash=projection.source_hash,
                actual_source_hash=projection.source_hash,
            )


def materialize_projection(
    root: Path,
    projection: TaskProjection,
) -> Tuple[str, ...]:
    """Write only changed fixed projection files and return their names."""

    root.mkdir(parents=True, exist_ok=True)
    changed = []
    for filename, content in render_projection_files(projection).items():
        path = root / filename
        if path.exists() and path.read_bytes() == content:
            continue
        path.write_bytes(content)
        changed.append(filename)
    return tuple(sorted(changed))
