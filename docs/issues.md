# 目前缺陷与设计议题

> 记录已识别的设计缺陷、技术债务、待讨论议题。**这是动态文档** —— 遇到新发现随时加。
>
> 状态图例：📋 待讨论 · 🚧 进行中 · ✅ 已解决 · ❌ 不会做 · ⚠️ 已知限制
>
> **唯一主账**：任务 `tasks.md` / `retro.md` 或代码 `TODO` 中出现的长期遗留项，必须同步登记到本文；其他文件只能引用，不能成为第二份状态源。
>
> **最近清账**：2026-07-21 · 关闭动作按 [`issue-closure-template.md`](templates/issue-closure-template.md) 核验。
>
> **2026-07-22 决策更新**（同步自 [`research.md` § 八](tasks/2026-07-21-issues-audit/research.md#八用户决策清单不属调研产出需用户拍板)）：
> - ✅ **议题 A + E** 联合实施：service 真调 `graph.ainvoke` + `evaluate_agent` / `report_agent` 用 `with_structured_output`（不升级 LangGraph 框架）
> - 🟡 **议题 B** 默认按职责拆（lifecycle/runtime/query）· 待用户最终确认
> - ✅ **议题 C** 全力全双工（路径 2）：三路径全替换 + transcript+语音 UI + LiveKit built-in VAD
> - 🟡 **议题 D + F** 暂缓，与 🔴 组并行不冲突
> - 🔴 **2026-07-22 新增债务 9**：V4 AI 推送模块存在 **41 个测试空壳被 pytest 计为通过**（详见三、债务 9）· 用户原话「先改两个 P0」

---

## 决策更新（2026-07-22）

> 📌 **决策主账**（按任务独立 · CLAUDE.md § 6.9）：
> - 审计任务：[`docs/tasks/2026-07-21-issues-audit/decisions.md`](tasks/2026-07-21-issues-audit/decisions.md)（议题 A/B/C/D/F · 1-10/15-17）
> - V4 AI 推送：[`docs/tasks/2026-07-17-new-feature-ai-push/decisions.md`](tasks/2026-07-17-new-feature-ai-push/decisions.md)（V4 决策 1/2 = 原审计 13/14 · 已迁）
>
> 本节是简表镜像 · 详细记录请看对应 decisions.md

| # | 决策项 | 选择 | 状态 |
|---|---|---|---|
| 1 | 议题 C 语音架构 | ✅ 全力全双工 | ✅ 已决策 |
| 2 | 议题 B 拆分路径 | 🟡 按职责拆（默认） | 🟡 待最终确认 |
| 3 | 债务 4 Alembic | ⏸ 保留为未来迁移 | ⏸ 暂缓 |
| 4 | 债务 5 密码哈希 | ⏸ 接受 600K pbkdf2 | ⏸ 暂缓 |
| 5 | 同步 issues.md 偏差 | ✅ 是（5 处） | ✅ 已完成 |
| 6 | 启动 § 2 计划 | ⏸ 等用户指令 | ⏸ 待定 |
| 7 | 议题 C 实施范围 | ✅ 全部语音路径（Q1=2） | ✅ 已决策 |
| 8 | 议题 C UI 形态 | ✅ transcript+语音（Q2=2） | ✅ 已决策 |
| 9 | 议题 C VAD 策略 | ✅ LiveKit built-in（Q3=1） | ✅ 已决策 |
| 10 | 进 § 1 规格 | ✅ spec.md + design-spec.md + mockup | ✅ 已决策 |
| 11 | V4 假绿灯处置（债务 9） → [V4 决策 1](tasks/2026-07-17-new-feature-ai-push/decisions.md) | 🔴 **立即修** | 🔴 已决策（执行中） |
| 12 | 债务 3 数字偏差（29 → 41） → [V4 决策 2](tasks/2026-07-17-new-feature-ai-push/decisions.md) | 🔴 **同步修** | 🔴 已决策（执行中） |

---

## 一、设计议题（待深入讨论）

### 议题 A — 会话状态机：LangGraph StateGraph 写了但没用上

**状态**：✅ **2026-07-22 已决策**（与议题 E 联合实施）· 进 § 1 规格 · spec.md 已起草

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

### 议题 B — `interview.py` 873 行的拆分

**状态**：🟡 **2026-07-22 默认决策**：按职责拆（lifecycle/runtime/query） · 待用户最终确认 · spec.md 已起草

**现状**：`backend/api/interview.py` 单文件 873 行，承担了 13 个端点（议题描述列了 8 个，漏算 5 个）：
- Lifecycle：POST / + POST /complete + POST /{id}/favorite + DELETE /{id}
- Runtime：POST /{id}/next-question + POST /records/{id}/answer + POST /voice/respond + POST /transcribe + POST /livekit-token
- Query：GET / + GET /recent + GET /{id} + GET /{id}/records
- Other：2 个内联 Pydantic 模型（VoiceRespondRequest / LiveKitTokenRequest）

`grep -rn "from api.interview import" backend/api/` 仅命中 main.py —— **无反向依赖，拆分零摩擦**。

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

**状态**：✅ **2026-07-22 已决策**：全力全双工（路径 2）+ 全部语音路径替换（`/interview/room` + `/interview/setup` + `/interview.tsx`）+ transcript+语音 UI（上下分栏）+ LiveKit built-in VAD/turn-taking · spec.md 已起草

**现状**：
- `/interview.tsx` → `VoiceRoom.tsx`（旧 PTT + WebSocket）
- `/interview/setup.tsx` → `/interview/room.tsx` → `VoiceRecord.tsx`（新 PTT）
- `LiveKitVoice.tsx` 组件存在但**没有任何页面用**
- `voice/livekit_worker.py`（61 行）**从未被代码调用** —— 实际被 `_start_voice_worker` spawn 的是 `backend/voice/interview_room.py`（300+ 行），前者是 dead code
- `_start_voice_worker` 在 `start_interview` 时无条件启动 LiveKit worker，但前端 `/interview/room` 走 VoiceRecord（WebSocket ASR/TTS）**从不连 LiveKit 房间** → worker 永远 `wait_for_participant()` 阻塞直到 `/complete`
- `frontend/lib/livekit.ts` helper + `POST /api/interviews/livekit-token` 端点都是孤儿代码

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

**状态**：📋 待核验（已有后续模块实施，但尚未逐条对照本议题关闭条件）

**现状**：`recommendations_service.py` 主路径已真实集成 Obsidian + News（不再是占位）：
- L14 `from services.obsidian_service import obsidian` · L73 `obsidian.search(spot, limit=3)` 把 `name` / `path` 拼进 `title` / `link`
- L15 `from services.news_service import news_service` · L126 `news_service.get_code_stats(days=7)` 生成 stats 卡
- 但 L87-92 **fallback 仍是占位文案**（obsidian 召回为空时插入硬编码「补充学习「{weak_spots[0]}」」+「知识库中暂无相关笔记，建议添加」）
- `backend/api/analytics.py:236-281` 暴露独立 `/recommendations` 端点，**不调 `recommendations_service`**，自己写一套 blind_spot 计数逻辑（Counter → `{topic, label, frequency, priority}`）—— **两套并行实现并存**

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

**状态**：✅ **2026-07-22 已决策**：与议题 A 联合实施 · `evaluate_agent` / `report_agent` 用 `with_structured_output` · 不升级 LangGraph 2.x / `create_agent` · spec.md 已起草

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

**状态**：📋 待核验（已有相关设计，尚未验证全链路 trace / metrics / error 聚合）

**现状**：
- 73 处 `logger.{info,error,warning,debug}` 调用，绝大多数仍走 stdlib 默认 Formatter（纯文本）
- T15-T19 commit `96566d8` 在 `backend/utils/logger.py` 落了脚手架：
  - `setup_logger()` JSON formatter（ts/level/trace_id/logger/msg/exc）· `DigestMetrics`（push_total/push_failed/fetch_failures/push_latency_ms）· 模块级 `digest_logger` / `digest_metrics` 实例
- **全代码库零调用方** —— grep `from utils.logger` / `digest_metrics.` / `digest_logger.` 全 backend 0 命中（"抽屉里的工具盒"）
- `request_id` / `X-Request` / `correlation_id` 全仓 0 命中（除 logger.py 自己定义外）
- trace_id 是**进程级单值**（模块全局 `_trace_id`），并发请求会互相覆盖 —— 即便接 middleware 也是 race condition，关闭前必修
- `RateLimitMiddleware` 类存在但未注册 · slowapi `app.state.limiter` 但未加 `SlowAPIMiddleware`
- `sentry-sdk` / `glitchtip` / `langfuse` / `opentelemetry-*` 全部 0 命中

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

当前无已登记且完成证据不足的 Bug。新 Bug 必须写明复现路径、影响、优先级和对应回归测试。

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

### 债务 9 — V4 AI 推送模块存在 41 个测试空壳被 pytest 计为通过 🔴 P0 NEW

**位置**：以下 5 个文件全部位于 V4（`docs/tasks/2026-07-17-new-feature-ai-push/`）模块

**审计来源**：[`KnockWise-测试真实性基线-2026-07-21.md`](~/Documents/Codex/2026-07-21/ai-agent-1-agent-agent-2/outputs/KnockWise-测试真实性基线-2026-07-21.md)（2026-07-21 Codex 双 agent 静态 AST 审计）· 本机 `find backend/tests -name "test_*.py" | wc -l` 递归实测 = **41**（与审计一致）

**背景**：commit `9251fd6` 提交时这些测试在 commit message 就被定义为 **"test stub"**（标题：`test+frontend: T20-T24 + T26 测试 stub + 5 核心组件`），但随后 `tasks.md` / `retro.md` / `milestones.md` 全部标为 ✅ DONE，形成"假绿灯"状态。

**空壳分布**（41 个空壳 + 0 真实测试）：

| 文件 | 测试数 | 全部空壳 | 备注 |
|---|---:|---:|---|
| `backend/tests/api/test_digest_api.py` | 16 | 16 | 15 个纯 `pass` + 1 个 `import + 注释 + pass` |
| `backend/tests/e2e/test_digest_push.py` | 4 | 4 | 全 `pass` |
| `backend/tests/services/test_digest_llm.py` | 4 | 4 | 全 `pass` |
| `backend/tests/services/test_digest_service_unit.py` | 12 | 12 | 全 `pass` + 与真实 Digest 测试**重复** |
| `backend/tests/services/test_rss_fetch.py` | 5 | 5 | 全 `pass` · 12 源 fixture 找不到 |
| **合计** | **41** | **41** | pytest 会全计为通过 |

**额外 3 个弱测试**（不在 41 个内，但建议复核）：
- `test_interview_filters.py::test_status_filter_is_applied` → 准备 Mock 但不调用接口，可认定为假绿灯
- `test_archive_service.py::test_logs_count_when_archived` → 只验"没崩"
- `test_cache.py::test_close_idempotent` → 用"不抛异常"表达幂等

**影响**：
- V4 模块的 "32 个 Tasks 全部完成" 声明不成立（tasks.md T20-T24 / T28-T31 全部 ✅ DONE 但实际无效）
- milestones.md V4 "全部完成" 是统计幻觉
- retro.md "49+ 测试类" 数字混淆（测试类 / 测试函数 / 空壳测试 混算）
- verify.md (`docs/tasks/2026-07-17-new-feature-ai-push/verify.md`) **不存在** · 验证阶段未真正完成
- 邮件真实集成在 retro.md 自己的改进项中仍写"待补"
- 后端当前无 pytest 运行环境（`backend/.venv` 不存在），无法现场验证修复效果

**修复路径**（建议按 § 4 步分批，每任务 1 commit）：
1. **T20 重写**：16 endpoint × happy + invalid + edge 用 `TestClient` + fixture 跑通（约 48 case）
2. **T21 拆分**：删除 `test_digest_service_unit.py` 12 个空壳（与真实测试重复），让 `test_digest_service.py` 12 case + `test_digest_composite_score.py` 23 + `test_digest_push_daily.py` 5 + `test_digest_select_top_n.py` 8 作为真实单测基线
3. **T22 重写**：4 个 LLM mock 测试用 `unittest.mock` 拦截 `ChatOpenAI.ainvoke` + 验证 prompt 含用户偏好 + scope 过滤词
4. **T23 重写**：5 个 RSS mock + 12 源 fixture（实际创建 `backend/tests/fixtures/rss/*.xml`）
5. **T24 重写**：4 个 E2E 用 `TestClient` 跑 `cron → DB → API → email` 全链路（可 mock email）
6. **T28 视觉测试**：创建 `frontend/tests/visual/digest.spec.ts`（spec § 6.7 verify-loop）
7. **T29 E2E**：5 个 Playwright scenario 实跑（已编写但未执行）
8. **T30 RSSHub**：创建 `scripts/deploy-rsshub.sh` + `docker-compose.yml` RSSHub service + `curl http://localhost:1200/juejin/tag/AI` 验证
9. **T31 metrics**：将 `backend/utils/logger.py` 内的 `DigestMetrics` 搬出到独立 `backend/utils/metrics.py` 并暴露接口

**验证手段**：
- 重建 `backend/.venv` 后 `pytest backend/tests --collect-only` 收集所有测试
- `pytest backend/tests/api/test_digest_api.py -v` 跑 16 endpoint 测试
- 跑完用 `pytest --tb=short --cov=backend/services/digest_service --cov-report=term-missing` 输出覆盖率

**优先级**：🔴 **P0（高优工程债务）**——直接影响 V4 模块的可信度与"完成度"声明
**修复工时估算**：约 6-8h AI 工作量（含跑通）
**关联决策**：decisions.md 决策 11 + 12（2026-07-22 新增）
**关联文档**：
- [`docs/tasks/2026-07-17-new-feature-ai-push/tasks.md`](tasks/2026-07-17-new-feature-ai-push/tasks.md)（T20-T31 状态即将同步校正）
- [`docs/tasks/2026-07-17-new-feature-ai-push/retro.md`](tasks/2026-07-17-new-feature-ai-push/retro.md)（标题"实施完成"应改"阶段性实现，验证未完成"）
- [`docs/rules/milestones.md`](rules/milestones.md) V4 状态（"全部完成"应改"核心功能已实现，测试与交付验证修复中"）

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

### 债务 3 — 测试覆盖需要持续量化 ⚠️

**状态**：🚧 改善中

**位置**：`backend/tests/` + `frontend/__tests__/`

**现状（2026-07-22 数字修正）**：递归统计 `find backend/tests -name "test_*.py" -type f | wc -l` = **41 个**（含 `api/` `e2e/` `schemas/` `services/` 4 个子目录），顶层 `ls backend/tests/test_*.py | wc -l` = 29 个 —— 之前 29 数字是顶层漏算。**前端 25 个 Vitest 文件不变**（实测 `find frontend -name "*.test.*" -not -path "*/node_modules/*" | wc -l`）。

⚠️ **关联债务 9**：V4 AI 推送模块的 5 个文件含 **41 个确定空壳测试**（纯 `pass`），pytest 会全计为通过。这部分"覆盖"是虚假绿光，详见三、债务 9。

注：`pyproject.toml` 无 coverage 配置；`requirements.txt:29` 列了 `pytest-cov>=6.0.0` 但未启用；无 `.coverage` / `htmlcov` 文件。

**建议优先级**：
1. 核心 service 单测（`interview_service.process_answer`、`report_agent.generate_report`）
2. API contract 测试（OpenAPI snapshot）
3. E2E happy path 1-2 个
4. **修复债务 9**：V4 41 个空壳测试重写

**优先级**：中（重构前必做，否则改完没信心）

---

### 债务 4 — 无 Alembic，迁移全靠 `_MIGRATIONS` 启动 ALTER ⚠️

**位置**：`backend/core/database.py:_MIGRATIONS`

**现状**：每加一列手动 append，schema drift 风险（多人开发时本地 SQL 不一致）。

**建议**：用 Alembic（之前评估过，工时 ~0.5 天）。

**优先级**：低（单人项目不痛，但多协作者/多环境部署前必做）

---

### 债务 5 — 邮箱 + 密码哈希用 stdlib `hashlib.pbkdf2_hmac` 而非 bcrypt/argon2 ⚠️

**位置**：`backend/api/auth.py:38,46` 注册 / 校验路径

**现状（2026-07-21 清账）**：`_hash_password` / `_verify_password` 已使用 **PBKDF2-SHA256 iterations=600_000**（OWASP 2023 推荐值，原议题的"调到 600000+"建议已落实）。仅剩"非 argon2/bcrypt（内存硬度不足）"一点仍成立。
> 关联虚假注释：`backend/models/__init__.py:49` 注释写 `# bcrypt hash`，实际是 pbkdf2 —— 应改注释（见新增发现，非本议题必修项）。

**建议**：若上线前要进一步硬化，换 argon2-cffi（内存硬度更好）；否则接受 600K pbkdf2 现状并修正误导注释即可。

**优先级**：低（600K 已达标，仅算法选择与注释订正）

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
| Bug 9：SM-2 测试参数 `repetition_count` → `review_count` | 2026-06-25 | commit `7a5a21e` · commit 记录 92 passed；2026-07-21 代码复核一致，当前环境无 pytest 未重复执行 |

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
- `docs/issues.md`（本文档登记）
