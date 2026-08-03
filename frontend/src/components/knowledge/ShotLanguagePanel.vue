<template>
  <div class="shot-language-panel">
    <div class="panel-header">
      <n-input
        v-model:value="searchText"
        placeholder="搜索运镜、景别、角度..."
        clearable
        size="small"
        class="search-input"
      >
        <template #prefix>
          <n-icon :component="Search" />
        </template>
      </n-input>
    </div>

    <n-tabs v-model:value="activeCategory" type="line" size="small" class="category-tabs">
      <n-tab-pane
        v-for="cat in movementCategories"
        :key="cat.id"
        :name="cat.id"
      >
        <template #tab>
          <span class="tab-label">
            <span class="tab-icon">{{ cat.icon }}</span>
            <span>{{ cat.shortName || cat.name }}</span>
          </span>
        </template>
      </n-tab-pane>
      <n-tab-pane name="basics" tab="基础">
        <template #tab>
          <span class="tab-label">
            <span class="tab-icon">📐</span>
            <span>基础</span>
          </span>
        </template>
      </n-tab-pane>
      <n-tab-pane name="combos" tab="组合">
        <template #tab>
          <span class="tab-label">
            <span class="tab-icon">🎬</span>
            <span>组合</span>
          </span>
        </template>
      </n-tab-pane>
      <n-tab-pane name="quiz" tab="测验">
        <template #tab>
          <span class="tab-label">
            <span class="tab-icon">🧠</span>
            <span>测验</span>
          </span>
        </template>
      </n-tab-pane>
    </n-tabs>

    <div class="panel-content">
      <div v-if="searchText" class="search-results">
        <div v-if="filteredMovements.length === 0" class="empty-state">
          <n-empty description="未找到匹配的镜头语言" size="small" />
        </div>
        <div
          v-for="movement in filteredMovements"
          :key="movement.id"
          class="movement-card"
        >
          <div class="card-header">
            <div class="card-title">
              <span class="movement-name">{{ movement.name }}</span>
              <n-tag size="tiny" type="info">{{ movement.nameEn }}</n-tag>
              <n-tag v-if="movement.isHighFrequency" size="tiny" type="success">常用</n-tag>
            </div>
            <n-tag size="tiny" :type="getCategoryTagType(movement.category)">
              {{ getCategoryName(movement.category) }}
            </n-tag>
          </div>
          <p class="card-desc">{{ movement.useCase }}</p>
          
          <div class="card-section">
            <span class="section-label">关键词</span>
            <div class="keyword-list">
              <n-tag
                v-for="kw in movement.keywords.slice(0, 3)"
                :key="kw"
                size="small"
                class="keyword-tag"
                @click="handleInsertKeyword(kw)"
              >
                {{ kw }}
              </n-tag>
            </div>
          </div>

          <div class="card-footer">
            <n-button size="tiny" quaternary @click="showDetail(movement)">
              查看详情
            </n-button>
            <n-button size="tiny" type="primary" @click="goToVideoPanel(movement)">
              去视频生成使用
            </n-button>
          </div>
        </div>
      </div>

      <template v-else-if="activeCategory === 'basics'">
        <div class="basics-section">
          <div class="section-header">
            <n-icon :component="Ruler" size="16" />
            <span>景别</span>
          </div>
          <n-grid :cols="2" :x-gap="8" :y-gap="8">
            <n-gi v-for="shot in shotTypes" :key="shot.id">
              <div class="basic-card" @click="handleInsertKeyword(shot.keywords[0] ?? shot.name)">
                <div class="basic-title">{{ shot.name }}</div>
                <div class="basic-en">{{ shot.nameEn }}</div>
              </div>
            </n-gi>
          </n-grid>
        </div>

        <div class="basics-section">
          <div class="section-header">
            <n-icon :component="Eye" size="16" />
            <span>拍摄角度</span>
          </div>
          <n-grid :cols="2" :x-gap="8" :y-gap="8">
            <n-gi v-for="angle in cameraAngles" :key="angle.id">
              <div class="basic-card" @click="handleInsertKeyword(angle.keywords[0] ?? angle.name)">
                <div class="basic-title">{{ angle.name }}</div>
                <div class="basic-en">{{ angle.nameEn }}</div>
              </div>
            </n-gi>
          </n-grid>
        </div>

        <div class="basics-section">
          <div class="section-header">
            <n-icon :component="Gauge" size="16" />
            <span>运镜速度</span>
          </div>
          <n-grid :cols="2" :x-gap="8" :y-gap="8">
            <n-gi v-for="speed in movementSpeeds" :key="speed.id">
              <div class="basic-card" @click="handleInsertKeyword(speed.keyword)">
                <div class="basic-title">{{ speed.name }}</div>
                <div class="basic-en">{{ speed.nameEn }}</div>
              </div>
            </n-gi>
          </n-grid>
        </div>
      </template>

      <template v-else-if="activeCategory === 'combos'">
        <div class="combo-list">
          <div
            v-for="combo in shotCombinations"
            :key="combo.id"
            class="combo-card"
          >
            <div class="combo-header">
              <div class="combo-title">
                <span class="combo-icon">{{ combo.icon }}</span>
                <span>{{ combo.name }}</span>
              </div>
              <n-tag size="tiny" type="info">{{ combo.shots.length }}镜</n-tag>
            </div>
            <p class="combo-desc">{{ combo.description }}</p>
            
            <div class="combo-shots">
              <n-tag
                v-for="(shot, idx) in combo.shots"
                :key="`${shot.movement}-${idx}`"
                size="small"
                :type="idx === 0 ? 'primary' : 'default'"
              >
                {{ idx + 1 }}. {{ getMovementName(shot.movement) }} · {{ getShotTypeName(shot.type) }}
              </n-tag>
            </div>

            <div class="combo-footer">
              <n-button size="tiny" quaternary @click="showComboDetail(combo)">
                查看完整提示词
              </n-button>
              <n-button size="tiny" type="primary" @click="applyCombo(combo)">
                一键应用
              </n-button>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="activeCategory === 'quiz'">
        <ShotLanguageQuiz
          @go-to-movement="handleQuizGoToMovement"
        />
      </template>

      <template v-else>
        <div class="movement-grid">
          <div
            v-for="movement in categoryMovements"
            :key="movement.id"
            class="movement-card"
          >
            <div class="card-header">
              <div class="card-title">
                <span class="movement-name">{{ movement.name }}</span>
                <n-tag size="tiny" type="info">{{ movement.nameEn }}</n-tag>
              </div>
              <n-tag v-if="movement.isHighFrequency" size="tiny" type="success">常用</n-tag>
            </div>
            <p class="card-desc">{{ movement.useCase }}</p>
            
            <div class="card-section">
              <span class="section-label">关键词</span>
              <div class="keyword-list">
                <n-tag
                  v-for="kw in movement.keywords.slice(0, 3)"
                  :key="kw"
                  size="small"
                  class="keyword-tag"
                  @click="handleInsertKeyword(kw)"
                >
                  {{ kw }}
                </n-tag>
              </div>
            </div>

            <div class="card-footer">
              <n-button size="tiny" quaternary @click="showDetail(movement)">
                详情
              </n-button>
              <n-button size="tiny" type="primary" @click="goToVideoPanel(movement)">
                去使用
              </n-button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <n-modal v-model:show="showDetailModal" preset="card" :title="currentMovement?.name || '详情'" style="width: 560px">
      <template v-if="currentMovement">
        <div class="detail-modal">
          <div class="detail-tags">
            <n-tag type="info">{{ currentMovement.nameEn }}</n-tag>
            <n-tag :type="getCategoryTagType(currentMovement.category)">
              {{ getCategoryName(currentMovement.category) }}
            </n-tag>
            <n-tag v-if="currentMovement.isHighFrequency" type="success">高频使用</n-tag>
            <n-tag type="warning">推荐速度：{{ getSpeedName(currentMovement.recommendedSpeed) }}</n-tag>
          </div>

          <n-divider style="margin: 12px 0" />

          <div class="detail-section">
            <div class="detail-label">📝 用途说明</div>
            <p class="detail-text">{{ currentMovement.useCase }}</p>
          </div>

          <div class="detail-section">
            <div class="detail-label">💡 使用技巧</div>
            <ul class="detail-list">
              <li v-for="(tip, idx) in currentMovement.tips" :key="idx">{{ tip }}</li>
            </ul>
          </div>

          <div class="detail-section">
            <div class="detail-label">🎯 适合情绪</div>
            <div class="emotion-tags">
              <n-tag
                v-for="emotion in currentMovement.suitableEmotions"
                :key="emotion"
                size="small"
                type="info"
              >
                {{ getEmotionName(emotion) }}
              </n-tag>
            </div>
          </div>

          <div class="detail-section">
            <div class="detail-label">📌 示例提示词（点击复制）</div>
            <div class="example-list">
              <div
                v-for="(example, idx) in currentMovement.examples"
                :key="idx"
                class="example-item"
                @click="handleInsertKeyword(example)"
              >
                {{ example }}
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showDetailModal = false">关闭</n-button>
          <n-button type="primary" @click="handleGoToVideoFromDetail">
            去视频生成面板使用
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showComboModal" preset="card" :title="currentCombo?.name || '组合详情'" style="width: 560px">
      <template v-if="currentCombo">
        <div class="detail-modal">
          <div class="detail-tags">
            <n-tag type="info">{{ currentCombo.shots.length }} 个镜头</n-tag>
            <n-tag type="success">常用组合</n-tag>
          </div>

          <n-divider style="margin: 12px 0" />

          <div class="detail-section">
            <div class="detail-label">📝 适用场景</div>
            <p class="detail-text">{{ currentCombo.description }}</p>
          </div>

          <div class="detail-section">
            <div class="detail-label">🎬 镜头序列</div>
            <n-steps :vertical="true" size="small">
              <n-step
                v-for="(shot, idx) in currentCombo.shots"
                :key="`${shot.movement}-${idx}`"
                :title="`${getMovementName(shot.movement)} · ${getShotTypeName(shot.type)}`"
                :description="`${getMovementUseCase(shot.movement)}（${shot.duration}秒）`"
              />
            </n-steps>
          </div>

          <div class="detail-section">
            <div class="detail-label">📌 完整提示词</div>
            <n-input
              :value="currentCombo.prompt"
              type="textarea"
              readonly
              :rows="3"
            />
          </div>
        </div>
      </template>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showComboModal = false">关闭</n-button>
          <n-button type="primary" @click="applyCurrentCombo">
            应用到提示词
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { Search, Ruler, Eye, Gauge } from 'lucide-vue-next'
import {
  cameraMovements,
  shotTypes,
  cameraAngles,
  movementSpeeds,
  shotCombinations,
  movementCategories,
  getCategoryMeta,
  getCameraMovementById,
} from '../../data/shotLanguage'
import type { CameraMovement, CameraMovementCategory, CameraMovementOption, EmotionTag, ShotCombination, ShotType } from '../../data/shotLanguage'
import ShotLanguageQuiz from './ShotLanguageQuiz.vue'

const emit = defineEmits<{
  insert: [keyword: string]
  gotoVideo: [movement?: CameraMovementOption]
}>()

const message = useMessage()

const searchText = ref('')
const activeCategory = ref<CameraMovementCategory | 'basics' | 'combos' | 'quiz'>('basic_direction')
const showDetailModal = ref(false)
const showComboModal = ref(false)
const currentMovement = ref<CameraMovementOption | null>(null)
const currentCombo = ref<ShotCombination | null>(null)

const filteredMovements = computed(() => {
  const q = searchText.value.toLowerCase().trim()
  if (!q) return []
  return cameraMovements.filter(m =>
    m.name.includes(q) ||
    m.nameEn.toLowerCase().includes(q) ||
    m.useCase.includes(q) ||
    m.keywords.some(k => k.toLowerCase().includes(q)) ||
    m.tips.some(t => t.includes(q))
  )
})

const categoryMovements = computed(() => {
  if (activeCategory.value === 'basics' || activeCategory.value === 'combos') return []
  return cameraMovements.filter(m => m.category === activeCategory.value)
})

function getCategoryName(cat: CameraMovementCategory): string {
  return getCategoryMeta(cat)?.name || cat
}

function getCategoryTagType(cat: CameraMovementCategory): 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error' {
  const typeMap: Record<CameraMovementCategory, any> = {
    basic_direction: 'primary',
    spatial_movement: 'info',
    character_follow: 'success',
    crane_orbit: 'warning',
    emotion_intensify: 'error',
    transition: 'default',
  }
  return typeMap[cat] || 'default'
}

function getSpeedName(speedId: string): string {
  return movementSpeeds.find(s => s.id === speedId)?.name || speedId
}

function getEmotionName(emotion: EmotionTag): string {
  const emotionMap: Record<EmotionTag, string> = {
    calm: '平静',
    tense: '紧张',
    warm: '温馨',
    shocking: '震撼',
    grand: '宏大',
    mysterious: '神秘',
    immersive: '沉浸',
    documentary: '纪实',
    dynamic: '动感',
    delicate: '细腻',
  }
  return emotionMap[emotion] || emotion
}

function getMovementName(id: string): string {
  return getCameraMovementById(id as CameraMovement)?.name || id
}

function getMovementUseCase(id: string): string {
  return getCameraMovementById(id as CameraMovement)?.useCase || ''
}

function getShotTypeName(id: ShotType): string {
  return shotTypes.find(s => s.id === id)?.name || id
}

function handleInsertKeyword(keyword: string) {
  emit('insert', keyword)
  message.success(`已插入: ${keyword}`)
}

function showDetail(movement: CameraMovementOption) {
  currentMovement.value = movement
  showDetailModal.value = true
}

function showComboDetail(combo: ShotCombination) {
  currentCombo.value = combo
  showComboModal.value = true
}

function goToVideoPanel(movement: CameraMovementOption) {
  emit('gotoVideo', movement)
  message.info('正在跳转到视频生成面板...')
}

function handleGoToVideoFromDetail() {
  if (currentMovement.value) {
    emit('gotoVideo', currentMovement.value)
    showDetailModal.value = false
  }
}

function applyCombo(combo: ShotCombination) {
  emit('insert', combo.prompt)
  message.success('已应用组合提示词')
}

function applyCurrentCombo() {
  if (currentCombo.value) {
    applyCombo(currentCombo.value)
    showComboModal.value = false
  }
}

function handleQuizGoToMovement(movementId: string) {
  const movement = getCameraMovementById(movementId as CameraMovement)
  if (movement) {
    showDetail(movement)
  }
}
</script>

<style scoped>
.shot-language-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 8px 0;
  flex-shrink: 0;
}

.search-input {
  width: 100%;
}

.category-tabs {
  flex-shrink: 0;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.tab-icon {
  font-size: 14px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.movement-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.movement-card {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
}

.movement-card:hover {
  border-color: #18a058;
  background: #f0fff4;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.movement-name {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.card-desc {
  font-size: 12px;
  color: #666;
  margin: 4px 0 8px;
  line-height: 1.5;
}

.card-section {
  margin-bottom: 8px;
}

.section-label {
  font-size: 11px;
  color: #999;
  display: block;
  margin-bottom: 4px;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keyword-tag {
  cursor: pointer;
}

.keyword-tag:hover {
  opacity: 0.8;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding-top: 4px;
  border-top: 1px solid #f0f0f0;
}

.basics-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 13px;
  color: #333;
  margin-bottom: 8px;
}

.basic-card {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.basic-card:hover {
  border-color: #18a058;
  background: #f0fff4;
}

.basic-title {
  font-weight: 500;
  font-size: 13px;
  color: #333;
  margin-bottom: 2px;
}

.basic-en {
  font-size: 11px;
  color: #999;
}

.combo-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.combo-card {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
}

.combo-card:hover {
  border-color: #18a058;
  background: #f0fff4;
}

.combo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.combo-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.combo-icon {
  font-size: 16px;
}

.combo-desc {
  font-size: 12px;
  color: #666;
  margin: 4px 0 8px;
  line-height: 1.5;
}

.combo-shots {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.combo-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  padding-top: 4px;
  border-top: 1px solid #f0f0f0;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-state {
  padding: 40px 0;
}

.detail-modal {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-section {
  margin-bottom: 14px;
}

.detail-label {
  font-weight: 600;
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
}

.detail-text {
  font-size: 13px;
  color: #555;
  line-height: 1.6;
  margin: 0;
}

.detail-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #555;
  line-height: 1.8;
}

.emotion-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.example-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.example-item {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
  font-family: monospace;
  transition: background 0.2s;
}

.example-item:hover {
  background: #e8ffe8;
  color: #18a058;
}
</style>
