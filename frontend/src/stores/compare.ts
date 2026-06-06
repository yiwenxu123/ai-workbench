import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../api'
import { useProviderStore } from './provider'

export interface CompareItem {
  id: string
  prompt: string
  model: string
  size: string
  status: 'pending' | 'generating' | 'success' | 'error'
  imageUrl: string | null
  error: string | null
}

export type CompareMode = 'prompt' | 'model' | 'size'

export const useCompareStore = defineStore('compare', () => {
  const mode = ref<CompareMode>('prompt')
  const basePrompt = ref('')
  const items = ref<CompareItem[]>([])
  const isGenerating = ref(false)

  const completedCount = computed(() =>
    items.value.filter(item => item.status === 'success').length
  )

  const hasError = computed(() =>
    items.value.some(item => item.status === 'error')
  )

  function generateId(): string {
    return `compare-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  }

  function setupPromptCompare(prompts: string[], model: string, size: string): void {
    mode.value = 'prompt'
    items.value = prompts.map(prompt => ({
      id: generateId(),
      prompt,
      model,
      size,
      status: 'pending',
      imageUrl: null,
      error: null
    }))
  }

  function setupModelCompare(prompt: string, models: string[], size: string): void {
    mode.value = 'model'
    basePrompt.value = prompt
    items.value = models.map(model => ({
      id: generateId(),
      prompt,
      model,
      size,
      status: 'pending',
      imageUrl: null,
      error: null
    }))
  }

  function setupSizeCompare(prompt: string, model: string, sizes: string[]): void {
    mode.value = 'size'
    basePrompt.value = prompt
    items.value = sizes.map(size => ({
      id: generateId(),
      prompt,
      model,
      size,
      status: 'pending',
      imageUrl: null,
      error: null
    }))
  }

  async function generateItem(item: CompareItem): Promise<void> {
    const providerStore = useProviderStore()
    const activeProvider = providerStore.getDefaultProviderByCapability('image')

    if (!activeProvider || !activeProvider.apiKey || !activeProvider.endpoint) {
      item.status = 'error'
      item.error = '请先配置图像生成API密钥'
      return
    }

    item.status = 'generating'

    try {
      const params = {
        prompt: item.prompt,
        model: item.model,
        size: item.size,
        api_key: activeProvider.apiKey,
        api_endpoint: activeProvider.endpoint,
      }

      const result = await apiService.generateImage(params)

      if (result.success && result.data?.data?.[0]) {
        const imageData = result.data.data[0]
        item.imageUrl = imageData.url ||
          (imageData.b64_json ? `data:image/png;base64,${imageData.b64_json}` : null)
        item.status = 'success'
      } else {
        item.error = result.error || '生成失败'
        item.status = 'error'
      }
    } catch {
      item.error = '请求失败'
      item.status = 'error'
    }
  }

  async function generateAll(): Promise<void> {
    if (isGenerating.value) return
    isGenerating.value = true
    await Promise.all(items.value.map(item => generateItem(item)))
    isGenerating.value = false
  }

  function clear(): void {
    items.value = []
    basePrompt.value = ''
  }

  function removeItem(id: string): void {
    items.value = items.value.filter(item => item.id !== id)
  }

  return {
    mode, basePrompt, items, isGenerating, completedCount, hasError,
    setupPromptCompare, setupModelCompare, setupSizeCompare,
    generateAll, clear, removeItem,
  }
})
