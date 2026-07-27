#!/usr/bin/env python3
"""check-product-doc.py (P2-3 决策 1/5 + P1-7 决策 1/2 v1.2 修订)

v2 校验：
  1. product-doc-template.md 5 段（§ 0/§ 1/§ 2/§ 3/§ 4 / § 5 旧版）
  2. § 4 成功指标 4 字段（用户价值 / 商业价值 / 基线 / 目标）

v3 增量（v1.2 修订）：
  3. product_baseline frontmatter 校验（PyYAML + Pydantic ProductBaseline schema）
     - problem_evidence (3-5 条 · file/line/quote/baseline_value/baseline_source)
     - target_user (5 字段 · role/persona_count/frequency_per_week/device/network)
     - kill_criteria (1-3 条 · name/trigger/evidence)
     - dangerous_assumptions (可选 · hypothesis/falsification/risk_level)
     - legacy_skeleton (可选 · true 跳过校验)

用法：
  python3 scripts/check-product-doc.py <file.md>

返回：
  退出码 0 = 校验通过
  退出码 1 = 校验失败（打印所有不通过项）

校验规则参考：
  docs/tasks/2026-07-23-refactor-product-foundation/spec.md § 4.1 ProductBaseline schema
  docs/tasks/2026-07-23-refactor-product-foundation/spec.md § 2.2 SCN-P1.7.1 ~ SCN-P1.7.4

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
from check_spec_base import is_exempt, has_section, main_runner  # noqa: E402


# ─── Pydantic schema（spec § 4.1）───────────────────────────
class ProblemEvidence(BaseModel):
    file: str
    line: int = Field(ge=1)
    quote: str = Field(max_length=80)
    baseline_value: Union[str, int, float, None]
    baseline_source: Literal["git_commit", "实测命令", "估算"]


class TargetUser(BaseModel):
    role: str = Field(min_length=2, max_length=50)
    persona_count: int = Field(ge=1, le=10)
    frequency_per_week: int = Field(ge=0, le=1000)
    device: Literal["桌面", "移动", "混合"]
    network: Literal["高带宽", "低带宽", "N-A"]


class KillCriterion(BaseModel):
    name: str = Field(max_length=30)
    trigger: str = Field(min_length=10, max_length=200)
    evidence: str = Field(min_length=10, max_length=200)


class DangerousAssumption(BaseModel):
    hypothesis: str = Field(min_length=20, max_length=200)
    falsification: str = Field(min_length=20, max_length=200)
    risk_level: Literal["🔴", "🟡", "🟢"]


class ProductBaseline(BaseModel):
    problem_evidence: List[ProblemEvidence] = Field(min_items=3, max_items=5)
    target_user: TargetUser
    kill_criteria: List[KillCriterion] = Field(min_items=1, max_items=3)
    dangerous_assumptions: List[DangerousAssumption] = Field(default_factory=list)
    legacy_skeleton: bool = False


# ─── frontmatter 解析 ───────────────────────────────────────
FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(.*?)\n---(?:\s*\n|$)",
    re.DOTALL,
)


def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str | None]:
    """解析文件开头的 YAML frontmatter。

    Returns:
        (frontmatter_dict, None) on success
        (None, error_message) on failure
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, "no frontmatter (file must start with --- ... ---)"
    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            return None, f"frontmatter parse error: top-level must be mapping, got {type(data).__name__}"
        return data, None
    except yaml.YAMLError as e:
        return None, f"frontmatter parse error: {e}"


def validate_product_baseline(fm: dict[str, Any]) -> list[str]:
    """校验 frontmatter.product_baseline 字段。

    Returns:
        violations 列表（空 = 通过）
    """
    violations: list[str] = []
    baseline = fm.get("product_baseline")

    if baseline is None:
        violations.append("product_baseline.missing (frontmatter 必须含 product_baseline 段)")
        return violations

    if not isinstance(baseline, dict):
        violations.append(f"product_baseline: must be mapping, got {type(baseline).__name__}")
        return violations

    # legacy_skeleton 豁免
    if baseline.get("legacy_skeleton") is True:
        print("⚠️  legacy_skeleton=true · 跳过 product_baseline 校验（v1 → v2 迁移临时豁免）")
        return violations

    # Pydantic 校验
    try:
        ProductBaseline.model_validate(baseline)
    except ValidationError as e:
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            violations.append(f"product_baseline.{loc}: {err['msg']}")
    return violations


# ─── v0 校验（向后兼容 · 5 段 + § 4 成功指标 4 字段）────────
REQUIRED_SECTIONS = [
    (r"^##\s*0[\.、\s]*调研前置必填", "§ 0 调研前置必填（product_baseline）"),
    (r"^##\s*1[\.、\s]*问题定义", "§ 1 问题定义"),
    (r"^##\s*2[\.、\s]*目标用户", "§ 2 目标用户"),
    (r"^##\s*3[\.、\s]*价值主张", "§ 3 价值主张"),
    (r"^##\s*4[\.、\s]*MVP\s*范围", "§ 4 MVP 范围"),
    (r"^##\s*5[\.、\s]*成功指标", "§ 5 成功指标"),
]
REQUIRED_METRICS_FIELDS = ["baseline_value", "baseline_source"]  # v1.2 升级到 4 字段含 baseline


# ─── 主入口 ───────────────────────────────────────────────
def check_product_doc(file_path: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ check-product-doc exempt for {file_path} (legacy)")
        return 0
    p = Path(file_path)
    if not p.exists():
        print(f"::error::file not found: {file_path}")
        return 1
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        print(f"::error::read error: {file_path}: {e}")
        return 1

    violations: list[str] = []

    # 1. 5 段齐全（向后兼容 · v0 框架）
    for pattern, name in REQUIRED_SECTIONS:
        if not has_section(content, pattern):
            violations.append(f"{file_path}: 缺 {name}")

    # 2. § 5 成功指标 4 字段（v0 框架 · v1.2 升级 baseline 字段）
    metrics_section = re.search(
        r"##\s*5[\.、\s]*成功指标.*?(?=^##\s|\Z)",
        content, re.DOTALL | re.MULTILINE,
    )
    if metrics_section:
        for f in REQUIRED_METRICS_FIELDS:
            if f not in metrics_section.group(0):
                violations.append(f"{file_path}: § 5 成功指标 缺字段 {f!r}")

    # 3. product_baseline frontmatter 校验（v1.2 增量）
    fm, fm_err = parse_frontmatter(content)
    if fm_err:
        # 无 frontmatter 是错误（product_baseline 必填）
        violations.append(f"{file_path}: {fm_err}")
    else:
        baseline_violations = validate_product_baseline(fm)
        violations.extend(baseline_violations)

    return main_runner(file_path, violations, "check-product-doc")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check-product-doc.py <file>", file=sys.stderr)
        sys.exit(2)
    sys.exit(check_product_doc(sys.argv[1]))
