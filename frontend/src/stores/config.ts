/**
 * 配置状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '../api'
import { config } from '../config'
import type { ConfigResult } from '../types'
import type { ModelManifest } from '../types/api'

export const useConfigStore = defineStore('config', () => {
  const apiKey = ref(localStorage.getItem(config.storage.apiKey) || '')
  const apiEndpoint = ref(localStorage.getItem(config.storage.apiEndpoint) || '')
  /** 固定为浅色模式 */
  const theme = ref<'light'>('light')
  const serverConfig = ref<ConfigResult | null>(null)
  const modelManifest = ref<ModelManifest | null>(null)
  const showConfigModal = ref(false)
  const error = ref<string | null>(null)
  const backendAvailable = ref<boolean | null>(null)

  const isConfigured = computed(() => {
    return !!(apiKey.value && apiEndpoint.value) || !!(serverConfig.value?.has_backend_config)
  })

  /** 后端已为哪些能力配置了 API Key */
  const backendConfiguredCapabilities = computed<Record<string, boolean>>(() => {
    return serverConfig.value?.backend_configured_capabilities ?? {}
  })

  /** 检查某个能力是否已有后端 Key 配置 */
  function isBackendConfigured(capability: string): boolean {
    return backendConfiguredCapabilities.value[capability] ?? false
  }

  function saveApiConfig(key: string, endpoint: string): void {
    apiKey.value = key
    apiEndpoint.value = endpoint
    localStorage.setItem(config.storage.apiKey, key)
    localStorage.setItem(config.storage.apiEndpoint, endpoint)
  }

  function clearApiConfig(): void {
    apiKey.value = ''
    apiEndpoint.value = ''
    localStorage.removeItem(config.storage.apiKey)
    localStorage.removeItem(config.storage.apiEndpoint)
  }

  async function loadServerConfig(): Promise<void> {
    try {
      serverConfig.value = await apiService.getConfig()
      modelManifest.value = await apiService.getModelManifest().catch(() => null)
      backendAvailable.value = true
      error.value = null
    } catch {
      backendAvailable.value = false
      serverConfig.value = null
      modelManifest.value = null
    }
  }

  return {
    apiKey,
    apiEndpoint,
    theme,
    serverConfig,
    modelManifest,
    showConfigModal,
    error,
    backendAvailable,
    isConfigured,
    backendConfiguredCapabilities,
    isBackendConfigured,
    saveApiConfig,
    clearApiConfig,
    loadServerConfig,
  }
})
