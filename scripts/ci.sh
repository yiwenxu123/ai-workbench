#!/usr/bin/env bash
# 一键质量检查（CI 入口）：后端测试 + 前端类型/测试/构建 + MCP 测试 + API 巡检
# 用法: scripts/ci.sh [--skip-build] [--verbose]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_BUILD=0
VERBOSE=0
for arg in "$@"; do
  case "$arg" in
    --skip-build) SKIP_BUILD=1 ;;
    --verbose) VERBOSE=1 ;;
  esac
done

PASS=0
FAIL=0
report() {
  local name="$1" ok="$2"
  if [ "$ok" = "0" ]; then
    PASS=$((PASS + 1)); echo "  ✔ $name"
  else
    FAIL=$((FAIL + 1)); echo "  ✘ $name"
  fi
}

echo "===== AI 绘图工作台 CI ====="

echo "[1/5] 后端单元测试"
cd "${ROOT_DIR}/backend"
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY="python3"; fi
if ${PY} -m pytest tests/ -q ${VERBOSE:+-v} >/tmp/ci-backend.log 2>&1; then
  report "后端 pytest (${PY})" 0
else
  report "后端 pytest" 1; tail -5 /tmp/ci-backend.log
fi

echo "[2/5] 前端类型检查 + 单元测试"
cd "${ROOT_DIR}/frontend"
if pnpm exec vue-tsc -b >/tmp/ci-tsc.log 2>&1; then
  report "前端 vue-tsc" 0
else
  report "前端 vue-tsc" 1; tail -5 /tmp/ci-tsc.log
fi
if pnpm vitest run >/tmp/ci-vitest.log 2>&1; then
  report "前端 vitest" 0
else
  report "前端 vitest" 1; tail -5 /tmp/ci-vitest.log
fi

if [ "$SKIP_BUILD" = "0" ]; then
  echo "[3/5] 前端生产构建"
  if pnpm build >/tmp/ci-build.log 2>&1; then
    report "前端 build" 0
  else
    report "前端 build" 1; tail -8 /tmp/ci-build.log
  fi
else
  echo "[3/5] 前端生产构建（已跳过 --skip-build）"
fi

echo "[4/5] MCP 服务器测试"
cd "${ROOT_DIR}/mcp-server"
if node test.js >/tmp/ci-mcp.log 2>&1; then
  report "MCP test.js" 0
else
  report "MCP test.js" 1; tail -5 /tmp/ci-mcp.log
fi

echo "[5/5] API 巡检（冒烟）"
if "${ROOT_DIR}/backend/.venv/bin/python" "${ROOT_DIR}/scripts/check_apis.py" --json >/tmp/ci-apis.json 2>&1; then
  report "API 巡检" 0
else
  report "API 巡检" 1; tail -5 /tmp/ci-apis.json
fi

echo "===== 结果: ${PASS} 通过, ${FAIL} 失败 ====="
[ "$FAIL" = "0" ]
