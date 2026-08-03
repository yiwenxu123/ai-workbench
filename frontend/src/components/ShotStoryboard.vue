<template>
  <div class="shot-storyboard">
    <div class="storyboard-header">
      <div class="header-left">
        <span class="header-title">分镜脚本</span>
        <n-tag size="small" type="info">{{ storyboard.length }} 个镜头</n-tag>
        <n-tag size="small" type="success">{{ totalDuration }} 秒</n-tag>
      </div>
      <div class="header-right">
        <n-dropdown :options="templateOptions" @select="handleApplyTemplate">
          <n-button size="small" quaternary>
            <template #icon>
              <component :is="LayoutTemplate" :size="16" />
            </template>
            套用模板
          </n-button>
        </n-dropdown>
        <n-button size="small" quaternary @click="handleExport">
          <template #icon>
            <component :is="Download" :size="16" />
          </template>
          导出脚本
        </n-button>
        <n-button size="small" type="primary" @click="handleAddShot">
          <template #icon>
            <component :is="Plus" :size="16" />
          </template>
          添加镜头
        </n-button>
      </div>
    </div>

    <div v-if="storyboard.length === 0" class="empty-state">
      <component :is="Clapperboard" :size="48" class="empty-icon" />
      <p class="empty-text">还没有分镜</p>
      <p class="empty-hint">点击"添加镜头"开始创建，或选择一个预设模板</p>
    </div>

    <div v-else class="storyboard-timeline">
      <div
        v-for="(shot, index) in storyboard"
        :key="shot.id"
        class="shot-card"
        :class="{ active: activeShotIndex === index }"
        @click="setActiveShot(index)"
      >
        <div class="shot-number">{{ index + 1 }}</div>
        <div class="shot-content">
          <div class="shot-header">
            <input
              class="shot-name-input"
              :value="shot.name"
              @input="updateShotName(index, ($event.target as HTMLInputElement).value)"
              @click.stop
            />
            <span class="shot-duration">{{ shot.duration }}s</span>
          </div>
          <div class="shot-tags">
            <n-tag v-if="shot.shotType" size="tiny" type="info">
              {{ getShotTypeName(shot.shotType) }}
            </n-tag>
            <n-tag v-if="shot.cameraMovement" size="tiny" type="success">
              {{ getMovementName(shot.cameraMovement) }}
            </n-tag>
            <n-tag v-if="shot.emotionTag" size="tiny" type="warning">
              {{ getEmotionName(shot.emotionTag) }}
            </n-tag>
          </div>
          <p class="shot-prompt-preview">
            {{ shot.prompt || '点击编辑提示词...' }}
          </p>
        </div>
        <div class="shot-actions" @click.stop>
          <n-button
            v-if="index > 0"
            size="tiny"
            text
            @click="moveUp(index)"
            title="上移"
          >
            <component :is="ChevronUp" :size="14" />
          </n-button>
          <n-button
            v-if="index < storyboard.length - 1"
            size="tiny"
            text
            @click="moveDown(index)"
            title="下移"
          >
            <component :is="ChevronDown" :size="14" />
          </n-button>
          <n-button
            size="tiny"
            text
            type="primary"
            @click="applyToForm(index)"
            title="应用到表单"
          >
            <component :is="Send" :size="14" />
          </n-button>
          <n-popconfirm @positive-click="removeShot(index)">
            <template #trigger>
              <n-button size="tiny" text type="error" title="删除">
                <component :is="Trash2" :size="14" />
              </n-button>
            </template>
            确定删除这个镜头？
          </n-popconfirm>
        </div>
      </div>
    </div>

    <n-drawer v-model:show="showEditor" :width="480" placement="right">
      <n-drawer-content title="编辑分镜" :native-scrollbar="false">
        <div v-if="activeShot" class="shot-editor">
          <div class="editor-section">
            <span class="section-label">镜头名称</span>
            <n-input
              :value="activeShot.name"
              @update:value="(v: string) => updateActiveShot({ name: v })"
            />
          </div>
          <div class="editor-section">
            <span class="section-label">提示词</span>
            <n-input
              type="textarea"
              :rows="4"
              :value="activeShot.prompt"
              placeholder="描述这个镜头的画面内容..."
              @update:value="(v: string) => updateActiveShot({ prompt: v })"
            />
          </div>
          <div class="editor-section">
            <span class="section-label">负面提示词</span>
            <n-input
              type="textarea"
              :rows="2"
              :value="activeShot.negativePrompt || ''"
              placeholder="不需要的内容..."
              @update:value="(v: string) => updateActiveShot({ negativePrompt: v })"
            />
          </div>
          <div class="editor-grid">
            <div class="editor-section">
              <span class="section-label">景别</span>
              <n-select
                :value="activeShot.shotType || null"
                :options="shotTypeOptions"
                @update:value="(v: any) => updateActiveShot({ shotType: v })"
              />
            </div>
            <div class="editor-section">
              <span class="section-label">运镜</span>
              <n-select
                :value="activeShot.cameraMovement || null"
                :options="movementOptions"
                @update:value="(v: any) => updateActiveShot({ cameraMovement: v })"
              />
            </div>
            <div class="editor-section">
              <span class="section-label">角度</span>
              <n-select
                :value="activeShot.cameraAngle || null"
                :options="angleOptions"
                @update:value="(v: any) => updateActiveShot({ cameraAngle: v })"
              />
            </div>
            <div class="editor-section">
              <span class="section-label">速度</span>
              <n-select
                :value="activeShot.movementSpeed || null"
                :options="speedOptions"
                @update:value="(v: any) => updateActiveShot({ movementSpeed: v })"
              />
            </div>
            <div class="editor-section">
              <span class="section-label">情绪</span>
              <n-select
                :value="activeShot.emotionTag || null"
                :options="emotionOptions"
                @update:value="(v: any) => updateActiveShot({ emotionTag: v })"
              />
            </div>
            <div class="editor-section">
              <span class="section-label">时长（秒）</span>
              <n-input-number
                :value="activeShot.duration"
                :min="1"
                :max="60"
                @update:value="(v: number) => updateActiveShot({ duration: v || 5 })"
              />
            </div>
          </div>
          <div class="editor-section">
            <span class="section-label">转场效果</span>
            <n-select
              :value="activeShot.transition || null"
              :options="transitionOptions"
              @update:value="(v: any) => updateActiveShot({ transition: v })"
            />
          </div>
          <div class="editor-section">
            <span class="section-label">备注</span>
            <n-input
              type="textarea"
              :rows="2"
              :value="activeShot.notes || ''"
              placeholder="拍摄备注、注意事项..."
              @update:value="(v: string) => updateActiveShot({ notes: v })"
            />
          </div>
          <div class="editor-actions">
            <n-button block @click="applyActiveToForm">
              <template #icon>
                <component :is="Send" :size="16" />
              </template>
              应用到生成表单
            </n-button>
            <n-button block type="primary" @click="syncFromForm">
              <template #icon>
                <component :is="RefreshCw" :size="16" />
              </template>
              从表单同步
            </n-button>
          </div>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useVideoStore } from '../stores/video'
import { storeToRefs } from 'pinia'
import {
  shotTypes,
  cameraMovements,
  cameraAngles,
  movementSpeeds,
  emotionTags,
  shotCombinations,
  getCameraMovementById,
} from '../data/shotLanguage'
import type { StoryboardShot } from '../data/shotLanguage'
import {
  Plus,
  ChevronUp,
  ChevronDown,
  Trash2,
  Send,
  Download,
  LayoutTemplate,
  Clapperboard,
  RefreshCw,
} from 'lucide-vue-next'

const videoStore = useVideoStore()
const { storyboard, activeShotIndex, activeShot, storyboardTotalDuration: totalDuration } = storeToRefs(videoStore)

const showEditor = ref(false)

const shotTypeOptions = shotTypes.map((t) => ({ label: t.name, value: t.id }))
const movementOptions = cameraMovements.map((m) => ({ label: m.name, value: m.id }))
const angleOptions = cameraAngles.map((a) => ({ label: a.name, value: a.id }))
const speedOptions = movementSpeeds.map((s) => ({ label: s.label, value: s.value }))
const emotionOptions = emotionTags.map((e) => ({ label: e.label, value: e.value }))
const transitionOptions = [
  { label: '无转场', value: '' },
  { label: '淡入淡出', value: 'fade' },
  { label: '划像', value: 'wipe' },
  { label: '缩放', value: 'zoom' },
  { label: '模糊', value: 'blur' },
  { label: '闪白', value: 'flash' },
]

const templateOptions = shotCombinations.map((combo) => ({
  label: combo.name,
  key: combo.id,
}))

function getShotTypeName(id?: string): string {
  if (!id) return ''
  return shotTypes.find((t) => t.id === id)?.name || id
}

function getMovementName(id?: string): string {
  if (!id) return ''
  return getCameraMovementById(id as any)?.name || id
}

function getEmotionName(id?: string): string {
  if (!id) return ''
  return emotionTags.find((e) => e.value === id)?.label || id
}

function handleAddShot() {
  videoStore.addShot()
}

function removeShot(index: number) {
  videoStore.removeShot(index)
}

function moveUp(index: number) {
  videoStore.moveShot(index, index - 1)
}

function moveDown(index: number) {
  videoStore.moveShot(index, index + 1)
}

function setActiveShot(index: number) {
  videoStore.setActiveShot(index)
  showEditor.value = true
}

function updateShotName(index: number, name: string) {
  videoStore.updateShot(index, { name })
}

function updateActiveShot(updates: Partial<StoryboardShot>) {
  if (activeShotIndex.value >= 0 && activeShotIndex.value < storyboard.value.length) {
    videoStore.updateShot(activeShotIndex.value, updates)
  }
}

function applyToForm(index: number) {
  videoStore.applyShotToForm(index)
}

function applyActiveToForm() {
  videoStore.applyShotToForm(activeShotIndex.value)
}

function syncFromForm() {
  videoStore.applyFormToShot(activeShotIndex.value)
}

function handleApplyTemplate(key: string) {
  const combo = shotCombinations.find((c) => c.id === key)
  if (combo) {
    videoStore.loadShotCombination(combo)
  }
}

function handleExport() {
  const text = videoStore.exportStoryboardText()
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `分镜脚本_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.shot-storyboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.storyboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-1);
}

.header-right {
  display: flex;
  gap: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  color: var(--text-color-3);
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 15px;
  font-weight: 500;
  margin: 0 0 4px 0;
}

.empty-hint {
  font-size: 13px;
  margin: 0;
}

.storyboard-timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shot-card {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--item-bg-color);
}

.shot-card:hover {
  border-color: var(--primary-color-hover);
}

.shot-card.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.shot-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.shot-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.shot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.shot-name-input {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color-1);
  border: none;
  background: transparent;
  outline: none;
  padding: 2px 4px;
  border-radius: 4px;
}

.shot-name-input:hover,
.shot-name-input:focus {
  background: var(--item-bg-color-hover);
}

.shot-duration {
  font-size: 12px;
  color: var(--text-color-3);
  font-weight: 500;
}

.shot-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.shot-prompt-preview {
  font-size: 13px;
  color: var(--text-color-2);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.shot-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  justify-content: center;
}

.shot-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color-2);
}

.editor-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.editor-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
</style>
