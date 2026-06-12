<template>
  <div class="section-block">
    <div class="section-header">
      <n-icon :component="Film" class="section-icon" />
      <span class="section-title">视频生成</span>
      <n-tag v-if="providerStore.hasConfiguredVideoProvider" type="success" size="small">已配置</n-tag>
      <n-tag v-if="configStore.isBackendConfigured('video')" type="info" size="small">已由后端配置</n-tag>
    </div>

    <!-- 后端已配置 Key → 隐藏手动配置 -->
    <template v-if="configStore.isBackendConfigured('video')">
      <n-alert type="success" size="small" class="mb-2">
        后端已配置视频生成 API Key，开发者无需在此处重复配置。
      </n-alert>
    </template>

    <template v-else>
    <n-list bordered>
      <n-list-item v-for="preset in videoPresets" :key="preset.type">
        <n-thing :title="preset.name">
          <template #avatar>
            <n-tag :type="preset.recommended ? 'success' : 'default'">
              {{ preset.recommended ? '推荐' : '可选' }}
            </n-tag>
          </template>
          <template #description>{{ preset.description }}</template>
          <template #header-extra>
            <n-space align="center">
              <n-tag v-if="isVideoConfigured(preset.type)" type="success" size="small">已配置</n-tag>
              <n-button size="small" :type="isVideoConfigured(preset.type) ? 'default' : 'primary'" @click="showVideoConfigModal(preset)">
                {{ isVideoConfigured(preset.type) ? '修改' : '配置' }}
              </n-button>
            </n-space>
          </template>
        </n-thing>
      </n-list-item>
    </n-list>
    <n-button block dashed class="mt-2" @click="emit('open-custom', 'video')">+ 自定义视频供应商</n-button>
    </template>
  </div>

  <!-- ── 视频配置弹窗 ── -->
  <n-modal
    v-model:show="showVideoModal"
    preset="card"
    :title="`配置 ${currentVideoPreset?.name || '视频供应商'}`"
    style="width: 450px"
  >
    <n-form label-placement="left" label-width="100">
      <n-form-item label="API Key">
        <n-input
          v-model:value="videoApiKeyInput"
          type="password"
          show-password-on="click"
          :placeholder="currentVideoPreset?.keyPlaceholder || '请输入 API Key'"
        />
      </n-form-item>
      <n-form-item label="模型">
        <n-input
          v-model:value="videoModelInput"
          :placeholder="currentVideoPreset?.defaultModel || '请输入模型名称'"
        />
      </n-form-item>
      <n-form-item label="API Endpoint">
        <n-input
          v-model:value="videoEndpointInput"
          :placeholder="currentVideoPreset?.endpoint || 'API Endpoint'"
        />
      </n-form-item>
    </n-form>

    <div v-if="testTarget === 'video' && testResult" class="test-result" :class="{ success: testResult.success }">
      {{ testResult.message }}
    </div>

    <template v-if="currentVideoPreset?.helpUrl">
      <n-divider />
      <n-space vertical>
        <n-text depth="3">获取 API Key：</n-text>
        <n-button text type="primary" tag="a" :href="currentVideoPreset.helpUrl" target="_blank">
          {{ currentVideoPreset.helpText || '点击前往获取' }}
        </n-button>
      </n-space>
    </template>

    <template #footer>
      <n-space justify="space-between" style="width: 100%">
        <div>
          <n-button
            :loading="testingVideo"
            :disabled="!videoApiKeyInput"
            @click="testConnection(videoEndpointInput, videoApiKeyInput, currentVideoPreset?.type || 'video', 'video')"
          >
            测试连接
          </n-button>
        </div>
        <n-space>
          <n-button @click="showVideoModal = false">取消</n-button>
          <n-button type="primary" @click="saveVideoConfig" :disabled="!videoApiKeyInput">
            保存
          </n-button>
        </n-space>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NModal, NForm, NFormItem, NInput, NList, NListItem, NThing, NButton, NSpace, NText, NDivider, NTag, useMessage } from 'naive-ui'
import { useProviderStore, useConfigStore } from '../../stores'
import { apiService } from '../../api'
import type { ProviderType } from '../../types/provider'
import { Film } from 'lucide-vue-next'

const message = useMessage()
const providerStore = useProviderStore()
const configStore = useConfigStore()
const emit = defineEmits<{
  'open-custom': [capability: 'video' | 'edit' | 'vision']
}>()

interface VideoPreset {
  type: string
  name: string
  description: string
  keyPlaceholder: string
  endpoint: string
  defaultModel?: string
  helpUrl?: string
  helpText?: string
  recommended?: boolean
}

const videoPresets: VideoPreset[] = [
  {
    type: 'kling',
    name: '可灵AI',
    description: '国内领先的视频生成平台，性价比高，¥0.5-2/条',
    keyPlaceholder: '可灵 API Key',
    endpoint: 'https://api.klingai.com/v1/videos/generations',
    defaultModel: 'kling-v1',
    helpUrl: 'https://platform.klingai.com/',
    helpText: '可灵开放平台 - 注册即送免费额度',
    recommended: true
  },
  {
    type: 'jimeng',
    name: '即梦AI',
    description: '字节跳动出品，中文理解好，积分制',
    keyPlaceholder: '即梦 API Key',
    endpoint: 'https://api.jimeng.ai/v1/videos/generations',
    defaultModel: 'jimeng-2.1',
    helpUrl: 'https://jimeng.jianying.com/',
    helpText: '即梦AI官网'
  },
  {
    type: 'runway',
    name: 'Runway',
    description: '国际领先的视频生成平台，专业级',
    keyPlaceholder: 'Runway API Key',
    endpoint: 'https://api.runwayml.com/v1/generate',
    defaultModel: 'gen3a',
    helpUrl: 'https://runwayml.com/',
    helpText: 'Runway官网'
  }
]

const showVideoModal = ref(false)
const currentVideoPreset = ref<VideoPreset | null>(null)
const videoApiKeyInput = ref('')
const videoEndpointInput = ref('')
const videoModelInput = ref('')

const testingVideo = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testTarget = ref<string | null>(null)

function isVideoConfigured(type: string): boolean {
  return providerStore.providers.some(p => p.type === type && p.capabilities?.includes('video') && p.apiKey)
}

function showVideoConfigModal(preset: VideoPreset): void {
  currentVideoPreset.value = preset
  const existing = providerStore.providers.find(p => p.type === preset.type && p.capabilities?.includes('video'))
  videoApiKeyInput.value = existing?.apiKey || localStorage.getItem(`video_${preset.type}_apiKey`) || ''
  videoEndpointInput.value = existing?.endpoint || localStorage.getItem(`video_${preset.type}_endpoint`) || preset.endpoint
  videoModelInput.value = existing?.defaultModel || localStorage.getItem(`video_${preset.type}_model`) || preset.defaultModel || ''
  showVideoModal.value = true
}

function saveVideoConfig(): void {
  if (!currentVideoPreset.value || !videoApiKeyInput.value) return

  providerStore.upsertCapabilityProvider({
    name: currentVideoPreset.value.name,
    type: currentVideoPreset.value.type as ProviderType,
    apiKey: videoApiKeyInput.value,
    endpoint: videoEndpointInput.value || currentVideoPreset.value.endpoint,
    defaultModel: videoModelInput.value || currentVideoPreset.value.defaultModel || '',
    capability: 'video'
  })

  showVideoModal.value = false
  message.success(`${currentVideoPreset.value.name} 视频配置已保存`)
}

async function testConnection(endpoint: string, apiKey: string, providerType: string, target: string, model?: string) {
  if (!apiKey || !endpoint) {
    message.warning('请先填写 API Key 和 Endpoint')
    return
  }
  testResult.value = null
  testTarget.value = target

  if (target === 'video') testingVideo.value = true

  try {
    const res = await apiService.validateApi({
      api_key: apiKey,
      api_endpoint: endpoint,
      provider_type: providerType,
      ...(model ? { model } : {})
    })
    testResult.value = {
      success: res.valid,
      message: res.valid ? `✅ 连接成功` : `❌ ${res.message}`
    }
    if (res.valid) message.success('连接成功！')
    else message.error(res.message)
  } catch (e: any) {
    const errMsg = e?.response?.data?.error || e?.userMessage || '连接测试失败'
    testResult.value = { success: false, message: `❌ ${errMsg}` }
    message.error(errMsg)
  } finally {
    testingVideo.value = false
  }
}
</script>

<style scoped>
.section-block {
  margin-bottom: 4px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.section-icon {
  font-size: 18px;
  color: var(--brand-500);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.test-result {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-sm, 6px);
  font-size: 13px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.test-result.success {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #16a34a;
}
</style>
