/**
 * 图片缩放/拖拽 Composable
 * 统一管理单张图片的缩放、平移、拖拽和自适应逻辑
 */
import { ref, computed, type Ref } from 'vue'

export interface UseImageZoomOptions {
  containerRef: Ref<HTMLElement | null>
  imageDimensions: Ref<{ width: number; height: number } | null>
  minScale?: number
  maxScale?: number
  /** 额外的容器内边距（像素），默认 20 */
  containerPadding?: number
}

export function useImageZoom(options: UseImageZoomOptions) {
  const { containerRef, imageDimensions, containerPadding = 20 } = options
  const minScale = options.minScale ?? 0.25
  const maxScale = options.maxScale ?? 4

  const scale = ref(1)
  const offset = ref({ x: 0, y: 0 })
  const isDragging = ref(false)
  const dragStart = ref({ x: 0, y: 0 })
  const dragOffsetStart = ref({ x: 0, y: 0 })

  const style = computed(() => ({
    transform: `translate(${offset.value.x}px, ${offset.value.y}px) scale(${scale.value})`,
    transformOrigin: 'center center',
    transition: isDragging.value ? 'none' : 'transform 0.15s ease-out',
  }))

  function fitToContainer() {
    const container = containerRef.value
    const dims = imageDimensions.value
    if (!container || !dims) return

    const cw = container.clientWidth
    const ch = container.clientHeight
    const sx = (cw - containerPadding) / dims.width
    const sy = (ch - containerPadding) / dims.height
    scale.value = Math.min(sx, sy, 1)
    offset.value = { x: 0, y: 0 }
  }

  function zoomIn() {
    scale.value = Math.min(maxScale, scale.value * 1.25)
  }

  function zoomOut() {
    scale.value = Math.max(minScale, scale.value / 1.25)
  }

  function reset() {
    fitToContainer()
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    scale.value = Math.max(minScale, Math.min(maxScale, scale.value * delta))
  }

  function startDrag(e: MouseEvent) {
    if (e.button !== 0) return
    isDragging.value = true
    dragStart.value = { x: e.clientX, y: e.clientY }
    dragOffsetStart.value = { ...offset.value }

    document.addEventListener('mousemove', onDrag)
    document.addEventListener('mouseup', stopDrag)
  }

  function onDrag(e: MouseEvent) {
    if (!isDragging.value) return
    offset.value = {
      x: dragOffsetStart.value.x + (e.clientX - dragStart.value.x),
      y: dragOffsetStart.value.y + (e.clientY - dragStart.value.y),
    }
  }

  function stopDrag() {
    isDragging.value = false
    document.removeEventListener('mousemove', onDrag)
    document.removeEventListener('mouseup', stopDrag)
  }

  return {
    scale,
    offset,
    isDragging,
    style,
    zoomIn,
    zoomOut,
    reset,
    fitToContainer,
    handleWheel,
    startDrag,
  }
}
