#!/usr/bin/env python3
"""check-product-doc.py (P2-3 决策 1/5)

验证 product-doc-template.md 的 5 段 + 5 成功指标字段
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from check_spec_base import is_exempt, has_section, main_runner

REQUIRED_SECTIONS = [
    (r"^##\s*0[\.、\s]*问题定义", "§ 0 问题定义"),
    (r"^##\s*1[\.、\s]*目标用户", "§ 1 目标用户"),
    (r"^##\s*2[\.、\s]*价值主张", "§ 2 价值主张"),
    (r"^##\s*3[\.、\s]*MVP\s*范围", "§ 3 MVP 范围"),
    (r"^##\s*4[\.、\s]*成功指标", "§ 4 成功指标"),
]
REQUIRED_METRICS_FIELDS = ["用户价值", "商业价值", "基线", "目标"]


def check_product_doc(file_path: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ check-product-doc exempt for {file_path} (legacy)")
        return 0
    p = Path(file_path)
    if not p.exists():
        print(f"::error::file not found: {file_path}")
        return 1
    content = p.read_text()
    violations = []
    for pattern, name in REQUIRED_SECTIONS:
        if not has_section(content, pattern):
            violations.append(f"{file_path}: 缺 {name}")
    metrics_section = re.search(r"## 4\.\s*成功指标.*?(?=^##\s|\Z)", content, re.DOTALL | re.MULTILINE)
    if metrics_section:
        for f in REQUIRED_METRICS_FIELDS:
            if f not in metrics_section.group(0):
                violations.append(f"{file_path}: § 4 成功指标 缺字段 {f!r}")
    return main_runner(file_path, violations, "check-product-doc")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check-product-doc.py <file>")
        sys.exit(2)
    sys.exit(check_product_doc(sys.argv[1]))
