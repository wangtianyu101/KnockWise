"""T17 · generated marker publication (REQ-008 / TC-012 / TC-013).

Rewrite only the ``<!-- workflow-state:begin ... end -->`` marker block in
tasks.md / verify.md, preserving all human-authored prose around it.  A
hand edit inside the marker block raises ``MarkerHandEditError`` instead of
silently overwriting the user's prose.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Iterable

from .models import TaskProjection


_MARKER_BEGIN_RE = re.compile(
    r"<!--\s*workflow-state:begin\s+(?P<attrs>[^>]+?)\s*-->"
)
_MARKER_END = "<!-- workflow-state:end -->"


class MarkerHandEditError(Exception):
    """Raised when the generated marker block has been hand-edited."""


@dataclasses.dataclass(frozen=True)
class PlannedChange:
    filename: str
    changed: bool


def _marker_attrs(projection: TaskProjection) -> str:
    return (
        f"task={projection.task_id} "
        f"source_sequence={projection.source_sequence} "
        f"source_hash={projection.source_hash}"
    )


def _marker_open(attrs: str) -> str:
    return f"<!-- workflow-state:begin {attrs} -->"


def _render_projection_files(projection: TaskProjection) -> dict[str, str]:
    """Reuse projector.render_projection_files but adapt dict to TaskProjection."""
    from .projector import render_projection_files  # local import keeps materialize optional

    if isinstance(projection, dict):
        projection = TaskProjection.model_validate(projection)
    return render_projection_files(projection)


def _tasks_md(projection: TaskProjection) -> str:
    from .projector import _tasks_markdown

    return _tasks_markdown(projection)


def _verify_md(projection: TaskProjection) -> str:
    from .projector import _verify_markdown

    return _verify_markdown(projection)


def _split_marker_block(body: str) -> tuple[str, str, str, str | None]:
    """Return (prefix, end_marker, suffix, attrs_string) for the workflow-state marker block.

    ``prefix`` / ``suffix`` are the human-authored regions outside the
    generated block.  ``end_marker`` is the literal marker text.  When the
    document has no marker block, ``attrs_string`` is ``None``.
    """
    begin_match = _MARKER_BEGIN_RE.search(body)
    if not begin_match:
        prefix = body
        end_marker = ""
        suffix = ""
        return prefix, end_marker, suffix, None

    begin_pos = begin_match.start()
    end_pos = body.find(_MARKER_END, begin_match.end())
    if end_pos < 0:
        raise MarkerHandEditError(
            f"workflow-state marker is missing the end sentinel at line "
            f"containing '{_MARKER_END[:30]}...'"
        )
    end_pos += len(_MARKER_END)

    prefix = body[:begin_pos]
    end_marker = body[begin_pos:end_pos]
    suffix = body[end_pos:]
    # Strip the single trailing newline that belongs to the marker block so
    # replacement + suffix can be composed without doubling the newline.
    if suffix.startswith("\n"):
        suffix = suffix[1:]
    return prefix, end_marker, suffix, begin_match.group("attrs")


def _render_marker_block(projection: TaskProjection) -> str:
    return f"{_marker_open(_marker_attrs(projection))}\n{_rendered_table_for(projection)}\n{_MARKER_END}\n"


def _rendered_table_for(projection: TaskProjection) -> str:
    """Render only the markdown table between begin/end markers."""
    full = _tasks_md(projection)
    parts = full.split(_MARKER_END, 1)
    inner = parts[0]
    return inner.split("\n", 1)[1]


def _rendered_table_for_verify(projection: TaskProjection) -> str:
    full = _verify_md(projection)
    parts = full.split(_MARKER_END, 1)
    inner = parts[0]
    return inner.split("\n", 1)[1]


def _apply_marker(
    body: str,
    replacement: str,
    expected_table: str,
    expected_attrs: str,
) -> tuple[str, bool]:
    prefix, old_marker, suffix, file_attrs = _split_marker_block(body)
    if old_marker and file_attrs and file_attrs.strip() == expected_attrs:
        # Marker attrs still match the projection → only fail if the
        # *table* content drifts.  This protects user prose in the marker
        # region from silent overwrites when an external tool edited the
        # file in-place.
        existing_table = _table_from_marker(old_marker)
        if existing_table.strip() != expected_table.strip():
            raise MarkerHandEditError(
                "workflow-state marker table content has drifted from "
                "projection; refusing to overwrite user edits"
            )

    new_body = f"{prefix}{replacement}{suffix}"
    changed = new_body != body
    return new_body, changed


def _table_from_marker(marker: str) -> str:
    """Extract the markdown table body between begin / end markers."""
    after_begin = marker.split("-->", 1)[1]
    before_end = after_begin.rsplit(_MARKER_END, 1)[0]
    return before_end.lstrip("\n").rstrip("\n")


def materialize_task_documents(
    task_root: Path | str,
    projection: dict | TaskProjection,
    *,
    dry_run: bool = False,
) -> tuple[PlannedChange, ...]:
    """Rewrite the workflow-state marker block in tasks.md / verify.md.

    Returns the planned file changes.  When ``dry_run=True`` the filesystem
    is not touched; the function still validates the marker attributes to
    fail closed on TC-013 hand edits.
    """
    task_root = Path(task_root)

    if not isinstance(projection, TaskProjection):
        projection = TaskProjection.model_validate(projection)

    rendered_tables = {
        "tasks.md": _rendered_table_for(projection),
        "verify.md": _rendered_table_for_verify(projection),
    }

    plans: list[PlannedChange] = []

    for filename, table in rendered_tables.items():
        replacement = _render_marker_block_for(projection, table)

        path = task_root / filename

        if path.exists():
            current_body = path.read_text(encoding="utf-8")
            new_body, changed = _apply_marker(
                current_body,
                replacement,
                table,
                _marker_attrs(projection),
            )
        else:
            new_body = replacement
            changed = True

        if not changed and path.exists():
            plans.append(PlannedChange(filename=filename, changed=False))
            continue

        plans.append(PlannedChange(filename=filename, changed=True))

        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new_body, encoding="utf-8")

    return tuple(plans)


def _render_marker_block_for(projection: TaskProjection, table: str) -> str:
    return (
        f"{_marker_open(_marker_attrs(projection))}\n"
        f"{table}\n"
        f"{_MARKER_END}\n"
    )


__all__ = [
    "MarkerHandEditError",
    "PlannedChange",
    "materialize_task_documents",
]