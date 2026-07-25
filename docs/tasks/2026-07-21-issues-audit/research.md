# Issues.md 审计调研报告

> **任务类型**：重构/整理（research-refactor 模板）
> 路径模式：`refactor-6`
> **调研日期**：2026-07-21
> **commit HEAD**：`a038958 docs(milestones): V4 AI 推送模块 entry`
> **调研方法**：5 路 general-purpose Agent 并行核验（议题 A+E / B / C+D / F / 债务 1-8）+ 实证文件读取 + grep 验证
> **产出文件**：`docs/tasks/2026-07-21-issues-audit/research.md`（本文件）

---

## 1. 任务理解

**用户原话**：「分析下文档内的问题 调研」

**AI 复述**：用户要求对 `docs/issues.md` 已登记的所有议题（设计议题 A-F + 技术债务 1-8）做一次**实证审计清账调研**，产出每项议题的：

1. 真实状态（仍存在 / 部分缓解 / 已解决）
2. 关闭条件 checklist（用于配合新加的 `issue-closure-template.md`）
3. 风险等级（🔴/🟡/🟢）
4. 6 步路径建议

**重构目标**（可多选）:

- [x] 可读性（命名 / 结构 / 注释）
- [x] 可维护性（拆文件 / 抽函数）
- [x] 一致性（统一模式 / 风格）
- [x] 可测试性（解耦 / 注入）

**议题编号**：A / B / C / D / E / F + 债务 1-8

**不重构会怎样**：`docs/issues.md` 长期仅含"粗清账标注"，每议题缺关闭条件 checklist；新增的 `issue-closure-template.md` 没有示范用法；调研偏差（5 处）无人对照 file:line 核验。

**自检结论**：复述与 `git diff docs/issues.md` 中已做的"粗清账标注"对齐（议题 A/B/C 加"待讨论"，D/E/F 加"待核验"，Bug 9 移到归档，债务 3 改"🚧 改善中"），但粗清账没逐项给关闭条件 —— 这是本次调研要补的核心。

---

## 2. 现状分析

### 2.1 调研证据（CLAUDE.md § 0.2 通用清单）

- [x] 任务理解：已复述（自检通过）
- [x] 读 `docs/issues.md`：完整 315 行 + 当前 `M` 改动 53 行
- [x] 跑 `git log -10`：HEAD `a038958` · 最近 5 commit 是 V4 AI 推送模块（digest / RSSHub / scheduler / preferences / logger 集成层 T15-T19）
- [x] 跑 `git status`：除 `M docs/issues.md` 等 5 个已修改外，还有 `D docs/templates/research-issue.md` + `?? docs/templates/issue-closure-template.md`（议题关闭模板新增）
- [x] 找到 ≥ 3 相关文件：**实测 11 个核心文件**（interview.py / interview_graph.py / interview_service.py / followup_agent.py / evaluate_agent.py / report_agent.py / recommendations_service.py / livekit_worker.py / interview_room.py / obsidian_service.py / auth.py / stt.py / main.py / core/database.py / models/__init__.py / core/config.py）
- [x] 列出依赖影响：见 § 4 风险评估 + § 5 输出建议
- [x] 风险点带等级：见 § 4 风险评估
- [x] 6 步路径：见 § 5.2 推荐路径

### 2.2 议题核验结果（实证 file:line）

#### 议题 A — 会话状态机：LangGraph StateGraph 写了但没用上

| 项 | 结论 |
|---|---|
| **状态** | ✅ 完全成立（比 docs/issues.md 描述更严重） |
| **核心事实** | `backend/agents/interview_graph.py:174-215` 真编译了 StateGraph（6 节点 + MemorySaver），但 `interview_service.py` 仅 `L122/L279` 调 `build_interview_graph()` 把结果塞 `self._sessions["graph"]`，**全仓零处 `graph.invoke` / `graph.ainvoke`**。Service 实际走直接调用链：`get_next_question` (L134-167) → `question_engine.select_next_question` → 手工 mutate state；`process_answer` (L169-223) → 顺序调 `followup_engine` + `evaluate_agent` → 手工 mutate state。 |
| **测试覆盖** | `tests/test_interview_service.py:65-67` 用 `MagicMock` 替换 `build_interview_graph` —— **等于单测 0 覆盖 graph runtime** |
| **关闭条件 checklist** | ☐ service 真调 `graph.ainvoke(state, config)` 或 `graph.stream(...)`<br>☐ graph 节点状态变更真的被执行到<br>☐ 测试不再用 `MagicMock` 替代 `build_interview_graph`<br>☐ `questions_asked` / `blind_spots` 不再在 graph 外手工维护<br>☐ 单测能证明 `state_snapshot` 与 graph runtime 状态一致 |
| **证据缺口** | 启动服务跑 `/start` → `/next-question` → `/submit-answer` → 在 server log 里塞 `print(graph.get_state(...))` 验证运行时脱钩 |

#### 议题 B — `interview.py` 873 行的拆分

| 项 | 结论 |
|---|---|
| **状态** | ✅ 完全成立 + 现状描述**少列 5 个端点**（调研偏差） |
| **端点清单（实际 13 个，议题 B 只列 8 个）** | Lifecycle：L269 POST / + L458 POST /complete + L196 POST /{id}/favorite + L232 DELETE /{id}<br>Runtime：L373 POST /{id}/next-question + L562 POST /records/{id}/answer + L721 POST /voice/respond + L673 POST /transcribe + L849 POST /livekit-token<br>Query：L131 GET / + L116 GET /recent + L341 GET /{id} + L360 GET /{id}/records<br>Other：L716 VoiceRespondRequest + L844 LiveKitTokenRequest（内联 Pydantic） |
| **对照** | interview.py 873 行 / 13 端点 = 67 行/端点（最稠）；learn.py 567/34 = 17 行/端点；knowledge.py 64/9 = 7 行/端点 |
| **依赖分析** | `grep -rn "from api.interview import" backend/api/` 仅命中 `main.py` —— **无反向依赖，拆分零摩擦**；`voice_ws.py` 通过 HTTP 跨进程调用（协议依赖，非模块依赖） |
| **关闭条件 checklist** | ☐ 选定路径（按职责 / CQRS / 保留单文件）<br>☐ `_livekit_workers` 字典归属（跨文件共享 / FastAPI Depends）<br>☐ 2 个内联 Pydantic 模型搬至 voice 子目录<br>☐ 3 个 helper（`_start_voice_worker` / `_stop_voice_worker` / `_search_clause`）归属<br>☐ 7 个 lazy import 显式化<br>☐ `main.py` router 注册是否引入 `api/__init__.py` 聚合（当前为空文件）<br>☐ 补 interview 端点单测（grep 显示**当前零覆盖**） |
| **证据缺口** | (1) 未跑实际 e2e 验证拆分后无回归；(2) `backend/api/digest/` 是否依赖 interview.py 未深查；(3) 前端是否硬编码了所有 13 个 path 未核对 |

#### 议题 C — 语音架构：3 套并存的最终形态

| 项 | 结论 |
|---|---|
| **状态** | ✅ 完全成立 + **worker 文件名与实际不一致**（重大调研偏差） |
| **前端组件引用矩阵** | `VoiceRoom.tsx` ← `pages/interview.tsx:4/301` · `VoiceRecord.tsx` ← `pages/interview/room.tsx:11/142` · `LiveKitVoice.tsx` ← **零引用** |
| **后端 worker 关键发现** | `livekit_worker.py`（61 行）**从未被代码调用**；实际被 `_start_voice_worker` spawn 的是 `backend/voice/interview_room.py`（300+ 行，自研 pipeline）。两份独立 worker 并存，前者是 dead code。 |
| **资源浪费链** | `/start` → `_start_voice_worker`（subprocess `interview_room.py`）→ worker `await room.connect(...)` → `wait_for_participant()` **永远阻塞**直到 `/complete`。前端 `/interview/room` 走 VoiceRecord（WebSocket ASR/TTS）**从不连 LiveKit 房间**。 |
| **孤儿代码** | `LiveKitVoice.tsx` / `frontend/lib/livekit.ts` / `POST /api/interviews/livekit-token` 全部无调用方 |
| **关闭条件 checklist** | ☐ 调通 LiveKit 客户端（前端 `Room.connect`，当前 `LiveKitVoice.tsx` 存在但无引用）<br>☐ `LiveKitVoice.tsx` 在 `/interview/room` + `/interview/setup` + `/interview.tsx` 中实际使用<br>☐ `livekit_worker.py` 启用 + 与 `_start_voice_worker` 整合（消除两份独立 worker）<br>☐ `_start_voice_worker` 与前端客户端连接时机一致<br>☐ VAD/turn-taking 走 LiveKit built-in<br>☐ transcript 实时显示（上下分栏 UI）<br>☐ 端到端延迟 P95 < 800ms<br>☐ 废弃 PTT 路径（`VoiceRecord` / `VoiceRoom` 标 deprecated 但保留作为 fallback） |
| **证据缺口** | (1) 未跑实际启动验证 worker 是否真"wait_for_participant"阻塞；(2) `livekit-server` docker 服务当前是否启动未验证 |

#### 议题 D — 跨模块数据流：AI 推荐如何真正打通

| 项 | 结论 |
|---|---|
| **状态** | 🟡 部分已成立（**比 docs/issues.md 描述乐观得多**） |
| **主路径真实集成** | `recommendations_service.py:14` `from services.obsidian_service import obsidian` · `:73` `obsidian.search(spot, limit=3)` · `:81-83` 把 `name` / `path` 拼进 `title` / `link` —— **真实联动** |
| **stats 联动** | `:15` `from services.news_service import news_service` · `:126` `news_service.get_code_stats(days=7)` · `:129-142` 用 `total_tokens` / `total_days` 生成 stats 卡 —— **真实联动** |
| **fallback 占位** | `:87-92` —— `obsidian.search()` 返回空时插入硬编码文案「补充学习「{weak_spots[0]}」」+「知识库中暂无相关笔记，建议添加」 |
| **并行实现** | `backend/api/analytics.py:236-281` 暴露独立 `/recommendations` 端点，**不调 `recommendations_service`**，自己写一套 blind_spot 计数 → `{topic, label, frequency, priority}` —— **两套并行逻辑并存** |
| **关闭条件 checklist** | ☐ 删 fallback 占位文案（或改为可观测的"零结果"提示）<br>☐ `analytics.py` /recommendations 端点改调 `recommendations_service`（合并并行实现）<br>☐ 验证 `obsidian.search` 对 weak_spot 关键词的实际召回率（中文分词 / 停用词）<br>☐ 确认前端 `analytics.tsx` 调哪个端点，影响"两套并行"是否被用户感知 |
| **证据缺口** | (1) 未跑 `obsidian.search("记忆管理")` 等真实查询验证召回率；(2) 前端调用端点未确认 |

#### 议题 E — AI Agent 框架：现在的"假 LangGraph"要不要换

| 项 | 结论 |
|---|---|
| **状态** | ✅ 完全成立（"直接调 LLM + 正则 JSON fallback"全部属实） |
| **核心事实** | `followup_agent.py:33-41` `ChatOpenAI(...)` 直接构造；`:144/206` 各一处 `self.llm.ainvoke([SystemMessage, HumanMessage])` · `evaluate_agent.py:77` 单次 `ainvoke` + `re.search(r'\{[^{}]*"score"...\}', clean)` (L84-85) + `try/except` fallback · `report_agent.py:105` 单次 `ainvoke` + `startswith("```")` 拆分 + `_fallback_report` 兜底 (L110-115) · `question_agent.py` **不调 LLM**（纯 Python `random.choice`） |
| **缺失能力** | 全 `backend/agents/` 目录 6 个文件，无 `with_structured_output` / `bind_tools` / 多 agent / supervisor / reflection / RAG |
| **与议题 A 强耦合** | A 不解决（graph 仍 dead code），E 单独换框架只是把"单次 LLM + 正则"换个位置，没有实质升级 |
| **关闭条件 checklist** | ☐ 至少一个 agent 用 `with_structured_output(SomePydanticModel)` 替代 `re.search`<br>☐ 反思 loop（self-critique → revise）或 RAG augmentation<br>☐ LangGraph 真用起来（议题 A 关闭条件）或换 `create_agent` API（任选其一）<br>☐ 单测覆盖"JSON 解析失败 → fallback"边界 + "Pydantic 校验失败"边界<br>☐ 引入多 agent 时同步 cross-agent contract + 可观测性 |
| **证据缺口** | (1) eval set 验证 `re.search` fallback 在 LLM 多说话 / 加 markdown / 中文逗号时的漏掉频率；(2) `report_agent.generate_report` 触发 `_fallback_report` 频率 |

#### 议题 F — 可观测性：零 trace / metrics / structured log

| 项 | 结论 |
|---|---|
| **状态** | 🟡 **部分已成立**（与原描述偏差较大 —— T15-T19 已写脚手架但零调用方） |
| **结构化日志** | `backend/utils/logger.py:38-63` `setup_logger()` 走 JSON（ts/level/trace_id/logger/msg/exc）· **但 73 处 `logger.{info,error,warning,debug}` 仍吃 stdlib 默认 Formatter**（纯文本） |
| **trace_id** | `utils/logger.py:15-35` 定义 `_trace_id` 全局 + `get/set_trace_id()` + `TraceFilter`，**但全仓零调用方**（除自身定义外）· `request_id` / `X-Request` / `correlation_id` 零命中 |
| **metrics** | `utils/logger.py:72-102` `DigestMetrics`（push_total/push_failed/fetch_failures/rsshub_routes_broken/push_latency_ms）+ 模块级 `digest_metrics` 实例 · **但 `grep digest_metrics.` 全仓仅命中定义行本身**（死代码） |
| **error 聚合** | `sentry-sdk` / `sentry` / `glitchtip` / `bugsnag` 全部 0 命中 |
| **middleware** | `main.py` 仅 1 处 `add_middleware` (CORSMiddleware) · `RateLimitMiddleware` 类存在但未注册 · slowapi `app.state.limiter` 但未加 `SlowAPIMiddleware` |
| **并发 race** | trace_id 是**进程级单值**，并发请求会互相覆盖（即便接 middleware 也不安全）—— **关闭前必须改 `contextvars.ContextVar` 或 `LoggerAdapter`** |
| **关闭条件 checklist** | ☐ ASGI middleware 读 `X-Request-ID` → `set_trace_id()` + 响应头回写<br>☐ `setup_logger()` 在 startup 接管所有 `knockwise.*` logger<br>☐ `push_daily()` + `fetch_all_sources` 等埋 `digest_metrics.inc()`<br>☐ 全局未捕获异常 handler 落盘 + 队列上报<br>☐ LLM 调用埋 token / latency counter（evaluate_agent / followup_agent）<br>☐ `test_observability.py` 覆盖 trace_id 注入 / JSON 序列化 / metrics 聚合<br>☐ `RateLimitMiddleware` 真注册 **或** 删除 |
| **证据缺口** | (1) trace_id 并发 race 实测；(2) `DigestMetrics.snapshot()` 该被谁定期 dump；(3) `/api/health` 之外的健康/就绪 endpoint 缺失 |

### 2.3 技术债务核验结果

| 债务 | 标题 | 状态 | 调研偏差 / 关键发现 |
|---|---|---|---|
| **8** | `question_progress.user_id` 去掉 FK | ❌ 仍存在 | `models/__init__.py:181` 无 FK · L174-176 注释明说"应用层保证 referential integrity" · 无 `UserService.delete_user` 函数（全 backend 无） |
| **1** | 数据库缺少复合索引 | ❌ 仍存在 + **虚假注释** | `interview_service.py:45` 注释声称"V1 closure 已加 idx_user_status"——**该索引实测不存在**（`grep idx_user_status` 全仓仅命中这行注释本身）· Interview / QuestionRecord 类都无 `__table_args__` |
| **2** | `start_interview` 去重是应用层做的 | ❌ 仍存在 | `interview.py:286-298` 仍是应用层 SELECT LIMIT 1 · Interview 模型无 `UniqueConstraint` · 12 处 `UniqueConstraint` 均用在其他表 |
| **3** | 测试覆盖需要持续量化 | 🟡 部分 + **数字偏差** | issues.md L217 写"41 / 20"——实测 **29 / 25**（口径不同） · `pyproject.toml` 无 coverage 配置 · `requirements.txt:29` 列了 `pytest-cov>=6.0.0` 但未启用 · 无 `.coverage` / `htmlcov` |
| **4** | 无 Alembic，迁移全靠 `_MIGRATIONS` | ❌ 仍存在 + **半完成** | `requirements.txt:6` 列了 `alembic==1.14.0` 但**代码完全没用**（`grep from alembic` 0 命中） · 无 `backend/alembic/` 目录 · `_MIGRATIONS` 仍 11 条 ALTER |
| **5** | 密码哈希用 stdlib `pbkdf2_hmac` | 🟡 部分缓解 + **虚假注释** | `auth.py:35-39` 已升级 **iterations=600_000**（OWASP 2023 推荐） · 但仍是 stdlib pbkdf2（非 argon2/bcrypt） · `models/__init__.py:49` 注释 "# bcrypt hash" **实际是 pbkdf2**（误导性） |
| **6** | Obsidian vault 路径硬编码 | ❌ 仍存在 | `obsidian_service.py:14` `VAULT_ROOT = Path.home() / "Obsidian" / "coding"` 硬编码 · `core/config.py` 47 行无 `OBSIDIAN_VAULT_PATH` · `grep OBSIDIAN_VAULT_PATH` 全仓 0 命中 |
| **7** | 启动时预热 STT 75MB 模型 | ❌ 仍存在 + **库名错误** | `main.py:163-169` startup `_warm_stt` 仍阻塞 · `voice/stt.py:1-3, 28` docstring 说 "faster-whisper" **实际是 `openai-whisper`**（`import whisper`）· 无预下载到 `backend/voice/models/` |

#### 2.3.1 新增发现（建议追加议题或单独清账）

| # | 类型 | 位置 | 描述 |
|---|---|---|---|
| 新 1 | 虚假声明 | `interview_service.py:45` | 注释"idx_user_status V1 closure 已加"实际不存在 |
| 新 2 | 虚假注释 | `models/__init__.py:49` | `password_hash` 注释 "# bcrypt hash" 实际是 pbkdf2 |
| 新 3 | 虚假注释 | `voice/stt.py:1-3, 28` | docstring/class 说 "faster-whisper" 实际 `import whisper` 是 openai-whisper |
| 新 4 | 半完成依赖 | `requirements.txt:6, 29` | `alembic==1.14.0` + `pytest-cov>=6.0.0` 装了不用 |
| 新 5 | 数字偏差 | `docs/issues.md:217` | "41 / 20" 应改为 "29 / 25"（口径：test_*.py / 排除 node_modules） |

### 2.4 调研偏差修正（自我复盘）

调研过程中发现的 docs/issues.md 与实际不符：

| # | 偏差位置 | docs/issues.md 写 | 实测 |
|---|---|---|---|
| 1 | 议题 B | "8 个端点" | **13 个端点**（漏 /recent, GET /{id}, /transcribe, /voice/respond, /livekit-token） |
| 2 | 议题 C | "LiveKit 服务 / `livekit-worker.py` 启动" | 真正 spawn 的是 `interview_room.py`；`livekit_worker.py` 是 dead code |
| 3 | 议题 D | "推荐的'相关笔记'是占位文字" | 主路径已真集成 obsidian + news；仅 fallback 占位 + analytics.py 重复实现 |
| 4 | 议题 F | "零 trace / metrics / structured log" | T15-T19 已写 `utils/logger.py` 脚手架，但零调用方（"抽屉里的工具盒"） |
| 5 | 债务 3 | "41 个后端 test_*.py + 20 个前端 Vitest" | 实测 **29 / 25**（口径不同） |
| 6 | 债务 5 | "PBKDF2 600K 调官方建议很多库还没跟进" | iterations 已升级到 **600_000**（OWASP 2023 推荐），仅"非 argon2/bcrypt"一点仍成立 |

---

## 3. 重构方案

### 3.1 议题 A — LangGraph 真实接 graph.ainvoke（与议题 E 联合实施）

| 维度 | 方案 A: 保留 service 调用结构，只换 LLM 调用层 | 方案 B: service 改走 graph.ainvoke（推荐） |
|---|---|---|
| **思路** | `evaluate_agent` 换 `with_structured_output` 即可，service 内部仍直接调 | service 真用 `graph.ainvoke(state, config)`，state 由 graph reducer 维护 |
| **改动范围** | 2 文件 / ~30 行 | 4 文件 / ~80 行（含 reducer + 测试替换 MagicMock） |
| **风险等级** | 🟡 中 | 🔴 高 |
| **兼容性** | ✅ 接口不变 | ⚠️ 节点 reducer 顺序影响 state 行为，需全链路测试 |
| **测试影响** | 仅 evaluate_agent 单测 | MagicMock fixture 替换为真 graph runtime 测试 + 单测补覆盖率 |
| **工作量** | 1h | 1.5h（与 E 联合实施） |

### 3.2 议题 B — interview.py 拆分（3 路径对比）

| 维度 | 方案 A: 按职责拆（推荐） | 方案 B: CQRS 拆 | 方案 C: 保留单文件（约定避免互相改） |
|---|---|---|---|
| **思路** | lifecycle / runtime / query 三文件 | 读写分离 + 命令查询独立文件 | 1 文件 + 注释分块 + 加 lint 规则禁止跨块改 |
| **改动范围** | 3 文件 + main.py 注册 | 6 文件 + api/__init__.py 聚合 | 0 文件 |
| **风险等级** | 🟡 中 | 🔴 高 | 🟢 低 |
| **兼容性** | ✅ 接口路径不变 | ⚠️ 需引入聚合层 | ✅ 不变 |
| **测试影响** | 13 端点单测全部补（当前 0 覆盖） | 同 A + 聚合层单测 | 0 |
| **工作量** | 2.5h | 4h | 0h（但债仍存在） |

### 3.3 议题 C — 语音架构收敛（3 路径对比）

| 维度 | 方案 A: 纯 PTT 收敛（删 LiveKit） | 方案 B: 全力全双工（启用 LiveKit） | 方案 C: Hybrid（双轨） |
|---|---|---|---|
| **思路** | 删 `livekit_worker.py` / `LiveKitVoice.tsx` / `/livekit-token`，纯 PTT | 启用 LiveKit 客户端，整合 worker，实时 transcript | LiveKit 主 + PTT 兜底 |
| **改动范围** | 删 3 文件 + 改 1 文件 | 启用 3 dead code + 改 3 文件 + WS 端点 | 双套维护 |
| **风险等级** | 🟢 低 | 🔴 高 | 🟡 中 |
| **兼容性** | ✅ PTT 已能用 | ⚠️ LiveKit 服务依赖 + 端到端延迟 | ✅ 两套并存 |
| **测试影响** | 仅 e2e 回归 | e2e + 延迟测试 + WS 测试 | 双套 e2e |
| **工作量** | 1h | 2h | 3h |

### 3.4 议题 D — recommendations 合并（2 路径对比）

| 维度 | 方案 A: 合并到 recommendations_service（推荐） | 方案 B: 删 fallback 占位即可 |
|---|---|---|
| **思路** | `analytics.py` /recommendations 改调 `recommendations_service`，删本地逻辑 | 仅删 :87-92 占位文案 |
| **改动范围** | 2 文件 / ~50 行 | 1 文件 / ~5 行 |
| **风险等级** | 🟡 中（前端调用端点需确认） | 🟢 低 |
| **兼容性** | ⚠️ 前端可能硬编码 | ✅ 仅后端 |
| **测试影响** | 双套单测合并 | 0 |
| **工作量** | 1h | 0.25h |

### 3.5 议题 F — 可观测性 contextvars 改造（2 路径对比）

| 维度 | 方案 A: contextvars.ContextVar（推荐） | 方案 B: LoggerAdapter |
|---|---|---|
| **思路** | `_trace_id` 改 `contextvars.ContextVar`，ASGI middleware 注入 | 每个 logger 实例包一层 Adapter |
| **改动范围** | logger.py + middleware + 全部 logger 调用点 | logger.py + 全部 logger 调用点 |
| **风险等级** | 🟡 中 | 🟡 中 |
| **兼容性** | ✅ 接口不变 | ⚠️ 调用方需改 |
| **测试影响** | 并发 race 单测 | 并发 race 单测 |
| **工作量** | 1h | 1.5h |

---

## 4. 风险评估

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| 1 | **议题 A 与 E 强耦合**：单独修 E（换框架）只是把"单次 LLM + 正则 JSON"换个位置，必须先解决 A（graph 真用起来）才有实质升级 | 🔴 | A+E 合并成一个实施任务，不单独出 PR |
| 2 | **议题 F trace_id 并发 race**：当前 `_trace_id` 是进程级单值，并发请求会互相覆盖 —— 即便接 middleware 也是 race condition，**关闭前必修** | 🔴 | 用 `contextvars.ContextVar` 替代模块全局 |
| 3 | **议题 C worker 永远阻塞**：`_start_voice_worker` 在 `/start` 无条件启动，但前端从不连 LiveKit → worker 永远 `wait_for_participant()` → livekit-server 资源/算力浪费 | 🔴 | 启用 LiveKit 客户端 + 整合 worker（不再是删 LiveKit 路径） |
| 4 | **议题 B 拆分零摩擦但零测试**：单仓 grep 显示 interview 端点**零单测覆盖**，拆分时无回归兜底 | 🟡 | 拆分 PR 必须配套 ≥ 13 个端点的 happy-path 单测 |
| 5 | **债务 1 虚假注释误导**：`interview_service.py:45` 注释声称已加索引实际未加 —— 后续开发者会信注释写错 DDL | 🟡 | 修注释 + 加索引同步 |
| 6 | **新增虚假注释（bcrypt / faster-whisper）**误导新人 | 🟢 | 一行 commit 改 3 处注释 |
| 7 | **半完成依赖**（alembic / pytest-cov 装了不用）会让 deps 文件与代码长期不一致 | 🟢 | 决策：实施 / 删除 / 标记未来 |
| 8 | **`backend/api/digest/` 未深查是否依赖 interview**：议题 B 拆分可能引入第 4 个跨文件耦合点 | 🟡 | 拆分前补 grep 核验 |

---

## 5. 输出建议

### 5.1 推荐方案

按风险等级分 3 组（建议并行实施）：

**组 1 — 🔴 高优先级（1-2 周）**：

- 议题 A + E 联合：把 `interview_service` 真接 `graph.ainvoke`，至少 1 个 agent 用 `with_structured_output`
- 议题 B：按"按职责拆"路径拆 interview.py 为 `interview_lifecycle.py` + `interview_runtime.py` + `interview_query.py`（方案 A · 最简单）
- 议题 C：方案 B 全力全双工（启用 LiveKit 客户端 + 整合 worker）
- 债务 1：加 `idx_user_status` + `idx_interview_created` + 修虚假注释

**组 2 — 🟡 中优先级（2-3 周）**：

- 议题 D：删 fallback 占位 + 合并 analytics.py `/recommendations`
- 议题 F：trace_id 改 `contextvars.ContextVar` + 接通 `digest_metrics` + LLM token counter + 修 `RateLimitMiddleware` 状态
- 债务 7：删 startup `_warm_stt` 阻塞 + 修 docstring

**组 3 — 🟢 低优先级（生产前）**：

- 债务 2/3/4/5/6/8：用户决策后批量实施
- 4 个新增虚假注释/声明：合并到组 2 PR 顺手修

### 5.2 推荐路径

```
0 调研（本文件完成）
→ 1 规格（议题 A+B+C+债务 1 合并，spec.md 已起草）
→ 2 计划（方案对比 + 推荐 → plan.md + db-design + api-spec + component-spec）
→ 3 拆分（按组拆 ≤ 1h AI 工作量原子任务，见 tasks.md）
→ 4 实现（TDD · 红→绿→refactor→commit；每 commit 必配单测）
→ 5 验证（L3 整合 + L5 staging；每 commit 单元开 verifier agent）
→ 6 复盘（retro.md · 调研偏差 / 流程改进 / memory 候选）
```

### 5.3 关键决策点

- 议题 C 语音架构未来方向：A. 纯 PTT 收敛（删 LiveKit）/ B. 全力全双工 / C. Hybrid — 待用户拍板
- 议题 B 拆分路径：A. 按职责拆 / B. CQRS / C. 保留单文件 — 默认 A
- 债务 4 Alembic 处置：A. 实施 / B. 删依赖 / C. 保留为未来迁移
- 债务 5 密码哈希：A. 换 argon2-cffi / B. 换 bcrypt / C. 接受 600K pbkdf2 + 改注释
- 是否同步更新 docs/issues.md：调研偏差（5 处）是否同步修正
- 是否启动第 2 步计划：3 组（🔴 / 🟡 / 🟢）是否并行 / 串行

### 5.4 调研方法 + 工具

| Agent | 输入 | 输出 | 工具 |
|---|---|---|---|
| Agent 1 | 议题 A + E（LangGraph） | `interview_graph.py` 编译证据 + service 绕过证据 + agent 直接 LLM 证据 + 关闭条件 5 条 | Read, Grep |
| Agent 2 | 议题 B（interview.py） | 13 端点清单 + 分组建议 + 依赖分析（无反向）+ 关闭条件 7 条 + 缺口 5 条 | Read, Grep, Bash |
| Agent 3 | 议题 C + D（语音 + 跨模块） | 组件引用矩阵 + worker 真假分析 + recommendations_service 真实联动分析 + 关闭条件 5+4 条 | Read, Grep, Bash |
| Agent 4 | 议题 F（可观测性） | logger / trace_id / metrics / error 聚合 / middleware 现状 + 7 条关闭条件 + 并发 race 风险 | Read, Grep, Bash |
| Agent 5 | 债务 1-8 全部 | 8 债务逐项状态 + 调研偏差 5 处 + 关闭条件 + 4 新增虚假注释 | Read, Grep, Bash, ls, find |

**总工具调用**：~120 次 Read / Grep / Bash（5 路 Agent 合并）
**调研时长**：~5 分钟（5 路 Agent 并行 wall-clock）
**核验文件数**：≥ 11 个核心文件 + 多个 grep 命中位置

### 5.5 memory 待写清单（CLAUDE.md § 6.6 强制）

调研阶段产出的可沉淀经验：

| 类型 | 候选名 | 内容 |
|---|---|---|
| `feedback` | `issues-audit-truthfulness.md` | docs/issues.md 中"现状描述"必须有 file:line 证据，否则视为调研偏差；本报告发现 6 处偏差 |
| `feedback` | `fake-claims-in-comments.md` | 4 处虚假注释/声明（idx_user_status 已加 / bcrypt / faster-whisper / 半完成依赖）应在 git pre-commit hook 检测"注释声称 X 但代码未实现"模式 |
| `feedback` | `agent-dead-code-detection.md` | 议题 A/C 中 "graph 是 dead code" / "livekit_worker.py 是 dead code" 都是**静态可检测**模式（grep 调用方 + 检查 .invoke() / .connect()） |
| `reference` | `issues-closure-template-usage.md` | 新 `issue-closure-template.md` 要求每议题配 checklist，本报告 § 2 已示范如何写 |
| `project` | `parallel-issues-state-table.md` | 多议题并行核验时，先列状态总览表（✅/🟡/❌ + 风险等级）再写详细分析 |

### 5.6 相关文件路径速查

**议题相关**：

- `backend/agents/interview_graph.py`（215 行）
- `backend/agents/followup_agent.py`（246 行）
- `backend/agents/evaluate_agent.py`（99 行）
- `backend/agents/report_agent.py`（109 行）
- `backend/agents/question_agent.py`（63 行）
- `backend/agents/states.py`（55 行）
- `backend/services/interview_service.py`（317 行）
- `backend/services/recommendations_service.py`（142 行）
- `backend/services/obsidian_service.py`（212 行）
- `backend/services/news_service.py`
- `backend/api/interview.py`（873 行）
- `backend/api/analytics.py`（281 行）
- `backend/voice/livekit_worker.py`（61 行 · **dead code**）
- `backend/voice/interview_room.py`（300+ 行 · 实际被 spawn）
- `backend/voice/stt.py`（177 行）
- `backend/main.py`（含 `_warm_stt` L163-169 / L215-218）
- `backend/utils/logger.py`（含 `setup_logger` / `digest_metrics` / `digest_logger`）
- `frontend/components/VoiceRoom.tsx`
- `frontend/components/VoiceRecord.tsx`
- `frontend/components/LiveKitVoice.tsx`（**零引用**）
- `frontend/lib/livekit.ts`（**零引用**）
- `frontend/pages/interview.tsx`
- `frontend/pages/interview/room.tsx`

**债务相关**：

- `backend/models/__init__.py`（L84-110 Interview · L113-129 QuestionRecord · L174-181 QuestionProgress · L313 QuestionTag · L49 password_hash 注释）
- `backend/core/database.py`（L30-42 _MIGRATIONS · L54-64 _PHASE1A_INDEX_DDL · L67-87 _run_migrations）
- `backend/core/config.py`（47 行 · 无 `OBSIDIAN_VAULT_PATH`）
- `backend/api/auth.py`（L35-39 _hash_password · L41-50 _verify_password）
- `backend/pyproject.toml`（L13-16 pytest 配置 · 无 coverage）
- `backend/requirements.txt`（L6 alembic==1.14.0 · L29 pytest-cov>=6.0.0）

---

## 自检清单

- [x] 重构目标明确（不是"让代码更好"）
- [x] 不重构会怎样有具体痛点
- [x] 调用方清单 ≥ 3 个（用 grep 验证）
- [x] 当前测试覆盖率已查（议题 B 端点 0 覆盖）
- [x] 方案对比 ≥ 2 个，含具体维度（A/B/C 路径对比）
- [x] 推荐方案有引用证据