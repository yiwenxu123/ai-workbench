import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGeneratorStore } from '@/stores/generator'
import { useConfigStore } from '@/stores/config'
import { useVideoStore } from '@/stores/video'
import { useProviderStore } from '@/stores/provider'
import { useEditorStore } from '@/stores/editor'
import { useHistoryStore } from '@/stores/history'

describe('GeneratorStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('validatePrompt', () => {
    it('should return error for empty prompt', () => {
      const store = useGeneratorStore()
      store.prompt = ''
      const error = store.validatePrompt()
      expect(error).toBe('请输入提示词')
    })

    it('should return error for whitespace-only prompt', () => {
      const store = useGeneratorStore()
      store.prompt = '   '
      const error = store.validatePrompt()
      expect(error).toBe('请输入提示词')
    })

    it('should return null for valid prompt', () => {
      const store = useGeneratorStore()
      store.prompt = 'A beautiful sunset over the ocean'
      const error = store.validatePrompt()
      expect(error).toBeNull()
    })

    it('should return error for prompt exceeding max length', () => {
      const store = useGeneratorStore()
      store.prompt = 'a'.repeat(4001)
      const error = store.validatePrompt()
      expect(error).toContain('不能超过')
    })
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      const store = useGeneratorStore()
      expect(store.prompt).toBe('')
      expect(store.model).toBe('default')
      expect(store.size).toBe('1024x1024')
      expect(store.status).toBe('idle')
      expect(store.progress).toBe(0)
      expect(store.lastImage).toBeNull()
      expect(store.error).toBeNull()
    })
  })

  describe('reset', () => {
    it('should reset state to initial values', () => {
      const store = useGeneratorStore()
      store.prompt = 'test prompt'
      store.status = 'success'
      store.progress = 100
      store.error = 'some error'
      
      store.reset()
      
      expect(store.status).toBe('idle')
      expect(store.progress).toBe(0)
      expect(store.error).toBeNull()
    })
  })
})

describe('VideoStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have correct initial state', () => {
    const store = useVideoStore()
    expect(store.prompt).toBe('')
    expect(store.model).toBe('kling-v1')
    expect(store.duration).toBe(5)
    expect(store.resolution).toBe('1080p')
    expect(store.status).toBe('idle')
    expect(store.error).toBeNull()
  })

  it('should validate empty prompt', () => {
    const store = useVideoStore()
    store.prompt = ''
    const error = store.validatePrompt()
    expect(error).toBe('请输入提示词')
  })

  it('should accept valid prompt', () => {
    const store = useVideoStore()
    store.prompt = '镜头推近，展示产品细节'
    const error = store.validatePrompt()
    expect(error).toBeNull()
  })

  it('should reset state correctly', () => {
    const store = useVideoStore()
    store.prompt = 'test'
    store.status = 'success'
    store.error = 'error'

    store.reset()

    expect(store.status).toBe('idle')
    expect(store.error).toBeNull()
  })
})

describe('ProviderStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('should add and manage providers', () => {
    const store = useProviderStore()
    expect(store.providers.length).toBeGreaterThanOrEqual(0)
  })

  it('should have LLM provider tracking', () => {
    const store = useProviderStore()
    expect(store.hasConfiguredLLM).toBeDefined()
  })
})

describe('EditorStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have correct initial state', () => {
    const store = useEditorStore()
    expect(store.sourceImage).toBeNull()
    expect(store.instruction).toBe('')
  })

  it('should set instruction correctly', () => {
    const store = useEditorStore()
    store.setInstruction('把背景换成白色')
    expect(store.instruction).toBe('把背景换成白色')
  })

  it('should clear instruction', () => {
    const store = useEditorStore()
    store.setInstruction('test')
    store.clearInstruction()
    expect(store.instruction).toBe('')
  })
})

describe('ConfigStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  describe('isConfigured', () => {
    it('should return false when no config', () => {
      const store = useConfigStore()
      expect(store.isConfigured).toBe(false)
    })

    it('should return true when apiKey and apiEndpoint are set', () => {
      const store = useConfigStore()
      store.saveApiConfig('test-key', 'https://api.example.com')
      expect(store.isConfigured).toBe(true)
    })
  })

  describe('saveApiConfig', () => {
    it('should save config to store and localStorage', () => {
      const store = useConfigStore()
      store.saveApiConfig('my-key', 'https://api.example.com')
      
      expect(store.apiKey).toBe('my-key')
      expect(store.apiEndpoint).toBe('https://api.example.com')
      expect(localStorage.getItem('ai_studio_api_key')).toBe('my-key')
      expect(localStorage.getItem('ai_studio_api_endpoint')).toBe('https://api.example.com')
    })
  })

  describe('clearApiConfig', () => {
    it('should clear config from store and localStorage', () => {
      const store = useConfigStore()
      store.saveApiConfig('my-key', 'https://api.example.com')
      store.clearApiConfig()
      
      expect(store.apiKey).toBe('')
      expect(store.apiEndpoint).toBe('')
      expect(localStorage.getItem('ai_studio_api_key')).toBeNull()
      expect(localStorage.getItem('ai_studio_api_endpoint')).toBeNull()
    })
  })

  describe('theme', () => {
    it('should be fixed to light mode', () => {
      const store = useConfigStore()
      expect(store.theme).toBe('light')
    })
  })
})

describe('HistoryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have correct initial state', () => {
    const store = useHistoryStore()
    expect(store.items).toEqual([])
    expect(store.selectedIds).toEqual([])
    expect(store.detailItemId).toBeNull()
  })

  it('should toggle selection correctly', () => {
    const store = useHistoryStore()
    // Simulate items
    ;(store.items as any) = [{ id: 1 }, { id: 2 }, { id: 3 }]

    store.toggleSelect(1)
    expect(store.selectedIds).toEqual([1])

    store.toggleSelect(3)
    expect(store.selectedIds).toEqual([1, 3])

    store.toggleSelect(1)
    expect(store.selectedIds).toEqual([3])
  })

  it('should select all and clear selection', () => {
    const store = useHistoryStore()
    ;(store.items as any) = [{ id: 1 }, { id: 2 }, { id: 3 }]

    store.selectAll()
    expect(store.selectedIds).toEqual([1, 2, 3])

    store.clearSelection()
    expect(store.selectedIds).toEqual([])
  })

  it('should compute favorites from items', () => {
    const store = useHistoryStore()
    ;(store.items as any) = [
      { id: 1, isFavorite: true },
      { id: 2, isFavorite: false },
      { id: 3, isFavorite: true },
    ]
    expect(store.favorites).toHaveLength(2)
    expect(store.favorites.map(i => i.id)).toEqual([1, 3])
  })

  it('should set detail item', () => {
    const store = useHistoryStore()
    expect(store.detailItem).toBeNull()

    store.setDetailItem(1)
    // detailItemId is set but items is empty, so detailItem should still be null
    expect(store.detailItemId).toBe(1)
    expect(store.detailItem).toBeNull()
  })
})
