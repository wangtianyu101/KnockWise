# Verify · pre-commit DOD checker 退出码修复

> 路径模式：`fix-mini` · 实施 commit：`d91fdef` + `ee6da13`
> 决策：[`decisions.md`](decisions.md) 决策 1：方案 A · 3 个回归场景

## 0. 上游证据

- L1 类型检查：✅（shell 不需类型检查）
- L2 单元测试：✅（详见 L3）
- L4 review：PASS（独立 verifier 校验，详见末段）

## L3 整合测试

测试主体：`backend/tests/test_pre_commit_hook.py`（端到端用 `subprocess.run` 真实执行 `sh scripts/pre-commit`）

### 实施命令

```
cd backend && .venv/bin/python -m pytest tests/test_pre_commit_hook.py tests/test_check_step.py -v
```

### 结果

✅ 16/16 PASSED（13 个 `test_check_step.py` + 3 个 `test_pre_commit_hook.py`）。

| 场景 | checker 退出码 | 期望 | 实际 |
|---|---|---|---|
| 1. 合法 research.md | 0 | hook exit 0 + 通过校验 | ✅ |
| 2. 非法 research.md（缺路径模式） | 1 | hook exit ≠ 0 + 阻断诊断 | ✅（修复前 RED，修复后 GREEN） |
| 3. 非法 tasks.md（多行错误） | 1 | hook exit ≠ 0 + tail ≤ 10 行 | ✅（修复前 RED，修复后 GREEN） |

## L5 staging 运行时验证

修复前后行为对照（手动验证）：

### 修复前（commit 9d8ecbc 的 hook 代码）

```sh
$ python3 scripts/check-step.py tasks /tmp/bad_tasks.md 2>&1 | tail -10
❌ tasks DOD 校验失败 (...): ...   # checker 输出
$ echo "${PIPESTATUS[@]}"           # bash 数组
0 1                              # tail=0, python=1
```

但 hook 的 `if ! python3 ... | tail -10; then` 取 `!` 后是 `tail` 的 0（POSIX `sh` 默认取末端），所以 `failed=1` 不执行。

### 修复后（commit d91fdef 的 hook 代码）

```sh
$ check_out=$(python3 scripts/check-step.py tasks /tmp/bad_tasks.md 2>&1); check_rc=$?
$ echo $check_rc
1                                # 真实捕获
$ printf '%s\n' "$check_out" | tail -10   # 仅展示末 10 行
❌ tasks DOD 校验失败 (...): ...
$ if [ "$check_rc" -ne 0 ]; then echo BLOCKED; fi
BLOCKED
```

✅ commit `d91fdef` 修复后，`failed=1` 正确执行，commit 被阻断。

## 独立 verifier 校验（§ 6.7 commit 级 verify）

独立 agent（全新 prompt 上下文）对照 `decisions.md` 决策 1 § 6.1 方案 A 校验：

- **A. 修复正确性**：**[ PASS ]** — diff 完全对齐方案 A；3/3 测试 PASS；手动复现根因（修复前 `bash -c 'python3 ... | tail -10; echo rc=$?'` 输出 `rc=0`）证实管道吞掉 checker 退出码；修复后 `check_rc=$?` 在 pipe 之前捕获 → `failed=1` → `exit 1`。
- **B. 测试覆盖**：**[ PASS ]** — `test_pre_commit_hook.py` 含 3 个 TestCase（合法/非法/长输出非法），用 `subprocess.run` 真实跑 hook + 临时 git repo + 复制 hook 与 checker，覆盖完整 Shell 调用路径，无 mock。
- **C. 边界**：**[ PASS ]** — 不可动文件（`livekit.yaml`、`seed_data/`、`.venv/`、`.env.local`、`node_modules/`）未被触碰；`scripts/check-step.py` 主体未改（测试用 `shutil.copy` 而非修改）；用户未授权改动（`.agents/`、`profile_settlement_service.py`、`docs/issues.md`）不在 diff 中。
- **D. 范围控制**：**[ PASS ]** — 未加全局 `pipefail`、未引入 `mktemp`/`trap`、`check_retro` 未动、未做环境 fail-closed、未做 hook 自动安装、未做 hook 重构（diff 仅 8 行集中于 § 4 DOD 段）。

**最终裁决：PASS**。证据路径：`scripts/pre-commit:106-114`、`backend/tests/test_pre_commit_hook.py`、`decisions.md:30,86`。

## 结果

✅ **PASS** — 修复 + 测试完全对齐决策 1 方案 A；根因复现与修复后行为均有证据；16/16 测试全绿；scope 控制严格。