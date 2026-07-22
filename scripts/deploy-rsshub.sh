#!/bin/bash
# RSSHub 一键部署脚本（T30 · 决策 1 修复路径）
#
# 功能：
#   1. 通过 docker compose 拉起 rsshub 服务（端口 1200）
#   2. 等服务就绪（健康检查）
#   3. curl 验证 juejin/tag/AI 路由返回有效 RSS
#
# 前置条件：
#   - Docker 已安装（docker --version 可用）
#   - 当前用户有 docker 权限
#
# 用法：
#   ./scripts/deploy-rsshub.sh           # 部署并验证
#   ./scripts/deploy-rsshub.sh status    # 只查状态
#   ./scripts/deploy-rsshub.sh stop      # 停止服务
#   ./scripts/deploy-rsshub.sh logs      # 跟踪日志

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="rsshub"
PORT=1200
VERIFY_ROUTE="/juejin/tag/AI"

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

# ── 检查 Docker ───────────────────────────────────
check_docker() {
  if ! command -v docker > /dev/null 2>&1; then
    fail "docker 未安装。请先安装 Docker Desktop 或 OrbStack"
    exit 1
  fi
  if ! docker info > /dev/null 2>&1; then
    fail "docker daemon 未运行或当前用户无权限"
    exit 1
  fi
}

# ── 启动服务 ──────────────────────────────────────
start_service() {
  cd "$PROJECT_ROOT"

  if is_listening "$PORT"; then
    ok "RSSHub:$PORT 已在跑（host 端口已占用）"
    return 0
  fi

  warn "拉起 rsshub 服务..."
  docker compose up -d rsshub

  # 等待启动（最多 60s）
  local waited=0
  while [ $waited -lt 60 ]; do
    if is_listening "$PORT"; then
      ok "RSSHub:$PORT 已起（等待 ${waited}s）"
      return 0
    fi
    sleep 2
    waited=$((waited + 2))
  done

  fail "RSSHub 启动超时（> 60s）· 看日志: docker compose logs rsshub"
  exit 1
}

# ── 验证路由 ──────────────────────────────────────
verify_route() {
  local url="http://localhost:${PORT}${VERIFY_ROUTE}"
  warn "验证路由: $url"

  local http_code
  http_code=$(curl -s -o /tmp/rsshub-verify.xml -w "%{http_code}" --max-time 10 "$url" || echo "000")

  if [ "$http_code" = "200" ]; then
    local size
    size=$(wc -c < /tmp/rsshub-verify.xml | tr -d ' ')
    if [ "$size" -gt 200 ]; then
      ok "RSSHub 路由返回有效 RSS（HTTP 200 · ${size} bytes · 前 200 字节:）"
      head -c 200 /tmp/rsshub-verify.xml
      echo ""
      return 0
    else
      fail "RSSHub 路由返回 200 但内容过短（${size} bytes）· 可能是空 RSS"
      cat /tmp/rsshub-verify.xml
      exit 1
    fi
  else
    fail "RSSHub 路由失败（HTTP $http_code）"
    cat /tmp/rsshub-verify.xml
    exit 1
  fi
}

# ── 主流程 ──────────────────────────────────────
TARGET="${1:-up}"
echo "🚀 RSSHub 部署脚本（目标: $TARGET · 端口: $PORT）"
echo "─────────────────────────────────────────────────"

case "$TARGET" in
  up)
    check_docker
    start_service
    verify_route
    echo "─────────────────────────────────────────────────"
    ok "部署完成！"
    echo ""
    echo "📋 访问地址："
    echo "  • RSSHub 主页:  http://localhost:$PORT"
    echo "  • 测试路由:     curl http://localhost:$PORT$VERIFY_ROUTE"
    echo "  • 路由文档:     https://docs.rsshub.app/"
    echo ""
    echo "🛑 关闭: ./scripts/deploy-rsshub.sh stop"
    ;;
  status)
    if is_listening "$PORT"; then
      ok "RSSHub:$PORT 在跑"
      curl -s -I --max-time 5 "http://localhost:$PORT/" | head -3
    else
      warn "RSSHub:$PORT 未启动"
    fi
    ;;
  stop)
    cd "$PROJECT_ROOT"
    docker compose stop rsshub
    docker compose rm -f rsshub
    ok "RSSHub 已停止"
    ;;
  logs)
    cd "$PROJECT_ROOT"
    docker compose logs -f rsshub
    ;;
  *)
    fail "未知目标: $TARGET（可选: up / status / stop / logs）"
    exit 1
    ;;
esac
