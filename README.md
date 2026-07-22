# KnockWise

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

## 🤖 Auto-fix CI（自动修复失败的 CI）

**触发条件**：`CI` workflow 失败（非 main 分支 / 非 fork PR）→ `auto-fix-ci.yml` 启动
**安全设计**（4 道关 · CLAUDE.md § 6.10）：
- **关 1 不可信输入净化**：Claude 仅接收 sanitized CI log（job 名 + 错误类型 + 截断 200 字符）
- **关 2 权限分层**：diagnostic job（只读，无 secrets）+ apply-fix job（env approval 后才有 secrets）
- **关 3 供应链防御**：所有第三方 Action pin 完整 40 字符 SHA（非 `@beta` / `@main` / `@v1`）
- **关 4 人工 gate**：apply-fix job 必须 `environment: auto-fix-approval` 人工审批
**输出**：开 Draft PR 到 `auto-fix/<branch>-<sha>` 分支（**绝不**直接 push 原 PR）· 强制人工 review 后合并

### 如何关闭 auto-fix

**方式 1 · 全局关闭**：仓库 Settings → Environments → `auto-fix-approval` → 改为不需要 reviewers
**方式 2 · 单 PR 关闭**：在 PR 上加 label `auto-fix-disabled`（待实现 · T19 follow-up）
**方式 3 · 跳过特定 commit**：在 commit msg 中加 `[skip-auto-fix]` 标记（待实现 · T19 follow-up）

### 失败上限

同一 commit 最多自动修 3 次（label `auto-fix-count-<sha>` 计数）· 第 4 次失败转人工 issue

### 详细文档

- 调研：[`docs/tasks/2026-07-22-new-feature-ci-autofix/research.md`](docs/tasks/2026-07-22-new-feature-ci-autofix/research.md)
- 规格：[`spec.md`](docs/tasks/2026-07-22-new-feature-ci-autofix/spec.md)
- 决策：[`decisions.md`](docs/tasks/2026-07-22-new-feature-ci-autofix/decisions.md)
- 实施：[`tasks.md`](docs/tasks/2026-07-22-new-feature-ci-autofix/tasks.md)
