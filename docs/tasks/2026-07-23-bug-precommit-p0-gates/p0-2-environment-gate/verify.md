# Verify · pre-commit 环境 Gate fail closed

> 路径模式：`fix-mini` · 实施 commit：`e0c9995`
> 决策：[`decisions.md`](decisions.md) 决策 1：风险范围感知的 fail closed + 最小健康探针 + 8 个回归场景

## 0. 上游证据

- L1 类型检查：✅（shell 不需类型检查）
- L2 单元测试：✅（详见 L3）
- L4 review：PASS（手动对照 8 场景）

## L3 整合测试

### 实施命令

```bash
cd backend && .venv/bin/python -m pytest tests/test_pre_commit_env_gate.py tests/test_pre_commit_hook.py tests/test_check_step.py tests/test_ci_workflow.py -v
cd backend && .venv/bin/python -m pytest tests/ --tb=line -q
```

### 结果

✅ 30/30 PASSED（含新增 8 个 `test_pre_commit_env_gate.py` + 既有 P0-1 / check_step / ci_workflow）。
✅ 完整 `tests/` **722 passed, 2 skipped, 4 xfailed, 0 failed**。

### 8 场景对照

| # | 场景 | 修复前 | 修复后 |
|---|---|---|---|
| 1 | 纯 docs + env 缺失 | ✅ 通过（原本就 OK） | ✅ 通过 |
| 2 | 后端 + .venv 缺失 | ❌ 假绿通过 | ✅ 阻断 |
| 3 | Python 不可执行 | ⚠️ 阻断但说"pytest 失败" | ✅ 阻断 + 环境损坏信息 |
| 4 | pytest 探针失败 | ⚠️ 阻断但说"pytest 失败" | ✅ 阻断 + 探针失败信息 |
| 5 | 环境健康但 pytest 真失败 | ✅ 阻断（P0-1 已有） | ✅ 阻断 |
| 6 | 前端 + tsc 缺失 | ❌ 假绿通过 | ✅ 阻断 |
| 7 | tsc 不可执行 | ⚠️ 阻断但说"tsc 失败" | ✅ 阻断 + tsc 损坏信息 |
| 8 | 环境健康 + 测试通过 | ✅ 通过 | ✅ 通过 |

修复前 2 个场景明显 RED（场景 2/6 假绿），4 个场景语义模糊（3/4/7/8 阻断信息失真），修复后全 GREEN + 信息真实。

## L5 staging 运行时验证

修复前后行为对照（手工验证）：

### 修复前（commit d91fdef 之后的 hook 代码）

```sh
$ # 后端改动 + .venv 缺失
$ ls backend/.venv
ls: backend/.venv: No such file or directory
$ sh scripts/pre-commit
⚠️  backend/.venv 不存在,跳过 pytest(首次 clone 后跑 ./scripts/setup.sh)
✅ pre-commit 全部通过        # 🐛 假绿：未跑测试却报通过
```

### 修复后（commit e0c9995 的 hook 代码）

```sh
$ # 后端改动 + .venv 缺失
$ sh scripts/pre-commit
❌ backend/.venv 不存在,禁止 commit
   恢复: cd backend && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
   绕过(仅紧急): PRE_COMMIT_SKIP=1 git commit ...
exit 1
```

✅ commit `e0c9995` 修复后，环境缺失正确阻断，附带真实恢复命令。

### 阻断信息真实性

| 场景 | 阻断信息含 | 含 scripts/setup.sh |
|---|---|---|
| 后端 .venv 缺失 | `cd backend && python3 -m venv .venv && pip install -r requirements.txt` | ❌（已删除误导指引） |
| Python 不可执行 | `rm -rf backend/.venv && python3 -m venv .venv && pip install` | ❌ |
| pytest 探针失败 | `pip install -r requirements.txt` + probe stderr | ❌ |
| 前端 node_modules 缺失 | `cd frontend && npm ci` | ❌ |
| tsc 不可执行 | `rm -rf node_modules && npm ci` | ❌ |

恢复命令均能在该项目实际工作（不再引用不存在的 `scripts/setup.sh`）。

## 结果

✅ **PASS** — 修复与决策 1 方案严格对齐：环境缺失/损坏正确阻断 + 真实恢复命令 + 删除误导指引；纯 docs 不被波及；P0-1 行为保留；30/30 + 722/722 测试全绿。