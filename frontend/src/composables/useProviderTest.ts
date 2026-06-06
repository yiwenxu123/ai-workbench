/**
 * API 连通性检测
 */

import axios from 'axios'
import type { ApiProvider, ProviderType } from '../types/provider'

interface TestResult {
  success: boolean
  latency?: number
  error?: string
  models?: string[]
}

function detectAliyunSubtype(endpoint: string): 'wanx' | 'qwen-v1' | 'qwen-v2' | 'unknown' {
  if (endpoint.includes('compatible-mode')) return 'qwen-v1'
  if (endpoint.includes('multimodal-generation')) return 'qwen-v2'
  if (endpoint.includes('text2image') || endpoint.includes('image-synthesis')) return 'wanx'
  return 'unknown'
}

export async function testImageProvider(provider: ApiProvider): Promise<TestResult> {
  if (!provider.apiKey || !provider.endpoint) {
    return {
      success: false,
      error: 'API Key 或 Endpoint 未配置'
    }
  }

  const startTime = Date.now()

  try {
    const testPayload = buildTestPayload(provider.type, provider.endpoint)
    const headers = buildHeaders(provider)

    const response = await axios.post(provider.endpoint, testPayload, {
      headers,
      timeout: 30000,
      validateStatus: () => true
    })

    const latency = Date.now() - startTime

    if (response.status === 200 || response.status === 201) {
      return {
        success: true,
        latency
      }
    } else if (response.status === 401 || response.status === 403) {
      return {
        success: false,
        latency,
        error: 'API Key 无效或无权限'
      }
    } else if (response.status === 429) {
      return {
        success: false,
        latency,
        error: '请求过于频繁，请稍后重试'
      }
    } else {
      const errorText = typeof response.data === 'string' 
        ? response.data.slice(0, 200) 
        : JSON.stringify(response.data).slice(0, 200)
      return {
        success: false,
        latency,
        error: `API 错误 (${response.status}): ${errorText}`
      }
    }
  } catch (e) {
    const latency = Date.now() - startTime
    const errorMessage = e instanceof Error ? e.message : '连接失败'
    
    if (errorMessage.includes('timeout')) {
      return {
        success: false,
        latency,
        error: '连接超时，请检查网络'
      }
    }
    if (errorMessage.includes('ECONNREFUSED') || errorMessage.includes('ENOTFOUND')) {
      return {
        success: false,
        latency,
        error: '无法连接到服务器，请检查 Endpoint'
      }
    }
    
    return {
      success: false,
      latency,
      error: errorMessage
    }
  }
}

function buildTestPayload(type: ProviderType, endpoint: string = ''): Record<string, unknown> {
  // aliyun 类型需要根据 endpoint 区分不同子类型
  if (type === 'aliyun') {
    const subtype = detectAliyunSubtype(endpoint)
    switch (subtype) {
      case 'qwen-v1':
        // Qwen-Image v1 compatible-mode → OpenAI 扁平格式
        return {
          model: 'qwen-image-plus',
          prompt: 'test',
          size: '1024x1024'
        }
      case 'qwen-v2':
        // Qwen-Image 2.0 → DashScope multimodal-generation messages 格式
        return {
          model: 'qwen-image-2.0-pro',
          input: {
            messages: [
              {
                role: 'user',
                content: [{ text: 'test' }]
              }
            ]
          },
          parameters: {
            size: '1024*1024',
            n: 1
          }
        }
      default:
        // 标准 DashScope text2image 格式（Wanx）
        return {
          model: 'wanx-v1',
          input: { prompt: 'test' },
          parameters: { size: '1024x1024', n: 1 }
        }
    }
  }

  switch (type) {
    case 'doubao':
      return {
        model: 'doubao-seedream-4-5-251128',
        prompt: 'test',
        size: '2048x2048',
        response_format: 'url'
      }
    case 'zhipu':
      return {
        model: 'cogview-3-flash',
        prompt: 'test',
        size: '1024x1024'
      }
    case 'openai':
      return {
        model: 'dall-e-2',
        prompt: 'test',
        size: '256x256',
        n: 1
      }
    default:
      return {
        prompt: 'test',
        size: '1024x1024'
      }
  }
}

function buildHeaders(provider: ApiProvider): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }

  switch (provider.type) {
    case 'doubao':
    case 'openai':
      headers['Authorization'] = `Bearer ${provider.apiKey}`
      break
    case 'aliyun':
      headers['Authorization'] = `Bearer ${provider.apiKey}`
      if (
        !provider.endpoint.includes('compatible-mode') &&
        !provider.endpoint.includes('multimodal-generation')
      ) {
        headers['X-DashScope-Async'] = 'enable'
      }
      break
    case 'zhipu':
      headers['Authorization'] = `Bearer ${provider.apiKey}`
      break
    default:
      headers['Authorization'] = `Bearer ${provider.apiKey}`
  }

  return headers
}
