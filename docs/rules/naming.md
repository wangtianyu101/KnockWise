# 命名规范

> **来源**：原 CLAUDE.md § 四（2026-07-17 拆出）

## 项目与文档入口

- 项目名：**KnockWise**
- 文档目录索引：[`docs/README.md`](../README.md)
- 相关文档（已存在，可引用）：
  - [`docs/tasks/2026-07-09-new-feature-question-bank-expand/`](../tasks/2026-07-09-new-feature-question-bank-expand/) （面试题库扩展）
  - [`docs/tasks/2026-07-17-new-feature-ai-push/`](../tasks/2026-07-17-new-feature-ai-push/) （AI 推送）
  - [`docs/tasks/2026-06-22-realtime-voice/`](../tasks/2026-06-22-realtime-voice/) （实时语音）
  - [`docs/api/README.md`](../api/README.md) （全局接口文档）
  - [`docs/issues.md`](../issues.md) （议題追踪）
  - [`docs/archive/2026-06-27-docs-old-structure/`](../archive/2026-06-27-docs-old-structure/) （4 层分类的旧结构）
  - [`docs/archive/三层记忆与学习闭环.md`](../archive/三层记忆与学习闭环.md)（v1 旧设计，已废弃）
  - [`docs/archive/project-history.md`](../archive/project-history.md)（项目阶段追踪归档）

## docs/ 目录结构（2026-07-21 更新）

```
docs/
├── README.md                       # 文档地图
├── issues.md                       # 议題追踪（动态）
├── DOD.md                          # 6 步 DOD 完成定义总表
│
├── rules/                          # ⭐ 项目规则（从 CLAUDE.md 拆出，2026-07-17）
│   ├── checklist.md                # 各阶段交付物清单（原 § 三）
│   ├── naming.md                   # 本文件（原 § 四）
│   ├── testing-rules.md            # 单测规则详情（原 § 六.1-6.4）
│   ├── local-dev.md                # 本地启动（原 § 七）
│   ├── milestones.md               # 当前状态（原 § 八）
│   └── design-mockup-workflow.md   # UI 设计子流程
│
├── tasks/                          # ⭐ 按任务组织
├── api/                            # ⭐ 全局 API 索引
├── designs/                        # HTML 设计稿
├── templates/                      # 15 个流程模板 + 1 个关闭核验模板
└── archive/                        # 归档旧文档
    ├── 2026-06-27-docs-old-structure/
    ├── 三层记忆与学习闭环.md
    └── project-history.md          # 阶段追踪归档
```

## 命名约定

任务目录 = `YYYY-MM-DD-<类型>-<topic>/`，文件 = 固定英文名。

| 字段 | 取值 |
|---|---|
| 日期 | `YYYY-MM-DD` 格式 |
| 类型 | `new-feature` / `bug` / `refactor` / `p0` |
| topic | kebab-case 简短描述 |
| 文件 | 固定英文名（`spec.md` / `plan.md` / `retro.md` 等） |

**示例**：`2026-07-17-new-feature-ai-push/`。

- 步骤 1：`product-doc.md`（仅新功能）+ `design-spec.md`（仅 UI）+ `spec.md`
- 步骤 2：`plan.md` + 按变更需要生成 `db-design.md` / `api-spec.md` / `component-spec.md`
- 不再新建 `technical-spec.md`；历史同名文件只作为旧格式归档或迁移来源
