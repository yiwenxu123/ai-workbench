<template>
  <div class="template-panel">
    <n-card title="提示词模板" size="small">
      <template #header-extra>
        <n-button size="small" @click="handleCreate">
          <template #icon><n-icon :component="AddOutline" /></template>
          新建
        </n-button>
      </template>

      <n-input
        v-model:value="templateStore.searchText"
        placeholder="搜索模板..."
        clearable
        class="search-input"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>

      <n-tabs v-model:value="activeTab" type="line" size="small" class="template-tabs">
        <n-tab-pane name="all" tab="全部">
          <TemplateList
            :templates="templateStore.filteredTemplates"
            @select="handleSelect"
            @edit="handleEdit"
            @delete="handleDelete"
            @duplicate="handleDuplicate"
          />
        </n-tab-pane>
        <n-tab-pane name="official" tab="官方模板">
          <TemplateList
            :templates="templateStore.officialTemplates"
            :readonly="true"
            @select="handleSelect"
            @duplicate="handleDuplicate"
          />
        </n-tab-pane>
        <n-tab-pane name="user" tab="我的模板">
          <TemplateList
            :templates="templateStore.userTemplates"
            @select="handleSelect"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <n-modal
      v-model:show="templateStore.showModal"
      preset="card"
      :title="templateStore.editingTemplate ? '编辑模板' : '新建模板'"
      style="width: 600px"
    >
      <n-form ref="formRef" :model="formData" label-placement="left" label-width="80">
        <n-form-item label="名称" path="name">
          <n-input v-model:value="formData.name" placeholder="模板名称" />
        </n-form-item>
        <n-form-item label="提示词" path="content">
          <n-input
            v-model:value="formData.content"
            type="textarea"
            placeholder="输入提示词，可使用 [SUBJECT]、[SCENE] 等占位符"
            :rows="4"
          />
        </n-form-item>
        <n-form-item label="分类" path="category">
          <n-select v-model:value="formData.category" :options="categoryOptions" />
        </n-form-item>
        <n-form-item label="负面词" path="negativePrompt">
          <n-input
            v-model:value="formData.negativePrompt"
            type="textarea"
            placeholder="负面提示词（可选）"
            :rows="2"
          />
        </n-form-item>
        <n-form-item label="推荐尺寸" path="recommendedSize">
          <n-select
            v-model:value="formData.recommendedSize"
            :options="sizeOptions"
            clearable
          />
        </n-form-item>
        <n-form-item label="标签" path="tags">
          <n-dynamic-tags v-model:value="formData.tags" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" @click="handleSave" style="margin-left: 8px">保存</n-button>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showApplyModal"
      preset="card"
      title="应用模板"
      style="width: 500px"
    >
      <template v-if="selectedTemplate">
        <div class="apply-preview">
          <div class="preview-name">{{ selectedTemplate.name }}</div>
          <div class="preview-desc">{{ selectedTemplate.content.slice(0, 100) }}...</div>
          
          <n-divider />

          <div v-if="placeholders.length > 0" class="placeholder-section">
            <n-text depth="3" style="font-size: 12px">替换占位符：</n-text>
            <div class="placeholder-inputs">
              <div v-for="ph in placeholders" :key="ph" class="placeholder-item">
                <span class="placeholder-label">{{ ph }}:</span>
                <n-input
                  v-model:value="placeholderValues[ph]"
                  :placeholder="`输入${ph}`"
                  size="small"
                />
              </div>
            </div>
          </div>

          <n-form-item label="预览">
            <div class="prompt-preview">{{ previewPrompt }}</div>
          </n-form-item>
        </div>
      </template>

      <template #footer>
        <n-button @click="showApplyModal = false">取消</n-button>
        <n-button type="primary" @click="applyTemplate">应用</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { NCard, NButton, NIcon, NInput, NTabs, NTabPane, NModal, NForm, NFormItem, NSelect, NDynamicTags, NDivider, NText, useMessage, useDialog } from 'naive-ui'
import { AddOutline, SearchOutline } from '@vicons/ionicons5'
import { useTemplateStore } from '../stores/template'
import { useGeneratorStore } from '../stores/generator'
import { useConfigStore } from '../stores'
import type { PromptTemplate, TemplateFormData } from '../types'
import TemplateList from './TemplateList.vue'

const emit = defineEmits<{
  (e: 'select', template: PromptTemplate, prompt: string): void
}>()

const message = useMessage()
const dialog = useDialog()
const templateStore = useTemplateStore()
const generatorStore = useGeneratorStore()
const configStore = useConfigStore()

const activeTab = ref('all')
const showApplyModal = ref(false)
const selectedTemplate = ref<PromptTemplate | null>(null)
const placeholderValues = ref<Record<string, string>>({})

const formData = ref<TemplateFormData>({
  name: '',
  content: '',
  category: 'general',
  tags: [],
  negativePrompt: '',
  recommendedSize: ''
})

const categoryOptions = [
  { label: '通用', value: 'general' },
  { label: '产品展示', value: 'product' },
  { label: '营销宣传', value: 'marketing' },
  { label: 'PPT配图', value: 'presentation' },
  { label: '人物肖像', value: 'portrait' },
  { label: '商业插画', value: 'illustration' },
  { label: '社媒素材', value: 'social' }
]

const sizeOptions = computed(() =>
  (configStore.serverConfig?.sizes || []).map(s => ({ label: s, value: s }))
)

const placeholders = computed(() => {
  if (!selectedTemplate.value) return []
  return templateStore.extractPlaceholders(selectedTemplate.value.content)
})

const previewPrompt = computed(() => {
  if (!selectedTemplate.value) return ''
  let prompt = selectedTemplate.value.content
  for (const [key, value] of Object.entries(placeholderValues.value)) {
    prompt = prompt.replace(new RegExp(`\\[${key}\\]`, 'g'), value)
  }
  return prompt
})

watch(() => templateStore.showModal, (val) => {
  if (val && templateStore.editingTemplate) {
    formData.value = {
      name: templateStore.editingTemplate.name,
      content: templateStore.editingTemplate.content,
      category: templateStore.editingTemplate.category,
      tags: [...templateStore.editingTemplate.tags],
      negativePrompt: templateStore.editingTemplate.negativePrompt || '',
      recommendedSize: templateStore.editingTemplate.recommendedSize || ''
    }
  } else if (val) {
    formData.value = { name: '', content: '', category: 'general', tags: [], negativePrompt: '', recommendedSize: '' }
  }
})

function handleCreate(): void {
  templateStore.cancelEdit()
  templateStore.showModal = true
}

function handleSelect(template: PromptTemplate): void {
  const phs = templateStore.extractPlaceholders(template.content)
  if (phs.length > 0) {
    selectedTemplate.value = template
    placeholderValues.value = {}
    phs.forEach(ph => {
      placeholderValues.value[ph] = ''
    })
    showApplyModal.value = true
  } else {
    applyPrompt(template, template.content)
  }
}

function handleEdit(template: PromptTemplate): void {
  templateStore.startEdit(template)
}

function handleDelete(id: number): void {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个模板吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await templateStore.remove(id)
      message.success('已删除')
    }
  })
}

async function handleDuplicate(id: number): Promise<void> {
  await templateStore.duplicate(id)
  message.success('已复制')
}

function handleCancel(): void {
  templateStore.cancelEdit()
  formData.value = { name: '', content: '', category: 'general', tags: [], negativePrompt: '', recommendedSize: '' }
}

async function handleSave(): Promise<void> {
  if (!formData.value.name || !formData.value.content) {
    message.warning('请填写名称和提示词')
    return
  }

  if (templateStore.editingTemplate) {
    await templateStore.update(templateStore.editingTemplate.id!, formData.value)
    message.success('更新成功')
  } else {
    await templateStore.add(formData.value)
    message.success('保存成功')
  }

  handleCancel()
}

function applyTemplate(): void {
  if (!selectedTemplate.value) return
  
  if (placeholders.value.some(ph => !placeholderValues.value[ph]?.trim())) {
    message.warning('请填写所有占位符')
    return
  }
  
  applyPrompt(selectedTemplate.value, previewPrompt.value)
  showApplyModal.value = false
}

function applyPrompt(template: PromptTemplate, prompt: string): void {
  generatorStore.prompt = prompt
  if (template.negativePrompt) {
    generatorStore.negativePrompt = template.negativePrompt
  }
  if (template.recommendedSize) {
    generatorStore.size = template.recommendedSize
  }
  emit('select', template, prompt)
  message.success('已应用模板')
}

onMounted(() => {
  templateStore.load()
})
</script>

<style scoped>
.template-panel {
  height: 100%;
}

.search-input {
  margin-bottom: 8px;
}

.template-tabs {
  margin-top: 8px;
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

.placeholder-section {
  margin-bottom: 16px;
}

.placeholder-inputs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.placeholder-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.placeholder-label {
  min-width: 80px;
  font-weight: 500;
}

.prompt-preview {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
