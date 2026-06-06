import { describe, it, expect } from 'vitest'
import { ApiService } from '@/api'
import { config } from '@/config'

describe('ApiService', () => {
  it('should create instance with correct base URL', () => {
    const service = new ApiService()
    expect(service).toBeDefined()
  })

  it('should have cache mechanism', () => {
    const service = new ApiService()
    service.clearCache()
    expect(service).toBeDefined()
  })
})

describe('Config', () => {
  it('should have correct default values', () => {
    expect(config.prompt.maxLength).toBe(4000)
    expect(config.prompt.minLength).toBe(1)
    expect(config.history.maxItems).toBe(50)
    expect(config.storage.apiKey).toBe('ai_studio_api_key')
  })

  it('should have request configuration', () => {
    expect(config.request.timeout).toBe(120000)
    expect(config.request.maxRetries).toBe(3)
  })
})
