# Verify · test_ci_workflow.py 旧断言修复

> 路径模式：`fix-mini` · 实施 commit：`d5c11e1`
> 决策：[`decisions.md`](decisions.md) 决策 1：最小修复范围

## 0. 上游证据

- L1 类型检查：✅（Python 无需类型检查）
- L2 单元测试：✅（详见 L3）
- L4 review：PASS（见末段手工对照）

## L3 整合测试

### 实施命令

```bash
cd backend && .venv/bin/python -m pytest tests/test_ci_workflow.py -v
cd backend && .venv/bin/python -m pytest tests/ --tb=line -q
```

### 结果

| 范围 | 修复前 | 修复后 |
|---|---|---|
| `tests/test_ci_workflow.py` | 1 failed / 5 passed | **6 passed** |
| `tests/test_ci_workflow.py + tests/test_check_step.py + tests/test_pre_commit_hook.py` | — | **22 passed** |
| 完整 `tests/` | — | **714 passed, 2 skipped, 4 xfailed, 0 failed** |

### 关键断言对照

| 断言 | 修复前 | 修复后 |
|---|---|---|
| `actions/checkout@v6` in content | 期望 True | 删除（不再断言） |
| `actions/setup-python@v6` in content | 期望 True | 删除 |
| `actions/setup-node@v6` in content | 期望 True | 删除 |
| `permissions:\n  contents: read` in content | True ✅ | True ✅（保留） |
| `actions/checkout@d23441a48...` in content | 未断言 | True ✅（新加） |
| `actions/setup-python@ece7cb06...` in content | 未断言 | True ✅（新加） |
| `actions/setup-node@24997072...` in content | 未断言 | True ✅（新加） |

## L5 staging 运行时验证

R8 防御性验证（手工）：

### 场景 A · workflow YAML 退化到 `@v6`（应该 FAIL）

```bash
# 模拟回滚 R8（手动）：把 ci.yml 中 @d23441a48... 改回 @v6
# 跑测试
pytest tests/test_ci_workflow.py::test_ci_uses_pinned_action_shas_and_read_only_permissions
# 期望：FAIL（@d23441a48... 不在 content 中）
```

修复后测试断言 SHA pin，对未来 R8 退化有保护。

### 场景 B · 三个 SHA 全部出现（PASSED）

`grep "actions/checkout\|actions/setup-python\|actions/setup-node" .github/workflows/*.yml` 实际输出（修复时已 grep 验证）：

```
.github/workflows/ci.yml:29:      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803  # pin SHA (R8)
.github/workflows/ci.yml:30:      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1  # pin SHA (R8)
.github/workflows/ci.yml:61:      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803  # pin SHA (R8)
.github/workflows/ci.yml:62:      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1  # pin SHA (R8)
.github/workflows/ci.yml:99:      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803  # pin SHA (R8)
.github/workflows/ci.yml:100:      - uses: actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38  # pin SHA (R8)
.github/workflows/auto-fix-ci.yml:65:        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803  # R8: pin SHA
.github/workflows/auto-fix-ci.yml:71:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1  # R8
.github/workflows/auto-fix-ci.yml:113:        uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803  # R8
.github/workflows/auto-fix-ci.yml:119:        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1  # R8
```

3 个 SHA 全部出现 6 次 → 测试 3 个 substring 断言全部命中 → 6 passed ✅。

## 结果

✅ **PASS** — 修复与决策 1 方案 A 严格对齐：单文件单函数 ~10 行改动；测试断言 SHA pin 反映 R8 实际；保留 permissions read-only；714/714 整体套件变绿；R8 退化有保护。