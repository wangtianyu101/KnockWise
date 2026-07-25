#!/usr/bin/env python3
"""check-db-design.py (P2-3 决策 4/5)"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from check_spec_base import is_exempt, has_section, main_runner

REQUIRED_SECTIONS = [
    (r"^##\s*0[\.、\s]*(?:ER|表结构|数据模型)", "§ 0 ER 图/表结构"),
    (r"^##\s*1[\.、\s]*(?:forward|migration|forward.sql)", "§ 1 forward SQL"),
    (r"^##\s*2[\.、\s]*(?:rollback|backward|rollback.sql)", "§ 2 rollback SQL"),
    (r"^##\s*3[\.、\s]*(?:索引|index)", "§ 3 索引"),
    (r"^##\s*4[\.、\s]*(?:数据影响|data.*impact)", "§ 4 数据影响"),
]


def check_db_design(file_path: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ check-db-design exempt for {file_path} (legacy)")
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
    return main_runner(file_path, violations, "check-db-design")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check-db-design.py <file>")
        sys.exit(2)
    sys.exit(check_db_design(sys.argv[1]))
