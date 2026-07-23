# Tasks · pre-commit DOD checker 退出码修复

> 路径模式：`fix-mini`（0 调研 → 4 实施/回归测试 → 6 复盘）
> 决策：[`decisions.md`](decisions.md) 决策 1：方案 A · 3 个回归场景

## 2. 任务清单

- [ ] T1: 修复 hook（POSIX 显式 `output + rc`）
  - **文件**: `scripts/pre-commit:106-113`
  - **测试**: `backend/tests/test_pre_commit_hook.py::TestDodCheckBlocksInvalidDoc` + `TestDodCheckTruncatesAndStillBlocks`
  - **依赖**: —
  - **估时**: 30 min
  - **产出**: 1 commit

- [ ] T2: 写红/绿测试 3 个场景
  - **文件**: `backend/tests/test_pre_commit_hook.py`
  - **测试**: 自身（3 用例：合法 / 非法 / 长输出非法）
  - **依赖**: T1
  - **估时**: 30 min
  - **产出**: 1 commit

- [ ] T3: 实测 + 跑相邻 `test_check_step.py` 确认无破坏
  - **文件**: —
  - **测试**: `pytest tests/test_check_step.py tests/test_pre_commit_hook.py`
  - **依赖**: T2
  - **估时**: 10 min
  - **产出**: 验证通过

## 6. 总估时

70 min

## 实施状态

- ✅ 已实施（3/3 测试通过）· 修复前场景 2/3 RED，修复后全 GREEN。
- 🚫 暂不做：环境 fail-closed、hook 自动安装、全 hook 重构、全局 `pipefail`、`check_retro` 覆盖（决策 1 § 明确排除）

## commit 历史

| 日期 | commit | 任务 | 估时 | 实际 | 偏差 |
|---|---|---|---|---|---|
| 2026-07-23 | (T1+T2+T3 合并 commit) | 全部 | 70 min | ~30 min | 提前完成（hook 改动极小、pytest 模板复用） |