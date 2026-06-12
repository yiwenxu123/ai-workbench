import { computed } from 'vue'
import { useProviderStore } from '../stores/provider'
import { useConfigStore } from '../stores/config'

export type GenerationCapability = 'image' | 'video' | 'edit'

export interface ProviderCredentials {
  api_key?: string
  api_endpoint?: string
  provider?: string
}

export function useCapabilityReady() {
  const providerStore = useProviderStore()
  const configStore = useConfigStore()

  const canUseImage = computed(
    () => providerStore.hasConfiguredImageProvider || configStore.isBackendConfigured('image')
  )
  const canUseVideo = computed(
    () => providerStore.hasConfiguredVideoProvider || configStore.isBackendConfigured('video')
  )
  const canUseEdit = computed(
    () => providerStore.hasConfiguredEditProvider || configStore.isBackendConfigured('edit')
  )

  function canUse(capability: GenerationCapability): boolean {
    if (capability === 'image') return canUseImage.value
    if (capability === 'video') return canUseVideo.value
    return canUseEdit.value
  }

  function getProviderCredentials(capability: GenerationCapability): ProviderCredentials | null {
    if (configStore.isBackendConfigured(capability)) {
      const provider = providerStore.getDefaultProviderByCapability(capability)
      return { provider: provider?.type }
    }
    const provider = providerStore.getDefaultProviderByCapability(capability)
    if (!provider?.apiKey || !provider?.endpoint) return null
    return {
      api_key: provider.apiKey,
      api_endpoint: provider.endpoint,
      provider: provider.type,
    }
  }

  return { canUseImage, canUseVideo, canUseEdit, canUse, getProviderCredentials }
}
