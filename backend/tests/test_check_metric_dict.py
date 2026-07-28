"""Tests for scripts/check_metric_dict.py (T8 · P1-8 治理).

覆盖 SCN：
- TC-3: 缺 failure_action 报错（SCN-P1.8.2）
- TC-4: failure_action 字符数 < 30 报错（SCN-P1.8.3）
- TC-10: L1 字典最小集豁免校验（SCN-P1.8.5）
- TC-4.5 (extra): metric_id 不符合正则报错（SCN-P1.8.4）
- TC-3.5 (extra): 5 项 AI 推送指标 L2 升级阻断（SCN-P1.8.6 · v1.2 决策 3 修正）

测试策略：
- subprocess 跑 scripts/check_metric_dict.py（不 mock · 真跑 · POSIX exit code 校验）
- tmp_path 写临时 metric dict YAML 文件
- 断言 rc + stdout 含关键定位字符串（v0 main_runner 输出到 stdout）

⚠️ **v1.2 跑测注意**：本测试用 `pytest --noconftest` 跑（绕开 backend/tests/conftest.py）。
原因：conftest.py:229 reset_limiter fixture 引用未安装的 `core.limiter` 模块（v40 启动前环境整治议题）。
T8 本身不依赖 limiter，可以安全用 `--noconftest` 跑（pytest 标准选项）。
跑测命令：`./.venv/bin/python -m pytest backend/tests/test_check_metric_dict.py -v --noconftest --tb=short`
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check_metric_dict.py"
PYTHON = REPO_ROOT / "backend" / ".venv" / "bin" / "python"


def _run_checker(file_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """跑 check_metric_dict.py 在指定 file 上（支持 --enforce-l2 等额外参数）。"""
    cmd = [str(PYTHON), str(CHECKER), str(file_path), *extra_args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _write_metric_dict(tmp_path: Path, yaml_content: str, name: str = "test_metric.yaml") -> Path:
    """写一个临时 metric dict YAML 文件。"""
    p = tmp_path / name
    p.write_text(yaml_content, encoding="utf-8")
    return p


# ─── TC-L2-baseline: L2 字典 8 必填齐全 → exit 0 ──────────────
def test_l2_full_baseline_ok(tmp_path):
    """L2 字典 8 必填齐全（且不是 AI 推送 5 项）→ exit 0。"""
    yaml_content = """
metric_id: dummy_baseline_metric
metric_name: Dummy Baseline Metric for Testing
formula: opened_count / delivered_count
num_event:
  name: dummy.opened
  file: backend/services/dummy.py
  line: 1
den_event:
  name: dummy.delivered
  file: backend/services/dummy.py
  line: 1
dedup:
  primary_key: user_id
  window: 7d
target:
  value: 0.50
  deadline: "2026-12-31"
  source: 实测命令（dummy baseline）
failure_action:
  - 上线 30 天后若比率 < 25%（target 50%），降级推送频率至每周 1 条
  - 进一步降低个性化推荐强度，专注核心场景与关键决策点的内容覆盖范围
layer: L2
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "passed" in result.stdout.lower() or "✅" in result.stdout


# ─── TC-3: 缺 failure_action 报错（SCN-P1.8.2）────────────────
def test_missing_failure_action(tmp_path):
    """L2 字典缺 failure_action → exit 1 + stdout 含 metric_dict.failure_action。"""
    yaml_content = """
metric_id: dummy_metric_test
metric_name: Dummy Metric for Testing
formula: opened_count / delivered_count
num_event:
  name: dummy.opened
  file: backend/services/dummy.py
  line: 1
den_event:
  name: dummy.delivered
  file: backend/services/dummy.py
  line: 1
dedup:
  primary_key: user_id
  window: 7d
target:
  value: 0.50
  deadline: 2026-12-31
  source: 实测命令（dummy baseline）
layer: L2
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "failure_action" in result.stdout


# ─── TC-4: failure_action 字符数 < 30 报错（SCN-P1.8.3）──────
def test_failure_action_too_short(tmp_path):
    """failure_action 字符数 = 25 → exit 1 + stdout 含'字符数'。"""
    yaml_content = """
metric_id: dummy_metric_test
metric_name: Dummy Metric for Testing
formula: opened_count / delivered_count
num_event:
  name: dummy.opened
  file: backend/services/dummy.py
  line: 1
den_event:
  name: dummy.delivered
  file: backend/services/dummy.py
  line: 1
dedup:
  primary_key: user_id
  window: 7d
target:
  value: 0.50
  deadline: "2026-12-31"
  source: 实测命令（dummy baseline）
failure_action:
  - 字符数不足 30 的 action  # 仅 13 字符（刻意触发 SCN-P1.8.3）
layer: L2
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "字符数" in result.stdout or "30" in result.stdout


# ─── TC-10: L1 字典最小集豁免校验（SCN-P1.8.5）─────────────
def test_l1_minimal_set_ok(tmp_path):
    """L1 探索性最小集（仅 metric_id + layer）→ exit 0（跳过 8 必填严格校验）。"""
    yaml_content = """
metric_id: dummy_l1_metric
layer: L1
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstdout: {result.stdout}"


# ─── TC-4.5: metric_id 不符合正则报错（SCN-P1.8.4）─────────
def test_metric_id_regex_invalid(tmp_path):
    """metric_id 不符合正则 ^[a-z][a-z0-9_]{2,40}$ → exit 1。"""
    yaml_content = """
metric_id: "1push_total"  # 数字开头不合规
layer: L1
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "metric_id" in result.stdout


# ─── TC-3.5: 5 项 AI 推送指标 L2 升级阻断（SCN-P1.8.6 · v1.2）──
def test_l2_threshold_blocked(tmp_path):
    """5 项 AI 推送指标（push_open_rate）标 L2 + current_baseline=None → exit 1 + stdout 含 SCN-P1.8.6。"""
    yaml_content = """
metric_id: push_open_rate
metric_name: AI 推送打开率（试图标 L2 但阈值未实测）
formula: opened_count / delivered_count
num_event:
  name: push.opened
  file: backend/services/digest_service.py
  line: 1
den_event:
  name: push.delivered
  file: backend/services/digest_service.py
  line: 1
dedup:
  primary_key: user_id
  window: 7d
target:
  value: 0.40
  deadline: 2026-12-31
  source: 估算（产品未上线 · 阈值未实测）
failure_action:
  - 上线 30 天后若打开率 < 20%（target 50%），降级推送频率至每周 1 条
  - 进一步降低个性化推荐强度，关注核心场景而非内容数量
current_baseline: null
observed_at: null
layer: L2  # 试图升 L2 · 应被 SCN-P1.8.6 硬阻断
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"
    assert "SCN-P1.8.6" in result.stdout or "硬阻断" in result.stdout
    assert "push_open_rate" in result.stdout


# ─── TC-extra: L1 字典应通过（5 项 AI 推送 L1 标记验证）──────
def test_l1_ai_push_metrics_pass(tmp_path):
    """5 项 AI 推送指标实际标 L1 → exit 0（v1.2 决策 3 修正后正确标记）。"""
    yaml_content = """
metric_id: push_open_rate
metric_name: AI 推送打开率（L1 探索性）
formula: opened_count / delivered_count
num_event:
  name: push.opened
  file: backend/services/digest_service.py
  line: 1
den_event:
  name: push.delivered
  file: backend/services/digest_service.py
  line: 1
dedup:
  primary_key: user_id
  window: 7d
target:
  value: 0.40
  deadline: 2026-12-31
  source: 估算（产品未上线 · 阈值未实测）
failure_action:
  - 上线 30 天后若打开率 < 20%（target 50%），降级推送频率至每周 1 条
current_baseline: null
instrumentation_site: T6 实施
owner: claude
observed_at: null
layer: L1  # v1.2 决策 3 修正后正确标记
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p)
    assert result.returncode == 0, f"expected rc=0, got rc={result.returncode}\nstdout: {result.stdout}"


# ─── TC-enforce-l2: --enforce-l2 标志强制 L2 校验 ─────────────
def test_enforce_l2_flag(tmp_path):
    """--enforce-l2 标志强制按 L2 校验，即使 YAML 标 L1。"""
    yaml_content = """
metric_id: dummy_enforce_test
layer: L1
"""
    p = _write_metric_dict(tmp_path, yaml_content)
    result = _run_checker(p, "--enforce-l2")
    assert result.returncode == 1, f"expected rc=1, got rc={result.returncode}\nstdout: {result.stdout}"