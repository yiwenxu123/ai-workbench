<template>
  <div class="provider-manager">
    <n-card title="供应商管理" size="small">
      <template #header-extra>
        <n-space :size="8">
          <n-button
            v-if="providerStore.providers.length > 1"
            size="small"
            :loading="testingAll"
            @click="testAllConnections"
          >
            测试全部
          </n-button>
          <n-button size="small" type="primary" @click="showAddModal = true">
            + 添加供应商
          </n-button>
        </n-space>
      </template>

      <n-alert v-if="!providerStore.hasConfiguredProvider" type="warning" class="mb-3">
        请选择一个平台预设并填写 API Key，保存后即可开始生成图片
      </n-alert>

      <n-empty v-if="providerStore.providers.length === 0" description="暂无配置的供应商">
        <template #extra>
          <n-button size="small" @click="showAddModal = true">添加供应商</n-button>
        </template>
      </n-empty>

      <div v-else class="provider-list">
        <div
          v-for="provider in providerStore.providers"
          :key="provider.id"
          class="provider-item"
          :class="{ 'is-default': provider.isDefault }"
        >
          <div class="provider-header">
            <div class="provider-info">
              <span class="provider-name">{{ provider.name }}</span>
              <n-tag size="tiny" :type="getStatusType(provider.status)">
                {{ getStatusLabel(provider.status) }}
              </n-tag>
              <n-tag v-if="provider.isDefault" size="tiny" type="success">默认</n-tag>
            </div>
            <div class="provider-actions">
              <n-button
                size="tiny"
                :loading="checkingId === provider.id"
                @click="testConnection(provider)"
              >
                测试连接
              </n-button>
              <n-button size="tiny" @click="editProvider(provider)">编辑</n-button>
              <n-button
                size="tiny"
                type="error"
                @click="confirmDelete(provider.id)"
              >
                删除
              </n-button>
            </div>
          </div>
          
          <div class="provider-details">
            <div class="detail-row">
              <span class="detail-label">Endpoint:</span>
              <span class="detail-value">{{ truncateUrl(provider.endpoint) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">API Key:</span>
              <span class="detail-value">{{ maskApiKey(provider.apiKey) }}</span>
            </div>
            <div class="detail-row" v-if="provider.latency">
              <span class="detail-label">延迟:</span>
              <span class="detail-value">{{ provider.latency }}ms</span>
            </div>
          </div>

          <div class="provider-footer">
            <n-button
              v-if="!provider.isDefault"
              size="tiny"
              text
              type="primary"
              @click="providerStore.setDefaultProvider(provider.id)"
            >
              设为默认
            </n-button>
          </div>
        </div>
      </div>
    </n-card>

    <n-modal v-model:show="showAddModal" preset="card" style="width: 500px" title="添加供应商">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="选择预设">
          <n-select
            v-model:value="selectedPreset"
            :options="presetOptions"
            placeholder="选择供应商预设"
            @update:value="applyPreset"
          />
        </n-form-item>
        
        <n-form-item label="名称">
          <n-input v-model:value="formData.name" placeholder="供应商名称" />
        </n-form-item>
        
        <n-form-item label="Endpoint">
          <n-input v-model:value="formData.endpoint" placeholder="API 端点地址" />
        </n-form-item>
        
        <n-form-item label="API Key">
          <n-input
            v-model:value="formData.apiKey"
            type="password"
            show-password-on="click"
            placeholder="API 密钥"
          />
        </n-form-item>

        <n-form-item label="默认模型">
          <n-input v-model:value="formData.defaultModel" placeholder="默认使用的模型" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-button @click="showAddModal = false">取消</n-button>
        <n-button type="primary" @click="saveProvider" :disabled="!canSave">
          保存
        </n-button>
      </template>
    </n-modal>

    <n-modal v-model:show="showEditModal" preset="card" style="width: 500px" title="编辑供应商">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="名称">
          <n-input v-model:value="editFormData.name" placeholder="供应商名称" />
        </n-form-item>
        
        <n-form-item label="Endpoint">
          <n-input v-model:value="editFormData.endpoint" placeholder="API 端点地址" />
        </n-form-item>
        
        <n-form-item label="API Key">
          <n-input
            v-model:value="editFormData.apiKey"
            type="password"
            show-password-on="click"
            placeholder="API 密钥"
          />
        </n-form-item>

        <n-form-item label="默认模型">
          <n-input v-model:value="editFormData.defaultModel" placeholder="默认使用的模型" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="updateProvider">
          更新
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { NCard, NButton, NTag, NEmpty, NModal, NForm, NFormItem, NInput, NSelect, NAlert, useMessage, useDialog } from 'naive-ui'
import { useProviderStore } from '../stores/provider'
import { testImageProvider } from '../composables/useProviderTest'
import { providerPresets } from '../types/provider'
import type { ApiProvider, ProviderType } from '../types/provider'

const message = useMessage()
const dialog = useDialog()
const providerStore = useProviderStore()

const showAddModal = ref(false)
const showEditModal = ref(false)
const checkingId = ref<string | null>(null)
const testingAll = ref(false)
const selectedPreset = ref<string | null>(null)
const editingId = ref<string | null>(null)

const formData = ref({
  name: '',
  type: 'custom' as ProviderType,
  endpoint: '',
  apiKey: '',
  defaultModel: ''
})

const editFormData = ref({
  name: '',
  endpoint: '',
  apiKey: '',
  defaultModel: ''
})

const presetOptions = computed(() => [
  { label: '自定义', value: 'custom' },
  ...providerPresets.map(p => ({
    label: p.name,
    value: p.name  // 用 name 作为唯一 key，避免同 type 预设冲突
  }))
])

const canSave = computed(() => 
  formData.value.name && 
  formData.value.endpoint && 
  formData.value.apiKey
)

// 通义千问模型 → 正确 endpoint 的映射
const ALIYUN_MODEL_ENDPOINTS: Record<string, string> = {
  'qwen-image-plus': 'https://dashscope.aliyuncs.com/compatible-mode/v1/images/generations',
  'qwen-image': 'https://dashscope.aliyuncs.com/compatible-mode/v1/images/generations',
  'qwen-image-2.0-pro': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation',
  'qwen-image-2.0': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation',
}

function applyPreset(name: string): void {
  if (name === 'custom') {
    formData.value = {
      name: '',
      type: 'custom',
      endpoint: '',
      apiKey: '',
      defaultModel: ''
    }
    return
  }
  
  const preset = providerPresets.find(p => p.name === name)
  if (preset) {
    formData.value = {
      name: preset.name,
      type: preset.type,
      endpoint: preset.endpoint,
      apiKey: '',
      defaultModel: preset.defaultModel
    }
  }
}

// 当 defaultModel 改变时自动匹配正确的 endpoint
watch(() => formData.value.defaultModel, (model) => {
  if (ALIYUN_MODEL_ENDPOINTS[model]) {
    formData.value.endpoint = ALIYUN_MODEL_ENDPOINTS[model]
  }
})
watch(() => editFormData.value.defaultModel, (model) => {
  if (ALIYUN_MODEL_ENDPOINTS[model]) {
    editFormData.value.endpoint = ALIYUN_MODEL_ENDPOINTS[model]
  }
})

function getStatusType(status: string): 'success' | 'error' | 'warning' | 'default' {
  const map: Record<string, 'success' | 'error' | 'warning' | 'default'> = {
    active: 'success',
    error: 'error',
    checking: 'warning',
    inactive: 'default'
  }
  return map[status] || 'default'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: '已连接',
    error: '连接失败',
    checking: '检测中',
    inactive: '未检测'
  }
  return labels[status] || status
}

function truncateUrl(url: string): string {
  if (url.length <= 40) return url
  return url.slice(0, 40) + '...'
}

function maskApiKey(key: string): string {
  if (!key) return '未配置'
  if (key.length <= 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}

async function testConnection(provider: ApiProvider): Promise<void> {
  checkingId.value = provider.id
  providerStore.updateProvider(provider.id, { status: 'checking' })
  
  const result = await testImageProvider(provider)
  
  providerStore.updateProvider(provider.id, {
    status: result.success ? 'active' : 'error',
    latency: result.latency,
    errorMessage: result.error
  })
  
  checkingId.value = null
  
  if (result.success) {
    message.success(`连接成功，延迟 ${result.latency}ms`)
  } else {
    message.error(result.error || '连接失败')
  }
}

async function testAllConnections(): Promise<void> {
  testingAll.value = true
  const configured = providerStore.providers.filter(p => p.apiKey && p.endpoint)
  let successCount = 0
  let failCount = 0

  for (const provider of configured) {
    checkingId.value = provider.id
    providerStore.updateProvider(provider.id, { status: 'checking' })
    const result = await testImageProvider(provider)
    providerStore.updateProvider(provider.id, {
      status: result.success ? 'active' : 'error',
      latency: result.latency,
      errorMessage: result.error,
    })
    if (result.success) successCount++
    else failCount++
  }

  checkingId.value = null
  testingAll.value = false

  if (failCount === 0) {
    message.success(`全部 ${successCount} 个供应商连接正常`)
  } else {
    message.warning(`${successCount} 个成功，${failCount} 个失败`)
  }
}

function saveProvider(): void {
  const newProvider = providerStore.addProvider({
    name: formData.value.name,
    type: formData.value.type,
    endpoint: formData.value.endpoint,
    apiKey: formData.value.apiKey,
    defaultModel: formData.value.defaultModel
  })
  
  showAddModal.value = false
  message.success('供应商已添加')
  
  formData.value = {
    name: '',
    type: 'custom',
    endpoint: '',
    apiKey: '',
    defaultModel: ''
  }
  selectedPreset.value = null
  
  testConnection(newProvider)
}

function editProvider(provider: ApiProvider): void {
  editingId.value = provider.id
  editFormData.value = {
    name: provider.name,
    endpoint: provider.endpoint,
    apiKey: provider.apiKey,
    defaultModel: provider.defaultModel
  }
  showEditModal.value = true
}

function updateProvider(): void {
  if (!editingId.value) return
  
  providerStore.updateProvider(editingId.value, {
    name: editFormData.value.name,
    endpoint: editFormData.value.endpoint,
    apiKey: editFormData.value.apiKey,
    defaultModel: editFormData.value.defaultModel
  })
  
  showEditModal.value = false
  message.success('供应商已更新')
}

function confirmDelete(id: string): void {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个供应商配置吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: () => {
      providerStore.removeProvider(id)
      message.success('供应商已删除')
    }
  })
}

onMounted(() => {
  providerStore.init()
})
</script>

<style scoped>
.provider-manager {
  height: 100%;
}

.mb-3 {
  margin-bottom: 12px;
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.provider-item {
  background: var(--bg-subtle);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e8e8e8;
}

.provider-item.is-default {
  border-color: #52c41a;
  background: #f6ffed;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.provider-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-name {
  font-weight: 600;
  font-size: 14px;
}

.provider-actions {
  display: flex;
  gap: 6px;
}

.provider-details {
  margin-bottom: 8px;
}

.detail-row {
  display: flex;
  font-size: 12px;
  margin-bottom: 4px;
}

.detail-label {
  color: #999;
  min-width: 70px;
}

.detail-value {
  color: #666;
  word-break: break-all;
}

.provider-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
