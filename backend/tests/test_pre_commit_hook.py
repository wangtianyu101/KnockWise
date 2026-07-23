"""回归测试：scripts/pre-commit 的 DOD check 段必须正确传播 check-step.py 的退出码。

P0-1 修复（decisions.md 决策 1 · 方案 A）：

  原代码：`if ! python3 scripts/check-step.py ... 2>&1 | tail -10; then failed=1; fi`
  问题：POSIX /bin/sh 默认取管道末端 tail 的退出码；checker 非零但 tail=0 时，failed=1 不会执行。
  修复：先 `set +e` 捕获 `check_out=$(python3 ... 2>&1)` 与 `check_rc=$?`，再 `set -e`，
        然后用 `printf '%s\\n' "$check_out" | tail -10` 仅作展示；最后按 rc 设置 failed。

本测试通过真实跑 hook（subprocess + 临时 git repo）覆盖 3 个场景：

  1. 合法文档 → hook exit 0（不阻断 commit）
  2. 非法文档 → hook exit ≠ 0（阻断 commit，且包含失败诊断）
  3. 非法文档且 checker 输出 > 10 行 → hook exit ≠ 0，且展示输出被 tail -10 截断

修复前场景 2 必须 RED（hook 假绿放过）；修复后必须 GREEN。
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
CHECK_STEP_SRC = REPO_ROOT / "scripts" / "check-step.py"


# ─── 合法 / 非法 文档 fixtures ─────────────────────────────────

VALID_RESEARCH_MD = """\
# 调研报告

> 路径模式：`fix-mini`

## 1. 任务理解
已和用户确认。
## 2. 复现路径
已稳定复现。
## 3. 影响范围
影响范围已列出。
## 4. 根因假设
根因已分析并被对抗 Agent 纠正。
## 5. 最近相关改动
已跑 `git log -10` 与 `git status`；最近相关 commit 已列出。
## 6. 输出建议
走 `fix-mini`（0 调研 → 4 回归测试 → 6 复盘）。

证据：docs/issues.md；git log -10；git status
"""

INVALID_RESEARCH_MD = "# 空文档（缺路径模式与全部必填段）\n"

# 故意让 check_tasks 同时命中 5+ 条 error，输出明显超过 10 行
INVALID_TASKS_MD_LONG_OUTPUT = (
    "# 空 tasks.md（无任务项 / 无总估时 / 无依赖 / 无 commit / 无测试）\n"
)


# ─── 临时 git repo + 跑 hook 工具函数 ───────────────────────────

def _stage_file_in_tmp_repo(relpath: str, content: str) -> Path:
    """在临时目录里初始化 git repo、放置 hook + check-step、暂存给定内容。返回 tmpdir 路径。"""
    tmp = Path(tempfile.mkdtemp(prefix="precommit-dod-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.local"],
            cwd=tmp, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "test"],
            cwd=tmp, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "commit.gpgsign", "false"],
            cwd=tmp, check=True, capture_output=True,
        )
        # 复制 hook 与 checker 到 tmp（hook 用 cd "$(git rev-parse --show-toplevel)" + scripts/pre-commit）
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        shutil.copy(HOOK_SRC, scripts_dir / "pre-commit")
        shutil.copy(CHECK_STEP_SRC, scripts_dir / "check-step.py")
        # 暂存目标文件
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


def _run_hook(tmp: Path):
    """跑 hook，返回 CompletedProcess。捕获 stdout/stderr/rc。"""
    return subprocess.run(
        ["sh", "scripts/pre-commit"],
        cwd=tmp,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )


@pytest.fixture
def cleanup_tmp():
    """确保每个测试后清理临时目录。"""
    cleanup_paths: list[Path] = []

    def _track(p: Path) -> Path:
        cleanup_paths.append(p)
        return p

    yield _track
    for p in cleanup_paths:
        shutil.rmtree(p, ignore_errors=True)


# ─── 场景 1：合法文档 → hook 通过 ────────────────────────────────

class TestDodCheckPassesValidDoc:
    """合法文档不应被 DOD 段阻断。"""

    def test_valid_research_md_allows_commit(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo(
                "docs/tasks/2026-07-23-ok/research.md",
                VALID_RESEARCH_MD,
            )
        )
        result = _run_hook(tmp)

        assert result.returncode == 0, (
            f"合法 research.md 不应被 DOD 段阻断，但 hook 退出 {result.returncode}。"
            f"\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        assert "✅ 6 步 v2 DOD 校验通过" in result.stdout


# ─── 场景 2：非法文档 → hook 必须阻断 ────────────────────────────

class TestDodCheckBlocksInvalidDoc:
    """非法文档必须被 DOD 段阻断 — 这是 P0-1 修复的核心场景。"""

    def test_invalid_research_md_blocks_commit(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo(
                "docs/tasks/2026-07-23-bad/research.md",
                INVALID_RESEARCH_MD,
            )
        )
        result = _run_hook(tmp)

        # 关键断言：必须阻断。
        # 修复前：hook 因 `python3 ... | tail -10` 管道吞掉非零退出，返回 0（假绿）。
        # 修复后：hook 必须返回非零。
        assert result.returncode != 0, (
            "P0-1 回归失败：非法 research.md 未被 DOD 段阻断（假绿）。"
            f"\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        # 阻断信息应清晰
        assert "❌ 6 步 v2 DOD 校验失败" in result.stdout, (
            f"应输出 'DOD 校验失败' 阻断信息，但 stdout 为：\n{result.stdout}"
        )
        # 阻断后不应再出现 "DOD 校验通过"
        assert "✅ 6 步 v2 DOD 校验通过" not in result.stdout


# ─── 场景 3：非法文档且输出 > 10 行 → 仅末 10 行且仍阻断 ────────

class TestDodCheckTruncatesAndStillBlocks:
    """checker 输出多行错误时，必须只显示末 10 行，但同时仍阻断 commit。"""

    def test_long_failure_output_is_truncated_to_ten_lines(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo(
                "docs/tasks/2026-07-23-long/tasks.md",
                INVALID_TASKS_MD_LONG_OUTPUT,
            )
        )
        result = _run_hook(tmp)

        # 必须阻断（不退化为假绿）
        assert result.returncode != 0, (
            f"非法 tasks.md（多行错误）未阻断 commit。stdout:\n{result.stdout}"
        )
        assert "❌ 6 步 v2 DOD 校验失败" in result.stdout

        # 提取 hook 输出中"DOD 校验失败"之前的"tail -10"展示段。
        # 钩子脚本的输出格式：
        #   📋 docs/tasks/ 改动 → 跑 6 步 v2 DOD 校验...
        #      → tasks: docs/tasks/.../tasks.md
        #   <tail -10 输出>
        #   ❌ 6 步 v2 DOD 校验失败
        # 我们校验：'tail 段' 总行数 ≤ 10（不含 hook 自己的 echo 行）。
        out = result.stdout
        # 找 "DOD 校验失败" 之前的内容
        marker = "❌ 6 步 v2 DOD 校验失败"
        idx = out.find(marker)
        assert idx != -1, "应输出阻断标记"
        before = out[:idx]

        # before 段：开头是 hook 的 echo（"📋 docs/tasks/..." 与 "   → tasks: ..."），中间是
        # 由 `printf '%s\n' "$check_out" | tail -10` 产生的 ≤ 10 行的 checker 输出。
        # 我们统计 before 段的非空行数，并断言最后 ≤ 10 行都是 checker 错误行（不是 hook 元行）。
        lines = before.splitlines()
        # 移除 hook 自己的两行元数据（"📋 docs/tasks/ 改动..." 与 "   → tasks: ..."）
        # 直接数从底部往上连续属于 checker 输出的行数：含 "❌"（每条错误）或 "💡" 提示
        tail_block: list[str] = []
        for line in reversed(lines):
            s = line.strip()
            if not s:
                continue
            if s.startswith("❌") or s.startswith("💡") or s.startswith("DOD 校验失败") or s.startswith("共"):
                tail_block.append(line)
                continue
            # 钩子元行（"📋 docs/tasks/ 改动..." / "   → tasks: ..."）终止 tail 段
            break

        assert 1 <= len(tail_block) <= 10, (
            f"tail 段行数应在 1..10 之间，实际 {len(tail_block)} 行：\n"
            + "\n".join(tail_block)
            + f"\n--- 完整 before 段 ---\n{before}"
        )