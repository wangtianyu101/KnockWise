---
title: pre-commit 把 docs/issues.md 误判为 product-doc · 调研
type: research
step: 0
date: 2026-07-29
status: approved
tags: [refactor, governance, pre-commit, hook, regression]
related: [task.yaml, decisions.md, ../../issues.md]
---

# pre-commit 把 docs/issues.md 误判为 product-doc · 调研

## 1. 任务理解

**用户原话**：「A — 修改 pre-commit 第 220 行 regex 把 docs/issues.md 从 product-doc 列表移除」（承接债务 24 收尾的 commit 拦截）

**复述**：`scripts/pre-commit` 第 220 行 grep regex 把 `docs/issues.md` 列入 product-doc 检查清单，导致任何对议题主账的合法修改都会因 check-product-doc.py 的 frontmatter 校验失败而被阻断。修复 = 把 `docs/issues.md` 从该 regex 移除（边界缩小），并加回归测试守住。

## 2. 根因（已确认）

### 2.1 regex 误分类

**位置**：`scripts/pre-commit:220`

```sh
product_doc_files=$(echo "$staged_files" | grep -E "^(docs/templates/product-doc-template\.md|docs/tasks/.+/product-doc\.md|docs/issues\.md)$" || true)
```

| 路径 | 实际文档类型 | 应走校验 |
|---|---|---|
| `docs/templates/product-doc-template.md` | product-doc 模板 | `check-product-doc.py` |
| `docs/tasks/<date>-*/product-doc.md` | 各任务 product-doc 实例 | `check-product-doc.py` |
| `docs/issues.md` | **议题主账**（按 `AGENTS.md` § 0.5 + § 6.9 + `templates/issue-closure-template.md`）| **无 frontmatter/§ 4 MVP/§ 5 成功指标要求** |

`docs/issues.md` 不属于 product-doc 范畴，但被列入同一 regex，导致任何合法修改都被误判。

### 2.2 触发后果（本次复现）

- 修改 `docs/issues.md` → git add → git commit
- pre-commit 跑 check-product-doc.py 校验 → exit 1（缺 frontmatter / 缺 § 4 / 缺 § 5）
- 输出 7 条 violation，禁止 commit

### 2.3 历史追溯

`docs/issues.md` 由 T17-T18 期间被加入到 product-doc 列表（推测来自债务 19/20 的 spec 落地：把所有议题主账文档统一走同一治理）。但产品文档与议题主账语义不同，应分离。

## 3. 影响与依赖

### 3.1 直接影响

- ✅ **修复后**：docs/issues.md 可正常 commit（包括债务 24 ✅ 状态同步 + 债务 23 用户授权的 🔴 → 🟠 变更）
- 🟢 **真 product-doc 仍受保护**：`docs/templates/product-doc-template.md` 和 `docs/tasks/<date>-*/product-doc.md` 仍走 check-product-doc.py 校验

### 3.2 依赖文件

- `scripts/pre-commit`（改）
- `backend/tests/test_pre_commit_hook.py`（加回归测试）
- `docs/issues.md`（commit 落地债务 24/23 状态变更）

### 3.3 反向影响

- 不修改 `scripts/check-product-doc.py`（保持其产品文档校验语义）
- 不修改 `docs/issues.md` 的议题主账结构
- 不引入新测试框架

## 4. 风险与缓解

| 风险 | 等级 | 缓解 |
|---|---|---|
| regex 改错导致真 product-doc 漏过 | 🟢 | 缩窄（移除 `docs/issues.md`），其他两条保持 |
| pre-commit 行为变更影响其他工作流 | 🟡 | 跑真实 `git commit` + `git add docs/issues.md` 端到端验证 |
| 回归测试覆盖不足 | 🟡 | 用 `subprocess.run(["sh", ...])` 跑真实 pre-commit + 临时 git repo，覆盖 4 场景 |
| 工作区其他 ?? 目录误触发 | 🟢 | 不在 commit 范围，git add 限定 3 文件 |

## 5. 安全审查（涉及 CI/CD · § 0.2.1 必做）

### 5.1 官方文档

- [GitHub · pre-commit hooks 规范](https://pre-commit.com/)（按 .git/hooks/* + scripts/pre-commit 实现）
- POSIX `sh` + `grep -E` 正则语义

### 5.2 威胁模型

| 场景 | 攻击向量 | 影响 | 缓解 |
|---|---|---|---|
| T1 | 攻击者让 `docs/issues.md` 修改绕过 product-doc 校验 | 实质上是议题主账，不应被 product-doc 拦；本修复**正中预期行为** | 缩窄 regex |
| T2 | 攻击者改 regex 让自己写的真 product-doc 漏过 | 本任务不改其他两条 regex，攻击面不扩大 | review 边界 |
| T3 | 攻击者伪造 docs/issues.md 路径（如 `docs/issues.md.bak`） | 不影响：grep regex 是 `^...$` 严格匹配 | 已严格 |

### 5.3 权限边界

```text
developer local git commit
   ↓
scripts/pre-commit（developer 本地，无 secrets）
   ↓
边界缩窄：docs/issues.md 不再走 check-product-doc.py
   ↓
commit 落地
```

**降权而非升权**：本次修复 = 把不应被拦的文档从误分类中移除，**不引入新的执行路径**。

### 5.4 不可信输入

| 输入 | 当前 | 本任务策略 |
|---|---|---|
| `staged_files`（git diff 输出） | 不可信 | 保持原 regex 严格匹配 |
| regex 修改本身 | 静态字符串 | review + 回归测试覆盖 |

## 6. 方案与推荐

### 6.1 方案 A：缩窄 regex（用户决策）

```sh
# Before
product_doc_files=$(echo "$staged_files" | grep -E "^(docs/templates/product-doc-template\.md|docs/tasks/.+/product-doc\.md|docs/issues\.md)$" || true)

# After
product_doc_files=$(echo "$staged_files" | grep -E "^(docs/templates/product-doc-template\.md|docs/tasks/.+/product-doc\.md)$" || true)
```

**优点**：边界明确缩小，真 product-doc 仍受保护。
**风险**：无新增面。
**推荐**：✅

### 6.2 方案 B：给 docs/issues.md 加 frontmatter hack（已拒绝）

按用户决策不采纳。

### 6.3 方案 C：改 check-product-doc.py 加 bypass

不推荐——改 checker 语义，超出本任务 scope。

## 7. 路径建议

`refactor-6`：0（当前）→ 1-3 合并（单行改动 + 1 回归测试）→ 4 实施 → 5 验证 → 6 复盘。

## 8. 用户决策

| 日期 | 决策项 | 选择 | 用户原话 |
|---|---|---|---|
| 2026-07-29 | 路径 | A：缩窄 regex | 「A」 |

## 9. 自检

- [x] 任务理解已复述
- [x] 读 docs/issues.md（议题主账职责）
- [x] git log -10（最近 pre-commit 治理由 P0-1/P0-2/P0-3 修复）
- [x] git status（3 文件 unstaged + 9 个 ??）
- [x] 找到 3 个相关文件（pre-commit / test_pre_commit_hook.py / docs/issues.md）
- [x] 依赖影响列出
- [x] 风险分级 + 缓解
- [x] § 0.2.1 安全审查（CI/CD 必做）· 4 道关全部对齐