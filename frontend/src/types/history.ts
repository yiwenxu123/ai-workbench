/**
 * 增强的历史记录类型定义
 */

export interface EnhancedHistory {
  id?: number
  prompt: string
  model: string
  size: string
  imageUrl?: string
  thumbnail?: string
  seed?: number
  steps?: number
  cfgScale?: number
  sampler?: string
  negativePrompt?: string
  providerId?: string
  providerName?: string
  generationTime?: number
  notes?: string
  rating?: number
  tags: string[]
  isFavorite: boolean
  createdAt: Date
}

export interface Note {
  id?: number
  targetType: 'history' | 'prompt' | 'workflow'
  targetId: number
  title?: string
  content: string
  tags: string[]
  createdAt: Date
  updatedAt: Date
}
