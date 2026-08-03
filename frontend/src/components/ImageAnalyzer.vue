<template>
  <div class="image-analyzer">
    <n-card title="图片分析" size="small">
      <n-space vertical>
        <n-upload
          :max="1"
          accept="image/*"
          :show-file-list="false"
          :custom-request="handleUpload"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 12px">
              <n-icon size="48" :depth="3">
                <CloudUploadOutline />
              </n-icon>
            </div>
            <n-text style="font-size: 16px">
              点击或拖拽图片到此区域
            </n-text>
            <n-p depth="3" style="margin: 8px 0 0 0">
              支持 JPG、PNG、WebP 格式
            </n-p>
          </n-upload-dragger>
        </n-upload>

        <div v-if="uploadedImageUrl" class="uploaded-preview">
          <n-image
            :src="uploadedImageUrl"
            alt="上传的图片"
            object-fit="contain"
            style="max-height: 200px"
          />
          <n-button
            size="small"
            type="error"
            text
            @click="clearImage"
            style="position: absolute; top: 4px; right: 4px"
          >
            清除
          </n-button>
        </div>

        <n-alert v-if="providerOptions.length === 0" type="warning" title="未配置视觉模型">
          <n-space vertical>
            <span>请先配置视觉模型 API Key 以使用图片分析功能</span>
            <n-button type="primary" size="small" @click="configStore.showConfigModal = true">
              前往配置
            </n-button>
          </n-space>
        </n-alert>

        <template v-else>
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
              :disabled="!selectedProviderId || !uploadedImageUrl"
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

          <n-alert v-if="error" type="error" title="分析失败">
            {{ error }}
          </n-alert>

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
        </template>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NUpload, NUploadDragger, NIcon, NText, NP, NImage, NButton,
  NSpace, NSelect, NProgress, NAlert, NTag, useMessage
} from 'naive-ui'
import { CloudUploadOutline } from '@vicons/ionicons5'
import type { UploadCustomRequestOptions } from 'naive-ui'
import { useConfigStore, useProviderStore } from '../stores'
import { useGeneratorStore } from '../stores/generator'
import { analyzeImage } from '../api/vision'
import type { VisionProvider } from '../types/provider'
import type { VisionAnalysisResult } from '../api/vision'

const message = useMessage()
const configStore = useConfigStore()
const providerStore = useProviderStore()
const generatorStore = useGeneratorStore()

const uploadedImageUrl = ref<string | null>(null)
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
      return preset?.supportsVision && p.apiKey
    })
    .map(p => ({
      label: `${p.name} (${p.type === 'zhipu' ? '免费' : '付费'})`,
      value: p.id
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

function handleUpload({ file }: UploadCustomRequestOptions): void {
  const fileObj = file.file
  if (!fileObj) return
  
  if (!fileObj.type.startsWith('image/')) {
    message.error('请上传图片文件')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImageUrl.value = e.target?.result as string
    result.value = null
    error.value = null
  }
  reader.readAsDataURL(fileObj)
}

function clearImage(): void {
  uploadedImageUrl.value = null
  result.value = null
  error.value = null
}

async function handleAnalyze(): Promise<void> {
  if (!selectedProvider.value || !uploadedImageUrl.value) return
  
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
      uploadedImageUrl.value
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
  message.success('已应用为当前提示词')
}

onMounted(() => {
  const firstAvailable = providerOptions.value[0]
  if (firstAvailable) {
    selectedProviderId.value = firstAvailable.value
  }
})
</script>

<style scoped>
.image-analyzer {
  height: 100%;
}

.uploaded-preview {
  position: relative;
  display: flex;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 8px;
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
  background: var(--bg-subtle);
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
