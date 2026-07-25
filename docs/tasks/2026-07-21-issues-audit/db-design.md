---
title: DB Design（议题 C transcript 表增量 + 债务 1 复合索引）
date: 2026-07-22
status: v1 (AI 起草 · 待用户验收)
tags: [db-design, 2步, refactor-6, schema]
related:
  - plan.md（实施计划）
  - spec.md（业务契约 R1 · transcript 实时滚动）
  - api-spec.md（接口清单）
  - research.md（议题 C / 债务 1 调研）
---

# DB Design（议题 C transcript 表增量 + 债务 1 复合索引）

> **覆盖范围**：议题 C（新增 `interview_transcripts` 表）· 债务 1（加复合索引 + 修虚假注释）
>
> **不在本 spec 范围**：议题 A / B / D / F · 债务 2-8

---

## § 1 概述

| 项 | 描述 |
|---|---|
| **议题 C** | LiveKit 全双工实时语音 · 需要持久化 transcript（每条对话一句） |
| **债务 1** | `interviews` / `question_records` 表缺复合索引 · list_recent_interviews 走全表扫 |
| **关键决策** | spec.md R1（实时 transcript）+ research.md § 三 议题 C 关闭条件 + research.md § 四 债务 1 |

---

## § 2 新增表：`interview_transcripts`

### § 2.1 业务说明

议题 C 实时语音进行中，AI 与候选人的每句对话需要**实时持久化**（不仅是前端 state）。

**为什么不在前端 only 存**：
- LiveKit 断连 / 浏览器崩溃 → 用户期望恢复后看到 transcript
- 报告生成需要从 DB 拉 transcript（spec.md R3 evaluate + R5 报告）
- 多端访问（手机 + 电脑）需要同一份 transcript

### § 2.2 表结构

```sql
CREATE TABLE interview_transcripts (
  id              BIGINT       NOT NULL AUTO_INCREMENT
  , interview_id   VARCHAR(36)  NOT NULL
  , speaker        VARCHAR(8)   NOT NULL  -- 'ai' | 'user'
  , content        TEXT         NOT NULL
  , ts             DATETIME(3)  NOT NULL  -- 客户端时间戳（精度 ms）
  , created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
  , PRIMARY KEY (id)
  , FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  PARTITION BY HASH(interview_id) PARTITIONS 16;  -- 与 QuestionProgress 一致
```

### § 2.3 字段约束

| 字段 | 类型 | 约束 | 业务说明 |
|---|---|---|---|
| `id` | BIGINT | PK · AUTO_INCREMENT | 全局自增 |
| `interview_id` | VARCHAR(36) | NOT NULL · FK | 关联 `interviews.id`（UUID） |
| `speaker` | VARCHAR(8) | NOT NULL · Literal('ai','user') | 对话方 |
| `content` | TEXT | NOT NULL · max 2000 字 | 单句内容（transcript 一句） |
| `ts` | DATETIME(3) | NOT NULL | 客户端时间戳（VAD/turn 切分时点） |
| `created_at` | DATETIME | NOT NULL · DEFAULT CURRENT_TIMESTAMP | 服务端落库时间（审计用） |

### § 2.4 业务不变量

- `speaker` 必须是 `ai` 或 `user`（用 CHECK 或 app 层 Literal）
- `ts` 必须是客户端发送时的时间戳（非服务端 time()）
- `content` 单句最长 2000 字（超长 AI 输出截断）
- 同一 `interview_id` 的 transcript 按 `ts` 升序排序展示

---

## § 3 索引设计

### § 3.1 `interview_transcripts` 索引

| 索引 | 列 | 用途 | 优先级 |
|---|---|---|---|
| PK | id | 默认 | 必须 |
| FK | interview_id | 关联查询 | 自动 |
| **idx_interview_ts** | (interview_id, ts) | 按 interview 查询 + 按时间排序 | ✅ 推荐 |
| idx_speaker | (interview_id, speaker, ts) | 按 speaker 过滤 + 时间排序 | 🟡 可选 |

### § 3.2 `interviews` 索引（债务 1）

| 索引 | 列 | 用途 |
|---|---|---|
| **idx_user_status** | (user_id, status, deleted_at) | list_recent_interviews 走索引扫描而非全表扫 |

**注**：`interview_service.py:45` 注释声称"V1 closure 已加 idx_user_status"实际**不存在**（调研偏差）· T1 实施时**必须加索引 + 改注释**同步。

### § 3.3 `question_records` 索引（债务 1）

| 索引 | 列 | 用途 |
|---|---|---|
| **idx_interview_created** | (interview_id, created_at) | 按 interview 查询 + 按创建时间排序 |

### § 3.4 是否分区

- `interview_transcripts`：**HASH 分区 16**（与 QuestionProgress 一致）· 单 interview 数据可能很多
- `interviews` / `question_records`：**不分区**（数据量 < 10k）

---

## § 4 关系图

```
                    ┌─────────────────────┐
                    │     interviews        │
                    │  PK: id (UUID)        │
                    │  idx_user_status      │ ← 新增
                    └──────────┬────────────┘
                               │ 1:N
                               ▼
        ┌──────────────────────┴──────────────────────┐
        │                                              │
┌───────────────────────┐                ┌──────────────────────────┐
│  question_records      │                │  interview_transcripts   │ ← 新增
│  PK: id               │                │  PK: id                   │
│  FK: interview_id     │                │  FK: interview_id         │
│  idx_interview_created │ ← 新增         │  idx_interview_ts         │ ← 新增
└───────────────────────┘                └──────────────────────────┘
```

---

## § 5 数据量预估

| 表 | 当前 | 1 年预估 | 备注 |
|---|---|---|---|
| `interviews` | < 1k | ~5k | 增长慢 |
| `question_records` | < 10k | ~50k | 增长中等 |
| `interview_transcripts` | 0 | ~500k（每面试 100 句 × 5000 面试）| **增长快** · 分区必要 |

**影响**：transcript 表增长快 · 索引 `(interview_id, ts)` 能保证按 interview 查询 O(log N) · HASH 分区让单 interview 查询只扫 1 个 partition。

---

## § 6 迁移 SQL

### § 6.1 迁移策略（CLAUDE.md § 二 例外）

按 `backend/core/database.py:_run_migrations()` 启动 ALTER 模式：
- 新增表：用 `CREATE TABLE IF NOT EXISTS`
- 新增索引：用 `CREATE INDEX IF NOT EXISTS`（MySQL 8 在线 DDL · 不锁表）
- 注释修改：直接改文件（spec.md R5 关闭条件 · 调研偏差修正）

### § 6.2 迁移内容（按 T1 实施）

```sql
-- T1.1: 债务 1 复合索引（IF NOT EXISTS 幂等）
ALTER TABLE interviews
  ADD INDEX IF NOT EXISTS idx_user_status (user_id, status, deleted_at);

ALTER TABLE question_records
  ADD INDEX IF NOT EXISTS idx_interview_created (interview_id, created_at);

-- T1.2: 修虚假注释（文件修改，不是 SQL）
--   - backend/services/interview_service.py:45
--     "走 idx_user_status 索引（V1 closure 已加）" 
--     → "走 idx_user_status 索引（本 PR 新增，research.md 已核验）"
--   - backend/models/__init__.py:49
--     "# bcrypt hash" → "# pbkdf2-sha256 hash, nullable for GitHub OAuth users"
--   - backend/voice/stt.py:1-3, 28
--     "faster-whisper" → "openai-whisper"
```

### § 6.3 迁移内容（按 T4 实施 · 议题 C）

```sql
-- T4.1: 新增 interview_transcripts 表
CREATE TABLE IF NOT EXISTS interview_transcripts (
  id              BIGINT       NOT NULL AUTO_INCREMENT
  , interview_id   VARCHAR(36)  NOT NULL
  , speaker        VARCHAR(8)   NOT NULL  -- 'ai' | 'user'
  , content        TEXT         NOT NULL
  , ts             DATETIME(3)  NOT NULL
  , created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
  , PRIMARY KEY (id)
  , FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  PARTITION BY HASH(interview_id) PARTITIONS 16;

-- T4.2: 复合索引
CREATE INDEX IF NOT EXISTS idx_interview_ts
  ON interview_transcripts (interview_id, ts);
```

### § 6.4 写入到 `_MIGRATIONS` 列表

```python
# backend/core/database.py
_MIGRATIONS = [
    # ... 已有 11 条 ALTER ...
    
    # 2026-07-22 T1 (债务 1)
    "ALTER TABLE interviews ADD INDEX IF NOT EXISTS idx_user_status (user_id, status, deleted_at)",
    "ALTER TABLE question_records ADD INDEX IF NOT EXISTS idx_interview_created (interview_id, created_at)",
    
    # 2026-07-22 T4 (议题 C transcript)
    """
    CREATE TABLE IF NOT EXISTS interview_transcripts (
      id BIGINT NOT NULL AUTO_INCREMENT,
      interview_id VARCHAR(36) NOT NULL,
      speaker VARCHAR(8) NOT NULL,
      content TEXT NOT NULL,
      ts DATETIME(3) NOT NULL,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id),
      FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    PARTITION BY HASH(interview_id) PARTITIONS 16
    """,
    "CREATE INDEX IF NOT EXISTS idx_interview_ts ON interview_transcripts (interview_id, ts)",
]
```

---

## § 7 Rollback（CLAUDE.md § 6.1 风险缓解）

### § 7.1 索引可逆

```sql
-- 回滚 T1 索引（如有性能问题）
ALTER TABLE interviews DROP INDEX idx_user_status;
ALTER TABLE question_records DROP INDEX idx_interview_created;
ALTER TABLE interview_transcripts DROP INDEX idx_interview_ts;
```

### § 7.2 表不可逆（drop table）

```sql
-- 谨慎！drop table 会丢 transcript 数据
-- 仅在确认无保留价值时执行
DROP TABLE IF EXISTS interview_transcripts;
```

**建议**：transcript 表的 rollback 不做（除非业务明确放弃该功能）· 索引可单独 rollback。

---

## § 8 影响分析

| 范围 | 影响 |
|---|---|
| **已有数据** | 无破坏（只新增 + 加索引）|
| **现有 API** | 无影响（前端不变）|
| **现有 service** | 无影响（interview_service.py 仅改注释）|
| **现有单测** | 无影响（mock 测试）|
| **新 API** | POST /api/interviews/{id}/transcripts（写）+ GET /api/interviews/{id}/transcripts（读）|
| **新 service** | `transcript_service.py`（写 + 读）|
| **新前端组件** | LiveKitVoice（已有）· ReconnectToast（新建）|

---

## 🎯 硬性 DOD（db-design.md 完成必须全过）

- [x] § 1-5 业务表结构（interview_transcripts 字段 + 索引 + 关系）
- [x] § 6 迁移 SQL（CREATE TABLE IF NOT EXISTS + CREATE INDEX IF NOT EXISTS · 幂等）
- [x] § 7 Rollback 方案（索引可逆 / 表不可逆）
- [x] § 8 影响分析（无破坏性）
- [x] 业务不变量（speaker Literal / ts 客户端时间 / content max 2000）
- [x] 与 plan.md / spec.md / research.md 决策对齐
- [ ] **用户验收签字**（待用户确认）

---

## ✍️ 验收区

请回复以下任一：
- **"db-design 验收通过"** → 我继续写 api-spec.md（13 端点拆分 + LiveKit token API + transcript 推送协议）
- **"db-design 调 X"** → 修订（字段 / 索引 / 迁移）
- **"再想想"** → 停在 db-design 阶段等讨论