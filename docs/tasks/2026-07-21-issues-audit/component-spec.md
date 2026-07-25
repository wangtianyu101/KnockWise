---
title: Component Spec（议题 C · LiveKitVoice + ReconnectToast）
date: 2026-07-22
status: v1 (AI 起草 · 待用户验收)
tags: [component-spec, 2步, refactor-6, React]
related:
  - plan.md（实施计划）
  - spec.md（业务契约 R1）
  - design-spec.md（**已验收** · 引用不重新设计）
  - api-spec.md（LiveKit token API + transcript WS）
  - mockups/03-interview-room.html（**已验收** 拟人化版本 v3）
---

# Component Spec（议题 C · LiveKitVoice + ReconnectToast）

> **覆盖范围**：议题 C 涉及的 2 个前端组件
>
> **设计契约已锁定**：[design-spec.md](design-spec.md) + [mockups/03-interview-room.html](mockups/03-interview-room.html) · 本文件**不重新设计**，只定义实现契约

---

## § 1 概述

| 组件 | 来源 | 变更 |
|---|---|---|
| **LiveKitVoice** | `frontend/components/LiveKitVoice.tsx`（已存在 75 行）| **大幅改造** · 增强 props · 加 transcript UI · VAD 状态可视化 |
| **ReconnectToast** | 新建 | LiveKit 断线自动重连时显示 toast · 3 次失败后转错误页 |

### § 1.1 引用已验收的设计契约

- 视觉系统：[design-mockup-workflow.md § 8](../rules/design-mockup-workflow.md) KnockWise V3 视觉（dark glassmorphism）
- 已验收 mockup：[mockups/03-interview-room.html](mockups/03-interview-room.html)（v3 拟人化）
- 3 处改动点：[design-spec.md § 3.2](../rules/design-mockup-workflow.md) · ① L142 组件替换 · ② L142-150 props · ③ L127-131 nav

---

## § 1.5 页面 ASCII Wireframe（[mockups/03-interview-room.html](mockups/03-interview-room.html) v3）

```
┌─────────────────────────────────────────────────────────────────┐
│ K [已连上 LiveKit · 320ms · 我在认真听 · 我在认真听]   12:34  ✕退出 │  ← Top nav + LiveKit 状态
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [AI avatar halo]  Alex · 你的面试官       [● 正在说话]         │
│                    系统设计 · 中级难度                          │
│                                                                 │
│   ━━━━ ● ━━━━━━━━━━ (18 bar AI 实时波形 · LiveKit audio)         │
│                                                                 │
│   ┌─ [🎤] 实时语音已开启                       [● Alex 在讲] ┐  │
│   │                                                       │  │
│   │   我把你的话实时转成文字，Alex 说的也会实时推到这里。      │  │
│   │   和之前的 VoiceRecord 比，我能在他说话的时候打断。        │  │
│   │                                                       │  │
│   │   [🎤] 麦克风已经开了 · 不用按按钮 · 你说完我立刻接话     │  │
│   └───────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌─ ● 对话记录 · 实时更新 ────────────────────────────────┐   │
│   │  [Alex avatar]  Alex                                   │   │
│   │  我们从系统设计开始吧。你能讲讲怎么设计一个分布式缓存吗？│   │
│   │                                                       │   │
│   │  [你 avatar]    你                                    │   │
│   │  主要解决两个问题：热点数据的快速访问...                │   │
│   │                                                       │   │
│   │  [Alex] (active)  Alex                                │   │
│   │  嗯，你提到了一致性 hash。能详细说下虚拟节点是干嘛的吗？│   │
│   │                                                       │   │
│   │  [你] (active)    你                                  │   │
│   │  主要是为了解决数据倾斜...                            │   │
│   │                                                       │   │
│   │  🤔 Alex 在想怎么接话...                              │   │
│   └───────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─ [🎤] 你 · wangty          麦克风已开 · 实时传输 ─┐      │
│   │   ━━━━━━●━━━━━━━━━━ (候选人波形)                │      │
│   │   [⏸ 让 Alex 等等]  [⏹ 聊完了]                  │      │
│   └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## § 2 LiveKitVoice 组件

### § 2.1 Props 接口

```typescript
interface LiveKitVoiceProps {
  // 必填 · LiveKit 房间
  roomName: string;                       // 面试 session_id（UUID）
  token: string;                          // LiveKit JWT（后端签发）

  // 必填 · 回调
  onTranscript: (text: string, speaker: "ai" | "user", ts: number) => void;
  onStateChange: (state: VoiceState) => void;

  // 选填 · 错误与重连
  onError?: (code: VoiceErrorCode, message: string) => void;
  onReconnectStateChange?: (state: ReconnectState) => void;

  // 选填 · UI 变体
  variant?: "default" | "minimal";        // default = 含完整调试 / minimal = 生产
  showWaveform?: boolean;                 // 默认 true
  autoStart?: boolean;                    // 默认 true（自动 Room.connect）
  className?: string;                     // 透传样式
}

type VoiceState =
  | "connecting"     // 初始连接
  | "connected"      // Room.connect 成功 + VAD 监听中
  | "listening"      // AI 在听候选人（VAD 检测到候选人说话）
  | "speaking"       // AI 说话中（TrackSubscribed audio）
  | "thinking"       // AI 收到答案后在评估（VAD 停顿 + LLM 推理）
  | "disconnected"   // 断线
  | "error";         // 连接失败 / token 错 / 权限拒绝

type ReconnectState =
  | { kind: "idle" }
  | { kind: "reconnecting"; attempt: number; maxAttempts: number; nextRetryAt: number }
  | { kind: "exhausted"; lastError: VoiceErrorCode }
  | { kind: "recovered"; at: number };

type VoiceErrorCode =
  | "permission_denied"        // 麦克风权限被拒
  | "token_invalid"            // LiveKit JWT 过期 / 签名错
  | "room_not_found"           // 后端没签发对应房间
  | "network_unstable"         // 重连 3 次失败
  | "auth_failed";             // WS 鉴权失败
```

### § 2.2 State

```typescript
const [state, setState] = useState<VoiceState>("connecting");
const [reconnectState, setReconnectState] = useState<ReconnectState>({ kind: "idle" });
const [speakingVolume, setSpeakingVolume] = useState(0);   // 0-100 AI 当前音量
const [localVolume, setLocalVolume] = useState(0);          // 0-100 候选人本地音量

const roomRef = useRef<Room | null>(null);
const reconnectAttemptRef = useRef(0);    // 用于 § 2.5 重连逻辑
const wsRef = useRef<WebSocket | null>(null);
```

### § 2.3 Events（输出 / 副作用）

| Event | 触发时机 | 携带数据 |
|---|---|---|
| `onTranscript(text, speaker, ts)` | LiveKit `RoomEvent.DataReceived` 收到 transcript | text 长度 ≤ 2000 |
| `onStateChange(state)` | 任何 VoiceState 变化 | state: VoiceState |
| `onError(code, message)` | 鉴权 / 权限 / 网络错误 | code ∈ VoiceErrorCode |
| `onReconnectStateChange(state)` | 自动重连状态变化 | state: ReconnectState |

### § 2.4 行为详解

#### § 2.4.1 初始化（autoStart = true 时）

```typescript
useEffect(() => {
  const room = new Room({
    adaptiveStream: true,
    dynacast: true,
    audioCaptureDefaults: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });
  roomRef.current = room;

  // 事件订阅
  room.on(RoomEvent.Connected, () => setState("connected"));
  room.on(RoomEvent.Disconnected, () => handleDisconnect());
  room.on(RoomEvent.TrackSubscribed, (track) => {
    if (track.kind === Track.Kind.Audio) {
      setState("speaking");
      // 解析轨道音量 → setSpeakingVolume（用 analyser node 或 VolumeIndicator）
      monitorVolume(track, setSpeakingVolume);
    }
  });
  room.on(RoomEvent.TrackUnsubscribed, () => setState("listening"));
  room.on(RoomEvent.DataReceived, (payload) => {
    const msg = JSON.parse(new TextDecoder().decode(payload));
    if (msg.speaker && msg.text) {
      onTranscript?.(msg.text, msg.speaker, msg.ts);
      if (msg.speaker === "ai") setState("speaking");
      else setState("listening");
    }
  });

  // 连接
  try {
    setState("connecting");
    await room.connect(LIVEKIT_URL, token);
    await room.localParticipant.setMicrophoneEnabled(true);
    setState("connected");
  } catch (err) {
    setState("error");
    onError?.(classifyError(err), err.message);
  }

  return () => room.disconnect();
}, [roomName, token]);
```

#### § 2.4.2 自动重连（断线时）

```typescript
const MAX_RECONNECT_ATTEMPTS = 3;
const BACKOFF_MS = [1000, 2000, 4000];  // 指数退避

async function handleDisconnect() {
  setState("disconnected");
  if (reconnectAttemptRef.current >= MAX_RECONNECT_ATTEMPTS) {
    setReconnectState({ kind: "exhausted", lastError: "network_unstable" });
    onError?.("network_unstable", "已重试 3 次仍失败");
    return;
  }
  const attempt = ++reconnectAttemptRef.current;
  const delay = BACKOFF_MS[attempt - 1];
  setReconnectState({ kind: "reconnecting", attempt, maxAttempts: MAX_RECONNECT_ATTEMPTS, nextRetryAt: Date.now() + delay });
  await sleep(delay);
  try {
    await roomRef.current?.connect(LIVEKIT_URL, token);
    reconnectAttemptRef.current = 0;
    setState("connected");
    setReconnectState({ kind: "recovered", at: Date.now() });
    onReconnectStateChange?.({ kind: "recovered", at: Date.now() });
  } catch (err) {
    handleDisconnect();  // 递归重试
  }
}
```

#### § 2.4.3 VAD 状态可视化（speakingVolume / localVolume）

```typescript
async function monitorVolume(track: RemoteTrack | RemoteAudioTrack, setter: (v: number) => void) {
  const el = track.attach();
  el.setAttribute("autoplay", "true");
  document.getElementById("ai-audio-sink")?.appendChild(el);
  
  // 用 AnalyserNode + requestAnimationFrame 估算音量（0-100）
  const ctx = new AudioContext();
  const source = ctx.createMediaElementSource(el);
  const analyser = ctx.createAnalyser();
  source.connect(analyser);
  analyser.fftSize = 256;
  const data = new Uint8Array(analyser.frequencyBinCount);
  
  function tick() {
    analyser.getByteFrequencyData(data);
    const avg = data.reduce((a, b) => a + b, 0) / data.length;
    setter(Math.round((avg / 255) * 100));
    requestAnimationFrame(tick);
  }
  tick();
}
```

### § 2.5 复用 / 依赖

- **复用现有 75 行逻辑**：Room.connect / RoomEvent 监听 / DataReceived 解析
- **依赖**：`livekit-client` ^1.x（已装）+ `AudioContext`（浏览器原生）
- **不要引入**：`@livekit/components-react`（重量过大）· 不引第三方 UI 库

### § 2.6 边界 / 错误处理

| 场景 | 行为 |
|---|---|
| 用户拒绝麦克风权限 | state="error" · onError("permission_denied") · toast 引导浏览器设置 · **不影响** transcript 显示（AI 那侧仍可连接）|
| Token 过期 | state="error" · onError("token_invalid") · 引导用户重新签发 token |
| Room 不存在 | state="error" · onError("room_not_found") · 引导用户重新创建面试 |
| 网络断开 30s 内 | handleDisconnect 自动重连 · state="disconnected" · toast "实时语音断连 · 正在重连（1/3）" |
| 重连 3 次失败 | state="error" · onError("network_unstable") · toast "请检查网络" · 保留前端 transcript 历史（不丢数据）|
| AI 服务异常（DataReceived 长时间无消息）| state="thinking" · 5s 后切回 "listening" · 加视觉提示 |

### § 2.7 测试场景（CLAUDE.md § 6.1 强制）

#### § 2.7.1 单元测试（vitest + @testing-library/react）

- [ ] TC-1: `LiveKitVoice.test.tsx` — 渲染 + variant="minimal" 不渲染调试
- [ ] TC-2: `LiveKitVoice.test.tsx` — autoStart=false 不自动连接
- [ ] TC-3: `LiveKitVoice.test.tsx` — state machine 切换（connecting → connected → speaking → listening）
- [ ] TC-4: `LiveKitVoice.test.tsx` — DataReceived 转发 onTranscript callback
- [ ] TC-5: `LiveKitVoice.test.tsx` — 麦克风权限拒绝 → onError("permission_denied")
- [ ] TC-6: `LiveKitVoice.test.tsx` — Token 过期 → onError("token_invalid")
- [ ] TC-7: `LiveKitVoice.test.tsx` — 3 次重连失败 → onError("network_unstable")

#### § 2.7.2 集成测试

- [ ] TC-8: Playwright E2E — 进入 /interview/room → LiveKit 连上 → AI 开口 → 候选人回答 → transcript 实时更新
- [ ] TC-9: Playwright E2E — LiveKit 断线 → ReconnectToast 显示 → 网络恢复 → 重连成功

---

## § 3 ReconnectToast 组件

### § 3.1 Props 接口

```typescript
interface ReconnectToastProps {
  state: ReconnectState;     // 接 LiveKitVoice.onReconnectStateChange
  onRetry?: () => void;      // 用户点"立即重试"
  onAbort?: () => void;      // 用户点"放弃"（跳历史报告页）
  className?: string;
}
```

### § 3.2 State（全部 props 驱动 · 无内部 state）

### § 3.3 事件

| Event | 触发 | 行为 |
|---|---|---|
| `onRetry()` | 点击"立即重试"按钮 | 触发 LiveKitVoice 重新 connect |
| `onAbort()` | 点击"放弃"按钮 | 跳 `/interview/history` |

### § 3.4 视觉（引用 mockup v3 · 顶部 toast 风格）

| ReconnectState | 视觉 |
|---|---|
| `{kind: "idle"}` | 不渲染 |
| `{kind: "reconnecting", attempt: 1, ...}` | 顶部 toast · "实时语音断连 · 正在重连（1/3）" + 转圈图标 |
| `{kind: "reconnecting", attempt: 2, ...}` | "实时语音断连 · 正在重连（2/3）" · 倒计时 |
| `{kind: "reconnecting", attempt: 3, ...}` | "实时语音断连 · 正在重连（3/3）" · 渐变背景变橙 |
| `{kind: "exhausted", lastError: "network_unstable"}` | "重连失败 · 请检查网络" + 2 按钮：[立即重试] [放弃] |
| `{kind: "recovered", at: ts}` | 顶部 toast 2s 后自动消失 · "实时语音已恢复" ✓ |

### § 3.5 复用

- 引用已验收的 design-spec.md § 5.4（toast 视觉体系：`backdrop-blur` + 渐变 + `var(--ease-spring)` 动画）
- 不创建新的视觉 token · 用现有 `--color-warning` / `--color-error` / `--color-success`

### § 3.6 边界

- `state.kind === "reconnecting"` 时显示倒计时（"X 秒后重试"）
- `state.kind === "exhausted"` 时按钮 disabled 状态自动恢复"重试中..."
- 自动消失：recovered 状态 2s 后 unmount

### § 3.7 测试场景

#### § 3.7.1 单元测试

- [ ] TC-1: `ReconnectToast.test.tsx` — idle 状态不渲染
- [ ] TC-2: `ReconnectToast.test.tsx` — reconnecting 状态显示 attempt/maxAttempts
- [ ] TC-3: `ReconnectToast.test.tsx` — exhausted 状态有 onRetry/onAbort 按钮
- [ ] TC-4: `ReconnectToast.test.tsx` — recovered 状态 2s 后自动消失
- [ ] TC-5: `ReconnectToast.test.tsx` — 点击 Retry 触发 onRetry 回调

---

## § 4 复用 / 边界总结

| 组件 | 复用现有 | 新增 |
|---|---|---|
| LiveKitVoice | `LiveKitVoice.tsx` 75 行骨架 + `livekit-client` Room API | 完整 VAD 状态机 + Volume 监控 + ReconnectState + Transcript UI |
| ReconnectToast | V3 视觉 token + 已有 Button 组件 | 新组件（无现有实现） |

**复用已有 mockup v3 视觉**：
- 5 层 radial-gradient 背景
- glass-card backdrop-blur
- emerald/cyan/violet accent
- `--ease-spring` 动效曲线
- 拟人化文案（"Alex · 你的面试官" / "我在认真听" / "让 Alex 等等"）

**不重新设计**（遵守 checklist.md § 2 行 43）：
- 不画新 wireframe
- 不创视觉 token
- 不改 mockup 内容

---

## § 5 测试场景汇总（CLAUDE.md § 6.1）

**LiveKitVoice**：7 TC 单元 + 2 TC 集成 = 9 个
**ReconnectToast**：5 TC 单元 = 5 个
**总计**：14 个测试场景

---

## § 6 与其他文档链接

| 文档 | 链接 | 关系 |
|---|---|---|
| `plan.md` | T4 议题 C 实施 | 引用本组件契约 |
| `spec.md` | R1 全双工实时语音 + Scenario 1.1-1.5 | 业务契约 |
| `design-spec.md` | § 3.2 改后 ASCII + § 4 room 状态机 | 设计契约（**已验收**）|
| `api-spec.md` | § 3.7 WS /transcripts/stream + § 3.5 livekit-token | 接口契约 |
| `mockups/03-interview-room.html` | v3 拟人化 | 设计验收 |

---

## 🎯 硬性 DOD（component-spec.md 完成必须全过）

- [x] Props / State / Events 完整定义（LiveKitVoice + ReconnectToast）
- [x] 行为详解（连接 / 重连 / VAD / 音量监控）
- [x] 复用 / 边界（不重复造轮）
- [x] 测试场景（14 个 TC）
- [x] 引用已验收的设计（design-spec.md + mockup v3）
- [x] 不重新设计（checklist.md § 2 行 43）
- [ ] **用户验收签字**

---

## ✍️ 验收区

请回复以下任一：
- **"component-spec 验收通过 · 下一步拆任务"** → § 1/§ 2 计划闭环 · 进 § 3 拆分（tasks.md · 4 个 T 原子任务）
- **"component-spec 调 X"** → 修订（Props / 事件 / 测试）
- **"再想想"** → 停在 component-spec 阶段等讨论