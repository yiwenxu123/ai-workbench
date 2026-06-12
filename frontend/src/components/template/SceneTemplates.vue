<template>
  <div>
    <n-grid :cols="3" :x-gap="8" :y-gap="8">
      <n-gi v-for="cat in sceneCategories" :key="cat.id">
        <n-card
          size="small"
          hoverable
          class="category-card"
          :class="{ 'category-selected': selectedCategory === cat.id }"
          @click="selectedCategory = cat.id"
        >
          <div class="category-content">
            <n-icon :component="cat.icon" class="category-icon" />
            <span class="category-name">{{ cat.name }}</span>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-collapse v-if="selectedCategory" class="mt-3">
      <n-collapse-item title="选择模板" name="templates">
        <n-list bordered>
          <n-list-item v-for="template in filteredTemplates" :key="template.id">
            <n-thing :title="template.name" :description="template.description">
              <template #avatar>
                <n-tag type="info" size="small">{{ template.type === 'image' ? '图' : '视频' }}</n-tag>
              </template>
              <template #action>
                <n-button size="small" type="primary" @click="handleApply(template)">使用</n-button>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-collapse-item>
    </n-collapse>

    <n-modal v-model:show="showFieldModal" preset="card" :title="currentFieldTemplate?.name" style="width: 500px">
      <n-alert type="info" class="mb-3" :show-icon="false">{{ currentFieldTemplate?.description }}</n-alert>
      <n-form label-placement="left" label-width="80">
        <n-form-item v-for="field in currentFieldTemplate?.fields" :key="field.key" :label="field.label" :required="field.required">
          <n-select v-if="field.options" v-model:value="fieldValues[field.key]" :options="field.options.map((o: string) => ({ label: o, value: o }))" :placeholder="field.placeholder" clearable />
          <n-input v-else v-model:value="fieldValues[field.key]" :placeholder="field.placeholder" />
        </n-form-item>
      </n-form>
      <n-card size="small" title="生成预览" class="mt-3">
        <n-text>{{ generatedPrompt }}</n-text>
      </n-card>
      <n-card size="small" title="小贴士" class="mt-3" v-if="currentFieldTemplate?.tips?.length">
        <ul class="tips-list"><li v-for="(tip, index) in currentFieldTemplate.tips" :key="index">{{ tip }}</li></ul>
      </n-card>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showFieldModal = false">取消</n-button>
          <n-button type="primary" @click="applyFieldTemplate">应用到提示词</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore, useDataStore } from '../../stores'
import { Package, Building2, BookOpen, Palette, Smartphone, User } from 'lucide-vue-next'

const emit = defineEmits<{ select: [prompt: string] }>()
const message = useMessage()
const generatorStore = useGeneratorStore()
const dataStore = useDataStore()

const sceneCategories = [
  { id: 'product', name: '产品展示', icon: Package },
  { id: 'brand', name: '企业品牌', icon: Building2 },
  { id: 'education', name: '科普教育', icon: BookOpen },
  { id: 'culture', name: '文化内容', icon: Palette },
  { id: 'social', name: '社媒内容', icon: Smartphone },
  { id: 'portrait', name: '人物肖像', icon: User }
]

const selectedCategory = ref<string | null>(null)
const showFieldModal = ref(false)
const currentFieldTemplate = ref<any>(null)
const fieldValues = ref<Record<string, string>>({})

const filteredTemplates = computed(() => {
  if (!selectedCategory.value) return []
  const image = (dataStore.workTemplates || [])
    .filter((t: any) => t.category === selectedCategory.value)
    .map((t: any) => ({ ...t, type: 'image' as const }))
  const video = (dataStore.videoTemplates || [])
    .filter((t: any) => t.category === selectedCategory.value)
    .map((t: any) => ({ ...t, type: 'video' as const }))
  return [...image, ...video]
})

const generatedPrompt = computed(() => {
  if (!currentFieldTemplate.value) return ''
  let prompt = currentFieldTemplate.value.prompt
  for (const [key, value] of Object.entries(fieldValues.value)) {
    prompt = prompt.replace(`{${key}}`, value)
  }
  return prompt
})

function handleApply(template: any) {
  if (template.fields?.length > 0) {
    currentFieldTemplate.value = template
    fieldValues.value = {}
    showFieldModal.value = true
    return
  }
  const prompt = template.content || template.prompt || template.promptTemplate || ''
  if (prompt) {
    generatorStore.prompt = prompt
    if (template.negativePrompt) generatorStore.negativePrompt = template.negativePrompt
    message.success('模板已应用')
    emit('select', generatorStore.prompt)
  }
}

function applyFieldTemplate() {
  if (!generatedPrompt.value || !currentFieldTemplate.value) return
  const missing = (currentFieldTemplate.value.fields?.filter((f: any) => f.required) || [])
    .filter((f: any) => !fieldValues.value[f.key])
  if (missing.length > 0) {
    message.warning(`请填写必填项：${missing.map((f: any) => f.label).join('、')}`)
    return
  }
  generatorStore.prompt = generatedPrompt.value
  if (currentFieldTemplate.value.negativePrompt) generatorStore.negativePrompt = currentFieldTemplate.value.negativePrompt
  message.success('模板已应用')
  showFieldModal.value = false
  emit('select', generatorStore.prompt)
}
</script>

<style scoped>
.category-card {
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.16,1,0.3,1),
              box-shadow 0.2s cubic-bezier(0.16,1,0.3,1),
              border-color 0.15s ease;
}
.category-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--brand-400);
}
.category-selected {
  border: 2px solid var(--brand-500) !important;
  box-shadow: 0 0 0 3px rgba(79, 125, 243, 0.12) !important;
}
.category-content { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.category-icon { font-size: 26px; transition: transform 0.2s ease; }
.category-card:hover .category-icon { transform: scale(1.15); }
.category-name { font-size: 12px; font-weight: 500; color: var(--gray-600); }
.tips-list { margin: 0; padding-left: 16px; }
.tips-list li { margin: 4px 0; color: var(--gray-500); font-size: 13px; }
.mb-3 { margin-bottom: 12px; }
.mt-3 { margin-top: 12px; }
</style>
