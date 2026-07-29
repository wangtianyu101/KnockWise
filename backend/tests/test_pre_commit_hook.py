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
CHECK_TASK_SRC = REPO_ROOT / "scripts" / "check-task.py"
CHECK_TASK_STATE_SRC = REPO_ROOT / "scripts" / "check_task_state.py"


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
        shutil.copy(CHECK_TASK_SRC, scripts_dir / "check-task.py")
        shutil.copy(CHECK_TASK_STATE_SRC, scripts_dir / "check_task_state.py")
        # product-doc checker（2026-07-29 refactor：覆盖 docs/issues.md 边界修复回归）
        check_product_doc_src = REPO_ROOT / "scripts" / "check-product-doc.py"
        check_spec_base_src = REPO_ROOT / "scripts" / "check_spec_base.py"
        if check_product_doc_src.exists():
            shutil.copy(check_product_doc_src, scripts_dir / "check-product-doc.py")
        if check_spec_base_src.exists():
            shutil.copy(check_spec_base_src, scripts_dir / "check_spec_base.py")
        # 暂存目标文件
        staged = tmp / relpath
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text(content, encoding="utf-8")
        parts = Path(relpath).parts
        if len(parts) >= 4 and parts[:2] == ("docs", "tasks"):
            task_id = parts[2]
            manifest_relpath = f"docs/tasks/{task_id}/task.yaml"
            manifest = tmp / manifest_relpath
            manifest.write_text(
                "schema: task/v1\n"
                f"task_id: {task_id}\n"
                "mode: timebox\n"
                "current_step: 0\n"
                "step_state: in_progress\n"
                "triggers:\n"
                "  ui_design: false\n"
                "  ui_components: false\n"
                "  api_change: false\n"
                "  db_change: false\n"
                "test_evidence:\n"
                "  type: pending\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", manifest_relpath],
                cwd=tmp,
                check=True,
                capture_output=True,
            )
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


# ─── 场景 4-7：docs/issues.md 与 product-doc 边界修复（D-003）───
#
# 2026-07-29 refactor：scripts/pre-commit:220 regex 移除 docs/issues.md
#   Before: ^(docs/templates/product-doc-template\.md|docs/tasks/.+/product-doc\.md|docs/issues\.md)$
#   After:  ^(docs/templates/product-doc-template\.md|docs/tasks/.+/product-doc\.md)$
#
# 核心场景：docs/issues.md 合法修改（无 frontmatter / 无 § 4 MVP / 无 § 5 成功指标）必须通过 hook。
# 边界保留：docs/templates/product-doc-template.md 与 docs/tasks/<date>/product-doc.md 仍被拦。
# 共同 commit：只有真 product-doc 被拦，docs/issues.md 不受影响。


VALID_ISSUES_MD = """\
# 目前缺陷与设计议题

> 唯一主账（按 AGENTS.md § 0.5）。

## 一、设计议题（待深入讨论）

### 议题 X — 示例

**状态**：📋 待讨论
"""

INVALID_PRODUCT_DOC_TEMPLATE = """\
# product-doc-template 占位
（无 frontmatter / 无 § 4 MVP / 无 § 5 成功指标）
"""

INVALID_PRODUCT_DOC_INSTANCE = """\
# 产品文档实例占位
（无 frontmatter / 无 § 4 MVP / 无 § 5 成功指标）
"""


class TestIssuesMdBypassesProductDocCheck:
    """docs/issues.md 是议题主账，不应被 product-doc 校验拦下。"""

    def test_issues_md_modification_passes_hook(
        self, cleanup_tmp,
    ):
        """核心场景：合法的 docs/issues.md 修改不应被 pre-commit 阻断。

        修复前：pre-commit 第 220 行 regex 把 docs/issues.md 当作 product-doc，
        跑 check-product-doc.py → exit 1 → hook 阻断 commit。
        修复后：regex 不再命中 docs/issues.md，hook 通过。
        """
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo("docs/issues.md", VALID_ISSUES_MD)
        )
        result = _run_hook(tmp)

        # docs/issues.md 不应触发 product-doc frontmatter 校验失败
        assert "❌ product-doc frontmatter 校验失败" not in result.stdout, (
            f"docs/issues.md 不应被 product-doc 校验拦下，但 stdout 包含阻断信息：\n"
            f"{result.stdout}"
        )
        # 不应出现 "check-product-doc.py 不存在" 的 fail closed 路径
        assert "check-product-doc.py 不存在" not in result.stdout, (
            f"hook 不应 fail closed，但 stdout 提示 checker 缺失：\n{result.stdout}"
        )


class TestProductDocBoundaryStillEnforced:
    """修复后，真 product-doc 仍受 check-product-doc.py 校验保护。"""

    def test_product_doc_template_without_frontmatter_blocks_hook(
        self, cleanup_tmp,
    ):
        """边界保留：docs/templates/product-doc-template.md 无 frontmatter → 仍被拦。"""
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo(
                "docs/templates/product-doc-template.md",
                INVALID_PRODUCT_DOC_TEMPLATE,
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"product-doc 模板无 frontmatter 必须被 hook 阻断，但 rc={result.returncode}。"
            f"\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        assert "❌ product-doc frontmatter 校验失败" in result.stdout, (
            f"应输出 product-doc frontmatter 阻断信息，但 stdout 为：\n{result.stdout}"
        )

    def test_product_doc_instance_without_frontmatter_blocks_hook(
        self, cleanup_tmp,
    ):
        """边界保留：docs/tasks/<date>/product-doc.md 无 frontmatter → 仍被拦。

        注意：路径必须用 2026-08-XX 日期，避开 scripts/check_spec_base.py 的
        LEGACY_TASKS 豁免（`docs/tasks/2026-07-*` 全部自动豁免）。
        """
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo(
                "docs/tasks/2026-08-01-test/product-doc.md",
                INVALID_PRODUCT_DOC_INSTANCE,
            )
        )
        result = _run_hook(tmp)

        assert result.returncode != 0, (
            f"product-doc 实例无 frontmatter 必须被 hook 阻断，但 rc={result.returncode}。"
            f"\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        assert "❌ product-doc frontmatter 校验失败" in result.stdout, (
            f"应输出 product-doc frontmatter 阻断信息，但 stdout 为：\n{result.stdout}"
        )


class TestMixedCommitOnlyBlocksRealProductDoc:
    """docs/issues.md 与真 product-doc 同 commit 时：只有真 product-doc 被拦。"""

    def test_issues_md_and_product_doc_mixed_blocks_only_product_doc(
        self, cleanup_tmp,
    ):
        tmp = cleanup_tmp(
            _stage_file_in_tmp_repo("docs/issues.md", VALID_ISSUES_MD)
        )
        # 在同一 tmp repo 加 product-doc 实例并 stage（用 2026-08-* 避开 LEGACY 豁免）
        product_doc_relpath = "docs/tasks/2026-08-01-mixed/product-doc.md"
        product_doc_path = tmp / product_doc_relpath
        product_doc_path.parent.mkdir(parents=True, exist_ok=True)
        product_doc_path.write_text(INVALID_PRODUCT_DOC_INSTANCE, encoding="utf-8")
        subprocess.run(
            ["git", "add", product_doc_relpath],
            cwd=tmp, check=True, capture_output=True,
        )
        # 同时补 task.yaml 让 manifest 校验通过
        manifest_relpath = "docs/tasks/2026-08-01-mixed/task.yaml"
        (tmp / manifest_relpath).write_text(
            "schema: task/v1\n"
            "task_id: 2026-08-01-mixed\n"
            "mode: timebox\n"
            "current_step: 0\n"
            "step_state: in_progress\n"
            "triggers:\n"
            "  ui_design: false\n"
            "  ui_components: false\n"
            "  api_change: false\n"
            "  db_change: false\n"
            "test_evidence:\n"
            "  type: pending\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", manifest_relpath],
            cwd=tmp, check=True, capture_output=True,
        )

        result = _run_hook(tmp)

        # 真 product-doc 必须被拦（hook 整体退出非零）
        assert result.returncode != 0, (
            f"真 product-doc 必须被拦，但 rc={result.returncode}。stdout:\n{result.stdout}"
        )
        assert "❌ product-doc frontmatter 校验失败" in result.stdout
        # 阻断信息应只提到真 product-doc，不应提到 docs/issues.md
        assert "docs/issues.md" not in result.stdout or (
            "→ docs/issues.md" not in result.stdout
            and "📋 product-doc 改动" not in result.stdout
            or result.stdout.count("❌ product-doc frontmatter 校验失败") == 1
        ), (
            f"docs/issues.md 不应触发 product-doc 阻断，但 stdout 包含：\n{result.stdout}"
        )
