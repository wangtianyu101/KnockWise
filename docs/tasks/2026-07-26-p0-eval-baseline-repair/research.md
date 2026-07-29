---
title: P0 调研 · AI Eval 基线 13 个失败
type: research
step: 0
date: 2026-07-26
status: approved
tags: [p0, eval, jsonl, digest, testing]
related: [task.yaml, decisions.md, tasks.md, test-cases.md]
---

# P0 调研 · AI Eval 基线 13 个失败

> 路径模式：`timebox`
> 用户确认：2026-07-26「1」

## 0. 任务理解

本轮只修复后端全量红灯中的 13 个 AI Eval 失败：12 个由同一条非法 JSONL 数据引起，1 个由 Digest prompt-injection fallback 不符合结构化输出契约引起。9 个 Digest API 失败明确留到下一批，不通过删断言或放宽契约凑绿。

## 1. 影响

- **用户影响**：无直接线上数据损坏；Backend CI 无法全绿，Required Checks 无法安全启用。
- **功能影响**：AI Eval 的 6 类 agent 套件被一条非法数据整体阻断；Digest fallback 契约产生假失败。
- **基线命令**：`cd backend && ./.venv/bin/python -m pytest tests/eval tests/test_digest_llm.py -q`
- **基线结果**：`13 failed, 7 passed`。
- **相关文件**：
  - `backend/tests/eval/datasets/interview_eval_v1.jsonl`
  - `backend/tests/eval/conftest.py`
  - `backend/tests/eval/runner.py`
  - `backend/tests/eval/test_*.py`
  - `backend/tests/test_digest_llm.py`

## 2. 临时止血

| 方案 | 时间 | 副作用 | 结论 |
|---|---:|---|---|
| A. xfail/跳过 Eval | 5 min | 形成假绿，失去 Agent 安全契约 | 不采用 |
| B. 修合法 JSON + 保持 fallback 结构化 | 20-40 min | 无业务运行时影响 | 推荐 |
| C. 放宽测试接受非 JSON fallback | 15 min | 破坏 schema_required_fields | 不采用 |

选择 B：`None` 改为 JSON `null`；Digest fallback mock 返回保守但 schema-valid 的 JSON；新增逐行 JSONL 完整性测试。

## 3. 根本原因

1. JSONL 是手写测试数据，缺少逐行语法 Gate，Python `None` 被写进 JSON。
2. `digest_llm` 被 runner 归类为结构化 JSON agent，但注入 fallback mock 返回普通文本。
3. 单条共享 fixture 加载失败，使 12 个测试在业务断言前同时崩溃，错误数量被放大。

### 3.1 关闭条件

- [ ] 107 条 JSONL 每行均可由 `json.loads` 解析。
- [ ] `fmatch-017.expected.matched_branch_index` 解析后为 `None`。
- [ ] Digest 注入 fallback 是合法 JSON，并包含 `summary/category/quality_score`。
- [ ] Eval 专项从 13 failed 收敛为 0 failed。
- [ ] 后端全量失败从 22 降到只剩 Digest API 批次；不宣称全绿。
- [ ] 独立 verifier 对照范围与安全契约 PASS。

## 4. 后续时间盒

- **T+30m**：修复两处确定性根因并加回归。
- **T+2h**：跑 Eval 专项、测试质量与后端全量。
- **T+24h**：将剩余 Digest API 失败保留在 `docs/issues.md`。
- **T+48h**：处理下一批 API 测试/实现漂移。
- **T+72h**：如连续出现 fixture 语法事故，升级为数据集 lint Gate。

## 5. 沟通

- **当前状态**：已确认范围并复现红测，尚未宣布恢复。
- **通报渠道**：当前 Codex 对话。
- **负责人**：Codex 实施与验证；用户 acceptance。

## 6. 安全审查

本任务涉及 LLM/Agent 测试，但不调用真实 LLM、网络、secrets 或高权限操作。

| 攻击场景 | 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|
| 不可信 fixture 注入非法 JSON | 手写 `None`/截断行 | 整套 Eval 拒绝运行 | 🔴 | 逐行解析回归 |
| prompt injection 触发非结构化 fallback | 恶意输入 tag | 下游 schema 失效 | 🔴 | schema-valid 保守 fallback |
| 为追求绿灯放宽断言 | 删除 JSON/schema 要求 | 安全回归失真 | 🔴 | 保持必填字段与注入用例 |
| fixture 意外携带 secrets | 测试数据提交 | 仓库泄露 | 🟡 | 本次仅固定离线文本，无 secrets |

```text
JSONL / prompt 文本（不可信）
        |
        v
离线 mock dispatcher（无网络、无 secrets）
        |
        v
schema + invariant checker（只读） → PASS / FAIL
```

- **权限边界**：仅工作区测试文件读写；无数据库、网络、Action 或生产权限。
- **供应链**：不新增依赖。
- **人工 Gate**：实现后独立 verifier；用户负责 acceptance。

## 7. 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| `null` 改变注入 case 预期 | 🟡 | runner 已显式把 Python `None` 识别为注入 case |
| fallback JSON 内容产生幻觉判定 | 🟡 | 使用输入无关的保守摘要、固定类别、最低质量分 |
| 误把 API 失败混进本批 | 🟡 | 专项命令只含 `tests/eval` + `tests/test_digest_llm.py` |

## 8. 用户决策

| 日期 | 决策项 | 选择 | 状态 | 用户原话 |
|---|---|---|---|---|
| 2026-07-26 | 22 个失败先修哪批 | 先修 13 个 Eval，API 9 个后续 | ✅ 已确认 | 「1」 |

## 自检清单

- [x] 任务理解已由用户选择确认
- [x] 已读 `docs/issues.md`
- [x] 已跑 `git log -10` / `git status`
- [x] 已定位 ≥3 个相关文件
- [x] 已复现红测 `13 failed, 7 passed`
- [x] 已列依赖影响与风险
- [x] 已完成 Agent 安全四道关
