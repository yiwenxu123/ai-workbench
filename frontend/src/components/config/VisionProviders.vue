<template>
  <div class="section-block">
    <div class="section-header">
      <n-icon :component="Eye" class="section-icon" />
      <span class="section-title">图片分析（视觉模型）</span>
      <n-tag v-if="hasConfiguredVision" type="success" size="small">已配置</n-tag>
    </div>
    <n-alert type="info" size="small" class="mb-2">
      上传图片后自动分析并反推提示词。
    </n-alert>
    <n-list bordered>
      <n-list-item v-for="preset in visionPresets" :key="preset.type">
        <n-thing :title="preset.name">
          <template #avatar>
            <n-tag :type="preset.type === 'zhipu' ? 'success' : 'default'">
              {{ preset.type === 'zhipu' ? '免费' : '付费' }}
            </n-tag>
          </template>
          <template #description>{{ preset.description }}</template>
          <template #header-extra>
            <n-space align="center">
              <n-tag v-if="isConfigured(preset.type)" type="success" size="small">已配置</n-tag>
              <n-button size="small" :type="isConfigured(preset.type) ? 'default' : 'primary'" @click="showConfigModal(preset)">
                {{ isConfigured(preset.type) ? '修改' : '配置' }}
              </n-button>
            </n-space>
          </template>
        </n-thing>
      </n-list-item>
    </n-list>
    <n-button block dashed class="mt-2" @click="emit('open-custom', 'vision')">+ 自定义视觉供应商</n-button>
  </div>

  <!-- ── 视觉模型配置弹窗 ── -->
  <n-modal
    v-model:show="showApiKeyModal"
    preset="card"
    :title="`配置 ${currentPreset?.name}`"
    style="width: 450px"
  >
    <n-form label-placement="left" label-width="100">
      <n-form-item label="API Key">
        <n-input
          v-model:value="apiKeyInput"
          type="password"
          show-password-on="click"
          :placeholder="currentPreset?.keyPlaceholder || '请输入 API Key'"
        />
      </n-form-item>
      <n-form-item label="模型">
        <n-input
          v-model:value="visionModelInput"
          :placeholder="currentPreset?.visionModel || '请输入模型名称'"
        />
      </n-form-item>
      <n-form-item label="API Endpoint">
        <n-input
          v-model:value="endpointInput"
          :placeholder="currentPreset?.visionEndpoint || '自定义 API Endpoint'"
        />
      </n-form-item>
    </n-form>

    <div v-if="testTarget === 'vision' && testResult" class="test-result" :class="{ success: testResult.success }">
      {{ testResult.message }}
    </div>

    <template v-if="currentPreset?.helpUrl">
      <n-divider />
      <n-space vertical>
        <n-text depth="3">获取 API Key：</n-text>
        <n-button text type="primary" tag="a" :href="currentPreset.helpUrl" target="_blank">
          {{ currentPreset.helpText || '点击前往获取' }}
        </n-button>
      </n-space>
    </template>

    <template #footer>
      <n-space justify="space-between" style="width: 100%">
        <div>
          <n-button
            :loading="testingVision"
            :disabled="!apiKeyInput"
            @click="testConnection(endpointInput || currentPreset?.visionEndpoint || '', apiKeyInput, currentPreset?.type || 'image', 'vision')"
          >
            <template #icon>
              <n-icon :component="testingVision ? undefined : (testTarget === 'vision' && testResult?.success ? CheckCircle : XCircle)" />
            </template>
            测试连接
          </n-button>
        </div>
        <n-space>
          <n-button @click="showApiKeyModal = false">取消</n-button>
          <n-button type="primary" @click="saveVisionConfig" :disabled="!apiKeyInput">
            保存
          </n-button>
        </n-space>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NModal, NForm, NFormItem, NInput, NAlert, NList, NListItem, NThing, NButton, NSpace, NText, NDivider, NTag, NIcon, useMessage } from 'naive-ui'
import { useProviderStore } from '../../stores'
import { apiService } from '../../api'
import type { ProviderType, ProviderCapability } from '../../types/provider'
import { Eye, CheckCircle, XCircle } from 'lucide-vue-next'

const message = useMessage()
const providerStore = useProviderStore()
const emit = defineEmits<{
  'open-custom': [capability: 'video' | 'edit' | 'vision']
}>()

interface VisionPreset {
  type: ProviderType
  name: string
  description: string
  keyPlaceholder: string
  helpUrl?: string
  helpText?: string
  customEndpoint?: boolean
  visionModel: string
  visionEndpoint: string
}

const visionPresets: VisionPreset[] = [
  {
    type: 'zhipu',
    name: '智谱 GLM-4V-Flash',
    description: '免费模型，新用户赠送额度，1元可处理约300张图',
    keyPlaceholder: '智谱 API Key (如: xxx.xxx)',
    helpUrl: 'https://open.bigmodel.cn/',
    helpText: '智谱开放平台 - 注册即送免费额度',
    visionModel: 'glm-4v-flash',
    visionEndpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
  },
  {
    type: 'doubao',
    name: '豆包视觉理解',
    description: '火山引擎出品，低价高效，约0.003元/千tokens',
    keyPlaceholder: '火山引擎 API Key',
    helpUrl: 'https://console.volcengine.com/ark',
    helpText: '火山引擎控制台 - 开通视觉理解服务',
    visionModel: 'doubao-vision-pro-32k',
    visionEndpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
  },
  {
    type: 'aliyun',
    name: '通义千问 VL',
    description: '阿里云出品，多模态理解能力强',
    keyPlaceholder: '阿里云 DashScope API Key',
    helpUrl: 'https://dashscope.console.aliyun.com/',
    helpText: '阿里云 DashScope 控制台',
    visionModel: 'qwen-vl-plus',
    visionEndpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
  }
]

const showApiKeyModal = ref(false)
const currentPreset = ref<VisionPreset | null>(null)
const apiKeyInput = ref('')
const endpointInput = ref('')
const visionModelInput = ref('')

const testingVision = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testTarget = ref<string | null>(null)

const hasConfiguredVision = computed(() =>
  providerStore.visionProviderPresets.some(p => providerStore.providers.find(vp => vp.type === p.type)?.apiKey)
)

function isConfigured(type: ProviderType): boolean {
  const provider = providerStore.providers.find(p => p.type === type)
  return !!provider?.apiKey
}

function showConfigModal(preset: VisionPreset): void {
  currentPreset.value = preset
  const existing = providerStore.providers.find(p => p.type === preset.type)
  apiKeyInput.value = existing?.apiKey || ''
  endpointInput.value = existing?.endpoint || preset.visionEndpoint
  visionModelInput.value = existing?.defaultModel || preset.visionModel
  showApiKeyModal.value = true
}

async function saveVisionConfig(): Promise<void> {
  if (!currentPreset.value || !apiKeyInput.value) return

  const existing = providerStore.providers.find(p => p.type === currentPreset.value!.type)

  if (existing) {
    providerStore.updateProvider(existing.id, {
      apiKey: apiKeyInput.value,
      endpoint: endpointInput.value || currentPreset.value!.visionEndpoint,
      models: [visionModelInput.value || currentPreset.value!.visionModel],
      defaultModel: visionModelInput.value || currentPreset.value!.visionModel,
      capabilities: [...new Set([...(existing.capabilities || []), 'vision' as const])] as ProviderCapability[]
    })
  } else {
    providerStore.addProvider({
      name: currentPreset.value.name,
      type: currentPreset.value.type,
      apiKey: apiKeyInput.value,
      endpoint: endpointInput.value || currentPreset.value.visionEndpoint,
      models: [visionModelInput.value || currentPreset.value.visionModel],
      defaultModel: visionModelInput.value || currentPreset.value.visionModel,
      capabilities: ['vision']
    })
  }

  showApiKeyModal.value = false
}

async function testConnection(endpoint: string, apiKey: string, providerType: string, target: string, model?: string) {
  if (!apiKey || !endpoint) {
    message.warning('请先填写 API Key 和 Endpoint')
    return
  }
  testResult.value = null
  testTarget.value = target

  if (target === 'vision') testingVision.value = true

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
    testingVision.value = false
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
