/**
 * 模型能力注册表 — 唯一数据源（来自 /api/model-manifest）
 */
import { computed } from 'vue'
import { useConfigStore } from '../stores/config'
import type { ModelCapability } from '../types/api'

export interface VideoModelOption {
  value: string
  label: string
  description: string
  provider: string
}

export function useModelManifest() {
  const configStore = useConfigStore()

  const manifest = computed(() => configStore.modelManifest)
  const models = computed(() => manifest.value?.models ?? [])

  function getModel(modelId: string): ModelCapability | undefined {
    return models.value.find((m) => m.id === modelId)
  }

  function hasCapability(modelId: string, capability: string): boolean {
    return getModel(modelId)?.capabilities.includes(capability) ?? false
  }

  function validateSize(modelId: string, size: string): { valid: boolean; reason?: string } {
    const model = getModel(modelId)
    if (!model?.min_pixels && !model?.max_pixels) {
      return { valid: true }
    }

    const [width = 0, height = 0] = size.split('x').map((v) => Number.parseInt(v, 10))
    const pixels = width * height

    if (model.min_pixels && pixels < model.min_pixels) {
      return {
        valid: false,
        reason: `该模型要求最小 ${model.min_pixels.toLocaleString()} 像素`,
      }
    }
    if (model.max_pixels && pixels > model.max_pixels) {
      return {
        valid: false,
        reason: `该模型最大支持 ${model.max_pixels.toLocaleString()} 像素`,
      }
    }
    return { valid: true }
  }

  function getSupportedSizes(modelId: string, allSizes: string[]): string[] {
    const model = getModel(modelId)
    if (model?.supported_sizes?.length) {
      return allSizes.filter((s) => model.supported_sizes.includes(s))
    }
    return allSizes
  }

  function getRecommendedSizes(modelId: string): string[] {
    const model = getModel(modelId)
    return model?.recommended_sizes?.length ? model.recommended_sizes : []
  }

  function getModelNote(modelId: string): string | null {
    return getModel(modelId)?.limitations ?? null
  }

  function getImageModels(): ModelCapability[] {
    return models.value.filter((m) => m.capabilities.includes('image'))
  }

  function getVideoModels(): VideoModelOption[] {
    return models.value
      .filter((m) => m.capabilities.includes('video'))
      .map((m) => ({
        value: m.id,
        label: m.name || m.id,
        description: m.description || m.limitations || m.recommended_scenarios?.join('、') || '',
        provider: m.provider,
      }))
  }

  return {
    manifest,
    models,
    getModel,
    hasCapability,
    validateSize,
    getSupportedSizes,
    getRecommendedSizes,
    getModelNote,
    getImageModels,
    getVideoModels,
  }
}
