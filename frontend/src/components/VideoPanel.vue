<template>
  <div class="video-panel">
    <div class="panel-layout">
      <!-- 左侧：配置区 -->
      <div class="panel-sider">
        <div class="sider-header">
          <h3>视频生成</h3>
        </div>

        <n-alert
          v-if="!providerStore.hasConfiguredVideoProvider"
          type="warning"
          class="mb-3"
          :show-icon="false"
        >
          <span>请先配置生成视频能力</span>
          <n-button text type="primary" @click="configStore.showConfigModal = true">
            立即配置
          </n-button>
        </n-alert>

        <n-tabs v-model:value="activeTab" type="line" animated>
        <n-tab-pane name="text2video" tab="文生视频">
          <n-form label-placement="left" label-width="60">
            <n-form-item label="提示词">
              <n-input
                v-model:value="videoStore.prompt"
                type="textarea"
                placeholder="描述你想要的视频画面，例如：一只金毛犬在海滩上奔跑，阳光明媚，镜头跟随..."
                :rows="4"
                :disabled="videoStore.status === 'generating'"
                :maxlength="4000"
                show-count
                @keydown.enter.ctrl="handleGenerate"
              />
            </n-form-item>

            <n-form-item label="负面词">
              <n-input
                v-model:value="videoStore.negativePrompt"
                type="textarea"
                placeholder="不想要的内容（可选）..."
                :rows="2"
                :disabled="videoStore.status === 'generating'"
              />
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <n-tab-pane name="image2video" tab="图生视频">
          <n-form label-placement="left" label-width="60">
            <n-form-item label="源图片">
              <div class="image-upload-area">
                <n-upload
                  accept="image/*"
                  :show-file-list="false"
                  :custom-request="handleImageUpload"
                >
                  <n-button>上传图片</n-button>
                </n-upload>
                <div v-if="videoStore.sourceImage" class="preview-container">
                  <img :src="videoStore.sourceImage" alt="源图片" class="preview-image" />
                  <n-button size="small" quaternary circle @click="videoStore.setSourceImage(null)">
                    <template #icon>
                      <n-icon><CloseOutline /></n-icon>
                    </template>
                  </n-button>
                </div>
              </div>
            </n-form-item>

            <n-form-item label="提示词">
              <n-input
                v-model:value="videoStore.prompt"
                type="textarea"
                placeholder="描述图片如何动起来，例如：人物微笑眨眼，头发随风飘动..."
                :rows="3"
                :disabled="videoStore.status === 'generating'"
                :maxlength="4000"
                show-count
              />
            </n-form-item>
          </n-form>
        </n-tab-pane>

        <n-tab-pane name="template" tab="模板向导">
          <VideoTemplateWizard
            @apply="handleApplyTemplate"
          />
        </n-tab-pane>
      </n-tabs>

      <n-collapse class="mt-3">
        <n-collapse-item name="shot">
          <template #header>
            <n-space align="center" :size="4">
              <n-icon :component="Film" />
              <span>镜头语言</span>
            </n-space>
          </template>
          <n-space vertical>
            <n-form-item label="景别" label-placement="left">
              <n-select
                v-model:value="videoStore.shotType"
                :options="shotTypeOptions"
                placeholder="选择景别"
                clearable
              />
            </n-form-item>
            <n-form-item label="运镜" label-placement="left">
              <n-select
                v-model:value="videoStore.cameraMovement"
                :options="movementOptions"
                placeholder="选择运镜方式"
                clearable
              />
            </n-form-item>
            <n-form-item label="视角" label-placement="left">
              <n-select
                v-model:value="videoStore.cameraAngle"
                :options="angleOptions"
                placeholder="选择视角"
                clearable
              />
            </n-form-item>
          </n-space>
        </n-collapse-item>
      </n-collapse>

      <n-grid :cols="3" :x-gap="12" class="mt-3">
        <n-gi>
          <n-form-item label="模型" label-placement="left">
            <n-select
              v-model:value="videoStore.model"
              :options="modelOptions"
              :disabled="videoStore.status === 'generating'"
              size="small"
            />
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item label="时长" label-placement="left">
            <n-select
              v-model:value="videoStore.duration"
              :options="durationOptions"
              :disabled="videoStore.status === 'generating'"
              size="small"
            />
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item label="分辨率" label-placement="left">
            <n-select
              v-model:value="videoStore.resolution"
              :options="resolutionOptions"
              :disabled="videoStore.status === 'generating'"
              size="small"
            />
          </n-form-item>
        </n-gi>
      </n-grid>

        <n-form-item class="mt-3">
          <n-space vertical style="width: 100%">
            <n-button
              type="primary"
              block
              size="large"
              :loading="videoStore.status === 'generating'"
              :disabled="!canGenerate"
              @click="handleGenerate"
            >
              {{ videoStore.status === 'generating' ? `生成中 ${Math.round(videoStore.progress)}%` : '生成视频' }}
            </n-button>
          </n-space>
        </n-form-item>
      </div> <!-- /panel-sider -->

      <!-- 右侧：生成结果区 -->
      <div class="panel-content">
        <n-progress
          v-if="videoStore.status === 'generating'"
          type="line"
          :percentage="Math.round(videoStore.progress)"
          :show-indicator="true"
          class="mb-3"
        />

        <n-alert
          v-if="videoStore.error"
          type="error"
          class="mb-3"
          :show-icon="false"
          closable
          @close="videoStore.error = null"
        >
          {{ videoStore.error }}
        </n-alert>

        <div v-if="videoStore.lastVideo" class="video-result-container">
          <div class="result-header">
            <span class="result-title">生成结果</span>
          </div>
        <video
          :src="videoStore.lastVideo"
          controls
          class="result-video"
          @error="handleVideoError"
        />
        <n-space class="mt-2">
          <n-button size="small" @click="handleDownload">
            下载视频
          </n-button>
          <n-button size="small" @click="handleCopyPrompt">
            复制提示词
          </n-button>
          <n-button size="small" @click="videoStore.clearAll">
            清空
          </n-button>
        </n-space>
      </div>
        <div v-else class="empty-state">
          <div class="empty-illustration">
            <div class="empty-glow"></div>
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <defs>
                <linearGradient id="videoEmptyGrad" x1="0" y1="0" x2="80" y2="80">
                  <stop offset="0%" stop-color="#4f7df3" stop-opacity="0.3"/>
                  <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0.15"/>
                </linearGradient>
              </defs>
              <rect x="12" y="24" width="56" height="40" rx="10" stroke="url(#videoEmptyGrad)" stroke-width="1.5" stroke-dasharray="4 4"/>
              <polygon points="34,36 34,52 48,44" fill="#4f7df3" opacity="0.15"/>
              <circle cx="24" cy="38" r="3" fill="#8b5cf6" opacity="0.1"/>
              <circle cx="56" cy="36" r="3" fill="#4f7df3" opacity="0.08"/>
              <path d="M40 10l-5 10h10l-5 10" stroke="#8b5cf6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.2"/>
            </svg>
          </div>
          <div class="empty-title">准备创作一段视频</div>
          <div class="empty-hint">选择文生视频或图生视频，输入提示词即可生成</div>
          <div class="empty-shortcut">
            <span class="shortcut-key">⌘ ↵</span>
            <span class="shortcut-label">快速生成</span>
          </div>
        </div>
      </div> <!-- /panel-content -->
    </div> <!-- /panel-layout -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'
import { Film } from 'lucide-vue-next'
import { useVideoStore } from '../stores/video'
import { useConfigStore } from '../stores/config'
import { useProviderStore } from '../stores/provider'
import { shotTypes, cameraMovements, cameraAngles, videoDurations, videoResolutions } from '../data/shotLanguage'
import { videoModels } from '../data/videoTemplates'
import VideoTemplateWizard from './VideoTemplateWizard.vue'
import type { UploadCustomRequestOptions } from 'naive-ui'

const message = useMessage()
const videoStore = useVideoStore()
const configStore = useConfigStore()
const providerStore = useProviderStore()

const activeTab = ref('text2video')

const shotTypeOptions = computed(() =>
  shotTypes.map(s => ({ label: s.name, value: s.id }))
)

const movementOptions = computed(() =>
  cameraMovements.map(m => ({ label: m.name, value: m.id }))
)

const angleOptions = computed(() =>
  cameraAngles.map(a => ({ label: a.name, value: a.id }))
)

const modelOptions = computed(() =>
  videoModels.map(m => ({ label: m.label, value: m.value }))
)

const durationOptions = computed(() =>
  videoDurations.map(d => ({ label: d.label, value: d.value }))
)

const resolutionOptions = computed(() =>
  videoResolutions.map(r => ({ label: r.label, value: r.value }))
)

const canGenerate = computed(() => {
  if (!videoStore.prompt.trim()) return false
  if (!providerStore.hasConfiguredVideoProvider) return false
  if (videoStore.status === 'generating') return false
  return true
})

function handleImageUpload({ file }: UploadCustomRequestOptions) {
  const reader = new FileReader()
  reader.onload = (e) => {
    videoStore.setSourceImage(e.target?.result as string)
  }
  reader.readAsDataURL(file.file as File)
}

async function handleGenerate() {
  if (!canGenerate.value) return
  
  const success = await videoStore.generate()
  if (success) {
    message.success('视频生成成功')
  }
}

function handleApplyTemplate(prompt: string) {
  videoStore.prompt = prompt
  activeTab.value = 'text2video'
}

function handleDownload() {
  if (!videoStore.lastVideo) return
  
  const link = document.createElement('a')
  link.href = videoStore.lastVideo
  link.download = `video_${Date.now()}.mp4`
  link.click()
}

async function handleCopyPrompt() {
  try {
    await navigator.clipboard.writeText(videoStore.prompt)
    message.success('提示词已复制')
  } catch {
    message.error('复制失败')
  }
}

function handleVideoError() {
  message.error('视频加载失败')
}
</script>

<style scoped>
.video-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

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

.sider-header h3 {
  margin: 0 0 20px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
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
.empty-illustration {
  position: relative;
  color: var(--gray-300);
  margin-bottom: 4px;
}
.empty-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(79, 125, 243, 0.12) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.empty-illustration svg {
  position: relative;
  z-index: 1;
}
.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-700);
  letter-spacing: -0.2px;
}
.empty-hint {
  font-size: 13px;
  color: var(--gray-400);
}
.empty-shortcut {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--gray-400);
}
.shortcut-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 20px;
  padding: 0 5px;
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: 5px;
  font-size: 11px;
  font-family: inherit;
  color: var(--gray-500);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.shortcut-label { color: var(--gray-400); }

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-title {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
}

.video-result-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.image-upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  background: var(--bg-subtle);
  border: 1.5px dashed var(--gray-300);
  border-radius: var(--radius-md);
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.image-upload-area:hover {
  border-color: var(--brand-500);
  background: var(--brand-50);
}

.preview-container {
  position: relative;
  display: inline-block;
}

.preview-image {
  width: 88px;
  height: 88px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 2px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.video-result { width: 100%; }

.result-video {
  width: 100%;
  max-height: 420px;
  border-radius: var(--radius-md);
  background: var(--gray-900);
  box-shadow: var(--shadow-lg);
}

/* 面板内生成按钮推到最底部 */
.panel-sider > :deep(.n-form-item:last-child) {
  margin-top: auto !important;
  margin-bottom: 0;
}

.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mb-3 { margin-bottom: 12px; }
</style>
