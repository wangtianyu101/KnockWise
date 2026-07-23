# 复盘 · pre-commit 环境 Gate fail closed

> 路径模式：`fix-mini` · 实施 commit：`e0c9995`
> 决策：[`decisions.md`](decisions.md) 决策 1 · 验证：[`verify.md`](verify.md)

## 一、数据

| 维度 | 值 |
|---|---|
| 总估时 | 120 min |
| 实际耗时 | ~50 min（含 8 场景 fixture 调试 · 2 次写入被拒后等用户授权） |
| 偏差 | 提前 58% |
| commit 数 | 1（`e0c9995`） |
| 改动文件 | `scripts/pre-commit`（+47/-26，两个 Gate 段重写）+ `backend/tests/test_pre_commit_env_gate.py`（+474，新增）+ `docs/tasks/.../tasks.md`（+30，新增） |
| 测试 | 30/30 PASSED（含新增 8 + 既有 22） + 全套 722/722 PASSED |
| 返工次数 | 2（场景 8 mock 设计 · symlink vs wrapper） |
| 调研偏差 | 0 |
| 范围控制 | ✅ 严格遵守 8 项明确排除 |

## 二、做对的事

1. **TDD 严格执行**：8 场景红/绿对照（修复前 2 RED，修复后 8 GREEN）；完整 pytest 验证无 regression。
2. **场景 8 fixture 调试**：从 symlink 失败 → wrapper script 解决（python 通过 symlink 调用时 `sys.executable` 指向真实 binary，找不到 venv site-packages，导致 `import pytest` 失败）。保留这个发现供未来参考。
3. **阻断信息含真实恢复命令**：删除 `scripts/setup.sh` 误导指引（该项目无该脚本），改用 `python3 -m venv .venv && pip install -r requirements.txt` + `cd frontend && npm ci`。
4. **保留 P0-1 行为**：pytest/tsc 真失败仍正确阻断（场景 5/7）。
5. **风险范围感知**：纯 docs 不触发应用环境 Gate（场景 1）。

## 三、做错的事

1. **场景 8 误用 symlink**：直接 `os.symlink(host_python, bin_dir / "python")` 让 python 通过 symlink 调用，导致 `sys.executable` 是 `/opt/homebrew/.../python3.12`，找不到 venv site-packages 中的 pytest。改用 wrapper script `exec host_python "$@"` 后通过。**根因**：未先验证 python venv symlink 行为。
2. **场景 6 没加 `npm ci` 关键词断言**：初版只断言 returncode != 0，后来加了 `npm ci` 关键词确保恢复命令真实性。
3. **写 verify.md / retro.md 时被用户拒**：第一次 Write 工具调用两次被拒（用户希望先授权再写）。后续 § 6.6 场景需提前确认"用户是否授权完整 5/6 步文档"。

## 四、改进项

| # | 改进 | 负责人 | 优先级 |
|---|---|---|---|
| 1 | **Python venv symlink 行为记录**：python 通过 symlink 调用时 sys.executable 指向真实 binary，venv site-packages 找不到 → 必须 wrapper script 或真实 venv 重建 | 负责人: memory feedback | 🟢 中 |
| 2 | **`scripts/setup.sh` 误导指引排查**：扫一遍其他文档/脚本是否还有引用不存在的脚本（同步检查 `local-dev.md`） | 负责人: 后续 task | 🟡 建议另开 |
| 3 | **轻量 backend-test bootstrap/profile 作为独立 P1**：避免每次 dev 都要安装完整 requirements（research.md § 6.3 已识别） | 负责人: 后续 P1 task | 🟢 长期 |
| 4 | **pytest 探针 + pytest 真运行的双重保护**：防止未来有人改 pytest 安装位置后探针误报 | 负责人: hook 自检 | 🟡 中 |
| 5 | **写大文档前先与用户确认授权**：避免 Write 工具调用被拒浪费时间 | 负责人: AI 流程规则 | 🟡 高 |

## 五、沉淀（规则更新建议）

1. **新增 memory `feedback-python-venv-symlink-pitfall`**：python 通过 symlink 调用时 sys.executable 指向真实 binary，找不到 venv site-packages。测试场景下 mock venv 必须用 wrapper script `exec host_python "$@"`，不能用 symlink。
2. **新增 memory `feedback-precommit-fail-closed-pattern`**：CI/hook 的"环境缺失时只 warning 跳过"是确定性假绿源。最小修复模式 = 风险范围感知 + 可执行 binary 检测 + 最小工具探针 + 真实恢复命令 + 删除误导指引。
3. **更新 `feedback-pipe-exit-code-bug-in-sh.md`**：本次 hook 修复同时用了 4 处同样的"set +e/var capture/set -e/exit 1"模式（pytest 探针、pytest 真跑、tsc 探针、tsc 真跑），证明该模式是 POSIX sh 的标准捕获退出码 pattern，已成铁律。

## 六、memory 更新清单

- [ ] 写 `feedback-python-venv-symlink-pitfall.md`（mock venv 必须 wrapper exec · 不能 symlink）→ 必写
- [ ] 写 `feedback-precommit-fail-closed-pattern.md`（环境缺失 fail closed 模式）→ 必写
- [ ] 更新 `feedback-pipe-exit-code-bug-in-sh.md`（4 处复用已成铁律）→ 选写
- [ ] 改进项 #2（`scripts/setup.sh` 误导指引排查）→ 留作新 task，不在本修复 scope
- [ ] 改进项 #5（写大文档前确认授权）→ 立即沉淀到 § 6.6 流程