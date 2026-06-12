#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/3] 检查环境..."
command -v pnpm >/dev/null 2>&1 || { echo "缺少 pnpm，请先安装 pnpm。"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "缺少 python3，请先安装 Python 3。"; exit 1; }

echo "[2/3] 启动后端（FastAPI）..."
echo "提示：首次启动请先在 backend/ 配置 .env，并安装依赖：pip install -r requirements.txt"
echo "提示：知识库会在后端首次启动时从 backend/data/*.json 自动灌入（无需手动 migrate）"
(cd "${ROOT_DIR}/backend" && python3 "main.py") &
BACKEND_PID=$!

echo "[3/3] 启动前端（Vite）..."
echo "提示：首次启动请先在 frontend/ 安装依赖：pnpm install"
(cd "${ROOT_DIR}/frontend" && pnpm "dev") &
FRONTEND_PID=$!

trap 'kill "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null || true' EXIT

echo "已启动。按 Ctrl+C 停止。"
wait

