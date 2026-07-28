#!/usr/bin/env python3
"""check_metric_dict.py — 指标字典 8 必填 + 4 可选 + L0-L3 分层校验（P1-8 治理）

用法：
  python3 scripts/check_metric_dict.py <file.yaml>
  python3 scripts/check_metric_dict.py <file.yaml> --enforce-l2  # 强制 L2 校验（默认遵循 layer 字段）

返回：
  退出码 0 = 校验通过
  退出码 1 = 校验失败（打印所有不通过项）

校验规则参考：
  docs/tasks/2026-07-23-refactor-product-foundation/spec.md § 4.2 MetricDict schema
  docs/tasks/2026-07-23-refactor-product-foundation/spec.md § 2.2 SCN-P1.8.1 ~ SCN-P1.8.6

分层规则（spec § 3.2）：
- L0（内部/一次性）：不要求字典
- L1（探索性）：1 句话问题假设 + 1 核心信号 + ≤3 事件（最小集）
- L2（核心闭环）：8 必填 + 4 可选字段齐全
- L3（稳定用户）：L2 + dashboard + cohort + 数据质量 + 隐私

5 项 AI 推送产品指标（push_open_rate / push_read_rate / favorite_rate / block_rate / retention_30d）阈值未实测
→ 必须标 L1 · SCN-P1.8.6 硬阻断 L2 升级（v1.2 决策 3 修正）

pre-commit 兼容：POSIX exit code · 输出到 stdout/stderr
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, List, Literal, Union

import yaml
from pydantic import BaseModel, Field, ValidationError

# v0 框架
sys.path.insert(0, str(Path(__file__).parent))
from check_spec_base import main_runner  # noqa: E402


# ─── Pydantic schema（spec § 4.2）───────────────────────────
class EventRef(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_.]{2,50}$")
    file: str
    line: int = Field(ge=1)


class DedupSpec(BaseModel):
    primary_key: str
    window: str = Field(pattern=r"^\d+[hd]$")


class Target(BaseModel):
    value: float = Field(ge=0)
    deadline: str
    source: str = Field(min_length=5)


class MetricDict(BaseModel):
    metric_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,40}$")
    metric_name: str = Field(min_length=3, max_length=50)
    formula: str = Field(min_length=10, max_length=200)
    num_event: EventRef
    den_event: EventRef
    dedup: DedupSpec
    target: Target
    failure_action: List[str] = Field(min_items=1)
    # 4 可选（L3 触发）
    current_baseline: Union[str, float, None] = None
    instrumentation_site: str = None
    owner: str = None
    observed_at: str = None
    layer: Literal["L0", "L1", "L2", "L3"]


# ─── 业务校验（spec SCN-P1.8.3 · failure_action 字符数）─────
def validate_failure_action_length(actions: List[str], layer: str) -> list[str]:
    """L2/L3 校验：failure_action 每条字符数 ≥ 30（spec § 2.2 SCN-P1.8.3）。"""
    violations: list[str] = []
    if layer in ("L2", "L3"):
        for i, action in enumerate(actions):
            if len(action) < 30:
                violations.append(
                    f"failure_action[{i}]: 字符数 {len(action)} < 30 (min_length 30 spec SCN-P1.8.3, 当前实际字符数 = {len(action)})"
                )
    return violations


# ─── 5 项 AI 推送产品指标（SCN-P1.8.6 硬阻断 L2 升级）───────
AI_PUSH_METRIC_IDS = {
    "push_open_rate",
    "push_read_rate",
    "favorite_rate",
    "block_rate",
    "retention_30d",
}


def validate_l2_threshold_blocked(data: dict[str, Any]) -> list[str]:
    """SCN-P1.8.6：5 项 AI 推送指标阈值未实测 · 标 L2 升级被硬阻断。

    关键修复（v1.2 verifier FAIL 偏差 5）：原版只读 YAML 原始 layer，--enforce-l2 标志
    可绕过（局部变量 layer 改 L2 但 YAML 数据 layer 仍 L1 → 阻断失效）。
    修法：先在调用方 mutate data['layer'] = 'L2'（如果 enforce_l2），然后本函数读 data['layer']。
    调用方负责 mutate · 本函数只负责校验逻辑。
    """
    violations: list[str] = []
    metric_id = data.get("metric_id", "")
    layer = data.get("layer", "")
    current_baseline = data.get("current_baseline")
    observed_at = data.get("observed_at")

    if metric_id in AI_PUSH_METRIC_IDS and layer in ("L2", "L3"):
        # 阈值未实测判定：current_baseline=None 或 observed_at=None
        if current_baseline is None or observed_at is None:
            violations.append(
                f"SCN-P1.8.6 硬阻断：{metric_id} 阈值未实测验证（current_baseline={current_baseline}, observed_at={observed_at}）"
                f"· 必须保持 layer: L1"
            )
    return violations


def validate_l1_minimal_set(data: dict[str, Any]) -> list[str]:
    """L1 最小集校验（spec § 4.2 / § 3.2 分层规则 / SCN-P1.8.5）。

    v1.2 verifier FAIL 偏差 4 修法：原版只校验 metric_id + layer，spec 要求 L1 最小集包含：
    - 1 句话问题假设（problem_hypothesis · min 20 字）
    - 1 核心成功信号（core_signal · min 10 字）
    - ≤ 3 个事件（events · 列表 ≤ 3 项）
    """
    violations: list[str] = []
    problem_hypothesis = data.get("problem_hypothesis", "")
    core_signal = data.get("core_signal", "")
    events = data.get("events", [])

    if not problem_hypothesis or len(problem_hypothesis) < 20:
        violations.append("L1 最小集缺 problem_hypothesis (1 句话问题假设 · 至少 20 字)")
    if not core_signal or len(core_signal) < 10:
        violations.append("L1 最小集缺 core_signal (1 核心成功信号 · 至少 10 字)")
    if not isinstance(events, list) or len(events) == 0 or len(events) > 3:
        violations.append(f"L1 最小集缺 events (≤ 3 事件 · 当前 {len(events) if isinstance(events, list) else 'N/A'})")

    # metric_id 正则
    metric_id = data.get("metric_id", "")
    if not re.match(r"^[a-z][a-z0-9_]{2,40}$", metric_id):
        violations.append(f"metric_id: '{metric_id}' 不符合正则 ^[a-z][a-z0-9_]{{2,40}}$")

    return violations


# ─── 主入口 ───────────────────────────────────────────────
def check_metric_dict(file_path: str, enforce_l2: bool = False) -> int:
    """校验单个 metric dict 文件。

    Args:
        file_path: YAML 文件路径
        enforce_l2: 强制按 L2 校验（默认遵循 layer 字段）

    Returns:
        0 = OK
        1 = 校验失败
    """
    p = Path(file_path)
    if not p.exists():
        print(f"::error::file not found: {file_path}", file=sys.stderr)
        return 1
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"::error::read error: {file_path}: {e}", file=sys.stderr)
        return 1

    # 解析 YAML
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"::error::YAML parse error: {file_path}: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print(f"::error::{file_path}: top-level must be mapping, got {type(data).__name__}", file=sys.stderr)
        return 1

    violations: list[str] = []
    layer = data.get("layer", "L0")

    # v1.2 偏差 5 修法：--enforce-l2 必须 mutate data['layer'] 而不只是局部变量
    # 否则 SCN-P1.8.6 硬阻断读 YAML 原始 layer 会绕过
    if enforce_l2:
        data["layer"] = "L2"
        layer = "L2"

    if layer == "L1":
        # L1 最小集校验（v1.2 偏差 4 修法）：问题假设 + 核心信号 + ≤3 事件
        violations.extend(validate_l1_minimal_set(data))
    else:
        # L2/L3 严格校验：8 必填
        try:
            MetricDict.model_validate(data)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                violations.append(f"metric_dict.{loc}: {err['msg']}")

        # 业务校验：failure_action 字符数
        if "failure_action" in data:
            violations.extend(validate_failure_action_length(data["failure_action"], layer))

    # SCN-P1.8.6 硬阻断（v1.2 偏差 5 修法：读 mutate 后的 layer）
    violations.extend(validate_l2_threshold_blocked(data))

    if violations:
        # v1.2 偏差 1 修法：所有错误写入 stderr（spec 约定）
        for v in violations:
            print(f"::error::{v}", file=sys.stderr)
        print(f"\n❌ {len(violations)} check-metric-dict violation(s)", file=sys.stderr)
        return 1

    print(f"✅ check-metric-dict passed for {file_path} (layer: {layer})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_metric_dict.py <file.yaml> [--enforce-l2]", file=sys.stderr)
        sys.exit(2)

    enforce_l2 = "--enforce-l2" in sys.argv
    file_arg = sys.argv[1]
    sys.exit(check_metric_dict(file_arg, enforce_l2=enforce_l2))