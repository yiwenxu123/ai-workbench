# AI Agent 集成指南

本项目支持通过 **MCP (Model Context Protocol)** 和 **OpenAPI Skills** 两种方式集成到主流 AI Agent 平台。

## 架构

```
Agent 平台 (Claude Code / Hermes / OpenClaw)
    │
    ├── MCP 协议 ─── mcp-server/index.js ──── 后端 API (端口 8000)
    │
    └── OpenAPI Skills ─── /skills/openapi.json ── 后端自动生成
```

## MCP 工具一览

| 工具 | 说明 |
|------|------|
| `generate_image` | 根据提示词生成图片 |
| `generate_video` | 提交文生视频/图生视频任务 |
| `check_task_status` | 查询异步任务状态 |
| `edit_image` | 用自然语言编辑图片 |
| `list_templates` | 列出提示词模板 |
| `get_template` | 获取模板详情 |
| `list_cases` | 列出优秀案例 |
| `extract_knowledge` | 从文章提取知识入库 |
| `search_knowledge` | 搜索知识库获取术语/案例 |
| `optimize_prompt` | 知识增强型提示词优化（返回英文+中文） |

## 两种传输模式

### 本地 Stdio 模式（默认）
Agent 与 MCP 服务器在同一台机器上。Agent 启动 MCP 服务器子进程，通过 stdin/stdout 通信。

```bash
# 直接运行，等待 Agent 连接
node mcp-server/index.js
```

### 远程 SSE 模式
Agent 在远程，通过 HTTP/SSE 连接 MCP 服务器。

```bash
# 启动 SSE 模式（监听端口 3001）
MCP_TRANSPORT=sse MCP_PORT=3001 node mcp-server/index.js

# 自定义监听地址和路径
MCP_TRANSPORT=sse MCP_PORT=3001 MCP_PATH=/sse node mcp-server/index.js
```

启动后，MCP 服务器暴露三个端点：

| 端点 | 说明 |
|------|------|
| `GET /mcp` | SSE 端点，Agent 建立连接用 |
| `POST /messages` | 消息端点，Agent 发送请求用（带 sessionId 参数） |
| `GET /health` | 健康检查，返回服务器状态和工具数量 |

---

## 平台接入配置

### 1. Claude Code

**本地 Stdio 模式**（推荐）：

项目根目录已包含 `.mcp.json`，Claude Code 会自动识别。

```bash
# 确保后端运行
cd backend && python3 main.py

# 在项目中启动 Claude Code
claude

# 直接对话即可
# "生成一张白色保温杯电商主图"
# "帮我优化提示词：白色保温杯，高级感"
```

**远程 SSE 模式**：

在目标机器上配置 MCP：

```json
// ~/.claude.json（全局）或 .mcp.json（项目）
{
  "mcpServers": {
    "ai-workbench": {
      "url": "http://<服务器IP>:3001/mcp"
    }
  }
}
```

或使用命令行：

```bash
claude mcp add ai-workbench --transport sse http://<服务器IP>:3001/mcp
```

### 2. Hermes

**本地 Stdio**：

```json
{
  "mcpServers": {
    "ai-workbench": {
      "command": "node",
      "args": ["/path/to/AI绘图/mcp-server/index.js"],
      "env": { "AI_WORKBENCH_API_BASE": "http://127.0.0.1:8000" }
    }
  }
}
```

**远程 SSE**：

```json
{
  "mcpServers": {
    "ai-workbench": {
      "url": "http://<服务器IP>:3001/mcp"
    }
  }
}
```

### 3. OpenClaw

OpenClaw 支持 OpenAPI Skills，配置如下：

```yaml
skills:
  - name: AI绘图工作台
    openapi_url: http://<服务器IP>:8000/skills/openapi.json
    description: AI 图像/视频生成、提示词优化、知识管理
```

自动注册的技能：

| Skill | 触发词 |
|-------|--------|
| `generateImage` | 生成图片、画图、创作 |
| `generateVideo` | 生成视频、视频创作 |
| `checkTaskStatus` | 查询任务状态 |
| `editImage` | 编辑图片、修改图片 |
| `extractContent` | 提取知识、入库 |
| `optimizePrompt` | 优化提示词 |

---

## 快速验证

```bash
# 1. 启动后端
cd backend && python3 main.py

# 2. 启动 MCP SSE 模式
cd mcp-server
MCP_TRANSPORT=sse MCP_PORT=3001 node index.js

# 3. 健康检查
curl http://localhost:3001/health

# 4. 测试知识搜索
curl -X POST http://localhost:8000/api/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"白色保温杯","scene":"ecommerce","limit":3}'

# 5. 测试提示词优化（需配置 LLM API Key）
curl -X POST http://localhost:8000/api/optimize-prompt \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "白色保温杯，女性，高级感",
    "scene": "product",
    "llm_endpoint": "https://api.deepseek.com/v1/chat/completions",
    "llm_api_key": "sk-xxx",
    "llm_model": "deepseek-chat"
  }'
```
