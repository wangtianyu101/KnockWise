---
title: Design Spec（议题 C 全双工实时语音 UI）
date: 2026-07-22
status: v1 (AI 起草 · 待用户验收)
tags: [design-spec, 1步, 设计脑, 全双工, LiveKit]
related:
  - spec.md
  - research.md
  - decisions.md
  - mockups/*.html
  - docs/designs/real-time-voice/index.md
---

# Design Spec（议题 C 全双工实时语音 UI 替换）

> **覆盖范围**：议题 C 路径 2（全力全双工）· 全部语音路径 UI 替换
>
> **上游决策**：[decisions.md](decisions.md) 决策 1/7/8/9/10/11（路径 2 + 全部语音路径 + transcript+语音 UI + LiveKit built-in VAD + § 1 规格验收）
>
> **下游**：`mockups/*.html` + `docs/designs/real-time-voice/index.md`（按 design-mockup-workflow.md 三层产物）

---

## § 1 用户旅程（聚焦 room.tsx）

### 完整流程（候选人视角 · 房间页）

```
1. 用户通过 setup.tsx 进入 /interview/room.tsx
   → room.tsx 自动 POST /api/interviews 创建 interview
   → 拿到 interviewId → setRoomState("ready")

2. 组件层：room.tsx 渲染 <LiveKitVoice roomName={...} token={...}>
   → LiveKitVoice 内部 Room.connect + setMicrophoneEnabled(true)
   → 1.5s 内 LiveKit 连接成功 · state: connecting → connected → listening
   → AI 主动开口追问（实时流式 audio + transcript data channel）

3. 候选人开口回答
   → 本地麦克风自动采集（无需按住按钮）
   → LiveKit DataReceived 推送 transcript → LiveVoice.onTranscript
   → room.tsx addLine(text, "user") → LiveTranscript 实时滚动

4. 用户停顿 0.5s（VAD 检测）
   → AI 立即接话追问（延迟 < 500ms）
   → state: listening → speaking

5. 面试进行 30-45 分钟
   → transcript 累计所有对话
   → 用户可点击"提前结束"

6. 点击"结束面试"
   → POST /api/interviews/{id}/complete
   → 跳转 /interview/history
```

### 异常路径

| 异常 | 用户应对 |
|---|---|
| LiveKit 服务掉线 | LiveKitVoice 自动重连 3 次（指数退避）· 失败 state=disconnected · toast 提示 |
| 麦克风权限拒绝 | 引导浏览器设置 · 仍可看 transcript |
| 网络不稳 | 自动重连 + 保留 transcript 历史 |

---

## § 2 页面地图（聚焦 room.tsx · 议题 C 唯一改动页）

| 路由 | 页面 | 议题 C 改动 | 备注 |
|---|---|---|---|
| `/interview/room.tsx` | 实时语音房间（166 行）| **核心改动** · 把 `<VoiceRecord>` 替换为 `<LiveKitVoice>` + 加连接状态条 | 其余页面（`/interview.tsx` / `setup.tsx`）**不在议题 C 范围**，仅 room.tsx |

**改动 3 处（精确范围）**：
1. `room.tsx` L142：`<VoiceRecord>` → `<LiveKitVoice>`（核心组件替换）
2. `room.tsx` L142-150：props 调整 · `onTranscript/onResponse/onAudio/onError` → `onTranscript/onStateChange`（LiveKit DataReceived 实时推送）
3. `room.tsx` 顶部 nav：加连接状态条 · "● LiveKit 已连 · 延迟 Xms · VAD Active"（新增 ~10 行）

### 视觉一致性（继承 V3 · 按 design-mockup-workflow.md § 8）

- **app-nav**：56px sticky · KnockWise logo + breadcrumb
- **glass-card**：backdrop-blur + rgba bg + border
- **tag 体系**：tag-default / tag-direction / tag-active
- **动效曲线**：`--ease-spring` / `--ease-out`
- **dark mode**：bg-page `#050914` + 主色 `#6366f1` + 渐变光晕 radial-gradient

---

## § 3 页面线框（聚焦 room.tsx · ASCII 前后对比 · 65 字符宽 · box-drawing）

> **设计选择**（用户决策 12）：**ASCII 前后对比 · 不写 HTML mockup**
> - 范围聚焦 room.tsx（议题 C 唯一改动页）
> - 改前 vs 改后两张 ASCII 直接对比 · 5-10 行/页
> - 之前的 mockup 1+2+3 + index.md 已删（范围过大）

### § 3.1 改前（room.tsx · 当前用 VoiceRecord.tsx · PTT 模式）

```
┌─────────────────────────────────────────────────────────────────┐
│ ← 退出          面试中                              12:34        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│              [InterviewerAvatar · Alex]                          │
│                  (speaking/listening)                            │
│                                                                 │
│   ┌─ VoiceRecord（WebSocket ASR/TTS）────────────┐             │
│   │  [🎤 按住说话 · 松开识别]                       │             │
│   │  PTT 模式 · 录完才送 ASR · 单向音频流           │             │
│   └──────────────────────────────────────────────┘             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [LiveTranscript lines={transcript}]                            │
│   AI: 让我们从系统设计开始...                                    │
│   你: 主要解决热点数据访问和高并发问题...                          │
│   AI: 你提到了一致性 hash，能详细说下虚拟节点的作用吗？            │
├─────────────────────────────────────────────────────────────────┤
│                    [结束面试]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### § 3.2 改后（room.tsx · 议题 C · 用 LiveKitVoice.tsx 全双工）

```
┌─────────────────────────────────────────────────────────────────┐
│ ← 退出   ● LiveKit 已连 · 延迟 320ms · VAD Active    12:34     │  ← [改动3]
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│              [InterviewerAvatar · Alex]                          │
│       ━━━━━━━━━ ● ━━━━━━━━━━ (AI 实时音频波形 · LiveKit audio)  │
│                                                                 │
│   ┌─ LiveKitVoice（全双工）────────────────┐                  │  ← [改动1]
│   │  ● 聆听中 / ● 面试官说话中                  │                  │
│   │  自动采集麦克风 · 无录音按钮                │                  │
│   │  onTranscript(text, speaker) → addLine    │                  │  ← [改动2]
│   └────────────────────────────────────────┘                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [LiveTranscript lines={transcript}]                            │
│   AI: 让我们从系统设计开始...                                    │
│   你: 主要解决热点数据访问和高并发问题...                          │
│   AI: 你提到了一致性 hash，能详细说下虚拟节点的作用吗？            │
│   （LiveKit DataReceived 实时推送 · 替代 WebSocket ASR）         │
├─────────────────────────────────────────────────────────────────┤
│                    [结束面试]                                    │
└─────────────────────────────────────────────────────────────────┘
```

### § 3.3 改动点对照（3 处 · 用户明确范围）

| # | 文件:行 | 改前 | 改后 | 备注 |
|---|---|---|---|---|
| 1 | `room.tsx` L142 | `<VoiceRecord ... />` | `<LiveKitVoice ... />` | **核心组件替换** · LiveKitVoice 已存在 75 行 · 仅引用 |
| 2 | `room.tsx` L142-150 | props: `onTranscript / onResponse / onAudio / onError` | props: `onTranscript / onStateChange` | LiveKit DataReceived 实时推送 · 简化回调 |
| 3 | `room.tsx` L127-131 nav | 仅"面试中"标题 | 加"● LiveKit 已连 · 延迟 Xms · VAD Active" | 顶部状态条 · ~10 行新增 |

---

## § 4 交互细节（≥ 5 种状态 · 状态机）

### § 4.1 `/interview.room` 关键状态表

| 状态 | 触发 | 视觉反馈 | 用户可操作 |
|---|---|---|---|
| 默认 | 进入页面 0-1.5s | "连接中..." spinner + 进度条 | 等待 |
| 连接成功 | LiveKit Room.connect 成功 | AI avatar 渐显 + 波形开始动画 | 点击麦克风开口 |
| AI 说话 | AI 流式返回 audio | 上方 AI 波形剧烈跳动 + transcript 上半部分实时滚动 | 听 + 看 |
| 候选人说话 | 本地麦克风采集 | 下方候选人波形跳动 + transcript 上半部分实时滚动 | 继续说话 |
| VAD 停顿 | 候选人停顿 0.5s | AI 立即接话追问（< 500ms） | 听 AI 说话 |
| LiveKit 断连 | 服务掉线 | toast "实时语音断连 · 正在重连（1/3）" + transcript 历史保留 | 等待重连 |
| 重连失败 | 3 次失败 | toast "请检查网络后重试" + transcript 历史可下载 | 重试 / 退出 |
| 麦克风权限拒绝 | 浏览器拦截 | toast "请允许麦克风权限" + 引导设置 | 设置后重试 |
| 暂停 | 用户点 ⏸ | transcript 灰显 + "已暂停" | 继续 / 退出 |
| 提前结束 | 用户点 ⏏ | 确认 modal "确认提前结束？已记录的对话将生成报告" | 确认 / 取消 |
| 完成 | 30 分钟到 | "面试完成 · 正在生成报告..." + 进度条 | 等待 |

### § 4.2 `/interview/room` 异常流程

- **LiveKit 服务掉线**：LiveKitVoice 内部自动重连 3 次（指数退避）· 失败 state=disconnected · toast 提示
- **麦克风权限拒绝**：浏览器拦截时引导用户去设置 · 仍可看 transcript
- **网络不稳**：自动重连 + 保留 transcript 历史
- **AI 服务异常**：transcript 显示"AI 暂时离开" · 30s 后自动重试

> **不在范围**：`/interview/setup` 与 `/interview.tsx` 的状态机不在议题 C 改动范围 · 不画

---

## § 5 视觉规范（5 方面齐全 · 继承 V3）

### § 5.1 颜色（继承项目 token · 不创）

| 用途 | Token | 颜色 |
|---|---|---|
| 主色 | `--color-primary` | `#6366f1` |
| 主色 hover | `--color-primary-hover` | `#4f46e5` |
| 背景 page | `--color-bg-page` | `#050914` |
| 背景 card | `--color-bg-card` | `rgba(15, 20, 40, 0.7)` |
| 文字 primary | `--color-text-primary` | `#f8fafc` |
| 文字 secondary | `--color-text-secondary` | `#94a3b8` |
| 状态 success | `--color-success` | `#34d399` |
| 状态 warning | `--color-warning` | `#fbbf24` |
| 状态 error | `--color-error` | `#f87171` |
| 实时语音指示 | `--color-emerald` | `#10b981`（VAD Active 时） |

### § 5.2 字体

- 标题：16px / 600 字重
- 正文：14px / 400 字重
- 辅助：12px / 400 字重
- transcript 文字：14px / 400 行高 1.6
- 等宽数字（计时器）：`.stat-num` 样式

### § 5.3 间距

- 8px：标签内边距
- 16px：组件之间
- 24px：段落之间
- 32px：页面 main-content padding

### § 5.4 组件库

- **app-nav**：56px sticky · KnockWise logo + breadcrumb + 用户头像
- **sidebar**：240px 固定 · 面试/学习/AI 推送分组
- **glass-card**：backdrop-blur(20px) saturate(180%) + rgba bg + border
- **tag**：tag-default / tag-direction / tag-active（不创 flat 实底色 badge）
- **btn**：btn-primary / btn-secondary / btn-ghost / btn-danger
- **toast**：Vercel 风格顶部 · 3 类（success / warning / error）
- **modal-overlay** + **modal-content**：背黑 + 中心居中 + 圆角 16px
- **实时波形**：纯 CSS 动画（不要 SVG · 保持 150-300 行/页）

### § 5.5 圆角 / 阴影 / 动效

- 圆角：4px（tag）/ 8px（btn）/ 12px（card）/ 16px（modal）
- 阴影：4 档（`--shadow-md` / `--shadow-lg` / `--shadow-glow-primary` / `--shadow-glow-emerald`）
- 动效：`--ease-spring`（按钮 hover）/ `--ease-out`（页面过渡）
- 波形动画：CSS keyframes + transform（不要 JS 库）

### § 5.6 实时语音特殊视觉元素

| 元素 | 实现 |
|---|---|
| LiveKit 连接指示 | 顶部 status bar · 节点 ●●●●●● · 延迟数字 |
| VAD Active 指示 | emerald 绿色脉冲点 · 持续 0.5s 后自动消失 |
| AI 说话波形 | 上方条 · 高度随音量变化 · 纯 CSS 动画 |
| 候选人波形 | 下方条 · 高度随本地麦克风音量 |
| transcript 高亮 | 当前说话方文字带背景色块 · 1s 后淡出 |

---

## § 5.5 跨文档引用

- ✅ 涉及 UI 改动 → § 1 已产 design-spec.md（本文件 · 聚焦 room.tsx 前后对比 ASCII）
- ✅ 涉及数据契约 → spec.md § 4 已定义 LiveKitTokenRequest / EvaluateSchema / ReportSchema
- ⏸ § 2 计划待产出：api-spec.md（LiveKit token API）/ db-design.md（transcript 表 schema 增量）/ component-spec.md（LiveKitVoice / ReconnectToast 组件）

---

## 🎯 硬性 DOD（design-spec.md 完成必须全过 · 按 design-mockup-workflow.md § 5 · 修订聚焦 room.tsx）

- [x] § 1 用户旅程齐全（聚焦 room.tsx · 含异常路径）
- [x] § 2 页面 routes 表聚焦（仅 room.tsx · 议题 C 唯一改动页）
- [x] § 3 ASCII 前后对比（改前 VoiceRecord · 改后 LiveKitVoice · 65 字符宽 · box-drawing）
- [x] § 4 交互细节 ≥ 5 种状态（实际 11 种状态 · 仅 room 部分）
- [x] § 5 视觉规范 5 方面齐全（颜色 / 字体 / 间距 / 组件库 / 圆角阴影 + 实时语音特殊元素）
- [x] 不写 HTML mockup（用户决策 12 · B 选项 · 删了 3 mockup + index）
- [x] **已继承项目现有视觉 token / 导航 / 组件体系**（room.tsx 现状 + LiveKitVoice 现状均已读）
- [ ] **用户验收签字**（待用户确认）

---

## ✍️ 验收区

请回复以下任一：
- **"design 验收通过"** → § 1 规格完成 · 进入 § 2 计划（plan.md + api-spec.md + db-design.md + component-spec.md）
- **"改前 ASCII 调 Y"** → 修订 § 3.1 VoiceRecord 前后状态
- **"改后 ASCII 调 Y"** → 修订 § 3.2 LiveKitVoice 前后状态
- **"§ 3.3 改动点增/删"** → 修订 3 处改动清单
- **"再想想"** → 停在 design-spec.md 阶段等讨论