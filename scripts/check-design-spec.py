#!/usr/bin/env python3
"""check-design-spec.py (P2-3 决策 2/5)"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from check_spec_base import is_exempt, has_section, main_runner

REQUIRED_SECTIONS = [
    (r"^##\s*0[\.、\s]*用户旅程", "§ 0 用户旅程"),
    (r"^##\s*1[\.、\s]*页面地图", "§ 1 页面地图"),
    (r"^##\s*2[\.、\s]*(?:线框|wireframe|线框)", "§ 2 wireframe"),
    (r"^##\s*3[\.、\s]*交互.*状态", "§ 3 交互状态"),
    (r"^##\s*4[\.、\s]*(?:视觉规范|视觉.*规范)", "§ 4 视觉规范"),
]


def check_design_spec(file_path: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ check-design-spec exempt for {file_path} (legacy)")
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
    return main_runner(file_path, violations, "check-design-spec")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check-design-spec.py <file>")
        sys.exit(2)
    sys.exit(check_design_spec(sys.argv[1]))
