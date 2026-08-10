#!/usr/bin/env python3
"""
check_task_state.py - 任务状态语义检查 (per P0-5 决策)

4 条不变量 (per P0-5 决策主账):
1. 三事实必填: implementation (commit + test + verifier) + phase_acceptance
2. 无 `✅ DONE` 标记
3. L5 段必含 phase_acceptance，REJECTED 不得冒充绿色完成
4. 2026-07-24 状态契约生效前的任务豁免 (legacy)

`[x]` 仅表示 implementation 已落入 commit，可与 test/verifier FAIL 共存；
失败不会抹掉已经发生的 implementation 事实。

Usage:
    python3 scripts/check_task_state.py <tasks_md_path> [--view {index,worktree}]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

# ─── violation 码 ────────────────────────────────────
ERROR_MISSING_THREE_FACTS = "task-state-missing-three-facts"
ERROR_NAKED_DONE = "task-state-naked-done"
ERROR_L5_NEEDS_ACCEPTANCE = "task-state-l5-needs-acceptance"
ERROR_REJECTED_CLAIMS_GREEN = "task-state-rejected-claims-green"

# ─── 豁免模式（状态契约在 2026-07-24 起生效）──────────
# 禁止使用 `2026-07-\d{2}` 之类的整月正则；它会把新任务永久豁免。
EXEMPT_LEGACY = (
    re.compile(r"^docs/tasks/2026-06-"),
    re.compile(r"^docs/tasks/2026-07-(0[1-9]|1\d|2[0-3])-"),
    re.compile(r"^docs/archive/"),
)

# ─── 合法状态枚举 ──────────────────────────────────
TEST_STATES = {"PASS", "FAIL", "NOT_RUN", "N/A"}
VERIFIER_STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED"}
ACCEPTANCE_STATES = {"PENDING", "ACCEPTED", "REJECTED"}


def is_exempt(path: str) -> bool:
    return any(pattern.match(path) for pattern in EXEMPT_LEGACY)


def read_content(path: Path, view: str = "worktree") -> str:
    """Read the worktree file or the exact staged/index version."""
    if view == "worktree":
        return path.read_text()
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise FileNotFoundError(f"staged file not found: {path}")
    return result.stdout


def parse_tasks_md(path: Path, view: str = "worktree") -> tuple[list, list]:
    """返回 (task_blocks, raw_lines)"""
    content = read_content(path, view)
    lines = content.splitlines()
    blocks = []
    current = None
    for i, line in enumerate(lines):
        # 匹配任务表行: | T1 | ... |
        m = re.match(r"\|\s*T(\d+)\s*\|", line)
        if m:
            if current:
                blocks.append((current["lineno"], current))
            current = {
                "task_id": int(m.group(1)),
                "lineno": i + 1,
                "cells": [c.strip() for c in line.split("|")[1:-1]],
            }
    if current:
        blocks.append((current["lineno"], current))
    return blocks, lines


def find_three_facts(cells: list) -> dict:
    """从 11 列表头: 任务 | 测试 | 场景 | REQ | SCN | TC | Level | 实施 commit | test | verifier | acceptance
    找最后 4 列 (索引 7, 8, 9, 10)"""
    if len(cells) < 11:
        return {}
    return {
        "commit": cells[7].strip("`").strip(),
        "test": cells[8].strip(),
        "verifier": cells[9].strip(),
        "acceptance": cells[10].strip(),
    }


def check_three_facts(path: Path, view: str = "worktree") -> list:
    """不变量 1: 三事实必填"""
    errors = []
    if not path.exists():
        return [f"task-state-missing-three-facts: tasks.md not found at {path}"]
    blocks, lines = parse_tasks_md(path, view)
    for lineno, blk in blocks:
        facts = find_three_facts(blk["cells"])
        if not facts:
            errors.append(
                f"{ERROR_MISSING_THREE_FACTS}@{path}:{lineno}: T{blk['task_id']} 缺三事实列 (应 11 列含 实施 commit / test / verifier / acceptance)"
            )
            continue
        for fld in ("commit", "test", "verifier", "acceptance"):
            v = facts.get(fld, "")
            if not v or v == "—":
                errors.append(
                    f"{ERROR_MISSING_THREE_FACTS}@{path}:{lineno}: T{blk['task_id']} {fld} 为空"
                )
    return errors


def check_no_naked_done(content: str, path: Path) -> list:
    """不变量 2: 无 `✅ DONE` 标记"""
    errors = []
    for i, line in enumerate(content.splitlines(), start=1):
        if re.search(r"✅\s*DONE|✅完成", line):
            errors.append(
                f"{ERROR_NAKED_DONE}@{path}:{i}: 裸 `✅ DONE` 标记 (P0-5 决策: [x] 仅表示 implementation, 不含 verifier / acceptance)"
            )
    return errors


def check_l5_acceptance(path: Path, view: str = "worktree") -> list:
    """不变量 3: L5 段必含 phase_acceptance"""
    if not path.exists():
        return []
    errors = []
    content = read_content(path, view)
    # 找 L5 段
    m = re.search(r"## L5[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not m:
        return []
    l5_content = m.group(1)
    if "phase_acceptance" not in l5_content:
        errors.append(
            f"{ERROR_L5_NEEDS_ACCEPTANCE}@{path}: L5 段缺 phase_acceptance 字段 (per P0-5 决策)"
        )
    return errors


def check_rejected_claims_green(path: Path, view: str = "worktree") -> list:
    """不变量 4 衍生: phase_acceptance=REJECTED 但 L5 结果标 PASSED/🟢"""
    if not path.exists():
        return []
    errors = []
    content = read_content(path, view)
    m = re.search(r"## L5[^\n]*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not m:
        return []
    l5_content = m.group(1)
    if "REJECTED" in l5_content and re.search(r"PASSED|🟢", l5_content):
        errors.append(
            f"{ERROR_REJECTED_CLAIMS_GREEN}@{path}: L5 段含 phase_acceptance=REJECTED 但同时标 PASSED/🟢"
        )
    return errors


def main():
    parser = argparse.ArgumentParser(description="任务状态语义检查 (per P0-5)")
    parser.add_argument("path", help="tasks.md 路径 (含对应 verify.md 同目录)")
    parser.add_argument("--view", choices=["index", "worktree"], default="worktree")
    args = parser.parse_args()

    input_path = Path(args.path)
    tasks_path = (
        input_path.parent / "tasks.md"
        if input_path.name == "verify.md"
        else input_path
    )
    dir_path = tasks_path.parent

    # 豁免检查
    rel = str(input_path).replace(str(Path.cwd()) + "/", "")
    if is_exempt(rel):
        print(f"⚠️ task-state check exempt for {rel} (legacy pre-P0-5)")
        return 0

    errors = []
    errors.extend(check_three_facts(tasks_path, args.view))
    if tasks_path.exists():
        content = read_content(tasks_path, args.view)
        errors.extend(check_no_naked_done(content, tasks_path))
    verify_path = dir_path / "verify.md"
    if verify_path.exists():
        errors.extend(check_l5_acceptance(verify_path, args.view))
        errors.extend(check_rejected_claims_green(verify_path, args.view))
    if errors:
        for e in errors:
            print(f"::error::{e}")
        print(f"\n❌ {len(errors)} task-state violation(s) found")
        return 1
    print(f"✅ task-state check passed for {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
