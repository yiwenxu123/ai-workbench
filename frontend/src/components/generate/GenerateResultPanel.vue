<template>
  <div class="panel-content">
    <div v-if="generatorStore.status === 'generating'" class="generation-feedback mb-3">
      <div class="feedback-pulse"></div>
      <div class="feedback-info">
        <span class="feedback-stage">{{ generatorStore.stageLabel || '准备中' }}</span>
        <span v-if="generatorStore.estimatedRemaining" class="feedback-eta">
          约 {{ Math.ceil(generatorStore.estimatedRemaining) }}s
        </span>
      </div>
      <n-progress type="line" :percentage="Math.round(generatorStore.progress)" :show-indicator="false" :height="4" />
    </div>

    <div v-if="generatorStore.error" class="error-card mb-3">
      <div class="error-title">{{ getErrorInfo(generatorStore.error).title }}</div>
      <div class="error-message">{{ getErrorInfo(generatorStore.error).message }}</div>
      <n-space v-if="getErrorInfo(generatorStore.error).action" class="mt-2">
        <n-button size="tiny" type="primary" @click="generatorStore.error = null">
          {{ getErrorInfo(generatorStore.error).action }}
        </n-button>
        <n-button size="tiny" quaternary @click="generatorStore.error = null">关闭</n-button>
      </n-space>
    </div>

    <div v-if="generatorStore.lastImage" class="image-result">
      <div class="result-header">
        <span class="result-title">生成结果</span>
        <n-space>
          <n-tag v-if="generatorStore.generationTime" size="small" type="info">
            耗时: {{ generatorStore.generationTime.toFixed(1) }}s
          </n-tag>
          <n-button size="tiny" quaternary @click="emit('fullscreen')">
            <template #icon><n-icon :component="ExpandOutline" /></template>
            全屏
          </n-button>
        </n-space>
      </div>

      <ImagePreview :src="generatorStore.lastImage" @loaded="(d) => emit('image-loaded', d)" />

      <div class="image-actions">
        <n-button size="small" type="primary" @click="emit('edit-image')">
          <template #icon><n-icon :component="CreateOutline" /></template>
          编辑图片
        </n-button>
        <n-button size="small" @click="emit('generate-video')">
          <template #icon><n-icon :component="VideocamOutline" /></template>
          生成视频
        </n-button>
        <n-button size="small" secondary @click="emit('save-case')">
          <template #icon><n-icon :component="StarOutline" /></template>
          收录为案例
        </n-button>
      </div>

      <div v-if="learningItems.length > 0" class="learning-section">
        <div class="learning-header">
          <n-space align="center" :size="4">
            <n-icon :component="BookOpen" />
            <span class="learning-title">相关知识推荐（点击可加入提示词）</span>
          </n-space>
        </div>
        <div class="learning-tags">
          <n-tag
            v-for="item in learningItems"
            :key="item.id || item.name"
            size="small"
            :bordered="false"
            style="cursor: pointer"
            @click="insertLearningTerm(item)"
          >
            {{ item.content || item.title || item.name }}
          </n-tag>
        </div>
      </div>

      <QuickActions @fullscreen="emit('fullscreen')" @regenerate="emit('regenerate')" />
    </div>

    <div v-else class="empty-state">
      <div class="empty-illustration">
        <div class="empty-glow"></div>
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <defs>
            <linearGradient id="emptyGrad" x1="0" y1="0" x2="80" y2="80">
              <stop offset="0%" stop-color="#4f7df3" stop-opacity="0.3"/>
              <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0.15"/>
            </linearGradient>
          </defs>
          <rect x="12" y="24" width="56" height="40" rx="10" stroke="url(#emptyGrad)" stroke-width="1.5" stroke-dasharray="4 4"/>
          <circle cx="28" cy="44" r="5" fill="#4f7df3" opacity="0.12"/>
          <circle cx="40" cy="38" r="5" fill="#8b5cf6" opacity="0.1"/>
          <circle cx="52" cy="42" r="5" fill="#4f7df3" opacity="0.08"/>
          <path d="M32 52l8-10 5 5 7-7" stroke="#4f7df3" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.25"/>
          <path d="M40 10l-5 10h10l-5 10" stroke="#8b5cf6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.2"/>
        </svg>
      </div>
      <div class="empty-title">准备生成一张图片</div>
      <div class="empty-hint">在左侧输入提示词，点击「生成图片」即可开始创作</div>
      <div class="empty-shortcut">
        <span class="shortcut-key">⌘ K</span>
        <span class="shortcut-label">聚焦输入</span>
        <span class="shortcut-sep">·</span>
        <span class="shortcut-key">⌘ ↵</span>
        <span class="shortcut-label">快速生成</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NProgress, NButton, NSpace, NTag, NIcon } from 'naive-ui'
import { ExpandOutline, CreateOutline, VideocamOutline, StarOutline } from '@vicons/ionicons5'
import { BookOpen } from 'lucide-vue-next'
import { useGeneratorStore } from '../../stores'
import ImagePreview from '../common/ImagePreview.vue'
import QuickActions from '../QuickActions.vue'
import { getErrorInfo } from '../../utils/errorMessages'
import { useGenerateLearning } from '../../composables/useGenerateLearning'

const generatorStore = useGeneratorStore()
const { learningItems, insertLearningTerm } = useGenerateLearning()

const emit = defineEmits<{
  fullscreen: []
  regenerate: []
  'edit-image': []
  'generate-video': []
  'save-case': []
  'image-loaded': [dimensions: { width: number; height: number }]
}>()
</script>

<style scoped>
.image-result { display: flex; flex-direction: column; flex: 1; min-height: 0; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.result-title { font-size: 14px; font-weight: 600; }
.image-actions { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
.learning-section {
  margin-top: 14px; padding: 12px 14px; background: var(--gray-50);
  border-radius: var(--radius-sm); border: 1px solid var(--border-light);
}
.learning-title { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.learning-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.generation-feedback {
  display: flex; flex-direction: column; gap: 8px; padding: 12px 14px;
  background: var(--brand-50, #f0f4ff); border-radius: var(--radius-md, 10px);
  border: 1px solid var(--brand-100, #e0e7ff); position: relative; overflow: hidden;
}
.feedback-pulse {
  position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, var(--brand-500, #4f7df3), transparent);
  animation: pulse-sweep 2s ease-in-out infinite;
}
@keyframes pulse-sweep { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
.feedback-info { display: flex; justify-content: space-between; align-items: center; }
.feedback-stage { font-size: 13px; font-weight: 500; color: var(--brand-600, #4f46e5); }
.feedback-eta { font-size: 12px; color: var(--text-tertiary, #94a3b8); }
.error-card { padding: 12px 14px; background: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius-md, 10px); }
.error-title { font-size: 13px; font-weight: 600; color: #dc2626; margin-bottom: 4px; }
.error-message { font-size: 12px; color: #7f1d1d; line-height: 1.5; }
.mb-3 { margin-bottom: 12px; }
.mt-2 { margin-top: 8px; }
</style>
