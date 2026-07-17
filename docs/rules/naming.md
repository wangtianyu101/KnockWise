# 命名规范

> **来源**：原 CLAUDE.md § 四（2026-07-17 拆出）

## 模块名 + 文档入口

- 模块名：**面试题库**
- 设计文档：`docs/tasks/2026-06-22-new-feature-question-bank/spec.md`
- 文档目录索引：[`docs/README.md`](../README.md)
- 相关文档（已存在，可引用）：
  - [`docs/tasks/2026-06-22-new-feature-question-bank/`](../tasks/2026-06-22-new-feature-question-bank/) （面试题库全套）
  - [`docs/tasks/2026-06-22-new-feature-ai-push/`](../tasks/2026-06-22-new-feature-ai-push/) （AI 推送全套）
  - [`docs/tasks/2026-06-22-realtime-voice/`](../tasks/2026-06-22-realtime-voice/) （实时语音）
  - [`docs/api/README.md`](../api/README.md) （全局接口文档）
  - [`docs/issues.md`](../issues.md) （议題追踪）
  - [`docs/archive/2026-06-27-docs-old-structure/`](../archive/2026-06-27-docs-old-structure/) （4 层分类的旧结构）
  - [`docs/archive/三层记忆与学习闭环.md`](../archive/三层记忆与学习闭环.md)（v1 旧设计，已废弃）
  - [`docs/archive/project-history.md`](../archive/project-history.md)（项目阶段追踪归档）

## docs/ 目录结构（2026-07-17 更新）

```
docs/
├── README.md                       # 文档地图
├── issues.md                       # 议題追踪（动态）
├── DOD.md                          # 7 步 DOD 完成定义总表（38 条）
│
├── rules/                          # ⭐ 项目规则（从 CLAUDE.md 拆出，2026-07-17）
│   ├── checklist.md                # 各阶段交付物清单（原 § 三）
│   ├── naming.md                   # 本文件（原 § 四）
│   ├── testing-rules.md            # 单测规则详情（原 § 六.1-6.4）
│   ├── local-dev.md                # 本地启动（原 § 七）
│   └── milestones.md               # 当前状态（原 § 八）
│
├── tasks/                          # ⭐ 按任务组织
├── api/                            # ⭐ 全局 API 索引
├── designs/                        # HTML 设计稿
├── templates/                      # 调研模板（基础设施，15 个模板）
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

**示例**：
- `2026-06-22-new-feature-question-bank/` 目录
- 内部 `spec.md`（1 步规格产品层）+ `technical-spec.md`（技术层）+ `design-spec.md`（设计层）+ `plan.md`（6 步实施计划）
