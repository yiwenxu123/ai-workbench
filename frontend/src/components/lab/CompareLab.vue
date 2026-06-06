<template>
  <n-modal v-model:show="showModal" preset="card" style="width: 90vw; max-width: 1200px;" title="A/B 对比实验室">
    <div class="compare-lab">
      <n-alert type="info" class="mb-3">
        固定其他参数，只改变一个变量，对比不同设置的效果差异
      </n-alert>

      <div class="lab-setup" v-if="!compareStore.items.length">
        <n-tabs v-model:value="compareMode" type="line">
          <n-tab-pane name="prompt" tab="提示词对比">
            <div class="setup-section">
              <p class="setup-desc">对比不同提示词的效果，固定模型和尺寸</p>
              <n-form label-placement="left" label-width="80">
                <n-form-item label="提示词1">
                  <n-input v-model:value="prompt1" type="textarea" :rows="2" placeholder="第一个提示词" />
                </n-form-item>
                <n-form-item label="提示词2">
                  <n-input v-model:value="prompt2" type="textarea" :rows="2" placeholder="第二个提示词" />
                </n-form-item>
                <n-form-item label="提示词3" v-if="showMorePrompts">
                  <n-input v-model:value="prompt3" type="textarea" :rows="2" placeholder="第三个提示词（可选）" />
                </n-form-item>
                <n-form-item label="提示词4" v-if="showMorePrompts">
                  <n-input v-model:value="prompt4" type="textarea" :rows="2" placeholder="第四个提示词（可选）" />
                </n-form-item>
                <n-button text @click="showMorePrompts = !showMorePrompts">
                  {{ showMorePrompts ? '收起' : '+ 添加更多' }}
                </n-button>
              </n-form>
            </div>
          </n-tab-pane>
          
          <n-tab-pane name="model" tab="模型对比">
            <div class="setup-section">
              <p class="setup-desc">对比不同模型的效果，固定提示词和尺寸</p>
              <n-form label-placement="left" label-width="80">
                <n-form-item label="提示词">
                  <n-input v-model:value="basePrompt" type="textarea" :rows="2" placeholder="输入提示词" />
                </n-form-item>
                <n-form-item label="选择模型">
                  <n-checkbox-group v-model:value="selectedModels">
                    <n-space>
                      <n-checkbox v-for="m in modelOptions" :key="m.value" :value="m.value" :label="m.label" />
                    </n-space>
                  </n-checkbox-group>
                </n-form-item>
              </n-form>
            </div>
          </n-tab-pane>
          
          <n-tab-pane name="size" tab="尺寸对比">
            <div class="setup-section">
              <p class="setup-desc">对比不同尺寸的效果，固定提示词和模型</p>
              <n-form label-placement="left" label-width="80">
                <n-form-item label="提示词">
                  <n-input v-model:value="basePrompt" type="textarea" :rows="2" placeholder="输入提示词" />
                </n-form-item>
                <n-form-item label="选择尺寸">
                  <n-checkbox-group v-model:value="selectedSizes">
                    <n-space>
                      <n-checkbox v-for="s in sizeOptions" :key="s" :value="s" :label="s" />
                    </n-space>
                  </n-checkbox-group>
                </n-form-item>
              </n-form>
            </div>
          </n-tab-pane>
        </n-tabs>

        <div class="common-config">
          <n-divider>通用配置</n-divider>
          <n-grid :cols="2" :x-gap="16">
            <n-gi>
              <n-form-item label="模型">
                <n-select v-model:value="commonModel" :options="modelOptions" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="尺寸">
                <n-select v-model:value="commonSize" :options="sizeOptions.map(s => ({ label: s, value: s }))" />
              </n-form-item>
            </n-gi>
          </n-grid>
        </div>
      </div>

      <div class="lab-results" v-else>
        <div class="results-header">
          <span>对比结果 ({{ compareStore.completedCount }}/{{ compareStore.items.length }})</span>
          <n-button size="small" @click="compareStore.clear()">重新设置</n-button>
        </div>
        
        <div class="results-grid" :class="gridClass">
          <div
            v-for="item in compareStore.items"
            :key="item.id"
            class="result-item"
          >
            <div class="item-header">
              <n-tag size="small" :type="item.status === 'success' ? 'success' : item.status === 'error' ? 'error' : 'default'">
                {{ getStatusLabel(item.status) }}
              </n-tag>
            </div>
            
            <div class="item-config">
              <span v-if="compareStore.mode === 'prompt'" class="config-text">{{ item.prompt.slice(0, 30) }}...</span>
              <span v-else-if="compareStore.mode === 'model'" class="config-text">模型: {{ item.model }}</span>
              <span v-else class="config-text">尺寸: {{ item.size }}</span>
            </div>

            <div class="item-image">
              <div v-if="item.status === 'generating'" class="generating-indicator">
                <n-spin size="small" />
                <span>生成中...</span>
              </div>
              <n-empty v-else-if="item.status === 'error'" :description="item.error || undefined" size="small" />
              <n-image
                v-else-if="item.imageUrl"
                :src="item.imageUrl"
                object-fit="contain"
                lazy
                class="generated-image"
              />
              <n-empty v-else description="等待生成" size="small" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="modal-footer">
        <n-button @click="showModal = false">关闭</n-button>
        <n-button 
          type="primary" 
          :loading="compareStore.isGenerating"
          :disabled="!canStart"
          @click="startCompare"
        >
          {{ compareStore.isGenerating ? '生成中...' : '开始对比' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NModal, NTabs, NTabPane, NForm, NFormItem, NInput, NSelect, NButton, NGrid, NGi, NCheckboxGroup, NCheckbox, NSpace, NDivider, NAlert, NTag, NSpin, NEmpty, NImage } from 'naive-ui'
import { useCompareStore } from '../../stores/compare'
import { useConfigStore, useProviderStore } from '../../stores'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const compareStore = useCompareStore()
const configStore = useConfigStore()
const providerStore = useProviderStore()

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const compareMode = ref<'prompt' | 'model' | 'size'>('prompt')
const showMorePrompts = ref(false)

const prompt1 = ref('')
const prompt2 = ref('')
const prompt3 = ref('')
const prompt4 = ref('')
const basePrompt = ref('')
const selectedModels = ref<string[]>([])
const selectedSizes = ref<string[]>([])
const commonModel = ref('default')
const commonSize = ref('1024x1024')

const modelOptions = computed(() =>
  (configStore.serverConfig?.models || []).map(m => ({ label: m.name, value: m.id }))
)

const sizeOptions = computed(() =>
  configStore.serverConfig?.sizes || ['1024x1024']
)

const gridClass = computed(() => {
  const count = compareStore.items.length
  if (count <= 2) return 'grid-2'
  if (count <= 3) return 'grid-3'
  return 'grid-4'
})

const canStart = computed(() => {
  if (!providerStore.hasConfiguredImageProvider) return false
  
  if (compareMode.value === 'prompt') {
    return prompt1.value.trim() && prompt2.value.trim()
  } else if (compareMode.value === 'model') {
    return basePrompt.value.trim() && selectedModels.value.length >= 2
  } else {
    return basePrompt.value.trim() && selectedSizes.value.length >= 2
  }
})

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    generating: '生成中',
    success: '成功',
    error: '失败'
  }
  return labels[status] || status
}

function startCompare(): void {
  if (!canStart.value) return

  if (compareMode.value === 'prompt') {
    const prompts = [prompt1.value, prompt2.value]
    if (prompt3.value.trim()) prompts.push(prompt3.value)
    if (prompt4.value.trim()) prompts.push(prompt4.value)
    compareStore.setupPromptCompare(prompts, commonModel.value, commonSize.value)
  } else if (compareMode.value === 'model') {
    compareStore.setupModelCompare(basePrompt.value, selectedModels.value, commonSize.value)
  } else {
    compareStore.setupSizeCompare(basePrompt.value, commonModel.value, selectedSizes.value)
  }

  compareStore.generateAll()
}

watch(showModal, (val) => {
  if (!val) {
    compareStore.clear()
  }
})
</script>

<style scoped>
.compare-lab {
  min-height: 400px;
}

.mb-3 {
  margin-bottom: 12px;
}

.setup-section {
  padding: 16px 0;
}

.setup-desc {
  color: #666;
  margin-bottom: 16px;
}

.common-config {
  margin-top: 16px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
}

.results-grid {
  display: grid;
  gap: 16px;
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.grid-4 {
  grid-template-columns: repeat(2, 1fr);
}

.result-item {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e8e8e8;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-config {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.config-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-image {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 6px;
}

.generating-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #999;
  font-size: 13px;
}

.generated-image {
  max-width: 100%;
  max-height: 100%;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
