<template>
  <div class="section-block">
    <div class="section-header">
      <n-icon :component="Brain" class="section-icon" />
      <span class="section-title">提示词优化（LLM）</span>
      <n-tag v-if="providerStore.hasConfiguredLLM" type="success" size="small">已配置</n-tag>
    </div>
    <n-alert type="info" size="small" class="mb-2">
      把中文需求优化成专业提示词，也用于 AI 入库的智能提取和去重。
    </n-alert>
    <n-list bordered>
      <n-list-item v-for="preset in llmPresets" :key="preset.type + preset.name">
        <n-thing :title="preset.name">
          <template #avatar><n-tag :type="preset.tagType">{{ preset.tagLabel }}</n-tag></template>
          <template #description>{{ preset.description }}</template>
          <template #header-extra>
            <n-space align="center">
              <n-tag v-if="isLLMConfigured(preset.name)" type="success" size="small">已配置</n-tag>
              <n-button size="small" :type="isLLMConfigured(preset.name) ? 'default' : 'primary'" @click="showLLMConfigModal(preset)">
                {{ isLLMConfigured(preset.name) ? '修改' : '配置' }}
              </n-button>
              <n-button v-if="isLLMConfigured(preset.name)" size="small" type="error" @click="removeLLMConfig(preset.name)">删除</n-button>
            </n-space>
          </template>
        </n-thing>
      </n-list-item>
    </n-list>
  </div>

  <!-- ── LLM 配置弹窗 ── -->
  <n-modal
    v-model:show="showLLMModal"
    preset="card"
    :title="`配置 ${currentLLMPreset?.name || 'LLM 供应商'}`"
    style="width: 450px"
  >
    <n-form label-placement="left" label-width="100">
      <n-form-item label="API Key">
        <n-input
          v-model:value="llmApiKeyInput"
          type="password"
          show-password-on="click"
          :placeholder="currentLLMPreset?.keyPlaceholder || '请输入 API Key'"
        />
      </n-form-item>
      <n-form-item label="模型">
        <n-input
          v-model:value="llmModelInput"
          :placeholder="currentLLMPreset?.defaultModel || '请输入模型名称'"
        />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px">常用：{{ (currentLLMPreset?.models ?? []).map(m => m.value).join(' / ') }}</n-text>
        </template>
      </n-form-item>
      <n-form-item label="Endpoint">
        <n-input
          v-model:value="llmEndpointInput"
          :placeholder="currentLLMPreset?.endpoint || 'API Endpoint'"
        />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px">通常无需修改，使用默认值即可</n-text>
        </template>
      </n-form-item>
    </n-form>

    <div v-if="testTarget === 'llm' && testResult" class="test-result" :class="{ success: testResult.success }">
      {{ testResult.message }}
    </div>

    <template v-if="currentLLMPreset?.helpUrl">
      <n-divider />
      <n-space vertical>
        <n-text depth="3">获取 API Key：</n-text>
        <n-button text type="primary" tag="a" :href="currentLLMPreset.helpUrl" target="_blank">
          {{ currentLLMPreset.helpText || '点击前往获取' }}
        </n-button>
      </n-space>
    </template>

    <template #footer>
      <n-space justify="space-between" style="width: 100%">
        <div>
          <n-button
            :loading="testingLLM"
            :disabled="!llmApiKeyInput"
            @click="testConnection(llmEndpointInput, llmApiKeyInput, 'llm', 'llm', llmModelInput)"
          >
            测试连接
          </n-button>
        </div>
        <n-space>
          <n-button @click="showLLMModal = false">取消</n-button>
          <n-button type="primary" @click="saveLLMConfig" :disabled="!llmApiKeyInput">
            保存
          </n-button>
        </n-space>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NModal, NForm, NFormItem, NInput, NAlert, NList, NListItem, NThing, NButton, NSpace, NText, NDivider, NTag, useMessage } from 'naive-ui'
import { useProviderStore } from '../../stores'
import { apiService } from '../../api'
import type { ProviderType } from '../../types/provider'
import { Brain } from 'lucide-vue-next'

const message = useMessage()
const providerStore = useProviderStore()

interface LLMPreset {
  type: ProviderType
  name: string
  description: string
  keyPlaceholder: string
  endpoint: string
  models: { label: string; value: string }[]
  defaultModel: string
  helpUrl?: string
  helpText?: string
  tagType: 'success' | 'info' | 'default' | 'warning'
  tagLabel: string
  isFree?: boolean
}

const llmPresets: LLMPreset[] = [
  {
    type: 'custom' as ProviderType,
    name: 'DeepSeek (推荐)',
    description: '性价比极高，中文理解优秀，注册即送 500 万 tokens',
    keyPlaceholder: 'sk-...',
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    models: [
      { label: 'DeepSeek Chat (推荐)', value: 'deepseek-chat' },
      { label: 'DeepSeek Reasoner', value: 'deepseek-reasoner' },
    ],
    defaultModel: 'deepseek-chat',
    helpUrl: 'https://platform.deepseek.com/api_keys',
    helpText: 'DeepSeek 开放平台 - 注册即送免费额度',
    tagType: 'success',
    tagLabel: '推荐',
  },
  {
    type: 'zhipu' as ProviderType,
    name: '智谱 GLM-4-Flash (免费)',
    description: '完全免费模型，适合体验和轻度使用',
    keyPlaceholder: '智谱 API Key',
    endpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    models: [
      { label: 'GLM-4-Flash (免费)', value: 'glm-4-flash' },
      { label: 'GLM-4-Air', value: 'glm-4-air' },
      { label: 'GLM-4-Plus', value: 'glm-4-plus' },
    ],
    defaultModel: 'glm-4-flash',
    helpUrl: 'https://open.bigmodel.cn/',
    helpText: '智谱开放平台 - 注册即可免费使用',
    tagType: 'info',
    tagLabel: '免费',
    isFree: true,
  },
  {
    type: 'aliyun' as ProviderType,
    name: '通义千问',
    description: '阿里云出品，中文能力强，价格低',
    keyPlaceholder: '阿里云 DashScope API Key',
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    models: [
      { label: 'Qwen Turbo', value: 'qwen-turbo' },
      { label: 'Qwen Plus', value: 'qwen-plus' },
      { label: 'Qwen Max', value: 'qwen-max' },
    ],
    defaultModel: 'qwen-turbo',
    helpUrl: 'https://dashscope.console.aliyun.com/',
    helpText: '阿里云 DashScope 控制台',
    tagType: 'default',
    tagLabel: '可选',
  },
  {
    type: 'doubao' as ProviderType,
    name: '豆包大模型',
    description: '字节跳动出品，低价高效',
    keyPlaceholder: '火山引擎 API Key',
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    models: [
      { label: 'Doubao Pro 32K', value: 'doubao-pro-32k' },
      { label: 'Doubao Lite 32K', value: 'doubao-lite-32k' },
    ],
    defaultModel: 'doubao-pro-32k',
    helpUrl: 'https://console.volcengine.com/ark',
    helpText: '火山引擎控制台',
    tagType: 'default',
    tagLabel: '可选',
  },
]

const showLLMModal = ref(false)
const currentLLMPreset = ref<LLMPreset | null>(null)
const llmApiKeyInput = ref('')
const llmEndpointInput = ref('')
const llmModelInput = ref('')

const testingLLM = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testTarget = ref<string | null>(null)

function isLLMConfigured(name: string): boolean {
  return providerStore.llmProviders.some(p => p.name === name && p.apiKey)
}

function showLLMConfigModal(preset: LLMPreset): void {
  currentLLMPreset.value = preset
  const existing = providerStore.llmProviders.find(p => p.name === preset.name)
  llmApiKeyInput.value = existing?.apiKey || ''
  llmEndpointInput.value = existing?.llmEndpoint || preset.endpoint
  llmModelInput.value = existing?.llmModel || preset.defaultModel
  showLLMModal.value = true
}

function saveLLMConfig(): void {
  if (!currentLLMPreset.value || !llmApiKeyInput.value) return

  const preset = currentLLMPreset.value
  const existing = providerStore.llmProviders.find(p => p.name === preset.name)

  if (existing) {
    providerStore.updateLLMProvider(existing.id, {
      apiKey: llmApiKeyInput.value,
      llmEndpoint: llmEndpointInput.value || preset.endpoint,
      endpoint: llmEndpointInput.value || preset.endpoint,
      llmModel: llmModelInput.value || preset.defaultModel,
      defaultModel: llmModelInput.value || preset.defaultModel,
    })
    message.success(`${preset.name} 配置已更新`)
  } else {
    providerStore.addLLMProvider({
      name: preset.name,
      type: preset.type,
      apiKey: llmApiKeyInput.value,
      llmEndpoint: llmEndpointInput.value || preset.endpoint,
      models: [llmModelInput.value || preset.defaultModel],
      llmModel: llmModelInput.value || preset.defaultModel,
      isFree: preset.isFree,
    })
    message.success(`${preset.name} 配置成功！`)
  }

  showLLMModal.value = false
}

function removeLLMConfig(name: string): void {
  const existing = providerStore.llmProviders.find(p => p.name === name)
  if (existing) {
    providerStore.removeLLMProvider(existing.id)
    message.info(`已删除 ${name} 配置`)
  }
}

async function testConnection(endpoint: string, apiKey: string, providerType: string, target: string, model?: string) {
  if (!apiKey || !endpoint) {
    message.warning('请先填写 API Key 和 Endpoint')
    return
  }
  testResult.value = null
  testTarget.value = target

  if (target === 'llm') testingLLM.value = true

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
    testingLLM.value = false
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
