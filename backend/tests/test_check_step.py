"""回归测试：scripts/check-step.py 兼容 markdown bold 字段名。

retro.md §3 改进项 #1：每个阶段的 spec/tasks 文档被 check-step.py 卡在 `**测试**:` 上多次，
本测试验证 check_tasks() 函数能识别 **bold** 字段名格式。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

# 直接 import scripts/check-step.py（不在 backend package 里）
_scripts_path = Path(__file__).parent.parent.parent / "scripts" / "check-step.py"
_spec = importlib.util.spec_from_file_location("check_step", _scripts_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
check_tasks = _mod.check_tasks
check_research = _mod.check_research
check_plan = _mod.check_plan
check_verify = _mod.check_verify
CHECKS = _mod.CHECKS
REPO_ROOT = Path(__file__).parent.parent.parent
CHECK_STEP = REPO_ROOT / "scripts" / "check-step.py"


def run_checker(step: str, path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_STEP), step, str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


TEMPLATE_CASES = [
    ("research", "research-new-feature.md"),
    ("research", "research-bug.md"),
    ("research", "research-refactor.md"),
    ("research", "research-p0.md"),
    ("spec", "spec-template.md"),
    ("plan", "plan-template.md"),
    ("tasks", "tasks-template.md"),
    ("implement", "test-cases-template.md"),
    ("verify", "verify-template.md"),
    ("retro", "retro-template.md"),
]


class TestTemplateResidueGate:
    """P0-2：模板结构和示例不能冒充真实 DOD 证据。"""

    @pytest.mark.parametrize(("step", "template_name"), TEMPLATE_CASES)
    def test_repository_templates_are_rejected(self, step, template_name):
        template = REPO_ROOT / "docs" / "templates" / template_name

        result = run_checker(step, template)

        assert result.returncode == 1, (
            f"{template_name} is an empty template and must fail, "
            f"but checker returned {result.returncode}:\n{result.stdout}"
        )

    def test_renamed_template_with_placeholders_is_rejected(self, tmp_path):
        content = (
            (REPO_ROOT / "docs" / "templates" / "spec-template.md")
            .read_text(encoding="utf-8")
            .replace("Spec 规格模板（技术脑）", "示例功能规格")
            .replace("tags: [spec, 1步, 技术脑, 模板]", "tags: [spec, 1步, 技术脑]")
        )
        copied_spec = tmp_path / "spec.md"
        copied_spec.write_text(content, encoding="utf-8")

        result = run_checker("spec", copied_spec)

        assert result.returncode == 1
        assert "模板残留" in result.stdout

    def test_technical_angle_brackets_are_not_placeholders(self, tmp_path):
        content = """
## 0. 上游引用
调研报告：research.md；用户已确认 2026-07-26。

## 1. 用户故事
作为开发者，我想验证文档内容，以便阻止空模板。

## 2. 验收标准
### Requirement: 阻断空模板
The system SHALL reject documents that still contain template residue.

#### Scenario: valid JSX
Given 文档包含 React `<Component>`，When 校验，Then 通过。
#### Scenario: valid path
Given 文档包含路径 `<id>`，When 校验，Then 通过。
#### Scenario: valid comparison
Given 文档包含性能目标 `< 200ms`，When 校验，Then 通过。

说明：`Scenario: <场景名>` 是单处格式示例，不代表整份文档为空。

## 3. 边界条件
空值、异常、并发、时序、安全、性能、兼容、国际化均已说明。

## 4. 数据契约
Pydantic BaseModel Schema：字段 content 为 str。

## 5. 测试场景
- [ ] TC-1: JSX 语法
- [ ] TC-2: 路径参数
- [ ] TC-3: 性能比较符
"""
        valid_spec = tmp_path / "spec.md"
        valid_spec.write_text(content, encoding="utf-8")

        result = run_checker("spec", valid_spec)

        assert result.returncode == 0, result.stdout

    def test_document_about_empty_templates_is_not_itself_a_template(self):
        content = """
---
title: P0 调研 · 空模板被 DOD checker 判绿
status: approved
tags: [p0, governance]
---
# P0 调研 · 空模板被 DOD checker 判绿

本文分析空模板为什么会被误判，不是一个待填写模板。
"""

        assert _mod.check_template_residue(content) == []

    def test_cli_reports_template_residue(self):
        template = REPO_ROOT / "docs" / "templates" / "verify-template.md"

        result = run_checker("verify", template)

        assert result.returncode == 1
        assert "模板残留" in result.stdout


# ─── 回归测试：bold-tolerant regex ──────────────────────

class TestCheckTasksBoldTolerance:
    """verify check_tasks() 不因 markdown bold 字段名误报。"""

    def test_plain_format_passes(self):
        """纯文本格式（无 bold）通过。"""
        content = """
---
type: tasks
layer: L1
---
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
---
type: tasks
layer: L1
---
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
---
type: tasks
layer: L1
---
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


class TestSixStepWorkflowV2:
    """回归测试：校验器必须与 6 步 v2 保持一致。"""

    def test_research_accepts_full_6(self):
        content = """
> 路径模式：`full-6`
## 1. 任务理解
已确认。
## 2. 现状扫描
已读 `docs/issues.md`，找到 3 个相关文件，已跑 `git log -10` 和 `git status`。
## 3. 依赖发现
列出调用方。
## 4. 风险评估
🔴 风险一；🟡 风险二。
## 5. 输出建议
走完整 6 步。
"""
        assert check_research(content) == []

    def test_research_rejects_full_7(self):
        errors = check_research("> 路径模式：`full-7`")
        assert any("full-6" in error for error in errors)

    def test_research_accepts_other_v2_path_modes(self):
        cases = {
            "fix-mini": ["任务理解", "复现路径", "影响范围", "根因假设", "最近相关改动", "输出建议"],
            "refactor-6": ["任务理解", "现状分析", "重构方案", "风险评估", "输出建议"],
            "timebox": ["影响", "临时止血", "根本原因", "后续时间盒", "沟通"],
        }
        for mode, sections in cases.items():
            body = [f"> 路径模式：`{mode}`"]
            body.extend(f"## {index}. {section}\n已填写" for index, section in enumerate(sections, 1))
            if mode != "timebox":
                body.append("证据：docs/issues.md；git log -10；git status")
            errors = check_research("\n".join(body))
            assert errors == [], f"{mode} should pass, got {errors}"

    def test_plan_allows_explicitly_inapplicable_product_docs(self):
        content = """
上游：research.md + spec.md；product-doc.md：不适用；design-spec.md：不适用
## 1. 推荐方案
**推荐**: 方案 A
## 2. 方案对比
方案 A
方案 B
## 3. 风险评估
🔴 风险一
🟡 风险二
🟢 风险三
## 4. 决策点
决策 1：使用现有模式
"""
        assert check_plan(content) == []

    def test_verify_accepts_distributed_evidence_plus_l3_l5(self):
        content = """
## 0. 上游证据
L1 类型检查：✅；L2 单元测试：✅；L4 review：PASS
## L3 整合测试
结果：PASSED ✅
## L5 staging 运行时验证
结果：PASSED ✅
"""
        assert check_verify(content) == []

    def test_verify_rejects_missing_l5(self):
        content = """
## 0. 上游证据
L1：✅；L2：✅；L4：PASS
## L3 整合测试
结果：PASSED ✅
"""
        errors = check_verify(content)
        assert any("L5" in error for error in errors)

    def test_verify_rejects_explicit_failed_result(self):
        content = """
## 0. 上游证据
L1：✅；L2：✅；L4：PASS
## L3 整合测试
结果：FAILED ❌
## L5 staging 运行时验证
结果：PASSED ✅
"""
        errors = check_verify(content)
        assert any("L3 最终结果为失败" in error for error in errors)

    def test_ship_is_not_a_workflow_step(self):
        assert "ship" not in CHECKS
