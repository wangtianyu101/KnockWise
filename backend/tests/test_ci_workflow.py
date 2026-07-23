"""Static contract tests for the GitHub Actions CI workflow."""
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_ci_defines_three_independent_gates():
    content = workflow_text()

    assert "  test-quality:" in content
    assert "  backend-test:" in content
    assert "  frontend-test:" in content
    assert "continue-on-error" not in content


def test_ci_runs_quality_checker_as_a_blocking_command():
    content = workflow_text()

    assert "python scripts/check_test_quality.py backend/tests" in content


def test_backend_gate_uses_mysql_and_real_integration_flag():
    content = workflow_text()

    assert "image: mysql:8.4" in content
    assert 'RUN_MYSQL_INTEGRATION: "1"' in content
    assert "mysqladmin ping" in content
    assert "tests/integration/test_mysql_ci.py" in content


def test_backend_gate_enforces_recorded_coverage_thresholds():
    content = workflow_text()

    assert "--cov-branch" in content
    assert "--global-lines 61" in content
    assert "--file-lines 80" in content
    assert "--file-branches 70" in content


def test_frontend_gate_runs_tests_types_and_build():
    content = workflow_text()

    assert "npm test" in content
    assert "npx tsc --noEmit" in content
    assert "npm run build" in content


def test_ci_uses_pinned_action_shas_and_read_only_permissions():
    content = workflow_text()

    assert "permissions:\n  contents: read" in content
    # R8 / Decision 7: 第三方 Actions 必须 pin 完整 40 字符 SHA（非 @v6 / @beta 等移动 tag）
    # SHA 来源：commit 66efa3c（2026-07-22 R8）· 同步由 scripts/ci/check_action_sha.py 机器化兜底
    assert "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" in content
    assert "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1" in content
    assert "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38" in content
