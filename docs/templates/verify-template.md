---
title: 验证文档模板（verify）
date: 2026-06-30
status: v1
tags: [verify, 5步, 验证, 5层gate, 模板]
related:
  - [test-cases-template.md](test-cases-template.md) — 上游
  - [tasks-template.md](tasks-template.md) — 上游
---

# 验证文档模板（verify.md）

> **一句话**：5 层 gate 全过才进 6 步发布——**多层证据证明 task 真的完成**。
>
> **产出时机**：5 步验证阶段（所有实现后必填）。
>
> **作者**：**AI 主导**（人 review L4）。
>
> **对应 DOD**：见 `docs/DOD.md` §七（5 层 gate 各 1 条）。

---

## L1 类型检查（必填）

```markdown
- [ ] tsc / mypy 0 error
- **命令**: `cd backend && ./.venv/bin/python -m mypy services/`
- **结果**: PASSED ✅
- **耗时**: <X 秒
```

**工具**：TypeScript（tsc）/ Python（mypy）

---

## L2 单元测试（必填）

```markdown
- [ ] pytest 全部通过
- [ ] 覆盖率 ≥ 80%
- **命令**: `cd backend && ./.venv/bin/python -m pytest tests/ --cov=services --cov-report=term-missing`
- **结果**:
  - passed: <X>
  - failed: 0
  - 覆盖率: <Y>%
- **耗时**: <Z> 秒
```

**覆盖率要求**（见 CLAUDE.md §1.8）：
- 核心 service ≥ 80%
- 非核心 service 不强制

---

## L3 集成测试（必填）

```markdown
- [ ] E2E / API contract 通过
- **命令**: `cd backend && ./.venv/bin/python -m pytest tests/integration`
- **结果**:
  - passed: <X>
  - failed: 0
- **耗时**: <Y> 秒
```

**测试范围**：
- API contract（端到端调用）
- 数据库事务
- 外部依赖（mock）

---

## L4 代码审查（必填）

```markdown
- [ ] human review diff 完成
- **审查人**: <姓名>
- **审查日期**: YYYY-MM-DD
- **审查范围**:
  - <commit 1>: <摘要>
  - <commit 2>: <摘要>
- **结论**: ✅ 通过 / ⚠️ 建议修改 / ❌ 拒绝
- **关键反馈**:
  - <反馈 1>
  - <反馈 2>
```

**审查 checklist**：
- [ ] 代码符合 spec.md
- [ ] 命名清晰
- [ ] 测试覆盖
- [ ] 无明显 bug
- [ ] 边界 case 处理

---

## L5 运行时验证（必填）

```markdown
- [ ] staging 跑通
- [ ] 截图 / 日志存档
- **环境**: staging / pre-prod
- **验证人**: <姓名>
- **验证日期**: YYYY-MM-DD

### 验证场景
1. 场景 1: <描述>
   - 步骤: 1. ... 2. ...
   - 期望: <应该看到>
   - 实际: <实际看到>
   - 截图: <路径或链接>

2. 场景 2: ...
```

---

## 🎯 硬性 DOD（verify.md 5 层 gate 全过）

- [ ] **L1 类型检查**：tsc / mypy 0 error
- [ ] **L2 单元测试**：pytest 通过 + 覆盖率 ≥ 80%
- [ ] **L3 集成测试**：E2E / API contract 通过
- [ ] **L4 代码审查**：human review 完成
- [ ] **L5 运行时验证**：staging 跑通

> ⚠️ 任何 1 层没过 → verify.md 不算完成，不能进 6 步发布
> ⚠️ 工具校验：`python3 scripts/check-step.py verify <file>`

---

## 📚 相关文档

- [test-cases-template.md](test-cases-template.md) — 上游：测试用例
- [tasks-template.md](tasks-template.md) — 上游：任务拆分
- `docs/DOD.md` §七 — 5 步验证 DOD 完整定义