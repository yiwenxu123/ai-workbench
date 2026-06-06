import axios from 'axios'
import type { LLMProvider } from '../types/provider'
import type { KnowledgeEntry } from '../types/api'
import { searchKnowledge, buildKnowledgeContext } from './knowledge'

export interface OptimizeResult {
  success: boolean
  originalPrompt: string
  optimizedPrompt?: string
  optimizedPromptCN?: string
  negativePrompt?: string
  suggestions?: string[]
  style?: string
  explanation?: string
  knowledgeRefs?: KnowledgeEntry[]
  error?: string
}

export interface OptimizeOptions {
  scene?: 'product' | 'marketing' | 'presentation' | 'portrait' | 'illustration' | 'general'
  style?: 'general' | 'professional' | 'minimalist' | 'creative' | 'corporate' | 'casual'
  language?: 'zh' | 'en'
  modelType?: string
}

const SCENE_DESC: Record<string, string> = {
  product: '电商产品展示图，白底或简洁背景，突出产品细节，商业摄影风格，需要专业灯光和材质质感',
  marketing: '社交媒体营销宣传图，视觉冲击力强，吸引眼球，适合小红书/抖音/公众号封面',
  presentation: 'PPT演示文稿配图，简洁专业，留有文字排版空间，适合演示和报告场景',
  portrait: '人物肖像/形象照，专业布光，干净背景，适合头像、企业宣传、个人IP',
  illustration: '商业插画/创意设计，独特的艺术风格，适合品牌传播、概念表达',
  general: '通用场景，根据用户描述自动适配'
}

const STYLE_DESC: Record<string, string> = {
  general: '通用风格，根据内容自动适配最合适的表达方式',
  professional: '专业商务风格，简洁大气，适合正式商业场景',
  minimalist: '极简风格，留白充足，构图干净，色彩克制',
  creative: '创意风格，独特视角，突破常规，适合需要视觉冲击的场景',
  corporate: '企业风格，稳重专业，符合品牌调性',
  casual: '轻松风格，亲切自然，适合生活化内容'
}

const STYLE_LABELS: Record<string, string> = {
  general: '通用风格',
  professional: '专业商务',
  minimalist: '极简风格',
  creative: '创意风格',
  corporate: '企业风格',
  casual: '轻松风格'
}

const QUALITY_KEYWORDS = [
  'high quality', 'professional', 'detailed', 'sharp focus',
  '8k resolution', 'studio lighting', 'clean background'
]

const NEGATIVE_KEYWORDS = [
  'blurry', 'low quality', 'watermark', 'text', 'logo',
  'distorted', 'deformed', 'ugly', 'bad anatomy', 'extra limbs',
  'poorly drawn', 'out of frame', 'cropped'
]

function mapSceneToKnowledgeScene(scene: string): string {
  const map: Record<string, string> = {
    product: 'ecommerce',
    marketing: 'social',
    presentation: 'presentation',
    portrait: 'portrait',
    illustration: 'illustration',
  }
  return map[scene] || 'general'
}

async function buildKnowledgeEnhancedSystemPrompt(
  prompt: string,
  scene: string,
  style: string,
  modelType?: string
): Promise<{ systemPrompt: string; knowledgeRefs: KnowledgeEntry[] }> {
  const sceneDesc = SCENE_DESC[scene] || SCENE_DESC.general
  const styleDesc = STYLE_DESC[style] || STYLE_DESC.professional

  const kbScene = mapSceneToKnowledgeScene(scene)
  const knowledgeEntries = await searchKnowledge(prompt, {
    scene: kbScene,
    limit: 15,
    modelType,
  })

  const knowledgeContext = buildKnowledgeContext(knowledgeEntries, kbScene)

  const systemPrompt = `你是一个专业的 AI 绘图提示词优化助手，专门为商业和工作场景服务。
你的任务是优化用户输入的提示词，使其更适合 AI 图像生成模型。

${knowledgeContext ? `以下是与当前场景相关的专业知识，请充分运用在优化中：

${knowledgeContext}

` : ''}优化原则：
1. 保持用户原始意图不变，但将其转化为更专业、更具画面感的描述
2. 补充必要的画质词和风格词以提升生成质量
3. 确保输出适合${sceneDesc}
4. 采用${styleDesc}
5. 使用英文输出（AI绘图模型对英文支持更好），用逗号分隔关键词
6. 如果提供了知识库中的术语，尽量合理使用
${modelType ? `7. 目标模型为 ${modelType}，注意该模型的能力特点` : ''}

请按以下 JSON 格式输出：
{
  "optimized_prompt": "优化后的英文提示词，用逗号分隔关键词",
  "optimized_prompt_cn": "优化后的中文翻译（对英文的直译），用逗号分隔，方便中文用户理解",
  "negative_prompt": "负面提示词建议（英文），用逗号分隔",
  "suggestions": ["优化建议1", "优化建议2"],
  "detected_style": "检测到的风格类型",
  "explanation": "用中文一段话解释优化思路，分别说明：主体选择、风格应用、构图考量、光线选择、画质设置"
}

注意：
- 提示词必须包含：主体(subject)、场景(scene)、风格(style)、光线(lighting)、画质(quality)
- optimized_prompt 和 optimized_prompt_cn 语义一致，只是语言不同
- negative_prompt 务必返回（即使复用通用词），不要留空
- explanation 要通俗易懂，帮助新手理解每一步的用意`

  return { systemPrompt, knowledgeRefs: knowledgeEntries }
}

function buildOptimizeRequest(
  prompt: string,
  provider: LLMProvider,
  systemPrompt: string
): unknown {
  return {
    model: provider.llmModel,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: `请优化以下提示词：${prompt}` }
    ],
    max_tokens: 1024,
    temperature: 0.7
  }
}

function parseOptimizeResponse(response: unknown, originalPrompt: string, knowledgeRefs: KnowledgeEntry[]): OptimizeResult {
  const data = response as Record<string, unknown>
  const choices = data.choices as Array<Record<string, unknown>>

  if (!choices || !choices[0]) {
    return { success: false, originalPrompt, error: '无法解析响应' }
  }

  const message = choices[0].message as Record<string, unknown>
  const content = message?.content as string || ''

  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0])
      return {
        success: true,
        originalPrompt,
        optimizedPrompt: parsed.optimized_prompt || '',
        optimizedPromptCN: parsed.optimized_prompt_cn || '',
        negativePrompt: parsed.negative_prompt || '',
        suggestions: parsed.suggestions || [],
        style: parsed.detected_style || '',
        explanation: parsed.explanation || '',
        knowledgeRefs: knowledgeRefs.length > 0 ? knowledgeRefs : undefined
      }
    }
  } catch {
    const lines = content.split('\n').filter(l => l.trim())
    const optimizedLine = lines.find(l =>
      l.toLowerCase().includes('optimized') || l.includes('优化')
    )
    if (optimizedLine) {
      const promptMatch = optimizedLine.match(/[:：]\s*(.+)/)
      if (promptMatch && promptMatch[1]) {
        return {
          success: true,
          originalPrompt,
          optimizedPrompt: promptMatch[1].trim(),
          negativePrompt: NEGATIVE_KEYWORDS.join(', '),
          suggestions: ['已自动优化提示词'],
          knowledgeRefs: knowledgeRefs.length > 0 ? knowledgeRefs : undefined
        }
      }
    }
  }

  return { success: false, originalPrompt, error: '无法解析优化结果' }
}

export async function optimizePrompt(
  prompt: string,
  provider: LLMProvider,
  options: OptimizeOptions = {}
): Promise<OptimizeResult> {
  if (!provider.apiKey) {
    return { success: false, originalPrompt: prompt, error: '请先配置大语言模型 API Key' }
  }

  if (!prompt.trim()) {
    return { success: false, originalPrompt: prompt, error: '请输入提示词' }
  }

  const scene = options.scene || 'general'
  const style = options.style || 'professional'

  const { systemPrompt, knowledgeRefs } = await buildKnowledgeEnhancedSystemPrompt(
    prompt, scene, style, options.modelType
  )

  const endpoint = provider.llmEndpoint || provider.endpoint

  try {
    const requestBody = buildOptimizeRequest(prompt, provider, systemPrompt)
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${provider.apiKey}`
    }

    const response = await axios.post(endpoint, requestBody, {
      headers,
      timeout: 30000
    })

    return parseOptimizeResponse(response.data, prompt, knowledgeRefs)
  } catch (error: unknown) {
    const axiosError = error as {
      response?: { data?: { error?: { message?: string } }; status?: number }
      message?: string
    }
    const errorMessage = axiosError.response?.data?.error?.message ||
      axiosError.message || '优化请求失败'

    return {
      success: false,
      originalPrompt: prompt,
      error: errorMessage,
      knowledgeRefs: knowledgeRefs.length > 0 ? knowledgeRefs : undefined
    }
  }
}

export function quickOptimize(prompt: string, options: OptimizeOptions = {}): string {
  const parts: string[] = [prompt]

  const scene = options.scene
  if (scene && scene !== 'general' && SCENE_DESC[scene]) {
    parts.push(SCENE_DESC[scene])
  }

  const style = options.style
  if (style && style !== 'general' && STYLE_LABELS[style]) {
    parts.push(STYLE_LABELS[style])
  }

  parts.push(...QUALITY_KEYWORDS.slice(0, 3))
  return parts.join(', ')
}

export function getDefaultNegativePrompt(): string {
  return NEGATIVE_KEYWORDS.join(', ')
}
