"""Tests for check-step.py tasks § 9 埋点挂载点校验 (T17 · P1-9 L2 § 9 治理).

覆盖 SCN：
- TC-7: L2 任务缺 § 9 段报错（SCN-P1.9.9）
- TC-7.5: event_name 不符合正则报错（SCN-P1.9.10）
- TC-7.6: L1 任务 § 9 豁免（SCN-P1.9.11）

测试策略：
- subprocess 跑 scripts/check-step.py tasks（不 mock · 真跑 · POSIX exit code 校验）
- tmp_path 写临时 tasks.md（含/不含 § 9 段）
- 断言 rc + stderr 含关键定位字符串

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题）。
T17 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest backend/tests/test_check_tasks_template.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check-step.py"
PYTHON = REPO_ROOT / "backend" / ".venv" / "bin" / "python"


def _run_checker_tasks(file_path: Path) -> subprocess.CompletedProcess:
    """跑 check-step.py tasks 在指定 file 上。"""
    return subprocess.run(
        [str(PYTHON), str(CHECKER), "tasks", str(file_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _write_tasks_md(tmp_path: Path, frontmatter: str, body: str) -> Path:
    """写一个临时 tasks.md 文件（含 frontmatter + body）。"""
    content = f"---\n{frontmatter}\n---\n{body}"
    p = tmp_path / "test_tasks.md"
    p.write_text(content, encoding="utf-8")
    return p


# 完整 fixture 模板（含 § 1-5 必需字段：commit/测试/依赖/总估时 · 让 § 9 校验成为唯一点）
FULL_BODY_TEMPLATE = """
# Test Tasks

- [ ] T1: 测试任务
  - **估时**: 30 min
  - **依赖**: —
  - **测试**: tests/test_check_tasks_template.py::test_dummy
  - **commit**: `abc1234`

## 总估时

- T1: 30 min
- **总估时**: 0.5h

## 1. 任务粒度原则

## 7. 实施顺序

1. T1（测试）— 30 min
"""


# ─── TC-7: L2 任务缺 § 9 段报错（SCN-P1.9.9）───────────────
def test_l2_missing_section_9(tmp_path):
    """L2 任务（默认 layer）缺 § 9 段 → exit 1 + stderr 含 § 9 缺失错误。"""
    frontmatter = """
type: tasks
"""
    body = FULL_BODY_TEMPLATE
    p = _write_tasks_md(tmp_path, frontmatter, body)
    result = _run_checker_tasks(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstderr: {result.stderr}"
    assert "§ 9 埋点挂载点缺失" in result.stdout or "layer=L2" in result.stdout


# ─── TC-7b: L2 任务含 § 9 段通过 ──
def test_l2_with_section_9_ok(tmp_path):
    """L2 任务含完整 § 9 段 → exit 0。"""
    frontmatter = """
type: tasks
layer: L2
"""
    body = FULL_BODY_TEMPLATE + """

## 9. 埋点挂载点

### 9.1 事件挂载

| 任务 | event_name | trigger 位置 | data fields |
|---|---|---|---|
| T1 | push.delivered | backend/services/digest_service.py | user_id |
"""
    p = _write_tasks_md(tmp_path, frontmatter, body)
    result = _run_checker_tasks(p)
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstderr: {result.stderr}"


# ─── TC-7.5: event_name 不符合正则报错（SCN-P1.9.10）────────
def test_event_name_regex_invalid(tmp_path):
    """event_name 不符合正则 ^[a-z][a-z0-9_.]{2,50}$ → exit 1 + stderr 含正则错误。"""
    frontmatter = """
type: tasks
layer: L2
"""
    body = FULL_BODY_TEMPLATE + """

## 9. 埋点挂载点

### 9.1 事件挂载

| 任务 | event_name | trigger 位置 | data fields |
|---|---|---|---|
| T1 | 1push.delivered | backend/services/digest_service.py | user_id |
"""
    p = _write_tasks_md(tmp_path, frontmatter, body)
    result = _run_checker_tasks(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstderr: {result.stderr}"
    assert "event_name" in result.stdout or "正则" in result.stdout


# ─── TC-7.6: L1 任务 § 9 豁免（SCN-P1.9.11）──────────────
def test_l1_section_9_exempt(tmp_path):
    """L1 任务（探索性）豁免 § 9 段 → exit 0（即使缺 § 9）。"""
    frontmatter = """
type: tasks
layer: L1
"""
    body = FULL_BODY_TEMPLATE
    p = _write_tasks_md(tmp_path, frontmatter, body)
    result = _run_checker_tasks(p)
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstderr: {result.stderr}"


# ─── TC-7.7: 实际任务的 tasks.md（layer: L1）应当通过 ──
def test_actual_tasks_md_passes():
    """本任务的实际 tasks.md（layer: L1 标记）应当通过 check-step.py tasks。"""
    actual_tasks = REPO_ROOT / "docs/tasks/2026-07-23-refactor-product-foundation/tasks.md"
    if not actual_tasks.exists():
        pytest.skip(f"实际 tasks.md 不存在: {actual_tasks}")
    result = _run_checker_tasks(actual_tasks)
    assert result.returncode == 0, (
        f"实际 tasks.md 校验失败 · rc={result.returncode}\n"
        f"stderr: {result.stderr[:500]}"
    )