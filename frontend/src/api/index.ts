/**
 * API 服务
 * 与后端通信
 */

import axios, { type AxiosInstance } from 'axios'
import { config } from '../config'
import type { GenerateParams, GenerateResult, ConfigResult, ModelManifest, UnifiedTemplate } from '../types/api'

export interface VideoGenerateParams {
  prompt: string
  model?: string
  duration?: number
  resolution?: string
  source_image?: string
  negative_prompt?: string
  api_key?: string
  api_endpoint?: string
}

export interface VideoGenerateResult {
  success: boolean
  data?: {
    data?: Array<{
      url?: string
      video_url?: string
      thumbnail_url?: string
    }>
    url?: string
    video_url?: string
    thumbnail_url?: string
  }
  task_id?: string
  error?: string
}

export interface TaskStatusResult {
  success: boolean
  status: 'pending' | 'processing' | 'succeed' | 'failed' | string
  progress?: number
  result_url?: string
  data?: Record<string, unknown> | null
  error?: string
}

export interface ImageEditParams {
  image: string
  instruction: string
  edit_type?: 'instruction' | 'inpaint' | 'outpaint'
  mask?: string
  api_key?: string
  api_endpoint?: string
  extra_params?: Record<string, unknown>
}

export interface ImageEditResult {
  success: boolean
  image?: string
  data?: {
    data?: Array<{
      url?: string
    }>
  }
  error?: string
}

class ApiService {
  private client: AxiosInstance
  private cache: Map<string, { data: unknown; timestamp: number }> = new Map()
  private readonly cacheTTL = 60000

  constructor() {
    this.client = axios.create({
      baseURL: config.apiBaseUrl,
      timeout: config.request.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
          error.userMessage = '无法连接到后端服务，请确认后端已启动'
        } else if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
          error.userMessage = '请求超时，请检查网络连接或稍后重试'
        } else if (error.response) {
          const status = error.response.status
          if (status === 429) {
            error.userMessage = error.response.data?.error || '请求过于频繁，请稍后再试'
          } else if (status >= 500) {
            error.userMessage = '服务器内部错误，请稍后重试'
          } else {
            error.userMessage = error.response.data?.error || `请求失败 (${status})`
          }
        } else {
          error.userMessage = '网络请求失败，请检查网络连接'
        }
        return Promise.reject(error)
      }
    )
  }

  private getCached<T>(key: string): T | null {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return cached.data as T
    }
    this.cache.delete(key)
    return null
  }

  private setCache(key: string, data: unknown): void {
    this.cache.set(key, { data, timestamp: Date.now() })
  }

  async getConfig(): Promise<ConfigResult> {
    const cacheKey = 'config'
    const cached = this.getCached<ConfigResult>(cacheKey)
    if (cached) return cached

    const res = await this.client.get<ConfigResult>('/config')
    this.setCache(cacheKey, res.data)
    return res.data
  }

  async generateImage(params: GenerateParams): Promise<GenerateResult> {
    const res = await this.client.post<GenerateResult>('/generate', params)
    return res.data
  }

  async generateVideo(params: VideoGenerateParams): Promise<VideoGenerateResult> {
    const res = await this.client.post<VideoGenerateResult>('/generate-video', params, {
      timeout: 300000
    })
    return res.data
  }

  async checkTaskStatus(taskId: string, params?: { api_key?: string; api_endpoint?: string }): Promise<TaskStatusResult> {
    const res = await this.client.get<TaskStatusResult>(`/task-status/${encodeURIComponent(taskId)}`, {
      params
    })
    return res.data
  }

  async editImage(params: ImageEditParams): Promise<ImageEditResult> {
    const res = await this.client.post<ImageEditResult>('/edit-image', params, {
      timeout: 180000
    })
    return res.data
  }

  async getVideoModels(): Promise<{ models: Array<{ id: string; name: string; description: string }>; resolutions: string[]; durations: number[] }> {
    const res = await this.client.get('/models/video')
    return res.data
  }

  async getEditModels(): Promise<{ models: Array<{ id: string; name: string; description: string }>; edit_types: Array<{ id: string; name: string; description: string }> }> {
    const res = await this.client.get('/models/edit')
    return res.data
  }

  async validateApi(params: { api_key: string; api_endpoint: string; provider_type: string }): Promise<{ success: boolean; valid: boolean; message: string; details?: string }> {
    const res = await this.client.post('/validate-api', params)
    return res.data
  }

  async getModelManifest(): Promise<ModelManifest> {
    const cacheKey = 'model-manifest'
    const cached = this.getCached<ModelManifest>(cacheKey)
    if (cached) return cached

    const res = await this.client.get<ModelManifest>('/api/model-manifest')
    this.setCache(cacheKey, res.data)
    return res.data
  }

  async getUnifiedTemplates(): Promise<UnifiedTemplate[]> {
    const res = await this.client.get<UnifiedTemplate[]>('/api/unified-templates')
    return res.data
  }

  clearCache(): void {
    this.cache.clear()
  }
}

export const apiService = new ApiService()

export { ApiService }
export type { GenerateParams, GenerateResult, ConfigResult, ModelManifest }
