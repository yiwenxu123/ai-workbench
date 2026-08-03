import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../api'
import { useProviderStore } from './provider'
import { config } from '../config'
import { useCapabilityReady } from '../composables/useCapabilityReady'
import {
  generatePromptWithShot,
  getPromptQualityCheck,
  getCameraMovementById,
} from '../data/shotLanguage'
import type {
  ShotType,
  CameraMovement,
  CameraAngle,
  MovementSpeed,
  EmotionTag,
  StoryboardShot,
  ShotCombination,
} from '../data/shotLanguage'

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
  const movementSpeed = ref<MovementSpeed | undefined>(undefined)
  const emotionTag = ref<EmotionTag | undefined>(undefined)
  const status = ref<VideoGenerateStatus>('idle')
  const progress = ref(0)
  const lastVideo = ref<string | null>(null)
  const lastThumbnail = ref<string | null>(null)
  const lastGenerateParams = ref<Record<string, any> | null>(null)
  const error = ref<string | null>(null)
  const taskId = ref<string | null>(null)
  const taskStatus = ref<string | null>(null)

  const storyboard = ref<StoryboardShot[]>([])
  const activeShotIndex = ref(0)

  const enhancedPrompt = computed(() => {
    return generatePromptWithShot({
      basePrompt: prompt.value,
      shotType: shotType.value,
      movement: cameraMovement.value,
      angle: cameraAngle.value,
      speed: movementSpeed.value,
      emotion: emotionTag.value,
    })
  })

  const promptQuality = computed(() => {
    return getPromptQualityCheck(prompt.value)
  })

  const selectedMovementInfo = computed(() => {
    if (!cameraMovement.value) return null
    return getCameraMovementById(cameraMovement.value)
  })

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

    lastGenerateParams.value = {
      prompt: prompt.value,
      negativePrompt: negativePrompt.value,
      model: model.value,
      duration: duration.value,
      resolution: resolution.value,
      sourceImage: sourceImage.value,
      shotType: shotType.value,
      cameraMovement: cameraMovement.value,
      cameraAngle: cameraAngle.value,
      movementSpeed: movementSpeed.value,
      emotionTag: emotionTag.value,
      enhancedPrompt: enhancedPrompt.value,
      generateTime: new Date().toISOString(),
    }

    try {
      const { getProviderCredentials } = useCapabilityReady()
      const credentials = getProviderCredentials('video')
      if (!credentials) {
        error.value = '请先配置视频生成API密钥'
        status.value = 'error'
        return false
      }

      const activeProvider = providerStore.getDefaultProviderByCapability('video')

      const finalPrompt = enhancedPrompt.value.trim() || prompt.value.trim()

      const params = {
        prompt: finalPrompt,
        model: activeProvider?.defaultModel || model.value,
        duration: duration.value,
        resolution: resolution.value,
        source_image: sourceImage.value || undefined,
        negative_prompt: negativePrompt.value || undefined,
        ...(credentials.api_key && credentials.api_endpoint
          ? { api_key: credentials.api_key, api_endpoint: credentials.api_endpoint }
          : {}),
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
          ...credentials,
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
    params: { api_key?: string; api_endpoint?: string; provider?: string }
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
    angle?: CameraAngle,
    speed?: MovementSpeed,
    emotion?: EmotionTag,
  ) {
    shotType.value = shot
    cameraMovement.value = movement
    cameraAngle.value = angle
    if (speed !== undefined) {
      movementSpeed.value = speed
    }
    if (emotion !== undefined) {
      emotionTag.value = emotion
    }
  }

  function setMovementSpeed(speed: MovementSpeed | undefined) {
    movementSpeed.value = speed
  }

  function setEmotionTag(emotion: EmotionTag | undefined) {
    emotionTag.value = emotion
  }

  function applyMovementWithRecommendedSpeed(movement: CameraMovement) {
    const moveInfo = getCameraMovementById(movement)
    cameraMovement.value = movement
    if (moveInfo?.recommendedSpeed) {
      movementSpeed.value = moveInfo.recommendedSpeed
    }
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
    movementSpeed.value = undefined
    emotionTag.value = undefined
    reset()
  }

  const storyboardTotalDuration = computed(() =>
    storyboard.value.reduce((sum, shot) => sum + shot.duration, 0)
  )

  const activeShot = computed(() =>
    storyboard.value[activeShotIndex.value] || null
  )

  function generateShotId(): string {
    return `shot_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  }

  function addShot(afterIndex?: number): StoryboardShot {
    const newShot: StoryboardShot = {
      id: generateShotId(),
      name: `镜头 ${storyboard.value.length + 1}`,
      prompt: '',
      duration: 5,
    }
    const index = afterIndex !== undefined ? afterIndex + 1 : storyboard.value.length
    storyboard.value.splice(index, 0, newShot)
    activeShotIndex.value = index
    return newShot
  }

  function removeShot(index: number) {
    if (storyboard.value.length <= 1) return
    storyboard.value.splice(index, 1)
    if (activeShotIndex.value >= storyboard.value.length) {
      activeShotIndex.value = storyboard.value.length - 1
    }
  }

  function moveShot(fromIndex: number, toIndex: number) {
    if (fromIndex < 0 || fromIndex >= storyboard.value.length) return
    if (toIndex < 0 || toIndex >= storyboard.value.length) return
    const [shot] = storyboard.value.splice(fromIndex, 1)
    storyboard.value.splice(toIndex, 0, shot)
    activeShotIndex.value = toIndex
  }

  function updateShot(index: number, updates: Partial<StoryboardShot>) {
    if (index < 0 || index >= storyboard.value.length) return
    storyboard.value[index] = { ...storyboard.value[index], ...updates }
  }

  function setActiveShot(index: number) {
    if (index < 0 || index >= storyboard.value.length) return
    activeShotIndex.value = index
  }

  function applyShotToForm(index: number) {
    const shot = storyboard.value[index]
    if (!shot) return
    prompt.value = shot.prompt
    if (shot.negativePrompt) negativePrompt.value = shot.negativePrompt
    shotType.value = shot.shotType
    cameraMovement.value = shot.cameraMovement
    cameraAngle.value = shot.cameraAngle
    movementSpeed.value = shot.movementSpeed
    emotionTag.value = shot.emotionTag
    duration.value = shot.duration
  }

  function applyFormToShot(index: number) {
    if (index < 0 || index >= storyboard.value.length) return
    storyboard.value[index] = {
      ...storyboard.value[index],
      prompt: prompt.value,
      negativePrompt: negativePrompt.value,
      shotType: shotType.value,
      cameraMovement: cameraMovement.value,
      cameraAngle: cameraAngle.value,
      movementSpeed: movementSpeed.value,
      emotionTag: emotionTag.value,
      duration: duration.value,
    }
  }

  function loadShotCombination(combo: ShotCombination) {
    storyboard.value = combo.shots.map((shot, idx) => ({
      id: generateShotId(),
      name: `镜头 ${idx + 1}`,
      prompt: '',
      shotType: shot.type,
      cameraMovement: shot.movement,
      duration: shot.duration,
    }))
    activeShotIndex.value = 0
  }

  function clearStoryboard() {
    storyboard.value = []
    activeShotIndex.value = 0
  }

  function exportStoryboardText(): string {
    const lines: string[] = []
    lines.push('=== 分镜脚本 ===')
    lines.push(`总镜头数：${storyboard.value.length}`)
    lines.push(`总时长：${storyboardTotalDuration.value}秒`)
    lines.push('')
    storyboard.value.forEach((shot, idx) => {
      lines.push(`【镜头 ${idx + 1}】${shot.name} (${shot.duration}秒)`)
      if (shot.shotType) lines.push(`  景别：${shot.shotType}`)
      if (shot.cameraMovement) lines.push(`  运镜：${shot.cameraMovement}`)
      if (shot.cameraAngle) lines.push(`  角度：${shot.cameraAngle}`)
      if (shot.movementSpeed) lines.push(`  速度：${shot.movementSpeed}`)
      if (shot.emotionTag) lines.push(`  情绪：${shot.emotionTag}`)
      if (shot.prompt) lines.push(`  内容：${shot.prompt}`)
      if (shot.transition) lines.push(`  转场：${shot.transition}`)
      if (shot.notes) lines.push(`  备注：${shot.notes}`)
      lines.push('')
    })
    return lines.join('\n')
  }

  return {
    prompt, negativePrompt, model, duration, resolution,
    sourceImage, shotType, cameraMovement, cameraAngle,
    movementSpeed, emotionTag,
    enhancedPrompt, promptQuality, selectedMovementInfo,
    status, progress, lastVideo, lastThumbnail, error,
    taskId, taskStatus, lastGenerateParams,
    storyboard, activeShotIndex, storyboardTotalDuration, activeShot,
    validatePrompt, generate, setSourceImage, setShotSettings,
    setMovementSpeed, setEmotionTag, applyMovementWithRecommendedSpeed,
    reset, clearAll,
    addShot, removeShot, moveShot, updateShot, setActiveShot,
    applyShotToForm, applyFormToShot, loadShotCombination,
    clearStoryboard, exportStoryboardText,
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
