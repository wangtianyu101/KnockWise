# CodeMock

一个真正会「追问」的 AI Agent 工程师语音面试 Agent。

> 📖 **完整使用 / 启动说明**：见 [`docs/issues.md`](docs/issues.md)

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
| [📍 文档地图](docs/README.md) | **从这里开始** — 整个 docs 结构图 |
| [📋 议題追踪](docs/issues.md) | **动态** — 设计议题 + 技术债务 + 讨论记录 |
| [🔧 面试题库](docs/tasks/2026-06-22-new-feature-question-bank/) | 完整功能 + 技能图谱 + 架构 + 接口 |
| [🔧 AI 推送](docs/tasks/2026-06-22-new-feature-ai-push/) | 产品 + 技术 + 设计 |
| [🔧 实时语音](docs/tasks/2026-06-22-realtime-voice/) | 实施 + 升级方案 |
| [📚 接口文档](docs/api/README.md) | REST API 全列表 |
| [📁 归档旧结构](docs/archive/2026-06-27-docs-old-structure/) | 4 层分类的旧目录结构 |

## 端口

| 端口 | 服务 |
|------|------|
| 3000 | 前端 (Next.js) |
| 8000 | 后端 (FastAPI) |
| 7880 | LiveKit 信令 |
| 3306 | MySQL |
