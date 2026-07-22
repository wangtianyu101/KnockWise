#!/usr/bin/env python3
"""Unit tests for check_action_sha.py (Decision 7 / R8 / T18)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_action_sha import (  # noqa: E402
    check_workflow,
    check_workflows,
    MOVING_TAGS,
)


def _write_workflow(content: str) -> Path:
    """Write a temp workflow file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, dir=tempfile.gettempdir()
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_beta_tag_rejected():
    """TC-SHA1: @beta moving tag → violation."""
    content = """
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@beta
"""
    path = _write_workflow(content)
    violations = check_workflow(path)
    path.unlink()
    assert len(violations) == 1
    assert "@beta" in violations[0][2]


def test_main_tag_rejected():
    """TC-SHA2: @main moving tag → violation."""
    content = """
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@main
"""
    path = _write_workflow(content)
    violations = check_workflow(path)
    path.unlink()
    assert len(violations) == 1
    assert "@main" in violations[0][2]


def test_v1_tag_rejected():
    """TC-SHA3: @v1 floating tag → violation."""
    content = """
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v1
"""
    path = _write_workflow(content)
    violations = check_workflow(path)
    path.unlink()
    assert len(violations) == 1
    assert "@v1" in violations[0][2]


def test_full_sha_accepted():
    """TC-SHA4: Full 40-char SHA → no violation."""
    content = """
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@a1b2c3d4e5f6789012345678901234567890abcd
      - uses: anthropics/claude-code-action@1234567890abcdef1234567890abcdef12345678
"""
    path = _write_workflow(content)
    violations = check_workflow(path)
    path.unlink()
    assert len(violations) == 0


def test_local_action_not_checked():
    """Local actions (./...) should not be checked for SHA."""
    content = """
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: ./local-action
"""
    path = _write_workflow(content)
    violations = check_workflow(path)
    path.unlink()
    assert len(violations) == 0


def test_moving_tags_list_complete():
    """MOVING_TAGS contains the common moving tags."""
    assert "beta" in MOVING_TAGS
    assert "main" in MOVING_TAGS
    assert "v1" in MOVING_TAGS
    assert "latest" in MOVING_TAGS


if __name__ == "__main__":
    tests = [
        test_beta_tag_rejected,
        test_main_tag_rejected,
        test_v1_tag_rejected,
        test_full_sha_accepted,
        test_local_action_not_checked,
        test_moving_tags_list_complete,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)