# 实时电话面试 — 架构升级方案

> 从"按键说话 → 等待 → AI 回应"升级为"真实电话级对话体验"
> 类似：豆包语音助手 / 牛客虚拟面试官 / ChatGPT Advanced Voice

---

## 一、现状 vs 目标

| 维度 | 现状（P0） | 目标（V2） |
|---|---|---|
| 交互模式 | 按键说话（PTT），说完松手等 AI | 自由说话，AI 实时聆听，可打断 |
| 延迟 | 整句说完→STT→Agent→TTS，3-5 秒 | 流式处理，首字 < 500ms |
| 打断 | 不支持。AI 说话时用户只能等 | 支持 barge-in，AI 被中断后自然停顿 |
| 语音输出 | Piper TTS 整句合成后播放 | 流式 TTS，边说边合成 |
| AI 人格 | 无，纯功能问答 | 面试官人格：语气、节奏、追问策略 |
| 静音处理 | 无 | VAD 检测说话/静音，自然停顿判断 |

---

## 二、目标架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Browser)                        │
│  mic → AudioContext → LiveKit WebRTC → speaker          │
│  (全双工，不停采集；interrupt 事件)                       │
└──────────────────────────┬──────────────────────────────┘
                           │ WebRTC (LiveKit)
┌──────────────────────────▼──────────────────────────────┐
│                  LiveKit Server                          │
│  ┌─────────┐   ┌──────────┐   ┌────────────────────┐    │
│  │ VAD     │──▶│ Turn     │──▶│ Interview Pipeline │    │
│  │ (Silero)│   │ Manager  │   │                    │    │
│  │         │   │          │   │ ┌────────────────┐ │    │
│  │ 检测说话 │   │ 判断轮次  │   │ │ Streaming STT  │ │    │
│  │ /静音   │   │ 何时回应  │   │ │ (WhisperLive)  │ │    │
│  │         │   │ 何时打断  │   │ └───────┬────────┘ │    │
│  └─────────┘   └──────────┘   │         ▼          │    │
│                               │ ┌────────────────┐ │    │
│                               │ │ LangGraph Agent │ │    │
│                               │ │ (追问引擎)      │ │    │
│                               │ └───────┬────────┘ │    │
│                               │         ▼          │    │
│                               │ ┌────────────────┐ │    │
│                               │ │Streaming TTS   │ │    │
│                               │ │(Piper stream)  │ │    │
│                               │ └───────┬────────┘ │    │
│                               └─────────┼──────────┘    │
└─────────────────────────────────────────┼──────────────┘
                                          │
                                     User Speaker
```

---

## 三、核心改造点

### 3.1 全双工音频（前端）

**当前**：PTT 按钮 → MediaRecorder → 松手后发 Blob → STT

**改为**：AudioContext 持续采集 → `AudioWorklet` 分帧 → WebRTC track 实时发送

```typescript
// 前端核心变化
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const track = stream.getAudioTracks()[0];

// 加入 LiveKit 房间，发布音频 track
room.localParticipant.publishTrack(track, {
  name: "microphone",
  source: Track.Source.Microphone,
});

// 接收 AI 音频 track
room.on(TrackEvent.TrackSubscribed, (track, publication, participant) => {
  if (track.kind === "audio") {
    track.attach(document.createElement("audio"));
  }
});

// 打断：用户开始说话 → 发 interrupt 信号
// LiveKit 的 VoicePipelineAgent 原生支持 interrupt
```

**关键**：LiveKit `VoicePipelineAgent` 已经内置了 interrupt 支持。不需要自己实现。

### 3.2 Turn Manager（新增）

这是实时对话的大脑，判断 "轮该谁说了"。

```
状态机：
  ┌──────────┐
  │ LISTENING │ ← 默认状态，AI 在听用户说话
  └────┬─────┘
       │ 用户说完 (VAD 检测到静音 > 800ms)
       ▼
  ┌──────────┐
  │ THINKING │ ← AI 正在生成回复
  └────┬─────┘
       │ 生成完成第一个句子
       ▼
  ┌──────────┐
  │ SPEAKING │ ← AI 正在说话
  └────┬─────┘
       │ 用户开始说话 → interrupt!
       ▼
  ┌──────────┐
  │ LISTENING │ ← 循环回到聆听状态
  └──────────┘
```

实现：

```python
class TurnManager:
    """管理对话轮次：谁在说、何时切换、打断处理"""
    
    def __init__(self, silence_threshold_ms=800, interrupt_threshold_ms=300):
        self.state = "LISTENING"  # LISTENING | THINKING | SPEAKING
        self.silence_duration = 0.0
        self.interrupt_buffer = []
    
    def on_user_speech_start(self):
        if self.state == "SPEAKING":
            self.state = "LISTENING"
            return "INTERRUPT"  # 触发打断事件
        return None
    
    def on_user_silence(self):
        if self.state == "LISTENING":
            self.state = "THINKING"
            return "START_RESPONSE"  # 触发 AI 开始回
        return None
```

### 3.3 Streaming TTS（替换 Piper 整句合成）

**当前**：Piper 等整句文本 → 合成完整 WAV → 播放

**改为**：LLM 流式输出 token → Piper 逐句合成 → 边合成边发送

Piper 支持流式（`piper-tts` 的 `synthesize_stream_raw`），每个句子独立合成，延迟从 3 秒降到 ~300ms。

```python
class StreamingTTS:
    """逐句合成 TTS，降低首字延迟"""
    
    async def synthesize_stream(self, text_generator: AsyncIterable[str]):
        """接收 LLM 流式输出，逐句合成音频帧"""
        buffer = ""
        for sentence_detector in [".", "。", "?", "？", "!", "！", "\n"]:
            async for chunk in text_generator:
                buffer += chunk
                if any(buffer.rstrip().endswith(d) for d in sentence_detector):
                    audio_frame = await self._tts.synthesize(buffer.strip())
                    buffer = ""
                    yield audio_frame
        if buffer.strip():
            yield await self._tts.synthesize(buffer.strip())
```

### 3.4 面试官人格（Persona Engine）

虚拟面试官不是冷冰冰的 TTS，需要有：

| 维度 | 实现 |
|---|---|
| **声音** | 固定声线（Piper 中文男声/女声，保持一致） |
| **语速** | 根据问题难度调整（难题稍慢，基础题正常） |
| **语气** | 追问时温和但坚定，不会因为用户答错而变凶 |
| **停顿** | 自然停顿：问完问题后停顿 > 给思考时间 |
| **反馈词** | 自然的过渡语："嗯，好的"、"让我换一个角度问"、"这个回答不错，我们深入一下" |

```python
class InterviewerPersona:
    """面试官人格引擎"""
    
    def __init__(self, style="professional-friendly"):
        self.style = style
        self.transitions = {
            "correct": ["好的，答得不错。", "嗯，基本正确。", "不错。那我们继续——"],
            "partial": ["可以再想想。", "方向对了，还能更深入吗？", "我给你个提示——"],
            "wrong": ["没关系。", "这个确实容易搞混。", "我们换个角度——"],
            "probe": ["能再展开一点吗？", "具体说说？", "举个例子？"],
        }
    
    def wrap(self, agent_text: str, evaluation: str) -> str:
        """把 Agent 的原始输出包装成面试官口吻"""
        prefix = random.choice(self.transitions.get(evaluation, [""]))
        return f"{prefix} {agent_text}"
```

### 3.5 启动流程

用户看到的体验：

```
1. 打开面试页面
2. 点击 "开始面试" — LiveKit 房间连接中...
3. 连接成功 → "面试官"出现在界面上（可以是一个简单的动画头像）
4. 面试官开口："你好，欢迎参加今天的面试。我是你的面试官 Alex。
   我们先从 AI Agent 的基础开始聊。你准备好了吗？"
5. 用户说话 → 实时对话 → 可以随时打断
6. 面试结束 → 面试官："好的，今天面试到这里。你的报告马上生成。"
```

---

## 四、技术选型对比

| 组件 | 当前 (V1) | 升级 (V2) | 变化 |
|---|---|---|---|
| 音频传输 | LiveKit WebRTC | LiveKit WebRTC | 不变 |
| STT | PTT → WhisperLive (整段) | Streaming → WhisperLive (流式) | 改为持续流式 |
| VAD | 无（手动按键） | Silero VAD (已有的包) | 开启自动检测 |
| TTS | Piper 整句合成 | Piper 流式逐句 | 改为流式 |
| Interrupt | 不支持 | LiveKit VoicePipelineAgent 原生支持 | 新增 |
| Persona | 无 | InterviewerPersona | 新增 |
| Turn | 无（一问一答） | TurnManager 状态机 | 新增 |
| UI | 文字聊天 + 语音按钮 | 头像动画 + 波形 + 字幕 | 升级 |

---

## 五、实施计划

| 步骤 | 内容 | 工作量 |
|---|---|---|
| 1 | 前端：PTT → 全双工 WebRTC track | 1 天 |
| 2 | TurnManager：VAD + 打断逻辑 | 1.5 天 |
| 3 | TTS 流式化：Piper streaming adapter | 1 天 |
| 4 | Persona Engine：面试官人格包装 | 1 天 |
| 5 | 联调：端到端实时对话 | 1.5 天 |
| 6 | UI：头像/波形/字幕/打断指示 | 1 天 |

**总计**：~7 天。

---

## 六、风险

| 风险 | 应对 |
|---|---|
| 实时流式延迟仍 > 2 秒 | 降级为句子级流式（非 token 级），首句延迟 1 秒 |
| Piper 流式不够快 | 考虑切换到 EdgeTTS / Azure TTS 做流式备选 |
| VAD 在中文场景误判 | Silero VAD 对中文支持好，调低静音阈值 |
| WhisperLive 中文转录差 | 注入 AI 术语 prompt（已在计划中） |

---

## 七、当前可立即改进（低成本）

不需要完整 V2 改造，今天就能做的：

1. **去掉 PTT 按键** → 改为浏览器 VAD 自动检测说话结束（已有 `VoiceRoom.tsx` 组件，抄牛客的方案）
2. **Piper TTS 加过渡语** → `process_answer` 返回时包装一句自然过渡
3. **前端加头像动画** → CSS 动画，说话时嘴动

这三个改动加起来不到 1 天，体验立刻从"工具感"变成"对话感"。
