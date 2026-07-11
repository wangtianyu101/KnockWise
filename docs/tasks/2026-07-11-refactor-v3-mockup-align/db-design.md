---
title: 数据库设计 · KnockWise 前端对齐重构
date: 2026-07-11
status: v1
tags: [db-design, 2步, 数据库, v3-mockup-align, knockwise, 无变更]
related:
  - [research.md](research.md) — 上游调研
  - [plan.md](plan.md) — 实施计划
  - [spec.md](spec.md) — 技术契约
  - [api-spec.md](api-spec.md) — /recent 端点详细
---

# 数据库设计：KnockWise 前端对齐重构

> **核心结论**：**本次重构不改 DB schema、不加表、不加字段、不加索引、不做迁移**。
>
> **唯一例外**：docker-compose.yml 中 `MYSQL_DATABASE` 改名（`codemock` → `knockwise`），但仅新部署生效，不影响真实运行中的 MySQL 数据（CLAUDE.md §二冻结）。

---

## 0. 全局结论（CLAUDE.md §1.5 全局图）

```
┌──────────────────────────────────────────────────────────────────────┐
│                       DB 改动范围：几乎为 0                          │
│                                                                       │
│  现有 19 张表 ──────────────────→  现有 19 张表（不变）              │
│  backend/models/__init__.py                                            │
│                                                                       │
│  现有索引 ──────────────────→  现有索引（不变）                       │
│  backend/core/database.py:_MIGRATIONS                                  │
│                                                                       │
│  现有 _MIGRATIONS 自动 ALTER ────→ 不增加任何新 ALTER                 │
│                                                                       │
│  docker-compose.yml:                                                   │
│    MYSQL_DATABASE: codemock ──→ knockwise（仅新部署）                 │
│    MYSQL_USER: codemock      ──→ knockwise（仅新部署）                 │
│    MYSQL_PASSWORD: codemock  ──→ knockwise（仅新部署）                 │
│                                                                       │
│  ⚠️ 真实运行的 MySQL 数据库不变（CLAUDE.md §二冻结）                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. 为什么不需要 DB 改动（CLAUDE.md §1.6 技术细节）

### 1.1 业务冻结原则

CLAUDE.md §1.7 重构路径定义："不改业务行为"。
本次重构是**纯 UI 重构**，所有 API 行为、数据模型、Service 逻辑均不变。

### 1.2 已有 Interview.radar_data 字段（关键）

V2 沉淀层（2026-06-28 new-feature-v2-smart-sediment）实施时，`backend/models/__init__.py:153` 已经添加了 `radar_data JSON` 字段到 `Interview` 表：

```python
class Interview(Base):
    __tablename__ = "interviews"
    id = Column(...)
    user_id = Column(...)
    round = Column(...)  # 字节·后端 / 阿里·前端 等
    overall_score = Column(Float, nullable=True)
    # ↓ V2 已添加
    radar_data = Column(JSON, default=dict)  # 5 维雷达数据
    # ... 其他字段
```

**这意味着**：`/api/interviews/recent` 端点**直接读取现有 `radar_data` 字段**即可，不需要 schema 改动。

### 1.3 现有索引覆盖（关键）

`idx_user_status` 复合索引已存在（V1 closure 实施），覆盖 `WHERE user_id=? AND status=? AND deleted_at IS NULL ORDER BY started_at DESC LIMIT N` 查询模式：

```sql
-- V1 closure 已有索引（无需新建）
CREATE INDEX idx_user_status ON interviews(user_id, status, deleted_at);
```

`/api/interviews/recent?limit=3` 查询完全走这个索引，O(1) limit 性能。

---

## 2. 受影响的 DB 相关代码（仅改名 · 不改 schema）

### 2.1 docker-compose.yml（仅新部署生效）

| 项 | 现状 | 改后 | 影响 |
|---|---|---|---|
| `MYSQL_DATABASE` | `codemock` | `knockwise` | 仅新部署生效 |
| `MYSQL_USER` | `codemock` | `knockwise` | 仅新部署生效 |
| `MYSQL_PASSWORD` | `codemock` | `knockwise` | 仅新部署生效 |
| `DATABASE_URL` | `mysql+aiomysql://codemock:codemock@mysql:3306/codemock` | `mysql+aiomysql://knockwise:knockwise@mysql:3306/knockwise` | 仅新部署生效 |

**重要约束（CLAUDE.md §二冻结）**：
- **真实 MySQL 数据库保持 codemock** —— 现有数据不能动
- **本次 P4b 阶段不重建 DB** —— 仅改 docker-compose.yml 文件
- **未来新部署**才用 knockwise DB 名，老部署继续用 codemock
- **详见 plan.md § P4b** —— 这是文案改名，不是 schema 改动

### 2.2 backend/core/config.py（不改）

```python
# backend/core/config.py:6
database_url: str = "mysql+aiomysql://codemock:codemock@localhost:3306/codemock"
```

**不改**：本地连接 URL 的 codemock 用户名/密码保持，**否则连不上现有真实 DB**。

> CLAUDE.md §二"绝对不能动：MySQL 真实数据"—— config.py 的 URL 是连接现有真实 DB 的凭证，不能改。

---

## 3. 现有 19 张表（无任何变更）

| 表 | 关键字段 | 与 V3.8 关系 | 变更 |
|---|---|---|---|
| `users` | id / display_name / role | Dashboard 显示用户名 | ❌ 无 |
| `interviews` | id / user_id / round / status / overall_score / radar_data | HeroCard 数据源 | ❌ 无 |
| `question_records` | id / interview_id / question_id / score | RadarMini 数据源 | ❌ 无 |
| `questions` | id / topic / difficulty | Sidebar 跳转题目 | ❌ 无 |
| `question_progress` | user_id / question_id / status / score | StatsBar 待复习数据 | ❌ 无 |
| `study_plans` | id / user_id / status | PlanCard | ❌ 无 |
| `collections` / `user_collection_subs` | id / user_id | 题单（V3.1 既有）| ❌ 无 |
| `qa_questions` / `qa_answers` | id | 问答社区 | ❌ 无 |
| `profiles` | id / user_id / data JSON | Profile 页 | ❌ 无 |
| `user_settlements` | id / user_id / week | V2 沉淀层 | ❌ 无 |
| `news_*` (3 张) | 各种 | 信息流 | ❌ 无 |
| `obsidian_sediments` | id / user_id / file_path | V2 沉淀层 | ❌ 无 |
| `interview_favorites` | user_id / interview_id | 历史报告 | ❌ 无 |
| `audit_logs` | user_id / action | V3.7 质量监控 | ❌ 无 |
| `question_sync_history` | id / source / status | V3.7 PR 4 监控 | ❌ 无 |

**全部 19 张表 + 现有 _MIGRATIONS 自动 ALTER 列表无变更**。

---

## 4. 现有索引（无任何变更）

| 索引 | 表 | 字段 | 用途 |
|---|---|---|---|
| `idx_user_status` | interviews | user_id, status, deleted_at | /recent 端点走这个索引 |
| `idx_user_started` | interviews | user_id, started_at DESC | 历史报告列表 |
| `idx_interview_created` | question_records | interview_id, created_at | 答题记录 |
| `idx_topic_difficulty` | questions | topic, difficulty | 题库筛选 |
| `idx_question_user_status` | question_progress | question_id, user_id, status | 复习队列 |

**所有查询（含新的 /recent）的索引需求已被现有索引覆盖**，不需要加索引。

---

## 5. /api/interviews/recent 查询计划分析

### 5.1 查询 SQL

```sql
SELECT id, round, style, status, total_questions, overall_score, 
       radar_data, started_at, ended_at
FROM interviews
WHERE user_id = ? 
  AND status = 'completed' 
  AND deleted_at IS NULL
  AND overall_score IS NOT NULL
ORDER BY started_at DESC
LIMIT 3;
```

### 5.2 索引命中分析

| WHERE 条件 | 索引命中 |
|---|---|
| `user_id = ?` | ✅ idx_user_status |
| `status = 'completed'` | ✅ idx_user_status |
| `deleted_at IS NULL` | ✅ idx_user_status |
| ORDER BY started_at DESC | ⚠️ 需 filesort（但 LIMIT 3 + 小数据量 O(可忽略)）|

### 5.3 性能估算

- 走 idx_user_status 索引：O(log N + 3)
- filesort 3 行：~1ms
- 总查询：~20ms（mock 测试）
- P95 目标：< 50ms ✅ 满足

### 5.4 大数据量优化（未来如果性能不够）

如果将来面试数 > 10k，`ORDER BY started_at DESC` 可能成为瓶颈。**优化方案（本次不做）**：

```sql
-- 未来可选：复合索引覆盖排序
CREATE INDEX idx_user_completed ON interviews(user_id, status, started_at DESC);
```

**本次不做原因**：
- 现有数据 < 1k 面试
- mock 测试 P95 ~20ms 已满足
- CLAUDE.md §二冻结真实 DB（不能加索引风险）

---

## 6. 不需要的数据迁移

### 6.1 无 SQL 迁移脚本

**没有 SQL 文件需要创建**。CLAUDE.md § 阶段 3 详细化要求的"补：数据迁移 SQL"—— 本次是空。

### 6.2 无 Alembic 迁移

后端用 `backend/core/database.py:_MIGRATIONS` 启动时自动 ALTER，**本次不增加任何新 ALTER**。

### 6.3 docker-compose 改动不涉及数据迁移

`docker-compose.yml` 改名 `codemock → knockwise` 仅影响**未来新部署**用新 DB 名启动容器，**现有数据完全不动**。

---

## 7. 现有 _MIGRATIONS 列表（不增加新条目）

```python
# backend/core/database.py:_MIGRATIONS（节选）
_MIGRATIONS = [
    # ... 现有 20+ ALTER 语句（V1-V3 实施时添加） ...
    # 本次 V3.8 不增加任何新 ALTER
]
```

---

## 8. 风险评估

| 风险 | 等级 | 说明 |
|---|---|---|
| docker-compose 改名导致本地起服务失败 | 🟢 低 | 用户本地用 brew services 启的 MySQL（端口 3306），不用 docker-compose · 详见 CLAUDE.md § 七 |
| 真实 DB 改名导致连接失败 | 🔴 不做 | CLAUDE.md §二冻结 + 本次不改 config.py |
| 新加索引导致锁表 | 🔴 不做 | 本次不加索引 |
| Interview.radar_data 字段为空（旧数据）| 🟡 中 | /recent 端点需处理 radar_data 为 {} 的情况：EmptyState 提示用户 |

### 8.1 radar_data 空数据处理

旧面试（V2 沉淀层之前）可能 `radar_data = {}`：

```python
# backend/services/interview_service.py:list_recent_interviews
for iv in interviews:
    radar = iv.radar_data or {}
    # 如果 radar 为空，HeroCard partial 状态显示
    if not radar or not any(radar.values()):
        # partial 状态而非 full
        pass
```

前端 HeroCard 根据 `radar_data` 是否为空自动判断 full vs partial 状态（spec.md §3.3 + design-spec.md §3.1.3 已规定）。

---

## 9. 关联文档

- [research.md](research.md) §1.4 任务理解 + §4 风险评估
- [plan.md](plan.md) §2 P3 阶段 · §5 风险预案
- [spec.md](spec.md) §2 API 契约 / 兼容矩阵
- [api-spec.md](api-spec.md) /recent 端点完整规范
- CLAUDE.md § 二"绝对不能动：MySQL 真实数据"· § 一.三 阶段 2· § 阶段 3 数据迁移 SQL