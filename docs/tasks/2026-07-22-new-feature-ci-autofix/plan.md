---
title: Plan · CI 失败自动修复（v2 · 含安全审查）
date: 2026-07-22（v2 修订）
status: v2（待用户验收）
type: plan（技术详细化）
related:
  - [spec.md](spec.md) — 上游 · 10 Requirement + 12 Scenario
  - [research.md](research.md) — 调研 v2（含安全审查）
  - [decisions.md](decisions.md) — 决策主账（10/10 全拍）
---

# Plan · CI 失败自动修复（v2 · 含安全审查）

> 一句话：双 job workflow（diagnostic + apply-fix）+ 双 PR 模式（auto-fix/ 分支 + Draft PR）+ 4 道安全关（不可信输入净化 / 权限分层 / SHA 固定 / env approval）+ label 失败上限 3 次。

---

## 0. 上游引用

- **调研**：[`research.md`](research.md) v2（含 § 5.3 威胁模型 + § 5.4 权限边界 + § 5.5 不可信输入 + § 5.6 外部依赖）
- **规格**：[`spec.md`](spec.md) v2 · 10 Requirement + 12 Scenario + 12 测试场景
- **决策**：[`decisions.md`](decisions.md) v2 · 10/10 全拍
- **关联决策**：1 方案 1+SHA / 2 Draft PR / 3 3 次/commt / 4 job 白名单加固 / 5 外部 check / 6 $20/月 / 7 SHA / 8 双 job / 9 fork 排除 / 10 日志净化

### 0.1 适用性引用

- **product-doc.md 适用性**：✅ 已写（[`product-doc.md`](product-doc.md) v1 · § 4 范围与 § 5 度量直接对应本方案）
- **design-spec.md 适用性**：❌ **不适用**（devops feature 无 UI/UX 设计层）
- **db-design.md / api-spec.md / component-spec.md**：❌ **均不适用**（按 spec.md §5.5 已声明）

---

## 1. 推荐方案

- **推荐**: 方案 A v2 · 双 job + Draft PR + 4 道安全关 + Action pin SHA
- **方案**：**A. 单 workflow + 双 job（diagnostic + apply-fix）+ auto-fix/ 分支 + Draft PR + 4 道关**
- **理由**：
  1. **决策 1-10 全部锁定 v2 路径** —— 用户在 C 改造中已拍板
  2. **决策 8 拆双 job** —— 满足 CLAUDE.md § 6.10 关 2（权限分层）
  3. **决策 7 pin SHA** —— 满足关 3（供应链防御）
  4. **决策 2 Draft PR** —— 满足关 4（人工 gate）
  5. **决策 10 日志净化** —— 满足关 1（不可信输入净化）
  6. **决策 9 fork 排除** —— 补足 fork PR 风险
- **工作量**：~3.5h（含 v2 新增 T15-T20 安全任务）
- **风险**：🟢 低（v2 安全审查已对齐 4 道关 · 9 条风险全部缓解）

---

## 2. 方案对比（≥ 2 个）

### 方案 A v2 · 双 job + Draft PR + 4 道关（推荐 ⭐）

- **思路**：1 个 workflow + 2 个 job（diagnostic + apply-fix）+ 4 道安全关
- **优点**：
  - **安全**：4 道关完整覆盖密钥外发 / 供应链 / prompt injection / 权限提升
  - **透明**：所有 auto-fix 走 Draft PR · 强制人工 review
  - **可控**：env approval + label 失败上限 + fork 排除
- **缺点**：
  - GitHub env approval 需要人工点击（每次 5-30s 延迟）
  - 双 job 比单 job 多 2-3 min 启动延迟
- **风险等级**：🟢 低
- **工作量**：~3.5h
- **兼容性**：✅ 完全兼容现有 CI（不动 `ci.yml`）
- **测试影响**：新增 `scripts/ci/sanitize_ci_log.py` + `scripts/ci/check_auto_fix_diff.py` + `scripts/ci/check_action_sha.py`（3 个脚本 + 单测）

### 方案 B · 拆多 workflow（备选 · 不推荐）

- **思路**：每个 CI job（test-quality / backend-test / frontend-test）一个 auto-fix workflow
- **优点**：失败粒度细
- **缺点**：
  - 3 个 workflow 文件 · 维护成本 3 倍
  - env approval 需配 3 次
  - 失败上限 label 协议在 3 处同步
  - token 烧 3 倍
- **风险等级**：🟡 中
- **工作量**：~4h

### 方案 C · 单 job 单 workflow（v1 旧方案 · 不推荐）

- **思路**：v1 旧方案，单 job 含 secrets + checkout + push
- **优点**：实现快
- **缺点**：
  - ❌ 违背 CLAUDE.md § 6.10 关 2（密钥外发）
  - ❌ 违背 GitHub Secure Use 准则
  - ❌ 已废除（v2 安全审查否决）

> **结论**：选 A v2 · B 不实用 · C 是反模式

---

## 3. 风险评估（v2 · 含安全审查）

| # | 风险 | 等级 | 缓解（v2 决策对齐） |
|---|---|---|---|
| 1 | **密钥外发** | 🔴 | 决策 8 双 job + 决策 2 Draft PR + env approval |
| 2 | **Fork PR 非可信代码** | 🔴 | 决策 9 fork 排除 |
| 3 | **供应链攻击** | 🔴 | 决策 7 Action pin SHA |
| 4 | **Prompt injection** | 🔴 | 决策 10 日志净化 |
| 5 | **死循环** | 🔴 | 决策 3 label 计数 3 次上限 |
| 6 | **绕过 § 6.1 单测规则** | 🟡 | 决策 5 外部 check · 移除 self-attestation |
| 7 | **业务 service 被改** | 🟡 | 决策 4 backend service 必走 Draft PR |
| 8 | **Token 烧** | 🟡 | max-turns 25 · $20/月 Console 限 |
| 9 | **环境审批被绕过** | 🟡 | GitHub 原生 env approval · required reviewers |
| 10 | **GitHub Actions runner 网络抖动** | 🟢 | retry 2 次 |

---

## 4. 决策点（10 个 · 全部锁定 v2）

| # | 决策 | 选择 | 落地位置 |
|---|---|---|---|
| D1 | workflow 结构 | **双 job（diagnostic + apply-fix）** | `.github/workflows/auto-fix-ci.yml` |
| D2 | 输出模式 | **Draft PR** | `auto-fix-ci.yml` apply-fix job |
| D3 | 失败上限实现 | **label 计数 3 次** | workflow step |
| D4 | 单测规则协同 | **外部 check**（T33 + pytest） | apply-fix 跑测试 |
| D5 | Claude 模型 | `claude-sonnet-4-5` | workflow env |
| D6 | max-turns | 25 | workflow env |
| D7 | main 分支处理 | skip + comment | workflow `if:` |
| D8 | backend service 改动 | **必走 Draft PR**（不允许直接 push） | `scripts/ci/check_auto_fix_diff.py` |
| D9 | 第三方 Action | **完整 40 字符 SHA** | workflow `uses:` + `scripts/ci/check_action_sha.py` |
| D10 | 日志净化 | 仅 job 名 + 错误类型 + 截断字符串 | `scripts/ci/sanitize_ci_log.py` |
| D11 | Fork PR 排除 | `if: head_repository.fork == false` | workflow `if:` |
| D12 | env approval | `environment: auto-fix-approval` | GitHub Settings + workflow |

---

## 5. 任务拆分建议（≤ 1h 原子任务 · T1-T20 · 含 v2 新增 T15-T20）

### v1 任务（T1-T14 · 保留 + 部分修订）

| ID | 任务 | 估时 | 验证 |
|---|---|---:|---|
| **T1** | workflow 双 job 骨架（diagnostic + apply-fix） | 20 min | YAML 校验 + `act --dryrun` |
| **T2** | label check step（3 次上限 · v2 修订） | 15 min | e2e |
| **T3** | diff 校验脚本（含 NEEDS_REVIEW 检测） | 25 min | 单测 6 case |
| **T4** | diagnostic job · Claude step（日志净化输入） | 20 min | YAML + e2e |
| **T5** | apply-fix job · patch 应用 + 跑 pytest | 15 min | e2e S7 |
| **T6** | Draft PR 创建 + needs-review label（S6） | 20 min | e2e S6 |
| **T7** | 错误处理（5xx retry + comment） | 15 min | e2e |
| **T8** | fork PR 排除 if（R7） | 10 min | e2e S9 |
| **T9** | diff 校验脚本单测（TDD 6 case） | 20 min | pytest |
| **T10** | e2e 脚本（act · 6 scenarios） | 25 min | act 本地 |
| **T11** | README "如何关闭 auto-fix" 段 | 10 min | review |
| **T12** | local-dev.md 链接 | 5 min | review |
| **T13** | 手动触发 workflow 真实验证 | 20 min | 真实 CI |
| **T14** | 写 verify.md（含安全验证段） | 25 min | 5 步产物 |

### 🆕 v2 新增安全任务（T15-T20）

| ID | 任务 | 估时 | 验证 | 对应决策 |
|---|---|---:|---|---|
| **T15** | 日志净化脚本 `sanitize_ci_log.py` | 25 min | 单测 6 case | 决策 10 / R9 |
| **T16** | 日志净化单测 `test_sanitize_ci_log.py`（TDD） | 20 min | pytest | 决策 10 |
| **T17** | Action SHA 校验脚本 `check_action_sha.py` | 20 min | 单测 4 case | 决策 7 / R8 |
| **T18** | Action SHA 校验单测 `test_check_action_sha.py`（TDD） | 15 min | pytest | 决策 7 |
| **T19** | 配置 GitHub environment `auto-fix-approval` | 10 min | manual + UI 截图 | 决策 8 / R10 |
| **T20** | 安全验证 e2e（S9 fork / S10 注入 / S11 SHA / S12 env approval） | 30 min | act + 真 CI | R7/R8/R9/R10 |

**总估时**：~5h（v1 3.5h + v2 新增 ~2h）

---

## 6. 路径建议

```
0 调研 v2（含安全审查 · research.md） ✅
  ↓
1 规格 v2（10 Requirement + 12 Scenario · spec.md） ✅
  ↓
2 计划 v2（双 job + T15-T20 安全任务 · plan.md） ✅
  ↓
3 拆分 v2（T1-T20 原子任务 · tasks.md） ⏳ 下一步
  ↓
4 实施（TDD + writer/verifier 双 agent · 6.7 规则）
  ↓
5 验证（L3 + L5 + 安全验证段 · verify.md）
  ↓
6 复盘（retro.md · 含 v1 → v2 调研偏差）
```

---

## 7. 关键技术细节（v2 双 job + 4 道关）

### 7.1 双 job workflow_run 触发结构

```yaml
# .github/workflows/auto-fix-ci.yml
name: auto-fix-ci
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches-ignore: [main]    # R5

env:
  MAX_FIX_ATTEMPTS: "3"       # R2 (v2: 3 instead of 2)
  MODEL: "claude-sonnet-4-5"
  MAX_TURNS: "25"
  # R7: Action SHA 在 each `uses:` 处单独 pin

jobs:
  # === Job 1: diagnostic (read-only, no secrets in workflow-level env) ===
  diagnostic:
    name: Diagnostic (read-only)
    if: |
      github.event.workflow_run.conclusion == 'failure' &&
      github.event.workflow_run.head_repository.fork == false    # R7
    runs-on: ubuntu-latest
    permissions:
      contents: read                                              # R10: 只读
    steps:
      - uses: actions/checkout@a1b2c3d4...                        # R8: pin SHA
      - name: Sanitize CI log
        id: sanitize
        run: python scripts/ci/sanitize_ci_log.py                  # R9
      - name: Generate patch via Claude
        uses: anthropics/claude-code-action@<40-char-sha>          # R8
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}     # secrets 仅在此 job
          claude_args: --max-turns 25 --model claude-sonnet-4-5
          prompt: |
            CI 失败 job: ${{ steps.sanitize.outputs.failed_job }}
            错误类型: ${{ steps.sanitize.outputs.error_code }}
            关键字符串（前 200 字符）: ${{ steps.sanitize.outputs.key_string }}
            请生成 patch（diff 格式）并通过 Write 工具上传 artifact。
            不接收原始 CI 日志 / PR 标题 / commit msg。
        env:
          SANITIZED_SUMMARY: ${{ steps.sanitize.outputs.summary }}
      - name: Upload patch artifact
        uses: actions/upload-artifact@<40-char-sha>
        with:
          name: auto-fix-patch
          path: patch.diff

  # === Job 2: apply-fix (write, env approval required) ===
  apply-fix:
    name: Apply fix (write, env approval)
    needs: diagnostic
    if: github.event.workflow_run.head_repository.fork == false   # R7 (double check)
    runs-on: ubuntu-latest
    environment: auto-fix-approval                                 # R10: env approval
    permissions:
      contents: write                                              # R10: write
      pull-requests: write
    steps:
      - uses: actions/checkout@<40-char-sha>
      - name: Check label count
        id: label-check
        run: |
          SHORT_SHA="${HEAD_SHA:0:7}"
          LABEL="auto-fix-count-$SHORT_SHA"
          COUNT=$(gh api repos/$REPO/labels/$LABEL --jq '.description' 2>/dev/null || echo "0")
          if [ "$COUNT" -ge "3" ]; then                            # R2: 3 (v2)
            echo "::error::auto-fix limit reached ($COUNT/3)"
            gh issue create --title "Manual fix needed: $SHORT_SHA" --body "..."
            exit 0
          fi
      - name: Download patch artifact
        uses: actions/download-artifact@<40-char-sha>
        with:
          name: auto-fix-patch
      - name: Create auto-fix branch
        run: |
          NEW_BRANCH="auto-fix/${HEAD_BRANCH##*/}-${HEAD_SHA:0:7}"
          git checkout -b "$NEW_BRANCH"
      - name: Apply patch
        run: git apply patch.diff
      - name: Check NEEDS_REVIEW
        id: needs-review-check
        run: python scripts/ci/check_auto_fix_diff.py              # R4 + R3
      - name: Run T33 + pytest (must pass)
        run: |
          python scripts/check_test_quality.py backend/tests        # R3
          cd backend && python -m pytest tests/ -q                   # R3
      - name: Commit and push
        if: success()
        run: |
          git add -A
          git commit -m "auto-fix(<scope>): <description>"
          git push origin "auto-fix/${HEAD_BRANCH##*/}-${HEAD_SHA:0:7}"
      - name: Open Draft PR
        if: success()
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          LABELS="auto-fix"
          if [ "${{ steps.needs-review-check.outputs.needs_review }}" = "true" ]; then
            LABELS="$LABELS,needs-review"                            # R4
          fi
          gh pr create \
            --base "$HEAD_BRANCH" \
            --head "auto-fix/${HEAD_BRANCH##*/}-${HEAD_SHA:0:7}" \
            --draft \
            --label "$LABELS" \
            --title "auto-fix: <description>" \
            --body "Draft auto-fix for $HEAD_SHA. Review required."
      - name: Update label count
        if: success()
        run: |
          SHORT_SHA="${HEAD_SHA:0:7}"
          gh api repos/$REPO/labels/auto-fix-count-$SHORT_SHA \
            -X PATCH -f description="$((COUNT + 1))"
```

### 7.2 日志净化脚本（决策 10 / R9）

```python
# scripts/ci/sanitize_ci_log.py
"""Sanitize CI log before passing to Claude."""
import json, re, sys

FAILED_JOB_PATTERN = re.compile(r"##\[error\](\w+)")
ERROR_CODE_PATTERN = re.compile(r"\b(TypeScriptError|CoverageBelowThreshold|PlaceholderViolation|PytestFailure)\b")
MAX_KEY_LEN = 200

def sanitize(raw_log: str) -> dict:
    # 1. 提取失败 job 名（白名单）
    jobs = FAILED_JOB_PATTERN.findall(raw_log)
    failed_job = jobs[0] if jobs else "unknown"
    # 2. 提取错误类型（白名单）
    codes = ERROR_CODE_PATTERN.findall(raw_log)
    error_code = codes[0] if codes else "UnknownError"
    # 3. 截断关键字符串（前 200 字符）
    key_string = raw_log[:MAX_KEY_LEN]
    return {
        "failed_job": failed_job,
        "error_code": error_code,
        "key_string": key_string,
        # 注意：不返回 raw_log / pr_title / commit_msg
    }

if __name__ == "__main__":
    raw = sys.stdin.read()
    print(json.dumps(sanitize(raw)))
```

### 7.3 Action SHA 校验脚本（决策 7 / R8）

```python
# scripts/ci/check_action_sha.py
"""Reject moving tags (@beta, @main, @v1) in workflow YAMLs."""
import re, sys, yaml
from pathlib import Path

MOVING_TAGS = {"beta", "main", "master", "v1", "v2", "v3", "latest"}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

def check(workflow_path: Path) -> list[str]:
    violations = []
    with open(workflow_path) as f:
        content = f.read()
        # YAML 加载
        wf = yaml.safe_load(content)
    # 递归查找所有 uses:
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "uses" and isinstance(v, str):
                    ref = v.split("@")[-1]
                    if ref in MOVING_TAGS or not SHA_PATTERN.match(ref):
                        violations.append(f"{path}.uses = {v}")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
    walk(wf)
    return violations

if __name__ == "__main__":
    workflow_dir = Path(".github/workflows")
    all_violations = []
    for wf in workflow_dir.glob("*.yml"):
        all_violations.extend(check(wf))
    if all_violations:
        print("❌ Moving tag / invalid SHA found:")
        for v in all_violations:
            print(f"  - {v}")
        sys.exit(1)
    print("✅ All third-party Actions pinned to full SHA")
```

### 7.4 diff 校验脚本（决策 4 + 5）

```python
# scripts/ci/check_auto_fix_diff.py
"""Detect service file changes for NEEDS_REVIEW + verify no self-attestation."""
import sys, subprocess

DIFF = subprocess.check_output(["git", "diff", "HEAD~1", "--name-only"]).decode().splitlines()
COMMIT_MSG = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode()

SERVICE_FILES = [f for f in DIFF if f.startswith("backend/services/")]
TEST_FILES = [f for f in DIFF if "test_" in f and f.endswith(".py")]

needs_review = bool(SERVICE_FILES)

# R3: 不允许 [NO-TEST-NEEDED] 自我豁免
if "[NO-TEST-NEEDED]" in COMMIT_MSG:
    print("::error::[NO-TEST-NEEDED] self-attestation not allowed (decision 5)")
    sys.exit(1)

# 输出供 workflow 使用
print(f"needs_review={str(needs_review).lower()}")
print(f"service_files={','.join(SERVICE_FILES)}")
print(f"test_files={','.join(TEST_FILES)}")

if not TEST_FILES and not SERVICE_FILES:
    print("::warning::no test files in diff (R3: pytest will catch real failures)")
```

---

## 8. 测试架构（v2 含安全验证）

### 8.1 单元测试（pytest）

| 文件 | case 数 |
|---|---:|
| `scripts/ci/test_sanitize_ci_log.py` | 6 |
| `scripts/ci/test_check_auto_fix_diff.py` | 6 |
| `scripts/ci/test_check_action_sha.py` | 4 |

### 8.2 e2e 测试（act + 真 CI）

- `scripts/ci/test_auto_fix_e2e.sh`：
  - T10: S1-S8 通用场景
  - T20: S9 fork / S10 注入 / S11 SHA / S12 env approval（安全场景）

### 8.3 真实 CI 触发（staging）

- T13 + T20：手动在 test PR 验证
- 必须包含恶意 log string 测试（验证 R9 净化有效）

---

## 9. 元信息

- **是否需要外部评审**：是（10 项决策 + 4 道安全关 · 需用户最终验收）
- **是否涉及 schema 变更**：否
- **是否需要 AB 测试**：否
- **下游产物**：tasks.md（3 步 · T1-T20 拆分）→ 4 步 TDD 实施

---

## 10. 下一步

1. ⏸ **用户验收本 plan.md**（特别是 § 5 T15-T20 安全任务 + § 7 双 job YAML 模板）
2. ✅ 验收后 → 进 3 步写 tasks.md（T1-T20 完整化）
3. 3 步后 → 4 步 TDD 实施

---

## 硬性 DOD（plan.md v2 完成必须全过）

- [x] 5 段齐全
- [x] 方案对比 ≥ 2 个（3 个 · A v2 推荐 + B 备选 + C 反模式）
- [x] 风险评估 ≥ 3 条（10 条 · 含 4 个 🔴 安全风险）
- [x] 决策点 ≥ 1（12 个 D1-D12 · 全部锁定 v2）
- [x] 任务拆分 ≤ 1h 原子任务（T1-T20 · 含 v2 新增 6 个安全任务）
- [x] 路径建议完整
- [x] §0 上游引用齐全
- [x] 适用性引用齐全（product-doc + design-spec）
- [ ] ⏸ 用户验收