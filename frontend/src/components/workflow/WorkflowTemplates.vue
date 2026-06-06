<template>
  <div class="workflow-templates">
    <n-card title="工作流模板" size="small">
      <template #header-extra>
        <n-button size="tiny" @click="showCreateModal = true">
          + 新建
        </n-button>
      </template>

      <n-input
        v-model:value="workflowStore.searchText"
        placeholder="搜索模板..."
        clearable
        size="small"
        class="search-input"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>

      <n-space class="category-filter">
        <n-tag
          v-for="cat in workflowStore.categories"
          :key="cat.value"
          size="small"
          :type="workflowStore.selectedCategory === cat.value ? 'primary' : 'default'"
          @click="workflowStore.selectedCategory = cat.value"
        >
          {{ cat.label }}
        </n-tag>
      </n-space>

      <n-scrollbar style="max-height: 350px">
        <div class="template-list">
          <div
            v-for="template in workflowStore.filteredTemplates"
            :key="template.id"
            class="template-item"
            @click="selectTemplate(template)"
          >
            <div class="template-header">
              <span class="template-name">{{ template.name }}</span>
              <n-tag size="tiny">{{ getCategoryLabel(template.category) }}</n-tag>
            </div>
            <div class="template-desc">{{ template.description }}</div>
            <div class="template-config">
              <span class="config-item">{{ template.config.size }}</span>
            </div>
            <div class="template-tags">
              <n-tag v-for="tag in template.tags" :key="tag" size="tiny" round>{{ tag }}</n-tag>
            </div>
          </div>
        </div>
      </n-scrollbar>
    </n-card>

    <n-modal v-model:show="showApplyModal" preset="card" style="width: 500px" title="应用模板">
      <template v-if="selectedTemplate">
        <div class="apply-preview">
          <div class="preview-name">{{ selectedTemplate.name }}</div>
          <div class="preview-desc">{{ selectedTemplate.description }}</div>
          
          <n-divider />

          <n-form label-placement="left" label-width="80">
            <n-form-item label="变量替换">
              <div class="variable-inputs">
                <div
                  v-for="variable in extractedVariables"
                  :key="variable"
                  class="variable-item"
                >
                  <span class="variable-label">{{ variable }}:</span>
                  <n-input
                    v-model:value="variableValues[variable]"
                    :placeholder="`输入${variable}`"
                    size="small"
                  />
                </div>
              </div>
            </n-form-item>
            
            <n-form-item label="预览">
              <div class="prompt-preview">{{ previewPrompt }}</div>
            </n-form-item>
          </n-form>
        </div>
      </template>

      <template #footer>
        <n-button @click="showApplyModal = false">取消</n-button>
        <n-button type="primary" @click="applyTemplate">应用</n-button>
      </template>
    </n-modal>

    <n-modal v-model:show="showCreateModal" preset="card" style="width: 500px" title="创建模板">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="名称" required>
          <n-input v-model:value="newTemplate.name" placeholder="模板名称" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newTemplate.description" placeholder="模板描述" />
        </n-form-item>
        <n-form-item label="分类">
          <n-select
            v-model:value="newTemplate.category"
            :options="workflowStore.categories.filter(c => c.value !== 'all')"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-select
            v-model:value="newTemplate.config.model"
            :options="modelOptions"
          />
        </n-form-item>
        <n-form-item label="尺寸">
          <n-select
            v-model:value="newTemplate.config.size"
            :options="sizeOptions"
          />
        </n-form-item>
        <n-form-item label="提示词模板">
          <n-input
            v-model:value="newTemplate.config.promptTemplate"
            type="textarea"
            :rows="3"
            placeholder="使用 {变量名} 作为占位符，如：{主题}、{风格}"
          />
        </n-form-item>
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="newTemplate.tags" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" @click="createTemplate">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NInput, NIcon, NTag, NSpace, NScrollbar, NModal, NForm, NFormItem, NSelect, NDivider, NButton, NDynamicTags, useMessage } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import { useWorkflowStore, type WorkflowTemplate } from '../../stores/workflow'
import { useConfigStore } from '../../stores'
import { useGeneratorStore } from '../../stores'

const message = useMessage()
const workflowStore = useWorkflowStore()
const configStore = useConfigStore()
const generatorStore = useGeneratorStore()

const showApplyModal = ref(false)
const showCreateModal = ref(false)
const selectedTemplate = ref<WorkflowTemplate | null>(null)
const variableValues = ref<Record<string, string>>({})

const newTemplate = ref({
  name: '',
  description: '',
  category: 'custom',
  config: {
    model: 'default',
    size: '1024x1024',
    promptTemplate: ''
  },
  tags: [] as string[]
})

const modelOptions = computed(() =>
  (configStore.serverConfig?.models || []).map(m => ({ label: m.name, value: m.id }))
)

const sizeOptions = computed(() =>
  (configStore.serverConfig?.sizes || []).map(s => ({ label: s, value: s }))
)

const extractedVariables = computed(() => {
  if (!selectedTemplate.value) return []
  const matches = selectedTemplate.value.config.promptTemplate.match(/\{(\w+)\}/g)
  return matches ? [...new Set(matches.map(m => m.slice(1, -1)))] : []
})

const previewPrompt = computed(() => {
  if (!selectedTemplate.value) return ''
  return workflowStore.applyTemplate(selectedTemplate.value, variableValues.value)
})

function getCategoryLabel(category: string): string {
  const cat = workflowStore.categories.find(c => c.value === category)
  return cat?.label || category
}

function selectTemplate(template: WorkflowTemplate) {
  selectedTemplate.value = template
  variableValues.value = {}
  extractedVariables.value.forEach(v => {
    variableValues.value[v] = ''
  })
  showApplyModal.value = true
}

function applyTemplate() {
  if (!selectedTemplate.value) return
  
  const prompt = workflowStore.applyTemplate(selectedTemplate.value, variableValues.value)
  
  generatorStore.prompt = prompt
  generatorStore.model = selectedTemplate.value.config.model
  generatorStore.size = selectedTemplate.value.config.size
  
  showApplyModal.value = false
  message.success('模板已应用')
}

async function createTemplate() {
  if (!newTemplate.value.name || !newTemplate.value.config.promptTemplate) {
    message.warning('请填写名称和提示词模板')
    return
  }
  
  await workflowStore.add(newTemplate.value)
  showCreateModal.value = false
  message.success('模板已创建')
  
  newTemplate.value = {
    name: '',
    description: '',
    category: 'custom',
    config: {
      model: 'default',
      size: '1024x1024',
      promptTemplate: ''
    },
    tags: []
  }
}

onMounted(() => {
  workflowStore.load()
})
</script>

<style scoped>
.workflow-templates {
  height: 100%;
}

.search-input {
  margin-bottom: 8px;
}

.category-filter {
  margin-bottom: 12px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.template-item:hover {
  background: #f0f0f0;
  border-color: #e0e0e0;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.template-name {
  font-weight: 600;
  font-size: 14px;
}

.template-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.template-config {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
}

.config-item {
  font-size: 11px;
  color: #999;
}

.template-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.apply-preview {
  padding: 8px 0;
}

.preview-name {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 4px;
}

.preview-desc {
  color: #666;
  font-size: 13px;
}

.variable-inputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.variable-label {
  min-width: 60px;
  font-weight: 500;
}

.prompt-preview {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}
</style>
