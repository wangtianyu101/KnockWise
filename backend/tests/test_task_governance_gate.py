"""P0 regression tests for the task-governance execution chain."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_SRC = REPO_ROOT / "scripts" / "pre-commit"
SCRIPT_NAMES = ("check-step.py", "check-task.py", "check_task_state.py")


def _load_state_checker():
    spec = importlib.util.spec_from_file_location(
        "check_task_state",
        REPO_ROOT / "scripts" / "check_task_state.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _init_repo(tmp_path: Path, *, copy_task_checker: bool = True) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.local"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=tmp_path,
        check=True,
    )
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy(HOOK_SRC, scripts / "pre-commit")
    for name in SCRIPT_NAMES:
        if name == "check-task.py" and not copy_task_checker:
            continue
        shutil.copy(REPO_ROOT / "scripts" / name, scripts / name)
    return tmp_path


def _stage(repo: Path, relpath: str, content: str) -> None:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    subprocess.run(["git", "add", relpath], cwd=repo, check=True)


def _run_hook(repo: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SKIP_TASKS_SYNC"] = "1"
    return subprocess.run(
        ["sh", "scripts/pre-commit"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


VALID_TASK_YAML = """\
schema: task/v1
task_id: 2026-07-26-new-governed-task
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

VALID_VERIFY = """\
# Verification

Distributed evidence: L1, L2, L4.

## L3 整合测试

结果：通过

## L5 staging 运行时验证

结果：通过
phase_acceptance: PENDING
"""


def test_post_cutoff_task_is_not_legacy_exempt():
    checker = _load_state_checker()
    assert checker.is_exempt(
        "docs/tasks/2026-07-23-refactor-task-status-semantics/tasks.md"
    )
    assert not checker.is_exempt(
        "docs/tasks/2026-07-24-new-task/tasks.md"
    )
    assert not checker.is_exempt(
        "docs/tasks/2026-07-26-new-task/tasks.md"
    )


def test_state_checker_index_view_reads_staged_content(tmp_path):
    checker = _load_state_checker()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    task_path = Path("docs/tasks/2026-07-26-new-task/tasks.md")
    absolute = tmp_path / task_path
    absolute.parent.mkdir(parents=True)
    absolute.write_text("# tasks\n")
    subprocess.run(["git", "add", str(task_path)], cwd=tmp_path, check=True)
    absolute.write_text("# tasks\n✅ DONE should only be in worktree\n")

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        staged = checker.read_content(task_path, "index")
        worktree = checker.read_content(task_path, "worktree")
    finally:
        os.chdir(old_cwd)

    assert "✅ DONE" not in staged
    assert "✅ DONE" in worktree


def test_state_checker_does_not_overwrite_task_with_later_table(tmp_path):
    checker = _load_state_checker()
    task_path = tmp_path / "tasks.md"
    task_path.write_text(
        "| 任务 | 自动化测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        "| T1 | node | scenario | REQ-1 | SCN-1 | TC-1 | L1 | worktree | PASS | PASS | PENDING |\n"
        "\n"
        "| 轮次 | 范围 | 结果 | 偏差与修复 |\n"
        "|---|---|---|---|\n"
        "| writer-1 | focused | PASS | none |\n"
    )

    errors = checker.check_three_facts(task_path)

    assert errors == [], errors


def _task_state_document(*, verifier: str, task_line: str) -> str:
    return (
        "| 任务 | 自动化测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|\n"
        f"| T1 | node | scenario | REQ-1 | SCN-1 | TC-1 | L1 | abc1234 | PASS | {verifier} | PENDING |\n"
        f"{task_line}\n"
        "\n"
        "implementation evidence follows\n"
    )


def _run_state_checker(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "check_task_state.py"),
            str(path),
            "--view",
            "worktree",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_failed_verifier_keeps_implemented_checkbox(tmp_path):
    task_path = tmp_path / "tasks.md"
    task_path.write_text(
        _task_state_document(verifier="FAIL", task_line="- [x] T1: 已实施")
    )

    result = _run_state_checker(task_path)

    assert result.returncode == 0, result.stdout + result.stderr


def test_naked_done_still_blocks_implemented_checkbox(tmp_path):
    task_path = tmp_path / "tasks.md"
    task_path.write_text(
        _task_state_document(verifier="PASS", task_line="- [x] T1: ✅ DONE")
    )

    result = _run_state_checker(task_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "task-state-naked-done" in result.stdout


def test_active_task_status_guidance_uses_orthogonal_facts():
    agents = (REPO_ROOT / "AGENTS.md").read_text()
    template = (REPO_ROOT / "docs/templates/tasks-template.md").read_text()
    hook = (REPO_ROOT / "scripts/pre-commit").read_text()

    assert "- [x] T<n>: ✅ DONE" not in agents
    assert "只有 `verifier: PASS` + `acceptance: ACCEPTED` 才能写 `[x]`" not in template
    assert "把对应 task 标 - [x] ✅ DONE" not in hook
    assert "[x]` 只表示已实施，可与 test/verifier `FAIL` 共存" in agents
    assert "`[x]` 只表示 implementation 已落入 commit，可与 test/verifier `FAIL` 共存" in template
    assert "[x] 可与 test/verifier FAIL 共存" in hook


def test_new_task_without_manifest_blocks_hook(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/notes.md",
        "# task notes\n",
    )

    result = _run_hook(repo)

    assert result.returncode != 0, result.stdout
    assert "task.yaml" in result.stdout
    assert "禁止 commit" in result.stdout


def test_new_task_with_valid_manifest_passes_hook(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/notes.md",
        "# task notes\n",
    )
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/task.yaml",
        VALID_TASK_YAML,
    )

    result = _run_hook(repo)

    assert result.returncode == 0, result.stdout
    assert "task.yaml 契约校验通过" in result.stdout


def test_existing_legacy_task_can_add_file_without_manifest(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(
        repo,
        "docs/tasks/2026-07-23-existing-legacy/notes.md",
        "# existing task\n",
    )
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repo, check=True)
    _stage(
        repo,
        "docs/tasks/2026-07-23-existing-legacy/follow-up.md",
        "# follow-up\n",
    )

    result = _run_hook(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "缺少" not in result.stdout


def test_renamed_task_root_without_manifest_blocks_hook(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(
        repo,
        "docs/tasks/2026-07-23-existing-legacy/notes.md",
        "# existing task\n",
    )
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "mv",
            "docs/tasks/2026-07-23-existing-legacy",
            "docs/tasks/2026-07-26-renamed-task",
        ],
        cwd=repo,
        check=True,
    )

    result = _run_hook(repo)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "docs/tasks/2026-07-26-renamed-task/task.yaml" in result.stdout


def test_verify_only_change_validates_sibling_tasks_from_index(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/task.yaml",
        VALID_TASK_YAML,
    )
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/tasks.md",
        "# Tasks\n\n| T1 | missing governance facts |\n",
    )
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repo, check=True)
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/verify.md",
        VALID_VERIFY,
    )

    result = _run_hook(repo)

    assert result.returncode != 0, result.stdout
    assert "task-state-missing-three-facts" in result.stdout


def test_missing_task_checker_fails_closed(tmp_path):
    repo = _init_repo(tmp_path, copy_task_checker=False)
    _stage(
        repo,
        "docs/tasks/2026-07-26-new-governed-task/task.yaml",
        VALID_TASK_YAML,
    )

    result = _run_hook(repo)

    assert result.returncode != 0, result.stdout
    assert "scripts/check-task.py 不存在" in result.stdout


def test_versioned_hook_installer_sets_core_hooks_path(tmp_path):
    repo = _init_repo(tmp_path)
    installer = REPO_ROOT / "scripts" / "install-hooks.sh"
    copied = repo / "scripts" / "install-hooks.sh"
    shutil.copy(installer, copied)
    copied.chmod(0o755)

    result = subprocess.run(
        ["sh", "scripts/install-hooks.sh"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    configured = subprocess.run(
        ["git", "config", "--local", "--get", "core.hooksPath"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert configured.stdout.strip() == "scripts"
