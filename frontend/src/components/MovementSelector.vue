<template>
  <div class="movement-selector">
    <div class="selector-header">
      <n-radio-group v-model:value="viewMode" size="small">
        <n-radio-button value="category">按分类</n-radio-button>
        <n-radio-button value="emotion">按情绪</n-radio-button>
        <n-radio-button value="frequency">高频推荐</n-radio-button>
      </n-radio-group>
    </div>

    <div v-if="viewMode === 'category'" class="category-tabs">
      <div
        v-for="cat in movementCategories"
        :key="cat.id"
        class="category-tab"
        :class="{ active: activeCategory === cat.id }"
        @click="activeCategory = cat.id"
      >
        <span class="tab-name">{{ cat.name }}</span>
        <span class="tab-count">{{ getMovementsByCategory(cat.id).length }}</span>
      </div>
    </div>

    <div v-if="viewMode === 'emotion'" class="emotion-chips">
      <n-tag
        v-for="em in emotionTags"
        :key="em.value"
        class="emotion-chip"
        :type="selectedEmotion === em.value ? 'primary' : 'default'"
        checkable
        :checked="selectedEmotion === em.value"
        @click="toggleEmotion(em.value)"
      >
        {{ em.label }}
      </n-tag>
    </div>

    <div class="movement-grid">
      <div
        v-for="move in filteredMovements"
        :key="move.id"
        class="movement-card"
        :class="{ selected: modelValue === move.id }"
        @click="handleSelect(move.id)"
      >
        <div class="card-header">
          <span class="card-name">{{ move.name }}</span>
          <span class="card-en">{{ move.nameEn.split(' / ')[0] }}</span>
        </div>
        <div class="card-desc">{{ move.useCase }}</div>
        <div v-if="move.isHighFrequency" class="hf-badge">高频</div>
      </div>
      <n-empty v-if="filteredMovements.length === 0" description="暂无匹配的运镜" size="small" />
    </div>

    <div v-if="selectedMovement" class="selected-detail">
      <div class="detail-header">
        <span class="detail-title">{{ selectedMovement.name }}</span>
        <n-tag size="small" type="info">
          {{ getCategoryMeta(selectedMovement.category)?.name }}
        </n-tag>
      </div>

      <div v-if="selectedMovement.tips.length > 0" class="detail-section">
        <div class="detail-label">💡 注意事项</div>
        <ul class="tip-list">
          <li v-for="(tip, i) in selectedMovement.tips" :key="i">{{ tip }}</li>
        </ul>
      </div>

      <div v-if="selectedMovement.examples.length > 0" class="detail-section">
        <div class="detail-label">📝 示例提示词</div>
        <div
          v-for="(ex, i) in selectedMovement.examples"
          :key="i"
          class="example-item"
          @click="$emit('apply-example', ex)"
        >
          {{ ex }}
        </div>
      </div>

      <div class="detail-actions">
        <n-button size="small" @click="handleClear">清除选择</n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  movementCategories,
  getMovementsByCategory,
  getMovementsByEmotion,
  getHighFrequencyMovements,
  getCameraMovementById,
  getCategoryMeta,
  emotionTags,
} from '../data/shotLanguage'
import type { CameraMovement, CameraMovementCategory, EmotionTag } from '../data/shotLanguage'

const props = defineProps<{
  modelValue?: CameraMovement
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: CameraMovement | undefined): void
  (e: 'apply-example', prompt: string): void
}>()

type ViewMode = 'category' | 'emotion' | 'frequency'

const viewMode = ref<ViewMode>('category')
const activeCategory = ref<CameraMovementCategory>('basic_direction')
const selectedEmotion = ref<EmotionTag | null>(null)

const selectedMovement = computed(() => {
  if (!props.modelValue) return null
  return getCameraMovementById(props.modelValue)
})

const filteredMovements = computed(() => {
  if (viewMode.value === 'frequency') {
    return getHighFrequencyMovements()
  }
  if (viewMode.value === 'emotion' && selectedEmotion.value) {
    return getMovementsByEmotion(selectedEmotion.value)
  }
  return getMovementsByCategory(activeCategory.value)
})

function handleSelect(id: CameraMovement) {
  if (props.modelValue === id) {
    emit('update:modelValue', undefined)
  } else {
    emit('update:modelValue', id)
  }
}

function handleClear() {
  emit('update:modelValue', undefined)
}

function toggleEmotion(em: EmotionTag) {
  selectedEmotion.value = selectedEmotion.value === em ? null : em
}
</script>

<style scoped>
.movement-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.selector-header {
  display: flex;
  justify-content: center;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.category-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.category-tab:hover {
  border-color: var(--brand-300);
  background: var(--brand-50);
}

.category-tab.active {
  background: var(--brand-500);
  border-color: var(--brand-500);
  color: white;
}

.tab-name {
  font-weight: 500;
}

.tab-count {
  font-size: 11px;
  opacity: 0.7;
}

.emotion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.emotion-chip {
  cursor: pointer;
}

.movement-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 4px;
}

.movement-card {
  position: relative;
  padding: 10px;
  background: var(--bg-card);
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.movement-card:hover {
  border-color: var(--brand-300);
  background: var(--brand-50);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.movement-card.selected {
  border-color: var(--brand-500);
  background: var(--brand-50);
  box-shadow: 0 0 0 2px var(--brand-200);
}

.card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px;
  margin-bottom: 4px;
}

.card-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.card-en {
  font-size: 10px;
  color: var(--text-tertiary);
  font-style: italic;
}

.card-desc {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hf-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 9px;
  padding: 1px 5px;
  background: var(--warning-100);
  color: var(--warning-600);
  border-radius: 4px;
  font-weight: 600;
}

.selected-detail {
  margin-top: 4px;
  padding: 12px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.detail-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.detail-section {
  margin-bottom: 10px;
}

.detail-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.tip-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.example-item {
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  cursor: pointer;
  margin-bottom: 6px;
  transition: all var(--duration-fast) var(--ease-out);
}

.example-item:hover {
  border-color: var(--brand-300);
  background: var(--brand-50);
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
