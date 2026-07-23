# Tasks · pre-commit 环境缺失/损坏 Gate

> 路径模式：`fix-mini`（0 调研 → 4 实施/回归测试 → 6 复盘）
> 决策：[`decisions.md`](decisions.md) 决策 1：风险范围感知的 fail closed + 最小健康探针 + 8 个回归场景
> 调研：[`research.md`](research.md)（已含决策依据）

## 2. 任务清单

- [ ] T1: 修复 scripts/pre-commit 后端段 · 环境健康探针
  - **文件**: `scripts/pre-commit:21-41`（后端 § 1 段）
  - **测试**: `tests/test_pre_commit_env_gate.py::TestBackendGate*`（场景 2-5）
  - **依赖**: —
  - **估时**: 30 min
  - **产出**: 1 commit

- [ ] T2: 修复 scripts/pre-commit 前端段 · 环境健康探针
  - **文件**: `scripts/pre-commit:43-63`（前端 § 2 段）
  - **测试**: `tests/test_pre_commit_env_gate.py::TestFrontendGate*`（场景 6-7）
  - **依赖**: T1
  - **估时**: 20 min
  - **产出**: 1 commit

- [ ] T3: 修复 scripts/pre-commit 路径分类 · 风险范围感知
  - **文件**: `scripts/pre-commit:18-19`（backend_changed / frontend_changed 计算）
  - **测试**: 场景 1（纯 docs）/ 场景 8（健康）
  - **依赖**: T2
  - **估时**: 15 min
  - **产出**: 1 commit

- [ ] T4: 写红/绿测试 8 场景（端到端）
  - **文件**: `backend/tests/test_pre_commit_env_gate.py`
  - **测试**: 自身 8 个用例
  - **依赖**: T3
  - **估时**: 45 min
  - **产出**: 1 commit

- [ ] T5: 实测 + 跑相邻测试确认无破坏
  - **文件**: —
  - **测试**: `pytest tests/test_pre_commit_env_gate.py tests/test_pre_commit_hook.py tests/test_check_step.py tests/test_ci_workflow.py`
  - **依赖**: T4
  - **估时**: 10 min
  - **产出**: 验证通过

## 6. 总估时

120 min

## 实施状态

- 🟡 已决策 · 待实施（decisions.md 决策 1 · 用户原话"确认"）
- 🚫 暂不做（明确排除）：hook 自动安装、required checks、bypass trailer、新建多 profile setup.sh、start.sh 服务健康、端口误判、全量 pre-commit 重构、P0-1

## commit 历史

| 日期 | commit | 任务 | 估时 | 实际 | 偏差 |
|---|---|---|---|---|---|
| 2026-07-23 | (T1-T5 多 commit) | 全部 | 120 min | (待填) | (待填) |