"""共享基类: 5 模板 checker 通用工具 (per P2-3 决策)"""
import re
import sys
from pathlib import Path

LEGACY_TASKS = re.compile(r"^docs/tasks/2026-07-\d{2}-")


def is_exempt(path: str) -> bool:
    if LEGACY_TASKS.match(path):
        return True
    return False


def has_section(content: str, section_pattern: str) -> bool:
    return re.search(section_pattern, content, re.MULTILINE) is not None


def main_runner(file_path: str, violations: list, checker_name: str) -> int:
    if is_exempt(file_path):
        print(f"⚠️ {checker_name} exempt for {file_path} (legacy)")
        return 0
    if violations:
        for v in violations:
            print(f"::error::{v}")
        print(f"\n❌ {len(violations)} {checker_name} violation(s)")
        return 1
    print(f"✅ {checker_name} passed for {file_path}")
    return 0
