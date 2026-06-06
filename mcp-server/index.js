import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import {
  CallToolRequestSchema,
  GetPromptRequestSchema,
  ListPromptsRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import http from "node:http";

const API_BASE = process.env.AI_WORKBENCH_API_BASE || "http://127.0.0.1:8000";
const MCP_TRANSPORT = process.env.MCP_TRANSPORT || "stdio";
const MCP_PORT = parseInt(process.env.MCP_PORT || "3001", 10);
const MCP_PATH = process.env.MCP_PATH || "/mcp";

const server = new Server(
  {
    name: "ai-workbench-mcp",
    version: "2.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

const tools = [
  {
    name: "generate_image",
    description: "根据自然语言提示词生成图片。",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "画面描述" },
        model: { type: "string", default: "default" },
        size: { type: "string", default: "1024x1024" },
        n: { type: "number", default: 1 },
        negative_prompt: { type: "string" },
        api_key: { type: "string" },
        api_endpoint: { type: "string" },
      },
      required: ["prompt"],
    },
  },
  {
    name: "generate_video",
    description: "提交文生视频或图生视频任务，通常返回 task_id。",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "视频画面、动作和镜头描述" },
        model: { type: "string", default: "kling-v1" },
        duration: { type: "number", default: 5 },
        resolution: { type: "string", default: "1080p" },
        source_image: { type: "string", description: "图生视频的源图片 URL 或 Base64" },
        negative_prompt: { type: "string" },
        api_key: { type: "string" },
        api_endpoint: { type: "string" },
      },
      required: ["prompt"],
    },
  },
  {
    name: "check_task_status",
    description: "查询异步生成任务状态。",
    inputSchema: {
      type: "object",
      properties: {
        task_id: { type: "string" },
        api_key: { type: "string" },
        api_endpoint: { type: "string" },
      },
      required: ["task_id"],
    },
  },
  {
    name: "edit_image",
    description: "用自然语言指令编辑图片，支持指令编辑、局部重绘、扩图。",
    inputSchema: {
      type: "object",
      properties: {
        image: { type: "string", description: "原图 URL 或 Base64" },
        instruction: { type: "string", description: "编辑指令" },
        edit_type: { type: "string", enum: ["instruction", "inpaint", "outpaint"], default: "instruction" },
        mask: { type: "string" },
        api_key: { type: "string" },
        api_endpoint: { type: "string" },
      },
      required: ["image", "instruction"],
    },
  },
  {
    name: "list_templates",
    description: "列出可复用的提示词模板。",
    inputSchema: {
      type: "object",
      properties: {
        category: { type: "string" },
      },
    },
  },
  {
    name: "get_template",
    description: "按模板 ID 获取模板详情。",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string" },
      },
      required: ["id"],
    },
  },
  {
    name: "list_cases",
    description: "列出优秀案例库，可作为创作参考。",
    inputSchema: {
      type: "object",
      properties: {
        category: { type: "string" },
      },
    },
  },
  {
    name: "extract_knowledge",
    description: "将文章内容提取为案例、知识或模板条目，并做去重对比。",
    inputSchema: {
      type: "object",
      properties: {
        content: { type: "string" },
        source_url: { type: "string" },
        target_type: { type: "string", enum: ["cases", "knowledge", "templates"], default: "cases" },
        llm_endpoint: { type: "string" },
        llm_api_key: { type: "string" },
        llm_model: { type: "string", default: "deepseek-chat" },
      },
      required: ["content", "llm_endpoint", "llm_api_key"],
    },
  },
  {
    name: "search_knowledge",
    description: "搜索知识库，查找与用户输入相关的专业术语、行业知识和优秀案例。",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "搜索关键词，如用户输入的提示词" },
        scene: { type: "string", description: "场景: ecommerce/social/presentation/portrait/illustration/general", default: "general" },
        limit: { type: "number", default: 10 },
      },
      required: ["query"],
    },
  },
  {
    name: "optimize_prompt",
    description: "结合知识库内容进行知识增强型提示词优化，返回优化后的英文提示词、中文翻译、负面词和解释。",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "需要优化的原始提示词" },
        scene: { type: "string", enum: ["product", "marketing", "presentation", "portrait", "illustration", "general"], default: "general" },
        style: { type: "string", enum: ["general", "professional", "minimalist", "creative", "corporate", "casual"], default: "general" },
        modelType: { type: "string", description: "目标图像模型ID，如 doubao-seedream-4-5-251128" },
        llm_endpoint: { type: "string", description: "LLM API端点，如 https://api.deepseek.com/v1/chat/completions" },
        llm_api_key: { type: "string", description: "LLM API密钥" },
        llm_model: { type: "string", default: "deepseek-chat" },
      },
      required: ["prompt", "llm_endpoint", "llm_api_key"],
    },
  },
];

const resources = [
  {
    uri: "ai-workbench://templates",
    name: "模板库",
    description: "提示词模板、工作场景模板、节庆模板合集。",
    mimeType: "application/json",
  },
  {
    uri: "ai-workbench://cases",
    name: "案例库",
    description: "优秀 AI 绘图/视频案例。",
    mimeType: "application/json",
  },
  {
    uri: "ai-workbench://model-manifest",
    name: "模型能力注册表",
    description: "模型能力、尺寸、异步状态和推荐场景。",
    mimeType: "application/json",
  },
  {
    uri: "ai-workbench://knowledge",
    name: "术语知识库",
    description: "AI 绘图、视频、镜头语言相关知识。",
    mimeType: "application/json",
  },
];

const prompts = [
  {
    name: "beginner_prompt_rewrite",
    description: "把小白的一句话需求改写为适合 AI 绘图的提示词。",
    arguments: [{ name: "need", description: "用户的一句话需求", required: true }],
  },
  {
    name: "image_to_video_script",
    description: "把静态图片创意扩展为图生视频镜头脚本。",
    arguments: [{ name: "motion", description: "希望画面如何运动", required: true }],
  },
  {
    name: "image_edit_instruction",
    description: "把模糊修改需求改写为清晰图片编辑指令。",
    arguments: [{ name: "change", description: "用户想修改的内容", required: true }],
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));
server.setRequestHandler(ListResourcesRequestSchema, async () => ({ resources }));
server.setRequestHandler(ListPromptsRequestSchema, async () => ({ prompts }));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = request.params.uri;
  const data = await readResource(uri);
  return {
    contents: [
      {
        uri,
        mimeType: "application/json",
        text: JSON.stringify(data, null, 2),
      },
    ],
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const name = request.params.name;
  const args = request.params.arguments || {};
  const text = buildPrompt(name, args);
  return {
    messages: [
      {
        role: "user",
        content: { type: "text", text },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args = {} } = request.params;
    const data = await callTool(name, args);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error calling tool: ${error?.response?.data?.error || error.message}` }],
      isError: true,
    };
  }
});

async function callTool(name, args) {
  if (name === "generate_image") {
    return post("/generate", args);
  }
  if (name === "generate_video") {
    return post("/generate-video", args);
  }
  if (name === "check_task_status") {
    const { task_id, api_key, api_endpoint } = args;
    return get(`/task-status/${encodeURIComponent(task_id)}`, { api_key, api_endpoint });
  }
  if (name === "edit_image") {
    return post("/edit-image", args);
  }
  if (name === "list_templates") {
    const templates = await getTemplates();
    return filterByCategory(templates, args.category);
  }
  if (name === "get_template") {
    const templates = await getTemplates();
    const template = templates.find((item) => item.id === args.id);
    if (!template) throw new Error(`Template not found: ${args.id}`);
    return template;
  }
  if (name === "list_cases") {
    const cases = await get("/api/cases");
    return filterByCategory(cases, args.category);
  }
  if (name === "extract_knowledge") {
    return post("/api/ingest/extract", args);
  }
  if (name === "search_knowledge") {
    const { query, scene, limit, ...rest } = args;
    return post("/api/knowledge/search", { query, scene: scene || "general", limit: limit || 10 });
  }
  if (name === "optimize_prompt") {
    const { prompt, scene, style, modelType, llm_endpoint, llm_api_key, llm_model } = args;
    return post("/api/optimize-prompt", {
      prompt, scene: scene || "general", style: style || "general",
      modelType: modelType || "", llm_endpoint, llm_api_key,
      llm_model: llm_model || "deepseek-chat",
    });
  }
  throw new Error(`Unknown tool: ${name}`);
}

async function readResource(uri) {
  if (uri === "ai-workbench://templates") {
    return getTemplates();
  }
  if (uri === "ai-workbench://cases") {
    return get("/api/cases");
  }
  if (uri === "ai-workbench://model-manifest") {
    return get("/api/model-manifest");
  }
  if (uri === "ai-workbench://knowledge") {
    return get("/api/knowledge");
  }
  throw new Error(`Unknown resource: ${uri}`);
}

function buildPrompt(name, args) {
  if (name === "beginner_prompt_rewrite") {
    return `请把这个小白需求改写为 AI 绘图提示词：${args.need || ""}\n输出：优化后提示词、负面词、为什么这样写。`;
  }
  if (name === "image_to_video_script") {
    return `请把这个图生视频需求整理成 5 秒镜头脚本：${args.motion || ""}\n输出：主体动作、镜头运动、节奏、负面词。`;
  }
  if (name === "image_edit_instruction") {
    return `请把这个图片修改需求改写为清晰编辑指令：${args.change || ""}\n要求说明保留什么、修改什么、避免什么。`;
  }
  throw new Error(`Unknown prompt: ${name}`);
}

async function getTemplates() {
  return get("/api/unified-templates").catch(() => [])
}

function filterByCategory(items, category) {
  if (!category) return items
  return items.filter(
    (item) =>
      item.taskType === category ||
      item.type === category ||
      item.category === category
  )
}

async function get(path, params) {
  const response = await axios.get(`${API_BASE}${path}`, { params });
  return response.data;
}

async function post(path, payload) {
  const response = await axios.post(`${API_BASE}${path}`, payload);
  return response.data;
}

// ── 启动 ──────────────────────────────────────────────────────────

if (MCP_TRANSPORT === "sse") {
  // 远程 SSE 模式：通过 HTTP/SSE 暴露 MCP 服务
  const activeTransports = new Map();

  const httpServer = http.createServer(async (req, res) => {
    // CORS 头
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");

    if (req.method === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    const url = new URL(req.url, `http://localhost:${MCP_PORT}`);

    // GET /mcp — 建立 SSE 流
    if (req.method === "GET" && url.pathname === MCP_PATH) {
      const transport = new SSEServerTransport("/messages", res);
      activeTransports.set(transport.sessionId, transport);
      transport.onclose = () => activeTransports.delete(transport.sessionId);
      await server.connect(transport);
      console.error(`[SSE] 新连接 sessionId=${transport.sessionId}`);
      return;
    }

    // POST /messages — 接收 Agent 发来的消息
    if (req.method === "POST" && url.pathname === "/messages") {
      const sessionId = url.searchParams.get("sessionId");
      const transport = activeTransports.get(sessionId);
      if (!transport) {
        res.writeHead(404, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Session not found" }));
        return;
      }
      await transport.handlePostMessage(req, res);
      return;
    }

    // GET /health — 健康检查
    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/health")) {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        status: "ok",
        name: "ai-workbench-mcp",
        transport: "sse",
        tools: 10,
        activeSessions: activeTransports.size,
        connect: `GET ${MCP_PATH}`,
      }));
      return;
    }

    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Not found" }));
  });

  httpServer.listen(MCP_PORT, "0.0.0.0", () => {
    console.error(`AI Workbench MCP Server (SSE) on http://0.0.0.0:${MCP_PORT}`);
    console.error(`  SSE 端点:  GET http://<host>:${MCP_PORT}${MCP_PATH}`);
    console.error(`  消息端点:  POST http://<host>:${MCP_PORT}/messages`);
    console.error(`  健康检查:  GET http://<host>:${MCP_PORT}/health`);
  });

} else {
  // 本地 stdio 模式（默认，Claude Code 等本地客户端使用）
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`AI Workbench MCP Server (stdio) running, API_BASE=${API_BASE}`);
}
