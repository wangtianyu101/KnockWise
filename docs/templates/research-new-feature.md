# 调研模板 · 新功能

> 触发词：`调研 新功能：<topic>` 或 `调研 设计：<topic>` 或 `调研 feature：<topic>`
> 时间预算：30-60 min
> 必填段：1, 2, 3, 4, 5（全部必填）

---

# 🔍 调研报告 · 新功能：<名字>

> 日期：YYYY-MM-DD · 调研人：<AI 名>

## 1. 任务理解（必填）

- **用户原话**: "<原话>"
- **AI 复述**: <用自己的话讲要做啥，1-2 句；如果复述不对，立刻停下等用户确认>
- **涉及模块**: [interview / learn / qa / news / obsidian / ai-push / ...]
- **估时**: ~Xh（后端 / 前端 / 测试 分开估）

## 2. 现状扫描（必填）

### 2.1 相关文件
- `backend/api/<...>.py` — <作用>
- `backend/services/<...>.py` — <作用>
- `frontend/pages/<...>.tsx` — <作用>
- `frontend/components/<...>.tsx` — <作用>

### 2.2 相关议題（来自 `docs/40-追踪/目前缺陷.md`）
- [A-1, F-3 ...]（无则写"无"）
- 如议題沉积超过 30 天未推进 → 标注 ⚠️

### 2.3 最近相关改动
```bash
git log --oneline -10 -- <相关路径>
```
- commit `abc1234`: <摘要>（日期）
- commit `def5678`: <摘要>（日期）

### 2.4 类似功能怎么实现的（必填，找 1-2 个）
- **参考 A**: `<已有功能>` — 用了什么模式 / 组件 / endpoint
- **参考 B**: `<已有功能>` — 用了什么模式 / 组件 / endpoint

## 3. 依赖发现（必填）

### 3.1 改这些文件会影响
- `<file>`: <影响什么>
- `<test>`: <影响什么>

### 3.2 需要先改的
- `<file>`: <为什么>
- `<migration>`: <为什么>

### 3.3 调用方清单（改之前必查）
- `<file>:line` — <怎么调用>
- `<file>:line` — <怎么调用>

## 4. 风险评估（必填）

| 风险 | 等级 | 缓解 |
|---|---|---|
| 已有未提交改动（`git status`） | 🟡/🔴 | 确认是不是冲突，协调其他 session |
| 类似功能已有但不一致 | 🟡 | 决定是统一还是并存 |
| 涉及 schema 变更 | 🔴 | 必走迁移流程 + 备份 |
| 涉及多个 agent / branch | 🟡 | 强调研 + 走 1.7 分支 |
| 议題沉积影响判断 | 🟡 | 必读 `目前缺陷.md` |
| 估时偏差 > 50% | 🟡 | 拆更小的 task |

## 5. 输出建议（必填）

### 5.1 推荐路径
```
0 调研（本步完成）
→ 1 规格（spec.md · 三脑交汇）
→ 2 计划（plan.md + db/api/component spec）
→ 3 拆分（tasks.md · ≤ 1h 原子任务）
→ 4 实现（TDD 循环 · 红→绿→refactor）
→ 5 验证（L3 整合 + L5 staging）
→ 6 复盘（retro.md）
```

> ⚠️ v2 变更（2026-07-02）：砍掉原"6 发布"（灰度 + 监控 + 回滚）—— PR/commit 即交付。
> v2 验证精简：原 5 层 gate → 2 段（L3 整合测试 + L5 staging 实地）· L1/L2 由 pre-commit hook 兜底 · L4 review 是活动不是步骤。
> 详见 CLAUDE.md § 一 v1 → v2 变化。

### 5.2 关键决策点（必填 ≥ 1）
- 决策 1: <用什么组件 / 库 / 模式>
- 决策 2: <要不要缓存 / 限流 / 重试>

### 5.3 元信息
- 是否需要外部评审: 是 / 否
- 是否涉及 schema 变更: 是 / 否
- 是否需要 AB 测试: 是 / 否

---

## 6. spec.md 写法（必读 · 指向规范模板）

> ⚠️ **spec.md 写法是规范化的，禁止在调研报告里重新定义**。
> 直接打开 [`spec-template.md`](spec-template.md) 按模板写，第 2 段「验收标准 / Requirement + Scenario」已经定义了 Requirement (SHALL) + Scenario (GWT) 双层结构 + 完整示例 + DOD 自检。

### 6.1 关键约束（spec-template.md §2 摘要）

- **Requirement ≥ 1**：每个用 `### Requirement: <名字>` + `The system SHALL <承诺>`
- **Scenario ≥ 3**：每个用 `#### Scenario: <名字>` + Given/When/Then（沿用项目 GWT 写法，向后兼容）
- **4 类场景覆盖**：happy / invalid / edge / failure 至少各 1（详见 spec-template.md §3.7）
- **强约束 SHALL**：禁止用 should / may，否则 `scripts/check-step.py spec` 不通过

### 6.2 自动校验

- 工具：`python3 scripts/check-step.py spec docs/tasks/<date>-<topic>/spec.md`
- 钩子：pre-commit 已挂（`scripts/pre-commit` 第 4 段），提交时自动跑
- 跳过：`PRE_COMMIT_SKIP=1 git commit ...`

### 6.3 来源（决策记录 · 2026-07-17）

- 写法借鉴 [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) 的 SDD 思想（Requirement + SHALL + Scenario）
- 与项目原有 GWT 写法**合并**（不替换）：GWT 在 Scenario 段内继续生效，向后兼容
- **不装 OpenSpec 工具**（避免双源真理，详见 § 0 调研决策）
- 原文链接：https://juejin.cn/post/7662638440001388578（Harness 企业级落地三 · 给了灵感）

---

## 自检清单（AI 调研完必过）

- [ ] 任务理解段已写且用户复述对
- [ ] 现状扫描覆盖 ≥ 3 个相关文件
- [ ] 依赖发现列出 ≥ 3 个影响点
- [ ] 风险评估 ≥ 3 条带等级
- [ ] 输出建议给完整 6 步路径
- [ ] 关键决策点 ≥ 1
- [ ] 已读 `docs/40-追踪/目前缺陷.md`
- [ ] 已跑 `git log -10` + `git status`
- [ ] 步 1 写 spec.md 时按 [spec-template.md](spec-template.md) §2 用 Requirement+Scenario 结构
