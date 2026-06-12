<template>
  <div class="section-block">
    <div class="section-header">
      <n-icon :component="Pencil" class="section-icon" />
      <span class="section-title">图片编辑</span>
      <n-tag v-if="providerStore.hasConfiguredEditProvider" type="success" size="small">已配置</n-tag>
      <n-tag v-if="configStore.isBackendConfigured('edit')" type="info" size="small">已由后端配置</n-tag>
    </div>

    <!-- 后端已配置 Key → 隐藏手动配置 -->
    <template v-if="configStore.isBackendConfigured('edit')">
      <n-alert type="success" size="small" class="mb-2">
        后端已配置图片编辑 API Key，开发者无需在此处重复配置。
      </n-alert>
    </template>

    <template v-else>
    <n-list bordered>
      <n-list-item v-for="preset in editPresets" :key="preset.type">
        <n-thing :title="preset.name">
          <template #avatar><n-tag type="success">推荐</n-tag></template>
          <template #description>{{ preset.description }}</template>
          <template #header-extra>
            <n-space align="center">
              <n-tag v-if="isEditConfigured(preset.type)" type="success" size="small">已配置</n-tag>
              <n-button size="small" :type="isEditConfigured(preset.type) ? 'default' : 'primary'" @click="showEditConfigModal(preset)">
                {{ isEditConfigured(preset.type) ? '修改' : '配置' }}
              </n-button>
            </n-space>
          </template>
        </n-thing>
      </n-list-item>
    </n-list>
    <n-button block dashed class="mt-2" @click="emit('open-custom', 'edit')">+ 自定义编辑供应商</n-button>
    </template>
  </div>

  <!-- ── 图片编辑配置弹窗 ── -->
  <n-modal
    v-model:show="showEditModal"
    preset="card"
    :title="`配置 ${currentEditPreset?.name || '图片编辑供应商'}`"
    style="width: 450px"
  >
    <n-form label-placement="left" label-width="100">
      <n-form-item label="API Key">
        <n-input
          v-model:value="editApiKeyInput"
          type="password"
          show-password-on="click"
          :placeholder="currentEditPreset?.keyPlaceholder || '请输入 API Key'"
        />
      </n-form-item>
      <n-form-item label="模型">
        <n-input
          v-model:value="editModelInput"
          :placeholder="currentEditPreset?.defaultModel || '请输入模型名称'"
        />
      </n-form-item>
      <n-form-item label="API Endpoint">
        <n-input
          v-model:value="editEndpointInput"
          :placeholder="currentEditPreset?.endpoint || 'API Endpoint'"
        />
      </n-form-item>
    </n-form>

    <div v-if="testTarget === 'edit' && testResult" class="test-result" :class="{ success: testResult.success }">
      {{ testResult.message }}
    </div>

    <template v-if="currentEditPreset?.helpUrl">
      <n-divider />
      <n-space vertical>
        <n-text depth="3">获取 API Key：</n-text>
        <n-button text type="primary" tag="a" :href="currentEditPreset.helpUrl" target="_blank">
          {{ currentEditPreset.helpText || '点击前往获取' }}
        </n-button>
      </n-space>
    </template>

    <template #footer>
      <n-space justify="space-between" style="width: 100%">
        <div>
          <n-button
            :loading="testingEdit"
            :disabled="!editApiKeyInput"
            @click="testConnection(editEndpointInput, editApiKeyInput, currentEditPreset?.type || 'edit', 'edit')"
          >
            测试连接
          </n-button>
        </div>
        <n-space>
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="saveEditConfig" :disabled="!editApiKeyInput">
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
import { Pencil } from 'lucide-vue-next'

const message = useMessage()
const providerStore = useProviderStore()
const configStore = useConfigStore()
const emit = defineEmits<{
  'open-custom': [capability: 'video' | 'edit' | 'vision']
}>()

interface EditPreset {
  type: string
  name: string
  description: string
  keyPlaceholder: string
  endpoint: string
  defaultModel?: string
  helpUrl?: string
  helpText?: string
}

const editPresets: EditPreset[] = [
  {
    type: 'aliyun-wanx',
    name: '阿里云万相编辑',
    description: '支持指令编辑、局部重绘、扩图，¥0.14/张',
    keyPlaceholder: '阿里云 DashScope API Key',
    endpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-edit',
    defaultModel: 'wanx-background-generation-v2',
    helpUrl: 'https://dashscope.console.aliyun.com/',
    helpText: '阿里云 DashScope 控制台'
  }
]

const showEditModal = ref(false)
const currentEditPreset = ref<EditPreset | null>(null)
const editApiKeyInput = ref('')
const editEndpointInput = ref('')
const editModelInput = ref('')

const testingEdit = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testTarget = ref<string | null>(null)

function isEditConfigured(type: string): boolean {
  return providerStore.providers.some(p => p.type === type && p.capabilities?.includes('edit') && p.apiKey)
}

function showEditConfigModal(preset: EditPreset): void {
  currentEditPreset.value = preset
  const existing = providerStore.providers.find(p => p.type === preset.type && p.capabilities?.includes('edit'))
  editApiKeyInput.value = existing?.apiKey || localStorage.getItem(`edit_${preset.type}_apiKey`) || ''
  editEndpointInput.value = existing?.endpoint || localStorage.getItem(`edit_${preset.type}_endpoint`) || preset.endpoint
  editModelInput.value = existing?.defaultModel || localStorage.getItem(`edit_${preset.type}_model`) || preset.defaultModel || ''
  showEditModal.value = true
}

function saveEditConfig(): void {
  if (!currentEditPreset.value || !editApiKeyInput.value) return

  providerStore.upsertCapabilityProvider({
    name: currentEditPreset.value.name,
    type: currentEditPreset.value.type as ProviderType,
    apiKey: editApiKeyInput.value,
    endpoint: editEndpointInput.value || currentEditPreset.value.endpoint,
    defaultModel: editModelInput.value || currentEditPreset.value.defaultModel || '',
    capability: 'edit'
  })

  showEditModal.value = false
  message.success(`${currentEditPreset.value.name} 编辑配置已保存`)
}

async function testConnection(endpoint: string, apiKey: string, providerType: string, target: string, model?: string) {
  if (!apiKey || !endpoint) {
    message.warning('请先填写 API Key 和 Endpoint')
    return
  }
  testResult.value = null
  testTarget.value = target

  if (target === 'edit') testingEdit.value = true

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
    testingEdit.value = false
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
