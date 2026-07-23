# Tasks · test_ci_workflow.py 旧断言修复

> 路径模式：`fix-mini`（0 调研 → 4 实施/回归测试 → 6 复盘）
> 决策：[`decisions.md`](decisions.md) 决策 1：最小修复范围

## 2. 任务清单

- [ ] T1: 改 `test_ci_workflow.py` 一个函数（重命名 + 删 `@v6` 3 条断言 + 加 SHA pin 3 条断言）
  - **文件**: `backend/tests/test_ci_workflow.py:54-60`
  - **测试**: `pytest tests/test_ci_workflow.py`（6/6 PASSED）
  - **依赖**: —
  - **估时**: 15 min
  - **产出**: 1 commit

- [ ] T2: 跑相邻测试确认无破坏
  - **文件**: —
  - **测试**: `pytest tests/test_ci_workflow.py tests/test_check_step.py tests/test_pre_commit_hook.py`（22/22）+ `pytest tests/`（714/714）
  - **依赖**: T1
  - **估时**: 5 min
  - **产出**: 验证通过

## 6. 总估时

20 min

## 实施状态

- ✅ 已实施（6/6 + 714/714 全绿）· 修复前 RED（1 failed 5 passed），修复后全 GREEN。
- 🚫 暂不做：workflow YAML 改动 / `check_action_sha.py` pytest 覆盖 / 重构 test_ci_workflow.py（决策 1 § 明确排除）

## commit 历史

| 日期 | commit | 任务 | 估时 | 实际 | 偏差 |
|---|---|---|---|---|---|
| 2026-07-23 | (T1+T2 合并 commit) | 全部 | 20 min | ~15 min | 提前（grep 已固化 SHA、Edit 一处完成） |