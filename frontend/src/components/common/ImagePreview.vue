<template>
  <div class="image-preview">
    <div class="image-toolbar">
      <n-button-group size="small">
        <n-button @click="zoomOut" :disabled="scale <= 0.25">
          <template #icon><n-icon :component="RemoveOutline" /></template>
        </n-button>
        <n-button disabled>{{ Math.round(scale * 100) }}%</n-button>
        <n-button @click="zoomIn" :disabled="scale >= 4">
          <template #icon><n-icon :component="AddOutline" /></template>
        </n-button>
      </n-button-group>
      <n-button size="small" @click="reset">
        <template #icon><n-icon :component="ResizeOutline" /></template>
        适应
      </n-button>
    </div>

    <div
      class="image-preview-container"
      ref="containerRef"
      @wheel="handleWheel"
      @mousedown="startDrag"
    >
      <img
        :src="src"
        class="preview-image"
        :style="style"
        @load="onImgLoad"
        draggable="false"
      />
    </div>

    <div class="image-info" v-if="dimensions">
      <n-tag size="small" type="info">{{ dimensions.width }} × {{ dimensions.height }}</n-tag>
      <n-tag size="small" v-if="scale !== 1">{{ Math.round(scale * 100) }}% 缩放</n-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NButton, NButtonGroup, NIcon, NTag } from 'naive-ui'
import { RemoveOutline, AddOutline, ResizeOutline } from '@vicons/ionicons5'
import { useImageZoom } from '../../composables/useImageZoom'

const props = defineProps<{
  src: string
}>()

const emit = defineEmits<{
  loaded: [dimensions: { width: number; height: number }]
}>()

const containerRef = ref<HTMLElement | null>(null)
const dimensions = ref<{ width: number; height: number } | null>(null)

const {
  scale,
  style,
  zoomIn,
  zoomOut,
  reset,
  handleWheel,
  startDrag,
  fitToContainer,
} = useImageZoom({
  containerRef,
  imageDimensions: dimensions,
})

function onImgLoad(event: Event) {
  const img = event.target as HTMLImageElement
  dimensions.value = {
    width: img.naturalWidth,
    height: img.naturalHeight,
  }
  fitToContainer()
  emit('loaded', dimensions.value)
}

// 切图时重置
watch(() => props.src, () => {
  dimensions.value = null
  scale.value = 1
})
</script>

<style scoped>
.image-preview {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.image-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.image-preview-container {
  flex: 1;
  min-height: 200px;
  overflow: hidden;
  background:
    linear-gradient(45deg, #dde1e7 25%, transparent 25%),
    linear-gradient(-45deg, #dde1e7 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #dde1e7 75%),
    linear-gradient(-45deg, transparent 75%, #dde1e7 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
  background-color: #eceff4;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  border: 1px solid var(--border, #e2e8f0);
  cursor: grab;
  user-select: none;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.04);
}

.image-preview-container:active {
  cursor: grabbing;
}

.preview-image {
  max-width: none;
  max-height: none;
  will-change: transform;
}

.image-info {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}
</style>
