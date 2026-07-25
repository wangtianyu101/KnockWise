#!/usr/bin/env python3
"""check-component-spec.py (P2-3 决策 5/5)"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from check_spec_base import is_exempt, has_section, main_runner

REQUIRED_SECTIONS = [
    (r"^##\s*0[\.、\s]*(?:上游|引用|reference)", "§ 0 上游引用"),
    (r"^##\s*1[\.、\s]*(?:组件清单|components)", "§ 1 组件清单"),
    (r"^##\s*2[\.、\s]*(?:Props|props)", "§ 2 Props"),
    (r"^##\s*3[\.、\s]*(?:State|state|useState)", "§ 3 State"),
    (r"^##\s*4[\.、\s]*(?:Events|on[A-Z])", "§ 4 Events"),
]


def check_component_spec(file_path: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ check-component-spec exempt for {file_path} (legacy)")
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
    return main_runner(file_path, violations, "check-component-spec")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check-component-spec.py <file>")
        sys.exit(2)
    sys.exit(check_component_spec(sys.argv[1]))
