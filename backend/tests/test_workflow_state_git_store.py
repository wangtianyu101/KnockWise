"""Git-backed workflow-state bootstrap and read-only store tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_state.git_store import (  # noqa: E402
    FORMAT_CONTENT,
    STATE_REF,
    GitStateStore,
    StateStoreError,
)


GIT_LOCAL_ENV_KEYS = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_DIR",
    "GIT_GRAFT_FILE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_WORK_TREE",
}


def _clean_git_env():
    environment = os.environ.copy()
    for key in GIT_LOCAL_ENV_KEYS:
        environment.pop(key, None)
    return environment


def _git(repo: Path, *args: str, input_bytes: Optional[bytes] = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        capture_output=True,
        check=True,
        env=_clean_git_env(),
    )
    return result.stdout.decode("utf-8").strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Workflow State Tests")
    _git(repo, "config", "user.email", "workflow-state@example.invalid")
    (repo / "business.txt").write_text("business branch\n")
    _git(repo, "add", "business.txt")
    _git(repo, "commit", "-qm", "business root")
    return repo


def _commit_format(repo: Path, content: bytes | None) -> str:
    env = _clean_git_env()
    index_path = repo / ".git" / "test-state-index"
    env["GIT_INDEX_FILE"] = str(index_path)
    subprocess.run(
        ["git", "read-tree", "--empty"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
    )
    if content is not None:
        blob = _git(repo, "hash-object", "-w", "--stdin", input_bytes=content)
        subprocess.run(
            [
                "git",
                "update-index",
                "--add",
                "--cacheinfo",
                f"100644,{blob},FORMAT",
            ],
            cwd=repo,
            env=env,
            check=True,
            capture_output=True,
        )
    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    commit = _git(repo, "commit-tree", tree, input_bytes=b"state fixture\n")
    index_path.unlink(missing_ok=True)
    _git(repo, "update-ref", STATE_REF, commit)
    return commit


def test_bootstrap_creates_orphan_state_ref_without_touching_business_head(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    (repo / "business.txt").write_text("uncommitted business change\n")
    business_head = _git(repo, "rev-parse", "HEAD")
    business_status = _git(repo, "status", "--porcelain=v1")

    state_head = store.bootstrap()

    assert state_head == _git(repo, "rev-parse", STATE_REF)
    assert _git(repo, "rev-list", "--parents", "-n", "1", state_head) == state_head
    assert _git(repo, "show", f"{state_head}:FORMAT") + "\n" == FORMAT_CONTENT.decode()
    assert _git(repo, "rev-parse", "HEAD") == business_head
    assert _git(repo, "status", "--porcelain=v1") == business_status
    assert (repo / "business.txt").read_text() == "uncommitted business change\n"


def test_bootstrap_is_idempotent_when_supported_state_ref_exists(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)

    first = store.bootstrap()
    second = store.bootstrap()

    assert second == first
    assert _git(repo, "rev-list", "--count", STATE_REF) == "1"


def test_load_snapshot_is_read_only_and_returns_immutable_bytes(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    state_head = store.bootstrap()
    business_head = _git(repo, "rev-parse", "HEAD")

    snapshot = store.load_snapshot()

    assert snapshot.commit == state_head
    assert snapshot.files == {"FORMAT": FORMAT_CONTENT}
    with pytest.raises(TypeError):
        snapshot.files["manual.txt"] = b"not allowed"
    assert _git(repo, "rev-parse", STATE_REF) == state_head
    assert _git(repo, "rev-parse", "HEAD") == business_head
    assert _git(repo, "status", "--porcelain=v1") == ""


@pytest.mark.parametrize(
    ("content", "error_code"),
    [
        (None, "format_missing"),
        (b"workflow-state/v999\n", "format_unsupported"),
        (b"workflow-state/v1", "format_unsupported"),
    ],
)
def test_existing_state_ref_with_missing_or_unsupported_format_fails_closed(
    tmp_path,
    content,
    error_code,
):
    repo = _repo(tmp_path)
    bad_head = _commit_format(repo, content)
    store = GitStateStore(repo)

    with pytest.raises(StateStoreError) as exc_info:
        store.bootstrap()

    assert exc_info.value.code == error_code
    assert _git(repo, "rev-parse", STATE_REF) == bad_head
    assert _git(repo, "rev-list", "--count", STATE_REF) == "1"


def test_missing_state_ref_load_fails_closed_without_bootstrapping(tmp_path):
    repo = _repo(tmp_path)

    with pytest.raises(StateStoreError) as exc_info:
        GitStateStore(repo).load_snapshot()

    assert exc_info.value.code == "state_ref_missing"
    assert (
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", STATE_REF],
            cwd=repo,
            env=_clean_git_env(),
        ).returncode
        != 0
    )


def test_temporary_worktree_is_detached_and_always_cleaned_up(tmp_path):
    repo = _repo(tmp_path)
    store = GitStateStore(repo)
    state_head = store.bootstrap()

    with pytest.raises(RuntimeError, match="probe failure"):
        with store.temporary_worktree() as worktree:
            worktree_path = worktree
            assert worktree.is_dir()
            assert (worktree / "FORMAT").read_bytes() == FORMAT_CONTENT
            assert _git(worktree, "rev-parse", "HEAD") == state_head
            assert (
                subprocess.run(
                    ["git", "symbolic-ref", "-q", "HEAD"],
                    cwd=worktree,
                    capture_output=True,
                    env=_clean_git_env(),
                ).returncode
                != 0
            )
            raise RuntimeError("probe failure")

    assert not worktree_path.exists()
    assert str(worktree_path) not in _git(repo, "worktree", "list", "--porcelain")


def test_non_repository_fails_with_stable_error(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()

    with pytest.raises(StateStoreError) as exc_info:
        GitStateStore(plain).bootstrap()

    assert exc_info.value.code == "not_git_repository"


def test_store_ignores_inherited_local_git_environment(tmp_path, monkeypatch):
    target = _repo(tmp_path / "target")
    foreign = _repo(tmp_path / "foreign")
    foreign_head = _git(foreign, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_DIR", str(foreign / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(foreign))
    monkeypatch.setenv("GIT_INDEX_FILE", str(foreign / ".git" / "index"))

    state_head = GitStateStore(target).bootstrap()

    assert state_head == _git(target, "rev-parse", STATE_REF)
    assert _git(foreign, "rev-parse", "HEAD") == foreign_head
    assert (
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", STATE_REF],
            cwd=foreign,
            env=_clean_git_env(),
        ).returncode
        != 0
    )
