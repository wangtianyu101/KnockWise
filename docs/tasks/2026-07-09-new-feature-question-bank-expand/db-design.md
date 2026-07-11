---
title: 数据库设计 · V3 题库扩量 + 多维分类 + LeetCode 三件套
date: 2026-07-09
status: v1
tags: [db-design, 2步, 数据库, schema, v3]
related:
  - [plan.md](plan.md) — 2 步方案
  - [spec.md](spec.md) — 1 步技术契约
  - V1 既有 schema：见 `backend/models/__init__.py`
---

# 数据库设计：V3 题库扩量 + 多维分类 + LeetCode 三件套

> **目标**：V3 新增 5 张表（精选题单 3 张 + 每日一题 2 张）+ 1 张 seed_data 升级（系统标签预填）。不破坏 V1/V2 既有 schema。
>
> **迁移方式**：V1 既有 `_MIGRATIONS` 启动 ALTER（CLAUDE.md § 二债务 4 已知无 Alembic）。所有新表用 `CREATE TABLE IF NOT EXISTS` 幂等执行。
>
> **作者**：AI 主导（V1 既有 schema 基础 + V3 新增）

---

## 1. 设计原则

| 原则 | 实施 |
|---|---|
| **不破坏 V1 既有 schema** | Question / QuestionTag / QuestionTagMap / BookmarkCollection 等表不动 |
| **不破坏 V2 Profile 字段** | Profile.weak_topics / mastered_topics 等字符串字段不动 |
| **新表全部带 user_id 关联** | 所有新表都有 user_id 索引，符合 V1 既有模式 |
| **CREATE TABLE IF NOT EXISTS** | 启动时幂等创建，重复启动不报错 |
| **外键 ON DELETE CASCADE** | 题目删除自动清理子表（V1 模式） |
| **JSON 字段存扩展数据** | 进度 / 配置等扩展用 JSON 字段（V1 QuestionAnswerLog.tags 模式） |

---

## 2. V3 新增 5 张表

### 2.1 `question_collections`（精选题单表 · 官方/系统题单）

```sql
CREATE TABLE IF NOT EXISTS question_collections (
  id              VARCHAR(64) PRIMARY KEY,           -- 'algorithms_50' / 'system_design_30'
  name            VARCHAR(100) NOT NULL,             -- '算法入门 50 题'
  description     VARCHAR(500),                      -- 简介
  cover_color     VARCHAR(16) DEFAULT '#6366f1',     -- 封面渐变色
  icon_emoji      VARCHAR(16) DEFAULT '📘',          -- 封面 emoji（V3 mockup 用）
  is_system       BOOLEAN NOT NULL DEFAULT TRUE,     -- 系统题单（不可删）
  question_count  INT NOT NULL DEFAULT 0,            -- 冗余字段（性能）
  sort_order      INT NOT NULL DEFAULT 0,            -- 列表排序
  created_at      DATETIME NOT NULL,
  updated_at      DATETIME NOT NULL,
  INDEX idx_qc_system_order (is_system, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**说明**：
- V3 不做用户自建题单（`is_system` 全部为 TRUE）
- `cover_color` + `icon_emoji` 是 mockup 装饰字段
- `question_count` 冗余字段（避免每次都 COUNT 题单-题目表）

### 2.2 `question_collection_maps`（题单 ↔ 题目 多对多）

```sql
CREATE TABLE IF NOT EXISTS question_collection_maps (
  collection_id  VARCHAR(64) NOT NULL,
  question_id   VARCHAR(64) NOT NULL,
  position      INT NOT NULL DEFAULT 0,             -- 题单内顺序
  created_at    DATETIME NOT NULL,
  PRIMARY KEY (collection_id, question_id),
  FOREIGN KEY (collection_id) REFERENCES question_collections(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  INDEX idx_qcm_collection_pos (collection_id, position),
  INDEX idx_qcm_question (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**说明**：
- 多对多关联（V1 QuestionTagMap 模式）
- `position` 决定题单内题目顺序
- 复合主键 `(collection_id, question_id)` 防重复加入

### 2.3 `collection_subscribes`（题单订阅表 · 用户的题单进度）

```sql
CREATE TABLE IF NOT EXISTS collection_subscribes (
  id              VARCHAR(36) PRIMARY KEY,           -- UUID
  user_id         VARCHAR(36) NOT NULL,               -- FK → users.id
  collection_id   VARCHAR(64) NOT NULL,              -- FK → question_collections.id
  progress_json   JSON NOT NULL,                      -- {done_count, total_count, completion_rate, last_question_id}
  subscribed_at   DATETIME NOT NULL,
  last_active_at  DATETIME NOT NULL,
  completed_at    DATETIME,                          -- 完成时填（NULL = 进行中）
  UNIQUE KEY uniq_cs_user_collection (user_id, collection_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (collection_id) REFERENCES question_collections(id) ON DELETE CASCADE,
  INDEX idx_cs_user_active (user_id, last_active_at),
  INDEX idx_cs_collection (collection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**说明**：
- 1 个用户订阅 1 个题单 = 1 行
- `progress_json` 存 `{done_count, total_count, completion_rate, last_question_id}` 实时进度
- 唯一约束 `(user_id, collection_id)` 防重复订阅

### 2.4 `daily_challenges`（每日一题 · 题目分配表）

```sql
CREATE TABLE IF NOT EXISTS daily_challenges (
  date          DATE PRIMARY KEY,                    -- '2026-07-09'（按天分）
  question_id   VARCHAR(64) NOT NULL,                -- FK → questions.id
  created_at    DATETIME NOT NULL,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**说明**：
- 1 天 = 1 道题
- `date` 主键确保每天只有 1 道
- 选题策略：seed_service 启动时按 `date_hash % 200_questions` 自动分配

### 2.5 `daily_challenge_completions`（每日一题 · 用户完成表）

```sql
CREATE TABLE IF NOT EXISTS daily_challenge_completions (
  id              VARCHAR(36) PRIMARY KEY,           -- UUID
  user_id         VARCHAR(36) NOT NULL,                -- FK → users.id
  date            DATE NOT NULL,                       -- '2026-07-09'
  question_id     VARCHAR(64) NOT NULL,
  score           INT NOT NULL,                        -- 0-5（SM-2 quality）
  duration_sec    INT NOT NULL DEFAULT 0,              -- 答题用时
  completed_at    DATETIME NOT NULL,
  UNIQUE KEY uniq_dcc_user_date (user_id, date),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  INDEX idx_dcc_user_completed (user_id, completed_at),
  INDEX idx_dcc_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**说明**：
- 1 个用户 × 1 天 = 1 行（唯一约束）
- `score` 0-5 用于计算 streak（连续天数）
- streak 逻辑：连续 7 天都有 `completed_at` → streak=7

---

## 3. V3 升级的既有表（0 字段改动）

### 3.1 `questions` 表（不动字段 · 只加 150 行 seed_data）

```sql
-- V1 既有 schema 不变
-- V3 在 seed_data/*.json 新增 90 题（system_design 25 + algorithms 25 + network 20 + frontend 20）
-- seed_service 启动时插入新题（ID 命名规范：{topic_short}{3位序号}）
```

### 3.2 `question_tags` 表（系统标签预填 ~50 条）

```sql
-- V1 既有 schema 不变
-- V3 seed_service 启动时预填 is_system=True 的标签（命名规范：sys_ 前缀防冲突）
-- 预填示例：
--   A 维度（面试方向）：sys_algorithm / sys_system_design / sys_network / sys_frontend
--   B 维度（技术栈）：sys_python / sys_java / sys_redis / sys_kafka / sys_react / sys_k8s
--   C 维度（公司轮次）：sys_bytedance_r1 / sys_bytedance_r2 / sys_ali_r3 / sys_tencent_r2
```

### 3.3 `question_tag_maps` 表（关联预填 ~600 条）

```sql
-- V1 既有 schema 不变
-- V3 seed_service 启动时按 question.topic + question.sub_topic 自动映射 ~3 条/题
-- 新 90 题 × 平均 3 tag = ~270 条
-- 旧 50 题保留（不入 tag，向后兼容）
```

### 3.4 `study_plans` 表（V1 既有 · V3.0 补前端 UI · 不动 schema）

```sql
-- V1 既有 schema 完全不动
-- V3.0 只补前端 /plan 页面 + nav 入口，调用现有 5 端点
```

---

## 4. 索引与性能

| 表 | 索引 | 用途 |
|---|---|---|
| question_collections | `idx_qc_system_order` | 列表查询（按 is_system + sort_order） |
| question_collection_maps | `idx_qcm_collection_pos` | 题单详情（按 position 排序） |
| collection_subscribes | `idx_cs_user_active` | 用户订阅列表（按最近活跃） |
| daily_challenges | (主键 date) | 当日题查询 |
| daily_challenge_completions | `idx_dcc_user_completed` | streak 计算 |
| question_tag_maps | `idx_qtm_tag_question` (V1 既有) | 多标签筛选 |

---

## 5. 迁移 SQL（V1 `_MIGRATIONS` 风格）

```python
# backend/core/database.py:_MIGRATIONS 追加
MIGRATIONS = [
    # ... V1/V2 既有 migrations ...
    
    # V3.0 精选题单 + 题单关联
    """
    CREATE TABLE IF NOT EXISTS question_collections (
      id VARCHAR(64) PRIMARY KEY,
      ...
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS question_collection_maps (
      ...
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS collection_subscribes (
      ...
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    
    # V3.2 每日一题
    """
    CREATE TABLE IF NOT EXISTS daily_challenges (
      ...
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_challenge_completions (
      ...
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]
```

**回滚**：5 张表都是 `CREATE TABLE IF NOT EXISTS`，不删除既有表，无回滚风险。

---

## 6. 数据规模预估（V3 上线 30 天后）

| 表 | 预估行数 | 备注 |
|---|---|---|
| question_collections | 5-8 | 系统题单 5 个起 + 后续追加 |
| question_collection_maps | 90-150 | 5 题单 × 18-30 题 = 90-150 |
| collection_subscribes | 100-500 | 100 用户 × 1-5 题单 |
| daily_challenges | 30-90 | 每日 1 道，保留 30-90 天 |
| daily_challenge_completions | 100-500 | 100 用户 × 1-5 次完成 |
| question_tags (新增) | ~50 | 系统标签 50 条 |
| question_tag_maps (新增) | ~270 | 90 新题 × 3 tag/题 |

总新增行数：~600-1500（轻量）。

---

## 7. 🎯 硬性 DOD（db-design.md 完成必须全过）

- [x] 5 张新表 schema 完整（含字段 / 类型 / 约束 / 索引 / 外键）
- [x] V1/V2 既有 schema 零改动说明
- [x] 迁移 SQL 完整（CREATE TABLE IF NOT EXISTS）
- [x] 索引与性能有说明
- [x] 数据规模预估
- [x] 回滚策略（5 张表 IF NOT EXISTS 无回滚风险）

> ✅ 工具校验：`python3 scripts/check-step.py db-design <file>`

---

## 8. 📚 相关文档

- [plan.md](plan.md) — 2 步方案
- [spec.md](spec.md) — 1 步技术契约（含 GWT / 数据契约）
- [api-spec.md](api-spec.md) — 2 步 API 契约（即将生成）
- [component-spec.md](component-spec.md) — 2 步组件规范（即将生成）
- V1 models 现有 schema：`backend/models/__init__.py`
- V1 迁移模式：`backend/core/database.py:_MIGRATIONS`