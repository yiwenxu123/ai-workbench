/**
 * 视觉模型 API 服务
 * 支持国内主流视觉模型进行图片理解和提示词反推
 */

import axios from 'axios'
import type { VisionProvider } from '../types/provider'

export interface VisionAnalysisResult {
  success: boolean
  prompt?: string
  description?: string
  tags?: string[]
  style?: string
  error?: string
}

function buildDoubaoVisionRequest(imageUrl: string, visionModel: string): unknown {
  return {
    model: visionModel,
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'image_url',
            image_url: { url: imageUrl }
          },
          {
            type: 'text',
            text: '请分析这张图片，生成一个用于AI绘图的提示词。要求：1. 描述图片的主要内容、风格、色调、构图等关键要素；2. 使用英文输出，格式为逗号分隔的关键词；3. 包含画质描述词如"high quality, detailed, 8k"等；4. 直接输出提示词，不要有其他解释。'
          }
        ]
      }
    ],
    max_tokens: 1024
  }
}

function buildAliyunVisionRequest(imageUrl: string, visionModel: string): unknown {
  return {
    model: visionModel,
    input: {
      messages: [
        {
          role: 'user',
          content: [
            { image: imageUrl },
            { text: '请分析这张图片，生成一个用于AI绘图的提示词。要求：1. 描述图片的主要内容、风格、色调、构图等关键要素；2. 使用英文输出，格式为逗号分隔的关键词；3. 包含画质描述词如"high quality, detailed, 8k"等；4. 直接输出提示词，不要有其他解释。' }
          ]
        }
      ]
    },
    parameters: {
      max_tokens: 1024
    }
  }
}

function buildZhipuVisionRequest(imageUrl: string, visionModel: string): unknown {
  return {
    model: visionModel,
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'image_url',
            image_url: { url: imageUrl }
          },
          {
            type: 'text',
            text: '请分析这张图片，生成一个用于AI绘图的提示词。要求：1. 描述图片的主要内容、风格、色调、构图等关键要素；2. 使用英文输出，格式为逗号分隔的关键词；3. 包含画质描述词如"high quality, detailed, 8k"等；4. 直接输出提示词，不要有其他解释。'
          }
        ]
      }
    ],
    max_tokens: 1024
  }
}

function parseVisionResponse(providerType: string, response: unknown): string {
  const data = response as Record<string, unknown>
  
  if (providerType === 'aliyun') {
    const output = data.output as Record<string, unknown>
    const choices = output?.choices as Array<Record<string, unknown>>
    if (choices && choices[0]) {
      const message = choices[0].message as Record<string, unknown>
      return message?.content as string || ''
    }
  } else {
    const choices = data.choices as Array<Record<string, unknown>>
    if (choices && choices[0]) {
      const message = choices[0].message as Record<string, unknown>
      return message?.content as string || ''
    }
  }
  
  return ''
}

function extractTags(prompt: string): string[] {
  const keywords = prompt.split(/[,，]/)
    .map(k => k.trim().toLowerCase())
    .filter(k => k.length > 2 && k.length < 30)
  
  const styleKeywords = [
    'realistic', 'anime', 'cartoon', 'oil painting', 'watercolor',
    'digital art', 'sketch', '3d render', 'photorealistic', 'fantasy',
    'cyberpunk', 'steampunk', 'minimalist', 'impressionist'
  ]
  
  const foundStyles = styleKeywords.filter(s => 
    prompt.toLowerCase().includes(s)
  )
  
  return [...new Set([...keywords.slice(0, 10), ...foundStyles])]
}

export async function analyzeImage(
  provider: VisionProvider,
  imageUrl: string
): Promise<VisionAnalysisResult> {
  if (!provider.apiKey) {
    return {
      success: false,
      error: '请先配置视觉模型 API Key'
    }
  }

  const endpoint = provider.visionEndpoint || provider.endpoint
  
  try {
    let requestBody: unknown
    let headers: Record<string, string> = {}

    switch (provider.type) {
      case 'doubao':
        requestBody = buildDoubaoVisionRequest(imageUrl, provider.visionModel)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${provider.apiKey}`
        }
        break
        
      case 'aliyun':
        requestBody = buildAliyunVisionRequest(imageUrl, provider.visionModel)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${provider.apiKey}`
        }
        break
        
      case 'zhipu':
        requestBody = buildZhipuVisionRequest(imageUrl, provider.visionModel)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${provider.apiKey}`
        }
        break
        
      default:
        return {
          success: false,
          error: '不支持的视觉模型类型'
        }
    }

    const response = await axios.post(endpoint, requestBody, {
      headers,
      timeout: 60000
    })

    const prompt = parseVisionResponse(provider.type, response.data)
    
    if (!prompt) {
      return {
        success: false,
        error: '未能解析视觉模型响应'
      }
    }

    const tags = extractTags(prompt)
    
    return {
      success: true,
      prompt: prompt.trim(),
      description: prompt.trim(),
      tags
    }
  } catch (error: unknown) {
    const axiosError = error as { response?: { data?: { error?: { message?: string } }; status?: number }; message?: string }
    const errorMessage = axiosError.response?.data?.error?.message || 
                         axiosError.message || 
                         '请求视觉模型失败'
    
    return {
      success: false,
      error: errorMessage
    }
  }
}

export async function testVisionProvider(provider: VisionProvider): Promise<{
  success: boolean
  latency?: number
  error?: string
}> {
  const testImageUrl = 'https://via.placeholder.com/256x256/4A90E2/FFFFFF?text=Test'
  
  const startTime = Date.now()
  const result = await analyzeImage(provider, testImageUrl)
  const latency = Date.now() - startTime
  
  if (result.success) {
    return { success: true, latency }
  }
  
  return {
    success: false,
    latency,
    error: result.error
  }
}
