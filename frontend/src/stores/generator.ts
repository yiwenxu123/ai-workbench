import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../api'
import { useProviderStore } from './provider'
import { useHistoryStore } from './history'
import { config } from '../config'
import { useCapabilityReady } from '../composables/useCapabilityReady'
import type { GenerateParams } from '../types'

export type GenerateStatus = 'idle' | 'generating' | 'success' | 'error'
export type GenerateStage = 'preparing' | 'submitting' | 'processing' | 'downloading' | null

const STAGE_LABELS: Record<string, string> = {
  preparing: '准备中',
  submitting: '提交请求',
  processing: 'AI 创作中',
  downloading: '下载结果',
}

export const useGeneratorStore = defineStore('generator', () => {
  const prompt = ref('')
  const negativePrompt = ref('')
  const model = ref('default')
  const size = ref('1024x1024')
  const seed = ref<number | undefined>(undefined)
  const steps = ref<number | undefined>(undefined)
  const cfgScale = ref<number | undefined>(undefined)
  const sampler = ref<string | undefined>(undefined)
  const status = ref<GenerateStatus>('idle')
  const stage = ref<GenerateStage>(null)
  const progress = ref(0)
  const lastImage = ref<string | null>(null)
  const error = ref<string | null>(null)
  const generationTime = ref<number | null>(null)
  const estimatedRemaining = ref<number | null>(null)

  const stageLabel = computed(() => stage.value ? STAGE_LABELS[stage.value] : '')

  function validatePrompt(): string | null {
    const trimmed = prompt.value.trim()
    if (!trimmed) return '请输入提示词'
    if (trimmed.length < config.prompt.minLength) return `提示词至少需要 ${config.prompt.minLength} 个字符`
    if (trimmed.length > config.prompt.maxLength) return `提示词不能超过 ${config.prompt.maxLength} 个字符`
    return null
  }

  async function generate(): Promise<boolean> {
    const providerStore = useProviderStore()
    const historyStore = useHistoryStore()

    const validationError = validatePrompt()
    if (validationError) {
      error.value = validationError
      return false
    }

    error.value = null

    const { getProviderCredentials } = useCapabilityReady()
    const credentials = getProviderCredentials('image')
    if (!credentials) {
      error.value = '请先配置图像生成API密钥'
      return false
    }

    const activeProvider = providerStore.getDefaultProviderByCapability('image')

    status.value = 'generating'
    stage.value = 'preparing'
    progress.value = 0
    lastImage.value = null
    generationTime.value = null
    estimatedRemaining.value = null

    const startTime = Date.now()

    // 阶段进度映射
    const stageTimers: ReturnType<typeof setTimeout>[] = []
    const advanceStage = (s: GenerateStage, pct: number, delay: number) => {
      stageTimers.push(setTimeout(() => {
        stage.value = s
        progress.value = pct
      }, delay))
    }
    advanceStage('submitting', 10, 200)
    advanceStage('processing', 30, 800)
    // processing 阶段持续估算剩余时间
    const estimateInterval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000
      if (elapsed > 2) {
        // 估算总时长约 8-15 秒，根据已用时间线性推算
        const estimated = Math.max(8, elapsed * 2.5)
        estimatedRemaining.value = Math.max(0, estimated - elapsed)
        progress.value = Math.min(85, 30 + (elapsed / estimated) * 55)
      }
    }, 500)

    try {
      const resolvedModel = model.value === 'default' && activeProvider?.defaultModel
        ? activeProvider.defaultModel
        : model.value

      const params: GenerateParams = {
        prompt: prompt.value.trim(),
        model: resolvedModel,
        size: size.value,
        negative_prompt: negativePrompt.value || undefined,
        seed: seed.value,
        steps: steps.value,
        cfg_scale: cfgScale.value,
        sampler: sampler.value,
        ...(credentials.api_key && credentials.api_endpoint
          ? { api_key: credentials.api_key, api_endpoint: credentials.api_endpoint }
          : {}),
      }

      const result = await apiService.generateImage(params)
      generationTime.value = (Date.now() - startTime) / 1000

      if (result.success && result.data?.data?.[0]) {
        clearInterval(estimateInterval)
        stage.value = 'downloading'
        progress.value = 90

        const imageData = result.data.data[0]
        lastImage.value = imageData.url ||
          (imageData.b64_json ? `data:image/png;base64,${imageData.b64_json}` : null)

        await historyStore.add({
          prompt: prompt.value,
          model: model.value,
          size: size.value,
          imageUrl: lastImage.value || undefined,
          seed: seed.value,
          steps: steps.value,
          cfgScale: cfgScale.value,
          sampler: sampler.value,
          negativePrompt: negativePrompt.value || undefined,
          providerId: activeProvider?.id,
          providerName: activeProvider?.name,
          generationTime: generationTime.value,
        })

        status.value = 'success'
        progress.value = 100
        return true
      } else {
        clearInterval(estimateInterval)
        stageTimers.forEach(clearTimeout)
        error.value = result.error || '生成失败'
        status.value = 'error'
        stage.value = null
        return false
      }
    } catch (e: any) {
      clearInterval(estimateInterval)
      stageTimers.forEach(clearTimeout)
      error.value = e.userMessage || e.message || '请求失败，请检查后端服务是否运行'
      status.value = 'error'
      stage.value = null
      return false
    }
  }

  function reset(): void {
    status.value = 'idle'
    stage.value = null
    progress.value = 0
    error.value = null
    estimatedRemaining.value = null
  }

  return {
    prompt, negativePrompt, model, size, seed, steps, cfgScale, sampler,
    status, stage, progress, lastImage, error, generationTime,
    estimatedRemaining, stageLabel,
    validatePrompt, generate, reset,
  }
})
