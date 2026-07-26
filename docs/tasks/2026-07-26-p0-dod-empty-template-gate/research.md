---
title: P0 调研 · 空模板被 DOD checker 判绿
type: research
step: 0
date: 2026-07-26
status: approved
tags: [p0, governance, dod, template-gate]
related: [task.yaml, decisions.md, tasks.md]
---

# P0 调研 · 空模板被 DOD checker 判绿

> 路径模式：`timebox`
> 用户确认：2026-07-26「P0-2：空模板可以被判定为 DOD 通过 我们直接来解决这个问题吧」

## 0. 任务理解

修复 `scripts/check-step.py` 的内容假绿：文档只有模板说明、示例、占位符和未完成 DOD checklist 时，不得被判定为完成；合法且包含真实内容的文档仍应通过。范围只含 checker、回归测试和治理主账，不顺带处理此前暂停的 AI Eval 或 Digest API 失败。

## 1. 影响

- **实测基线**：原样运行模板时，`spec-template.md`、`tasks-template.md`、`test-cases-template.md`、`verify-template.md`、`retro-template.md` 均返回 0。
- **受影响对象**：本地 pre-commit、CI workflow governance job、所有由 AI 生成的 0-6 步任务文档。
- **影响性质**：机器 Gate 假绿，可能把只有结构、没有证据的文档推进到下一阶段；不涉及业务数据。
- **现状证据**：已读 `docs/issues.md`；已跑 `git log -10` 和 `git status`；当前 worktree 有 P0-1 与 Eval 的未提交改动，本任务不覆盖。
- **相关文件**：
  - `scripts/check-step.py`
  - `backend/tests/test_check_step.py`
  - `docs/templates/spec-template.md`
  - `docs/templates/test-cases-template.md`
  - `scripts/pre-commit`
  - `scripts/check-governance.py`

## 2. 临时止血

| 方案 | 时间 | 优点 | 缺点 | 结论 |
|---|---:|---|---|---|
| A. 仅拒绝 `docs/templates/` 路径 | 10 min | 改动最小 | 复制到 task 目录即可绕过 | 不采用 |
| B. 共享模板残留 Gate | 30-45 min | 能阻断原模板及复制空壳；规则集中 | 需设计误伤边界 | **采用** |
| C. 每阶段完整 Markdown AST/schema | 3-6 h | 最严格 | 超出 P0，兼容成本高 | 后续 P1 |

**止血选择**：方案 B。先做通用内容前置检查，再保留现有阶段 DOD checker；不把自然语言质量交给启发式评分。

## 3. 根本原因

1. 当前 checker 只统计标题、关键词、TC 编号和 PASS 字样，模板内的说明与示例本身即可满足正则。
2. `check_verify()` 对 `PASSED / FAILED` 使用子串匹配，因此模板里的候选值被误当作真实结果。
3. 各阶段没有共同的“仍是模板 / 仍为 draft / 仍有高置信度占位”前置 Gate。
4. 既有测试只覆盖合法短文档和字段格式兼容，没有把仓库真实模板当成负例。

### 3.1 依赖影响

```text
docs/templates/*.md / task 文档（不可信输入）
                   ↓
          scripts/check-step.py
             ↙             ↘
scripts/pre-commit      scripts/check-governance.py
             ↘             ↙
               commit / CI Gate
```

- 改 `check-step.py` 会同时影响本地 Hook 与 CI，无需修改两条调用链。
- 新 Gate 必须兼容合法技术符号：React `<Component>`、路径 `<id>`、性能比较 `< 200ms`。
- 历史未完成文档可能从假绿变为红灯，这是预期显形，不自动篡改历史文档。

## 4. 后续时间盒

- **T+30m**：补原模板和复制模板负例，确认 RED。
- **T+2h**：实现共享 Gate，专项测试和实际 CLI 全绿。
- **T+24h**：将结果同步 `docs/issues.md`，记录历史假绿边界。
- **T+48h**：若误伤率不可接受，再评估 Markdown AST 方案。
- **T+72h**：在一次真实 staged 文档变更上验证 Hook 阻断。

## 5. 沟通

- **当前状态**：已复现 5 个原样模板假绿，进入 TDD。
- **负责人**：Codex 实施；独立 verifier 复验；用户验收。
- **范围外**：AI Eval 未提交修复、Digest API 失败、GitHub Ruleset 外部配置。

## 6. 安全审查

已阅读 GitHub Actions Secure use 与 OWASP LLM Prompt Injection 指引。任务文档与 AI 产物均视为不可信输入。

### 6.1 威胁模型

| 场景 | 攻击者能力 / 向量 | 影响 | 等级 | 缓解 |
|---|---|---|---|---|
| 关键词填充绕过 | 提交者复制模板，保留 PASS/TC/标题 | 假绿进入下一阶段 | 🔴 | 模板身份 + 占位残留前置 Gate |
| 正常技术文本被误伤 | 文档包含 `<Component>`、`<id>`、`< 200ms` | 合法提交被阻断 | 🟡 | 只匹配高置信度填空语义并加边界测试 |
| 文档内容触发执行 | 恶意文档嵌入 shell/Markdown | 命令执行或泄密 | 🔴 | checker 只读文本，不 eval、不 shell 插值 |
| CI 权限扩大 | 为修 checker 新增 secrets/write | 供应链风险 | 🔴 | 不改 workflow 权限，不新增依赖和 Action |

### 6.2 权限边界

```text
task Markdown（不可信）
        │ 只读文本
        ▼
check-step.py（无网络 / 无 secrets / 无写权限）
        │ exit code + 固定错误摘要
        ├── local Hook
        └── CI read-only governance job
```

- **外部依赖**：无新增依赖、无新增 Action、无移动 tag。
- **不可信输入**：Markdown 正文与 frontmatter；只做长度受限的正则检测，不执行其中命令。
- **人工 Gate**：用户仍负责阶段验收；机器 Gate 只负责阻断明显空壳。

## 7. 风险

| 风险 | 等级 | 缓解方案 |
|---|---|---|
| 通用 `<...>` 正则误伤 JSX/路径/比较符 | 🔴 | 禁止宽泛匹配；增加合法技术文本回归 |
| 只按路径拦截可被复制绕过 | 🔴 | 检查内容中的模板身份、draft 与高置信度残留 |
| 规则分散到 7 个 checker 后漂移 | 🟡 | 单一共享前置函数，由 CLI 统一调用 |
| 历史文档暴露为未完成 | 🟢 | 如实 FAILED；不自动回填或伪造证据 |

## 8. 决策

| 日期 | 决策项 | 选择 | 状态 | 用户原话 | 关联 |
|---|---|---|---|---|---|
| 2026-07-26 | P0-2 修复范围 | 共享模板残留 Gate + 真实模板负例 + 合法边界回归 | ✅ 已确认 | 「我们直接来解决这个问题吧」 | [decisions.md](decisions.md) |

### 8.1 关闭条件

- [x] 仓库 7 类步骤模板运行对应 checker 均非零（10 个实际模板 rc=1）。
- [x] 复制并改名的空模板仍非零。
- [x] 合法文档与 JSX/路径/比较符边界保持通过。
- [x] `backend/tests/test_check_step.py` 全绿且测试质量 0 violations。
- [x] 独立 verifier 对照本文复验 PASS。
