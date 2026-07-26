"""
Tests for scripts/check-task.py
- 10 schema validation cases (per spec § 7)
- 2 EXEMPT cases (per spec § 7.7-7.8)
- 1 INDEX view case (per spec § 7.6)
"""
import os
import subprocess
from pathlib import Path

import pytest
import yaml

# Import the script as a module via importlib (filename has dash)
import sys
import importlib.util

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # backend/tests/<this> -> repo root
_SCRIPT = _REPO_ROOT / "scripts" / "check-task.py"
_spec = importlib.util.spec_from_file_location("check_task", str(_SCRIPT))
check_task = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_task)
HAS_SCRIPT = True

FIXTURES = Path(__file__).parent / "fixtures" / "task-yaml"


def _load(name: str) -> dict:
    """Load a fixture YAML and return parsed dict."""
    return yaml.safe_load((FIXTURES / f"{name}.yaml").read_text())


def _run_cli(
    cwd: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    """Execute the production CLI; never replace its result with a mock."""
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_minimal_manifest(repo: Path, task_id: str) -> Path:
    task_dir = repo / "docs" / "tasks" / task_id
    task_dir.mkdir(parents=True)
    content = (FIXTURES / "valid_minimal.yaml").read_text().replace(
        "task_id: 2026-07-24-test-task",
        f"task_id: {task_id}",
    )
    (task_dir / "task.yaml").write_text(content)
    return task_dir


class TestCliContract:
    """Black-box evidence for the documented rc 0/1/2/3 contract."""

    def test_valid_worktree_manifest_returns_zero(self, tmp_path):
        task_id = "2026-07-24-cli-valid"
        _write_minimal_manifest(tmp_path, task_id)

        result = _run_cli(
            tmp_path,
            "--dir",
            f"docs/tasks/{task_id}",
            "--view",
            "worktree",
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "task.yaml valid" in result.stdout

    def test_invalid_worktree_manifest_returns_one(self, tmp_path):
        task_id = "2026-07-24-cli-invalid"
        task_dir = _write_minimal_manifest(tmp_path, task_id)
        manifest = task_dir / "task.yaml"
        manifest.write_text(manifest.read_text().replace("mode: full-6", "mode: unknown"))

        result = _run_cli(
            tmp_path,
            "--dir",
            f"docs/tasks/{task_id}",
            "--view",
            "worktree",
        )

        assert result.returncode == 1, result.stdout + result.stderr
        assert "E001" in result.stdout

    def test_missing_manifest_returns_two(self, tmp_path):
        task_id = "2026-07-24-cli-missing"
        (tmp_path / "docs" / "tasks" / task_id).mkdir(parents=True)

        result = _run_cli(
            tmp_path,
            "--dir",
            f"docs/tasks/{task_id}",
            "--view",
            "worktree",
        )

        assert result.returncode == 2, result.stdout + result.stderr
        assert "task.yaml not found" in result.stdout

    def test_invocation_error_returns_three(self, tmp_path):
        result = _run_cli(tmp_path)

        assert result.returncode == 3, result.stdout + result.stderr
        assert "required" in result.stderr

    def test_index_uses_staged_valid_manifest_not_invalid_worktree(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        task_id = "2026-07-24-cli-index"
        task_dir = _write_minimal_manifest(tmp_path, task_id)
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        manifest = task_dir / "task.yaml"
        manifest.write_text(manifest.read_text().replace("mode: full-6", "mode: unknown"))

        result = _run_cli(
            tmp_path,
            "--dir",
            f"docs/tasks/{task_id}",
            "--view",
            "index",
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "task.yaml valid" in result.stdout

    def test_index_missing_manifest_is_not_rescued_by_worktree(self, tmp_path):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        task_id = "2026-07-24-cli-index-missing"
        _write_minimal_manifest(tmp_path, task_id)

        result = _run_cli(
            tmp_path,
            "--dir",
            f"docs/tasks/{task_id}",
            "--view",
            "index",
        )

        assert result.returncode == 2, result.stdout + result.stderr
        assert "task.yaml not found" in result.stdout


@pytest.mark.skipif(not HAS_SCRIPT, reason="check_task module not importable")
class TestSchemaValidation:
    """Spec § 7.1-7.10: 10 schema validation cases"""

    def test_minimal_task_yaml_valid(self, tmp_path):
        """S-1: 完整 task.yaml 通过校验"""
        # Create a real task directory with task.yaml
        task_dir = tmp_path / "docs" / "tasks" / "2026-07-24-test-task"
        task_dir.mkdir(parents=True)
        (task_dir / "task.yaml").write_text((FIXTURES / "valid_minimal.yaml").read_text())
        errors = check_task.validate_dir(str(task_dir), view="worktree")
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_missing_mode_blocked(self):
        """S-2: 缺 mode → E001"""
        data = _load("invalid_missing_mode")
        errors = check_task.validate_yaml(data, "2026-07-24-test-task")
        assert any("E001" in e for e in errors), f"Expected E001 in: {errors}"

    def test_step_out_of_range_blocked(self):
        """S-3: current_step=10 → E002"""
        data = _load("invalid_step_out_of_range")
        errors = check_task.validate_yaml(data, "2026-07-24-test-task")
        assert any("E002" in e for e in errors), f"Expected E002 in: {errors}"

    def test_step_4_pending_evidence_blocked(self):
        """S-4: current_step=4 + type=pending → blocked"""
        data = _load("invalid_step_4_pending")
        errors = check_task.validate_yaml(data, "2026-07-24-test-task")
        # type=pending requires current_step < 4 (per REQ-4)
        # Also: code requires path (not pending)
        assert len(errors) > 0
        # Should mention either evidence pending or test_evidence missing
        assert any("pending" in e.lower() or "evidence" in e.lower() for e in errors), \
            f"Expected evidence error in: {errors}"

    def test_task_id_must_match_dir_name(self, tmp_path):
        """S-5: task_id 与目录名不匹配 → E007"""
        task_dir = tmp_path / "docs" / "tasks" / "2026-07-24-correct-name"
        task_dir.mkdir(parents=True)
        (task_dir / "task.yaml").write_text((FIXTURES / "invalid_task_id_vs_dirname.yaml").read_text())
        errors = check_task.validate_dir(str(task_dir), view="worktree")
        assert any("E007" in e for e in errors), f"Expected E007 in: {errors}"

    def test_trigger_ui_design_requires_design_spec(self, tmp_path):
        """S-6: triggers.ui_design=true 但缺 design-spec.md"""
        task_dir = tmp_path / "docs" / "tasks" / "2026-07-24-test-ui-task"
        task_dir.mkdir(parents=True)
        (task_dir / "task.yaml").write_text((FIXTURES / "invalid_trigger_ui_design.yaml").read_text())
        # Don't create design-spec.md
        errors = check_task.validate_dir(str(task_dir), view="worktree")
        assert any("design-spec" in e.lower() for e in errors), \
            f"Expected design-spec error in: {errors}"
        assert any("mockups" in e.lower() for e in errors), \
            f"Expected mockups error in: {errors}"

    def test_step_state_accepted_requires_verify(self, tmp_path):
        """S-9: step_state=accepted 但缺 verify.md"""
        task_dir = tmp_path / "docs" / "tasks" / "2026-07-24-test-task"
        task_dir.mkdir(parents=True)
        (task_dir / "task.yaml").write_text((FIXTURES / "invalid_step_state_accepted_no_evidence.yaml").read_text())
        # Don't create verify.md
        errors = check_task.validate_dir(str(task_dir), view="worktree")
        # Should fail on either step_state vs verify, or evidence type=pending at step≥4
        assert len(errors) > 0

    def test_mode_unknown_blocked(self):
        """S-9 (variant): mode 不在枚举 → E001"""
        data = _load("invalid_mode_unknown")
        errors = check_task.validate_yaml(data, "2026-07-24-test-task")
        assert any("E001" in e for e in errors), f"Expected E001 in: {errors}"

    def test_schema_version_must_be_v1(self):
        """S-10: schema=task/v2 → E008"""
        data = _load("invalid_schema_version")
        errors = check_task.validate_yaml(data, "2026-07-24-test-task")
        assert any("E008" in e for e in errors), f"Expected E008 in: {errors}"
        # When schema is wrong, should be the only error
        assert all("E008" in e for e in errors), f"Other errors leaked: {errors}"


@pytest.mark.skipif(not HAS_SCRIPT, reason="check_task module not importable")
class TestExempt:
    """Spec § 7.7-7.8: EXEMPT_TASKS 白名单"""

    def test_legacy_task_dir_exempted(self):
        """S-7: 2026-07-01~22 老任务目录豁免（LEGACY_UNVERIFIED）"""
        for day in [f"{i:02d}" for i in range(1, 23)]:  # 01 to 22
            legacy = f"docs/tasks/2026-07-{day}-something"
            assert check_task.is_exempt(legacy) is True, f"Should exempt {legacy}"

    def test_archive_dir_exempted(self):
        """S-8: docs/archive/ 全豁免"""
        assert check_task.is_exempt("docs/archive/some-old-task/task.md") is True
        assert check_task.is_exempt("docs/archive/") is True

    def test_post_legacy_2026_07_23_not_exempted(self):
        """2026-07-23 起新任务强制 task.yaml 契约"""
        assert check_task.is_exempt("docs/tasks/2026-07-23-refactor-task-artifact-contract") is False
        assert check_task.is_exempt("docs/tasks/2026-08-01-new-task") is False
        assert check_task.is_exempt("docs/tasks/2027-01-01-future-task") is False


@pytest.mark.skipif(not HAS_SCRIPT, reason="check_task module not importable")
class TestIndexView:
    """Spec § 7.6: INDEX 视图校验"""

    def test_read_task_yaml_worktree(self, tmp_path):
        """INDEX view requires git repo; worktree view uses regular read"""
        task_dir = tmp_path / "docs" / "tasks" / "2026-07-24-test"
        task_dir.mkdir(parents=True)
        (task_dir / "task.yaml").write_text((FIXTURES / "valid_minimal.yaml").read_text())

        # Worktree view (no git needed)
        content = check_task.read_task_yaml(str(task_dir), view="worktree")
        assert "task/v1" in content

    def test_read_task_yaml_index_requires_git(self, tmp_path):
        """INDEX view must see artifacts staged in the index, not only HEAD."""
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
        task_dir = Path("docs/tasks/2026-07-24-test-ui")
        absolute_task_dir = tmp_path / task_dir
        (absolute_task_dir / "mockups").mkdir(parents=True)
        yaml_content = (FIXTURES / "valid_full_ui.yaml").read_text()
        yaml_content = yaml_content.replace(
            "task_id: 2026-07-24-test-ui-task",
            "task_id: 2026-07-24-test-ui",
        )
        (absolute_task_dir / "task.yaml").write_text(yaml_content)
        (absolute_task_dir / "design-spec.md").write_text("# design\n")
        (absolute_task_dir / "component-spec.md").write_text("# component\n")
        (absolute_task_dir / "mockups/index.html").write_text("<!doctype html>\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)

        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            errors = check_task.validate_dir(str(task_dir), view="index")
        finally:
            os.chdir(old_cwd)

        assert errors == [], errors

    def test_index_validation_ignores_unstaged_worktree_deletion(self, tmp_path):
        """A staged manifest remains authoritative if worktree deletes it later."""
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        task_dir = Path("docs/tasks/2026-07-24-index-only")
        absolute_task_dir = tmp_path / task_dir
        absolute_task_dir.mkdir(parents=True)
        yaml_content = (FIXTURES / "valid_minimal.yaml").read_text().replace(
            "task_id: 2026-07-24-test-task",
            "task_id: 2026-07-24-index-only",
        )
        manifest = absolute_task_dir / "task.yaml"
        manifest.write_text(yaml_content)
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        manifest.unlink()

        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            errors = check_task.validate_dir(str(task_dir), view="index")
        finally:
            os.chdir(old_cwd)

        assert errors == [], errors


@pytest.mark.skipif(not HAS_SCRIPT, reason="check_task module not importable")
class TestPathMode:
    """Spec § 1 REQ-2: 路径模式限制 current_step 范围"""

    def test_fix_mini_restricts_steps(self):
        """fix-mini 只能 0/4/6"""
        data = {
            "schema": "task/v1",
            "task_id": "2026-07-24-test",
            "mode": "fix-mini",
            "current_step": 5,  # not in {0, 4, 6}
            "step_state": "in_progress",
            "triggers": {"ui_design": False, "ui_components": False, "api_change": False, "db_change": False},
            "test_evidence": {"type": "pending"},
        }
        errors = check_task.validate_yaml(data, "2026-07-24-test")
        assert any("E002" in e for e in errors), f"Expected E002 in: {errors}"

    def test_full_6_allows_any_step(self):
        """full-6 允许 0-6"""
        for step in [0, 1, 2, 3, 4, 5, 6]:
            data = {
                "schema": "task/v1",
                "task_id": "2026-07-24-test",
                "mode": "full-6",
                "current_step": step,
                "step_state": "in_progress",
                "triggers": {"ui_design": False, "ui_components": False, "api_change": False, "db_change": False},
                "test_evidence": {"type": "pending"},
            }
            errors = check_task.validate_yaml(data, "2026-07-24-test")
            assert not any("E002" in e for e in errors), f"Step {step} should be valid in full-6"
