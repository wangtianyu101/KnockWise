# Spec 规格（议题 A + B + C + 债务 1 合并）

> **调研引用**：[research.md](research.md)（§ 3 重构方案 + § 4 风险评估 + § 5.1 推荐分组）
>
> **覆盖范围**：🔴 高优先级 4 个议题（A + B + C + 债务 1）
>
> **不在本 spec 范围**：议题 D（🟡 中）/ 议题 F（🟡 中）/ 🟢 低优先级债务 2-8
>
> **上游决策（详见 research.md § 5.3）**：
> - 议题 C 语音架构：默认推荐"全力全双工"（启用 LiveKit 客户端 + 整合 worker），待用户拍板
> - 议题 B 拆分路径：默认推荐"按职责拆"（interview_lifecycle / interview_runtime / interview_query 三文件）

---

## § 0 上游引用

- **调研报告**：[`research.md`](research.md)（§ 3 重构方案含 5 个议题对比表 + § 4 风险评估含 8 个风险点 + § 5.1 推荐分组）
- **关键风险**（🔴）：
  - 议题 A 与 E 强耦合（必须联合实施）
  - 议题 C 当前 `livekit_worker.py` 是 dead code，worker 永远阻塞
  - 议题 F trace_id 并发 race（不在本 spec 范围但相关）
  - 债务 1 `interview_service.py:45` 注释声称已加 `idx_user_status` 实测不存在（虚假注释）

---

## 1. 用户故事

### U-1：全双工实时语音体验
> 作为 KnockWise 模拟面试候选人，我想要 AI 面试官**实时打断**我并追问，这样练习更接近真实面试体验（不再是"说完一段 → 等 AI 评"的 PTT 模式）。

### U-2：实时 transcript
> 作为 KnockWise 候选人，我想要看到 transcript **实时滚动**，这样我能在嘈杂环境或没戴耳机时也能跟上 AI 追问内容。

### U-3：AI 评估稳定可信
> 作为 KnockWise 候选人，我想要 AI 面试官**正确评估**我的答案（不再因 LLM 输出格式变化导致 parse 失败），这样报告分数稳定可信。

### U-4：LangGraph 状态一致性
> 作为开发者，我想要 LangGraph StateGraph **真用起来**（不再 dead code），这样未来加新节点只需改 graph 不需改 service。

### U-5：拆分 interview.py 提升可维护性
> 作为开发者，我想要 `interview.py` 873 行拆成 **3 个职责清晰的文件**，这样改动一处不会影响别处，单测也能隔离。

### U-6：list_recent_interviews 性能
> 作为开发者，我想要 `list_recent_interviews` **走索引扫描**（不再全表扫），这样用户有 100+ 行 interview 时查询仍 P95 < 200ms。

---

## 2. 验收标准

### Requirement: 全双工实时语音
The system SHALL 在 `/interview/room` `/interview/setup` `/interview.tsx` 三个路径上提供 LiveKit 实时语音对话，废弃 PTT 路径。

#### Scenario: 房间页实时语音连接
- **Given** 候选人进入 `/interview/room`（已选好题目）
- **When** 页面加载 1.5s 内
- **Then** LiveKit 客户端自动 `Room.connect()` 加入房间
- **And** 候选人看到实时波形动画 + AI avatar
- **And** AI 面试官主动开口追问（不需要候选人触发）

#### Scenario: PTT 路径废弃
- **Given** 候选人用 `VoiceRecord` 或 `VoiceRoom` 组件
- **When** 候选人发起语音输入
- **Then** 系统拒绝并提示「请使用实时语音模式」
- **And** 前端 console 显示"VoiceRecord/VoiceRoom 已废弃"

#### Scenario: VAD/turn-taking 自然切换
- **Given** 候选人连续说话 5s 后停顿 0.5s
- **When** VAD 检测到 speech end
- **Then** AI 面试官立即接话追问（延迟 < 500ms）
- **And** transcript 实时显示双方对话

#### Scenario: LiveKit 服务断连
- **Given** 候选人在实时语音进行中
- **When** LiveKit 服务掉线（30s 内）
- **Then** 前端 toast 显示「实时语音断连，正在重连」
- **And** 自动尝试重连 3 次（指数退避 1s/2s/4s）
- **And** 重连失败 → 提示「请检查网络后重试」并保留 transcript 历史

#### Scenario: transcript 实时滚动
- **Given** 实时语音进行中
- **When** AI 面试官说完一句
- **Then** 1s 内 transcript 出现新文本
- **And** transcript 自动滚动到最新一行

---

### Requirement: LangGraph StateGraph 真用起来
The system SHALL 让 `interview_service` 通过 `graph.ainvoke` 调用 LangGraph StateGraph，状态变更走节点 reducer 而不是 service 内手工 mutate。

#### Scenario: get_next_question 走 graph 节点
- **Given** 候选人请求下一题
- **When** `interview_service.get_next_question(session_id)` 被调用
- **Then** 内部调 `graph.ainvoke(state, config)` 而非直接调 `question_engine`
- **And** graph 节点 `select_question` 真被执行（单测覆盖）
- **And** `state["current_question_id"]` 由 graph reducer 维护

#### Scenario: process_answer 走 graph 节点
- **Given** 候选人提交答案
- **When** `interview_service.process_answer(...)` 被调用
- **Then** 内部调 `graph.ainvoke(state, config)`
- **And** graph 节点 `evaluate` → `followup` 顺序执行
- **And** `state["blind_spots"]` / `state["current_depth"]` 由 graph reducer 维护

#### Scenario: 测试不再用 MagicMock 替代 build_interview_graph
- **Given** `tests/test_interview_service.py` 现有 fixture
- **When** 单测跑 pytest
- **Then** `MagicMock` 不再用于 `build_interview_graph`
- **And** 真 graph 跑通（MemorySaver 检查点 + 节点真实执行）

---

### Requirement: LLM 结构化输出
The system SHALL 让 `evaluate_agent` 和 `report_agent` 使用 `with_structured_output(SomePydanticModel)` 替代 `re.search` 正则 fallback。

#### Scenario: evaluate_answer 结构化输出
- **Given** 候选人答案文本
- **When** `evaluate_agent.evaluate_answer(...)` 被调用
- **Then** 使用 `ChatOpenAI(...).with_structured_output(EvaluateSchema)`
- **And** 返回值是 `EvaluateSchema` Pydantic 实例（不是 dict）
- **And** Pydantic 校验失败时显式抛 `ValidationError` 而非 `try/except fallback`

#### Scenario: generate_report 结构化输出
- **Given** 面试结果记录
- **When** `report_agent.generate_report(...)` 被调用
- **Then** 使用 `with_structured_output(ReportSchema)`
- **And** 返回值是 `ReportSchema` Pydantic 实例
- **And** `radar_data` 维度严格 = 11 个 SKILL_CATEGORIES（不会因 LLM 自由发挥而漏维度）

#### Scenario: Pydantic 校验失败边界
- **Given** LLM 输出字段缺失或类型错误
- **When** Pydantic schema 校验
- **Then** 抛 `ValidationError` 含具体字段错误
- **And** 单测覆盖该边界（happy + invalid + edge 各 1）

---

### Requirement: interview.py 按职责拆分
The system SHALL 把 `backend/api/interview.py`（873 行 13 端点）拆为 3 个文件：`interview_lifecycle.py` / `interview_runtime.py` / `interview_query.py`，按 Lifecycle / Runtime / Query 职责分组。

#### Scenario: 拆分后 13 端点归属
- **Given** 拆分 PR 完成
- **When** 跑 `ls backend/api/interview_*.py`
- **Then** `interview_lifecycle.py` 含 4 端点：POST / + POST /complete + POST /{id}/favorite + DELETE /{id}
- **And** `interview_runtime.py` 含 5 端点：POST /{id}/next-question + POST /records/{id}/answer + POST /voice/respond + POST /transcribe + POST /livekit-token
- **And** `interview_query.py` 含 4 端点：GET / + GET /recent + GET /{id} + GET /{id}/records

#### Scenario: 拆分后 13 端点单测覆盖
- **Given** 拆分 PR 完成
- **When** 跑 `pytest backend/tests/api/test_interview_*.py -v`
- **Then** 13 端点每个至少 1 happy-path 单测（13/13 全绿）
- **And** 当前 `test_interview_service.py` 的 MagicMock fixture 拆分为对应文件 fixture

#### Scenario: 拆分后无回归
- **Given** 拆分 PR 完成
- **When** 端到端跑 13 端点 curl
- **Then** 13 端点全返回正确 status code + response body（与拆分前一致）
- **And** `grep -rn "from api.interview import" backend/api/` 仅命中 `main.py`（无反向依赖）

---

### Requirement: 复合索引
The system SHALL 在 `interviews` 表加 `idx_user_status` 索引，在 `question_records` 表加 `idx_interview_created` 索引，让 `list_recent_interviews` 走索引扫描而非全表扫。

#### Scenario: idx_user_status 加索引
- **Given** MySQL 8 启动
- **When** `_run_migrations()` 执行完成
- **Then** `SHOW INDEX FROM interviews WHERE Key_name='idx_user_status'` 返回 1 行
- **And** EXPLAIN SELECT * FROM interviews WHERE user_id=? AND status=? AND deleted_at IS NULL 显示用索引（type=ref）而非 ALL

#### Scenario: idx_interview_created 加索引
- **Given** MySQL 8 启动
- **When** `_run_migrations()` 执行完成
- **Then** `SHOW INDEX FROM question_records WHERE Key_name='idx_interview_created'` 返回 1 行
- **And** EXPLAIN SELECT * FROM question_records WHERE interview_id=? ORDER BY created_at DESC 显示用索引

#### Scenario: 修虚假注释
- **Given** `services/interview_service.py:45` 注释
- **When** 加索引 PR 完成
- **Then** 注释改为「走 idx_user_status 索引（本 PR 新增，research.md 已核验）」
- **And** `models/__init__.py:49` 注释 "bcrypt hash" 改为 "pbkdf2-sha256 hash"
- **And** `voice/stt.py:1-3, 28` docstring 说 faster-whisper 实为 openai-whisper

---

## 3. 边界条件

### 3.1 空值 / 异常 / 并发（基础）
- **空值**：`LiveKitTokenRequest` 缺 `room_name` → 422 ValidationError · `EvaluateSchema` 缺 `score` → Pydantic 抛 ValidationError · Index DDL 缺表名 → migration 抛
- **异常**：LiveKit 服务掉线 → 自动重连 3 次（指数退避 1s/2s/4s）· 失败后保留 transcript 历史
- **并发**：`list_recent_interviews` 并发 100 QPS → 走 idx_user_status 索引 P95 < 200ms · LiveKit 房间同一 `session_id` 不允许多客户端并发连接

### 3.2 时序（顺序依赖）
- **拆分 interview.py 时序**：`interview_lifecycle.py` → `interview_runtime.py` → `interview_query.py` 顺序 PR（每 PR 独立可回滚）· 不一次性拆
- **加索引时序**：先 `idx_user_status`（高频查询）再 `idx_interview_created`（历史记录）
- **LangGraph 真用起来时序**：先 PR 1（`evaluate_agent` `with_structured_output`）+ PR 2（`report_agent` `with_structured_output`）+ PR 3（`interview_service` 调 `graph.ainvoke`）· 不一次性改

### 3.3 安全 / 权限
- **LiveKit token**：JWT 签名 + 1h 过期 · 只有 `livekit-token` API 签发 · 不在前端硬编码 token
- **Pydantic schema 校验**：拒绝注入字段（LLM 输出额外字段被 Pydantic 忽略）
- **数据库迁移**：`_run_migrations()` 用 IF NOT EXISTS · 不破坏现有数据

### 3.4 性能 / QPS
- **LiveKit 实时语音延迟**：客户端 → 服务端 → 客户端 P95 < 800ms（包含 ASR + LLM + TTS）
- **list_recent_interviews**：P95 < 200ms（10k 行数据）
- **VAD 检测延迟**：speech end → AI 追问 < 500ms

### 3.5 兼容性 / 版本
- **LangGraph 1.x API 保持**：不升级到 LangGraph 2.x / `create_agent`（议题 E 决策 = 不升级）
- **Pydantic schema 向后兼容**：`EvaluateSchema` 新增字段为 Optional，旧数据不破坏
- **MySQL 8 分区表保留**：`QuestionProgress.user_id` 仍无 FK（债务 8 暂缓）

### 3.6 国际化
- **transcript 中文支持**：实时 ASR 走中文模型（whisper-large-v3-turbo 或阿里云 ASR）
- **AI 面试官语种**：默认中文（与 KnockWise V3 一致）

### 3.7 Scenario 4 类场景覆盖检查
- ✅ Happy path：每 Requirement ≥ 1 个
- ✅ Invalid input：Pydantic 校验失败 / LiveKit token 缺字段
- ✅ Edge / 边界值：transcript 1s 内出现 / LiveKit 断连 30s 内重试 3 次
- ✅ Failure / 异常路径：LiveKit 断连 / Pydantic ValidationError / 拆分后无回归

---

## 4. 数据契约

### 4.1 LiveKit token API（Pydantic BaseModel）

```python
class LiveKitTokenRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=64)  # 业务：面试 session_id
    participant_identity: str = Field(min_length=1, max_length=64)  # 业务：user_id
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)  # 业务：1h 过期

class LiveKitTokenResponse(BaseModel):
    token: str  # 业务：JWT 签名
    url: str = Field(default="wss://livekit.example.com")
    expires_at: datetime
```

### 4.2 LangGraph InterviewState（TypedDict Schema）

```python
class InterviewState(TypedDict):
    session_id: str
    user_id: str
    current_question_id: Optional[str]
    questions_asked: Annotated[List[str], operator.add]  # reducer
    blind_spots: Annotated[List[str], operator.add]
    current_depth: int
    interview_phase: Literal["intro", "main", "followup", "wrap_up"]
    transcript: Annotated[List[Dict[str, str]], operator.add]  # [{role, content, ts}]
```

### 4.3 EvaluateSchema (Pydantic BaseModel)

```python
class EvaluateSchema(BaseModel):
    score: int = Field(ge=1, le=5)  # 业务：1-5 分
    blind_spots: List[str] = Field(max_length=5)  # 业务：最多 5 个盲点
    depth: int = Field(ge=1, le=3)  # 业务：追问深度 1-3
    feedback: str = Field(max_length=500)
```

### 4.4 ReportSchema (Pydantic BaseModel)

```python
class RadarData(BaseModel):
    dimension: Literal[
        "tech_fundamentals", "system_design", "coding",
        "communication", "problem_solving", "experience",
        "leadership", "learning_agility", "domain_knowledge",
        "engineering_practice", "ai_awareness"  # 11 个 SKILL_CATEGORIES
    ]
    score: int = Field(ge=1, le=5)

class ReportSchema(BaseModel):
    overall_score: float = Field(ge=1.0, le=5.0)
    radar_data: List[RadarData] = Field(min_length=11, max_length=11)  # 业务：必须 11 维度
    strengths: List[str] = Field(max_length=3)
    weaknesses: List[str] = Field(max_length=3)
    summary: str = Field(max_length=1000)
```

### 4.5 复合索引 DDL（Schema）

```sql
ALTER TABLE interviews
  ADD INDEX idx_user_status (user_id, status, deleted_at);

ALTER TABLE question_records
  ADD INDEX idx_interview_created (interview_id, created_at);
```

### 4.6 副作用
- **DB**：`interviews` / `question_records` 加索引（IF NOT EXISTS）
- **LiveKit**：启用 `livekit_worker.py`（不再 dead code）· `frontend/components/LiveKitVoice.tsx` 在三页面被引用 · 删除 `frontend/lib/livekit.ts`（无引用）
- **代码注释**：`interview_service.py:45` / `models/__init__.py:49` / `voice/stt.py:1-3,28` 修虚假注释
- **废弃**：PTT 组件 `VoiceRecord` / `VoiceRoom`（保留但 console.warn「已废弃」）
- **删除端点**：暂无（livekit-token 端点继续用）

---

## 5. 测试用例

### 单元测试（pytest）

- [ ] TC-1: `test_interview_graph.py` — graph 节点真执行（替换 MagicMock fixture）
- [ ] TC-2: `test_evaluate_agent.py` — `with_structured_output` happy path（5 分）
- [ ] TC-3: `test_evaluate_agent.py` — Pydantic 校验失败边界（score=6）
- [ ] TC-4: `test_report_agent.py` — `with_structured_output` happy path（11 维度）
- [ ] TC-5: `test_report_agent.py` — radar_data 漏维度边界（10 维度 → ValidationError）
- [ ] TC-6: `test_api_interview_lifecycle.py` — 4 端点 happy path
- [ ] TC-7: `test_api_interview_runtime.py` — 5 端点 happy path
- [ ] TC-8: `test_api_interview_query.py` — 4 端点 happy path

### 集成测试

- [ ] TC-9: `test_livekit_e2e.py` — 客户端 Room.connect 成功 + transcript 实时显示
- [ ] TC-10: `test_index_perf.py` — list_recent_interviews 100 QPS P95 < 200ms

### E2E（手测或 Playwright）

- [ ] TC-11: 候选人进入 /interview/room → 1.5s 内连上 LiveKit → AI 主动开口
- [ ] TC-12: VAD/turn-taking 候选人说话停顿 0.5s → AI 追问延迟 < 500ms
- [ ] TC-13: LiveKit 服务断线 → 自动重连 3 次 → 重连失败提示保留 transcript

---

## 5.5 跨文档引用

- ✅ 涉及 schema 变更 → § 2 计划产出 db-design.md（复合索引 DDL）
- ✅ 涉及新/改 API → § 2 计划产出 api-spec.md（13 端点拆分 + LiveKit token）
- ✅ 涉及新组件 → § 2 计划产出 component-spec.md（议题 C 实时语音 UI 组件）
- ✅ 涉及 UI 改动 → § 1 规格产出 design-spec.md（议题 C 全双工 UI 替换）
- ⏸ § 2 计划产出 plan.md（≥ 2 方案对比 + 推荐）

---

## 🎯 硬性 DOD（spec.md 完成必须全过）

- [x] 5 段齐全（用户故事 / Requirement + Scenario / 边界 / 数据契约 / 测试用例）
- [x] Requirement ≥ 1（5 个 Requirement，每个 SHALL 强约束）
- [x] Scenario ≥ 3 条（合计 17 个，覆盖 happy + invalid + edge/failure）
- [x] 数据契约 ≥ 1 schema（5 个：LiveKit Token / InterviewState / EvaluateSchema / ReportSchema / Index DDL）
- [x] 测试场景 ≥ 3 条（13 个 TC）
- [x] §0 上游引用齐全（research.md + 关键决策 + 关键风险）
- [ ] ⏸ 已验收（待用户正式签字）

> ⚠️ 用户验收前不能进 § 2 计划 + 不能进 § 1 设计阶段（design-spec.md + mockup）