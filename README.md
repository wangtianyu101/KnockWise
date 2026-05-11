# CodeMock

一个真正会「追问」的 AI Agent 工程师语音面试 Agent。

## 技术栈

- **后端**: Python 3.12 + FastAPI + LangGraph + LangChain
- **语音**: LiveKit (WebRTC) + WhisperLive (STT) + piper-tts (TTS)
- **数据库**: MySQL 8.4
- **前端**: Next.js 15 + LiveKit React + Tailwind CSS

## 快速开始

```bash
# 1. 配置环境变量
cp backend/.env backend/.env.local
# 编辑 backend/.env.local，填入 GitHub OAuth 和 LLM API key

# 2. 启动所有服务
docker-compose up -d

# 3. 健康检查
curl http://localhost:8000/api/health
```

## 项目结构

```
codemock/
├── docs/            # 设计文档
├── backend/         # FastAPI + LangGraph Agent
├── frontend/        # Next.js + LiveKit React
└── docker-compose.yml
```

## MVP 进度

- [ ] Week 1: 基础设施 + 题库
- [ ] Week 2: Agent 引擎
- [ ] Week 3: 语音 + 前端
- [ ] Week 4: 报告 + 发布
