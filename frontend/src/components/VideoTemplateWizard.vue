<template>
  <div class="video-template-wizard">
    <n-space vertical size="medium">
      <div class="category-section">
        <div class="section-label">选择场景</div>
        <div class="category-buttons">
          <n-button
            v-for="cat in categories"
            :key="cat.id"
            :type="selectedCategory === cat.id ? 'primary' : 'default'"
            size="small"
            @click="selectedCategory = cat.id"
          >
            {{ cat.icon }} {{ cat.name }}
          </n-button>
        </div>
      </div>

      <div class="template-section">
        <div class="section-label">选择模板</div>
        <div class="template-grid">
          <div
            v-for="template in filteredTemplates"
            :key="template.id"
            class="template-card"
            :class="{ 'template-card--selected': selectedTemplate?.id === template.id }"
            @click="selectTemplate(template)"
          >
            <div class="template-card__header">
              <span class="template-icon">{{ categoryIcon(template.taskType) }}</span>
              <span class="template-title">{{ template.title }}</span>
            </div>
            <p class="template-desc">{{ template.description }}</p>
            <div v-if="template.tags?.length" class="template-tags">
              <n-tag v-for="tag in template.tags.slice(0, 3)" :key="tag" size="tiny" type="info">
                {{ tag }}
              </n-tag>
            </div>
          </div>
        </div>
        <n-empty v-if="filteredTemplates.length === 0" description="暂无视频模板" size="small" class="mt-2" />
      </div>

      <div v-if="selectedTemplate" class="selected-detail">
        <n-collapse :default-expanded-names="['settings', 'fields']">
          <n-collapse-item title="📸 镜头方案" name="settings">
            <div v-if="selectedTemplate.shotSettings" class="shot-settings-grid">
              <div class="setting-item">
                <span class="setting-label">运镜方式</span>
                <span class="setting-value">{{ getMovementName(selectedTemplate.shotSettings.movement) }}</span>
              </div>
              <div class="setting-item">
                <span class="setting-label">景别</span>
                <span class="setting-value">{{ getShotTypeName(selectedTemplate.shotSettings.shotType) }}</span>
              </div>
              <div class="setting-item">
                <span class="setting-label">拍摄角度</span>
                <span class="setting-value">{{ getAngleName(selectedTemplate.shotSettings.angle) }}</span>
              </div>
              <div class="setting-item">
                <span class="setting-label">运镜速度</span>
                <span class="setting-value">{{ getSpeedName(selectedTemplate.shotSettings.speed) }}</span>
              </div>
              <div class="setting-item">
                <span class="setting-label">情绪基调</span>
                <span class="setting-value">{{ getEmotionName(selectedTemplate.shotSettings.emotion) }}</span>
              </div>
              <div v-if="selectedTemplate.recommendedDuration" class="setting-item">
                <span class="setting-label">推荐时长</span>
                <span class="setting-value">{{ selectedTemplate.recommendedDuration }}秒</span>
              </div>
            </div>
            <n-alert v-else type="info" :show-icon="false" size="small">
              该模板暂无预设镜头方案
            </n-alert>
          </n-collapse-item>

          <n-collapse-item v-if="templateFields.length > 0" title="✏️ 填写参数" name="fields">
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

          <n-collapse-item title="📝 生成的提示词" name="prompt">
            <n-input
              :value="generatedPrompt"
              type="textarea"
              readonly
              :rows="4"
            />
          </n-collapse-item>

          <n-collapse-item v-if="selectedTemplate.tips?.length" title="💡 使用技巧" name="tips">
            <ul class="tips-list">
              <li v-for="(tip, idx) in selectedTemplate.tips" :key="idx">{{ tip }}</li>
            </ul>
          </n-collapse-item>
        </n-collapse>

        <div class="action-buttons">
          <n-button type="primary" size="small" block @click="handleApplyAll">
            🎬 一键应用全部参数
          </n-button>
          <n-space justify="center">
            <n-button size="tiny" quaternary @click="handleCopyPrompt">
              仅复制提示词
            </n-button>
            <n-button size="tiny" quaternary @click="handleApplyPromptOnly">
              仅应用提示词
            </n-button>
          </n-space>
        </div>
      </div>

      <n-alert v-if="selectedTemplate?.negativePrompt" type="info" :show-icon="false" size="small">
        <template #header>推荐负面词</template>
        {{ selectedTemplate.negativePrompt }}
      </n-alert>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { useDataStore, useVideoStore } from '../stores'
import type { UnifiedTemplate } from '../types/api'
import { extractPlaceholders, fillPromptTemplate } from '../utils/templatePrompt'
import {
  getCameraMovementById,
  getShotTypeById,
  getCameraAngleById,
  getMovementSpeedById,
  emotionTags,
} from '../data/shotLanguage'
import type { CameraMovement, ShotType, CameraAngle, MovementSpeed, EmotionTag } from '../data/shotLanguage'

const emit = defineEmits<{
  apply: [prompt: string]
  applyAll: [template: UnifiedTemplate, filledPrompt: string, fieldValues: Record<string, string>]
}>()

const message = useMessage()
const dataStore = useDataStore()
const videoStore = useVideoStore()

const CATEGORY_META: Record<string, { name: string; icon: string }> = {
  product: { name: '电商产品', icon: '📦' },
  brand: { name: '企业品牌', icon: '🏢' },
  education: { name: '科普教育', icon: '📚' },
  culture: { name: '文化内容', icon: '🎨' },
  social: { name: '社媒内容', icon: '📱' },
  portrait: { name: '人像摄影', icon: '👤' },
  vlog: { name: 'Vlog', icon: '🎥' },
  food: { name: '美食', icon: '🍜' },
  realestate: { name: '房产空间', icon: '🏠' },
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

function getMovementName(id?: string): string {
  if (!id) return '—'
  return getCameraMovementById(id as CameraMovement)?.name || id
}

function getShotTypeName(id?: string): string {
  if (!id) return '—'
  return getShotTypeById(id as ShotType)?.name || id
}

function getAngleName(id?: string): string {
  if (!id) return '—'
  return getCameraAngleById(id as CameraAngle)?.name || id
}

function getSpeedName(id?: string): string {
  if (!id) return '—'
  return getMovementSpeedById(id as MovementSpeed)?.label || id
}

function getEmotionName(id?: string): string {
  if (!id) return '—'
  const found = emotionTags.find(e => e.value === id)
  return found?.label || id
}

function selectTemplate(template: UnifiedTemplate) {
  selectedTemplate.value = template
  const values: Record<string, string> = {}
  for (const field of extractPlaceholders(template.promptTemplate)) {
    values[field] = ''
  }
  fieldValues.value = values
}

function handleApplyAll() {
  if (!selectedTemplate.value) return
  
  const prompt = generatedPrompt.value
  if (!prompt.trim()) {
    message.warning('请先填写模板参数')
    return
  }

  videoStore.prompt = prompt
  
  if (selectedTemplate.value.negativePrompt) {
    videoStore.negativePrompt = selectedTemplate.value.negativePrompt
  }

  const shot = selectedTemplate.value.shotSettings
  if (shot) {
    if (shot.movement) {
      const movement = getCameraMovementById(shot.movement as CameraMovement)
      if (movement) {
        videoStore.applyMovementWithRecommendedSpeed(movement as any)
      }
    }
    if (shot.shotType) {
      videoStore.shotType = shot.shotType
    }
    if (shot.angle) {
      videoStore.cameraAngle = shot.angle
    }
    if (shot.speed) {
      videoStore.movementSpeed = shot.speed
    }
    if (shot.emotion) {
      videoStore.emotionTag = shot.emotion as EmotionTag
    }
  }

  if (selectedTemplate.value.recommendedDuration) {
    videoStore.duration = selectedTemplate.value.recommendedDuration
  }

  emit('applyAll', selectedTemplate.value, prompt, fieldValues.value)
  message.success('已应用全部参数')
}

function handleApplyPromptOnly() {
  if (generatedPrompt.value) {
    emit('apply', generatedPrompt.value)
    message.success('提示词已应用')
  }
}

async function handleCopyPrompt() {
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

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.category-section {
  margin-bottom: 4px;
}

.category-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.template-section {
  margin-bottom: 4px;
}

.template-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-card {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: #18a058;
  background: #f0fff4;
}

.template-card--selected {
  border: 2px solid #18a058;
  background: #f0fff4;
}

.template-card__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.template-icon {
  font-size: 16px;
}

.template-title {
  font-weight: 600;
  font-size: 13px;
  color: #333;
}

.template-desc {
  font-size: 12px;
  color: #666;
  margin: 0 0 6px;
  line-height: 1.5;
}

.template-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.selected-detail {
  margin-top: 8px;
}

.shot-settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.setting-item {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 8px 10px;
}

.setting-label {
  font-size: 11px;
  color: #999;
  display: block;
  margin-bottom: 2px;
}

.setting-value {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.tips-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #555;
  line-height: 1.8;
}

.action-buttons {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mt-2 {
  margin-top: 8px;
}
</style>
