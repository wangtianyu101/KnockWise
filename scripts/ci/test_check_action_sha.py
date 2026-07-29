#!/usr/bin/env python3
"""Unit tests for check_action_sha.py (Decision 7 / R8 / T18)."""
import sys
import json
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_action_sha import (  # noqa: E402
    check_workflow,
    check_workflows,
    MOVING_TAGS,
)

CHECKER_PATH = Path(__file__).with_name("check_action_sha.py")


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


class _ProvenanceHandler(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, dict]] = {}

    def do_GET(self):  # noqa: N802
        status, payload = self.routes.get(
            self.path, (404, {"message": "Not Found"})
        )
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def _run_remote_check(workflow: str, routes: dict[str, tuple[int, dict]]):
    with tempfile.TemporaryDirectory() as tmp:
        workflows_dir = Path(tmp)
        (workflows_dir / "test.yml").write_text(workflow, encoding="utf-8")
        _ProvenanceHandler.routes = routes
        server = ThreadingHTTPServer(("127.0.0.1", 0), _ProvenanceHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            return subprocess.run(
                [
                    sys.executable,
                    str(CHECKER_PATH),
                    "--workflows-dir",
                    str(workflows_dir),
                    "--verify-remote",
                    "--api-base",
                    f"http://127.0.0.1:{server.server_port}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


def test_remote_provenance_accepts_matching_repository_sha():
    """TC-P0-3 happy path: repository commit endpoint returns the same SHA."""
    sha = "a" * 40
    workflow = f"""
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/upload-artifact@{sha}
"""
    result = _run_remote_check(
        workflow,
        {f"/repos/actions/upload-artifact/git/commits/{sha}": (200, {"sha": sha})},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "provenance verified" in result.stdout


def test_remote_provenance_rejects_fake_40_character_sha():
    """TC-P0-3 regression: shape-valid but missing SHA must fail closed."""
    sha = "b" * 40
    workflow = f"""
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: anthropics/claude-code-action@{sha}
"""
    result = _run_remote_check(workflow, {})
    assert result.returncode == 1
    assert "not found" in result.stdout.lower()
    assert "anthropics/claude-code-action" in result.stdout


def test_remote_provenance_rejects_mismatched_response_sha():
    """TC-P0-3: a 200 response for another SHA is not sufficient."""
    sha = "c" * 40
    workflow = f"""
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@{sha}
"""
    result = _run_remote_check(
        workflow,
        {
            f"/repos/actions/download-artifact/git/commits/{sha}": (
                200,
                {"sha": "d" * 40},
            )
        },
    )
    assert result.returncode == 1
    assert "mismatch" in result.stdout.lower()


def test_remote_provenance_network_or_server_error_is_blocked():
    """TC-P0-4: upstream uncertainty must never become PASS."""
    sha = "e" * 40
    workflow = f"""
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{sha}
"""
    result = _run_remote_check(
        workflow,
        {
            f"/repos/actions/checkout/git/commits/{sha}": (
                503,
                {"message": "unavailable"},
            )
        },
    )
    assert result.returncode == 1
    assert "blocked" in result.stdout.lower()


def test_remote_provenance_cache_key_includes_repository():
    """TC-P0-5: the same SHA in another repository needs its own proof."""
    sha = "f" * 40
    workflow = f"""
name: test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/upload-artifact@{sha}
      - uses: anthropics/claude-code-action@{sha}
"""
    result = _run_remote_check(
        workflow,
        {
            f"/repos/actions/upload-artifact/git/commits/{sha}": (
                200,
                {"sha": sha},
            )
        },
    )
    assert result.returncode == 1
    assert "anthropics/claude-code-action" in result.stdout


if __name__ == "__main__":
    tests = [
        test_beta_tag_rejected,
        test_main_tag_rejected,
        test_v1_tag_rejected,
        test_full_sha_accepted,
        test_local_action_not_checked,
        test_moving_tags_list_complete,
        test_remote_provenance_accepts_matching_repository_sha,
        test_remote_provenance_rejects_fake_40_character_sha,
        test_remote_provenance_rejects_mismatched_response_sha,
        test_remote_provenance_network_or_server_error_is_blocked,
        test_remote_provenance_cache_key_includes_repository,
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
