import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiService } from '../api'
import { useProviderStore } from './provider'
import { useHistoryStore } from './history'
import { config } from '../config'
import type { GenerateParams } from '../types'

export type GenerateStatus = 'idle' | 'generating' | 'success' | 'error'

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
  const progress = ref(0)
  const lastImage = ref<string | null>(null)
  const error = ref<string | null>(null)
  const generationTime = ref<number | null>(null)

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

    const activeProvider = providerStore.getDefaultProviderByCapability('image')
    if (!activeProvider || !activeProvider.apiKey || !activeProvider.endpoint) {
      error.value = '请先配置图像生成API密钥'
      return false
    }

    status.value = 'generating'
    progress.value = 0
    lastImage.value = null
    generationTime.value = null

    const startTime = Date.now()

    try {
      const resolvedModel = model.value === 'default' && activeProvider.defaultModel
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
        api_key: activeProvider.apiKey,
        api_endpoint: activeProvider.endpoint,
      }

      const result = await apiService.generateImage(params)
      generationTime.value = (Date.now() - startTime) / 1000

      if (result.success && result.data?.data?.[0]) {
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
        error.value = result.error || '生成失败'
        status.value = 'error'
        return false
      }
    } catch (e: any) {
      error.value = e.userMessage || e.message || '请求失败，请检查后端服务是否运行'
      status.value = 'error'
      return false
    }
  }

  function reset(): void {
    status.value = 'idle'
    progress.value = 0
    error.value = null
  }

  return {
    prompt, negativePrompt, model, size, seed, steps, cfgScale, sampler,
    status, progress, lastImage, error, generationTime,
    validatePrompt, generate, reset,
  }
})
