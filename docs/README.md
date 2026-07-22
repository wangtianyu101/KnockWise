---
title: KnockWise 文档地图
date: 2026-06-27
status: v1
---

# KnockWise 文档地图

> **新结构**：2026-06-27 重构完成。旧 4 层分类已归档到 `archive/2026-06-27-docs-old-structure/`。
>
> **新哲学**：**按任务分类**（一次任务的所有文档放一起）+ **全局汇总独立**。

---

## 📁 当前目录结构

```
docs/
├── README.md                  # ⭐ 本文件（文档地图）
├── issues.md                  # ⭐ 议題追踪（动态）
├── DOD.md                     # ⭐ 6 步 DOD 完成定义总表
│
├── rules/                     # ⭐ 项目规则（从 CLAUDE.md 拆出 · 2026-07-17）
│   ├── checklist.md           # 各阶段交付物清单
│   ├── naming.md              # 命名规范 + docs/ 结构
│   ├── testing-rules.md       # 单测规则详情
│   ├── local-dev.md           # 本地启动
│   ├── milestones.md          # 实施状态流水
│   └── design-mockup-workflow.md  # UI 设计 mockup 工作流（HTML + ASCII + index 三层）
│
├── tasks/                     # ⭐ 按任务（主存储）
│   └── YYYY-MM-DD-<type>-<topic>/
│       ├── research.md        # 0 调研
│       ├── product-doc.md     # 1 产品脑（仅新功能）
│       ├── design-spec.md     # 1 设计脑（仅 UI）
│       ├── spec.md            # 1 业务契约
│       ├── plan.md            # 2 方案
│       ├── db-design.md       # 2 条件产物：schema
│       ├── api-spec.md        # 2 条件产物：API
│       ├── component-spec.md  # 2 条件产物：UI 组件
│       ├── tasks.md           # 3 拆分与实施状态
│       ├── test-cases.md      # 4 测试汇总
│       ├── verify.md          # 5 L3 + L5
│       ├── retro.md           # 6 复盘
│       └── mockups/           # UI 任务的 HTML mockup（进 git）
│
├── api/                       # ⭐ 全局 API 索引
│   └── README.md
├── designs/                   # 设计稿 HTML
├── templates/                 # ⭐ 15 个流程模板 + 1 个遗留项关闭核验模板
│   ├── research-new-feature.md      # 0 步 new-feature
│   ├── research-bug.md               # 0 步 bug
│   ├── research-refactor.md          # 0 步 refactor
│   ├── research-p0.md                # 0 步 P0
│   ├── issue-closure-template.md      # 收尾动作：遗留项关闭核验
│   ├── product-doc-template.md       # 1 步产品脑（业务层）
│   ├── design-spec-template.md       # 1 步设计脑（业务层）
│   ├── spec-template.md              # 1 步技术脑（业务层，纯契约）
│   ├── db-design-template.md         # 2 步数据库设计（技术详细化）
│   ├── api-spec-template.md          # 2 步 API 设计（技术详细化）
│   ├── component-spec-template.md    # 2 步组件设计（技术详细化）
│   ├── plan-template.md              # 2 步方案文档
│   ├── tasks-template.md             # 3 步任务拆分
│   ├── test-cases-template.md        # 4 步整合测试
│   ├── verify-template.md            # 5 步验证文档
│   └── retro-template.md             # 6 步复盘文档
│
└── archive/                   # 归档
    ├── 2026-06-27-docs-old-structure/   # 4 层分类的旧结构
    ├── 三层记忆与学习闭环.md              # v1 旧设计，已废弃
    └── project-history.md              # 阶段追踪归档（CLAUDE.md § 8.1 旧内容）
```

---

## 🎯 我应该看哪个？

| 我想... | 看 |
|---|---|
| 看议題列表 / 找要做的活 | [issues.md](issues.md) |
| 验证并关闭遗留项 | [templates/issue-closure-template.md](templates/issue-closure-template.md) |
| 检查某步是否完成 / 找 DOD 模板 | [DOD.md](DOD.md) |
| **看各阶段交付物** | **[rules/checklist.md](rules/checklist.md)** |
| **看命名规范 + docs/ 结构** | **[rules/naming.md](rules/naming.md)** |
| **看单测规则详情** | **[rules/testing-rules.md](rules/testing-rules.md)** |
| **启动本地服务** | **[rules/local-dev.md](rules/local-dev.md)** |
| **看实施状态 / 历史里程碑** | **[rules/milestones.md](rules/milestones.md)** |
| **设计 UI / 产出 HTML mockup** | **[rules/design-mockup-workflow.md](rules/design-mockup-workflow.md)** |
| 了解面试题库特性 | [tasks/2026-07-09-new-feature-question-bank-expand/](tasks/2026-07-09-new-feature-question-bank-expand/) |
| 了解 AI 推送特性 | [tasks/2026-07-17-new-feature-ai-push/](tasks/2026-07-17-new-feature-ai-push/) |
| 了解实时语音方案 | [tasks/2026-06-22-realtime-voice/](tasks/2026-06-22-realtime-voice/) |
| 看 API 接口 | [api/README.md](api/README.md) |
| 看设计稿 HTML | [designs/](designs/) |
| 调研新任务 | [templates/](templates/) |
| 查旧结构 | [archive/2026-06-27-docs-old-structure/](archive/2026-06-27-docs-old-structure/) |

---

## 📝 命名约定

### 任务目录
- 格式：`YYYY-MM-DD-<类型>-<topic>/`
- 类型：`new-feature` / `bug` / `refactor` / `p0`
- 示例：`2026-06-22-new-feature-question-bank/`

### 任务目录内文件
- 固定英文名：`spec.md` / `plan.md` / `retro.md` 等
- 按 6 步流程命名（详见 CLAUDE.md §0）

---

## 🔄 迁移历史

- **2026-06-27**：从 4 层分类（00-入门/10-架构/20-参考/30-历史/40-追踪）改为按任务分类
- 旧目录完整保留在 `archive/2026-06-27-docs-old-structure/`

---

## 📚 相关文档

- [CLAUDE.md](../CLAUDE.md) — 6 步流程 + 单测 + DOD 完整定义
- [issues.md](issues.md) — 议題追踪（每日开工必读）
- [templates/research-new-feature.md](templates/research-new-feature.md) — 调研模板样例
