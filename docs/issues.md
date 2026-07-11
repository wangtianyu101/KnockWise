# 目前缺陷与设计议题

> 记录已识别的设计缺陷、技术债务、待讨论议题。**这是动态文档** —— 遇到新发现随时加。
>
> 状态图例：📋 待讨论 · 🚧 进行中 · ✅ 已解决 · ❌ 不会做 · ⚠️ 已知限制

---

## 一、设计议题（待深入讨论）

### 议题 A — 会话状态机：LangGraph StateGraph 写了但没用上

**现状**：`backend/agents/interview_graph.py` 定义了完整的 StateGraph 编译产物，但 `backend/services/interview_service.py:80-150` 实际走的是**直接调用** `question_engine` / `followup_engine` / `evaluate_agent`，绕开了 graph 的状态转移逻辑。

**影响**：
- 失去了 LangGraph 的可视化 trace 能力
- 自定义状态字段（如 `state["questions_asked"]`）在 graph 之外手动维护，存在不一致风险
- 增加新节点（如人机协作、阶段性回顾）需要改 service 而不是改 graph

**可选路径**：
1. **保留现状**：service 是薄封装层，agent 是真正逻辑，graph 暂时是 dead code
2. **真用 graph**：service 改为 `graph.invoke(state)`，所有状态变更走图
3. **完全删 graph**：service 已经是 single source of truth，删 `interview_graph.py` 减少误导

**讨论时机**：状态：A. 状态机重构的代价与扩展性收益对比；B. 现有 50 道种子题 + 追问树是否能在 graph 里清晰表达

---

### 议题 B — `interview.py` 803 行的拆分

**现状**：`backend/api/interview.py` 单文件 803 行，承担了 start / list / next-question / submit-answer / complete / favorite / delete / records 全部端点。

**影响**：
- 改动一处容易影响别处
- 单测难以隔离
- 后续加新端点（如 round 切换、题目回看）会让文件更长

**可选路径**：
1. **按职责拆**：`interview_lifecycle.py`（start/complete）+ `interview_runtime.py`（next-q/answer）+ `interview_query.py`（list/records）
2. **CQRS 分离**：写操作（start/complete/answer）vs 读操作（list/records）分文件
3. **保留单文件 + 拆 router prefix**：技术上更轻，团队约定避免互相改

**讨论时机**：模块边界、团队协作模式

---

### 议题 C — 语音架构：3 套并存的最终形态

**现状**：
- `/interview.tsx` → `VoiceRoom.tsx`（旧 PTT + WebSocket）
- `/interview/setup.tsx` → `/interview/room.tsx` → `VoiceRecord.tsx`（新 PTT）
- `LiveKitVoice.tsx` 组件存在但**没有任何页面用**
- `voice/livekit_worker.py` 在每次 start interview 时启动，但**没有客户端连**

**影响**：
- 维护 3 套组件的认知成本
- 不知道该往哪个方向投入
- `livekit-server` 一直在跑但没被消费

**可选路径**：
1. **文字 + PTT 收敛**：保留 `/interview` 和 `/interview/room` 两套，分别服务"打字用户"和"不想打字用户"
2. **全力上全双工**：废弃 PTT，`room.tsx` 改为 `LiveKitVoice`，等 LiveKit 调通
3. **Hybrid**：默认 PTT（已稳定），新用户在 onboarding 给一次"试试全双工"的选择

**讨论时机**：技术决策，需要明确"未来 6 个月用户主要用什么形态"

---

### 议题 D — 跨模块数据流：AI 推荐如何真正打通

**现状**：`recommendations_service.py` 已经能从 `blind_spots` 推"补充学习"建议，但跟 `knowledge_service`（Obsidian）、`news_service`（日报）没有真正的内容联动 —— 推荐的"相关笔记"是占位文字。

**影响**：
- "AI 副脑"的差异化定位目前只体现在 dashboard 卡片上
- 用户感知不到"面试 → 知识库 → 日报"的联动价值

**可选路径**：
1. **基于关键词匹配**：把 `blind_spots` 关键词（如"记忆管理"）去 `~/Obsidian/coding/` 全文搜，返回 top-3 笔记
2. **基于 embedding**：`blind_spots` + 笔记标题/内容 embedding → 向量检索 → top-k
3. **基于知识图谱**：从 `blind_spots` 对应的 topic 出发，wikilink 遍历 1 跳，推荐相关笔记

**讨论时机**：差异化价值，需要先想清楚"用户能感知到的跨模块体验是什么"

---

### 议题 E — AI Agent 框架：现在的"假 LangGraph"要不要换

**现状**：
- `interview_graph.py` 编译了图但运行时绕开
- `followup_agent` / `evaluate_agent` / `report_agent` 都是**直接调 LLM**（langchain `ChatOpenAI.ainvoke`）
- 没有 multi-agent 协作、tool use 链、反思机制

**影响**：
- 未来要做"AI 自己出题 / 自动评估代码 / 模拟面试官间讨论"，需要更强的 agent 框架
- 当前 `evaluate_agent` 是一次性 LLM 调用，没有 RAG、没有反思、没有结构化输出校验（LLM JSON 解析靠正则 fallback）

**可选路径**：
1. **继续 LangGraph 1.x**：把现有的 graph 真用起来，加节点、加 tool、加 human-in-the-loop
2. **换 LangGraph 2.x / LangChain 1.3+ 的 create_agent API**：声明式、build-in 工具多
3. **引入 CrewAI / AutoGen**：多 agent 协作（一个出题、一个评估、一个出报告）

**讨论时机**：3-6 月后的扩展计划，MVP 阶段不必急

---

### 议题 F — 可观测性：零 trace / metrics / structured log

**现状**：
- 所有日志走 `logging.getLogger("knockwise.xxx")` + print
- 没有 trace 关联（一次 request 跨多服务/agent 怎么串起来）
- 没有 metrics（LLM 调用次数、token 消耗、STT 延迟、报告生成耗时）
- 没有 error 聚合（Sentry / GlitchTip 都没接）

**影响**：
- 上线后出问题只能靠用户报
- LLM 成本不可见（每次 evaluate 调几次？多少 token？）
- Agent 行为不可调试（某次面试追问为什么跑偏了？）

**可选路径**：
1. **轻量**：本地 `json_log` + Loki / Grafana 聚合
2. **中等**：OpenTelemetry SDK + Jaeger + Prometheus
3. **AI 专用**：Langfuse / Helicone（专门给 LLM 调用打 trace + 算成本）

**讨论时机**：上线前必须做，可以分阶段引入

---

## 二、已发现 bug（待修复）

### Bug 9 — SM-2 测试与函数签名不一致 🔥 NEW 2026-06-25

**位置**：`backend/tests/test_sm2.py` vs `backend/services/learning_progress_service.py:52`

**症状**：
- `pytest tests/test_sm2.py` → **10 failed, 82 passed**
- 错误：`TypeError: calculate_next_srs() got an unexpected keyword argument 'repetition_count'`

**根因**：
- 函数签名用 `review_count`（参数名 + dict key + DB 字段名）
- 测试用 `repetition_count`（参数名 + dict key）
- 不匹配

**修复方向**：
- ✅ 改测试 → 用 `review_count`（与函数/DB 一致，无迁移）
- ❌ 改函数 → 要 DB 迁移 + 影响所有调用方

**影响文件**：
- `backend/tests/test_sm2.py`（改测试）

**优先级**：🔴 高（阻塞 pre-commit hook）

---

## 三、已识别的技术债务

### 债务 8 — `question_progress.user_id` 去掉 FK，应用层保证引用完整性 ⚠️ NEW

**位置**：`backend/models/__init__.py:QuestionProgress`

**背景**：Phase 1a 启用 HASH 分区 (按 user_id 散 16 partition)。MySQL 8 分区表不允许 FK（无论作为父表还是子表），所以从 `QuestionProgress.user_id` 移除了 FK 约束。

**影响**：
- 删除 user 时不会 cascade 清 question_progress 行 → 孤立行
- 当前没有 User.delete API，暂时不痛
- 但如果有 batch data fix / GDPR 删除需求，需要手动写清理逻辑

**建议**：建一个 `UserService.delete_user(user_id)` 方法，应用层清：
```sql
DELETE FROM question_progress WHERE user_id = ?;
DELETE FROM question_tags WHERE user_id = ?;
DELETE FROM user_questions WHERE user_id = ?;
-- ... 其他子表
```

**优先级**：低（上线前要写）

---

### 债务 1 — 数据库缺少复合索引 ⚠️

**位置**：`backend/models/__init__.py` 的 Interview / QuestionRecord

**问题**：
- `interviews` 表有 100+ 行后，`WHERE user_id=? AND status=? AND deleted_at IS NULL` 全表扫
- `question_records` 没有 `(interview_id, created_at)` 复合索引
- JSON 字段（`state_snapshot` / `radar_data`）无全文检索索引

**建议**：
```sql
ALTER TABLE interviews ADD INDEX idx_user_status (user_id, status, deleted_at);
ALTER TABLE question_records ADD INDEX idx_interview_created (interview_id, created_at);
```

**优先级**：中（数据量 < 10k 之前不痛）

---

### 债务 2 — `start_interview` 去重是应用层做的 ⚠️

**位置**：`backend/api/interview.py:241-280`（之前修过 dedup 那个 bug）

**现状**：dedup 逻辑在 Python 层 `SELECT ... LIMIT 1`，并发情况下两个请求同时跑会双 INSERT（因为没有 unique constraint）。

**建议**：
```sql
ALTER TABLE interviews ADD CONSTRAINT uniq_user_inprogress
  UNIQUE (user_id, round, style) /* 仅当 status='in_progress' */;
```
但 MySQL 不支持部分 unique index，需要用 generated column 或业务约束。

**优先级**：低（单用户并发点击的概率小，但严格说应该做）

---

### 债务 3 — 测试覆盖几乎为零 ⚠️

**位置**：`backend/tests/` 目录存在但稀疏

**现状**：从 `git log` 看项目里几乎没有单元测试，E2E 全靠手动 curl。

**建议优先级**：
1. 核心 service 单测（`interview_service.process_answer`、`report_agent.generate_report`）
2. API contract 测试（OpenAPI snapshot）
3. E2E happy path 1-2 个

**优先级**：中（重构前必做，否则改完没信心）

---

### 债务 4 — 无 Alembic，迁移全靠 `_MIGRATIONS` 启动 ALTER ⚠️

**位置**：`backend/core/database.py:_MIGRATIONS`

**现状**：每加一列手动 append，schema drift 风险（多人开发时本地 SQL 不一致）。

**建议**：用 Alembic（之前评估过，工时 ~0.5 天）。

**优先级**：低（单人项目不痛，但多协作者/多环境部署前必做）

---

### 债务 5 — 邮箱 + 密码哈希用 stdlib `hashlib.pbkdf2_hmac` 而非 bcrypt/argon2 ⚠️

**位置**：`backend/api/auth.py` 注册路径

**现状**：注释说"零依赖"所以选 stdlib。PBKDF2 是 OK 的，但 PBKDF2-SHA256 调 600K 次的官方建议很多库还没跟进。

**建议**：换 argon2-cffi（更现代、内存硬度好），或显式把 PBKDF2 iterations 调到 600000+。

**优先级**：低（生产前要改）

---

### 债务 6 — 知识库的 vault 路径硬编码 `~/Obsidian/coding/` ⚠️

**位置**：`backend/services/obsidian_service.py:14`

**现状**：路径写死 `Path.home() / "Obsidian" / "coding"`，多 vault / iCloud 同步 / Windows 用户都没法用。

**建议**：写到 `core/config.py` 的 `OBSIDIAN_VAULT_PATH`，从 `.env.local` 读。

**优先级**：低（当前用户用 Mac + 单 vault，不痛）

---

### 债务 7 — 启动时预热 STT 75MB 模型，加载慢 ⚠️

**位置**：`backend/main.py:_warm_stt` + `backend/voice/stt.py:_load_model`

**现状**：后端启动时会下载 + 加载 faster-whisper tiny，第一次启动 + 每次冷启慢。

**建议**：
- 预下载到 `backend/voice/models/` 打包
- 启动失败时不阻塞（已经在做了：`try/except logger.warning`）
- 改成 lazy 加载：第一次 `/api/interviews/transcribe` 时再加载

**优先级**：低

---

## 四、已完成的修复（历史归档）

| 修复 | 时间 | 链接 |
|---|---|---|
| SQLite PRAGMA → MySQL 兼容的迁移 | 2026-06-17 | commit `core/database.py` |
| `start_interview` 同 (user/round/style) 去重 | 2026-06-17 | commit `api/interview.py` |
| `record.question_id` 缺失导致 `total_questions=0` | 2026-06-17 | commit `api/interview.py` |
| 报告生成从全 3 stub 改调真 `ReportAgent` | 2026-06-17 | commit `api/report.py` |
| `get_backlinks` 模糊匹配（去空格） | 2026-06-17 | commit `obsidian_service.py` |
| React StrictMode 双触发防护 | 2026-06-17 | commit `interview/room.tsx` `interview.tsx` |
| 文档英文名 → 中文名 + 合并重构方案 | 2026-06-18 | `docs/` git mv |
| Alembic 启动 ALTER 自动跑 | 2026-06-17 | `core/database.py:_MIGRATIONS` |

---

## 五、讨论记录区

> 每次讨论某个议题后，把结论记在这里。格式：
> ```
> ### [YYYY-MM-DD] 议题 X — 结论
> **决定**：
> **行动项**：
> **影响文件**：
> ```

### [2026-06-25] Bug 9 — SM-2 测试与签名不一致 — 结论

**决定**：改测试，从 `repetition_count` 改为 `review_count`（与函数签名 / DB 字段一致，无需迁移）。

**行动项**：
1. `test_sm2.py` 全文 `repetition_count` → `review_count`（一次性 replace_all）
2. 跑 `pytest tests/test_sm2.py -v` 验证 10 个测试全绿
3. pre-commit hook 应该自动跑过（如果不通过 → 排查）
4. commit 前缀：`fix(sm2): 测试对齐函数签名`

**影响文件**：
- `backend/tests/test_sm2.py`（改）
- `docs/40-追踪/目前缺陷.md`（本文档登记）
