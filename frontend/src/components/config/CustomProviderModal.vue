<template>
  <n-modal
    :show="show"
    preset="card"
    title="自定义供应商"
    style="width: 480px"
    @update:show="$emit('update:show', $event)"
  >
    <p class="custom-modal-hint mb-3">填写以下信息接入自定义 API 供应商（适用于未列出的模型平台）</p>
    <n-form label-placement="left" label-width="100">
      <n-form-item label="供应商名称">
        <n-input v-model:value="customForm.name" placeholder="例如：Stability AI、Midjourney 代理" />
      </n-form-item>
      <n-form-item label="API Key">
        <n-input
          v-model:value="customForm.apiKey"
          type="password"
          show-password-on="click"
          placeholder="输入 API Key"
        />
      </n-form-item>
      <n-form-item label="API Endpoint">
        <n-input
          v-model:value="customForm.endpoint"
          placeholder="https://api.example.com/v1/generate"
        />
      </n-form-item>
      <n-form-item label="模型名称">
        <n-input
          v-model:value="customForm.model"
          placeholder="例如：stable-diffusion-xl"
        />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px">用于生成时选择使用的具体模型</n-text>
        </template>
      </n-form-item>
      <n-form-item label="类型">
        <n-tag type="info">{{ capability === 'video' ? '视频生成' : capability === 'edit' ? '图片编辑' : '图片分析' }}</n-tag>
      </n-form-item>
    </n-form>

    <template #footer>
      <n-space justify="space-between" style="width: 100%">
        <div>
          <n-button
            :loading="testingCustom"
            :disabled="!customForm.apiKey || !customForm.endpoint"
            @click="testConnection"
          >
            测试连接
          </n-button>
          <div v-if="testResult" class="test-result" :class="{ success: testResult.success }">
            {{ testResult.message }}
          </div>
        </div>
        <n-space>
          <n-button @click="$emit('update:show', false)">取消</n-button>
          <n-button type="primary" @click="saveCustomProvider" :disabled="!customForm.name || !customForm.apiKey">
            保存
          </n-button>
        </n-space>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  NModal, NForm, NFormItem, NInput,
  NTag, NButton, NSpace, NText,
  useMessage
} from 'naive-ui'
import { useProviderStore } from '../../stores'
import { apiService } from '../../api'
import type { ProviderType, ProviderCapability } from '../../types/provider'

const props = defineProps<{
  show: boolean
  capability: 'video' | 'edit' | 'vision'
}>()

defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()
const providerStore = useProviderStore()

const testingCustom = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const customForm = ref({
  name: '',
  apiKey: '',
  endpoint: '',
  model: ''
})

watch(() => props.show, (val) => {
  if (val) {
    customForm.value = { name: '', apiKey: '', endpoint: '', model: '' }
    testResult.value = null
  }
})

function saveCustomProvider() {
  if (!customForm.value.name || !customForm.value.apiKey) return

  const capMap: Record<string, ProviderCapability> = {
    video: 'video',
    edit: 'edit',
    vision: 'vision'
  }

  providerStore.upsertCapabilityProvider({
    name: customForm.value.name,
    type: 'custom' as ProviderType,
    apiKey: customForm.value.apiKey,
    endpoint: customForm.value.endpoint,
    defaultModel: customForm.value.model || undefined,
    capability: capMap[props.capability] ?? 'image'
  })

  message.success(`自定义供应商 ${customForm.value.name} 配置成功！`)
}

async function testConnection() {
  if (!customForm.value.apiKey || !customForm.value.endpoint) {
    message.warning('请先填写 API Key 和 Endpoint')
    return
  }
  testResult.value = null
  testingCustom.value = true

  try {
    const res = await apiService.validateApi({
      api_key: customForm.value.apiKey,
      api_endpoint: customForm.value.endpoint,
      provider_type: props.capability,
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
    testingCustom.value = false
  }
}
</script>

<style scoped>
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
