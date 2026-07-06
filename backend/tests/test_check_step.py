"""回归测试：scripts/check-step.py 兼容 markdown bold 字段名。

retro.md §3 改进项 #1：每个阶段的 spec/tasks 文档被 check-step.py 卡在 `**测试**:` 上多次，
本测试验证 check_tasks() 函数能识别 **bold** 字段名格式。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

# 直接 import scripts/check-step.py（不在 backend package 里）
_scripts_path = Path(__file__).parent.parent.parent / "scripts" / "check-step.py"
_spec = importlib.util.spec_from_file_location("check_step", _scripts_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
check_tasks = _mod.check_tasks


# ─── 回归测试：bold-tolerant regex ──────────────────────

class TestCheckTasksBoldTolerance:
    """verify check_tasks() 不因 markdown bold 字段名误报。"""

    def test_plain_format_passes(self):
        """纯文本格式（无 bold）通过。"""
        content = """
## 2. 任务清单

### V2.1
- [ ] T1: 任务 1
  - 文件: `f.py:1-50`
  - 测试: `test_x`
  - 依赖: —
  - 估时: 30 min
  - 产出: 1 commit
- [ ] T2: 任务 2
  - 文件: `f.py:50-100`
  - 测试: `test_y`
  - 依赖: T1
  - 估时: 60 min
  - 产出: 1 commit

## 6. 总估时
90 min
"""
        errors = check_tasks(content)
        assert errors == [], f"expected no errors, got {errors}"

    def test_bold_format_passes(self):
        """markdown bold 格式（**字段**）通过 — 这是 retro §3 改进项 #1 修复的关键场景。"""
        content = """
## 2. 任务清单

### V2.1
- [ ] T1: 任务 1
  - **文件**: `f.py:1-50`
  - **测试**: `test_x`
  - **依赖**: —
  - **估时**: 30 min
  - **产出**: 1 commit
- [ ] T2: 任务 2
  - **文件**: `f.py:50-100`
  - **测试**: `test_y`
  - **依赖**: T1
  - **估时**: 60 min
  - **产出**: 1 commit

## 6. 总估时
90 min
"""
        errors = check_tasks(content)
        # 关键：bold 格式不应该再误报"测试用例不足"或"估时 > 1h"
        assert errors == [], f"bold format should pass, got {errors}"

    def test_mixed_format_passes(self):
        """bold + plain 混合格式也通过。"""
        content = """
## 2. 任务清单

### V2.1
- [ ] T1: 任务 1
  - **文件**: `f.py:1-50`
  - 测试: `test_x`           # plain 测试:
  - **依赖**: —
  - 估时: 30 min            # plain 估时:
  - **产出**: 1 commit
- [ ] T2: 任务 2
  - 文件: `f.py:50-100`      # plain 文件:
  - **测试**: `test_y`
  - 依赖: T1                # plain 依赖:
  - **估时**: 60 min
  - 产出: 1 commit

## 6. 总估时
90 min
"""
        errors = check_tasks(content)
        assert errors == [], f"mixed format should pass, got {errors}"

    def test_over_hour_still_fails(self):
        """估时 > 1h 的边界检查仍然生效（bold 容忍不影响核心校验）。"""
        content = """
## 2. 任务清单
- [ ] T1: 大任务
  - **文件**: `f.py`
  - **测试**: `test_x`
  - **依赖**: —
  - **估时**: 2 h
  - **产出**: 1 commit

## 6. 总估时
2 h
"""
        errors = check_tasks(content)
        # 仍应报"估时 > 1h"（修复不能破坏核心校验）
        assert any("> 1h" in e for e in errors), f"should still catch over-hour, got {errors}"

    def test_real_v2_tasks_md_passes(self):
        """实际 V2 tasks.md（曾因 bold 卡 2 次）现在应该通过。"""
        from pathlib import Path
        v2_tasks = (
            Path(__file__).parent.parent
            / "docs"
            / "tasks"
            / "2026-06-28-new-feature-v2-smart-sediment"
            / "tasks.md"
        )
        if not v2_tasks.exists():
            return  # skip if not yet created
        errors = check_tasks(v2_tasks.read_text(encoding="utf-8"))
        assert errors == [], f"V2 tasks.md should pass now, got {errors}"