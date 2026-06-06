/**
 * 供应商类型定义
 */

export type ProviderType = 'doubao' | 'aliyun' | 'zhipu' | 'openai' | 'custom' | 'kling' | 'jimeng' | 'runway' | 'aliyun-wanx'
export type ProviderCapability = 'image' | 'video' | 'edit' | 'vision' | 'llm'

export interface ApiProvider {
  id: string
  name: string
  type: ProviderType
  endpoint: string
  apiKey: string
  models: string[]
  defaultModel: string
  capabilities?: ProviderCapability[]
  isDefault: boolean
  status: 'active' | 'inactive' | 'error' | 'checking'
  lastChecked?: Date
  latency?: number
  errorMessage?: string
}

export interface VisionProvider extends ApiProvider {
  visionEndpoint?: string
  visionModel: string
  supportsVision: boolean
}

export interface LLMProvider extends ApiProvider {
  llmEndpoint?: string
  llmModel: string
  supportsLLM: boolean
  isFree?: boolean
}

export const providerPresets: Omit<ApiProvider, 'id' | 'apiKey' | 'status'>[] = [
  {
    name: '豆包 (火山引擎)',
    type: 'doubao',
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/images/generations',
    models: ['doubao-seedream-4-5-251128', 'doubao-seedream-4-0-250828'],
    defaultModel: 'doubao-seedream-4-5-251128',
    isDefault: false
  },
  {
    name: '通义万相 (阿里云)',
    type: 'aliyun',
    endpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis',
    models: ['wanx-v1', 'wanx-xl', 'wanx-xcessive'],
    defaultModel: 'wanx-v1',
    isDefault: false
  },
  {
    name: '通义千问 Qwen-Image',
    type: 'aliyun',
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/images/generations',
    models: ['qwen-image-plus', 'qwen-image', 'qwen-image-2.0-pro', 'qwen-image-2.0'],
    defaultModel: 'qwen-image-2.0-pro',
    isDefault: false
  },
  {
    name: '智谱 CogView',
    type: 'zhipu',
    endpoint: 'https://open.bigmodel.cn/api/paas/v4/images/generations',
    models: ['cogview-4-plus', 'cogview-4', 'cogview-3-plus', 'cogview-3-flash'],
    defaultModel: 'cogview-4',
    isDefault: false
  },
  {
    name: 'OpenAI DALL-E',
    type: 'openai',
    endpoint: 'https://api.openai.com/v1/images/generations',
    models: ['dall-e-3', 'dall-e-2'],
    defaultModel: 'dall-e-3',
    isDefault: false
  }
]

export const visionProviderPresets: Omit<VisionProvider, 'id' | 'apiKey' | 'status'>[] = [
  {
    name: '豆包视觉理解',
    type: 'doubao',
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/images/generations',
    visionEndpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    models: ['doubao-seedream-4-5-251128'],
    defaultModel: 'doubao-seedream-4-5-251128',
    visionModel: 'doubao-vision-pro-32k',
    isDefault: false,
    supportsVision: true
  },
  {
    name: '通义千问 VL',
    type: 'aliyun',
    endpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis',
    visionEndpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation',
    models: ['wanx-v1'],
    defaultModel: 'wanx-v1',
    visionModel: 'qwen-vl-plus',
    isDefault: false,
    supportsVision: true
  },
  {
    name: '智谱 GLM-4V (免费)',
    type: 'zhipu',
    endpoint: 'https://open.bigmodel.cn/api/paas/v4/images/generations',
    visionEndpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    models: ['cogview-3-flash'],
    defaultModel: 'cogview-3-flash',
    visionModel: 'glm-4v-flash',
    isDefault: false,
    supportsVision: true
  }
]

export const llmProviderPresets: Omit<LLMProvider, 'id' | 'apiKey' | 'status'>[] = [
  {
    name: 'DeepSeek (推荐)',
    type: 'custom',
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    llmEndpoint: 'https://api.deepseek.com/v1/chat/completions',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    defaultModel: 'deepseek-chat',
    llmModel: 'deepseek-chat',
    isDefault: false,
    supportsLLM: true,
    isFree: false
  },
  {
    name: '智谱 GLM-4-Flash (免费)',
    type: 'zhipu',
    endpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    llmEndpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    models: ['glm-4-flash', 'glm-4-plus', 'glm-4-air'],
    defaultModel: 'glm-4-flash',
    llmModel: 'glm-4-flash',
    isDefault: false,
    supportsLLM: true,
    isFree: true
  },
  {
    name: '通义千问 Turbo',
    type: 'aliyun',
    endpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    llmEndpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
    defaultModel: 'qwen-turbo',
    llmModel: 'qwen-turbo',
    isDefault: false,
    supportsLLM: true
  },
  {
    name: '豆包大模型',
    type: 'doubao',
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    llmEndpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    models: ['doubao-pro-32k', 'doubao-lite-32k'],
    defaultModel: 'doubao-pro-32k',
    llmModel: 'doubao-pro-32k',
    isDefault: false,
    supportsLLM: true
  }
]
