<template>
  <n-modal v-model:show="showModal" preset="card" style="width: 800px; max-height: 90vh;" title="批量生成">
    <div class="batch-generator">
      <n-alert type="info" class="mb-3">
        <template #icon></template>
        使用 {变量名} 定义变量，系统将自动生成所有组合
      </n-alert>

      <n-form label-placement="left" label-width="80">
        <n-form-item label="提示词模板">
          <n-input
            v-model:value="batchGenerator.template.value"
            type="textarea"
            :rows="3"
            placeholder="例如：一只{动物}在{地点}，{风格}风格"
            @update:value="batchGenerator.setTemplate"
          />
        </n-form-item>

        <n-form-item label="变量定义" v-if="batchGenerator.variables.value.length > 0">
          <div class="variables-section">
            <div
              v-for="variable in batchGenerator.variables.value"
              :key="variable.name"
              class="variable-item"
            >
              <div class="variable-header">
                <n-tag type="primary" size="small">{ { {{ variable.name }} } }</n-tag>
                <span class="variable-count">{{ variable.values.filter(v => v.trim()).length }} 个值</span>
              </div>
              <n-dynamic-tags
                v-model:value="variable.values"
                size="small"
              />
            </div>
          </div>
        </n-form-item>

        <n-form-item label="组合预览">
          <div class="preview-section">
            <n-tag type="info" size="small">
              将生成 {{ batchGenerator.totalCombinations.value }} 张图片
            </n-tag>
            <div class="preview-list" v-if="previewCombinations.length > 0">
              <n-tag
                v-for="(combo, idx) in previewCombinations.slice(0, 10)"
                :key="idx"
                size="small"
                class="preview-tag"
              >
                {{ Object.values(combo).join(' + ') }}
              </n-tag>
              <n-tag v-if="previewCombinations.length > 10" size="small" type="warning">
                ...还有 {{ previewCombinations.length - 10 }} 个组合
              </n-tag>
            </div>
          </div>
        </n-form-item>

        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="模型">
              <n-select v-model:value="batchModel" :options="modelOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="尺寸">
              <n-select v-model:value="batchSize" :options="sizeOptions.map(s => ({ label: s, value: s }))" />
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>

      <div class="results-section" v-if="batchGenerator.tasks.value.length > 0">
        <n-divider>生成结果</n-divider>
        
        <n-progress
          type="line"
          :percentage="batchGenerator.progress.value"
          :status="batchGenerator.isGenerating.value ? 'default' : 'success'"
        />

        <div class="results-grid">
          <div
            v-for="task in batchGenerator.tasks.value"
            :key="task.id"
            class="result-item"
          >
            <div class="result-vars">
              {{ Object.values(task.variables).join(' + ') }}
            </div>
            <div class="result-status">
              <n-tag
                size="tiny"
                :type="task.status === 'success' ? 'success' : task.status === 'error' ? 'error' : 'default'"
              >
                {{ getStatusLabel(task.status) }}
              </n-tag>
            </div>
            <div class="result-image" v-if="task.imageUrl">
              <n-image :src="task.imageUrl" lazy object-fit="cover" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <n-button @click="batchGenerator.clear()" v-if="batchGenerator.tasks.value.length > 0">
          清空
        </n-button>
        <n-button @click="showModal = false">关闭</n-button>
        <n-button
          type="primary"
          :loading="batchGenerator.isGenerating.value"
          :disabled="!canStart"
          @click="startBatch"
        >
          {{ batchGenerator.isGenerating.value ? `生成中 (${batchGenerator.progress.value}%)` : '开始批量生成' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NModal, NForm, NFormItem, NInput, NSelect, NButton, NGrid, NGi, NTag, NDynamicTags, NDivider, NAlert, NProgress, NImage, useMessage } from 'naive-ui'
import { useBatchGenerator } from '../../composables/useBatchGenerator'
import { useConfigStore, useProviderStore } from '../../stores'
import { apiService } from '../../api'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const message = useMessage()
const configStore = useConfigStore()
const providerStore = useProviderStore()
const batchGenerator = useBatchGenerator()

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const batchModel = ref('default')
const batchSize = ref('1024x1024')

const modelOptions = computed(() =>
  (configStore.serverConfig?.models || []).map(m => ({ label: m.name, value: m.id }))
)

const sizeOptions = computed(() =>
  configStore.serverConfig?.sizes || ['1024x1024']
)

const previewCombinations = computed(() => 
  batchGenerator.generateCombinations()
)

const canStart = computed(() => 
  batchGenerator.totalCombinations.value > 0 && 
  batchGenerator.totalCombinations.value <= 20 &&
  providerStore.hasConfiguredImageProvider
)

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待',
    generating: '生成中',
    success: '成功',
    error: '失败'
  }
  return labels[status] || status
}

async function generateTask(task: { id: string; prompt: string; status: string; imageUrl: string | null; error: string | null }): Promise<void> {
  task.status = 'generating'

  try {
    const activeProvider = providerStore.getDefaultProviderByCapability('image')
    if (!activeProvider || !activeProvider.apiKey || !activeProvider.endpoint) {
      task.error = '请先配置图像生成API密钥'
      task.status = 'error'
      return
    }

    const params = {
      prompt: task.prompt,
      model: batchModel.value,
      size: batchSize.value,
      api_key: activeProvider.apiKey,
      api_endpoint: activeProvider.endpoint
    }

    const result = await apiService.generateImage(params)

    if (result.success && result.data?.data?.[0]) {
      const imageData = result.data.data[0]
      task.imageUrl = imageData.url || 
        (imageData.b64_json ? `data:image/png;base64,${imageData.b64_json}` : null)
      task.status = 'success'
    } else {
      task.error = result.error || '生成失败'
      task.status = 'error'
    }
  } catch {
    task.error = '请求失败'
    task.status = 'error'
  }
}

async function startBatch(): Promise<void> {
  if (!canStart.value) return

  batchGenerator.prepareTasks()
  batchGenerator.isGenerating.value = true

  for (const task of batchGenerator.tasks.value) {
    await generateTask(task)
    await new Promise(resolve => setTimeout(resolve, 500))
  }

  batchGenerator.isGenerating.value = false
  message.success(`批量生成完成！成功 ${batchGenerator.tasks.value.filter(t => t.status === 'success').length} 张`)
}

watch(showModal, (val) => {
  if (!val) {
    batchGenerator.clear()
  }
})
</script>

<style scoped>
.batch-generator {
  min-height: 300px;
}

.mb-3 {
  margin-bottom: 12px;
}

.variables-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.variable-item {
  background: #fafafa;
  padding: 12px;
  border-radius: 6px;
}

.variable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.variable-count {
  font-size: 12px;
  color: #999;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.preview-tag {
  font-size: 11px;
}

.results-section {
  margin-top: 16px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.result-item {
  background: #fafafa;
  border-radius: 6px;
  padding: 8px;
}

.result-vars {
  font-size: 11px;
  color: #666;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-status {
  margin-bottom: 4px;
}

.result-image {
  height: 100px;
  border-radius: 4px;
  overflow: hidden;
}

.result-image :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
