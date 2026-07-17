# 本地启动（macOS 本机模式）

> **来源**：原 CLAUDE.md § 七（2026-07-17 拆出）
> **触发**：每早开工 / 拉新代码 / 启动基础设施服务时读

> 2026-06-27 实测确认：Docker 模式**走不通**，必须用本机模式。
> AI 开工前**必须**先 `./scripts/start.sh` 把基础设施起起来。

## 为什么不用 Docker

| 阻塞 | 详情 |
|---|---|
| `registry-1.docker.io`（Docker Hub） | 在国内网络下 timeout / 无法访问 |
| `ghcr.io` 匿名访问 | 仅 `livekit/*` 等极少数公开仓库可匿名 pull；`collabora/whisperlive` 需 auth |
| `daocloud.io` mirror | 仅代理 `library/`（Docker 官方镜像），第三方仓库不代理 |
| `livekit/livekit-server` | 无 macOS 原生二进制（仅 linux/windows），必须 Docker |
| WhisperLive | **不需要**！代码里 `WhisperLiveClient` 类定义了但**无任何调用**；主路径走 `SimpleSTT`（本地 openai-whisper） |

**结论**：Docker 路径会卡在第一步（pull 镜像），本机模式用 brew 装的 livekit-server + 本地 MySQL/Redis 替代。

## 本机模式 5 个服务

5 个服务（MySQL/Redis/LiveKit/Backend/Frontend）的端口表 + 单独启动命令见 [`../../scripts/start.sh`](../../scripts/start.sh) 头部注释（不在 CLAUDE.md 重复维护，会与脚本脱钩）。

## 一键启停（推荐）

```bash
./scripts/start.sh           # 幂等起全部（已在跑就跳过）
./scripts/stop.sh            # 优雅停 livekit + backend + frontend（不动 MySQL/Redis）
./scripts/stop.sh all        # + 关 MySQL/Redis
./scripts/start.sh backend   # 单起某个服务
```

幂等 / 优雅关闭 / PID / 日志 设计要点见 [`../../scripts/start.sh`](../../scripts/start.sh) 头部注释。

## 已知坑（避雷）

| 坑 | 解决 |
|---|---|
| `livekit.yaml` 里 `node_ip: 192.168.1.20` 硬编码 | 启动时加 `--node-ip 127.0.0.1`（脚本已处理） |
| LiveKit 二进制命令名是 `livekit-server` 不是 `livekit` | `brew install livekit` 后用 `livekit-server` |
| 后端 init_db/cache 失败**不阻塞**启动 | 是设计如此（不让 DB 挂掉拖死服务），看日志 `Database unavailable` 警告 |
| 端到端业务（dashboard/dev-login）走 JWT | 拿 token: `curl 'http://localhost:8000/api/auth/dev-login?user_id=1'` |

## 端到端验证脚本（真实业务）

其他途径（浏览器/Swagger/health）太显然，**真正能验业务的是 JWT dev-login + dashboard**：

```bash
TOKEN=$(curl -s 'http://localhost:8000/api/auth/dev-login?user_id=1' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/dashboard
```

## 故障排查速查

| 症状 | 排查 |
|---|---|
| `Failed to fetch`（前端） | 后端没起？`curl http://localhost:8000/api/health` |
| `Unknown column 'xxx'` | DB 旧表缺列 → `core/database.py:_MIGRATIONS` 应自动 ALTER，看启动日志 |
| LiveKit 连不上 | `node_ip` 没改？用 `lsof -i :7880` 看进程是否在 |
| 知识库空 | `~/Obsidian/coding/` 不存在？改 `services/obsidian_service.py:VAULT_ROOT` |
