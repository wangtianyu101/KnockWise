#!/usr/bin/env python3
"""Unit tests for check_auto_fix_diff.py (Decision 4+5 / R3+R4 / T9)."""
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_auto_fix_diff import (  # noqa: E402
    check,
    SERVICE_PATH_PREFIX,
    NO_TEST_MARKER,
)


def _setup_git_repo():
    """Create a temp git repo with 2 commits. Returns (repo_path, HEAD~1_sha, HEAD_sha)."""
    tmp = tempfile.mkdtemp()
    repo = Path(tmp)
    # Init
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, capture_output=True, check=True)
    # Commit 1: empty
    (repo / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, capture_output=True, check=True)
    return repo


def test_service_file_change_needs_review():
    """TC-A1: backend/services/*.py change → needs_review=true."""
    repo = _setup_git_repo()
    try:
        # Commit 2: add service file (mkdir first)
        (repo / "backend/services").mkdir(parents=True)
        (repo / "backend/services/foo.py").write_text("# foo service")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add service"], cwd=repo, capture_output=True, check=True)
        # Now check from this repo
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, '{Path(__file__).parent}'); "
             f"from check_auto_fix_diff import check; print(check())"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        # Parse output: it's a dict printed via __str__
        assert "needs_review': True" in result.stdout or "'needs_review': True" in result.stdout
    finally:
        subprocess.run(["rm", "-rf", str(repo)], capture_output=True)


def test_test_file_only_no_review():
    """TC-A2: diff contains only test_*.py → needs_review=false."""
    repo = _setup_git_repo()
    try:
        (repo / "tests").mkdir()
        (repo / "tests/test_foo.py").write_text("# test")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add test"], cwd=repo, capture_output=True, check=True)
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, '{Path(__file__).parent}'); "
             f"from check_auto_fix_diff import check; print(check())"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        assert "'needs_review': False" in result.stdout
    finally:
        subprocess.run(["rm", "-rf", str(repo)], capture_output=True)


def test_empty_diff_no_review():
    """TC-A3: empty diff → no review + warning."""
    repo = _setup_git_repo()
    try:
        # No second commit, diff is empty
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, '{Path(__file__).parent}'); "
             f"from check_auto_fix_diff import check; print(check())"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        assert "'needs_review': False" in result.stdout
        assert "'test_files': []" in result.stdout
    finally:
        subprocess.run(["rm", "-rf", str(repo)], capture_output=True)


def test_no_test_needed_marker_rejected():
    """TC-A4 (v2 critical): commit msg with [NO-TEST-NEEDED] → exit 1."""
    repo = _setup_git_repo()
    try:
        (repo / "tests").mkdir()
        (repo / "tests/test_foo.py").write_text("# test")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add test [NO-TEST-NEEDED]"],
                       cwd=repo, capture_output=True, check=True)
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "check_auto_fix_diff.py")],
            cwd=repo, capture_output=True, text=True,
        )
        assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
        assert "self-attestation not allowed" in result.stderr or "self-attestation not allowed" in result.stdout
    finally:
        subprocess.run(["rm", "-rf", str(repo)], capture_output=True)


def test_service_plus_test_still_needs_review():
    """TC-A5: service + test files → still needs_review=true (service takes precedence)."""
    repo = _setup_git_repo()
    try:
        (repo / "backend/services").mkdir(parents=True)
        (repo / "tests").mkdir()
        (repo / "backend/services/foo.py").write_text("# service")
        (repo / "tests/test_foo.py").write_text("# test")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "both"], cwd=repo, capture_output=True, check=True)
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.path.insert(0, '{Path(__file__).parent}'); "
             f"from check_auto_fix_diff import check; print(check())"],
            cwd=repo, capture_output=True, text=True, check=True,
        )
        assert "'needs_review': True" in result.stdout
    finally:
        subprocess.run(["rm", "-rf", str(repo)], capture_output=True)


def test_service_path_prefix_correct():
    """TC-A6: SERVICE_PATH_PREFIX matches backend/services/."""
    assert SERVICE_PATH_PREFIX == "backend/services/"
    assert NO_TEST_MARKER == "[NO-TEST-NEEDED]"


if __name__ == "__main__":
    tests = [
        test_service_file_change_needs_review,
        test_test_file_only_no_review,
        test_empty_diff_no_review,
        test_no_test_needed_marker_rejected,
        test_service_plus_test_still_needs_review,
        test_service_path_prefix_correct,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
        except (AssertionError, subprocess.CalledProcessError) as e:
            print(f"❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)