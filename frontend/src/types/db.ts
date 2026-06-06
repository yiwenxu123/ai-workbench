/**
 * 数据库类型定义
 */

export interface Prompt {
  id?: number
  title: string
  content: string
  tags: string[]
  category: string
  createdAt: Date
  updatedAt: Date
}

export interface History {
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

export interface VideoHistory {
  id?: number
  prompt: string
  model: string
  duration: number
  resolution: string
  videoUrl?: string
  thumbnailUrl?: string
  sourceImageId?: number
  sourceImageUrl?: string
  shotType?: string
  cameraMovement?: string
  cameraAngle?: string
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

export interface GalleryItem {
  id?: number
  type: 'image' | 'video'
  itemId: number
  thumbnail?: string
  prompt: string
  tags: string[]
  isFavorite: boolean
  createdAt: Date
}

export type PromptCategory = 'general' | 'character' | 'landscape' | 'art' | 'other'

export interface PromptFormData {
  title: string
  content: string
  category: PromptCategory
  tags: string[]
}

export type TemplateCategory = 'product' | 'marketing' | 'presentation' | 'portrait' | 'illustration' | 'social' | 'general'

export interface PromptTemplate {
  id?: number
  name: string
  content: string
  category: TemplateCategory
  tags: string[]
  isOfficial: boolean
  negativePrompt?: string
  recommendedSize?: string
  tips?: string[]
  placeholders?: string[]
  createdAt: Date
  updatedAt: Date
}

export interface TemplateFormData {
  name: string
  content: string
  category: TemplateCategory
  tags: string[]
  negativePrompt?: string
  recommendedSize?: string
  tips?: string[]
}

export type VideoTemplateCategory = 'product' | 'brand' | 'education' | 'culture' | 'social' | 'festival'

export interface VideoTemplate {
  id?: number
  name: string
  category: VideoTemplateCategory
  description: string
  icon: string
  fields: Array<{
    key: string
    label: string
    type: 'text' | 'textarea' | 'select' | 'multiselect'
    placeholder: string
    options?: Array<{ value: string; label: string }>
    required: boolean
    defaultValue?: string
  }>
  promptTemplate: string
  negativePrompt?: string
  recommendedDuration: number
  recommendedResolution: string
  tips: string[]
  tags: string[]
  isOfficial: boolean
  createdAt: Date
  updatedAt: Date
}
