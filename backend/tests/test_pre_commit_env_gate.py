"""回归测试：scripts/pre-commit 的环境 Gate 必须 fail-closed。

P0-2 修复（decisions.md 决策 1）：

  原代码：`.venv` 或 `node_modules` 缺失时仅 warning 并跳过 pytest/tsc。
  问题：环境缺失时 Gate 假装成功（"✅ pre-commit 全部通过"），实际未运行测试。

  修复策略：风险范围感知的 fail closed + 最小健康探针。
  - 相关 backend/frontend 可执行/测试/依赖配置改动 → 必须有健康 Gate。
  - 测试文件与生产代码同等要求真实运行。
  - 纯 docs 不触发应用环境检查（已有 DOD check 兜底）。
  - 错误提示用真实恢复命令（删 setup.sh 误导指引）。

8 个场景（research.md § 6.4）：
  1. 纯 docs 改动、环境均缺失 → 不检查应用环境（不应阻断）
  2. 后端相关改动、`.venv` 缺失 → 阻断
  3. `.venv` 存在但 Python 不可执行 → 阻断
  4. Python 可执行但 pytest 探针失败 → 阻断
  5. 环境健康但 pytest 真失败 → 阻断
  6. 前端相关改动、tsc 缺失 → 阻断
  7. tsc 存在但执行失败 → 阻断
  8. 环境健康 + pytest/tsc 成功 → 通过

修复前场景 2/3/4/6/7 必须 RED（hook 假绿放过）；修复后必须 GREEN。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
HOOK_SRC = REPO_ROOT / "scripts" / "pre-commit"


# ─── 临时 git repo + 环境 mock 工具函数 ────────────────────────────

def _init_tmp_repo(
    staged_relpaths: list[tuple[str, str]],
    *,
    with_venv: str | None = "healthy",  # None=缺失 | "broken_exec"=不可执行 | "broken_pytest"=探针失败 | "healthy"=可用
    with_node_modules: str | None = "healthy",  # 同上语义，但语义对 tsc
    copy_check_step: bool = False,
) -> Path:
    """初始化临时 git repo，复制 hook，可选 mock 环境。

    - staged_relpaths: [(相对路径, 内容), ...]
    - with_venv:
        - None: 不创建 .venv（缺失）
        - "broken_exec": 创建空 .venv/bin/python 且无执行权限
        - "broken_pytest": 创建可执行 python 包装器，`-m pytest --version` 失败
        - "healthy": 创建真实可用 .venv（如能 link 主机 venv，否则 fallback）
    - with_node_modules: 同上但对 tsc
    """
    tmp = Path(tempfile.mkdtemp(prefix="precommit-env-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "t@t.local"],
            cwd=tmp, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "t"],
            cwd=tmp, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"],
            cwd=tmp, check=True, capture_output=True,
        )
        # 复制 hook
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        shutil.copy(HOOK_SRC, scripts_dir / "pre-commit")
        if copy_check_step:
            shutil.copy(
                REPO_ROOT / "scripts" / "check-step.py",
                scripts_dir / "check-step.py",
            )
        # Mock backend/.venv
        if with_venv is not None:
            _mock_backend_venv(tmp / "backend" / ".venv", with_venv)
        # Mock frontend/node_modules
        if with_node_modules is not None:
            _mock_frontend_node_modules(tmp / "frontend" / "node_modules", with_node_modules)
        # 暂存文件
        for relpath, content in staged_relpaths:
            staged = tmp / relpath
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(content, encoding="utf-8")
            subprocess.run(
                ["git", "add", relpath],
                cwd=tmp, check=True, capture_output=True,
            )
        return tmp
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def _mock_backend_venv(venv_path: Path, mode: str) -> None:
    """Mock backend/.venv/bin/python 的 4 种状态。"""
    bin_dir = venv_path / "bin"
    bin_dir.mkdir(parents=True)
    if mode == "broken_exec":
        # 空文件 + 无执行权限
        (bin_dir / "python").write_text("")
        (bin_dir / "python").chmod(0o644)
    elif mode == "broken_pytest":
        # 可执行但 `-m pytest --version` 失败
        wrapper = bin_dir / "python"
        wrapper.write_text(
            "#!/bin/sh\necho 'ImportError: pytest not installed' >&2\nexit 1\n"
        )
        wrapper.chmod(0o755)
        # 同时 mock pytest binary 让 -m pytest 调用失败（wrapper 已 exit 1 即可）
    elif mode == "healthy":
        # 通过 wrapper script 调用 host venv 的 python（保留 venv site-packages）
        # 直接 symlink 不行 —— python 通过 symlink 调用时 sys.executable 指向真实 binary，
        # 找不到 venv site-packages，所以 `import pytest` 失败。
        host_python = REPO_ROOT / "backend" / ".venv" / "bin" / "python"
        if not host_python.exists():
            pytest.fail(
                "healthy mode requires host backend/.venv to exist; "
                "run `./scripts/setup.sh` first"
            )
        wrapper = bin_dir / "python"
        wrapper.write_text(
            "#!/bin/sh\nexec " + str(host_python) + ' "$@"\n'
        )
        wrapper.chmod(0o755)


def _mock_frontend_node_modules(nm_path: Path, mode: str) -> None:
    """Mock frontend/node_modules/.bin/tsc 的 4 种状态。"""
    bin_dir = nm_path / ".bin"
    bin_dir.mkdir(parents=True)
    if mode == "broken_exec":
        (bin_dir / "tsc").write_text("")
        (bin_dir / "tsc").chmod(0o644)
    elif mode == "broken_pytest":  # 对前端 = "broken_tsc"
        wrapper = bin_dir / "tsc"
        wrapper.write_text(
            "#!/bin/sh\necho 'tsc: command parse error' >&2\nexit 1\n"
        )
        wrapper.chmod(0o755)
    elif mode == "healthy":
        # 真实可用 tsc：链接到 frontend/node_modules/.bin/tsc
        host_tsc = REPO_ROOT / "frontend" / "node_modules" / ".bin" / "tsc"
        if host_tsc.exists():
            os.symlink(host_tsc, bin_dir / "tsc")
        else:
            # Fallback: 写一个假 tsc（永远 exit 0）
            wrapper = bin_dir / "tsc"
            wrapper.write_text("#!/bin/sh\necho 'fake tsc' ; exit 0\n")
            wrapper.chmod(0o755)


# ─── 跑 hook 工具 ───────────────────────────────────────────

def _run_hook(tmp: Path):
    env = os.environ.copy()
    # 测试 fixture 下跳过 § 6.5 tasks.md 同步校验（与本测试无关）
    env["SKIP_TASKS_SYNC"] = "1"
    return subprocess.run(
        ["sh", "scripts/pre-commit"],
        cwd=tmp,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


@pytest.fixture
def cleanup_tmp():
    """每个测试后清理临时目录。"""
    cleanup_paths: list[Path] = []

    def _track(p: Path) -> Path:
        cleanup_paths.append(p)
        return p

    yield _track
    for p in cleanup_paths:
        shutil.rmtree(p, ignore_errors=True)


# ─── 场景 1：纯 docs 改动、环境均缺失 → 不检查应用环境 ──────────

class TestDocsOnlyNotTriggerEnvGate:
    """纯 docs commit 不应触发 backend/frontend 环境 Gate。"""

    def test_pure_docs_with_no_env_passes(
        self, cleanup_tmp,
    ):
        # 暂存一个合法但不触发 DOD 的 docs 文件（不以 research/spec/plan/tasks/test-cases/verify/retro 命名）
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("docs/README.md", "# readme\n"),
                ],
                with_venv=None,           # 环境缺失
                with_node_modules=None,   # 环境缺失
            )
        )
        result = _run_hook(tmp)

        # 不应阻断（不要求 docs commit 安装 venv）
        assert result.returncode == 0, (
            f"纯 docs commit 不应被环境 Gate 阻断。stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


# ─── 场景 2：后端相关改动、.venv 缺失 → 阻断 ─────────────────────

class TestBackendGateBlocksMissingVenv:
    """后端相关改动但 `.venv` 缺失时必须阻断。"""

    def test_backend_change_without_venv_blocks(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("backend/services/example_service.py", "# stub\n"),
                ],
                with_venv=None,
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"后端相关改动 + .venv 缺失未阻断 commit。stdout:\n{result.stdout}"
        )
        # 必须给出真实恢复命令（不能用 setup.sh 误导指引）
        # 关键：阻断信息中应包含可执行恢复命令（pip / venv / requirements）
        out = result.stdout + result.stderr
        # 任意一个真实恢复关键词命中
        recovery_hits = sum(1 for kw in [
            "backend/.venv/bin/python", "pip install", "requirements.txt",
            "python -m venv", "npm ci",
        ] if kw in out)
        assert recovery_hits >= 1, (
            f"阻断信息应含真实恢复命令，但 stdout/stderr 中未命中关键词：\n{out}"
        )
        # 不应再引用误导的 scripts/setup.sh
        assert "scripts/setup.sh" not in out, (
            f"阻断信息不应再引用不存在的 scripts/setup.sh：\n{out}"
        )


# ─── 场景 3：.venv 存在但 Python 不可执行 → 阻断 ───────────────

class TestBackendGateBlocksBrokenPython:
    """`.venv` 存在但 binary 不可执行时必须阻断。"""

    def test_backend_change_with_broken_python_blocks(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("backend/services/example_service.py", "# stub\n"),
                ],
                with_venv="broken_exec",
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f".venv/bin/python 不可执行未阻断 commit。stdout:\n{result.stdout}"
        )


# ─── 场景 4：Python 可执行但 pytest 探针失败 → 阻断 ────────────

class TestBackendGateBlocksBrokenPytest:
    """Python 可执行但 `pytest --version` 探针失败时必须阻断。"""

    def test_backend_change_with_broken_pytest_blocks(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("backend/services/example_service.py", "# stub\n"),
                ],
                with_venv="broken_pytest",
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"pytest 探针失败未阻断 commit。stdout:\n{result.stdout}"
        )


# ─── 场景 5：环境健康但 pytest 真失败 → 阻断（保留 P0-1 行为）──

class TestBackendGateBlocksPytestFailure:
    """环境健康但 pytest 真失败时必须阻断（这是 P0-1 已修的部分）。"""

    def test_backend_change_with_pytest_failure_blocks(
        self, cleanup_tmp,
    ):
        # 暂存一个故意让 collect 失败的 pytest 测试
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("backend/tests/test_crash.py", "def test_x(:\n"),  # syntax error
                ],
                with_venv="healthy",
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"pytest 实际失败未阻断 commit。stdout:\n{result.stdout}"
        )


# ─── 场景 6：前端相关改动、tsc 缺失 → 阻断 ─────────────────────

class TestFrontendGateBlocksMissingTsc:
    """前端相关改动但 tsc 缺失时必须阻断。"""

    def test_frontend_change_without_tsc_blocks(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("frontend/components/Button.tsx", "export const Button = () => null;\n"),
                ],
                with_node_modules=None,
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"前端相关改动 + tsc 缺失未阻断 commit。stdout:\n{result.stdout}"
        )
        # 阻断信息应含 npm ci 真实恢复命令
        out = result.stdout + result.stderr
        assert "npm ci" in out or "npm install" in out, (
            f"阻断信息应含 npm ci/npm install 真实恢复命令：\n{out}"
        )


# ─── 场景 7：tsc 存在但执行失败 → 阻断 ────────────────────────

class TestFrontendGateBlocksTscFailure:
    """tsc 存在但执行失败时必须阻断。"""

    def test_frontend_change_with_broken_tsc_blocks(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("frontend/components/Button.tsx", "export const Button = () => null;\n"),
                ],
                with_node_modules="broken_exec",
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"tsc 不可执行未阻断 commit。stdout:\n{result.stdout}"
        )


# ─── 场景 8：环境健康 + pytest/tsc 成功 → 通过 ────────────────

class TestEnvGatePassesWhenHealthy:
    """环境健康且 Gate 成功时不阻断 commit。"""

    def test_backend_change_with_healthy_env_passes(
        self, cleanup_tmp,
    ):
        # 提供一个能 PASS 的测试 + 健康 venv → hook 应通过
        tmp = cleanup_tmp(
            _init_tmp_repo(
                staged_relpaths=[
                    ("backend/services/example_service.py", "# stub\n"),
                    ("backend/tests/test_pass.py", "def test_pass():\n    assert True\n"),
                ],
                with_venv="healthy",
            )
        )
        result = _run_hook(tmp)

        assert result.returncode == 0, (
            f"环境健康时不应阻断 commit，但 hook 返回 {result.returncode}。"
            f"\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )