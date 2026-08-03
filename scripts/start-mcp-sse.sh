#!/usr/bin/env bash
# 一键启动 MCP SSE 模式（供远程 Agent 平台接入）
# 用法: scripts/start-mcp-sse.sh [端口] [路径]
#   - 端口: MCP SSE 监听端口（默认 3001）
#   - 路径: SSE 端点路径（默认 /mcp）
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-3001}"
MCP_PATH="${2:-/mcp}"

echo "[1/3] 检查环境..."
command -v node >/dev/null 2>&1 || { echo "缺少 node，请先安装 Node.js。"; exit 1; }

echo "[2/3] 检查后端健康状态..."
if curl -sf -m 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "后端已在 8000 端口运行，直接复用。"
else
  echo "后端未运行。请先启动后端："
  echo "  cd backend && python3 main.py"
  echo "（如需自动拉起，可设置 AUTO_START_BACKEND=1 后重试）"
  if [ "${AUTO_START_BACKEND:-0}" = "1" ]; then
    (cd "${ROOT_DIR}/backend" && python3 main.py) &
    BACKEND_PID=$!
    trap 'kill "${BACKEND_PID:-}" 2>/dev/null || true' EXIT
    echo "等待后端就绪..."
    for i in $(seq 1 15); do
      curl -sf -m 1 http://127.0.0.1:8000/health >/dev/null 2>&1 && break
      sleep 1
    done
  else
    exit 1
  fi
fi

echo "[3/3] 启动 MCP SSE 服务（端口 ${PORT}，路径 ${MCP_PATH}）..."
cd "${ROOT_DIR}/mcp-server"
MCP_TRANSPORT=sse MCP_PORT="${PORT}" MCP_PATH="${MCP_PATH}" node index.js

# 健康检查示例：
#   curl http://localhost:3001/health
# Agent 接入配置：
#   {"mcpServers": {"ai-workbench": {"url": "http://<服务器IP>:3001/mcp"}}}
