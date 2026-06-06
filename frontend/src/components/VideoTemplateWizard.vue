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
              @click="selectedTemplate = template"
            >
              <template #header>
                <n-space align="center">
                  <span>{{ template.icon }}</span>
                  <span>{{ template.name }}</span>
                </n-space>
              </template>
              <n-text depth="3">{{ template.description }}</n-text>
            </n-card>
          </n-gi>
        </n-grid>
      </n-form-item>

      <n-collapse v-if="selectedTemplate">
        <n-collapse-item title="填写模板参数" name="fields">
          <n-form label-placement="left" label-width="80">
            <n-form-item
              v-for="field in selectedTemplate.fields"
              :key="field.key"
              :label="field.label"
              :required="field.required"
            >
              <n-input
                v-if="field.type === 'text'"
                v-model:value="fieldValues[field.key]"
                :placeholder="field.placeholder"
              />
              <n-input
                v-else-if="field.type === 'textarea'"
                v-model:value="fieldValues[field.key]"
                type="textarea"
                :placeholder="field.placeholder"
                :rows="2"
              />
              <n-select
                v-else-if="field.type === 'select'"
                v-model:value="fieldValues[field.key]"
                :options="field.options"
                :placeholder="field.placeholder"
              />
              <n-select
                v-else-if="field.type === 'multiselect'"
                v-model:value="fieldValues[field.key]"
                :options="field.options"
                :placeholder="field.placeholder"
                multiple
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

      <n-card v-if="selectedTemplate" size="small" title="推荐镜头组合">
        <n-steps vertical :current="-1">
          <n-step
            v-for="(shot, index) in selectedTemplate.recommendedShots"
            :key="index"
            :title="getShotDescription(shot)"
            :description="`${shot.duration}秒`"
          />
        </n-steps>
      </n-card>

      <n-alert v-if="selectedTemplate" type="info" :show-icon="false">
        <template #header>小贴士</template>
        <ul class="tips-list">
          <li v-for="(tip, index) in selectedTemplate.tips" :key="index">{{ tip }}</li>
        </ul>
      </n-alert>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import {
  videoTemplateCategories,
  getVideoTemplatesByCategory,
  generatePromptFromTemplate
} from '../data/videoTemplates'
import { getShotTypeById, getCameraMovementById } from '../data/shotLanguage'
import type { VideoTemplate } from '../data/videoTemplates'

const emit = defineEmits<{
  apply: [prompt: string]
}>()

const message = useMessage()

const selectedCategory = ref<string>('product')
const selectedTemplate = ref<VideoTemplate | null>(null)
const fieldValues = ref<Record<string, string | string[]>>({})

const categories = computed(() => videoTemplateCategories)

const filteredTemplates = computed(() =>
  getVideoTemplatesByCategory(selectedCategory.value as any)
)

const generatedPrompt = computed(() => {
  if (!selectedTemplate.value) return ''
  return generatePromptFromTemplate(selectedTemplate.value, fieldValues.value)
})

watch(selectedTemplate, (template) => {
  if (template) {
    const values: Record<string, string | string[]> = {}
    for (const field of template.fields) {
      if (field.defaultValue) {
        values[field.key] = field.defaultValue
      } else if (field.type === 'multiselect') {
        values[field.key] = []
      } else {
        values[field.key] = ''
      }
    }
    fieldValues.value = values
  }
})

function getShotDescription(shot: any): string {
  const shotType = getShotTypeById(shot.type)
  const movement = getCameraMovementById(shot.movement)
  return `${shotType?.name || ''} ${movement?.name || ''} - ${shot.description}`
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

.tips-list {
  margin: 0;
  padding-left: 16px;
}

.tips-list li {
  margin: 4px 0;
}
</style>
