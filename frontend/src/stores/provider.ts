/**
 * 多供应商状态管理
 * 支持配置多个 API 供应商，每个供应商独立的 API Key 和 Endpoint
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ApiProvider, ProviderType, LLMProvider, ProviderCapability } from '../types/provider'
import { providerPresets, visionProviderPresets, llmProviderPresets } from '../types/provider'

const STORAGE_KEY = 'ai_studio_providers'
const LLM_STORAGE_KEY = 'ai_studio_llm_providers'

function generateId(): string {
  return `provider-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function loadFromStorage(): { providers: ApiProvider[]; defaultId: string | null } {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      const parsed = JSON.parse(data)
      return {
        providers: parsed.providers || [],
        defaultId: parsed.defaultId || null
      }
    }
  } catch (e) {
    console.error('Failed to load providers from storage:', e)
  }
  return { providers: [], defaultId: null }
}

function saveToStorage(providers: ApiProvider[], defaultId: string | null): void {
  const dataToSave = providers.map(p => ({
    ...p,
    apiKey: p.apiKey
  }))
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    providers: dataToSave,
    defaultId
  }))
}

function loadLLMFromStorage(): { providers: LLMProvider[]; defaultId: string | null } {
  try {
    const data = localStorage.getItem(LLM_STORAGE_KEY)
    if (data) {
      const parsed = JSON.parse(data)
      return {
        providers: parsed.providers || [],
        defaultId: parsed.defaultId || null
      }
    }
  } catch (e) {
    console.error('Failed to load LLM providers from storage:', e)
  }
  return { providers: [], defaultId: null }
}

function saveLLMToStorage(providers: LLMProvider[], defaultId: string | null): void {
  const dataToSave = providers.map(p => ({
    ...p,
    apiKey: p.apiKey
  }))
  localStorage.setItem(LLM_STORAGE_KEY, JSON.stringify({
    providers: dataToSave,
    defaultId
  }))
}

function normalizeProvider(provider: ApiProvider): ApiProvider {
  return {
    ...provider,
    capabilities: provider.capabilities?.length ? provider.capabilities : ['image']
  }
}

function capabilityFallbackName(capability: ProviderCapability): string {
  const names: Record<ProviderCapability, string> = {
    image: '图像',
    video: '视频',
    edit: '图片编辑',
    vision: '视觉理解',
    llm: '大语言模型'
  }
  return names[capability]
}

export const useProviderStore = defineStore('provider', () => {
  const providers = ref<ApiProvider[]>([])
  const defaultProviderId = ref<string | null>(null)
  const checkingProviderId = ref<string | null>(null)
  
  const llmProviders = ref<LLMProvider[]>([])
  const defaultLLMProviderId = ref<string | null>(null)

  const defaultProvider = computed(() => 
    providers.value.find(p => p.id === defaultProviderId.value) || providers.value[0] || null
  )

  const activeProviders = computed(() => 
    providers.value.filter(p => p.status === 'active')
  )

  const hasConfiguredProvider = computed(() => 
    providers.value.some(p => p.apiKey && p.endpoint)
  )

  const hasConfiguredImageProvider = computed(() => 
    providers.value.some(p => p.apiKey && p.endpoint && p.capabilities?.includes('image'))
  )

  const hasConfiguredVideoProvider = computed(() => 
    providers.value.some(p => p.apiKey && p.endpoint && p.capabilities?.includes('video'))
  )

  const hasConfiguredEditProvider = computed(() => 
    providers.value.some(p => p.apiKey && p.endpoint && p.capabilities?.includes('edit'))
  )

  const defaultLLMProvider = computed(() => 
    llmProviders.value.find(p => p.id === defaultLLMProviderId.value) || llmProviders.value[0] || null
  )

  const hasConfiguredLLM = computed(() => 
    llmProviders.value.some(p => p.apiKey)
  )

  function init(): void {
    const { providers: saved, defaultId } = loadFromStorage()

    if (saved.length > 0) {
      providers.value = saved.map(p => ({
        ...normalizeProvider(p),
        status: 'inactive' as const
      }))
      defaultProviderId.value = defaultId || saved[0]?.id || null
    }

    migrateLegacyConfig()
    migrateLegacyCapabilityProvider('video', [
      { type: 'kling', name: '可灵AI' },
      { type: 'jimeng', name: '即梦AI' },
      { type: 'runway', name: 'Runway' },
    ])
    migrateLegacyCapabilityProvider('edit', [
      { type: 'aliyun-wanx', name: '阿里云万相编辑' },
    ])

    const { providers: savedLLM, defaultId: defaultLLMId } = loadLLMFromStorage()
    if (savedLLM.length > 0) {
      llmProviders.value = savedLLM.map(p => ({
        ...p,
        status: 'inactive' as const
      }))
      defaultLLMProviderId.value = defaultLLMId || savedLLM[0]?.id || null
    }
  }

  function addProvider(preset: { name: string; type: ProviderType; endpoint?: string; apiKey?: string; models?: string[]; defaultModel?: string; capabilities?: ProviderCapability[] }): ApiProvider {
    const newProvider: ApiProvider = {
      id: generateId(),
      name: preset.name,
      type: preset.type,
      endpoint: preset.endpoint || '',
      apiKey: preset.apiKey || '',
      models: preset.models || [],
      defaultModel: preset.defaultModel || '',
      capabilities: preset.capabilities || ['image'],
      isDefault: providers.value.length === 0,
      status: 'inactive'
    }
    
    providers.value.push(newProvider)
    
    if (newProvider.isDefault) {
      defaultProviderId.value = newProvider.id
    }
    
    saveToStorage(providers.value, defaultProviderId.value)
    return newProvider
  }

  function updateProvider(id: string, updates: Partial<ApiProvider>): void {
    const index = providers.value.findIndex(p => p.id === id)
    if (index !== -1 && providers.value[index]) {
      const current = providers.value[index]
      providers.value[index] = {
        id: current.id,
        name: updates.name ?? current.name,
        type: updates.type ?? current.type,
        endpoint: updates.endpoint ?? current.endpoint,
        apiKey: updates.apiKey ?? current.apiKey,
        models: updates.models ?? current.models,
        defaultModel: updates.defaultModel ?? current.defaultModel,
        capabilities: updates.capabilities ?? current.capabilities ?? ['image'],
        isDefault: updates.isDefault ?? current.isDefault,
        status: updates.status ?? current.status,
        lastChecked: updates.lastChecked ?? current.lastChecked,
        latency: updates.latency ?? current.latency,
        errorMessage: updates.errorMessage ?? current.errorMessage
      }
      saveToStorage(providers.value, defaultProviderId.value)
    }
  }

  function removeProvider(id: string): void {
    const index = providers.value.findIndex(p => p.id === id)
    if (index !== -1) {
      providers.value.splice(index, 1)
      
      if (defaultProviderId.value === id) {
        defaultProviderId.value = providers.value[0]?.id || null
      }
      
      saveToStorage(providers.value, defaultProviderId.value)
    }
  }

  function setDefaultProvider(id: string): void {
    providers.value.forEach(p => {
      p.isDefault = p.id === id
    })
    defaultProviderId.value = id
    saveToStorage(providers.value, defaultProviderId.value)
  }

  function getProviderById(id: string): ApiProvider | undefined {
    return providers.value.find(p => p.id === id)
  }

  function getProvidersByType(type: ProviderType): ApiProvider[] {
    return providers.value.filter(p => p.type === type)
  }

  function getProvidersByCapability(capability: ProviderCapability): ApiProvider[] {
    return providers.value.filter(p => p.capabilities?.includes(capability))
  }

  function getDefaultProviderByCapability(capability: ProviderCapability): ApiProvider | null {
    const candidates = getProvidersByCapability(capability).filter(p => p.apiKey && p.endpoint)
    return candidates.find(p => p.id === defaultProviderId.value) || candidates[0] || null
  }

  function upsertCapabilityProvider(preset: { name: string; type: ProviderType; endpoint: string; apiKey: string; defaultModel?: string; capability: ProviderCapability }): ApiProvider {
    const existing = providers.value.find(p => p.type === preset.type && p.capabilities?.includes(preset.capability))
    if (existing) {
      updateProvider(existing.id, {
        name: preset.name,
        endpoint: preset.endpoint,
        apiKey: preset.apiKey,
        defaultModel: preset.defaultModel || existing.defaultModel,
        models: preset.defaultModel ? [preset.defaultModel] : existing.models,
        capabilities: [...new Set([...(existing.capabilities || []), preset.capability])]
      })
      return providers.value.find(p => p.id === existing.id) || existing
    }

    return addProvider({
      name: preset.name,
      type: preset.type,
      endpoint: preset.endpoint,
      apiKey: preset.apiKey,
      models: preset.defaultModel ? [preset.defaultModel] : [],
      defaultModel: preset.defaultModel || '',
      capabilities: [preset.capability]
    })
  }

  function migrateLegacyConfig(): void {
    const oldKey = localStorage.getItem('ai_studio_api_key')
    const oldEndpoint = localStorage.getItem('ai_studio_api_endpoint')
    if (!oldKey || !oldEndpoint) return

    const alreadyMigrated = providers.value.some(
      p => p.apiKey === oldKey && p.endpoint === oldEndpoint
    )
    if (!alreadyMigrated) {
      addProvider({
        name: '旧版配置 (已迁移)',
        type: 'custom',
        endpoint: oldEndpoint,
        apiKey: oldKey,
        capabilities: ['image', 'video', 'edit'],
      })
    }
    localStorage.removeItem('ai_studio_api_key')
    localStorage.removeItem('ai_studio_api_endpoint')
    console.info('旧版API配置已迁移到统一供应商管理')
  }

  function migrateLegacyCapabilityProvider(capability: ProviderCapability, presets: Array<{ type: ProviderType; name: string }>): void {
    let changed = false
    for (const preset of presets) {
      const apiKey = localStorage.getItem(`${capability}_${preset.type}_apiKey`)
      const endpoint = localStorage.getItem(`${capability}_${preset.type}_endpoint`)
      const model = localStorage.getItem(`${capability}_${preset.type}_model`)
      if (!apiKey || !endpoint) continue
      upsertCapabilityProvider({
        name: preset.name,
        type: preset.type,
        endpoint,
        apiKey,
        defaultModel: model || '',
        capability
      })
      localStorage.removeItem(`${capability}_${preset.type}_apiKey`)
      localStorage.removeItem(`${capability}_${preset.type}_endpoint`)
      localStorage.removeItem(`${capability}_${preset.type}_model`)
      changed = true
    }
    if (changed) {
      console.info(`${capabilityFallbackName(capability)}供应商配置已迁移到统一供应商管理`)
    }
  }

  function addLLMProvider(preset: { name: string; type: ProviderType; llmEndpoint?: string; apiKey?: string; models?: string[]; llmModel?: string; isFree?: boolean }): LLMProvider {
    const newProvider: LLMProvider = {
      id: generateId(),
      name: preset.name,
      type: preset.type,
      endpoint: preset.llmEndpoint || '',
      llmEndpoint: preset.llmEndpoint || '',
      apiKey: preset.apiKey || '',
      models: preset.models || [],
      defaultModel: preset.llmModel || '',
      llmModel: preset.llmModel || '',
      isDefault: llmProviders.value.length === 0,
      status: 'inactive',
      capabilities: ['llm'],
      supportsLLM: true,
      isFree: preset.isFree
    }
    
    llmProviders.value.push(newProvider)
    
    if (newProvider.isDefault) {
      defaultLLMProviderId.value = newProvider.id
    }
    
    saveLLMToStorage(llmProviders.value, defaultLLMProviderId.value)
    return newProvider
  }

  function updateLLMProvider(id: string, updates: Partial<LLMProvider>): void {
    const index = llmProviders.value.findIndex(p => p.id === id)
    if (index !== -1 && llmProviders.value[index]) {
      const current = llmProviders.value[index]
      llmProviders.value[index] = {
        ...current,
        ...updates
      }
      saveLLMToStorage(llmProviders.value, defaultLLMProviderId.value)
    }
  }

  function removeLLMProvider(id: string): void {
    const index = llmProviders.value.findIndex(p => p.id === id)
    if (index !== -1) {
      llmProviders.value.splice(index, 1)
      
      if (defaultLLMProviderId.value === id) {
        defaultLLMProviderId.value = llmProviders.value[0]?.id || null
      }
      
      saveLLMToStorage(llmProviders.value, defaultLLMProviderId.value)
    }
  }

  function setDefaultLLMProvider(id: string): void {
    llmProviders.value.forEach(p => {
      p.isDefault = p.id === id
    })
    defaultLLMProviderId.value = id
    saveLLMToStorage(llmProviders.value, defaultLLMProviderId.value)
  }

  function getLLMProviderById(id: string): LLMProvider | undefined {
    return llmProviders.value.find(p => p.id === id)
  }

  return {
    providers,
    defaultProviderId,
    checkingProviderId,
    defaultProvider,
    activeProviders,
    hasConfiguredProvider,
    hasConfiguredImageProvider,
    hasConfiguredVideoProvider,
    hasConfiguredEditProvider,
    providerPresets,
    visionProviderPresets,
    llmProviders,
    defaultLLMProviderId,
    defaultLLMProvider,
    hasConfiguredLLM,
    llmProviderPresets,
    init,
    addProvider,
    updateProvider,
    removeProvider,
    setDefaultProvider,
    getProviderById,
    getProvidersByType,
    getProvidersByCapability,
    getDefaultProviderByCapability,
    upsertCapabilityProvider,
    addLLMProvider,
    updateLLMProvider,
    removeLLMProvider,
    setDefaultLLMProvider,
    getLLMProviderById
  }
})
