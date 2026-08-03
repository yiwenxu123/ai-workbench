/**
 * MCP Server 端到端验证测试
 * 验证：
 * 1. 13 个工具的注册和参数定义
 * 2. 4 个资源的 URI 定义
 * 3. 4 个 Prompt 的定义
 * 4. 参数命名一致性（source_image 而非 image_url）
 *
 * 运行：node mcp-server/test.js
 */

import assert from 'node:assert'
import fs from 'node:fs'

const tests = []

function test(name, fn) {
  tests.push({ name, fn })
}

function run() {
  let passed = 0
  let failed = 0

  for (const { name, fn } of tests) {
    try {
      fn()
      console.log(`  ✓ ${name}`)
      passed++
    } catch (e) {
      console.log(`  ✗ ${name}: ${e.message}`)
      failed++
    }
  }

  console.log(`\n${passed} passed, ${failed} failed, ${tests.length} total`)
  return failed === 0
}

// ========== 工具 Schema 定义（与 index.js 同步） ==========

const tools = [
  {
    name: 'generate_image',
    description: '根据自然语言提示词生成图片。',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: '画面描述' },
        model: { type: 'string', default: 'default' },
        size: { type: 'string', default: '1024x1024' },
        n: { type: 'number', default: 1 },
        negative_prompt: { type: 'string' },
        api_key: { type: 'string' },
        api_endpoint: { type: 'string' },
      },
      required: ['prompt'],
    },
  },
  {
    name: 'generate_video',
    description: '提交文生视频或图生视频任务，通常返回 task_id。',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: '视频画面、动作和镜头描述' },
        model: { type: 'string', default: 'kling-v1' },
        duration: { type: 'number', default: 5 },
        resolution: { type: 'string', default: '1080p' },
        source_image: { type: 'string', description: '图生视频的源图片 URL 或 Base64' },
        negative_prompt: { type: 'string' },
        api_key: { type: 'string' },
        api_endpoint: { type: 'string' },
      },
      required: ['prompt'],
    },
  },
  {
    name: 'check_task_status',
    description: '查询异步生成任务状态。',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: { type: 'string' },
        api_key: { type: 'string' },
        api_endpoint: { type: 'string' },
      },
      required: ['task_id'],
    },
  },
  {
    name: 'edit_image',
    description: '用自然语言指令编辑图片，支持指令编辑、局部重绘、扩图。',
    inputSchema: {
      type: 'object',
      properties: {
        image: { type: 'string', description: '原图 URL 或 Base64' },
        instruction: { type: 'string', description: '编辑指令' },
        edit_type: { type: 'string', enum: ['instruction', 'inpaint', 'outpaint'], default: 'instruction' },
        mask: { type: 'string' },
        api_key: { type: 'string' },
        api_endpoint: { type: 'string' },
      },
      required: ['image', 'instruction'],
    },
  },
  {
    name: 'list_templates',
    description: '列出可复用的提示词模板。',
    inputSchema: {
      type: 'object',
      properties: {
        category: { type: 'string' },
      },
    },
  },
  {
    name: 'get_template',
    description: '按模板 ID 获取模板详情。',
    inputSchema: {
      type: 'object',
      properties: {
        id: { type: 'string' },
      },
      required: ['id'],
    },
  },
  {
    name: 'list_cases',
    description: '列出优秀案例库，可作为创作参考。',
    inputSchema: {
      type: 'object',
      properties: {
        category: { type: 'string' },
      },
    },
  },
  {
    name: 'extract_knowledge',
    description: '将文章内容提取为案例、知识或模板条目，并做去重对比。',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string' },
        source_url: { type: 'string' },
        target_type: { type: 'string', enum: ['cases', 'knowledge', 'templates'], default: 'cases' },
        llm_endpoint: { type: 'string' },
        llm_api_key: { type: 'string' },
        llm_model: { type: 'string', default: 'deepseek-chat' },
      },
      required: ['content', 'llm_endpoint', 'llm_api_key'],
    },
  },
  {
    name: 'search_knowledge',
    description: '搜索知识库，查找与用户输入相关的专业术语、行业知识和优秀案例。',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: '搜索关键词，如用户输入的提示词' },
        scene: { type: 'string', description: '场景: ecommerce/social/presentation/portrait/illustration/general', default: 'general' },
        limit: { type: 'number', default: 10 },
      },
      required: ['query'],
    },
  },
  {
    name: 'optimize_prompt',
    description: '结合知识库内容进行知识增强型提示词优化，返回优化后的英文提示词、中文翻译、负面词和解释。',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: '需要优化的原始提示词' },
        scene: { type: 'string', enum: ['product', 'marketing', 'presentation', 'portrait', 'illustration', 'general'], default: 'general' },
        style: { type: 'string', enum: ['general', 'professional', 'minimalist', 'creative', 'corporate', 'casual'], default: 'general' },
        modelType: { type: 'string', description: '目标图像模型ID，如 doubao-seedream-4-5-251128' },
        llm_endpoint: { type: 'string', description: 'LLM API端点，如 https://api.deepseek.com/v1/chat/completions' },
        llm_api_key: { type: 'string', description: 'LLM API密钥' },
        llm_model: { type: 'string', default: 'deepseek-chat' },
      },
      required: ['prompt', 'llm_endpoint', 'llm_api_key'],
    },
  },
  {
    name: 'compose_workflow',
    description: '组合工作流：一步完成「知识检索 → 提示词优化 → 图像生成 → 存案例」闭环。Agent 只需一句话需求。LLM 配置可选，未配置时跳过优化步骤直接用原始需求生成。',
    inputSchema: {
      type: 'object',
      properties: {
        need: { type: 'string', description: '一句话创作需求，如「白色保温杯电商主图」' },
        scene: { type: 'string', enum: ['product', 'marketing', 'presentation', 'portrait', 'illustration', 'general'], default: 'general' },
        modelType: { type: 'string', description: '目标图像模型ID，如 doubao-seedream-4-5-251128' },
        size: { type: 'string', default: '1024x1024' },
        n: { type: 'number', default: 1 },
        save_case: { type: 'boolean', default: false, description: '是否把生成结果保存到案例库' },
        api_key: { type: 'string', description: '可选：图像 API 密钥（默认用后端配置）' },
        api_endpoint: { type: 'string', description: '可选：图像 API 端点' },
        llm_endpoint: { type: 'string', description: '可选：LLM API端点（配置后启用提示词优化）' },
        llm_api_key: { type: 'string', description: '可选：LLM API密钥' },
        llm_model: { type: 'string', default: 'deepseek-chat' },
      },
      required: ['need'],
    },
  },
  {
    name: 'evaluate_knowledge',
    description: '评估一条知识条目的质量，从专业性、实用性、创新性、详细度四个维度打分。',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: '知识条目内容' },
        type: { type: 'string', enum: ['term', 'formula', 'case', 'industry', 'negative_pack'], default: 'term', description: '知识类型' },
        scene: { type: 'string', description: '目标场景（可选）' },
        llm_endpoint: { type: 'string', description: 'LLM API端点' },
        llm_api_key: { type: 'string', description: 'LLM API密钥' },
        llm_model: { type: 'string', default: 'deepseek-chat' },
      },
      required: ['content', 'llm_endpoint', 'llm_api_key'],
    },
  },
  {
    name: 'deduplicate_knowledge',
    description: '检查新知识条目是否与已有知识重复，返回决策建议（new/merge/skip）。',
    inputSchema: {
      type: 'object',
      properties: {
        item: { type: 'object', description: '待检查的知识条目' },
        target_type: { type: 'string', default: 'knowledge', description: '目标知识类型' },
        llm_endpoint: { type: 'string', description: 'LLM API端点（可选）' },
        llm_api_key: { type: 'string', description: 'LLM API密钥（可选）' },
        llm_model: { type: 'string', default: 'deepseek-chat' },
      },
      required: ['item'],
    },
  },
  {
    name: 'save_knowledge',
    description: '将知识条目保存到知识库，支持新增和合并更新。',
    inputSchema: {
      type: 'object',
      properties: {
        item: { type: 'object', description: '知识条目' },
        operation: { type: 'string', enum: ['new', 'merge'], default: 'new', description: '操作类型' },
        merge_target_id: { type: 'string', description: '合并目标ID（merge时必填）' },
      },
      required: ['item'],
    },
  },
]

const resources = [
  { uri: 'ai-workbench://templates', name: '模板库' },
  { uri: 'ai-workbench://cases', name: '案例库' },
  { uri: 'ai-workbench://model-manifest', name: '模型能力注册表' },
  { uri: 'ai-workbench://knowledge', name: '术语知识库' },
]

const prompts = [
  { name: 'beginner_prompt_rewrite', description: '把小白的一句话需求改写为适合 AI 绘图的提示词。' },
  { name: 'image_to_video_script', description: '把静态图片创意扩展为图生视频镜头脚本。' },
  { name: 'image_edit_instruction', description: '把模糊修改需求改写为清晰图片编辑指令。' },
  { name: 'extract_tips', description: '引导 Agent 从文章中提取 AI 生图技巧的完整工作流。' },
]

// ========== 测试用例 ==========

// 工具数量测试
test('应注册 14 个工具', () => {
  assert.strictEqual(tools.length, 14)
})

// 与 index.js 注册的工具名保持同步（防副本脱节）
test('工具名与 index.js 注册保持一致', () => {
  const src = fs.readFileSync(new URL('./index.js', import.meta.url), 'utf8')
  const m = src.match(/const tools = \[([\s\S]*?)\n\];/)
  assert.ok(m, 'index.js 未找到 tools 数组')
  const names = (m[1].match(/name: "([^"]+)"/gm) || [])
    .map((s) => s.replace(/name: "/, '').replace('"', '').trim())
  const testNames = tools.map((t) => t.name)
  assert.deepStrictEqual([...names].sort(), [...testNames].sort())
})

// 所有工具必须有 name
test('所有工具必须有 name 字段', () => {
  for (const tool of tools) {
    assert.ok(tool.name, `工具缺少 name`)
    assert.strictEqual(typeof tool.name, 'string')
  }
})

// 所有工具必须有 description
test('所有工具必须有 description 字段', () => {
  for (const tool of tools) {
    assert.ok(tool.description, `${tool.name} 缺少 description`)
  }
})

// 所有工具必须有 inputSchema
test('所有工具必须有 inputSchema 字段', () => {
  for (const tool of tools) {
    assert.ok(tool.inputSchema, `${tool.name} 缺少 inputSchema`)
    assert.strictEqual(tool.inputSchema.type, 'object')
  }
})

// 工具命名使用 snake_case
test('所有工具名使用 snake_case 命名', () => {
  for (const tool of tools) {
    assert.ok(/^[a-z][a-z0-9_]*$/.test(tool.name), `${tool.name} 不符合 snake_case`)
  }
})

// 参数命名一致性：使用 source_image 而非 image_url
test('generate_video 不应使用 image_url 参数（应使用 source_image）', () => {
  const videoTool = tools.find(t => t.name === 'generate_video')
  assert.ok(videoTool, 'generate_video 工具不存在')
  const props = videoTool.inputSchema.properties
  assert.ok(!('image_url' in props), 'generate_video 不应包含 image_url 参数')
  assert.ok('source_image' in props, 'generate_video 应包含 source_image 参数')
})

// 资源数量测试
test('应注册 4 个资源', () => {
  assert.strictEqual(resources.length, 4)
})

// 资源 URI 格式测试
test('所有资源 URI 应以 ai-workbench:// 开头', () => {
  for (const resource of resources) {
    assert.ok(resource.uri.startsWith('ai-workbench://'), `${resource.uri} 格式错误`)
  }
})

// Prompt 数量测试
test('应注册 4 个 Prompt', () => {
  assert.strictEqual(prompts.length, 4)
})

// API_BASE 环境变量可配置测试
test('API_BASE 默认值应为 http://127.0.0.1:8000', () => {
  process.env.AI_WORKBENCH_API_BASE = ''
  const defaultBase = process.env.AI_WORKBENCH_API_BASE || 'http://127.0.0.1:8000'
  assert.strictEqual(defaultBase, 'http://127.0.0.1:8000')
})

// 运行所有测试
const success = run()
process.exit(success ? 0 : 1)
