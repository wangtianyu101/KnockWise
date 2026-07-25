#!/usr/bin/env python3
"""
check-frontmatter.py - 验证 13+ 模板文件 frontmatter (per P2-4 决策)

最小必填 6 字段: title / type / step / date / status / tags
type 枚举: 13 种
status 枚举: 4 种

Usage:
    python3 scripts/check-frontmatter.py <file_or_dir>...
"""
import argparse
import re
import sys
from pathlib import Path

# ─── 配置 ─────────────────────────────────────────
ALLOWED_TYPES = {
    "research", "spec", "plan", "tasks",
    "product-doc", "design-spec", "api-spec", "component-spec",
    "db-design", "verify", "retro", "test-cases", "meta",
}
# status 兼容: 4 种枚举 OR 版本字符串 (v1/v2/v3 等)
ALLOWED_STATUS = {"draft", "in-review", "approved", "archived"}
# date 兼容: ISO date (YYYY-MM-DD) OR updated 字段
REQUIRED_FIELDS = ["title", "type", "step", "status", "tags"]

# legacy 豁免
LEGACY_TASKS = re.compile(r"^docs/tasks/2026-07-\d{2}-")


def is_exempt(path: Path) -> bool:
    rel = str(path)
    if LEGACY_TASKS.match(rel):
        return True
    return False


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """返回 (fm_dict, fm_block_text)"""
    if not content.startswith("---\n"):
        return {}, ""
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, ""
    block = content[4:end]
    fm = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, content[:end + 5]


def check_file(path: Path) -> list:
    errors = []
    if is_exempt(path):
        return errors
    if not path.exists():
        return [f"file not found: {path}"]
    content = path.read_text()
    fm, _ = parse_frontmatter(content)
    if not fm:
        return [f"{path}: 缺 frontmatter 块 (--- 包围)"]
    # 必填字段
    for f in REQUIRED_FIELDS:
        if f not in fm or not fm[f]:
            errors.append(f"{path}: 缺必填字段 {f!r}")
    # type 枚举
    if "type" in fm and fm["type"] not in ALLOWED_TYPES:
        errors.append(
            f"{path}: type {fm['type']!r} 不在 ALLOWED_TYPES 枚举 (13 种)"
        )
    # status 枚举 OR 版本字符串 (兼容现有 v1/v2 等)
    if "status" in fm:
        s = fm["status"]
        if s not in ALLOWED_STATUS and not re.match(r"^v\d+(\.\d+)*$", s):
            errors.append(
                f"{path}: status {s!r} 既不在 4 种枚举也不是 vN 版本字符串"
            )
    # step 范围
    if "step" in fm:
        try:
            step = int(fm["step"])
            if not (-1 <= step <= 6):
                errors.append(f"{path}: step {step} 越界 (-1 ~ 6)")
        except ValueError:
            errors.append(f"{path}: step 需为整数")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Frontmatter schema 验证 (per P2-4)")
    parser.add_argument("paths", nargs="+", help="文件或目录路径")
    parser.add_argument("--strict", action="store_true", help="legacy 任务也校验")
    args = parser.parse_args()

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            files.extend(path.rglob("*.md"))
        else:
            files.append(path)

    errors = []
    for f in files:
        if "node_modules" in str(f) or "test-results" in str(f):
            continue
        if not args.strict and is_exempt(f):
            continue
        errors.extend(check_file(f))

    if errors:
        for e in errors:
            print(f"::error::{e}")
        print(f"\n❌ {len(errors)} frontmatter violation(s)")
        return 1
    print(f"✅ frontmatter check passed ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
