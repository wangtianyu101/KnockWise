"""Regression tests for the AST-based empty-test quality gate."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "check_test_quality.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_test_quality", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return _load_checker()


def _write_test(tmp_path: Path, source: str, name: str = "test_sample.py") -> Path:
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        ("def test_empty():\n    pass\n", "empty-test"),
        ("def test_ellipsis():\n    ...\n", "empty-test"),
        ('def test_docstring_only():\n    """Nothing yet."""\n', "empty-test"),
        ("async def test_async_empty():\n    pass\n", "empty-test"),
        ("def test_todo():\n    # TODO: implement assertion\n    result = run()\n", "placeholder-marker"),
        (
            'def test_stub():\n    """Placeholder until the API exists."""\n    result = run()\n',
            "placeholder-marker",
        ),
    ],
)
def test_scan_flags_empty_and_placeholder_tests(tmp_path, checker, source, expected_code):
    test_file = _write_test(tmp_path, source)

    violations = checker.scan_paths([test_file])

    assert [violation.code for violation in violations] == [expected_code]
    assert violations[0].path == test_file


@pytest.mark.parametrize(
    "source",
    [
        "def test_assertion():\n    assert calculate() == 42\n",
        "def test_raises():\n    with pytest.raises(ValueError):\n        parse_bad_input()\n",
        "def test_mock_assertion():\n    service()\n    mock.assert_called_once()\n",
        "def test_helper_contract():\n    assert_response_matches_contract(call_api())\n",
        (
            "def test_real_placeholder_behavior():\n"
            "    field = render_input()\n"
            "    assert field.placeholder == 'Search'\n"
        ),
    ],
)
def test_scan_accepts_real_verification_styles(tmp_path, checker, source):
    test_file = _write_test(tmp_path, source)

    assert checker.scan_paths([test_file]) == []


def test_scan_ignores_non_test_helpers(tmp_path, checker):
    test_file = _write_test(
        tmp_path,
        "def helper_not_implemented():\n    pass\n\n"
        "class FakeBoundary:\n    async def fetch(self):\n        ...\n",
    )

    assert checker.scan_paths([test_file]) == []


@pytest.mark.parametrize(
    "source",
    [
        "@pytest.mark.skip\ndef test_skip_without_reason():\n    assert False\n",
        "@pytest.mark.skip()\ndef test_skip_without_reason():\n    assert False\n",
        "@pytest.mark.skipif(condition)\ndef test_skipif_without_reason():\n    assert False\n",
        "def test_runtime_skip_without_reason():\n    pytest.skip()\n",
    ],
)
def test_scan_rejects_skip_without_reason(tmp_path, checker, source):
    test_file = _write_test(tmp_path, source)

    violations = checker.scan_paths([test_file])

    assert [violation.code for violation in violations] == ["skip-without-reason"]


@pytest.mark.parametrize(
    "source",
    [
        "@pytest.mark.skip(reason='Requires optional MySQL fixture')\n"
        "def test_documented_skip():\n    assert False\n",
        "@pytest.mark.skipif(condition, reason='Issue #123: not supported on CI')\n"
        "def test_documented_skipif():\n    assert False\n",
        "def test_documented_runtime_skip():\n"
        "    pytest.skip('Seed file is not installed in this environment')\n",
    ],
)
def test_scan_accepts_skip_with_reason(tmp_path, checker, source):
    test_file = _write_test(tmp_path, source)

    assert checker.scan_paths([test_file]) == []


def test_scan_rejects_class_level_skip_without_reason(tmp_path, checker):
    test_file = _write_test(
        tmp_path,
        "@pytest.mark.skip\n"
        "class TestSkippedSuite:\n"
        "    def test_hidden_failure(self):\n"
        "        assert False\n",
    )

    violations = checker.scan_paths([test_file])

    assert [violation.code for violation in violations] == ["skip-without-reason"]
    assert violations[0].test_name == "test_hidden_failure"


def test_scan_accepts_documented_class_level_skip(tmp_path, checker):
    test_file = _write_test(
        tmp_path,
        "@pytest.mark.skip(reason='Issue #456: fixture is unavailable')\n"
        "class TestSkippedSuite:\n"
        "    def test_hidden_failure(self):\n"
        "        assert False\n",
    )

    assert checker.scan_paths([test_file]) == []


def test_scan_reports_syntax_errors_instead_of_silently_ignoring_them(tmp_path, checker):
    test_file = _write_test(tmp_path, "def test_broken(:\n    pass\n")

    violations = checker.scan_paths([test_file])

    assert [violation.code for violation in violations] == ["syntax-error"]


def test_cli_returns_nonzero_for_bad_test_and_zero_for_clean_test(tmp_path):
    bad_file = _write_test(tmp_path, "def test_empty():\n    pass\n", "test_bad.py")
    clean_file = _write_test(tmp_path, "def test_real():\n    assert 1 + 1 == 2\n", "test_clean.py")

    bad = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(bad_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    clean = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(clean_file)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert bad.returncode == 1
    assert "empty-test" in bad.stdout
    assert clean.returncode == 0
    assert "0 violation" in clean.stdout
