import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCapabilityReady } from '../useCapabilityReady'
import { useConfigStore } from '@/stores/config'
import { useProviderStore } from '@/stores/provider'

describe('useCapabilityReady', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('allows image generation when backend configured', () => {
    const configStore = useConfigStore()
    configStore.serverConfig = {
      models: [],
      backend_configured_capabilities: { image: true, video: false, edit: false },
    } as any

    const { canUseImage, getProviderCredentials } = useCapabilityReady()
    expect(canUseImage.value).toBe(true)
    expect(getProviderCredentials('image')).toEqual({ provider: undefined })
  })

  it('requires frontend provider credentials when backend not configured', () => {
    const providerStore = useProviderStore()
    providerStore.providers = [{
      id: 'p1',
      name: 'Test',
      type: 'openai',
      capabilities: ['image'],
      apiKey: 'sk-test',
      endpoint: 'https://api.example.com',
      status: 'active',
    } as any]
    providerStore.defaultProviderId = 'p1'

    const { canUseImage, getProviderCredentials } = useCapabilityReady()
    expect(canUseImage.value).toBe(true)
    expect(getProviderCredentials('image')).toEqual({
      api_key: 'sk-test',
      api_endpoint: 'https://api.example.com',
      provider: 'openai',
    })
  })

  it('returns null when neither backend nor frontend configured', () => {
    const { canUseImage, getProviderCredentials } = useCapabilityReady()
    expect(canUseImage.value).toBe(false)
    expect(getProviderCredentials('image')).toBeNull()
  })
})
