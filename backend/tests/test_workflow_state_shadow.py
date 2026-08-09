"""T18 · Shadow reconciliation + cutover report (REQ-008 / REQ-011).

Contract:
  - ``compare_task_states`` reconciles the legacy on-disk artefacts
    (docs/tasks/<id>/{tasks.md, verify.md}) with the v2 projection
    emitted by the workflow-state authority.
  - New tasks (no legacy artefacts) report a clean ``v2_only`` status.
  - Legacy tasks report a ``drifted`` status with the differing fields
    called out so an operator can decide whether the divergence is
    expected (legacy artefacts frozen) or a real misprojection.
  - The cutover summary marks a task as ``ready`` only when legacy and v2
    both agree on the trust/evidence state.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.workflow_state.shadow import (  # noqa: E402
    DriftReport,
    compare_task_states,
    summarise_cutover,
)


def _clean_env():
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
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout.decode().strip()


def _init_repo_with_state_branch(repo: Path) -> Path:
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Shadow Tests")
    _git(repo, "config", "user.email", "shadow@example.invalid")

    sys_path = str(Path(__file__).resolve().parents[2])
    if sys_path not in os.sys.path:
        os.sys.path.insert(0, sys_path)

    from scripts.workflow_state.git_store import GitStateStore

    GitStateStore(repo).bootstrap()
    return Path(repo)


def test_compare_new_task_reports_v2_only(tmp_path: Path):
    repo = _init_repo_with_state_branch(tmp_path)
    task_dir = repo / "docs" / "tasks" / "2026-08-10-new"
    task_dir.mkdir(parents=True)
    (task_dir / "tasks.md").write_text(
        "# New task\n\nThis task was born under v2.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "docs/tasks/2026-08-10-new/")
    _git(repo, "commit", "-qm", "new task born under v2")

    report = compare_task_states(repo, task_id="2026-08-10-new")

    assert isinstance(report, DriftReport)
    assert report.legacy_present is True
    # No workflow-state events yet → v2 empty, so the report flags it as
    # ready for cutover once the new task pipeline emits its first event.
    assert report.v2_present is False
    assert "v2_only" in (report.summary or "")


def test_compare_legacy_task_reports_drift(tmp_path: Path):
    repo = _init_repo_with_state_branch(tmp_path)
    task_dir = repo / "docs" / "tasks" / "2026-08-10-legacy"
    task_dir.mkdir(parents=True)
    (task_dir / "tasks.md").write_text(
        "# Legacy task\n\nImplemented by hand in 2026.\n",
        encoding="utf-8",
    )
    (task_dir / "verify.md").write_text(
        "# verify\n",
        encoding="utf-8",
    )
    _git(repo, "add", "docs/tasks/2026-08-10-legacy/")
    _git(repo, "commit", "-qm", "legacy task fixture")

    sys_path = str(Path(__file__).resolve().parents[2])
    if sys_path not in os.sys.path:
        os.sys.path.insert(0, sys_path)

    from scripts.workflow_state.migrate import import_legacy_snapshot

    projection = import_legacy_snapshot(
        repo,
        task_id="2026-08-10-legacy",
        default_branch_ref="refs/heads/main",
    )

    report = compare_task_states(repo, task_id="2026-08-10-legacy")

    assert report.legacy_present is True
    assert report.v2_present is True
    # The migrated projection must keep the LEGACY_UNVERIFIED trust tag.
    assert report.v2_trust == projection.legacy_trust.value
    assert any("legacy_trust" in field for field in report.drift_fields)


def test_summarise_cutover_marks_ready_only_on_consensus(tmp_path: Path):
    repo = _init_repo_with_state_branch(tmp_path)
    report_a = DriftReport(
        task_id="2026-08-10-A",
        legacy_present=True,
        v2_present=True,
        drift_fields=[],
        v2_trust="LEGACY_UNVERIFIED",
        summary="aligned",
    )
    report_b = DriftReport(
        task_id="2026-08-10-B",
        legacy_present=True,
        v2_present=True,
        drift_fields=["acceptance_state"],
        v2_trust="LEGACY_UNVERIFIED",
        summary="drifted",
    )

    summary = summarise_cutover([report_a, report_b])

    assert summary["ready"] == ["2026-08-10-A"]
    assert summary["blocked"] == ["2026-08-10-B"]