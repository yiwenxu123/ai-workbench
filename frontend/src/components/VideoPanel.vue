<template>
  <div class="video-panel">
    <div class="panel-layout">
      <!-- 左侧：配置区 -->
      <div class="panel-sider">
        <div class="sider-header">
          <h3>视频生成</h3>
        </div>

        <div class="panel-sider-scroll">
        <div v-if="!canUseVideo" class="status-banner mb-3" role="status">
          <div class="status-banner__icon">
            <n-icon :component="AlertCircle" size="16" />
          </div>
          <div class="status-banner__content">
            <div class="font-semibold">请先配置生成视频能力</div>
            <div class="text-xs mt-1" style="opacity: 0.85">配置视频生成供应商以解锁文生视频/图生视频</div>
          </div>
          <n-button class="status-banner__action" type="primary" size="small" @click="configStore.showConfigModal = true">
            立即配置
          </n-button>
        </div>

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

      <n-collapse class="mt-3" :default-expanded-names="['shot']">
        <n-collapse-item name="shot">
          <template #header>
            <n-space align="center" :size="4">
              <n-icon :component="Film" />
              <span>镜头语言</span>
              <n-tag v-if="videoStore.cameraMovement" size="small" type="primary" round>
                已选运镜
              </n-tag>
            </n-space>
          </template>
          <n-space vertical size="medium">
            <n-tabs v-model:value="shotPanelTab" type="line" size="small">
              <n-tab-pane name="selector" tab="手动选择">
                <MovementSelector
                  v-model:model-value="videoStore.cameraMovement"
                  @apply-example="handleApplyExample"
                />
              </n-tab-pane>
              <n-tab-pane name="wizard" tab="智能推荐">
                <MovementWizard
                  @apply="handleWizardApply"
                  @apply-combo="handleApplyCombo"
                />
              </n-tab-pane>
            </n-tabs>

            <n-grid :cols="2" :x-gap="10">
              <n-gi>
                <n-form-item label="景别" label-placement="left">
                  <n-select
                    v-model:value="videoStore.shotType"
                    :options="shotTypeOptions"
                    placeholder="选择景别"
                    clearable
                    size="small"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="视角" label-placement="left">
                  <n-select
                    v-model:value="videoStore.cameraAngle"
                    :options="angleOptions"
                    placeholder="选择视角"
                    clearable
                    size="small"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="速度" label-placement="left">
                  <n-select
                    v-model:value="videoStore.movementSpeed"
                    :options="speedOptions"
                    placeholder="运镜速度"
                    clearable
                    size="small"
                  />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="情绪" label-placement="left">
                  <n-select
                    v-model:value="videoStore.emotionTag"
                    :options="emotionOptions"
                    placeholder="情绪氛围"
                    clearable
                    size="small"
                  />
                </n-form-item>
              </n-gi>
            </n-grid>

            <n-alert v-if="videoStore.promptQuality.suggestions.length > 0" type="info" :show-icon="true" size="small">
              <template #header>提示词建议</template>
              <ul style="margin: 0; padding-left: 18px; font-size: 12px;">
                <li v-for="(s, i) in videoStore.promptQuality.suggestions.slice(0, 2)" :key="i">
                  {{ s }}
                </li>
              </ul>
            </n-alert>
          </n-space>
        </n-collapse-item>
      </n-collapse>

      <n-collapse class="mt-3">
        <n-collapse-item name="storyboard">
          <template #header>
            <n-space align="center" :size="4">
              <n-icon :component="Clapperboard" />
              <span>分镜脚本</span>
              <n-tag v-if="videoStore.storyboard.length > 0" size="small" type="success" round>
                {{ videoStore.storyboard.length }} 镜头
              </n-tag>
            </n-space>
          </template>
          <ShotStoryboard />
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

        </div> <!-- /panel-sider-scroll -->

        <!-- 生成按钮：固定在面板底部 -->
        <div class="panel-sider-footer">
          <n-button
            type="primary"
            block
            size="large"
            class="generate-btn"
            :loading="videoStore.status === 'generating'"
            :disabled="!canGenerate"
            @click="handleGenerate"
          >
            {{ videoStore.status === 'generating' ? `生成中 ${Math.round(videoStore.progress)}%` : '生成视频' }}
          </n-button>
        </div>
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

        <div v-if="videoStore.error" class="error-card mb-3">
          <div class="error-title">{{ getErrorInfo(videoStore.error).title }}</div>
          <div class="error-message">{{ getErrorInfo(videoStore.error).message }}</div>
          <n-space class="mt-2">
            <n-button v-if="getErrorInfo(videoStore.error).action" size="tiny" type="primary" @click="videoStore.error = null">
              {{ getErrorInfo(videoStore.error).action }}
            </n-button>
            <n-button size="tiny" quaternary @click="videoStore.error = null">
              关闭
            </n-button>
          </n-space>
        </div>

        <div v-if="videoStore.lastVideo" class="video-result-container">
          <div class="result-header">
            <span class="result-title">生成结果</span>
            <span v-if="videoStore.lastGenerateParams?.generateTime" class="result-time">
              {{ formatTime(videoStore.lastGenerateParams.generateTime) }}
            </span>
          </div>
        <video
          :src="videoStore.lastVideo"
          controls
          class="result-video"
          :poster="videoStore.lastThumbnail || undefined"
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

        <n-collapse class="mt-3" :default-expanded-names="[]">
          <n-collapse-item name="params">
            <template #header>
              <n-space align="center" :size="4">
                <n-icon :component="Settings" />
                <span>生成参数</span>
              </n-space>
            </template>
            <div v-if="videoStore.lastGenerateParams" class="params-detail">
              <div class="params-grid">
                <div class="param-item">
                  <span class="param-label">模型</span>
                  <span class="param-value">{{ videoStore.lastGenerateParams.model }}</span>
                </div>
                <div class="param-item">
                  <span class="param-label">时长</span>
                  <span class="param-value">{{ videoStore.lastGenerateParams.duration }} 秒</span>
                </div>
                <div class="param-item">
                  <span class="param-label">分辨率</span>
                  <span class="param-value">{{ videoStore.lastGenerateParams.resolution }}</span>
                </div>
                <div v-if="videoStore.lastGenerateParams.shotType" class="param-item">
                  <span class="param-label">景别</span>
                  <span class="param-value">{{ getShotTypeName(videoStore.lastGenerateParams.shotType) }}</span>
                </div>
                <div v-if="videoStore.lastGenerateParams.cameraMovement" class="param-item">
                  <span class="param-label">运镜</span>
                  <span class="param-value">{{ getMovementName(videoStore.lastGenerateParams.cameraMovement) }}</span>
                </div>
                <div v-if="videoStore.lastGenerateParams.cameraAngle" class="param-item">
                  <span class="param-label">角度</span>
                  <span class="param-value">{{ getAngleName(videoStore.lastGenerateParams.cameraAngle) }}</span>
                </div>
                <div v-if="videoStore.lastGenerateParams.movementSpeed" class="param-item">
                  <span class="param-label">速度</span>
                  <span class="param-value">{{ getSpeedName(videoStore.lastGenerateParams.movementSpeed) }}</span>
                </div>
                <div v-if="videoStore.lastGenerateParams.emotionTag" class="param-item">
                  <span class="param-label">情绪</span>
                  <span class="param-value">{{ getEmotionLabel(videoStore.lastGenerateParams.emotionTag) }}</span>
                </div>
              </div>
              <div v-if="videoStore.lastGenerateParams.negativePrompt" class="param-section">
                <span class="param-label">负面提示词</span>
                <p class="param-text">{{ videoStore.lastGenerateParams.negativePrompt }}</p>
              </div>
              <div v-if="videoStore.lastGenerateParams.enhancedPrompt" class="param-section">
                <span class="param-label">增强后提示词</span>
                <p class="param-text enhanced">{{ videoStore.lastGenerateParams.enhancedPrompt }}</p>
              </div>
            </div>
          </n-collapse-item>
        </n-collapse>
      </div>
        <div v-else>
          <EmptyState
            title="准备创作一段视频"
            hint="选择文生视频或图生视频，输入提示词即可生成"
            :shortcut="{ key: '⌘ ↵', label: '快速生成' }"
          />
        </div>
      </div> <!-- /panel-content -->
    </div> <!-- /panel-layout -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'
import { Film, AlertCircle, Clapperboard, Settings } from 'lucide-vue-next'
import { useVideoStore } from '../stores/video'
import { useConfigStore } from '../stores/config'
import { useProviderStore } from '../stores/provider'
import {
  shotTypes,
  cameraAngles,
  videoDurations,
  videoResolutions,
  movementSpeeds,
  emotionTags,
  getCameraMovementById,
} from '../data/shotLanguage'
import { useModelManifest } from '../composables/useModelManifest'
import { useCapabilityReady } from '../composables/useCapabilityReady'
import { getErrorInfo } from '../utils/errorMessages'
import VideoTemplateWizard from './VideoTemplateWizard.vue'
import MovementSelector from './MovementSelector.vue'
import MovementWizard from './MovementWizard.vue'
import ShotStoryboard from './ShotStoryboard.vue'
import EmptyState from './common/EmptyState.vue'
import type { UploadCustomRequestOptions } from 'naive-ui'

const message = useMessage()
const videoStore = useVideoStore()
const configStore = useConfigStore()
const providerStore = useProviderStore()
const { canUseVideo } = useCapabilityReady()
const { getVideoModels, getModel, verificationLabel } = useModelManifest()

const activeTab = ref('text2video')
const shotPanelTab = ref('selector')

const shotTypeOptions = computed(() =>
  shotTypes.map(s => ({ label: s.name, value: s.id }))
)

const angleOptions = computed(() =>
  cameraAngles.map(a => ({ label: a.name, value: a.id }))
)

const speedOptions = computed(() =>
  movementSpeeds.map(s => ({ label: s.label, value: s.value }))
)

const emotionOptions = computed(() =>
  emotionTags.map(e => ({ label: e.label, value: e.value }))
)

const modelOptions = computed(() => {
  const fromManifest = getVideoModels()
  if (fromManifest.length > 0) {
    return fromManifest.map((m) => ({
      label: `${m.label}${verificationLabel(m.value)}`,
      value: m.value,
    }))
  }
  return [
    { label: '可灵 V1', value: 'kling-v1' },
    { label: '可灵 V1.5', value: 'kling-v1-5' },
    { label: '即梦 V1', value: 'jimeng-v1' },
    { label: 'Runway Gen-3', value: 'runway-gen3' },
  ]
})

const selectedModelManifest = computed(() =>
  videoStore.model ? getModel(videoStore.model) : undefined
)

const durationOptions = computed(() => {
  const durations = selectedModelManifest.value?.durations
  if (durations && durations.length > 0) {
    const labels: Record<number, string> = { 3: '3秒', 5: '5秒', 10: '10秒', 15: '15秒', 30: '30秒', 60: '60秒' }
    return durations.map(d => ({ label: labels[d] ?? `${d}秒`, value: d }))
  }
  return videoDurations.map(d => ({ label: d.label, value: d.value }))
})

const resolutionOptions = computed(() => {
  const resolutions = selectedModelManifest.value?.resolutions
  if (resolutions && resolutions.length > 0) {
    const labels: Record<string, string> = { '720p': '720P', '1080p': '1080P', '4k': '4K' }
    return resolutions.map(r => ({ label: labels[r] ?? r, value: r }))
  }
  return videoResolutions.map(r => ({ label: r.label, value: r.value }))
})

watch(() => videoStore.model, (newModel) => {
  const manifest = newModel ? getModel(newModel) : undefined
  const durations = manifest?.durations
  const resolutions = manifest?.resolutions

  if (durations?.length && !durations.includes(videoStore.duration)) {
    videoStore.duration = durations[0]
  }
  if (resolutions?.length && !resolutions.includes(videoStore.resolution)) {
    videoStore.resolution = resolutions[0]
  }
})

const canGenerate = computed(() => {
  if (!videoStore.prompt.trim()) return false
  if (!canUseVideo.value) return false
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

function handleApplyExample(prompt: string) {
  videoStore.prompt = prompt
  activeTab.value = 'text2video'
  message.success('已应用示例提示词')
}

function handleWizardApply(movement: any) {
  videoStore.applyMovementWithRecommendedSpeed(movement)
  message.success('已应用运镜方案')
}

function handleApplyCombo(comboId: string) {
  message.info(`场景组合功能即将上线：${comboId}`)
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

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getShotTypeName(id?: string): string {
  if (!id) return ''
  return shotTypes.find((t) => t.id === id)?.name || id
}

function getMovementName(id?: string): string {
  if (!id) return ''
  return getCameraMovementById(id as any)?.name || id
}

function getAngleName(id?: string): string {
  if (!id) return ''
  return cameraAngles.find((a) => a.id === id)?.name || id
}

function getSpeedName(id?: string): string {
  if (!id) return ''
  return movementSpeeds.find((s) => s.value === id)?.label || id
}

function getEmotionLabel(id?: string): string {
  if (!id) return ''
  return emotionTags.find((e) => e.value === id)?.label || id
}
</script>

<style scoped>
.video-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
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

/* ── Panel Sider Footer (Sticky) ── */
.panel-sider-footer {
  flex-shrink: 0;
  padding: 12px 0 0;
  border-top: 1px solid var(--border-light);
  background: var(--bg-card);
}

.generate-btn {
  height: 44px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-md) !important;
}

.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mb-3 { margin-bottom: 12px; }

/* ── 错误卡片 ── */
.error-card {
  padding: var(--space-3) 14px;
  background: var(--error-50);
  border: 1px solid var(--error-100);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
}

.error-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--error-600);
  margin-bottom: var(--space-1);
}

.error-message {
  font-size: var(--font-size-sm);
  color: var(--error-600);
  opacity: 0.85;
  line-height: var(--line-height-base);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-1);
}

.result-time {
  font-size: 12px;
  color: var(--text-color-3);
}

.params-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.param-label {
  font-size: 12px;
  color: var(--text-color-3);
}

.param-value {
  font-size: 13px;
  color: var(--text-color-1);
  font-weight: 500;
}

.param-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
}

.param-text {
  font-size: 13px;
  color: var(--text-color-2);
  line-height: 1.5;
  margin: 0;
  word-break: break-all;
}

.param-text.enhanced {
  color: var(--primary-color);
  background: rgba(59, 130, 246, 0.05);
  padding: 8px;
  border-radius: 4px;
}
</style>
