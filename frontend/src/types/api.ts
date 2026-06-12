/**
 * API 类型定义
 */

export interface GenerateParams {
  prompt: string
  model: string
  size: string
  n?: number
  negative_prompt?: string
  seed?: number
  steps?: number
  cfg_scale?: number
  sampler?: string
  extra_params?: Record<string, unknown>
  api_key?: string
  api_endpoint?: string
}

export interface GenerateResult {
  success: boolean
  data?: {
    data?: Array<{
      url?: string
      b64_json?: string
    }>
  }
  error?: string
}

export interface ConfigResult {
  has_backend_config: boolean
  frontend_config_required: boolean
  models: Array<{ id: string; name: string }>
  sizes: string[]
  backend_configured_capabilities: Record<string, boolean>
}

export interface ModelCapability {
  id: string
  name?: string
  description?: string
  provider: string
  capabilities: string[]
  supported_sizes: string[]
  recommended_sizes?: string[]
  min_pixels?: number
  max_pixels?: number
  auto_scale?: boolean
  durations?: number[]
  max_duration?: number
  resolutions?: string[]
  supports_image_input?: boolean
  async: boolean
  pricing?: string
  recommended_scenarios: string[]
  limitations?: string | null
  updated_at: string
}

export interface ModelManifest {
  updated_at: string
  models: ModelCapability[]
}

export interface ApiError {
  message: string
  code?: string
  status?: number
}

export interface UnifiedTemplate {
  id: string
  type: 'image' | 'video' | 'edit'
  taskType: string
  audience: string
  requiredFields: string[]
  promptTemplate: string
  negativePrompt: string
  recommendedModels: string[]
  examples: Array<{ prompt: string; result?: string }>
  source: string
  title: string
  description: string
  updatedAt: string
}

/** 知识条目（统一模型，覆盖术语/公式/案例/行业知识/负面词包/模板） */
export interface KnowledgeEntry {
  id: string
  type: 'term' | 'formula' | 'case' | 'industry' | 'negative_pack' | 'template'
  title: string
  content: string
  tags: string[]
  category: string
  sceneRelevance: Record<string, number>
  quality: number
  usageCount: number
  lastVerified: string
  examples: string[]
  tips: string[]
  relatedTerms: string[]
  prompt: string
  negativePrompt: string
  model: string
}

export interface KnowledgeSearchRequest {
  query: string
  scene?: string
  types?: string[]
  limit?: number
  modelType?: string
}

export interface KnowledgeSearchResponse {
  success: boolean
  items: KnowledgeEntry[]
  total: number
  query: string
  scene: string
}
