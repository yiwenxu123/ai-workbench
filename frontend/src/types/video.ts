export interface VideoHistory {
  id?: number
  prompt: string
  model: string
  duration: number
  resolution: string
  videoUrl: string
  thumbnailUrl?: string
  sourceImageId?: number
  sourceImageUrl?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  taskId?: string
  createdAt: Date
}

export interface VideoModel {
  id: string
  name: string
  provider: string
  maxDuration: number
  supportedResolutions: string[]
  pricePerSecond: number
}

export const videoModels: VideoModel[] = [
  {
    id: 'kling-v1',
    name: '可灵 V1',
    provider: 'kling',
    maxDuration: 10,
    supportedResolutions: ['720p', '1080p'],
    pricePerSecond: 0.2
  },
  {
    id: 'kling-v1-5',
    name: '可灵 V1.5',
    provider: 'kling',
    maxDuration: 10,
    supportedResolutions: ['720p', '1080p'],
    pricePerSecond: 0.3
  },
  {
    id: 'jimeng-v1',
    name: '即梦 V1',
    provider: 'jimeng',
    maxDuration: 5,
    supportedResolutions: ['720p'],
    pricePerSecond: 0.15
  }
]
