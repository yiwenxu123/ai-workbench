# MCP SSE 远程部署指南

MCP 服务器支持两种模式：本地 Stdio（默认）与远程 SSE。本指南覆盖 SSE 模式的生产部署。

## 架构

```
远程 Agent (Claude Code / Hermes / OpenClaw)
    │  HTTPS/SSE
    ▼
MCP SSE 服务 (node, 端口 3001) ──► 后端 API (FastAPI, 端口 8000)
```

## 1. 前置条件

- Node.js ≥ 18（mcp-server/ 已包含 node_modules）
- 后端已在 8000 端口运行（`cd backend && python3 main.py`）
- 后端 `.env` 已配置（API Key 等）

## 2. 一键启动

```bash
# 默认端口 3001，路径 /mcp
scripts/start-mcp-sse.sh

# 自定义端口/路径
scripts/start-mcp-sse.sh 3002 /sse

# 自动拉起后端（后端未运行时）
AUTO_START_BACKEND=1 scripts/start-mcp-sse.sh
```

健康检查：

```bash
curl http://<服务器IP>:3001/health
# {"status":"ok","name":"ai-workbench-mcp","transport":"sse","tools":14,...}
```

## 3. 生产部署（systemd 守护）

以 Ubuntu/CentOS 为例，将 MCP SSE 注册为常驻服务：

```ini
# /etc/systemd/system/ai-workbench-mcp.service
[Unit]
Description=AI Workbench MCP Server (SSE)
After=network.target ai-workbench-backend.service

[Service]
WorkingDirectory=/opt/AI绘图/mcp-server
Environment=MCP_TRANSPORT=sse
Environment=MCP_PORT=3001
Environment=MCP_PATH=/mcp
ExecStart=/usr/bin/node index.js
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ai-workbench-mcp
```

## 4. 防火墙与反向代理

### 防火墙放行

```bash
# firewalld
sudo firewall-cmd --permanent --add-port=3001/tcp && sudo firewall-cmd --reload
# ufw
sudo ufw allow 3001/tcp
```

### Nginx 反向代理（建议，启用 HTTPS）

```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;
    # ssl_certificate ...;

    location /mcp {
        proxy_pass http://127.0.0.1:3001/mcp;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_read_timeout 3600s;
        chunked_transfer_encoding on;
    }

    location /messages {
        proxy_pass http://127.0.0.1:3001/messages;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        chunked_transfer_encoding on;
    }

    location /health {
        proxy_pass http://127.0.0.1:3001/health;
    }
}
```

注意：SSE 长连接必须关闭 proxy_buffering 并加大 read_timeout。

## 5. Agent 平台接入

### Claude Code

```bash
claude mcp add ai-workbench --transport sse https://mcp.example.com/mcp
```

### Hermes

```json
{
  "mcpServers": {
    "ai-workbench": {
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

## 6. 验证清单

| 步骤 | 命令 | 预期 |
|------|------|------|
| 健康检查 | `curl :3001/health` | `status: ok`，tools ≥ 14 |
| SSE 握手 | `curl -N :3001/mcp` | 输出 `event: endpoint` 及 sessionId |
| 消息调用 | 见 mcp-server/test.js | 11 项测试通过 |
| 后端连通 | 调 `search_knowledge` | 返回知识条目而非 ECONNREFUSED |

## 7. 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| `ECONNREFUSED 127.0.0.1:8000` | 后端未启动 | 先启动后端，或用 AUTO_START_BACKEND=1 |
| SSE 连接被断开 | 反向代理缓冲了响应 | 关闭 proxy_buffering，加大 read_timeout |
| 工具数 < 14 | index.js 加载异常 | 查看 mcp-server 进程日志 |
| 跨域访问被拒 | Agent 平台在浏览器环境 | 需走 HTTPS + CORS（当前仅服务端调用） |
