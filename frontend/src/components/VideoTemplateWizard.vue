<template>
  <div class="video-template-wizard">
    <n-space vertical>
      <n-form-item label="选择场景">
        <n-space wrap>
          <n-button
            v-for="cat in categories"
            :key="cat.id"
            :type="selectedCategory === cat.id ? 'primary' : 'default'"
            size="small"
            @click="selectedCategory = cat.id"
          >
            {{ cat.icon }} {{ cat.name }}
          </n-button>
        </n-space>
      </n-form-item>

      <n-form-item label="选择模板">
        <n-grid :cols="1" :x-gap="8" :y-gap="8">
          <n-gi v-for="template in filteredTemplates" :key="template.id">
            <n-card
              size="small"
              hoverable
              :class="{ 'template-selected': selectedTemplate?.id === template.id }"
              @click="selectTemplate(template)"
            >
              <template #header>
                <n-space align="center">
                  <span>{{ categoryIcon(template.taskType) }}</span>
                  <span>{{ template.title }}</span>
                </n-space>
              </template>
              <n-text depth="3">{{ template.description }}</n-text>
            </n-card>
          </n-gi>
        </n-grid>
        <n-empty v-if="filteredTemplates.length === 0" description="暂无视频模板" size="small" class="mt-2" />
      </n-form-item>

      <n-collapse v-if="selectedTemplate && templateFields.length > 0">
        <n-collapse-item title="填写模板参数" name="fields">
          <n-form label-placement="left" label-width="80">
            <n-form-item
              v-for="field in templateFields"
              :key="field"
              :label="field"
              required
            >
              <n-input
                v-model:value="fieldValues[field]"
                :placeholder="`填写${field}`"
              />
            </n-form-item>
          </n-form>
        </n-collapse-item>
      </n-collapse>

      <n-card v-if="generatedPrompt" size="small" title="生成的提示词">
        <n-text>{{ generatedPrompt }}</n-text>
        <template #footer>
          <n-space>
            <n-button type="primary" size="small" @click="handleApply">
              应用此提示词
            </n-button>
            <n-button size="small" @click="handleCopy">
              复制
            </n-button>
          </n-space>
        </template>
      </n-card>

      <n-alert v-if="selectedTemplate?.negativePrompt" type="info" :show-icon="false">
        <template #header>推荐负面词</template>
        {{ selectedTemplate.negativePrompt }}
      </n-alert>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { useDataStore } from '../stores'
import type { UnifiedTemplate } from '../types/api'
import { extractPlaceholders, fillPromptTemplate } from '../utils/templatePrompt'

const emit = defineEmits<{
  apply: [prompt: string]
}>()

const message = useMessage()
const dataStore = useDataStore()

const CATEGORY_META: Record<string, { name: string; icon: string }> = {
  product: { name: '电商产品', icon: '📦' },
  brand: { name: '企业品牌', icon: '🏢' },
  education: { name: '科普教育', icon: '📚' },
  culture: { name: '文化内容', icon: '🎨' },
  social: { name: '社媒内容', icon: '📱' },
  festival: { name: '节庆营销', icon: '🎉' },
}

const selectedCategory = ref<string>('product')
const selectedTemplate = ref<UnifiedTemplate | null>(null)
const fieldValues = ref<Record<string, string>>({})

onMounted(() => {
  dataStore.loadAll()
})

const categories = computed(() => {
  const seen = new Map<string, { id: string; name: string; icon: string }>()
  for (const template of dataStore.videoTemplates) {
    const id = template.taskType || 'general'
    if (!seen.has(id)) {
      const meta = CATEGORY_META[id] || { name: id, icon: '🎬' }
      seen.set(id, { id, ...meta })
    }
  }
  return [...seen.values()]
})

watch(categories, (cats) => {
  if (cats.length > 0 && !cats.some(c => c.id === selectedCategory.value)) {
    selectedCategory.value = cats[0].id
  }
}, { immediate: true })

const filteredTemplates = computed(() =>
  dataStore.videoTemplates.filter(t => (t.taskType || 'general') === selectedCategory.value)
)

const templateFields = computed(() => {
  if (!selectedTemplate.value) return []
  return extractPlaceholders(selectedTemplate.value.promptTemplate)
})

const generatedPrompt = computed(() => {
  if (!selectedTemplate.value) return ''
  return fillPromptTemplate(selectedTemplate.value.promptTemplate, fieldValues.value)
})

function categoryIcon(taskType: string): string {
  return CATEGORY_META[taskType]?.icon || '🎬'
}

function selectTemplate(template: UnifiedTemplate) {
  selectedTemplate.value = template
  const values: Record<string, string> = {}
  for (const field of extractPlaceholders(template.promptTemplate)) {
    values[field] = ''
  }
  fieldValues.value = values
}

function handleApply() {
  if (generatedPrompt.value) {
    emit('apply', generatedPrompt.value)
    message.success('提示词已应用')
  }
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(generatedPrompt.value)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败')
  }
}
</script>

<style scoped>
.video-template-wizard {
  width: 100%;
}

.template-selected {
  border: 2px solid #18a058;
}
</style>
