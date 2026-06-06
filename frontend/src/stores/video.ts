import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiService } from '../api'
import { useProviderStore } from './provider'
import { config } from '../config'
import type { ShotType, CameraMovement, CameraAngle } from '../data/shotLanguage'

export type VideoGenerateStatus = 'idle' | 'generating' | 'success' | 'error'
export type PollingStatus = 'pending' | 'processing' | 'succeed' | 'failed'

export const useVideoStore = defineStore('video', () => {
  const prompt = ref('')
  const negativePrompt = ref('')
  const model = ref('kling-v1')
  const duration = ref(5)
  const resolution = ref('1080p')
  const sourceImage = ref<string | null>(null)
  const shotType = ref<ShotType | undefined>(undefined)
  const cameraMovement = ref<CameraMovement | undefined>(undefined)
  const cameraAngle = ref<CameraAngle | undefined>(undefined)
  const status = ref<VideoGenerateStatus>('idle')
  const progress = ref(0)
  const lastVideo = ref<string | null>(null)
  const lastThumbnail = ref<string | null>(null)
  const error = ref<string | null>(null)
  const taskId = ref<string | null>(null)
  const taskStatus = ref<string | null>(null)

  function validatePrompt(): string | null {
    const trimmed = prompt.value.trim()
    if (!trimmed) return '请输入提示词'
    if (trimmed.length < config.prompt.minLength) return `提示词至少需要 ${config.prompt.minLength} 个字符`
    if (trimmed.length > config.prompt.maxLength) return `提示词不能超过 ${config.prompt.maxLength} 个字符`
    return null
  }

  async function generate(): Promise<boolean> {
    const providerStore = useProviderStore()

    const validationError = validatePrompt()
    if (validationError) {
      error.value = validationError
      return false
    }

    status.value = 'generating'
    progress.value = 0
    error.value = null
    lastVideo.value = null
    lastThumbnail.value = null
    taskId.value = null
    taskStatus.value = null

    try {
      const activeProvider = providerStore.getDefaultProviderByCapability('video')
      if (!activeProvider || !activeProvider.apiKey || !activeProvider.endpoint) {
        error.value = '请先配置视频生成API密钥'
        status.value = 'error'
        return false
      }

      const params = {
        prompt: prompt.value.trim(),
        model: activeProvider.defaultModel || model.value,
        duration: duration.value,
        resolution: resolution.value,
        source_image: sourceImage.value || undefined,
        negative_prompt: negativePrompt.value || undefined,
        api_key: activeProvider.apiKey,
        api_endpoint: activeProvider.endpoint,
      }

      const result = await apiService.generateVideo(params)

      if (!result.success || !result.data) {
        error.value = result.error || '视频生成失败'
        status.value = 'error'
        return false
      }

      const videoUrl = extractVideoUrl(result.data)
      const currentTaskId = result.task_id || null

      if (!videoUrl && currentTaskId) {
        taskStatus.value = 'pending'
        progress.value = 10
        taskId.value = currentTaskId

        const polledUrl = await pollTaskResult(currentTaskId, {
          api_key: activeProvider.apiKey,
          api_endpoint: activeProvider.endpoint,
        })

        if (polledUrl) {
          lastVideo.value = polledUrl
          status.value = 'success'
          progress.value = 100
          return true
        } else if (taskStatus.value !== 'failed') {
          error.value = '视频任务已提交，但尚未完成。请稍后查询任务状态'
          status.value = 'success'
          progress.value = 90
          return true
        } else {
          error.value = error.value || '视频生成失败'
          status.value = 'error'
          return false
        }
      }

      if (videoUrl) {
        lastVideo.value = videoUrl
        const videoData = result.data.data?.[0] || result.data
        lastThumbnail.value = videoData.thumbnail_url || null
        status.value = 'success'
        progress.value = 100
        return true
      }

      error.value = result.error || '视频生成失败'
      status.value = 'error'
      return false
    } catch (e: any) {
      error.value = e.userMessage || e.message || '请求失败，请检查后端服务是否运行'
      status.value = 'error'
      return false
    }
  }

  async function pollTaskResult(
    tid: string,
    params: { api_key?: string; api_endpoint?: string }
  ): Promise<string | null> {
    for (let attempt = 0; attempt < 36; attempt++) {
      const delay = attempt < 6 ? 5000 : 10000
      await sleep(delay)

      try {
        const pollResult = await apiService.checkTaskStatus(tid, params)
        const pollStatus = (pollResult.status || '').toLowerCase() as PollingStatus

        taskStatus.value = pollStatus
        if (pollResult.progress !== undefined && pollResult.progress !== null) {
          progress.value = Math.min(95, 10 + Math.round(pollResult.progress * 0.85))
        } else {
          progress.value = Math.min(95, 10 + attempt * 2)
        }

        if (pollStatus === 'failed') {
          error.value = pollResult.error || '视频生成失败'
          status.value = 'error'
          return null
        }

        const url = pollResult.result_url || extractVideoUrl(pollResult.data)
        if (pollStatus === 'succeed' && url) {
          return url
        }
      } catch {
        continue
      }
    }

    return null
  }

  function setSourceImage(image: string | null) {
    sourceImage.value = image
  }

  function setShotSettings(
    shot?: ShotType,
    movement?: CameraMovement,
    angle?: CameraAngle
  ) {
    shotType.value = shot
    cameraMovement.value = movement
    cameraAngle.value = angle
  }

  function reset(): void {
    status.value = 'idle'
    progress.value = 0
    error.value = null
    taskStatus.value = null
  }

  function clearAll(): void {
    prompt.value = ''
    negativePrompt.value = ''
    sourceImage.value = null
    shotType.value = undefined
    cameraMovement.value = undefined
    cameraAngle.value = undefined
    reset()
  }

  return {
    prompt, negativePrompt, model, duration, resolution,
    sourceImage, shotType, cameraMovement, cameraAngle,
    status, progress, lastVideo, lastThumbnail, error,
    taskId, taskStatus,
    validatePrompt, generate, setSourceImage, setShotSettings, reset, clearAll,
  }
})

function extractVideoUrl(data: any): string | null {
  const candidates = [
    data?.url, data?.video_url, data?.result_url,
    data?.data?.url, data?.data?.video_url, data?.data?.result_url,
    data?.data?.[0]?.url, data?.data?.[0]?.video_url,
    data?.data?.task_result?.videos?.[0]?.url,
    data?.task_result?.videos?.[0]?.url,
    data?.videos?.[0]?.url,
  ]
  return candidates.find(Boolean) || null
}

async function sleep(ms: number): Promise<void> {
  await new Promise(resolve => setTimeout(resolve, ms))
}
