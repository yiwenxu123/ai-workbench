<template>
  <n-modal
    v-model:show="show"
    :mask-closable="true"
    :closable="true"
    preset="card"
    style="width: 100vw; height: 100vh; max-width: none; top: 0; left: 0; margin: 0; border-radius: 0;"
    :bordered="false"
  >
    <template #header>
      <div class="fullscreen-header">
        <span>图片预览</span>
        <div class="fullscreen-toolbar">
          <n-button-group size="small">
            <n-button @click="fullscreenZoomOut" :disabled="fullscreenScale <= 0.25">
              <template #icon><n-icon :component="RemoveOutline" /></template>
            </n-button>
            <n-button disabled>{{ Math.round(fullscreenScale * 100) }}%</n-button>
            <n-button @click="fullscreenZoomIn" :disabled="fullscreenScale >= 4">
              <template #icon><n-icon :component="AddOutline" /></template>
            </n-button>
          </n-button-group>
          <n-button size="small" @click="resetFullscreen">
            <template #icon><n-icon :component="ResizeOutline" /></template>
            适应窗口
          </n-button>
        </div>
      </div>
    </template>

    <div
      class="fullscreen-container"
      ref="fullscreenContainerRef"
      @wheel="handleFullscreenWheel"
      @mousedown="startFullscreenDrag"
    >
      <img :src="imageUrl" class="fullscreen-image" :style="fullscreenStyle" draggable="false" />
    </div>

    <template #footer>
      <div class="fullscreen-actions">
        <n-button @click="emit('download')">
          <template #icon><n-icon :component="DownloadOutline" /></template>
          下载图片
        </n-button>
        <n-button type="primary" @click="show = false">关闭 (ESC)</n-button>
      </div>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { NModal, NButton, NButtonGroup, NIcon } from 'naive-ui'
import { DownloadOutline, RemoveOutline, AddOutline, ResizeOutline } from '@vicons/ionicons5'
import { useImageZoom } from '../../composables/useImageZoom'

defineProps<{
  imageUrl: string
}>()

const show = defineModel<boolean>('show', { default: false })

const emit = defineEmits<{
  download: []
}>()

const fullscreenContainerRef = ref<HTMLElement | null>(null)
const imageDimensions = ref<{ width: number; height: number } | null>(null)

const {
  scale: fullscreenScale,
  style: fullscreenStyle,
  zoomIn: fullscreenZoomIn,
  zoomOut: fullscreenZoomOut,
  reset: resetFullscreen,
  fitToContainer: fitFullscreen,
  handleWheel: handleFullscreenWheel,
  startDrag: startFullscreenDrag,
} = useImageZoom({
  containerRef: fullscreenContainerRef,
  imageDimensions,
})

watch(show, (val) => {
  if (val) resetFullscreen()
})

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && show.value) {
    show.value = false
  }
}

function onResize() {
  if (show.value) fitFullscreen()
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.fullscreen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.fullscreen-toolbar {
  display: flex;
  gap: 8px;
}
.fullscreen-container {
  width: 100%;
  height: calc(100vh - 140px);
  overflow: hidden;
  background: linear-gradient(45deg, #2a2a2a 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a2a 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a2a 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a2a 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  background-color: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  user-select: none;
}
.fullscreen-container:active {
  cursor: grabbing;
}
.fullscreen-image {
  max-width: none;
  max-height: none;
  will-change: transform;
}
.fullscreen-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
:deep(.n-modal .n-card) {
  height: 100vh;
}
:deep(.n-modal .n-card-body) {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}
</style>
