---
title: Product Doc · CI 失败自动修复
date: 2026-07-22
status: v1
type: product-doc（产品脑）
related:
  - research.md（调研）
  - spec.md（技术脑）
---

# Product Doc · CI 失败自动修复

> 一句话定义：CI 失败时，Claude Code Agent 自动读日志、改代码、commit 到原 PR 分支，开发者无需手动介入。

---

## 1. 问题定义

### 用户痛点
- 开发者提交 PR 后 CI 失败，需要手动打开 GitHub Actions → 找失败 job → 复制日志 → 本地复现 → 改 → 重 push → 循环
- 每次手动 debug 一个 CI 失败耗时 5-30 分钟（视复杂度）
- 偶发性失败（flaky test / 网络抖动 / 缓存问题）尤其浪费精力——明明代码没问题
- 多 PR 并行时，CI 失败的"上下文切换成本"很高

### 时机
- KnockWise 当前 CI baseline = 695 passed / 0 failed（2026-07-22）
- T34 三 Gate 已上线（quality / typecheck / build），CI 失败多为新增代码回归
- 项目刚完成 v3.8 sidebar / V4 假绿灯 修复，节奏快、PR 频繁，需要加速迭代
- Anthropic 官方 Claude Code Action 已 GA（2026-07），技术成熟度足够

### 不做会怎样
- 继续手动 debug · 每周浪费 ~3-5h 开发者时间
- PR 节奏变慢 · 推迟产品发布
- 偶发 CI 失败的"重 push"习惯会让 git history 变脏

---

## 2. 目标用户

### 角色
- **KnockWise 开发者**（项目所有者单人 + 偶尔协作者）· 25-40 岁 · Mac/Linux 用户

### 场景
- 提交 PR 后，CI 跑 1-5 分钟完结，发现红 ❌
- 开发者已经切换到下一个任务，Slack/IDE 收到 notification
- 2 分钟内看到 auto-fix 已经 push 一个新 commit，CI 重新跑，绿 ✅
- 开发者回来 review 一下 auto-fix 的 diff，approve merge

### 频率
- 每周 2-5 次 CI 失败（按当前节奏估）
- 每次节省 5-30 分钟手动 debug

---

## 3. 价值主张

| 维度 | 价值 | 量化 |
|---|---|---|
| 时间节省 | 每周 30-150 分钟 | 估按平均 10min × 5 fail × 70% auto-fix 成功率 |
| 反馈循环 | 失败到修复 ≤ 5 分钟 | vs 手动 5-30 分钟 |
| 代码质量 | 失败立即修，不积压 | 减少"先 merge 别的再回头修"的反模式 |
| 心理负担 | 不需要守在 CI 旁边 | "提交即可" 的工作流 |

---

## 4. 范围与非目标

### 范围内
- ✅ 自动修复：frontend typecheck / backend typecheck / 空壳测试 / 覆盖率阈值
- ✅ 自动 commit 推原 PR 分支
- ✅ 失败上限 2 次/commt
- ✅ `[NO-TEST-NEEDED]` 标注允许（CLAUDE.md § 6.1 协同）
- ✅ 不在 main 分支自动修

### 范围外（不做）
- ❌ 自动修业务 service 逻辑（interview / digest / report / 等）
- ❌ 自动 merge PR
- ❌ 跨 repo 联动
- ❌ 飞书 / Slack 主动通知（用 GitHub 原生 notification）
- ❌ 自我学习 / 记忆历史 fix 模式

---

## 5. 度量

- **触发率**：CI 失败中 auto-fix 启动的占比（目标 100%，main 分支除外）
- **成功率**：auto-fix 后 CI 重跑绿的占比（目标 ≥ 70%）
- **节省时间**：手动 debug 时间 vs auto-fix 时间（每月汇总）
- **Token 成本**：每月 API 费用（$20 上限）
- **异常率**：auto-fix 引入新 bug 的比例（每月 audit PR review）

---

## 6. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 静默改坏代码 | 强制改完跑测试再 commit · commit message 含 `auto-fix:` 前缀 |
| 死循环 | 2 次/commt 上限 · 第 3 次转人工 |
| 绕过单测强制规则 | `[NO-TEST-NEEDED]` 标注 · 24h 后审 |
| 业务逻辑被改 | prompt 显式禁止 service 文件 · 改动触发 `[NEEDS-REVIEW]` 标签 |
| Token 烧 | max-turns 25 · $20/月 Anthropic Console 限 |

---

## 7. 验收标准

- [ ] CI 失败后 ≤ 2 分钟内 auto-fix workflow 启动
- [ ] 修复后 CI 重跑绿（除非真需人工）
- [ ] 失败 3 次自动停止
- [ ] 业务 service 改动被拒绝 / 标 [NEEDS-REVIEW]
- [ ] main 分支 push 不自动修
- [ ] 每次 commit message 含 `auto-fix:` 前缀
- [ ] 文档完整：README 段说明 + 如何关闭

---

## 上游

- 调研：[`research.md`](research.md)
- 决策：[`decisions.md`](decisions.md)
