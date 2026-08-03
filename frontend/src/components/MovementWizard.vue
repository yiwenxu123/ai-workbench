<template>
  <div class="movement-wizard">
    <div class="wizard-step" v-if="step === 1">
      <div class="step-title">
        <span class="step-num">1</span>
        <span>你想传达什么情绪？</span>
      </div>
      <div class="emotion-grid">
        <div
          v-for="em in emotionTags"
          :key="em.value"
          class="emotion-card"
          :class="{ selected: selectedEmotion === em.value }"
          @click="selectEmotion(em.value)"
        >
          <component :is="getIcon(em.icon)" class="emotion-icon" :size="20" />
          <span class="emotion-label">{{ em.label }}</span>
        </div>
      </div>
    </div>

    <div class="wizard-step" v-if="step === 2">
      <div class="step-title">
        <span class="step-num">2</span>
        <span>推荐的运镜方案</span>
        <n-button text size="tiny" @click="step = 1">重新选择</n-button>
      </div>

      <div class="recommend-list">
        <div
          v-for="rec in recommendedMovements"
          :key="rec.id"
          class="recommend-card"
          :class="{ selected: selectedMovement === rec.id }"
          @click="selectMovement(rec.id)"
        >
          <div class="rec-header">
            <span class="rec-name">{{ rec.name }}</span>
            <n-tag size="small" type="info">
              {{ getCategoryMeta(rec.category)?.name }}
            </n-tag>
          </div>
          <div class="rec-desc">{{ rec.useCase }}</div>
          <div class="rec-tips">
            <span v-for="(tip, i) in rec.tips.slice(0, 2)" :key="i" class="rec-tip">
              {{ tip }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="recommendedMovements.length === 0" class="empty-recommend">
        <n-empty description="暂无推荐运镜" size="small" />
      </div>
    </div>

    <div class="wizard-actions" v-if="selectedMovement">
      <n-button type="primary" block size="small" @click="handleApply">
        应用此运镜方案
      </n-button>
    </div>

    <div class="wizard-divider">
      <span class="divider-text">或者直接选择场景</span>
    </div>

    <div class="quick-scenarios">
      <n-space wrap>
        <n-button
          v-for="scene in quickScenarios"
          :key="scene.id"
          size="tiny"
          :type="selectedScenario === scene.id ? 'primary' : 'default'"
          @click="selectScenario(scene.id)"
        >
          {{ scene.name }}
        </n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  emotionTags,
  getMovementsByEmotion,
  getCategoryMeta,
} from '../data/shotLanguage'
import type { EmotionTag, CameraMovement } from '../data/shotLanguage'
import {
  Heart,
  AlertTriangle,
  Zap,
  Mountain,
  HelpCircle,
  Eye,
  Film,
  Activity,
  Sparkles,
  Waves,
} from 'lucide-vue-next'

const emit = defineEmits<{
  (e: 'apply', movement: CameraMovement): void
  (e: 'apply-combo', comboId: string): void
}>()

const step = ref(1)
const selectedEmotion = ref<EmotionTag | null>(null)
const selectedMovement = ref<CameraMovement | null>(null)
const selectedScenario = ref<string | null>(null)

const iconMap: Record<string, any> = {
  Heart,
  AlertTriangle,
  Zap,
  Mountain,
  HelpCircle,
  Eye,
  Film,
  Activity,
  Sparkles,
  Waves,
}

function getIcon(name: string) {
  return iconMap[name] || Sparkles
}

const recommendedMovements = computed(() => {
  if (!selectedEmotion.value) return []
  return getMovementsByEmotion(selectedEmotion.value).slice(0, 6)
})

const quickScenarios = [
  { id: 'product_showcase', name: '产品展示' },
  { id: 'brand_story', name: '品牌故事' },
  { id: 'emotional_dramatic', name: '情感戏剧' },
  { id: 'action_dynamic', name: '动态动作' },
  { id: 'documentary', name: '纪录片风' },
]

function selectEmotion(em: EmotionTag) {
  selectedEmotion.value = em
  selectedMovement.value = null
  step.value = 2
}

function selectMovement(id: CameraMovement) {
  selectedMovement.value = selectedMovement.value === id ? null : id
}

function selectScenario(id: string) {
  selectedScenario.value = id
  emit('apply-combo', id)
}

function handleApply() {
  if (selectedMovement.value) {
    emit('apply', selectedMovement.value)
  }
}
</script>

<style scoped>
.movement-wizard {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wizard-step {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: var(--brand-500);
  color: white;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
}

.emotion-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.emotion-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background: var(--bg-card);
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.emotion-card:hover {
  border-color: var(--brand-300);
  background: var(--brand-50);
  transform: translateY(-1px);
}

.emotion-card.selected {
  border-color: var(--brand-500);
  background: var(--brand-50);
  box-shadow: 0 0 0 2px var(--brand-200);
}

.emotion-icon {
  color: var(--brand-500);
}

.emotion-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.recommend-card {
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.recommend-card:hover {
  border-color: var(--brand-300);
  background: var(--brand-50);
}

.recommend-card.selected {
  border-color: var(--brand-500);
  background: var(--brand-50);
  box-shadow: 0 0 0 2px var(--brand-200);
}

.rec-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.rec-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.rec-desc {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-bottom: 6px;
}

.rec-tips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.rec-tip {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--bg-subtle);
  color: var(--text-tertiary);
  border-radius: 4px;
}

.wizard-actions {
  margin-top: 4px;
}

.wizard-divider {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0;
}

.wizard-divider::before,
.wizard-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-light);
}

.divider-text {
  font-size: 11px;
  color: var(--text-tertiary);
}

.quick-scenarios {
  display: flex;
  justify-content: center;
}

.empty-recommend {
  padding: 16px 0;
}
</style>
