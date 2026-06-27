#!/bin/bash
# Intervue 一键启动脚本（macOS 本机模式）
#
# 启动顺序（依赖关系）：
#   MySQL → Redis → LiveKit → Backend → Frontend
#
# 用法：
#   ./scripts/start.sh           # 起全部
#   ./scripts/start.sh livekit   # 只起 livekit
#   ./scripts/start.sh backend   # 只起后端
#   ./scripts/start.sh frontend  # 只起前端
#
# 配合 ./scripts/stop.sh 关闭
#
# 设计要点：
#   - 幂等：端口已占用就跳过
#   - 后台：所有服务用 nohup + & 启，日志写到 /tmp/intervue-*.log
#   - PID 记录：写到 /tmp/intervue-pids.txt，stop.sh 读这个文件

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="/tmp/intervue-pids.txt"
LOG_DIR="/tmp"

# ── 颜色输出 ──────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; }

# ── 工具函数 ──────────────────────────────────────
is_listening() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN > /dev/null 2>&1
}

# 通过端口拿到 LISTEN 进程 PID（用于"已在跑"场景记录到 PID 文件）
pid_listening_on() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -1
}

record_pid() {
  # 追加 PID 到 PID_FILE（每行 "name pid"）
  echo "$1 $2" >> "$PID_FILE"
}

start_mysql_redis_if_needed() {
  # MySQL
  if is_listening 3306; then
    ok "MySQL:3306 已在跑"
  else
    warn "MySQL:3306 未启动，尝试 brew services start mysql"
    if brew services start mysql 2>&1 | tail -3; then
      sleep 2
      is_listening 3306 && ok "MySQL:3306 已起" || fail "MySQL 起不来，请手动排查"
    else
      fail "brew services start mysql 失败"
    fi
  fi

  # Redis
  if is_listening 6379; then
    ok "Redis:6379 已在跑"
  else
    warn "Redis:6379 未启动，尝试 brew services start redis"
    if brew services start redis 2>&1 | tail -3; then
      sleep 1
      is_listening 6379 && ok "Redis:6379 已起" || fail "Redis 起不来"
    fi
  fi
}

start_livekit() {
  if is_listening 7880; then
    EXISTING=$(pid_listening_on 7880)
    record_pid "livekit" "$EXISTING"
    ok "LiveKit:7880 已在跑 (PID $EXISTING)"
    return
  fi
  if ! command -v livekit-server > /dev/null 2>&1; then
    fail "livekit-server 未安装。请跑: brew install livekit"
    exit 1
  fi
  cd "$PROJECT_ROOT"
  nohup livekit-server --config ./livekit.yaml --node-ip 127.0.0.1 \
    > "$LOG_DIR/intervue-livekit.log" 2>&1 &
  PID=$!
  record_pid "livekit" "$PID"
  sleep 3
  if is_listening 7880; then
    ok "LiveKit:7880 已起 (PID $PID)"
  else
    fail "LiveKit 启动失败，看日志: tail $LOG_DIR/intervue-livekit.log"
    exit 1
  fi
}

start_backend() {
  if is_listening 8000; then
    EXISTING=$(pid_listening_on 8000)
    record_pid "backend" "$EXISTING"
    ok "Backend:8000 已在跑 (PID $EXISTING)"
    return
  fi
  if [ ! -d "$PROJECT_ROOT/backend/.venv" ]; then
    fail "backend/.venv 不存在"
    exit 1
  fi
  if [ ! -f "$PROJECT_ROOT/backend/.env.local" ]; then
    fail "backend/.env.local 不存在"
    exit 1
  fi
  cd "$PROJECT_ROOT/backend"
  nohup ./.venv/bin/uvicorn main:app --port 8000 --host 0.0.0.0 --env-file .env.local \
    > "$LOG_DIR/intervue-backend.log" 2>&1 &
  PID=$!
  record_pid "backend" "$PID"
  sleep 4
  if curl -s -f http://localhost:8000/api/health > /dev/null; then
    ok "Backend:8000 已起 (PID $PID, /api/health 200)"
  else
    fail "Backend 启动失败，看日志: tail $LOG_DIR/intervue-backend.log"
    exit 1
  fi
}

start_frontend() {
  if is_listening 3000; then
    EXISTING=$(pid_listening_on 3000)
    record_pid "frontend" "$EXISTING"
    ok "Frontend:3000 已在跑 (PID $EXISTING)"
    return
  fi
  if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    fail "frontend/node_modules 不存在，请跑: cd frontend && npm install"
    exit 1
  fi
  cd "$PROJECT_ROOT/frontend"
  nohup npm run dev > "$LOG_DIR/intervue-frontend.log" 2>&1 &
  PID=$!
  record_pid "frontend" "$PID"
  sleep 6
  if is_listening 3000; then
    ok "Frontend:3000 已起 (PID $PID)"
  else
    fail "Frontend 启动失败，看日志: tail $LOG_DIR/intervue-frontend.log"
    exit 1
  fi
}

# ── 主流程 ──────────────────────────────────────
TARGET="${1:-all}"
echo "🚀 Intervue 启动脚本（目标: $TARGET）"
echo "─────────────────────────────────────────────────"

# 清空 PID 文件（重新记录）
> "$PID_FILE"

case "$TARGET" in
  all)
    start_mysql_redis_if_needed
    start_livekit
    start_backend
    start_frontend
    ;;
  mysql)  start_mysql_redis_if_needed ;;
  redis)  start_mysql_redis_if_needed ;;
  livekit) start_livekit ;;
  backend) start_backend ;;
  frontend) start_frontend ;;
  *)
    fail "未知目标: $TARGET（可选: all / mysql / redis / livekit / backend / frontend）"
    exit 1
    ;;
esac

echo "─────────────────────────────────────────────────"
ok "启动完成！PID 已记到 $PID_FILE"
echo ""
echo "📋 访问地址："
echo "  • 前端:    http://localhost:3000"
echo "  • Swagger: http://localhost:8000/docs"
echo "  • 健康:    curl http://localhost:8000/api/health"
echo ""
echo "🛑 关闭: ./scripts/stop.sh"