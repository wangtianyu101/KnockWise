"""T18 · Shadow reconciliation + cutover report (REQ-008 / REQ-011).

Reconciles legacy on-disk artefacts (``docs/tasks/<id>/{tasks.md,verify.md}``)
with the v2 projection emitted by the workflow-state authority.  The output
is intentionally human-readable: ``DriftReport`` lists the fields that
disagree so operators can decide whether the drift is expected (legacy
artefacts frozen) or a real misprojection that blocks Shadow → Enforce.
"""
from __future__ import annotations

import dataclasses
import json
import os
import subprocess
from pathlib import Path
from typing import Iterable

from .canonical import event_hash
from .git_store import GitStateStore
from .models import TaskProjection
from .reducer import reduce_events


_LEGACY_TASK_PREFIX = "docs/tasks/"


@dataclasses.dataclass(frozen=True)
class DriftReport:
    task_id: str
    legacy_present: bool
    v2_present: bool
    drift_fields: tuple[str, ...]
    v2_trust: str | None
    summary: str | None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _clean_env() -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
    ):
        environment.pop(key, None)
    environment["LC_ALL"] = "C"
    return environment


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.decode().strip()


def _legacy_paths_present(repo: Path, task_id: str) -> bool:
    rel_tasks = f"{_LEGACY_TASK_PREFIX}{task_id}/tasks.md"
    listed = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{rel_tasks}"],
        cwd=repo,
        capture_output=True,
        env=_clean_env(),
        check=False,
    )
    return listed.returncode == 0


def _legacy_summary(repo: Path, task_id: str) -> dict[str, str]:
    """Best-effort summary of legacy on-disk artefacts for the task."""
    rel_tasks = f"{_LEGACY_TASK_PREFIX}{task_id}/tasks.md"
    rel_verify = f"{_LEGACY_TASK_PREFIX}{task_id}/verify.md"
    summary: dict[str, str] = {}
    for key, rel in (("tasks_md", rel_tasks), ("verify_md", rel_verify)):
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            cwd=repo,
            capture_output=True,
            env=_clean_env(),
            check=False,
        )
        if result.returncode == 0:
            summary[key] = result.stdout.decode(errors="replace")
    return summary


def _load_v2_projection(repo: Path, task_id: str) -> TaskProjection | None:
    store = GitStateStore(repo)
    try:
        snapshot = store.load_snapshot()
    except Exception:
        return None

    events = []
    for path, blob in snapshot.files.items():
        if not path.startswith(f"tasks/{task_id}/events/"):
            continue
        if not path.endswith(".json"):
            continue
        try:
            events.append(type(events[0]) if events else None)
            from .models import TaskEvent
            events[-1] = TaskEvent.model_validate(json.loads(blob.decode("utf-8")))
        except Exception:
            continue
    if not events:
        return None
    return reduce_events(sorted(events, key=lambda e: e.sequence))


def _compare_legacy_to_v2(
    legacy: dict[str, str], projection: TaskProjection
) -> tuple[str, ...]:
    """Return the names of fields that disagree between legacy and v2."""
    drift = []
    # The legacy artefacts do not encode the v2 trust tag; the migration
    # always sets it to LEGACY_UNVERIFIED, so any legacy + v2 coexistence
    # is a drift signal for operators.
    if projection.legacy_trust.value == "LEGACY_UNVERIFIED":
        drift.append("legacy_trust")

    legacy_text = (legacy.get("tasks_md") or "").strip().lower()
    if "implementation" in legacy_text and projection.implementation_state.value.lower() not in legacy_text:
        drift.append("implementation_state")

    legacy_verify = (legacy.get("verify_md") or "").strip().lower()
    if (
        legacy_verify
        and "pass" in legacy_verify
        and projection.verifier_state.value.lower() != "pass"
    ):
        drift.append("verifier_state")
    return tuple(drift)


def compare_task_states(repo: Path | str, task_id: str) -> DriftReport:
    """Compare the legacy and v2 state of a single task."""
    repo = Path(repo)

    legacy_present = _legacy_paths_present(repo, task_id)
    projection = _load_v2_projection(repo, task_id)
    v2_present = projection is not None

    if v2_present and legacy_present:
        legacy = _legacy_summary(repo, task_id)
        drift = _compare_legacy_to_v2(legacy, projection)
        summary = (
            "aligned" if not drift else "drifted"
        )
        v2_trust = projection.legacy_trust.value
    elif v2_present and not legacy_present:
        drift = ()
        summary = "v2_only"
        v2_trust = projection.legacy_trust.value
    elif legacy_present and not v2_present:
        drift = ("v2_missing",)
        summary = "v2_only_pending_first_event"
        v2_trust = None
    else:
        drift = ("unknown",)
        summary = "no_state"
        v2_trust = None

    return DriftReport(
        task_id=task_id,
        legacy_present=legacy_present,
        v2_present=v2_present,
        drift_fields=drift,
        v2_trust=v2_trust,
        summary=summary,
    )


def summarise_cutover(reports: Iterable[DriftReport]) -> dict[str, list[str]]:
    """Bucket drift reports into ``ready`` / ``blocked`` cutover lists."""
    ready: list[str] = []
    blocked: list[str] = []

    for report in reports:
        if report.summary == "aligned":
            ready.append(report.task_id)
        else:
            blocked.append(report.task_id)

    return {"ready": sorted(ready), "blocked": sorted(blocked)}


__all__ = [
    "DriftReport",
    "compare_task_states",
    "summarise_cutover",
]