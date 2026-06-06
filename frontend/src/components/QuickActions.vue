<template>
  <div class="quick-actions">
    <n-space :size="8">
      <n-tooltip trigger="hover" v-for="action in actions" :key="action.key">
        <template #trigger>
          <n-button
            :type="action.type || 'default'"
            :disabled="action.disabled"
            size="small"
            @click="action.handler"
          >
            <template #icon>
              <n-icon :component="action.icon" />
            </template>
            {{ action.label }}
          </n-button>
        </template>
        {{ action.tooltip }}
      </n-tooltip>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NIcon, NSpace, NTooltip, useMessage } from 'naive-ui'
import {
  CopyOutline,
  RefreshOutline,
  DownloadOutline,
  ExpandOutline,
  HeartOutline,
  CreateOutline
} from '@vicons/ionicons5'
import { useGeneratorStore, useHistoryStore } from '../stores'

interface QuickAction {
  key: string
  label: string
  icon: typeof CopyOutline
  handler: () => void
  disabled?: boolean
  type?: 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error'
  tooltip: string
}

const emit = defineEmits<{
  (e: 'fullscreen'): void
  (e: 'regenerate'): void
}>()

const message = useMessage()
const generatorStore = useGeneratorStore()
const historyStore = useHistoryStore()

const hasImage = computed(() => !!generatorStore.lastImage)
const hasPrompt = computed(() => !!generatorStore.prompt.trim())

const actions = computed<QuickAction[]>(() => [
  {
    key: 'copy-prompt',
    label: '复制提示词',
    icon: CopyOutline,
    disabled: !hasPrompt.value,
    tooltip: '复制当前提示词到剪贴板',
    handler: handleCopyPrompt
  },
  {
    key: 'regenerate',
    label: '重新生成',
    icon: RefreshOutline,
    disabled: !hasPrompt.value || generatorStore.status === 'generating',
    type: 'primary',
    tooltip: '使用相同参数重新生成',
    handler: () => emit('regenerate')
  },
  {
    key: 'download',
    label: '下载',
    icon: DownloadOutline,
    disabled: !hasImage.value,
    tooltip: '下载生成的图片',
    handler: handleDownload
  },
  {
    key: 'fullscreen',
    label: '全屏',
    icon: ExpandOutline,
    disabled: !hasImage.value,
    tooltip: '全屏查看图片',
    handler: () => emit('fullscreen')
  },
  {
    key: 'favorite',
    label: '收藏',
    icon: HeartOutline,
    disabled: !hasImage.value,
    tooltip: '收藏到历史记录',
    handler: handleFavorite
  },
  {
    key: 'feedback-good',
    label: '好用',
    icon: HeartOutline,
    disabled: !hasImage.value,
    tooltip: '记录这次结果好用，便于后续优化模板',
    handler: () => handleFeedback('good')
  },
  {
    key: 'feedback-bad',
    label: '不好用',
    icon: CreateOutline,
    disabled: !hasImage.value,
    tooltip: '记录这次结果不好用，便于后续复盘',
    handler: () => handleFeedback('bad')
  }
])

async function handleCopyPrompt(): Promise<void> {
  if (!generatorStore.prompt) return
  try {
    await navigator.clipboard.writeText(generatorStore.prompt)
    message.success('提示词已复制')
  } catch {
    message.error('复制失败')
  }
}

function handleDownload(): void {
  if (!generatorStore.lastImage) return
  const link = document.createElement('a')
  link.href = generatorStore.lastImage
  link.download = `ai-image-${Date.now()}.png`
  link.click()
  message.success('开始下载')
}

async function handleFavorite(): Promise<void> {
  if (!generatorStore.lastImage || !generatorStore.prompt) return
  
  try {
    const id = await historyStore.add({
      prompt: generatorStore.prompt,
      negativePrompt: generatorStore.negativePrompt,
      model: generatorStore.model,
      size: generatorStore.size,
      imageUrl: generatorStore.lastImage,
      seed: generatorStore.seed,
      steps: generatorStore.steps,
      cfgScale: generatorStore.cfgScale,
      rating: 5,
      tags: ['收藏']
    })
    await historyStore.toggleFavorite(id)
    message.success('已收藏到历史记录')
  } catch {
    message.error('收藏失败')
  }
}

function handleFeedback(value: 'good' | 'bad'): void {
  const records = JSON.parse(localStorage.getItem('ai_studio_feedback') || '[]')
  records.unshift({
    value,
    prompt: generatorStore.prompt,
    model: generatorStore.model,
    size: generatorStore.size,
    imageUrl: generatorStore.lastImage,
    createdAt: new Date().toISOString()
  })
  localStorage.setItem('ai_studio_feedback', JSON.stringify(records.slice(0, 100)))
  message.success(value === 'good' ? '已记录：这次结果好用' : '已记录：这次结果不好用')
}
</script>

<style scoped>
.quick-actions {
  display: flex;
  justify-content: center;
  padding: 8px 0;
  background: #fafafa;
  border-radius: 8px;
  margin-top: 8px;
}
</style>
