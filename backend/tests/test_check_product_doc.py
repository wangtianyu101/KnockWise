"""Tests for scripts/check-product-doc.py (T5 · P1-7 v2 治理).

覆盖 SCN：
- TC-1: 合规 product-doc 通过校验（SCN-P1.7.1）
- TC-2: 缺 problem_evidence 段被拒（SCN-P1.7.2）
- TC-2.5: target_user 缺 device 字段被拒（SCN-P1.7.3）
- TC-2.6: frontmatter YAML 解析失败被拒（SCN-P1.7.4）

测试策略：
- subprocess 跑 scripts/check-product-doc.py（不 mock · 真跑 · POSIX exit code 校验）
- tmp_path 写临时 product-doc.md 文件（含完整 5 段 + product_baseline frontmatter）
- 断言 rc + stdout 含关键定位字符串（v0 main_runner 输出到 stdout）

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题，已登记 docs/issues.md）。
T5 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest backend/tests/test_check_product_doc.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check-product-doc.py"
PYTHON = REPO_ROOT / "backend" / ".venv" / "bin" / "python"

# v0 framework 校验 5 段齐全 + § 5 成功指标 4 字段（baseline_value/baseline_source）
# fixture 必须含完整 5 段才能通过 v0 段校验
FULL_BODY_TEMPLATE = """
## 0. 调研前置必填（product_baseline · P1-7 治理）

## 1. 问题定义（必填）

## 2. 目标用户（必填）

## 3. 价值主张（必填）

## 4. MVP 范围（必填）

## 5. 成功指标（必填 · 可量化 · 含 baseline_value + baseline_source 字段）
"""


def _run_checker(file_path: Path) -> subprocess.CompletedProcess:
    """跑 check-product-doc.py 在指定 file 上。"""
    return subprocess.run(
        [str(PYTHON), str(CHECKER), str(file_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _write_product_doc(tmp_path: Path, frontmatter: str, body: str = FULL_BODY_TEMPLATE) -> Path:
    """写一个临时 product-doc.md 文件（含完整 5 段 + frontmatter）。"""
    content = f"---\n{frontmatter}\n---{body}"
    p = tmp_path / "test_product_doc.md"
    p.write_text(content, encoding="utf-8")
    return p


# ─── TC-1: 合规 product-doc 通过校验（SCN-P1.7.1）─────────
def test_baseline_ok(tmp_path):
    """合规 frontmatter + 5 段齐全 → exit 0 + stdout 含 OK。"""
    fm = """
product_baseline:
  problem_evidence:
    - file: docs/issues.md
      line: 42
      quote: V4 AI 推送模块存在 41 个测试空壳
      baseline_value: 41
      baseline_source: 实测命令
    - file: backend/utils/metrics.py
      line: 1
      quote: dead code
      baseline_value: 0
      baseline_source: 实测命令
    - file: docs/templates/tasks-template.md
      line: 1
      quote: 缺 § 9 段
      baseline_value: "N/A"
      baseline_source: 估算
  target_user:
    role: 开发者
    persona_count: 1
    frequency_per_week: 14
    device: 桌面
    network: 高带宽
  kill_criteria:
    - name: 投入产出比不达标
      trigger: 上线 30 天后核心指标 < 30% 目标
      evidence: 统计后台 CTR/留存 低于 30% target
"""
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "OK" in result.stdout or "passed" in result.stdout.lower()


# ─── TC-2: 缺 problem_evidence 段被拒（SCN-P1.7.2）─────────
def test_baseline_missing_evidence(tmp_path):
    """缺 problem_evidence → exit 1 + stdout 含 product_baseline.problem_evidence。"""
    fm = """
product_baseline:
  target_user:
    role: 开发者
    persona_count: 1
    frequency_per_week: 14
    device: 桌面
    network: 高带宽
  kill_criteria:
    - name: 投入产出比不达标
      trigger: 上线 30 天后核心指标 < 30% 目标
      evidence: 统计后台 CTR/留存 低于 30% target
"""
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "product_baseline.problem_evidence" in result.stdout


# ─── TC-2.5: target_user 缺 device 字段被拒（SCN-P1.7.3）──
def test_target_user_missing_device(tmp_path):
    """target_user 缺 device 字段 → exit 1 + stdout 定位 target_user.device。"""
    fm = """
product_baseline:
  problem_evidence:
    - file: docs/issues.md
      line: 42
      quote: V4 AI 推送模块存在 41 个测试空壳
      baseline_value: 41
      baseline_source: 实测命令
    - file: backend/utils/metrics.py
      line: 1
      quote: dead code
      baseline_value: 0
      baseline_source: 实测命令
    - file: docs/templates/tasks-template.md
      line: 1
      quote: 缺 § 9 段
      baseline_value: "N/A"
      baseline_source: 估算
  target_user:
    role: 开发者
    persona_count: 1
    frequency_per_week: 14
    network: 高带宽
  kill_criteria:
    - name: 投入产出比不达标
      trigger: 上线 30 天后核心指标 < 30% 目标
      evidence: 统计后台 CTR/留存 低于 30% target
"""
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "target_user.device" in result.stdout


# ─── TC-2.6: frontmatter YAML 解析失败被拒（SCN-P1.7.4）───
def test_frontmatter_parse_error(tmp_path):
    """非法 YAML 缩进 → exit 1 + stdout 含 frontmatter parse error。"""
    # 用 Tab 字符（YAML 不允许）
    fm = "product_baseline:\n\tproblem_evidence: []"
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "frontmatter parse error" in result.stdout


# ─── TC-extra: legacy_skeleton=true 豁免 product_baseline 校验 ─
def test_legacy_skeleton_exempt(tmp_path):
    """legacy_skeleton: true → product_baseline 校验豁免（但 5 段仍校验）。"""
    fm = """
product_baseline:
  legacy_skeleton: true
"""
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    # legacy_skeleton 豁免 product_baseline 校验（stdout 含"跳过 product_baseline 校验"）
    # 但 v0 framework 仍校验 5 段（fixture 包含 FULL_BODY_TEMPLATE 所以应通过 5 段校验）
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "legacy_skeleton" in result.stdout


# ─── TC-extra: 缺整个 product_baseline 段 ───────────────────
def test_baseline_section_missing(tmp_path):
    """完全缺 product_baseline 段 → exit 1 + stdout 含 product_baseline.missing。"""
    fm = """
title: Some Title
status: draft
"""
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "product_baseline.missing" in result.stdout


# ─── TC-extra: problem_evidence.quote 超 80 字符报错（确认 checker 严格）──
def test_problem_evidence_too_short_quote(tmp_path):
    """problem_evidence.quote 超 80 字符 → exit 1 + stdout 定位 problem_evidence.0.quote。"""
    long_quote = "x" * 100  # 100 字符 > 80 max_length
    fm = f"""
product_baseline:
  problem_evidence:
    - file: docs/issues.md
      line: 42
      quote: {long_quote}
      baseline_value: 1
      baseline_source: 实测命令
    - file: a
      line: 1
      quote: b
      baseline_value: 0
      baseline_source: 实测命令
    - file: c
      line: 2
      quote: d
      baseline_value: 0
      baseline_source: 实测命令
  target_user:
    role: 开发者
    persona_count: 1
    frequency_per_week: 14
    device: 桌面
    network: 高带宽
  kill_criteria:
    - name: 投入产出比不达标
      trigger: 上线 30 天后核心指标 < 30% 目标
      evidence: 统计后台 CTR/留存 低于 30% target
"""
    p = _write_product_doc(tmp_path, fm)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "problem_evidence" in result.stdout
    assert "max_length" in result.stdout or "80" in result.stdout
