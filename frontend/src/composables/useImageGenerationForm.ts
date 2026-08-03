/**
 * 图像生成表单：模型列表、尺寸选项、比例预设
 */
import { computed } from 'vue'
import { useConfigStore, useGeneratorStore, useProviderStore } from '../stores'
import { useModelManifest } from './useModelManifest'

export const SIZE_META: Record<string, { ratio: string; label: string; platforms: string }> = {
  '1024x1024': { ratio: '1:1', label: '正方', platforms: '1:1' },
  '2048x2048': { ratio: '1:1', label: '正方(高清)', platforms: '1:1 高清' },
  '1024x1792': { ratio: '9:16', label: '竖版', platforms: '9:16' },
  '1792x1024': { ratio: '16:9', label: '横版', platforms: '16:9' },
  '1440x2560': { ratio: '9:16', label: '竖版(高清)', platforms: '9:16 高清' },
  '2560x1440': { ratio: '16:9', label: '横版(高清)', platforms: '16:9 高清' },
  '1920x2560': { ratio: '3:4', label: '竖版(3:4)', platforms: '3:4' },
  '512x512': { ratio: '1:1', label: '小图', platforms: '预览' },
  '768x1024': { ratio: '3:4', label: '竖版(3:4)', platforms: '3:4' },
  '1024x768': { ratio: '4:3', label: '横版(4:3)', platforms: '4:3' },
}

export const RATIO_LIST = [
  { ratio: '1:1', label: '1:1' },
  { ratio: '3:4', label: '3:4' },
  { ratio: '4:3', label: '4:3' },
  { ratio: '9:16', label: '9:16' },
  { ratio: '16:9', label: '16:9' },
] as const

const PROVIDER_LABELS: Record<string, string> = {
  doubao: '豆包',
  zhipu: '智谱',
  aliyun: '通义',
  openai: 'OpenAI',
  kling: '可灵',
  jimeng: '即梦',
  runway: 'Runway',
}

function inferProviderType(modelId: string): string {
  if (modelId.startsWith('doubao')) return 'doubao'
  if (modelId.startsWith('cogview')) return 'zhipu'
  if (modelId.startsWith('wanx') || modelId.startsWith('qwen-image')) return 'aliyun'
  if (modelId.startsWith('dall-e')) return 'openai'
  if (modelId.includes('stable-diffusion')) return 'custom'
  return ''
}

export function useImageGenerationForm() {
  const configStore = useConfigStore()
  const generatorStore = useGeneratorStore()
  const providerStore = useProviderStore()
  const { manifest, getModel, validateSize, getSupportedSizes, getRecommendedSizes, getModelNote, verificationLabel } = useModelManifest()

  const defaultImageProvider = computed(() =>
    providerStore.getDefaultProviderByCapability('image')
  )

  const activeImageProviders = computed(() =>
    providerStore.providers.filter((p) => p.capabilities?.includes('image') && p.apiKey)
  )

  const modelOptions = computed(() => {
    function isProviderReady(providerType: string): boolean {
      if (!providerType) return true
      const found = providerStore.providers.find((p) => p.type === providerType)
      if (!found) return false
      if (found.status === 'active') return true
      return !!found.apiKey
    }

    const serverModelIds = new Set<string>()
    const serverModels = (configStore.serverConfig?.models || []).map((m) => {
      serverModelIds.add(m.id)
      const provider = inferProviderType(m.id)
      return {
        label: provider && PROVIDER_LABELS[provider]
          ? `${m.name} [${PROVIDER_LABELS[provider]}]${verificationLabel(m.id)}`
          : `${m.name}${verificationLabel(m.id)}`,
        value: m.id,
        disabled: !isProviderReady(provider),
        provider: provider || undefined,
      }
    })

    const imageProviders = providerStore.providers.filter(
      (p) => p.capabilities?.includes('image') && p.apiKey
    )
    const customModels: { label: string; value: string; disabled: boolean; provider?: string }[] = []
    for (const prov of imageProviders) {
      for (const mId of prov.models || []) {
        if (!serverModelIds.has(mId)) {
          const statusIcon = prov.status === 'active' ? '✅ ' : prov.status === 'error' ? '❌ ' : ''
          customModels.push({
            label: `${statusIcon}${mId} [${prov.name}]`,
            value: mId,
            disabled: prov.status === 'error' || !prov.apiKey,
            provider: prov.type,
          })
        }
      }
    }

    const defaultProv = providerStore.getDefaultProviderByCapability('image')
    if (defaultProv?.defaultModel && !serverModelIds.has(defaultProv.defaultModel)) {
      const already = customModels.some((m) => m.value === defaultProv.defaultModel)
      if (!already) {
        customModels.push({
          label: `${defaultProv.defaultModel} [${defaultProv.name}]`,
          value: defaultProv.defaultModel,
          disabled: !defaultProv.apiKey,
          provider: defaultProv.type,
        })
      }
    }

    const all = [...serverModels, ...customModels]
    const grouped = new Map<string, typeof all>()
    for (const m of all) {
      const key = m.provider || 'other'
      if (!grouped.has(key)) grouped.set(key, [])
      grouped.get(key)!.push(m)
    }

    return Array.from(grouped.entries()).map(([key, children]) => ({
      type: 'group' as const,
      label: PROVIDER_LABELS[key] || (key === 'other' ? '其他' : key),
      children: children.map(({ provider: _, ...rest }) => rest),
    }))
  })

  const sizeOptions = computed(() => {
    const modelId = generatorStore.model
    const allSizes = configStore.serverConfig?.sizes || [
      '1024x1024', '1024x1792', '1792x1024', '2048x2048',
    ]
    const filtered = getSupportedSizes(modelId, allSizes)
    const recommended = getRecommendedSizes(modelId)

    return filtered.map((size) => {
      const meta = SIZE_META[size]
      const valid = validateSize(modelId, size)
      const isRecommended = recommended.includes(size)
      let label = `${size} [${meta ? meta.platforms : ''}]`
      if (isRecommended) label += ' [推荐]'
      return { label, value: size, disabled: !valid.valid }
    })
  })

  const ratioActive = computed(() => {
    const meta = SIZE_META[generatorStore.size]
    return meta?.ratio || ''
  })

  const supportsAdvancedParams = computed(() => {
    const modelId = generatorStore.model
    if (!modelId || modelId === 'default') return false

    // 优先从 Manifest 读取 advanced_params 标记（后续扩展）
    if (manifest.value) {
      const entry = getModel(modelId)
      if (entry?.capabilities?.includes('advanced_params')) return true
    }

    // 回退：自定义供应商（非预设模型）通常支持 Seed/Steps/CFG
    const provider = defaultImageProvider.value
    if (provider && provider.type === 'custom') return true

    return modelId.includes('dall-e') || modelId.includes('stable-diffusion')
  })

  const currentModelNote = computed(() => getModelNote(generatorStore.model))

  function pickRatio(ratio: string) {
    const targets = ratio === '1:1' ? ['2048x2048', '1024x1024', '512x512']
      : ratio === '3:4' ? ['1920x2560', '768x1024']
        : ratio === '9:16' ? ['1440x2560', '1024x1792']
          : ratio === '16:9' ? ['2560x1440', '1792x1024']
            : ratio === '4:3' ? ['1024x768'] : []
    const avail = sizeOptions.value
    for (const t of targets) {
      const match = avail.find((o) => o.value === t && !o.disabled)
      if (match) {
        generatorStore.size = match.value
        return
      }
    }
  }

  function handleModelChange(modelId: string | undefined) {
    if (!modelId) return
    const opts = sizeOptions.value
    const currentSize = generatorStore.size
    const stillAvailable = opts.some((o) => o.value === currentSize && !o.disabled)
    if (stillAvailable) return
    const recommended = getRecommendedSizes(modelId)[0]
    if (recommended) {
      generatorStore.size = recommended
    }
  }

  return {
    defaultImageProvider,
    activeImageProviders,
    modelOptions,
    sizeOptions,
    ratioActive,
    supportsAdvancedParams,
    currentModelNote,
    pickRatio,
    handleModelChange,
    validateSize,
  }
}

export function providerStatusClass(status?: string): string {
  const map: Record<string, string> = {
    active: 'status-active',
    error: 'status-error',
    checking: 'status-checking',
    inactive: 'status-inactive',
  }
  return map[status || 'inactive'] || 'status-inactive'
}

export function providerStatusLabel(status?: string): string {
  const map: Record<string, string> = {
    active: '已连接',
    error: '连接失败',
    checking: '检测中',
    inactive: '未检测',
  }
  return map[status || 'inactive'] || '未检测'
}

export function stripeDotClass(status?: string): string {
  if (status === 'active') return 'stripe-active'
  if (status === 'error') return 'stripe-error'
  if (status === 'checking') return 'stripe-checking'
  return 'stripe-idle'
}
