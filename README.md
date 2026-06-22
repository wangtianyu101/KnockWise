# CodeMock

一个真正会「追问」的 AI Agent 工程师语音面试 Agent。

> 📖 **完整使用 / 启动说明**：见 [`docs/00-入门/应用说明.md`](docs/00-入门/应用说明.md)

## 技术栈

- **后端**: Python 3.12 + FastAPI + LangGraph + LangChain
- **语音**: LiveKit (WebRTC) + faster-whisper (STT) + Piper / edge-tts (TTS)
- **数据库**: MySQL 8.4
- **前端**: Next.js 15 + Tailwind CSS
- **LLM**: DeepSeek V3（OpenAI-compatible 代理）

## 快速开始

```bash
# 后端
cd backend && ./.venv/bin/uvicorn main:app --port 8000 --env-file .env.local

# 前端（另一个终端）
cd frontend && npm run dev

# LiveKit（实时语音需要，另一个终端）
livekit-server --config ./livekit.yaml --node-ip 127.0.0.1

# 打开浏览器
open http://localhost:3000
```

## 文档

| 文档 | 说明 |
|------|------|
| [应用说明](docs/00-入门/应用说明.md) | **从这里开始** — 启动 + 运行 + 排错 |
| [项目说明](docs/10-架构/项目说明.md) | 完整功能 + 技能图谱 + 架构 |
| [技术文档](docs/10-架构/技术文档.md) | 技术栈 + 数据模型 + Session 持久化 |
| [接口文档](docs/20-参考/接口文档.md) | REST API 全列表 |
| [设计文档](docs/10-架构/设计文档.md) | 设计原则 + UI 规范 |
| [功能介绍](docs/00-入门/功能介绍.md) | 三模块功能概览（marketing 风格） |
| [架构演进](docs/10-架构/架构演进.md) | 平台/前端重构历史 ✅ |
| [实施计划](docs/30-历史/实施计划.md) | 5 阶段实施记录 ✅ |
| [实时语音实施](docs/30-历史/实时语音实施.md) | 实时语音第一版方案 ✅ |
| [实时语音升级方案](docs/30-历史/实时语音升级方案.md) | 追问 / Persona / 流式 TTS ✅ |
| [目前缺陷](docs/40-追踪/目前缺陷.md) | **动态** — 设计议题 + 技术债务 + 讨论记录 |
| [三层记忆与学习闭环](docs/archive/三层记忆与学习闭环.md) | **新设计** — 3 层记忆 + Profile 沉淀 + 4 模块闭环 |

## 端口

| 端口 | 服务 |
|------|------|
| 3000 | 前端 (Next.js) |
| 8000 | 后端 (FastAPI) |
| 7880 | LiveKit 信令 |
| 3306 | MySQL |
