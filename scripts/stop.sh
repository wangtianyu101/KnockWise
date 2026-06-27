#!/bin/bash
# Intervue 一键关闭脚本
#
# 用法：
#   ./scripts/stop.sh           # 按 PID 文件关 livekit + backend + frontend（不动 MySQL/Redis）
#   ./scripts/stop.sh all       # 同上 + 关 MySQL/Redis
#   ./scripts/stop.sh backend   # 只关后端（按名字精确匹配 PID 文件）
#   ./scripts/stop.sh --force   # 不走优雅关闭，直接 SIGKILL
#
# 设计要点：
#   - 优雅关闭：SIGTERM → 等 5s → 还在就 SIGKILL
#   - 默认不动 MySQL/Redis（brew services 管的，关了会影响其他项目）
#   - 只关 PID 文件里记录的进程（不会误杀同名进程）

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="/tmp/intervue-pids.txt"
TARGET="${1:-}"
FORCE_KILL=false

[[ "$1" == "--force" ]] && { FORCE_KILL=true; shift; TARGET="${1:-}"; }

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; }

stop_pid() {
  local name=$1
  local pid=$2

  if ! kill -0 "$pid" 2>/dev/null; then
    warn "$name (PID $pid) 已不在，跳过"
    return
  fi

  if [ "$FORCE_KILL" = true ]; then
    kill -9 "$pid" 2>/dev/null || true
    ok "$name (PID $pid) 已 SIGKILL"
  else
    kill -TERM "$pid" 2>/dev/null || true
    # 等 5 秒
    for i in 1 2 3 4 5; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
      warn "$name (PID $pid) 5s 内未退出，强制 SIGKILL"
      kill -9 "$pid" 2>/dev/null || true
    else
      ok "$name (PID $pid) 已 SIGTERM 关闭"
    fi
  fi
}

stop_brew_services() {
  local svc=$1
  if brew services list 2>/dev/null | grep -q "^$svc.*started"; then
    warn "关闭 brew service: $svc"
    brew services stop "$svc" 2>&1 | tail -2
    ok "$svc 已停"
  else
    ok "$svc 未在运行（brew services）"
  fi
}

# ── 主流程 ──────────────────────────────────────
echo "🛑 Intervue 关闭脚本"
echo "─────────────────────────────────────────────────"

# 读 PID 文件（如果文件不存在或为空，回退到按端口查进程）
PID_CONTENT=""
if [ -f "$PID_FILE" ]; then
  PID_CONTENT=$(cat "$PID_FILE" 2>/dev/null || true)
fi

if [ -z "$PID_CONTENT" ]; then
  warn "PID 文件空/不存在（之前可能没通过 start.sh 启动？）"
  echo "回退到按端口找进程..."
  for entry in "livekit:7880" "backend:8000" "frontend:3000"; do
    name="${entry%:*}"; port="${entry##*:}"
    pid=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -1)
    if [ -n "$pid" ]; then
      warn "  发现 $name 在 PID $pid（端口 $port）"
      stop_pid "$name" "$pid"
    fi
  done
else
  while read -r name pid; do
    # 按 TARGET 过滤
    if [ -n "$TARGET" ] && [ "$TARGET" != "all" ] && [ "$name" != "$TARGET" ]; then
      continue
    fi
    stop_pid "$name" "$pid"
  done < "$PID_FILE"
  # 关完清空
  > "$PID_FILE"
fi

# 关 MySQL/Redis（只在 TARGET=all 时）
if [ "$TARGET" = "all" ]; then
  echo "─────────────────────────────────────────────────"
  echo "🍺 关闭 brew services（MySQL/Redis）"
  stop_brew_services "mysql"
  stop_brew_services "redis"
fi

echo "─────────────────────────────────────────────────"
ok "关闭完成"
echo ""
echo "🚀 重启: ./scripts/start.sh"