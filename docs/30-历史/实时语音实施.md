# 实时电话面试 — 完整实施计划 ✅ 已落地

> 基于 `voice/livekit_worker.py` + `components/VoiceRoom.tsx` 升级为全双工实时对话。
> 升级版方案见 [`实时语音升级方案.md`](./实时语音升级方案.md)。

---

## 总体架构变更

```text
┌──────────────────────────────────────────────────┐
│              前端 (next.js)                       │
│                                                  │
│  ┌─────────────────────┐  ┌──────────────────┐  │
│  │ AudioTrackPublisher │  │ AudioTrackPlayer │  │
│  │ (持续发送 mic)       │  │ (持续接收 AI)    │  │
│  └─────────┬───────────┘  └────────▲─────────┘  │
│            │ WebRTC                │             │
│  ┌─────────▼───────────────────────┴─────────┐  │
│  │ LiveKit Room                               │  │
│  │  ├─ user-mic track (publish)               │  │
│  │  └─ ai-speech track (subscribe)            │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  UI: 头像动画 + 实时字幕 + 打断按钮(可选)         │
└──────────────────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│           LiveKit VoicePipelineAgent              │
│  ┌──────┐  ┌──────────┐  ┌──────┐  ┌──────────┐ │
│  │ VAD  │→│ Turn     │→│ STT  │→│ Agent    │ │
│  │Silero│  │ Manager  │  │Stream│  │+Persona  │ │
│  └──────┘  └──────────┘  └──────┘  └────┬─────┘ │
│                                         │        │
│                                    ┌────▼─────┐  │
│                                    │Stream TTS│  │
│                                    │(sentence)│  │
│                                    └──────────┘  │
└──────────────────────────────────────────────────┘
```

**关键变化**：
- 前端：PTT button → WebRTC audio track publish
- 后端：VoicePipelineAgent 已存在 → 加 TurnManager + Persona + Stream TTS

---

## Phase 1: 前端全双工 (6h)

### 1.1 VoiceRoom → LiveKitPublisher

**文件**：`frontend/components/LiveKitVoice.tsx`（新组件）

```typescript
// 核心：替代 VoiceRoom.tsx，不再用 PTT
// AudioTrack 持续发布到 LiveKit room
// AI audio track 持续接收播放

interface LiveKitVoiceProps {
  roomName: string;       // LiveKit room name
  token: string;          // LiveKit access token
  onTranscript: (text: string) => void;  // 实时字幕回调
  onStateChange: (state: 'connecting' | 'connected' | 'listening' | 'speaking' | 'disconnected') => void;
}

export default function LiveKitVoice({ roomName, token, onTranscript, onStateChange }: LiveKitVoiceProps) {
  const roomRef = useRef<Room | null>(null);
  
  useEffect(() => {
    const room = new Room({ audioCaptureDefaults: { echoCancellation: true, noiseSuppression: true } });
    
    // 连接房间
    room.connect(process.env.NEXT_PUBLIC_LIVEKIT_URL!, token);
    
    // 发布本地麦克风 track（自动开始）
    room.localParticipant.setMicrophoneEnabled(true);
    
    // 接收 AI 的音频 track
    room.on(TrackEvent.TrackSubscribed, (track, pub, participant) => {
      if (track.kind === 'audio' && participant.isRemote) {
        // AI 开始说话
        onStateChange('speaking');
        const el = track.attach();
        document.getElementById('ai-audio-container')!.appendChild(el);
        
        track.on(TrackEvent.Ended, () => onStateChange('listening'));
      }
    });
    
    // 接收 AI 的实时字幕（通过 data channel）
    room.on(DataPacketEvent.Data, (payload) => {
      const text = new TextDecoder().decode(payload);
      onTranscript(text);
    });
    
    roomRef.current = room;
    return () => { room.disconnect(); };
  }, [roomName, token]);
  
  // UI: 仅显示状态指示器，不需要按钮
  return null; // UI 在外层组件
}
```

### 1.2 面试页面集成

**文件**：`frontend/pages/interview/room.tsx`

```text
变化：
  - 移除 VoiceRoom PTT 组件
  + 添加 LiveKitVoice 组件
  + 添加面试官头像动画
  + 添加实时字幕条
  + 添加通话状态指示

UI 布局：
┌─────────────────────────────────────┐
│          ┌───────────┐              │
│          │  🤖       │  面试官 Alex │
│          │  头像动画  │  ● 说话中   │
│          └───────────┘              │
│  ┌─────────────────────────────────┐│
│  │  实时字幕：                      ││
│  │  AI: 你能讲讲 ReAct 模式吗？     ││
│  │  你: ReAct 是 Reasoning + ...   ││
│  └─────────────────────────────────┘│
│                          [🔴 结束]  │
└─────────────────────────────────────┘
```

---

## Phase 2: TurnManager + Interrupt (8h)

### 2.1 TurnManager

**新建文件**：`backend/voice/turn_manager.py`

```python
"""
TurnManager — 管理实时对话轮次和打断逻辑。

状态机：
  LISTENING → (silence > 800ms) → THINKING → (first_chunk_ready) → SPEAKING
  SPEAKING → (user_speech > 300ms) → LISTENING (interrupt!)
  THINKING → (user_speech > 300ms) → LISTENING (cancel generation)
"""

import asyncio
import time
import logging
from enum import Enum

logger = logging.getLogger("codemock-turn")

class TurnState(Enum):
    LISTENING = "listening"        # AI 在听
    THINKING = "thinking"          # AI 在生成回复
    SPEAKING = "speaking"          # AI 在说话

class TurnManager:
    def __init__(self, silence_ms=800, interrupt_ms=300):
        self.state = TurnState.LISTENING
        self.silence_threshold = silence_ms / 1000.0
        self.interrupt_threshold = interrupt_ms / 1000.0
        
        self._user_speech_start = 0.0
        self._user_speech_end = 0.0
        self._user_is_speaking = False
        self._ai_speech_start = 0.0
        
        self.on_interrupt = None   # async callback
        self.on_turn_ready = None  # async callback
    
    def user_speech_started(self):
        """VAD 检测到用户开始说话"""
        self._user_speech_start = time.time()
        self._user_is_speaking = True
        
        # 打断检测
        if self.state == TurnState.SPEAKING:
            duration = time.time() - self._ai_speech_start
            if duration > self.interrupt_threshold:
                logger.info(f"INTERRUPT after {duration:.2f}s of AI speech")
                self.state = TurnState.LISTENING
                return "interrupt"
        
        if self.state == TurnState.THINKING:
            logger.info("User spoke during thinking — cancel generation")
            self.state = TurnState.LISTENING
            return "cancel"
        
        return None
    
    def user_speech_ended(self):
        """VAD 检测到用户停止说话"""
        self._user_speech_end = time.time()
        self._user_is_speaking = False
        duration = self._user_speech_end - self._user_speech_start
        
        if self.state == TurnState.LISTENING and duration > 0.5:
            # 用户说完了一段有意义的话
            self.state = TurnState.THINKING
            return "turn_ready"
        return None
    
    def ai_started_speaking(self):
        """AI 开始说话"""
        self._ai_speech_start = time.time()
        self.state = TurnState.SPEAKING
    
    def ai_stopped_speaking(self):
        """AI 说完"""
        self.state = TurnState.LISTENING
    
    def check_silence_timeout(self) -> str | None:
        """检查静音超时（用户沉默 > threshold 且说过话）"""
        if self._user_is_speaking:
            return None
        if self.state != TurnState.LISTENING:
            return None
        if self._user_speech_end == 0:
            return None
        
        elapsed = time.time() - self._user_speech_end
        if elapsed > self.silence_threshold:
            self.state = TurnState.THINKING
            return "turn_ready"
        return None
```

### 2.2 InterviewAgent 重写

**文件**：`backend/voice/livekit_worker.py`（重写 InterviewAgent 类）

核心改动：

```python
class InterviewAgentV2(VoicePipelineAgent):
    """V2: 全双工实时面试官。TurnManager + Persona + Stream TTS"""
    
    def __init__(self, ctx: JobContext):
        # 仍然用 silero VAD + LocalSTT + LocalTTS
        super().__init__(
            vad=silero.VAD.load(
                min_speech_duration=0.3,     # 300ms = 有效说话
                min_silence_duration=0.8,    # 800ms = 说完
            ),
            stt=LocalSTT(),
            tts=LocalTTS(),
            chat_ctx=ChatContext(),
            allow_interruptions=True,         # ← 关键！LiveKit 原生支持
        )
        self.turn = TurnManager()
        self.persona = InterviewerPersona()
        
    async def on_user_speech_started(self):
        """VAD 检测到用户开始说话"""
        action = self.turn.user_speech_started()
        if action == "interrupt":
            # LiveKit VoicePipelineAgent 自动停止 TTS 播放
            # 播放一个微小的"被打断"音效（可选）
            logger.info("AI interrupted by user")
        
    async def on_user_speech_ended(self):
        """VAD 检测到用户说完"""
        action = self.turn.user_speech_ended()
        if action == "turn_ready":
            # 触发 AI 回复
            text = await self._generate_response()
            self.turn.ai_started_speaking()
            await self.say(text)  # LiveKit 流式播放
            self.turn.ai_stopped_speaking()
    
    async def _generate_response(self) -> str:
        """生成 AI 回复（带 Persona 包装）"""
        raw = await self._interview_agent.process(...)
        return self.persona.wrap(raw)  # 面试官人格包装
```

---

## Phase 3: Persona Engine (4h)

### 3.1 InterviewerPersona

**新建文件**：`backend/voice/persona.py`

```python
"""
InterviewerPersona — 面试官人格引擎。
给 Agent 输出包装自然的面试官语气、过渡词、追问节奏。
"""

import random

class InterviewerPersona:
    def __init__(self, name="Alex", style="professional-friendly"):
        self.name = name
        self.style = style
        
        # 过渡词库
        self.openings = {
            "first_question": [
                "好的，我们开始吧。",
                "那我们先从基础开始。",
                "准备好了吗？第一个问题——",
            ],
            "next_question": [
                "好的。那我们换一个方向——",
                "不错，接下来——",
                "嗯。下一个问题——",
            ],
            "after_interrupt": [
                "抱歉，你刚才说的——",
                "好的，那——",
                "嗯，继续——",
            ],
        }
        
        self.transitions = {
            "correct": [
                "对，答得很好。", "基本正确。", "嗯，不错。",
            ],
            "partial": [
                "方向对了，还能再深入吗？", "可以再补充一点。",
                "我给你个提示——",
            ],
            "wrong": [
                "没关系，这个确实容易搞混。", "嗯，我们换个角度。",
                "这个不太对，不过没问题。",
            ],
            "probe": [
                "能再展开一点吗？", "具体说说？", "举个例子？",
                "这个点你实际用过吗？",
            ],
        }
        
        self.closings = [
            "好的，今天的面试就到这里。你的表现不错，有几个方向可以再深入。稍后给你一份完整报告。",
            "好的，面试结束。感谢你的时间。报告马上出来。",
        ]
    
    def wrap(self, agent_output: dict) -> str:
        """把 Agent 的原始输出包装成面试官口吻"""
        action = agent_output.get("action", "next_question")
        text = agent_output.get("followup_text") or agent_output.get("question_text", "")
        
        if action == "next_question":
            prefix = random.choice(self.openings["next_question"])
            return f"{prefix} {text}"
        
        if action in ("followup", "probe", "give_hint"):
            prefix = random.choice(self.transitions["probe"])
            return f"{prefix} {text}"
        
        if action == "skip_and_record":
            prefix = random.choice(self.transitions["wrong"])
            return f"{prefix} {text}"
        
        return text
    
    def greeting(self, tech_stack: list[str]) -> str:
        return (
            f"你好，我是{self.name}，今天的面试官。"
            f"我看到你的技术栈是{'、'.join(tech_stack[:4])}，"
            f"我们就围绕这些来聊。准备好了吗？"
        )
    
    def closing(self) -> str:
        return random.choice(self.closings)
```

---

## Phase 4: Streaming TTS (6h)

### 4.1 LocalTTS 流式化

**文件**：`backend/voice/tts.py`（修改 `TTSEngine` 类）

当前 Piper 只有整句合成。需要改为逐句流式：

```python
class TTSEngine:
    def synthesize(self, text: str) -> bytes:
        """整句合成（保留，兼容现有代码）"""
        ...
    
    def synthesize_stream(self, text: str) -> list[bytes]:
        """
        流式合成：把文本按句子分割，逐句返回音频帧。
        首句延迟从 3s 降到 ~300ms。
        """
        import re
        sentences = re.split(r'(?<=[。！？.!?\n])\s*', text)
        frames = []
        for sentence in sentences:
            if sentence.strip():
                wav = self._synthesize_single(sentence.strip())
                if wav:
                    frames.append(wav)
        return frames
```

### 4.2 前端播放

```typescript
// LiveKit 自动处理音频播放，不需要额外代码
// VoicePipelineAgent 发送的音频 track 会自动播放
```

LiveKit `VoicePipelineAgent.say()` 已经内部处理了 TTS → 音频帧 → WebRTC track，只需要 TTS adapter 支持分帧返回。

---

## Phase 5: UI 升级 (6h)

### 5.1 面试官头像动画

**新建文件**：`frontend/components/InterviewerAvatar.tsx`

```typescript
// CSS 动画：圆形头像 + 说话时嘴部波动
// 状态：idle(静止) | listening(呼吸灯) | speaking(波形) | thinking(旋转)
```

### 5.2 实时字幕

**新建文件**：`frontend/components/LiveTranscript.tsx`

```typescript
// 滚动字幕条
// AI 字幕：通过 LiveKit data channel 实时接收
// 用户字幕：STT 中间结果
```

### 5.3 面试页面重设计

```text
┌───────────────────────────────────────────┐
│   ← 退出         面试中    00:12:34      │
├───────────────────────────────────────────┤
│                                           │
│            ┌─────────────┐               │
│            │    🤖       │               │
│            │  [嘴部动画]  │  ● 聆听中    │
│            └─────────────┘               │
│             面试官 Alex                   │
│                                           │
│  ┌───────────────────────────────────┐   │
│  │ Alex: 能讲讲 ReAct 模式的          │   │
│  │ 核心思想和应用场景吗？             │   │
│  │                                   │   │
│  │ 你: ReAct 是一种结合推理和行动    │   │
│  │ 的 Agent 架构模式...              │   │
│  └───────────────────────────────────┘   │
│                                           │
│            🎤 正在聆听...                  │
│                                           │
│         [⏹ 结束面试]                     │
└───────────────────────────────────────────┘
```

---

## 实施时间线

```text
Day 1: Phase 1 (前端全双工)
  ├─ 上午: LiveKitVoice 组件 (新)
  ├─ 下午: 面试页面集成 + 测试
  └─ 验证: PTT 不需要了，mic 自动采集

Day 2: Phase 2 (TurnManager + Interrupt)
  ├─ 上午: turn_manager.py (新)
  ├─ 下午: InterviewAgentV2 重写
  └─ 验证: 打断正常工作

Day 3: Phase 3 (Persona)
  ├─ 上午: persona.py (新)
  ├─ 下午: 集成到 InterviewAgentV2
  └─ 验证: 面试官语气自然

Day 4: Phase 4 (Stream TTS)
  ├─ 上午: tts.py 流式化
  ├─ 下午: 延迟测试 + 优化
  └─ 验证: 首句延迟 < 500ms

Day 5: Phase 5 (UI)
  ├─ 上午: InterviewerAvatar + LiveTranscript
  ├─ 下午: 面试页面重设计
  └─ 验证: 完整通话体验

Day 6-7: 联调 + 打磨
  ├─ 端到端测试（完整面试流程）
  ├─ 延迟优化
  ├─ 边界 case（网络断开/静音/嘈杂环境）
  └─ 产出: Demo 视频录制
```

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|---|---|---|
| `frontend/components/LiveKitVoice.tsx` | **新建** | 全双工音频组件 |
| `frontend/components/InterviewerAvatar.tsx` | **新建** | 面试官头像动画 |
| `frontend/components/LiveTranscript.tsx` | **新建** | 实时字幕组件 |
| `frontend/pages/interview/room.tsx` | **重写** | 面试页面 |
| `backend/voice/turn_manager.py` | **新建** | 轮次管理 |
| `backend/voice/persona.py` | **新建** | 面试官人格 |
| `backend/voice/livekit_worker.py` | **重写** | InterviewAgentV2 |
| `backend/voice/tts.py` | **修改** | 流式 TTS |
