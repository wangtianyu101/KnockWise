# Tasks（议题 A+B+C+债务 1 拆分 · § 3）

> **拆分依据**：[plan.md](plan.md) § 1 推荐顺序 + § 5 估时
>
> **CLAUDE.md § 6.5 强制**：完成每个任务 → 立即回写本文件 + 标 commit hash
>
> **CLAUDE.md § 6.7 强制**：每 commit 后开 verifier agent（独立 prompt · 不复用 writer 上下文）

---

## 📋 总览（9 个原子任务 · ≤ 1h AI 工作量/每个）

| T | 任务 | 估时 | 难度 | 依赖 | Requirement | 文件范围 |
|---|---|---|---|---|---|---|
| **T1** | 债务 1 复合索引 + 修虚假注释 | 0.5h | 🟢 易 | 无 | R5 | `backend/core/database.py` · `models/__init__.py` · 4 处注释 |
| **T2.1** | 议题 B · 创建 `interview_lifecycle.py` | 0.75h | 🟡 中 | 无 | R4 | 拆 4 端点（lifecycle）|
| **T2.2** | 议题 B · 创建 `interview_runtime.py` | 1h | 🟡 中 | T2.1 | R4 | 拆 5 端点（runtime · 含 LiveKit token）|
| **T2.3** | 议题 B · 创建 `interview_query.py` | 0.75h | 🟡 中 | T2.2 | R4 | 拆 4 端点（query）· 13 端点单测 |
| **T3.1** | 议题 E · `with_structured_output` 改造 | 1h | 🟡 中 | 无 | R3 | `evaluate_agent.py` + `report_agent.py` |
| **T3.2** | 议题 A · service 接 `graph.ainvoke` | 0.5h | 🟡 中 | T3.1 | R2 | `interview_service.py` |
| **T4.1** | 议题 C · room.tsx 接入 `<LiveKitVoice>` | 1h | 🔴 难 | T2.2 | R1 | `pages/interview/room.tsx` |
| **T4.2** | 议题 C · 删除 `livekit_worker.py` dead code | 0.5h | 🟡 中 | T4.1 | R1 | 删 `backend/voice/livekit_worker.py` |
| **T4.3** | 议题 C · transcript 表 + WS 推送 | 0.5h | 🔴 难 | T4.1 | R1.Scenario 1.5 | `transcript_service.py` + WS 端点 |

**总估时**：6.5h（接近 plan.md 8h 含缓冲）

---

## ✅ 任务清单（check-step.py tasks 校验格式）

- [ ] T1: 债务 1 复合索引 + 修虚假注释（0.5h · 🟢 · 无依赖 · 1 commit）· 对应测试：test_models_index + EXPLAIN 验证索引
- [ ] T2.1: 议题 B 创建 `interview_lifecycle.py`（0.75h · 🟡 · 无依赖 · 1 commit）· 对应测试：test_api_interview_lifecycle 4 端点 happy + 401 + 409
- [ ] T2.2: 议题 B 创建 `interview_runtime.py`（1h · 🟡 · 依赖 T2.1 · 1 commit）· 对应测试：5 端点 happy + 异步 + JWT + Depends 注入
- [ ] T2.3: 议题 B 创建 `interview_query.py` + 13 端点单测（0.75h · 🟡 · 依赖 T2.2 · 1 commit）· 对应测试：query 4 端点 + lifecycle/runtime 已写 + EXPLAIN
- [ ] T3.1: 议题 E `with_structured_output` 改造（1h · 🟡 · 无依赖 · 1 commit）· 对应测试：test_evaluate_agent happy + ValidationError + test_report_agent happy + 10 维度边界
- [ ] T3.2: 议题 A service 接 `graph.ainvoke`（0.5h · 🟡 · 依赖 T3.1 · 1 commit）· 对应测试：test_interview_service graph 节点 + test_interview_graph 真 graph
- [ ] T4.1: 议题 C room.tsx 接 LiveKitVoice（1h · 🔴 · 依赖 T2.2 · 1 commit）· 对应测试：LiveKitVoice 渲染 + nav 状态条 + props 类型 + 视觉对齐
- [ ] T4.2: 议题 C 删 `livekit_worker.py` dead code（0.5h · 🟡 · 依赖 T4.1 · 1 commit）· 对应测试：grep 验证 + interview_room 端到端
- [ ] T4.3: 议题 C transcript 表 + WS 推送（0.5h · 🔴 · 依赖 T4.1 · 1 commit）· 对应测试：WS 连接 + 异步写库 + GET 历史 + 表结构

---

## 🟢 T1 · 债务 1 复合索引 + 修虚假注释

**估时**：0.5h · **难度**：🟢 易 · **依赖**：无
**映射 Requirement**：R5
**commit 边界**：1 commit · message `feat(db): T1 复合索引 + 修虚假注释（议题 audit）`

### 文件范围
- `backend/core/database.py` · `_PHASE1A_INDEX_DDL` 加 2 条 `CREATE INDEX IF NOT EXISTS`
- `backend/services/interview_service.py:45` · 注释 "V1 closure 已加 idx_user_status" → "本 PR 新增，research.md 已核验"
- `backend/models/__init__.py:49` · 注释 "# bcrypt hash" → "# pbkdf2-sha256 hash, nullable for GitHub OAuth users"
- `backend/voice/stt.py:1-3, 28` · docstring "faster-whisper" → "openai-whisper"

### 实施步骤
1. 数据库 `_PHASE1A_INDEX_DDL` 加：`CREATE INDEX IF NOT EXISTS idx_user_status (user_id, status, deleted_at)` + `idx_interview_created (interview_id, created_at)`
2. 修改 3 处注释（搜索替换）
3. 跑 `pytest tests/ -v` · 跑 `EXPLAIN SELECT * FROM interviews WHERE user_id=? AND status=?` 验证索引使用

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: `test_models_index.py` — Index 在 metadata 中有声明
- [ ] TC-2: 启动后端 → `SHOW INDEX FROM interviews` 验证 idx_user_status 存在
- [ ] TC-3: EXPLAIN 验证 SELECT 用索引（type=ref 而非 ALL）

### 验证
- [ ] pytest 全绿
- [ ] `_run_migrations()` 后 SHOW INDEX 验证

---

## 🟡 T2.1 · 议题 B · 创建 `interview_lifecycle.py`

**估时**：0.75h · **难度**：🟡 中 · **依赖**：无
**映射 Requirement**：R4
**commit 边界**：1 commit · message `refactor(api): T2.1 interview_lifecycle 拆分（议题 B）`

### 文件范围
- 新建 `backend/api/interview_lifecycle.py`（200 行）
- 删除 `backend/api/interview.py` 中 lifecycle 部分（约 200 行）

### 实施步骤
1. 从 `interview.py` 提取 4 端点：
   - `POST /` (L269)
   - `POST /complete` (L458)
   - `POST /{id}/favorite` (L196)
   - `DELETE /{id}` (L232)
2. 提取 2 个内联 Pydantic 模型到 `schemas/interview.py`
3. 调整 `from api.interview import router` → `from api.interview_lifecycle import router`
4. 跑 `pytest tests/api/test_interview_lifecycle.py -v`

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: `test_api_interview_lifecycle.py` — 4 端点 happy path
- [ ] TC-2: `test_api_interview_lifecycle.py` — 鉴权失败 401
- [ ] TC-3: `test_api_interview_lifecycle.py` — 状态冲突 409（重复 start / 已 complete）

---

## 🟡 T2.2 · 议题 B · 创建 `interview_runtime.py`

**估时**：1h · **难度**：🟡 中 · **依赖**：T2.1
**映射 Requirement**：R4
**commit 边界**：1 commit · message `refactor(api): T2.2 interview_runtime 拆分（议题 B）`

### 文件范围
- 新建 `backend/api/interview_runtime.py`（300 行）
- 删除 `interview.py` 中 runtime 部分（300 行）

### 实施步骤
1. 从 `interview.py` 提取 5 端点：
   - `POST /next-question` (L373) — 议题 A 实施后用 `graph.ainvoke`
   - `POST /records/{id}/answer` (L562)
   - `POST /voice/respond` (L721)
   - `POST /transcribe` (L673)
   - `POST /livekit-token` (L849) — 议题 C 复用
2. 提取 `_start_voice_worker` / `_stop_voice_worker` helper
3. 用 FastAPI Depends 注入 `_livekit_workers` dict（替换全局 dict）
4. 跑 `pytest tests/api/test_interview_runtime.py -v`

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: 5 端点 happy path
- [ ] TC-2: `voice/respond` 异步处理
- [ ] TC-3: `livekit-token` JWT 签名 + 过期
- [ ] TC-4: `_livekit_workers` Depends 注入

---

## 🟡 T2.3 · 议题 B · 创建 `interview_query.py` · 13 端点单测

**估时**：0.75h · **难度**：🟡 中 · **依赖**：T2.2
**映射 Requirement**：R4
**commit 边界**：1 commit · message `refactor(api): T2.3 interview_query 拆分 + 13 端点单测（议题 B）`

### 文件范围
- 新建 `backend/api/interview_query.py`（200 行）
- 删除 `interview.py` 剩余 query 部分（约 200 行）
- 新建 `backend/tests/api/test_interview_*.py`（13 端点单测）

### 实施步骤
1. 从 `interview.py` 提取 4 端点：
   - `GET /` (L131) — 列出用户面试（用 idx_user_status）
   - `GET /recent` (L116) — 最近面试
   - `GET /{id}` (L341) — 单面试详情
   - `GET /{id}/records` (L360) — 面试答题记录
2. 验证 `grep -rn "from api.interview import" backend/api/` 仅命中 main.py（无反向依赖）
3. 补 13 端点单测（CLAUDE.md § 6.1 · 当前 0 覆盖）

### 单测（CLAUDE.md § 6.1 · 13 端点全测）
- [ ] TC-1: `test_api_interview_query.py` — 4 端点 happy + list 过滤
- [ ] TC-2: `test_api_interview_lifecycle.py` — T2.1 已写
- [ ] TC-3: `test_api_interview_runtime.py` — T2.2 已写
- [ ] TC-4: `EXPLAIN list_recent_interviews` 用 idx_user_status 索引

### 验证
- [ ] 13 端点单测全绿（CLAUDE.md § 6.3 ≥ 80% 覆盖）
- [ ] `grep` 验证无反向依赖

---

## 🟡 T3.1 · 议题 E · `with_structured_output` 改造

**估时**：1h · **难度**：🟡 中 · **依赖**：无（独立于 T2）
**映射 Requirement**：R3
**commit 边界**：1 commit · message `refactor(agents): T3.1 with_structured_output 替代正则 fallback（议题 E）`

### 文件范围
- `backend/agents/evaluate_agent.py`（99 行 → 130 行）
- `backend/agents/report_agent.py`（109 行 → 150 行）
- 新建 `backend/agents/schemas.py`（Pydantic schema）

### 实施步骤
1. 在 `agents/schemas.py` 定义 `EvaluateSchema` + `ReportSchema` + `RadarData`（来自 spec.md § 4）
2. `evaluate_agent.py`:
   ```python
   self.llm = ChatOpenAI(...).with_structured_output(EvaluateSchema)
   # 替换 re.search(r'\{[^{}]*"score"...\}', clean) + try/except fallback
   ```
3. `report_agent.py` 同理
4. 跑 `pytest tests/agents/ -v`

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: `test_evaluate_agent.py` — `with_structured_output` happy path（score=5）
- [ ] TC-2: `test_evaluate_agent.py` — Pydantic 校验失败边界（score=6 → ValidationError）
- [ ] TC-3: `test_report_agent.py` — `with_structured_output` happy path（11 维度）
- [ ] TC-4: `test_report_agent.py` — radar_data 漏维度边界（10 维度 → ValidationError）

---

## 🟡 T3.2 · 议题 A · service 接 `graph.ainvoke`

**估时**：0.5h · **难度**：🟡 中 · **依赖**：T3.1
**映射 Requirement**：R2
**commit 边界**：1 commit · message `refactor(service): T3.2 interview_service 接 graph.ainvoke（议题 A）`

### 文件范围
- `backend/services/interview_service.py`（317 行 → 280 行）
- `backend/tests/test_interview_service.py`（替换 MagicMock fixture）

### 实施步骤
1. `interview_service.get_next_question()` 内调 `graph.ainvoke(state, config)` 替换直接 `question_engine` 调用
2. `interview_service.process_answer()` 内调 `graph.ainvoke(state, config)` 替换直接 `evaluate_agent` + `followup_engine` 顺序调用
3. 删除 `tests/test_interview_service.py` 的 `MagicMock` 替代 `build_interview_graph`（改为真 graph 跑通）
4. 跑 `pytest tests/test_interview_service.py -v` + 跑 `tests/test_interview_graph.py`（真 graph runtime 测试）

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: `test_interview_service.py` — `get_next_question` 走 graph 节点
- [ ] TC-2: `test_interview_service.py` — `process_answer` 走 graph 节点（evaluate → followup）
- [ ] TC-3: `test_interview_graph.py` — 真 graph 跑通（替换 MagicMock fixture）
- [ ] TC-4: state 字段（`questions_asked` / `blind_spots`）由 reducer 维护

---

## 🔴 T4.1 · 议题 C · room.tsx 接入 `<LiveKitVoice>`

**估时**：1h · **难度**：🔴 难 · **依赖**：T2.2（livekit-token 端点）
**映射 Requirement**：R1
**commit 边界**：1 commit · message `feat(frontend): T4.1 room.tsx 接 LiveKitVoice（议题 C）`

### 文件范围
- `frontend/pages/interview/room.tsx`（166 行 → 200 行）

### 实施步骤
1. import `LiveKitVoice` 替代 `VoiceRecord`
2. `room.tsx` L142: `<VoiceRecord ... />` → `<LiveKitVoice ... />`
3. props 调整：`onTranscript/onResponse/onAudio/onError` → `onTranscript/onStateChange`
4. room.tsx L127-131 nav 加 "● LiveKit 已连 · 延迟 Xms · VAD Active" 状态条
5. 跑 `cd frontend && npm test -- --run`

### 单测（CLAUDE.md § 6.1 · 引用已验收 mockup v3）
- [ ] TC-1: `<LiveKitVoice>` 渲染（替代 `<VoiceRecord>`）
- [ ] TC-2: 顶部 nav 显示 LiveKit 连接状态
- [ ] TC-3: props 类型正确（onTranscript/onStateChange）
- [ ] TC-4: 视觉对齐 mockup v3

---

## 🟡 T4.2 · 议题 C · 删除 `livekit_worker.py` dead code

**估时**：0.5h · **难度**：🟡 中 · **依赖**：T4.1
**映射 Requirement**：R1
**commit 边界**：1 commit · message `refactor(voice): T4.2 删 livekit_worker.py dead code（议题 C）`

### 文件范围
- 删除 `backend/voice/livekit_worker.py`（61 行 · dead code）

### 实施步骤
1. `git rm backend/voice/livekit_worker.py`
2. 验证 `interview_room.py`（实际被 spawn 的 worker）功能正常
3. 跑 `pytest tests/voice/ -v` 验证没有引用

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: `grep "livekit_worker"` backend/ 仅命中 `interview_room.py` 引用 + 文档注释
- [ ] TC-2: `interview_room.py` 端到端测试通过

---

## 🔴 T4.3 · 议题 C · transcript 表 + WS 推送

**估时**：0.5h · **难度**：🔴 难 · **依赖**：T4.1
**映射 Requirement**：R1.Scenario 1.5 + R1.Scenario 1.3
**commit 边界**：1 commit · message `feat(transcript): T4.3 transcript 表 + WS 推送（议题 C）`

### 文件范围
- 新建 `backend/services/transcript_service.py`
- 新建 `backend/api/interview_transcripts.py`（WS + GET 端点）
- `backend/core/database.py` 加 `CREATE TABLE interview_transcripts`（按 db-design.md § 6.3）

### 实施步骤
1. `_MIGRATIONS` 加 CREATE TABLE + CREATE INDEX（db-design.md § 6.3 SQL）
2. `transcript_service.py`:
   - `persist(transcript: WSTranscriptMessage)` — 异步写 `interview_transcripts` 表
   - `get_history(interview_id, limit, offset)` — 读历史 transcript
3. WS 端点 `/api/interviews/{id}/transcripts/stream`：
   - 订阅 LiveKit DataReceived → 转发 + 异步 persist
4. GET 端点 `/api/interviews/{id}/transcripts`
5. 跑 `pytest tests/api/test_transcripts.py -v`

### 单测（CLAUDE.md § 6.1）
- [ ] TC-1: WS 连接 + transcript 推送
- [ ] TC-2: transcript 异步写库（race condition）
- [ ] TC-3: GET 历史 transcript · 走 idx_interview_ts 索引
- [ ] TC-4: 表结构 + 索引创建（`_run_migrations()` 后 SHOW INDEX）

---

## 🎯 § 3 拆分 DOD

- [x] 9 个原子任务（每个 ≤ 1h AI 工作量 · T1 0.5h · T2 2.5h · T3 1.5h · T4 2h · 总 6.5h）
- [x] 每个任务一个 commit 边界（CLAUDE.md § 6.5）
- [x] 每个任务映射 Requirement/Scenario + 单测
- [x] 依赖清晰（T1 无依赖 · T2 顺序依赖 · T3 与 T2 并行 · T4 依赖 T2.2）
- [x] 实施顺序（T1 → T2 → T3 → T4 · 从易到难）
- [x] 文件范围明确
- [ ] **用户验收签字**

---

## ⏱ 实施时间线

| 时间 | 任务 | 累计 |
|---|---|---|
| 0:00 | T1 债务 1 复合索引 | 0.5h |
| 0:30 | T2.1 lifecycle 拆 | 1.25h |
| 1:30 | T2.2 runtime 拆 | 2.25h |
| 2:45 | T2.3 query 拆 + 13 端点单测 | 3h |
| 3:00 | T3.1 with_structured_output（与 T2.3 并行） | 4h |
| 4:00 | T3.2 service 接 graph（依赖 T3.1）| 4.5h |
| 4:30 | T4.1 room.tsx 接 LiveKitVoice | 5.5h |
| 5:30 | T4.2 删 livekit_worker.py | 6h |
| 6:00 | T4.3 transcript 表 + WS 推送 | **6.5h 总** |
| 6:30 | verify + commit 回写 tasks.md + retro.md | 8h |

---

## ✍️ 验收区

请回复以下任一：
- **"tasks 验收通过 · 下一步开始实施 T1"** → § 4 实施 T1（债务 1 复合索引）· TDD + commit + verifier
- **"tasks 调 T X"** → 修订具体任务（拆得更细 / 合并 / 估时调整）
- **"再想想"** → 停在 § 3 阶段等讨论