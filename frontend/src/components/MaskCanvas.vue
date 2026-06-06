<template>
  <div class="mask-canvas" ref="containerRef">
    <canvas
      ref="canvasRef"
      :width="canvasWidth"
      :height="canvasHeight"
      @mousedown="startDrawing"
      @mousemove="draw"
      @mouseup="stopDrawing"
      @mouseleave="stopDrawing"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="stopDrawing"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps<{
  imageSrc: string
  brushSize: number
}>()

const emit = defineEmits<{
  maskChange: [maskDataUrl: string]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const canvasWidth = ref(400)
const canvasHeight = ref(300)
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)

const imageWidth = ref(0)
const imageHeight = ref(0)
const offsetX = ref(0)
const offsetY = ref(0)
const scale = ref(1)

let imageObj: HTMLImageElement | null = null
let maskCanvas: HTMLCanvasElement | null = null
let maskCtx: CanvasRenderingContext2D | null = null

onMounted(() => {
  initCanvas()
})

watch(() => props.imageSrc, () => {
  nextTick(() => {
    initCanvas()
  })
})

function initCanvas() {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    imageObj = img
    imageWidth.value = img.width
    imageHeight.value = img.height

    const containerWidth = container.clientWidth
    const maxHeight = 400

    scale.value = Math.min(containerWidth / img.width, maxHeight / img.height)
    canvasWidth.value = Math.floor(img.width * scale.value)
    canvasHeight.value = Math.floor(img.height * scale.value)

    offsetX.value = 0
    offsetY.value = 0

    canvas.width = canvasWidth.value
    canvas.height = canvasHeight.value

    ctx.drawImage(img, 0, 0, canvasWidth.value, canvasHeight.value)

    maskCanvas = document.createElement('canvas')
    maskCanvas.width = canvasWidth.value
    maskCanvas.height = canvasHeight.value
    maskCtx = maskCanvas.getContext('2d')
  }
  img.src = props.imageSrc
}

function getCoordinates(e: MouseEvent | TouchEvent): { x: number; y: number } {
  const canvas = canvasRef.value
  if (!canvas) return { x: 0, y: 0 }

  const rect = canvas.getBoundingClientRect()
  let clientX = 0
  let clientY = 0

  if ('touches' in e && e.touches && e.touches.length > 0) {
    clientX = e.touches[0]!.clientX
    clientY = e.touches[0]!.clientY
  } else if ('clientX' in e) {
    clientX = e.clientX
    clientY = e.clientY
  }

  return {
    x: clientX - rect.left,
    y: clientY - rect.top
  }
}

function startDrawing(e: MouseEvent | TouchEvent) {
  isDrawing.value = true
  const coords = getCoordinates(e)
  lastX.value = coords.x
  lastY.value = coords.y

  drawMask(coords.x, coords.y, coords.x, coords.y)
}

function draw(e: MouseEvent | TouchEvent) {
  if (!isDrawing.value) return
  e.preventDefault()

  const coords = getCoordinates(e)
  drawMask(lastX.value, lastY.value, coords.x, coords.y)
  lastX.value = coords.x
  lastY.value = coords.y
}

function stopDrawing() {
  if (isDrawing.value) {
    isDrawing.value = false
    emitMask()
  }
}

function handleTouchStart(e: TouchEvent) {
  e.preventDefault()
  startDrawing(e)
}

function handleTouchMove(e: TouchEvent) {
  e.preventDefault()
  draw(e)
}

function drawMask(x1: number, y1: number, x2: number, y2: number) {
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!ctx || !maskCtx) return

  const brushRadius = props.brushSize / 2

  ctx.globalCompositeOperation = 'source-over'
  ctx.strokeStyle = 'rgba(255, 100, 100, 0.5)'
  ctx.lineWidth = props.brushSize
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'

  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2, y2)
  ctx.stroke()

  maskCtx.fillStyle = 'white'
  maskCtx.beginPath()
  maskCtx.arc(x1, y1, brushRadius, 0, Math.PI * 2)
  maskCtx.fill()

  if (x1 !== x2 || y1 !== y2) {
    maskCtx.lineWidth = props.brushSize
    maskCtx.lineCap = 'round'
    maskCtx.lineJoin = 'round'
    maskCtx.strokeStyle = 'white'
    maskCtx.beginPath()
    maskCtx.moveTo(x1, y1)
    maskCtx.lineTo(x2, y2)
    maskCtx.stroke()
  }
}

function emitMask() {
  if (!maskCanvas) return

  const hasMask = checkHasMask()
  if (hasMask) {
    const maskDataUrl = maskCanvas.toDataURL('image/png')
    emit('maskChange', maskDataUrl)
  } else {
    emit('maskChange', '')
  }
}

function checkHasMask(): boolean {
  const canvas = maskCanvas
  const ctx = maskCtx
  if (!ctx || !canvas) return false

  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  if (!imageData) return false
  
  const data = imageData.data

  for (let i = 3; i < data.length; i += 4) {
    if (data[i]! > 0) return true
  }

  return false
}

function clearMask() {
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (!ctx || !maskCtx || !maskCanvas || !imageObj) return

  ctx.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  ctx.drawImage(imageObj, 0, 0, canvasWidth.value, canvasHeight.value)

  maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height)

  emit('maskChange', '')
}

function getMaskDataUrl(): string | null {
  if (!maskCanvas) return null
  return maskCanvas.toDataURL('image/png')
}

defineExpose({
  clearMask,
  getMaskDataUrl
})
</script>

<style scoped>
.mask-canvas {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f0f0;
  min-height: 200px;
}

canvas {
  cursor: crosshair;
  max-width: 100%;
  touch-action: none;
}
</style>
