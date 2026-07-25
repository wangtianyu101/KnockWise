---
title: Frontmatter Schema
type: meta
date: 2026-07-24
status: v1
tags: [frontmatter, schema, validation]
related:
  - ../rules/checklist.md
  - ../../scripts/check-frontmatter.py
---

# Frontmatter Schema（per P2-4 决策）

所有 13+ 模板文件的 frontmatter 必填字段集。

## 最小必填集

```yaml
---
title: <必填 · 文档标题>
type: <必填 · research | spec | plan | tasks | product-doc | design-spec | api-spec | component-spec | db-design | verify | retro | test-cases | meta>
step: <必填 · 0-6 (refactor-6 阶段)>
date: <必填 · YYYY-MM-DD>
status: <必填 · draft | in-review | approved | archived>
tags: <必填 · 数组 · 至少 1 个>
related: <可选 · 引用路径数组>
---
```

## 字段说明

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `title` | string | ✅ | 简短描述，不超过 100 字符 |
| `type` | enum | ✅ | 13 种类型枚举 |
| `step` | int 0-6 | ✅ | `refactor-6` 流程阶段；`fix-mini` 允许 -1 |
| `date` | ISO date | ✅ | YYYY-MM-DD 格式 |
| `status` | enum | ✅ | draft / in-review / approved / archived |
| `tags` | list | ✅ | 至少 1 个 tag |
| `related` | list | ❌ | 引用相对路径数组 |

## 13 种 type 枚举

| type | 对应模板 |
|---|---|
| research | research-{new-feature,bug,refactor,p0}.md |
| spec | spec-template.md |
| plan | plan-template.md |
| tasks | tasks-template.md |
| product-doc | product-doc-template.md |
| design-spec | design-spec-template.md |
| api-spec | api-spec-template.md |
| component-spec | component-spec-template.md |
| db-design | db-design-template.md |
| verify | verify-template.md |
| retro | retro-template.md |
| test-cases | test-cases-template.md |
| meta | 本文件 + _frontmatter-schema.md |

## 与 P0-7 task.yaml 关系

- P0-7 task.yaml 是 任务目录级元数据（task/v1 schema）
- P2-4 frontmatter 是文档级元数据（_frontmatter-schema.md）
- 两个独立不互替代
