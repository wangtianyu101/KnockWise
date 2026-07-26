"""End-to-end tests for scripts/check-governance.py."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_NAMES = (
    "check-governance.py",
    "check-step.py",
    "check-task.py",
    "check_task_state.py",
)
VALID_TASK_YAML = """\
schema: task/v1
task_id: 2026-07-26-ci-task
mode: timebox
current_step: 0
step_state: in_progress
triggers:
  ui_design: false
  ui_components: false
  api_change: false
  db_change: false
test_evidence:
  type: pending
"""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _init_repo(tmp_path: Path) -> tuple[Path, str]:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@test.local")
    _git(tmp_path, "config", "user.name", "test")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in SCRIPT_NAMES:
        shutil.copy(REPO_ROOT / "scripts" / name, scripts / name)
    (tmp_path / "README.md").write_text("# base\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path, _git(tmp_path, "rev-parse", "HEAD").stdout.strip()


def _commit_task(repo: Path, *, with_manifest: bool) -> None:
    task_dir = repo / "docs/tasks/2026-07-26-ci-task"
    task_dir.mkdir(parents=True)
    (task_dir / "notes.md").write_text("# notes\n")
    if with_manifest:
        (task_dir / "task.yaml").write_text(VALID_TASK_YAML)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "task")


def _run(repo: Path, base: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/check-governance.py", "--base", base],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_ci_blocks_new_task_without_manifest(tmp_path):
    repo, base = _init_repo(tmp_path)
    _commit_task(repo, with_manifest=False)

    result = _run(repo, base)

    assert result.returncode != 0, result.stdout
    assert "requires docs/tasks/2026-07-26-ci-task/task.yaml" in result.stdout


def test_ci_accepts_new_task_with_valid_manifest(tmp_path):
    repo, base = _init_repo(tmp_path)
    _commit_task(repo, with_manifest=True)

    result = _run(repo, base)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "governance gate passed" in result.stdout


def test_ci_propagates_check_task_cli_failure(tmp_path):
    repo, base = _init_repo(tmp_path)
    task_dir = repo / "docs/tasks/2026-07-26-ci-task"
    task_dir.mkdir(parents=True)
    (task_dir / "notes.md").write_text("# notes\n")
    (task_dir / "task.yaml").write_text(
        VALID_TASK_YAML.replace("mode: timebox", "mode: invalid")
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "invalid task")

    result = _run(repo, base)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "E001" in result.stdout
    assert "task contract failed" in result.stdout


def test_ci_does_not_require_manifest_when_existing_task_adds_file(tmp_path):
    repo, _ = _init_repo(tmp_path)
    task_dir = repo / "docs/tasks/2026-07-23-existing-legacy"
    task_dir.mkdir(parents=True)
    (task_dir / "notes.md").write_text("# existing\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "legacy task")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    (task_dir / "follow-up.md").write_text("# follow-up\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "follow up")

    result = _run(repo, base)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "requires" not in result.stdout


def test_ci_blocks_deleting_existing_task_manifest(tmp_path):
    repo, _ = _init_repo(tmp_path)
    _commit_task(repo, with_manifest=True)
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "rm", "docs/tasks/2026-07-26-ci-task/task.yaml")
    _git(repo, "commit", "-qm", "delete manifest")

    result = _run(repo, base)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "task manifest deleted" in result.stdout


def test_ci_blocks_renamed_task_root_without_manifest(tmp_path):
    repo, _ = _init_repo(tmp_path)
    old_root = repo / "docs/tasks/2026-07-23-existing-legacy"
    old_root.mkdir(parents=True)
    (old_root / "notes.md").write_text("# existing\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "legacy task")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(
        repo,
        "mv",
        "docs/tasks/2026-07-23-existing-legacy",
        "docs/tasks/2026-07-26-renamed-task",
    )
    _git(repo, "commit", "-qm", "rename task")

    result = _run(repo, base)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "requires docs/tasks/2026-07-26-renamed-task/task.yaml" in result.stdout
