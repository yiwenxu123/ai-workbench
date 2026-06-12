<template>
  <div class="generate-panel">
    <div class="panel-layout">
      <GenerateFormSider
        @generate="handleGenerate"
        @prompt-input="onMainPromptInput"
        @apply-optimize="handleApplyOptimize"
        @quick-insert="handleQuickInsert"
      >
        <template #quick-entry>
          <SceneQuickEntryModal
            ref="sceneQuickEntryRef"
            @navigate-to-video="(p, n) => emit('navigateToVideo', p, n)"
            @navigate-to-edit="(i) => emit('navigateToEdit', i)"
          />
        </template>
      </GenerateFormSider>

      <GenerateResultPanel
        @fullscreen="showFullscreen = true"
        @regenerate="handleGenerate"
        @edit-image="editImage"
        @generate-video="generateVideo"
        @save-case="showSaveCaseModal = true"
        @image-loaded="onImageLoaded"
      />
    </div>

    <GenerateFullscreenModal
      v-model:show="showFullscreen"
      :image-url="generatorStore.lastImage || ''"
      @download="downloadImage"
    />

    <SaveCaseModal v-model:show="showSaveCaseModal" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore } from '../stores'
import { useKeyboard } from '../composables/useKeyboard'
import { useCreationContext } from '../composables/useCreationContext'
import GenerateFormSider from './generate/GenerateFormSider.vue'
import GenerateResultPanel from './generate/GenerateResultPanel.vue'
import SceneQuickEntryModal from './generate/SceneQuickEntryModal.vue'
import GenerateFullscreenModal from './generate/GenerateFullscreenModal.vue'
import SaveCaseModal from './generate/SaveCaseModal.vue'

const generatorStore = useGeneratorStore()
const message = useMessage()
const { setGenerationResult: setContextGenerationResult } = useCreationContext()

const sceneQuickEntryRef = ref<InstanceType<typeof SceneQuickEntryModal> | null>(null)
const showFullscreen = ref(false)
const showSaveCaseModal = ref(false)
const imageDimensions = ref<{ width: number; height: number } | null>(null)

watch(
  () => generatorStore.lastImage,
  (url) => {
    if (url) {
      setContextGenerationResult(url, generatorStore.model, generatorStore.size)
    }
  }
)

useKeyboard([
  {
    key: 'k', ctrl: true,
    handler: () => {
      document.querySelector<HTMLTextAreaElement>('.n-input textarea')?.focus()
    },
    description: '聚焦提示词输入框',
  },
  {
    key: 'Enter', ctrl: true,
    handler: (e) => { handleGenerate(); e.preventDefault() },
    description: '生成图片',
  },
])

const emit = defineEmits<{
  editImage: [imageUrl: string]
  generateVideo: [imageUrl: string, prompt: string]
  navigateToVideo: [prompt: string, negativePrompt: string]
  navigateToEdit: [instruction: string]
}>()

function onMainPromptInput() {
  sceneQuickEntryRef.value?.onMainPromptInput()
}

async function handleGenerate() {
  const success = await generatorStore.generate()
  if (success) message.success('生成成功！')
}

function handleQuickInsert(text: string) {
  const current = generatorStore.prompt
  generatorStore.prompt = current && !current.endsWith('，') && !current.endsWith(',')
    ? current + '，' + text
    : current + text
}

function handleApplyOptimize(prompt: string, negativePrompt?: string) {
  generatorStore.prompt = prompt
  if (negativePrompt) generatorStore.negativePrompt = negativePrompt
}

function onImageLoaded(dimensions: { width: number; height: number }) {
  imageDimensions.value = dimensions
}

function downloadImage() {
  if (!generatorStore.lastImage) return
  const link = document.createElement('a')
  link.href = generatorStore.lastImage
  link.download = `ai-image-${Date.now()}.png`
  link.click()
  message.success('开始下载')
}

function editImage() {
  if (!generatorStore.lastImage) return
  emit('editImage', generatorStore.lastImage)
}

function generateVideo() {
  if (!generatorStore.lastImage) return
  emit('generateVideo', generatorStore.lastImage, generatorStore.prompt)
}

onMounted(() => {
  // imageDimensions reserved for future zoom enhancements
  void imageDimensions.value
})
</script>

<style scoped>
.generate-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
