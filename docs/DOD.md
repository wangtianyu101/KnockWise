---
title: 7 步 DOD 完成定义总表
date: 2026-06-27
status: v1
tags: [DOD, 7步流程, 完成定义]
---

# 7 步 DOD 完成定义总表

> **一句话**：每步都必须满足 DOD 才能进下一步。
>
> **核心原则**：**可验证 + 可量化 + 可拒绝 + 可追溯**。
>
> **适用**：所有 AI Coding 协作流程。每步结束前对照本表自查，全过才能进下一步。

---

## 一、DOD 总览（38 条）

| 步 | DOD 条数 | 关键量化指标 | 默认校验方式 |
|---|---|---|---|
| 0 调研 | 6 条 | 6 字段非空、≥ N | `scripts/check-research.py`（TODO） |
| 1 规格 | 6 条 | GWT ≥ 3, 测试场景 ≥ 3 | 人 review + AI 自检 |
| 2 计划 | 5 条 | 方案 ≥ 2, 决策点 ≥ 1 | 人 review |
| 3 拆分 | 5 条 | ≤ 1h 任务, 偏差 ≤ 30% | 人 review + AI 自检 |
| 4 实现 | 5 条 | 覆盖率 ≥ 80% | pre-commit hook + AI 自检 |
| 5 验证 | 5 条 | 5 层 gate 各 1 条 | 工具 + 人 |
| 6 发布 | 5 条 | 灰度 + 回滚 + 监控 | 工具 + 人 |
| 7 复盘 | 5 条 | 改进已分配, 已更新知识库 | 人 review |
| **合计** | **38 条** | — | — |

---

## 二、0 步 调研 DOD（6 条）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/research.md`
> **校验**：TODO `scripts/check-research.py`

```markdown
## 🎯 硬性 DOD（调研报告完成必须全过）

- [ ] §0 任务规模自检 6 个字段全部非空（无"待定"/"略"/"无"）
- [ ] 路径模式行存在且匹配模板（如 new-feature = full-7）
- [ ] 必填段全部填写（无"待定"/"略"/"待写"）
- [ ] "≥ N" 数量满足最低要求
- [ ] 自检清单全部勾选 ✅
- [ ] 证据清单每段 ≥ 1 条引用

> ⚠️ 任何 1 条未满足 → 调研报告不算完成
> ⚠️ TODO: 接入 `scripts/check-research.py`（pre-commit hook）
```

---

## 三、1 步 规格 DOD（6 条 spec.md + 4 条 product-doc.md）

### 三.0 product-doc.md（产品脑 · 4 条 · 仅 new-feature 必填）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/product-doc.md`
> **作者**：**人主导**（产品经理 / 项目负责人）
> **校验**：人 review + AI 辅助

```markdown
## 🎯 硬性 DOD（product-doc.md 完成必须全过）

- [ ] 5 段齐全（问题定义 / 目标用户 / 价值主张 / MVP 范围 / 成功指标）
- [ ] 成功指标 ≥ 1 个量化数字（不能是"做得好"）
- [ ] MVP 范围明确"包含 + 不包含"
- [ ] 价值主张双向（用户价值 + 商业价值）

> ⚠️ 任何 1 条未满足 → product-doc.md 不算完成
> ⚠️ TODO: 接入 `scripts/check-product-doc.py`（pre-commit hook）
```

### 三.1 spec.md（技术脑 · 6 条）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/spec.md`
> **作者**：**AI 主导**（人审核）
> **校验**：人 review + AI 自检
> **模板**：[`docs/templates/spec-template.md`](templates/spec-template.md) / [`docs/templates/product-doc-template.md`](templates/product-doc-template.md) / [`docs/templates/design-spec-template.md`](templates/design-spec-template.md)

```markdown
## 🎯 硬性 DOD（spec.md 完成必须全过）

- [ ] 5 段齐全（用户故事 / GWT / 边界 / 数据契约 / 测试用例）
- [ ] GWT ≥ 3 条（happy + edge + failure 各 ≥ 1）
- [ ] 数据契约 ≥ 1 schema（Pydantic / Zod / TypeScript interface）
- [ ] 测试场景 ≥ 3 条（happy + edge + failure 各 ≥ 1）
- [ ] §0 上游引用齐全（research.md + product-doc.md）
- [ ] 用户故事已验收（人签字 / 写在文档里 "已验收：<name> <date>"）

> ⚠️ 任何 1 条未满足 → spec.md 不算完成，不能进 2 步
> ⚠️ TODO: 接入 `scripts/check-spec.py`（pre-commit hook）
```

### 三.2 design-spec.md（设计脑 · 5 条 · 仅 UI 改动时）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/design-spec.md`
> **作者**：**人主导**（设计师）
> **校验**：人 review

```markdown
## 🎯 硬性 DOD（design-spec.md 完成必须全过）

- [ ] 5 段齐全（用户旅程 / 页面地图 / 页面线框 / 交互细节 / 视觉规范）
- [ ] ≥ 1 个完整用户旅程
- [ ] ≥ 1 个页面线框图（ASCII 或图片引用）
- [ ] 交互细节 ≥ 5 种状态（默认 / hover / loading / success / error）
- [ ] 视觉规范 5 方面齐全（颜色 / 字体 / 间距 / 组件库 / 圆角阴影）

> ⚠️ 任何 1 条未满足 → design-spec.md 不算完成
> ⚠️ TODO: 接入 `scripts/check-design-spec.py`（pre-commit hook）
```

---

## 四、2 步 计划 DOD（5 条）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/plan.md`
> **校验**：人 review

```markdown
## 🎯 硬性 DOD（计划完成必须全过）

- [ ] 方案 ≥ 2 个（不是 1 个方案 = 没对比 = 不能算"计划"）
- [ ] 推荐方案明确（不是"建议 A 或 B"二选一，必须明确推荐 1 个）
- [ ] 风险点带等级（🔴/🟡/🟢）+ 缓解措施（不能空挂"注意风险"）
- [ ] 决策点 ≥ 1（用什么库 / 模式 / 缓存策略 / 限流 / 重试）
- [ ] 引用完整（spec.md + product-doc.md + research.md 路径全列）

> ⚠️ 任何 1 条未满足 → plan.md 不算完成
```

---

## 五、3 步 拆分 DOD（5 条）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/tasks.md`
> **校验**：人 review + AI 自检

```markdown
## 🎯 硬性 DOD（任务拆分完成必须全过）

- [ ] 每个任务 ≤ 1h AI 工作量（粒度约束，防"代码先行"）
- [ ] 每个任务 1 个 commit（不混合多任务）
- [ ] 每个任务对应 ≥ 1 测试用例（来自 spec §5）
- [ ] 任务依赖关系明确（无环 / 拓扑序）
- [ ] 总估时 vs 实际偏差 ≤ 30%（事后验证，闭环）

> ⚠️ 任何 1 条未满足 → tasks.md 不算完成
```

---

## 六、4 步 实现 DOD（5 条）

> **产出物**：git commits + `docs/tasks/<date>-<type>-<topic>/test-cases.md`
> **校验**：pre-commit hook + AI 自检
> **模板**：[`docs/templates/test-cases-template.md`](templates/test-cases-template.md)

```markdown
## 🎯 硬性 DOD（每个 task 内必须全过）

- [ ] TDD 红→绿（先写失败测试 → 跑确认红 → 写实现 → 跑确认绿）
- [ ] 1 个 commit 对应 1 个 task（commit message 含 task 编号）
- [ ] pre-commit hook 通过（tsc + pytest 全绿）
- [ ] 核心 service 覆盖率 ≥ 80%（CLAUDE.md §1.8 清单）
- [ ] 整合产出 test-cases.md（4 步后所有任务的测试汇总）

> ⚠️ 任何 1 条未满足 → 实现不算完成
```

---

## 七、5 步 验证 DOD（5 层 gate）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/verify.md`
> **校验**：工具 + 人

```markdown
## 🎯 硬性 DOD（5 层 gate 全过）

- [ ] **L1 类型检查**：tsc / mypy 0 error
- [ ] **L2 单元测试**：pytest 通过 + 覆盖率 ≥ 80%
- [ ] **L3 集成测试**：E2E / API contract 测试通过
- [ ] **L4 代码审查**：human review diff 完成（reviewer 签字）
- [ ] **L5 运行时验证**：staging 跑通 + 截图 / 日志存档

> ⚠️ 任何 1 层没过 → verify.md 不算完成，不能进 6 步发布
```

---

## 八、6 步 发布 DOD（5 条）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/ship.md`
> **校验**：工具 + 人

```markdown
## 🎯 硬性 DOD（发布方案完成必须全过）

- [ ] 灰度策略明确（10% → 50% → 100% + 时间窗口 + 升级条件）
- [ ] 监控 + 告警就位（latency / error rate / 业务指标 + 告警阈值）
- [ ] 回滚预案就位（触发条件 + 一键回滚命令 + 责任人）
- [ ] 通报模板发出（团队 / 老板 / 受影响方 / 客服）
- [ ] ship.md 含 3 段（部署 + 监控 + 回滚，缺一不可）

> ⚠️ 任何 1 条未满足 → 发布不算完成
```

---

## 九、7 步 复盘 DOD（5 条）

> **产出物**：`docs/tasks/<date>-<type>-<topic>/retro.md`
> **校验**：人 review

```markdown
## 🎯 硬性 DOD（复盘完成必须全过）

- [ ] retro.md 5 段齐全（数据 / 做对的 / 做错的 / 下次改进 / 沉淀到哪）
- [ ] 工作量数据记录（实际小时 / commit 数 / 任务数）
- [ ] 返工次数 ≥ 0（如果有返工必须分析原因并写进"做错的"）
- [ ] 改进项已分配（具体到人或任务，不能是"下次注意"这种空话）
- [ ] 已更新知识库（CLAUDE.md / spec 模板 / skill / DOD.md 之一）

> ⚠️ 任何 1 条未满足 → 任务不算真正完成，闭环断裂
```

---

## 十、使用说明

### 10.1 每步结束前自查

```
完成 0 步调研 → 对照本文 §二 自查 6 条 → 全过才能进 1 步
完成 1 步规格 → 对照本文 §三 自查 6 条 → 全过才能进 2 步
...
```

### 10.2 DOD 缺失的后果

| DOD 缺失 | 后果 |
|---|---|
| 0 步没 DOD | AI 调研敷衍，进度无保障 |
| 1 步没 DOD | spec 漂移，AI 自由发挥 |
| 2 步没 DOD | 方案没对比，直接干 |
| 3 步没 DOD | 任务太粗，代码先行 |
| 4 步没 DOD | 实现质量无保障 |
| 5 步没 DOD | 上线后挂掉 |
| 6 步没 DOD | 灰度 / 回滚 / 监控缺失 |
| 7 步没 DOD | 经验流失，下次重犯 |

### 10.3 工具校验 TODO

- `scripts/check-research.py`（0 步）
- `scripts/check-spec.py`（1 步）
- `scripts/check-plan.py`（2 步）
- `scripts/check-tasks.py`（3 步）
- `scripts/check-implement.py`（4 步）
- `scripts/check-verify.py`（5 步）
- `scripts/check-ship.py`（6 步）
- `scripts/check-retro.py`（7 步）

集成到 `scripts/pre-commit` 第 4 段，根据改动文件类型跑对应校验。

### 10.3.1 文档模板列表

| 模板 | 说明 | 步 |
|---|---|---|
| `docs/templates/research-*.md` | 0 步调研模板（4 个，按任务类型） | 0 |
| `docs/templates/product-doc-template.md` | 1 步产品脑（人主导） | 1 |
| `docs/templates/spec-template.md` | 1 步技术脑（AI 主导） | 1 |
| `docs/templates/design-spec-template.md` | 1 步设计脑（设计师主导） | 1 |
| `docs/templates/test-cases-template.md` | 4 步整合测试用例 | 4 |
| `scripts/check-step.py` | 7 步 DOD 校验工具（pre-commit 自动跑） | — |

### 10.4 DOD 演进规则

- 新增 1 条 DOD：必须先有 ≥ 1 个真实失败案例（"因为没这条 DOD，XX 出过问题"）
- 删除 1 条 DOD：必须先证明这条永远可满足（"这条从来没失败过"）
- 修改 1 条 DOD：必须给出量化数字（覆盖率从 70% 改成 80% 的理由）

---

## 📚 相关文档

- [README.md](README.md) — 文档地图
- [CLAUDE.md](../CLAUDE.md) — 6 步流程定义（含 0 步调研 5 模板）
- `~/obsidian/coding/AI代码工具使用心得/全局流程.md` — 7 步流程总览
- `~/obsidian/coding/AI代码工具使用心得/调研体系.md` — 0 步规则全集
- `docs/tasks/<date>-<type>-<topic>/retro.md` — 复盘后可能更新本表