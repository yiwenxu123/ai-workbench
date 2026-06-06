<template>
  <div class="panel-layout image-editor">
    <!-- 左侧参数区 -->
    <div class="panel-sider">
      <div class="sider-header">
        <h3>图片编辑</h3>
      </div>
      
      <n-alert v-if="!providerStore.hasConfiguredEditProvider" type="warning" class="mb-3" :show-icon="false">
        <span>请先配置图片编辑能力</span>
        <n-button text type="primary" @click="configStore.showConfigModal = true">
          立即配置
        </n-button>
      </n-alert>

      <!-- 统一上传区：在所有标签页中位置固定 -->
      <div class="upload-section">
        <n-upload accept="image/*" :show-file-list="false" :custom-request="handleImageUpload">
          <n-button type="primary" block dashed>+ 上传图片</n-button>
        </n-upload>
        <n-button v-if="!sourceImage && historyStore.items.length > 0" block @click="showHistorySelect = true" class="mt-2">
          从历史作品选择
        </n-button>
        <div v-if="sourceImage" class="uploaded-info mt-2">
          <span class="uploaded-dot"></span>
          <span class="uploaded-text">已上传图片</span>
          <n-button size="tiny" quaternary @click="clearImage" class="uploaded-replace">替换</n-button>
        </div>
      </div>

      <n-tabs v-model:value="activeTab" type="line" class="editor-mode-tabs">
        <!-- 指令编辑 -->
        <n-tab-pane name="instruction" tab="指令编辑">
          <div class="sider-controls">
            <n-form v-if="sourceImage" label-placement="top">
              <n-form-item label="编辑指令">
                <n-input
                  v-model:value="instruction"
                  type="textarea"
                  placeholder="描述你想要的修改，例如：把背景换成海滩、给人物戴上墨镜..."
                  :rows="4"
                  :disabled="isEditing"
                />
              </n-form-item>

              <n-form-item label="编辑强度">
                <n-slider v-model:value="editStrength" :min="0" :max="1" :step="0.1" />
                <span class="ml-2">{{ editStrength }}</span>
              </n-form-item>

              <n-button type="primary" block size="large" class="mt-2" :loading="isEditing" @click="handleInstructionEdit" :disabled="!instruction">
                开始编辑
              </n-button>
            </n-form>
            <div v-if="!sourceImage" class="no-image-hint">请先上传要编辑的图片</div>
          </div>
        </n-tab-pane>

        <!-- 局部重绘 -->
        <n-tab-pane name="inpaint" tab="局部重绘">
          <div class="sider-controls">
            <n-form v-if="sourceImage" label-placement="top">
              <n-form-item label="画笔大小">
                <n-slider v-model:value="brushSize" :min="5" :max="50" style="flex: 1" />
                <n-button size="small" class="ml-2" @click="clearMask">清除选区</n-button>
              </n-form-item>

              <n-form-item label="修改描述">
                <n-input
                  v-model:value="instruction"
                  type="textarea"
                  placeholder="描述涂抹区域的修改，例如：换成蓝色的天空、添加一朵花..."
                  :rows="4"
                  :disabled="isEditing"
                />
              </n-form-item>

              <n-button type="primary" block size="large" class="mt-2" :loading="isEditing" @click="handleInpaintEdit" :disabled="!instruction || !hasMask">
                开始重绘
              </n-button>
            </n-form>
            <div v-if="!sourceImage" class="no-image-hint">请先上传要编辑的图片</div>
          </div>
        </n-tab-pane>

        <!-- 扩图 -->
        <n-tab-pane name="outpaint" tab="扩图">
          <div class="sider-controls">
            <n-form v-if="sourceImage" label-placement="top">
              <n-form-item label="扩展方向">
                <n-checkbox-group v-model:value="expandDirections">
                  <n-space>
                    <n-checkbox value="top" label="上" />
                    <n-checkbox value="bottom" label="下" />
                    <n-checkbox value="left" label="左" />
                    <n-checkbox value="right" label="右" />
                  </n-space>
                </n-checkbox-group>
              </n-form-item>
              
              <n-form-item label="扩展比例">
                <n-slider v-model:value="expandRatio" :min="10" :max="100" :step="10" />
                <span class="ml-2">{{ expandRatio }}%</span>
              </n-form-item>
              
              <n-form-item label="扩展描述">
                <n-input
                  v-model:value="instruction"
                  type="textarea"
                  placeholder="描述扩展区域的内容（可选），例如：延伸蓝天白云背景..."
                  :rows="3"
                  :disabled="isEditing"
                />
              </n-form-item>

              <n-button type="primary" block size="large" class="mt-2" :loading="isEditing" @click="handleOutpaintEdit" :disabled="expandDirections.length === 0">
                开始扩图
              </n-button>
            </n-form>
            <div v-if="!sourceImage" class="no-image-hint">请先上传要编辑的图片</div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- 右侧画布区 -->
    <div class="panel-content">
      <div v-if="!sourceImage" class="empty-state">
        <div class="empty-icon"><n-icon :component="Image" /></div>
        <div class="empty-text">请在左侧上传图片开始编辑</div>
      </div>

      <div v-else class="editor-workspace">
        <div class="workspace-section">
          <div class="section-header">
            <span class="section-title">{{ activeTab === 'inpaint' ? '涂抹需要修改的选区' : '原图' }}</span>
            <n-button size="small" quaternary circle @click="clearImage" title="清除图片">
              <template #icon><n-icon><CloseOutline /></n-icon></template>
            </n-button>
          </div>
          
          <div class="canvas-container">
            <MaskCanvas
              v-if="activeTab === 'inpaint'"
              ref="maskCanvasRef"
              :image-src="sourceImage"
              :brush-size="brushSize"
              @mask-change="handleMaskChange"
            />
            <n-image v-else :src="sourceImage" object-fit="contain" class="preview-image" />
          </div>
        </div>

        <div v-if="isEditing || resultImage" class="workspace-section">
          <div class="section-header">
            <span class="section-title">编辑结果</span>
            <n-space v-if="resultImage">
              <n-button size="small" @click="downloadResult">下载图片</n-button>
              <n-button size="small" @click="continueEdit">基于此图继续</n-button>
              <n-button size="small" type="primary" @click="saveToHistory">保存到作品</n-button>
            </n-space>
          </div>
          
          <div class="result-container">
            <div v-if="isEditing" class="generating-state">
              <n-spin size="large" />
              <span class="mt-3">正在处理图片，请稍候...</span>
            </div>
            <n-image v-else-if="resultImage" :src="resultImage" object-fit="contain" class="preview-image" />
          </div>
        </div>
      </div>
    </div>

    <n-modal v-model:show="showHistorySelect" preset="card" title="选择历史图片" style="width: 600px">
      <n-scrollbar style="max-height: 400px">
        <n-grid :cols="3" :x-gap="8" :y-gap="8">
          <n-gi v-for="item in historyStore.items.slice(0, 12)" :key="item.id">
            <div class="history-card" @click="selectFromHistory(item)">
              <n-image :src="item.imageUrl" object-fit="cover" class="history-img" preview-disabled />
            </div>
          </n-gi>
        </n-grid>
      </n-scrollbar>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  NAlert, NButton, NTabs, NTabPane, NUpload, NForm, NFormItem, NInput,
  NSlider, NSpace, NIcon, NCheckboxGroup, NCheckbox, NImage, NSpin,
  NModal, NScrollbar, NGrid, NGi, useMessage
} from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'
import { Image } from 'lucide-vue-next'
import { useConfigStore, useHistoryStore, useEditorStore, useProviderStore } from '../stores'
import { apiService } from '../api'
import MaskCanvas from './MaskCanvas.vue'
import type { History } from '../types'
import type { UploadCustomRequestOptions } from 'naive-ui'

const message = useMessage()
const configStore = useConfigStore()
const historyStore = useHistoryStore()
const editorStore = useEditorStore()
const providerStore = useProviderStore()

const activeTab = ref('instruction')
const sourceImage = ref<string | null>(null)
const resultImage = ref<string | null>(null)
const instruction = ref('')
const editStrength = ref(0.7)
const isEditing = ref(false)

const brushSize = ref(20)
const hasMask = ref(false)
const maskCanvasRef = ref<InstanceType<typeof MaskCanvas> | null>(null)

const expandDirections = ref<string[]>([])
const expandRatio = ref(50)

const showHistorySelect = ref(false)

watch(() => editorStore.sourceImage, (newImage) => {
  if (newImage) {
    sourceImage.value = newImage
    resultImage.value = null
    instruction.value = editorStore.instruction || ''
    editorStore.clearSourceImage()
    editorStore.clearInstruction()
  }
})

watch(() => editorStore.instruction, (newInstruction) => {
  if (newInstruction && !sourceImage.value) {
    instruction.value = newInstruction
  }
})

function handleImageUpload({ file }: UploadCustomRequestOptions) {
  const reader = new FileReader()
  reader.onload = (e) => {
    sourceImage.value = e.target?.result as string
    resultImage.value = null
    instruction.value = ''
  }
  reader.readAsDataURL(file.file as File)
}

function clearImage() {
  sourceImage.value = null
  resultImage.value = null
  instruction.value = ''
  hasMask.value = false
}

function selectFromHistory(item: History) {
  sourceImage.value = item.imageUrl || null
  showHistorySelect.value = false
  resultImage.value = null
}

function handleMaskChange(maskDataUrl: string) {
  hasMask.value = !!maskDataUrl
}

function clearMask() {
  maskCanvasRef.value?.clearMask()
  hasMask.value = false
}

function getEditProviderParams() {
  const provider = providerStore.getDefaultProviderByCapability('edit')
  return {
    api_key: provider?.apiKey || undefined,
    api_endpoint: provider?.endpoint || undefined
  }
}

async function handleInstructionEdit() {
  if (!sourceImage.value || !instruction.value) return

  isEditing.value = true
  try {
    const result = await apiService.editImage({
      image: sourceImage.value,
      instruction: instruction.value,
      edit_type: 'instruction',
      ...getEditProviderParams()
    })

    if (result.success && result.image) {
      resultImage.value = result.image
      message.success('编辑成功')
    } else {
      message.error(result.error || '编辑失败')
    }
  } catch (error: any) {
    message.error(error.userMessage || `编辑失败: ${error.message}`)
  } finally {
    isEditing.value = false
  }
}

async function handleInpaintEdit() {
  if (!sourceImage.value || !instruction.value || !hasMask.value) return

  const maskDataUrl = maskCanvasRef.value?.getMaskDataUrl()
  if (!maskDataUrl) {
    message.warning('请先涂抹需要修改的区域')
    return
  }

  isEditing.value = true
  try {
    const result = await apiService.editImage({
      image: sourceImage.value,
      instruction: instruction.value,
      edit_type: 'inpaint',
      mask: maskDataUrl,
      ...getEditProviderParams()
    })

    if (result.success && result.image) {
      resultImage.value = result.image
      message.success('重绘成功')
    } else {
      message.error(result.error || '重绘失败')
    }
  } catch (error: any) {
    message.error(error.userMessage || `重绘失败: ${error.message}`)
  } finally {
    isEditing.value = false
  }
}

async function handleOutpaintEdit() {
  if (!sourceImage.value || expandDirections.value.length === 0) return

  isEditing.value = true
  try {
    const directionStr = expandDirections.value.join(',')
    const outpaintInstruction = instruction.value || `向${directionStr}方向扩展画面`

    const result = await apiService.editImage({
      image: sourceImage.value,
      instruction: outpaintInstruction,
      edit_type: 'outpaint',
      extra_params: {
        expand_directions: expandDirections.value,
        expand_ratio: expandRatio.value
      },
      ...getEditProviderParams()
    })

    if (result.success && result.image) {
      resultImage.value = result.image
      message.success('扩图成功')
    } else {
      message.error(result.error || '扩图失败')
    }
  } catch (error: any) {
    message.error(error.userMessage || `扩图失败: ${error.message}`)
  } finally {
    isEditing.value = false
  }
}

function downloadResult() {
  if (!resultImage.value) return

  const link = document.createElement('a')
  link.href = resultImage.value
  link.download = `edited_${Date.now()}.png`
  link.click()
}

function continueEdit() {
  if (!resultImage.value) return
  sourceImage.value = resultImage.value
  resultImage.value = null
  instruction.value = ''
  hasMask.value = false
  clearMask()
}

async function saveToHistory() {
  if (!resultImage.value) return

  await historyStore.add({
    prompt: instruction.value || '图片编辑',
    model: 'wanx2.1-imageedit',
    size: 'edited',
    imageUrl: resultImage.value,
    tags: ['编辑']
  })

  message.success('已保存到作品')
}
</script>

<style scoped>
.panel-layout {
  display: flex;
  gap: var(--panel-gap, 20px);
  height: 100%;
  transition: gap var(--duration-base) var(--ease-out);
}

.panel-sider {
  flex: 0 0 380px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  transition: box-shadow var(--duration-base) var(--ease-out), background var(--duration-base) var(--ease-out);
}

.panel-content {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  transition: box-shadow var(--duration-base) var(--ease-out), background var(--duration-base) var(--ease-out);
}

@media (max-width: 1024px) {
  .panel-layout {
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
  }
  .panel-sider {
    flex: none;
    max-height: 55vh;
  }
  .panel-content {
    flex: 1;
    min-height: 300px;
  }
}

.sider-header h3 {
  margin: 0 0 20px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
}

/* ── 统一上传区（固定在 Tab 上方）── */
.upload-section {
  flex-shrink: 0;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.uploaded-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-subtle);
  border-radius: var(--radius-sm);
}

.uploaded-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand-500);
  flex-shrink: 0;
}

.uploaded-text {
  font-size: 12px;
  color: var(--text-secondary);
  flex: 1;
}

.uploaded-replace {
  font-size: 11px !important;
}

/* ── Sider 内 Tabs 填满剩余高度 ── */
.editor-mode-tabs {
  overflow: hidden;
}

.panel-sider :deep(.n-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.panel-sider :deep(.n-tabs-pane-wrapper) {
  flex: 1;
  min-height: 0;
}

.panel-sider :deep(.n-tab-pane) {
  height: 100%;
}

.sider-controls {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 提交按钮推到最底部 */
.sider-controls .mt-2:last-child {
  margin-top: auto;
}

/* 无图片时的提示文字居中 */
.no-image-hint {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--text-tertiary);
}

.editor-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.workspace-section {
  display: flex;
  flex-direction: column;
  background: var(--bg-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  min-height: 200px;
  flex: 1;
}

.workspace-section:only-child {
  flex: 1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: transparent;
}

.section-title {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
}

.canvas-container, .result-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  background:
    linear-gradient(45deg, var(--gray-100) 25%, transparent 25%),
    linear-gradient(-45deg, var(--gray-100) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, var(--gray-100) 75%),
    linear-gradient(-45deg, transparent 75%, var(--gray-100) 75%);
  background-size: 20px 20px;
  background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  background-color: var(--bg-subtle);
  min-height: 200px;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 320px;
  color: var(--text-secondary);
  gap: 14px;
}
.empty-icon { font-size: 48px; margin-bottom: 4px; opacity: 0.35; color: var(--brand-400); }
.empty-text { font-size: 14px; color: var(--gray-400); }

.generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  padding: 40px;
}

.history-card {
  cursor: pointer;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.2s var(--ease-out);
}
.history-card:hover {
  border-color: var(--brand-500);
  transform: translateY(-2px);
}

.history-img {
  width: 100%;
  height: 100px;
  display: block;
}

</style>
