---
title: API Spec（议题 B 拆 13 端点 + 议题 C LiveKit token + transcript 推送）
date: 2026-07-22
status: v1 (AI 起草 · 待用户验收)
tags: [api-spec, 2步, refactor-6, FastAPI]
related:
  - plan.md（实施计划）
  - spec.md（业务契约）
  - db-design.md（schema 设计）
  - design-spec.md（设计契约）
  - component-spec.md（组件契约）
---

# API Spec（议题 B 拆 13 端点 + 议题 C LiveKit token + transcript 推送）

> **覆盖范围**：议题 B（按职责拆 interview.py 为 3 文件）· 议题 C（LiveKit token API + transcript 推送 WS）
>
> **不在本 spec 范围**：议题 A（业务契约见 spec.md）· 议题 D / F · 债务 2-8

---

## § 1 概述

按议题 B 决策（决策 2 · 按职责拆 · 默认 🟡 待确认）：
- `interview_lifecycle.py` (4 端点)
- `interview_runtime.py` (5 端点)
- `interview_query.py` (4 端点)

按议题 C 决策：
- LiveKit token 签发 API（已有 `POST /api/interviews/livekit-token` · 复用即可）
- transcript 推送协议（WebSocket / SSE）

---

## § 2 接口清单（按文件分组）

### § 2.1 `interview_lifecycle.py`（4 端点 · 写 / 状态变更）

| 方法 | 路径 | 用途 | 鉴权 |
|---|---|---|---|
| POST | /api/interviews | 创建面试（start） | Bearer |
| POST | /api/interviews/{id}/complete | 完成面试 | Bearer |
| POST | /api/interviews/{id}/favorite | 收藏面试 | Bearer |
| DELETE | /api/interviews/{id} | 删除面试（soft delete）| Bearer |

### § 2.2 `interview_runtime.py`（5 端点 · 运行时操作）

| 方法 | 路径 | 用途 | 鉴权 |
|---|---|---|---|
| POST | /api/interviews/{id}/next-question | 获取下一题 | Bearer |
| POST | /api/interviews/records/{id}/answer | 提交答案 | Bearer |
| POST | /api/interviews/voice/respond | 语音响应（异步）| Bearer |
| POST | /api/interviews/transcribe | 转写音频 | Bearer |
| POST | /api/interviews/livekit-token | 签发 LiveKit JWT | Bearer |

### § 2.3 `interview_query.py`（4 端点 · 查询 / 不改状态）

| 方法 | 路径 | 用途 | 鉴权 |
|---|---|---|---|
| GET | /api/interviews | 列出用户面试 | Bearer |
| GET | /api/interviews/recent | 最近面试（带 idx_user_status）| Bearer |
| GET | /api/interviews/{id} | 单面试详情 | Bearer |
| GET | /api/interviews/{id}/records | 面试答题记录 | Bearer |

### § 2.4 议题 C 新增 · transcript 推送（WS / SSE）

| 方法 | 路径 | 用途 | 鉴权 |
|---|---|---|---|
| WS | /api/interviews/{id}/transcripts/stream | 实时推送 transcript（议题 C）| Bearer + 房间权限 |
| GET | /api/interviews/{id}/transcripts | 拉取历史 transcript | Bearer |

---

## § 3 Request/Response（关键端点）

### § 3.1 POST `/api/interviews`（lifecycle · 创建面试）

```python
class CreateInterviewRequest(BaseModel):
    round: Literal["round1", "round2", "round3"] = "round1"
    style: Literal["standard", "system_design", "algorithm"] = "standard"
    interviewer: Literal["sonnet", "haiku"] = "sonnet"

class CreateInterviewResponse(BaseModel):
    id: str = Field(description="面试 UUID")
    user_id: str
    round: str
    style: str
    status: Literal["in_progress", "completed", "abandoned"]
    started_at: datetime
    # 议题 C：返回 livekit_room_name + token（可选）
    livekit_room_name: Optional[str] = None
    livekit_token: Optional[str] = None

# Error: 422 (参数错) / 401 (鉴权失败) / 409 (重复创建)
```

### § 3.2 POST `/api/interviews/{id}/complete`（lifecycle · 完成面试）

```python
class CompleteInterviewResponse(BaseModel):
    id: str
    status: Literal["completed"]
    completed_at: datetime
    report_id: Optional[str] = Field(None, description="异步生成报告的 ID")
    duration_seconds: int

# Effect: interview.status = 'completed' + 触发 report_agent 生成报告
# Error: 404 (面试不存在) / 409 (已完成 / abandoned 状态不可完成)
```

### § 3.3 POST `/api/interviews/{id}/next-question`（runtime · 获取下一题）

```python
class NextQuestionResponse(BaseModel):
    question_id: str
    content: str
    category: str
    difficulty: Literal["easy", "medium", "hard"]
    sequence: int  # 第几题
    follow_up: Optional[str] = None  # 是否追问树节点

# 议题 A 实施后：内部调 graph.ainvoke(state) → select_question 节点
# Error: 404 (面试不存在) / 409 (面试已完成)
```

### § 3.4 POST `/api/interviews/records/{id}/answer`（runtime · 提交答案）

```python
class SubmitAnswerRequest(BaseModel):
    question_id: str
    content: str = Field(min_length=1, max_length=5000)
    audio_url: Optional[str] = None  # 语音转写后的文本（议题 C）
    transcript_segment: Optional[str] = None  # 议题 C 实时 transcript

class SubmitAnswerResponse(BaseModel):
    record_id: str
    followup_question: Optional[NextQuestionResponse] = None  # AI 追问
    score: int = Field(ge=1, le=5)
    blind_spots: List[str] = Field(max_length=5)
    feedback: str

# 议题 A + E 实施后：graph.ainvoke → evaluate 节点 → with_structured_output(EvaluateSchema)
# Error: 404 / 409 / 422 (答案超长)
```

### § 3.5 POST `/api/interviews/livekit-token`（runtime · LiveKit JWT 签发）

```python
class LiveKitTokenRequest(BaseModel):
    room_name: str = Field(min_length=1, max_length=64, description="面试 session_id")
    participant_identity: str = Field(min_length=1, max_length=64, description="user_id")
    ttl_seconds: int = Field(default=3600, ge=60, le=86400, description="1h 过期")

class LiveKitTokenResponse(BaseModel):
    token: str = Field(description="LiveKit JWT")
    url: str = Field(default="wss://livekit.example.com", description="LiveKit 服务器地址")
    expires_at: datetime

# 业务：JWT 签名 + 1h 过期 · 不在前端硬编码 token
# 错误：401 (未鉴权) / 403 (无权限进该房间) / 404 (面试不存在)
```

### § 3.6 GET `/api/interviews/recent`（query · 最近面试 · 用 idx_user_status）

```python
class RecentInterviewsQuery(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    status: Optional[Literal["in_progress", "completed", "abandoned"]] = None
    offset: int = Field(default=0, ge=0)

class RecentInterviewsResponse(BaseModel):
    items: List[InterviewSummary]
    total: int
    has_more: bool

# 议题 B + 债务 1 实施后：走 idx_user_status 索引 · P95 < 200ms
# 索引：(user_id, status, deleted_at) WHERE deleted_at IS NULL
```

### § 3.7 WS `/api/interviews/{id}/transcripts/stream`（议题 C · transcript 实时推送）

**协议选择**：WebSocket（Full-duplex）+ Keepalive ping

```python
# Client → Server
class WSAuthMessage(BaseModel):
    type: Literal["auth"]
    token: str  # Bearer
    interview_id: str

# Server → Client（LiveKit DataReceived 转发）
class WSTranscriptMessage(BaseModel):
    type: Literal["transcript"]
    speaker: Literal["ai", "user"]
    content: str
    ts: datetime  # 毫秒
    sequence: int  # 单调递增

class WSPongMessage(BaseModel):
    type: Literal["pong"]
    server_ts: datetime

# Server → Client（错误）
class WSErrorMessage(BaseModel):
    type: Literal["error"]
    code: Literal["auth_failed", "room_not_found", "permission_denied", "internal_error"]
    message: str

# Keepalive: 30s ping, 90s 超时
```

**持久化**：服务端在转发给前端的同时，**异步写 `interview_transcripts` 表**（避免 WS 断连丢数据）。

### § 3.8 GET `/api/interviews/{id}/transcripts`（议题 C · 历史 transcript）

```python
class GetTranscriptsResponse(BaseModel):
    items: List[WSTranscriptMessage]
    total: int
    has_more: bool

# 走 idx_interview_ts 索引 · 按 ts 升序
# Error: 404 / 403
```

---

## § 4 错误码（统一约定）

| HTTP | 业务码 | 含义 | 触发场景 |
|---|---|---|---|
| 400 | BAD_REQUEST | 请求参数错 | 非 FastAPI 422 时的兜底 |
| 401 | UNAUTHENTICATED | 未登录 / token 失效 | Bearer 缺失或过期 |
| 403 | PERMISSION_DENIED | 无权限 | 不是自己的面试 / token 房间错 |
| 404 | NOT_FOUND | 资源不存在 | interview_id / record_id 不存在 |
| 409 | CONFLICT | 状态冲突 | start 重复 / complete 已完成 |
| 422 | VALIDATION_ERROR | 参数校验失败 | FastAPI Pydantic 校验失败 |
| 429 | RATE_LIMITED | 限流 | Sentry / GlitchTip 未接前可用 slowapi |
| 500 | INTERNAL_ERROR | 服务端错误 | 异常未捕获 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 | LiveKit 服务掉线 / ASR 不可用 |

**WS 错误**：见 § 3.7 `WSErrorMessage.code`。

---

## § 5 认证

所有端点统一使用 **Bearer JWT**（现有 `getToken()` 机制）：
- Header: `Authorization: Bearer <jwt>`
- Payload: `{ user_id, exp, iat }`
- 过期 24h

WS 鉴权：见 § 3.7 首条 `WSAuthMessage` 携带 token。

---

## § 6 测试（CLAUDE.md § 6.1 强制 · 每 commit 必配）

### § 6.1 单元测试（pytest · 13 端点 + transcript API）

- [ ] TC-1: `test_api_interview_lifecycle.py` — 4 端点 happy + invalid + permission denied
- [ ] TC-2: `test_api_interview_runtime.py` — 5 端点 happy + audio_url 缺失 + transcript_segment 超长
- [ ] TC-3: `test_api_interview_query.py` — 4 端点 happy + list 过滤 + idx_user_status EXPLAIN
- [ ] TC-4: `test_api_livekit_token.py` — JWT 签名 + 过期 + 房间名错
- [ ] TC-5: `test_api_transcripts.py` — WS 连接 + transcript 推送 + 表写入校验

### § 6.2 集成测试

- [ ] TC-6: `test_end_to_end_interview.py` — start → next-q → answer × 5 → complete → report
- [ ] TC-7: `test_livekit_e2e.py` — 客户端 Room.connect + transcript 实时推送 + 表记录
- [ ] TC-8: `test_index_perf.py` — list_recent 100 QPS P95 < 200ms（EXPLAIN 验证 idx_user_status 使用）

### § 6.3 E2E（手测或 Playwright）

- [ ] TC-9: 候选人进入 /interview/room → LiveKit 连上 → AI 开口 → transcript 显示
- [ ] TC-10: LiveKit 断线 → 自动重连 3 次 → 失败提示保留 transcript 历史

---

## § 7 技术实现要点

### § 7.1 FastAPI Depends 注入（议题 B · 取代全局 `_livekit_workers` dict）

```python
# interview_runtime.py
def get_voice_state() -> VoiceStateManager:
    return VoiceStateManager()  # 单例即可，FastAPI cache

@router.post("/voice/respond")
async def voice_respond(state: VoiceStateManager = Depends(get_voice_state)):
    ...
```

### § 7.2 LiveKit Token 签发（议题 C · 用 PyJWT）

```python
# api/interview_runtime.py
import jwt as pyjwt

def issue_livekit_token(room: str, identity: str, ttl: int = 3600) -> str:
    payload = {
        "iss": settings.livekit_api_key,
        "sub": identity,
        "exp": int(time.time()) + ttl,
        "video": {"room": room, "roomJoin": True},
        "audio": {"room": room, "roomJoin": True},
    }
    return pyjwt.encode(payload, settings.livekit_api_secret, algorithm="HS256")
```

### § 7.3 transcript 推送（议题 C · WS + 异步写库）

```python
# api/interview_transcripts.py
from fastapi import WebSocket

@router.websocket("/{interview_id}/transcripts/stream")
async def stream_transcripts(websocket: WebSocket, interview_id: str, db = Depends(get_db)):
    await websocket.accept()
    await authenticate_ws(websocket, interview_id)
    
    async def forward_to_client(transcript: WSTranscriptMessage):
        await websocket.send_json(transcript.dict())
    
    # 订阅 LiveKit DataReceived → 转发 + 异步写库
    async with livekit_manager.subscribe(interview_id, forward_to_client) as sub:
        # 同时异步写 transcript_service.persist()
        ...
```

### § 7.4 Cross-file 引用（议题 B · 拆分后）

- `_livekit_workers` dict：从全局 → **FastAPI app.state.lk_workers**（用 lifespan 初始化）
- `VoiceRecord/VoiceRoom` 引用：从 `interview_runtime.py` 直接 import → **保持单测可单独 mock**
- 13 端点的 schema 定义：从 2 个内联 Pydantic 移到 `schemas/interview.py`

---

## § 8 安全 / 鉴权边界

| 项 | 规则 |
|---|---|
| 越权访问 | user 只能访问自己的 interview_id（list 过滤 + 单查询 scoped）|
| LiveKit 房间 | token 的 `room` 必须等于 `interview_id`（避免跨房间）|
| Rate limit | 议题 F 治理前用 slowapi（rate_limit per user 100/min）|
| Input validation | Pydantic Literal 校验所有 enum · max_length 校验所有字符串 |
| Audit log | transcript 写库时 `created_at` 服务端生成（不受客户端 ts 影响）|

---

## 🎯 硬性 DOD（api-spec.md 完成必须全过）

- [x] § 1-5 业务接口（13 端点 + transcript 推送）
- [x] § 6 业务错误码（统一 400-503 + WSErrorMessage）
- [x] § 7 认证（Bearer JWT + WS 鉴权）
- [x] § 8 测试场景（10 个 TC · 单测 / 集成 / E2E）
- [x] § 9-10 技术实现（FastAPI Depends + LiveKit JWT + WS 推送）
- [x] 与 plan.md / spec.md / db-design.md / research.md 对齐
- [ ] **用户验收签字**

---

## ✍️ 验收区

请回复以下任一：
- **"api-spec 验收通过"** → 我继续写 component-spec.md（LiveKitVoice + ReconnectToast 组件契约）
- **"api-spec 调 X"** → 修订（端点 / 字段 / 错误码）
- **"再想想"** → 停在 api-spec 阶段等讨论