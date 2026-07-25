#!/usr/bin/env python3
"""check-api-spec.py (P2-3 决策 3/5)"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from check_spec_base import is_exempt, has_section, main_runner

REQUIRED_SECTIONS = [
    (r"^##\s*0[\.、\s]*接口清单", "§ 0 接口清单"),
    (r"^##\s*1[\.、\s]*(?:请求|Request)", "§ 1 Request"),
    (r"^##\s*2[\.、\s]*(?:响应|Response)", "§ 2 Response"),
    (r"^##\s*3[\.、\s]*(?:错误码|error)", "§ 3 错误码"),
    (r"^##\s*4[\.、\s]*(?:认证|auth)", "§ 4 认证"),
]


def check_api_spec(file_path: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ check-api-spec exempt for {file_path} (legacy)")
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
    return main_runner(file_path, violations, "check-api-spec")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check-api-spec.py <file>")
        sys.exit(2)
    sys.exit(check_api_spec(sys.argv[1]))
