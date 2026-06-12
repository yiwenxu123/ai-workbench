<template>
  <div>
    <n-space justify="space-between" class="mb-3">
      <n-input v-model:value="searchText" placeholder="搜索我的模板..." clearable size="small" style="width: 200px" />
      <n-button type="primary" size="small" @click="openCreate">+ 新建模板</n-button>
    </n-space>

    <n-space class="mb-3">
      <n-tag v-for="cat in categories" :key="cat.value" size="small" :type="selectedCategory === cat.value ? 'primary' : 'default'" @click="selectedCategory = cat.value">
        {{ cat.label }}
      </n-tag>
    </n-space>

    <n-scrollbar style="max-height: 300px">
      <n-empty v-if="filtered.length === 0" description="暂无模板，点击上方新建" />
      <n-list bordered v-else>
        <n-list-item v-for="template in filtered" :key="template.id">
          <n-thing :title="template.name" :description="template.description">
            <template #avatar>
              <n-tag size="small">{{ getCategoryLabel(template.category) }}</n-tag>
            </template>
            <template #action>
              <n-space>
                <n-button size="small" type="primary" @click="apply(template)">使用</n-button>
                <n-button size="small" @click="edit(template)">编辑</n-button>
                <n-button size="small" type="error" @click="remove(template)">删除</n-button>
              </n-space>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-scrollbar>

    <n-modal v-model:show="showFormModal" preset="card" :title="editing ? '编辑模板' : '新建模板'" style="width: 600px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="模板名称" required><n-input v-model:value="form.name" placeholder="如：小红书封面" /></n-form-item>
        <n-form-item label="描述"><n-input v-model:value="form.description" placeholder="模板用途描述" /></n-form-item>
        <n-form-item label="分类"><n-select v-model:value="form.category" :options="categories.map(c => ({ label: c.label, value: c.value }))" /></n-form-item>
        <n-form-item label="提示词模板" required><n-input v-model:value="form.promptTemplate" type="textarea" :rows="4" placeholder="使用 {变量名} 表示可替换变量" /></n-form-item>
        <n-form-item label="负面提示词"><n-input v-model:value="form.negativePrompt" type="textarea" :rows="2" placeholder="不想要的内容（可选）" /></n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-gi><n-form-item label="尺寸"><n-select v-model:value="form.size" :options="sizeOptions" /></n-form-item></n-gi>
          <n-gi><n-form-item label="模型"><n-select v-model:value="form.model" :options="modelOptions" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item label="标签"><n-dynamic-tags v-model:value="form.tags" /></n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showFormModal = false">取消</n-button>
          <n-button type="primary" @click="save">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showApplyModal" preset="card" title="应用模板" style="width: 500px">
      <template v-if="applying">
        <div class="apply-preview">
          <div class="preview-name">{{ applying.name }}</div>
          <div class="preview-desc">{{ applying.description }}</div>
          <n-divider />
          <n-form label-placement="left" label-width="80">
            <n-form-item label="变量替换">
              <div class="variable-inputs">
                <div v-for="variable in extractedVariables" :key="variable" class="variable-item">
                  <span class="variable-label">{{ variable }}:</span>
                  <n-input v-model:value="variableValues[variable]" :placeholder="`输入${variable}`" size="small" />
                </div>
              </div>
            </n-form-item>
          </n-form>
          <n-card size="small" title="预览"><n-text>{{ previewPrompt }}</n-text></n-card>
        </div>
      </template>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showApplyModal = false">取消</n-button>
          <n-button type="primary" @click="confirmApply">应用到生成面板</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore } from '../../stores'
import { useWorkflowStore, type WorkflowTemplate } from '../../stores/workflow'

const emit = defineEmits<{ select: [prompt: string] }>()
const message = useMessage()
const generatorStore = useGeneratorStore()
const workflowStore = useWorkflowStore()

const categories = [
  { label: '全部', value: 'all' },
  { label: '社媒', value: 'social' },
  { label: '电商', value: 'ecommerce' },
  { label: '设计', value: 'design' },
  { label: '其他', value: 'other' }
]

const sizeOptions = [
  { label: '1024x1024 (正方形)', value: '1024x1024' },
  { label: '1024x1792 (竖版)', value: '1024x1792' },
  { label: '1792x1024 (横版)', value: '1792x1024' },
  { label: '2048x2048 (高清正方形)', value: '2048x2048' },
  { label: '1440x2560 (小红书封面)', value: '1440x2560' }
]

const modelOptions = [
  { label: '豆包 Seedream 4.5', value: 'doubao-seedream-4-5-251128' },
  { label: '豆包 Seedream 4.0', value: 'doubao-seedream-4-0-250828' },
  { label: '智谱 CogView-3-Flash', value: 'cogview-3-flash' },
  { label: '通义万相 V1', value: 'wanx-v1' }
]

const searchText = ref('')
const selectedCategory = ref('all')
const showFormModal = ref(false)
const showApplyModal = ref(false)
const editing = ref<WorkflowTemplate | null>(null)
const applying = ref<WorkflowTemplate | null>(null)
const variableValues = ref<Record<string, string>>({})
const form = ref({ name: '', description: '', category: 'social', promptTemplate: '', negativePrompt: '', size: '1024x1024', model: 'doubao-seedream-4-5-251128', tags: [] as string[] })

const filtered = computed(() => {
  let templates = workflowStore.templates
  if (selectedCategory.value !== 'all') templates = templates.filter(t => t.category === selectedCategory.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    templates = templates.filter(t => (t.name || '').toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q))
  }
  return templates
})

const extractedVariables = computed(() => {
  if (!applying.value) return []
  return (applying.value.config.promptTemplate.match(/\{([^}]+)\}/g) || []).map(m => m.slice(1, -1))
})

const previewPrompt = computed(() => {
  if (!applying.value) return ''
  let prompt = applying.value.config.promptTemplate
  for (const [key, value] of Object.entries(variableValues.value)) prompt = prompt.replace(`{${key}}`, value)
  return prompt
})

function getCategoryLabel(category: string): string {
  return categories.find(c => c.value === category)?.label || category
}

function openCreate() {
  editing.value = null
  form.value = { name: '', description: '', category: 'social', promptTemplate: '', negativePrompt: '', size: '1024x1024', model: 'doubao-seedream-4-5-251128', tags: [] }
  showFormModal.value = true
}

function edit(template: WorkflowTemplate) {
  editing.value = template
  form.value = { name: template.name, description: template.description, category: template.category, promptTemplate: template.config.promptTemplate, negativePrompt: template.config.negativePrompt || '', size: template.config.size, model: template.config.model, tags: template.tags }
  showFormModal.value = true
}

function remove(template: WorkflowTemplate) {
  workflowStore.remove(template.id!)
  message.success('模板已删除')
}

function save() {
  if (!form.value.name || !form.value.promptTemplate) { message.warning('请填写模板名称和提示词模板'); return }
  const data = { name: form.value.name, description: form.value.description, category: form.value.category, config: { model: form.value.model, size: form.value.size, promptTemplate: form.value.promptTemplate, negativePrompt: form.value.negativePrompt }, tags: form.value.tags }
  if (editing.value) { workflowStore.update(editing.value.id!, data); message.success('模板已更新') }
  else { workflowStore.add(data); message.success('模板已创建') }
  showFormModal.value = false
  editing.value = null
}

function apply(template: WorkflowTemplate) {
  applying.value = template
  variableValues.value = {}
  showApplyModal.value = true
}

function confirmApply() {
  if (!applying.value) return
  let prompt = applying.value.config.promptTemplate
  for (const [key, value] of Object.entries(variableValues.value)) prompt = prompt.replace(`{${key}}`, value)
  generatorStore.prompt = prompt
  if (applying.value.config.negativePrompt) generatorStore.negativePrompt = applying.value.config.negativePrompt
  message.success('模板已应用')
  showApplyModal.value = false
  emit('select', generatorStore.prompt)
}

onMounted(() => workflowStore.load())
</script>

<style scoped>
.variable-inputs { display: flex; flex-direction: column; gap: 8px; width: 100%; }
.variable-item { display: flex; align-items: center; gap: 8px; }
.variable-label { min-width: 60px; font-weight: 500; }
.apply-preview { padding: 8px 0; }
.preview-name { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.preview-desc { color: var(--gray-500); font-size: 14px; }
.mb-3 { margin-bottom: 12px; }
</style>
