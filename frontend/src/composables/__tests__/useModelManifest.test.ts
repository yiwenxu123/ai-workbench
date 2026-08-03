import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConfigStore } from '@/stores/config'
import { useModelManifest } from '@/composables/useModelManifest'
import type { ModelManifest } from '@/types/api'

const fixture: ModelManifest = {
  updated_at: '2026-06-12',
  models: [
    {
      id: 'doubao-seedream-4-5-251128',
      name: '豆包 Seedream 4.5',
      provider: 'doubao',
      capabilities: ['image'],
      supported_sizes: ['2048x2048', '1024x1024'],
      recommended_sizes: ['2048x2048'],
      min_pixels: 1024 * 1024,
      max_pixels: 4096 * 4096,
      auto_scale: true,
      async: false,
      recommended_scenarios: ['电商'],
      limitations: '测试说明',
      updated_at: '2026-06-12',
    },
    {
      id: 'kling-v1',
      name: '可灵 V1',
      provider: 'kling',
      capabilities: ['video', 'image-to-video'],
      supported_sizes: [],
      async: true,
      recommended_scenarios: ['图生视频'],
      updated_at: '2026-06-12',
    },
  ],
}

describe('useModelManifest', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useConfigStore().modelManifest = fixture
  })

  it('validateSize rejects undersized dimensions', () => {
    const { validateSize } = useModelManifest()
    const result = validateSize('doubao-seedream-4-5-251128', '512x512')
    expect(result.valid).toBe(false)
    expect(result.reason).toContain('像素')
  })

  it('getVideoModels reads from manifest', () => {
    const { getVideoModels } = useModelManifest()
    const models = getVideoModels()
    expect(models.some((m) => m.value === 'kling-v1')).toBe(true)
    expect(models[0]!.label).toBe('可灵 V1')
  })

  it('getSupportedSizes filters by manifest', () => {
    const { getSupportedSizes } = useModelManifest()
    const sizes = getSupportedSizes('doubao-seedream-4-5-251128', [
      '2048x2048',
      '1024x1024',
      '1792x1024',
    ])
    expect(sizes).toEqual(['2048x2048', '1024x1024'])
  })
})
