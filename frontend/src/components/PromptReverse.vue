<template>
  <div class="prompt-reverse">
    <n-space vertical>
      <div class="image-preview" v-if="imageUrl">
        <n-image
          :src="imageUrl"
          alt="待分析图片"
          object-fit="contain"
          style="max-height: 200px"
        />
      </div>

      <n-space>
        <n-select
          v-model:value="selectedProviderId"
          :options="providerOptions"
          placeholder="选择视觉模型"
          style="width: 200px"
        />
        <n-button
          type="primary"
          :loading="analyzing"
          :disabled="!selectedProviderId || !imageUrl"
          @click="handleAnalyze"
        >
          {{ analyzing ? '分析中...' : '反推提示词' }}
        </n-button>
      </n-space>

      <n-progress
        v-if="analyzing"
        type="line"
        :percentage="progress"
        :show-indicator="false"
        status="info"
      />

      <div v-if="result" class="result-section">
        <div class="result-header">
          <span class="result-title">分析结果</span>
          <n-space>
            <n-button size="small" @click="copyResult">
              复制
            </n-button>
            <n-button size="small" type="primary" @click="useAsPrompt">
              使用此提示词
            </n-button>
          </n-space>
        </div>
        
        <n-card size="small" class="result-card">
          <div class="result-prompt">{{ result.prompt }}</div>
          
          <div v-if="result.tags && result.tags.length > 0" class="result-tags">
            <span class="tags-label">关键词：</span>
            <n-tag
              v-for="tag in result.tags"
              :key="tag"
              size="small"
              type="info"
              style="margin-right: 4px"
            >
              {{ tag }}
            </n-tag>
          </div>
        </n-card>
      </div>

      <n-alert v-if="error" type="error" title="分析失败">
        {{ error }}
      </n-alert>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSpace, NSelect, NButton, NProgress, NCard, NTag, NAlert, NImage, useMessage
} from 'naive-ui'
import { useProviderStore } from '../stores/provider'
import { useGeneratorStore } from '../stores/generator'
import { analyzeImage } from '../api/vision'
import type { VisionProvider } from '../types/provider'
import type { VisionAnalysisResult } from '../api/vision'

const props = defineProps<{
  imageUrl: string
}>()

const emit = defineEmits<{
  (e: 'use-prompt', prompt: string): void
}>()

const message = useMessage()
const providerStore = useProviderStore()
const generatorStore = useGeneratorStore()

const selectedProviderId = ref<string | null>(null)
const analyzing = ref(false)
const progress = ref(0)
const result = ref<VisionAnalysisResult | null>(null)
const error = ref<string | null>(null)

const providerOptions = computed(() => {
  return providerStore.providers
    .filter(p => {
      const preset = providerStore.visionProviderPresets.find(
        vp => vp.type === p.type
      )
      return preset?.supportsVision
    })
    .map(p => ({
      label: `${p.name} (${p.type === 'zhipu' ? '免费' : '付费'})`,
      value: p.id,
      disabled: !p.apiKey
    }))
})

const selectedProvider = computed(() => {
  if (!selectedProviderId.value) return null
  const provider = providerStore.getProviderById(selectedProviderId.value)
  if (!provider) return null
  
  const preset = providerStore.visionProviderPresets.find(
    vp => vp.type === provider.type
  )
  
  if (!preset) return null
  
  return {
    ...provider,
    visionEndpoint: preset.visionEndpoint,
    visionModel: preset.visionModel,
    supportsVision: true
  } as VisionProvider
})

async function handleAnalyze(): Promise<void> {
  if (!selectedProvider.value || !props.imageUrl) return
  
  analyzing.value = true
  progress.value = 0
  error.value = null
  result.value = null
  
  const progressInterval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 15
    }
  }, 500)
  
  try {
    const analysisResult = await analyzeImage(
      selectedProvider.value,
      props.imageUrl
    )
    
    progress.value = 100
    
    if (analysisResult.success) {
      result.value = analysisResult
    } else {
      error.value = analysisResult.error || '分析失败'
    }
  } catch (e: unknown) {
    error.value = (e as Error).message || '请求失败'
  } finally {
    clearInterval(progressInterval)
    analyzing.value = false
  }
}

function copyResult(): void {
  if (!result.value?.prompt) return
  
  navigator.clipboard.writeText(result.value.prompt)
    .then(() => message.success('已复制到剪贴板'))
    .catch(() => message.error('复制失败'))
}

function useAsPrompt(): void {
  if (!result.value?.prompt) return
  
  generatorStore.prompt = result.value.prompt
  emit('use-prompt', result.value.prompt)
  message.success('已应用为当前提示词')
}

onMounted(() => {
  const firstAvailable = providerOptions.value.find(o => !o.disabled)
  if (firstAvailable) {
    selectedProviderId.value = firstAvailable.value
  }
})
</script>

<style scoped>
.prompt-reverse {
  padding: 8px 0;
}

.image-preview {
  display: flex;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 12px;
}

.result-section {
  margin-top: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-title {
  font-weight: 500;
  font-size: 14px;
}

.result-card {
  background: #fafafa;
}

.result-prompt {
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  margin-bottom: 12px;
}

.result-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.tags-label {
  font-size: 12px;
  color: #666;
  margin-right: 4px;
}
</style>
