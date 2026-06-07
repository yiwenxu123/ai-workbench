<template>
  <div class="generate-panel">
    <div class="panel-layout">
      <!-- 左侧：配置区 -->
      <div class="panel-sider">
        <div class="panel-sider-scroll">
        <div class="sider-header">
          <div class="sider-header-row">
            <h3>图像生成</h3>
            <div class="provider-stripe">
              <template v-if="activeImageProviders.length > 0">
                <span
                  v-for="p in activeImageProviders"
                  :key="p.id"
                  class="stripe-dot"
                  :class="stripeDotClass(p.status)"
                  :title="`${p.name}: ${statusLabel(p.status)}${p.latency ? ' (' + p.latency + 'ms)' : ''}`"
                />
              </template>
              <span v-else class="stripe-dot stripe-none" title="未配置供应商" />
            </div>
          </div>
        </div>

        <!-- ── 快捷创作模板区 ── -->
        <div class="quick-create">
          <div class="qc-header" @click="quickCreateOpen = !quickCreateOpen">
            <div class="qc-header-left">
              <n-icon :component="Zap" size="16" />
              <span class="qc-title">快捷创作</span>
              <span class="qc-desc">选场景→描述需求→自动填写提示词</span>
            </div>
            <n-button text size="tiny" class="qc-toggle">
              {{ quickCreateOpen ? '收起' : '展开' }}
              <n-icon :component="quickCreateOpen ? ChevronUp : ChevronDown" size="14" />
            </n-button>
          </div>

          <n-collapse-transition :show="quickCreateOpen">
            <div class="qc-body">
              <!-- 任务卡片：3列2行 -->
              <div class="qc-grid">
                <button
                  v-for="task in quickTasks"
                  :key="task.id"
                  type="button"
                  class="qc-card"
                  :class="{ selected: selectedQuickTask?.id === task.id }"
                  @click="selectQuickTask(task)"
                >
                  <n-icon :component="task.icon" size="20" class="qc-card-icon" />
                  <div class="qc-card-text">
                    <span class="qc-card-title">{{ task.title }}</span>
                    <span class="qc-card-desc">{{ task.description }}</span>
                  </div>
                </button>
              </div>

              <!-- 选中任务后的输入区 -->
              <div v-if="selectedQuickTask" class="qc-form">
                <div class="qc-form-field">
                  <div class="qc-form-label">{{ selectedQuickTask.question }}</div>
                  <n-input
                    v-model:value="quickTaskInput"
                    type="textarea"
                    :rows="2"
                    :placeholder="selectedQuickTask.placeholder"
                    size="small"
                  />
                </div>

                <!-- 图像任务的比例选择 -->
                <div v-if="selectedQuickTask.type === 'image'" class="qc-ratio-row">
                  <n-radio-group v-model:value="quickTaskRatio" size="small">
                    <n-radio-button value="1:1">1:1</n-radio-button>
                    <n-radio-button value="3:4">3:4</n-radio-button>
                    <n-radio-button value="4:3">4:3</n-radio-button>
                    <n-radio-button value="16:9">16:9</n-radio-button>
                    <n-radio-button value="9:16">9:16</n-radio-button>
                  </n-radio-group>
                </div>

                <!-- 操作行：AI调优开关 + 应用按钮 -->
                <div class="qc-actions">
                  <div class="qc-ai-toggle">
                    <n-icon :component="Sparkles" size="14" />
                    <span class="qc-ai-label">AI 智能调优</span>
                    <n-switch v-model:value="useQuickAI" size="small" @update:value="onQuickAIChange" />
                  </div>
                  <n-button
                    size="small"
                    type="primary"
                    :disabled="!quickTaskInput.trim() || generatorStore.status === 'generating'"
                    :loading="quickAIWorking || generatorStore.status === 'generating'"
                    @click="applyQuickTask"
                  >
                    {{ selectedQuickTask.type === 'video' ? '生成视频' : selectedQuickTask.type === 'edit' ? '前往图片编辑' : '生成图片' }}
                  </n-button>
                </div>

                <!-- AI 调优结果 -->
                <div v-if="useQuickAI && quickAIResult && !quickAIWorking" class="qc-ai-result">
                  <n-alert type="success" :show-icon="false" size="small">
                    <div class="qc-ai-result-text">{{ quickAIResult.optimizedPromptCN || quickAIResult.explanation || '已优化' }}</div>
                  </n-alert>
                  <n-button size="tiny" type="primary" ghost style="margin-top:6px" @click="applyAIResult">
                    应用到主表单
                  </n-button>
                </div>

                <!-- 模板预览 -->
                <div v-if="!useQuickAI && quickTaskInput.trim()" class="qc-preview">
                  <div class="qc-preview-label">模板预览：</div>
                  <div class="qc-preview-text">{{ generatedQuickPrompt }}</div>
                </div>

<div v-if="selectedQuickTask.type === 'image'" class="qc-hint">
  <n-icon :component="Info" size="12" />
  <span>提示词已实时填入主表单，你可继续调整</span>
</div>
              </div>
            </div>
          </n-collapse-transition>
        </div>
        <!-- /快捷创作模板区 -->

        <n-alert
          v-if="!providerStore.hasConfiguredImageProvider"
          type="warning"
          class="mb-3"
          :show-icon="false"
        >
          <span>请先配置生成图片能力</span>
          <n-button text type="primary" @click="configStore.showConfigModal = true">
            立即配置
          </n-button>
        </n-alert>

        <n-form label-placement="left" label-width="60">
          <div class="prompt-label">提示词</div>
          <div class="prompt-field">
            <n-input
              v-model:value="generatorStore.prompt"
              type="textarea"
              placeholder="输入描述你想要的图片..."
              :rows="5"
              :disabled="generatorStore.status === 'generating'"
              :maxlength="4000"
              show-count
              @keydown.enter.ctrl="handleGenerate"
              @input="onMainPromptInput"
            />
            <PromptElementTagger :prompt="generatorStore.prompt" :min-length="3" />
            <div class="term-suggestions" v-if="termSuggestions.length > 0">
              <n-button text size="tiny" class="term-toggle" @click="termSuggestOpen = !termSuggestOpen">
                <n-icon :component="termSuggestOpen ? ChevronUp : ChevronDown" size="12" />
                <span class="suggestions-label">推荐术语 ({{ termSuggestions.length }})</span>
              </n-button>
              <n-collapse-transition :show="termSuggestOpen">
                <div class="term-tags">
                  <template v-for="s in visibleSuggestions" :key="s.term.id">
                    <n-tag
                      size="tiny"
                      :bordered="false"
                      :style="{ backgroundColor: getCategoryColor(s.term.category) + '10', color: getCategoryColor(s.term.category), cursor: 'pointer' }"
                      @click="insertTermSuggestion(s.term)"
                    >
                      + {{ s.term.name }}
                    </n-tag>
                  </template>
                  <n-button v-if="termSuggestions.length > 5 && !showAllTerms" size="tiny" text type="primary" @click="showAllTerms = true">
                    +{{ termSuggestions.length - 5 }} 个更多
                  </n-button>
                </div>
              </n-collapse-transition>
            </div>
        </div>

        <!-- 生成按钮：紧跟在提示词下方，无需滚动 -->
        <n-button
          type="primary"
          block
          size="large"
          class="generate-btn"
          :loading="generatorStore.status === 'generating'"
          :disabled="!generatorStore.prompt.trim() || !providerStore.hasConfiguredImageProvider"
          @click="generatorStore.generate()"
        >
          <template #icon v-if="generatorStore.status !== 'generating'">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </template>
          {{ generatorStore.status === 'generating' ? (generatorStore.stageLabel || '生成中') + '...' : '生成图片' }}
        </n-button>

        <!-- 折叠参数区：负面词/模型/尺寸/优化器 -->
        <n-collapse v-model:expanded-names="settingsCollapseOpen">
          <n-collapse-item name="settings">
            <template #header>
                <n-space align="center" :size="4">
                  <n-icon :component="Settings" />
                  <span>更多参数（负面词、模型、尺寸）</span>
                </n-space>
              </template>
            <div class="prompt-optimizer-section mb-3">
              <div class="section-header">
                <n-space align="center" :size="4">
                  <n-icon :component="Sparkles" />
                  <n-text strong depth="3" style="font-size: 13px">AI 提示词优化</n-text>
                </n-space>
                <n-button size="tiny" @click="showOptimizer = !showOptimizer">
                  {{ showOptimizer ? '收起' : '展开' }}
                </n-button>
              </div>
              <n-collapse-transition :show="showOptimizer">
                <PromptOptimizer
                  v-model:prompt="generatorStore.prompt"
                  @apply="handleApplyOptimize"
                />
              </n-collapse-transition>
            </div>

            <n-form-item label="负面词">
              <n-input
                v-model:value="generatorStore.negativePrompt"
                type="textarea"
                placeholder="不想要的内容（可选）..."
                :rows="2"
                :disabled="generatorStore.status === 'generating'"
              />
            </n-form-item>

            <PromptAnalyzer
              :prompt="generatorStore.prompt"
              v-if="generatorStore.prompt.trim()"
              @insert="handleQuickInsert"
            />

            <n-form-item label="模型">
              <n-select
                v-model:value="generatorStore.model"
                :options="modelOptions"
                :disabled="generatorStore.status === 'generating'"
                @update:value="handleModelChange"
              />
              <template #feedback>
                <div class="model-status-bar">
                  <!-- 当前默认图片 Provider 的连接状态 -->
                  <span
                    v-if="defaultImageProvider"
                    class="provider-status"
                    :class="statusClass(defaultImageProvider.status)"
                  >
                    <span class="status-dot" />
                    {{ defaultImageProvider.name }}:
                    {{ statusLabel(defaultImageProvider.status) }}
                    <span v-if="defaultImageProvider.latency" class="latency">
                      · {{ defaultImageProvider.latency }}ms
                    </span>
                  </span>
                  <span v-else class="provider-status status-inactive">
                    <span class="status-dot" />
                    尚未配置图像生成供应商
                  </span>
                  <n-button
                    size="tiny"
                    text
                    type="primary"
                    @click="configStore.showConfigModal = true"
                  >
                    配置
                  </n-button>
                </div>
              </template>
            </n-form-item>

            <n-form-item label="尺寸">
              <div class="size-field">
                <div class="ratio-presets">
                  <n-button
                    v-for="r in RatioList"
                    :key="r.ratio"
                    size="tiny"
                    :type="ratioActive === r.ratio ? 'primary' : 'default'"
                    @click="pickRatio(r.ratio)"
                  >
                    {{ r.label }}
                  </n-button>
                </div>
                <n-select
                  v-model:value="generatorStore.size"
                  :options="sizeOptions"
                  :disabled="generatorStore.status === 'generating'"
                />
              </div>
            </n-form-item>

            <n-alert
              v-if="currentModelNote"
              type="info"
              class="mb-3"
              :show-icon="false"
              size="small"
            >
              {{ currentModelNote }}
            </n-alert>

            <!-- 高级参数：仅对兼容模型显示 -->
            <n-collapse-item v-if="supportsAdvancedParams" name="advanced">
              <template #header>
                <n-space align="center" :size="4">
                  <n-icon :component="Zap" />
                  <span>高级参数（Seed、步数）</span>
                </n-space>
              </template>
              <n-grid :cols="3" :x-gap="12">
                <n-gi>
                  <n-form-item label="Seed" label-placement="top">
                    <n-input-number
                      v-model:value="generatorStore.seed"
                      placeholder="随机"
                      :min="0"
                      :max="2147483647"
                      clearable
                      size="small"
                      :show-button="false"
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="步数" label-placement="top">
                    <n-input-number
                      v-model:value="generatorStore.steps"
                      placeholder="默认"
                      :min="1"
                      :max="150"
                      clearable
                      size="small"
                      :show-button="false"
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="CFG" label-placement="top">
                    <n-input-number
                      v-model:value="generatorStore.cfgScale"
                      placeholder="默认"
                      :min="1"
                      :max="30"
                      :step="0.5"
                      clearable
                      size="small"
                      :show-button="false"
                    />
                  </n-form-item>
                </n-gi>
              </n-grid>
            </n-collapse-item>
          </n-collapse-item>
        </n-collapse>

        </n-form>
        </div> <!-- /panel-sider-scroll -->
      </div> <!-- /panel-sider -->

      <!-- 右侧：生成结果区 -->
      <div class="panel-content">
        <div v-if="generatorStore.status === 'generating'" class="generation-feedback mb-3">
          <div class="feedback-pulse"></div>
          <div class="feedback-info">
            <span class="feedback-stage">{{ generatorStore.stageLabel || '准备中' }}</span>
            <span v-if="generatorStore.estimatedRemaining" class="feedback-eta">
              约 {{ Math.ceil(generatorStore.estimatedRemaining) }}s
            </span>
          </div>
          <n-progress
            type="line"
            :percentage="Math.round(generatorStore.progress)"
            :show-indicator="false"
            :height="4"
          />
        </div>

        <div v-if="generatorStore.error" class="error-card mb-3">
          <div class="error-title">{{ getErrorInfo(generatorStore.error).title }}</div>
          <div class="error-message">{{ getErrorInfo(generatorStore.error).message }}</div>
          <n-space v-if="getErrorInfo(generatorStore.error).action" class="mt-2">
            <n-button size="tiny" type="primary" @click="generatorStore.error = null">
              {{ getErrorInfo(generatorStore.error).action }}
            </n-button>
            <n-button size="tiny" quaternary @click="generatorStore.error = null">
              关闭
            </n-button>
          </n-space>
        </div>

        <div v-if="generatorStore.lastImage" class="image-result">
          <div class="result-header">
            <span class="result-title">生成结果</span>
            <n-space>
              <n-tag v-if="generatorStore.generationTime" size="small" type="info">
                耗时: {{ generatorStore.generationTime.toFixed(1) }}s
              </n-tag>
              <n-button size="tiny" quaternary @click="openFullscreen">
                <template #icon><n-icon :component="ExpandOutline" /></template>
                全屏
              </n-button>
            </n-space>
          </div>

        <ImagePreview
          :src="generatorStore.lastImage"
          @loaded="onImageLoaded"
        />

        <div class="image-actions">
          <n-button size="small" type="primary" @click="editImage">
            <template #icon><n-icon :component="CreateOutline" /></template>
            编辑图片
          </n-button>
          <n-button size="small" @click="generateVideo">
            <template #icon><n-icon :component="VideocamOutline" /></template>
            生成视频
          </n-button>
          <n-button size="small" secondary @click="openSaveCaseModal">
            <template #icon><n-icon :component="StarOutline" /></template>
            收录为案例
          </n-button>
        </div>

        <!-- 推荐学习：基于当前提示词匹配相关知识 -->
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
              :key="item.id"
              size="small"
              :bordered="false"
              style="cursor: pointer"
              @click="insertTerm(item)"
            >
              {{ item.content || item.title || item.name }}
            </n-tag>
          </div>
        </div>

        <n-modal v-model:show="showSaveCaseModal" preset="card" style="width: 500px">
          <template #header>
            <n-space align="center" :size="4">
              <n-icon :component="StarOutline" />
              <span>收录为案例</span>
            </n-space>
          </template>
          <n-form label-placement="top">
            <n-form-item label="案例标题">
              <n-input v-model:value="caseTitle" placeholder="例如：白色保温杯电商主图" />
            </n-form-item>
            <n-form-item label="标签（用逗号分隔）">
              <n-input v-model:value="caseTags" placeholder="例如：电商, 产品, 保温杯, 白色" />
            </n-form-item>
            <n-form-item label="使用技巧">
              <n-input
                v-model:value="caseTips"
                type="textarea"
                :rows="3"
                placeholder="分享你的使用心得和技巧..."
              />
            </n-form-item>
            <n-form-item label="将收录的提示词">
              <n-input
                v-model:value="casePrompt"
                type="textarea"
                :rows="3"
              />
            </n-form-item>
          </n-form>
          <template #footer>
            <n-space justify="end">
              <n-button @click="showSaveCaseModal = false">取消</n-button>
              <n-button type="primary" :loading="savingCase" @click="handleSaveCase">
                <template #icon><n-icon :component="CheckCircle2" /></template>
                确认收录
              </n-button>
            </n-space>
          </template>
        </n-modal>

        <QuickActions 
          @fullscreen="openFullscreen" 
          @regenerate="handleGenerate" 
        />
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
      </div> <!-- /panel-content -->
    </div> <!-- /panel-layout -->

    <n-modal 
      v-model:show="showFullscreen" 
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
        <img
          :src="generatorStore.lastImage || ''"
          class="fullscreen-image"
          :style="fullscreenStyle"
          draggable="false"
        />
      </div>
      
      <template #footer>
        <div class="fullscreen-actions">
          <n-button @click="downloadImage">
            <template #icon><n-icon :component="DownloadOutline" /></template>
            下载图片
          </n-button>
          <n-button type="primary" @click="showFullscreen = false">
            关闭 (ESC)
          </n-button>
        </div>
      </template>
    </n-modal>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { NForm, NFormItem, NInput, NInputNumber, NSelect, NButton, NGrid, NGi, NAlert, NIcon, NProgress, NButtonGroup, NTag, NModal, NSpace, NCollapse, NCollapseItem, NCollapseTransition, useMessage } from 'naive-ui'
import { DownloadOutline, RemoveOutline, AddOutline, ExpandOutline, ResizeOutline, CreateOutline, VideocamOutline, StarOutline } from '@vicons/ionicons5'
import { Settings, Sparkles, Zap, BookOpen, CheckCircle2, ShoppingBag, Megaphone, BarChart3, User, Film, Pencil, ChevronDown, ChevronUp, Info } from 'lucide-vue-next'
import { useConfigStore, useGeneratorStore, useProviderStore, useDataStore } from '../stores'
import PromptAnalyzer from './learn/PromptAnalyzer.vue'
import PromptOptimizer from './PromptOptimizer.vue'
import QuickActions from './QuickActions.vue'
import ImagePreview from './common/ImagePreview.vue'
import PromptElementTagger from './common/PromptElementTagger.vue'
import { getModelSizeConfig, isSizeValidForModel } from '../data/modelSizeConfig'
import { useTermSuggestions } from '../composables/useTermSuggestions'
import { useImageZoom } from '../composables/useImageZoom'
import { useKeyboard } from '../composables/useKeyboard'
import { useCreationContext, type CreationScene } from '../composables/useCreationContext'
import { termCategoryConfig, type TermCategory } from '../data/terminology'
import type { TermEntry } from '../data/terminology'
import axios from 'axios'
import { config as appConfig } from '../config'
import { getErrorInfo } from '../utils/errorMessages'
import { optimizePrompt, type OptimizeResult } from '../api/optimize'
import type { Component } from 'vue'

const configStore = useConfigStore()
const generatorStore = useGeneratorStore()
const providerStore = useProviderStore()
const dataStore = useDataStore()
const message = useMessage()

const { suggestions: termSuggestions } = useTermSuggestions(computed(() => generatorStore.prompt))

/* ---- 跨 Tab 创作上下文（useCreationContext） ---- */
const {
  setScene,
  setGenerationResult: setContextGenerationResult,
  addOptimization: addContextOptimization,
} = useCreationContext()

/** QuickTask.id → CreationScene 场景映射 */
const TASK_SCENE_MAP: Record<string, CreationScene> = {
  ecommerce: 'ecommerce',
  'social-poster': 'social',
  presentation: 'presentation',
  portrait: 'portrait',
  'image-to-video': 'video',
  'edit-image': 'edit',
}

/** 监听生成结果，自动写入创作上下文 */
watch(
  () => generatorStore.lastImage,
  (url) => {
    if (url) {
      setContextGenerationResult(url, generatorStore.model, generatorStore.size)
    }
  }
)

const showAllTerms = ref(false)
const termSuggestOpen = ref(false)
const visibleSuggestions = computed(() => {
  const suggestions = termSuggestions.value
  if (showAllTerms.value || suggestions.length <= 5) return suggestions
  return suggestions.slice(0, 5)
})

function getCategoryColor(category: TermCategory): string {
  return termCategoryConfig[category]?.color || '#666'
}

function insertTermSuggestion(term: TermEntry) {
  const current = generatorStore.prompt
  const suffix = current && !current.endsWith('，') && !current.endsWith(',') && !current.endsWith(' ') ? '，' : ''
  generatorStore.prompt = current + suffix + term.name
}

const showOptimizer = ref(false)

/** 全局键盘快捷键 */
useKeyboard([
  {
    key: 'k', ctrl: true,
    handler: () => {
      const input = document.querySelector<HTMLTextAreaElement>('.n-input textarea')
      input?.focus()
    },
    description: '聚焦提示词输入框',
  },
  {
    key: 'Enter', ctrl: true,
    handler: (e) => { handleGenerate(); e.preventDefault() },
    description: '生成图片',
  },
])

/* ═══════════════════════════════════════════════
   快捷创作模板（原新手向导整合）
   ═══════════════════════════════════════════════ */
type QuickTaskType = 'image' | 'video' | 'edit'

interface QuickTask {
  id: string
  type: QuickTaskType
  icon: Component
  title: string
  description: string
  question: string
  placeholder: string
  promptTemplate: string
  negativePrompt: string
  recommendedSize: string
}

const quickTasks: QuickTask[] = [
  {
    id: 'ecommerce', type: 'image', icon: ShoppingBag,
    title: '电商主图', description: '商品清晰、背景干净',
    question: '你要卖什么？希望什么风格？',
    placeholder: '例如：一款白色保温杯，适合年轻女性，干净高级感',
    promptTemplate: '电商产品主图，主体是「{need}」，干净背景，商业摄影，产品细节清晰，柔和棚拍光，高级质感，适合电商上架',
    negativePrompt: '模糊，低质量，水印，文字，变形，杂乱背景',
    recommendedSize: '1024x1024',
  },
  {
    id: 'social-poster', type: 'image', icon: Megaphone,
    title: '社媒海报', description: '有冲击力，适合小红书',
    question: '你要宣传什么内容？',
    placeholder: '例如：春季咖啡新品上市，温暖、有活力、适合小红书',
    promptTemplate: '社交媒体宣传海报，主题是「{need}」，视觉焦点明确，色彩吸引人，现代设计，留出文字排版空间，高质量商业视觉',
    negativePrompt: '低清晰度，文字错误，水印，画面拥挤，主体不清',
    recommendedSize: '1440x2560',
  },
  {
    id: 'presentation', type: 'image', icon: BarChart3,
    title: 'PPT配图', description: '简洁专业，不抢正文',
    question: '这页 PPT 想表达什么？',
    placeholder: '例如：AI 正在帮助团队提升内容生产效率',
    promptTemplate: 'PPT 专业配图，表达「{need}」，简洁构图，商务科技感，低干扰背景，留白充足，清晰高级，适合演示文稿',
    negativePrompt: '过度复杂，刺眼颜色，水印，错误文字，低质量',
    recommendedSize: '2560x1440',
  },
  {
    id: 'portrait', type: 'image', icon: User,
    title: '生成头像', description: '专业形象照风格',
    question: '你想要什么人物形象？',
    placeholder: '例如：一位内容运营女生，亲和、专业、浅色背景',
    promptTemplate: '专业人物形象照，人物设定「{need}」，自然表情，干净背景，柔和光线，真实质感，适合头像和个人介绍页',
    negativePrompt: '畸形五官，多余手指，低质量，过度美颜，水印',
    recommendedSize: '1024x1024',
  },
  {
    id: 'image-to-video', type: 'video', icon: Film,
    title: '让图动起来', description: '图片变短视频',
    question: '你希望画面怎么动？',
    placeholder: '例如：人物轻轻微笑，头发随风飘动，镜头慢慢推进',
    promptTemplate: '图生视频，画面动作是「{need}」，自然运动，镜头稳定，细节连贯，电影感，5秒短视频',
    negativePrompt: '',
    recommendedSize: '1440x2560',
  },
  {
    id: 'edit-image', type: 'edit', icon: Pencil,
    title: '修改图片', description: '换背景、局部重绘',
    question: '你想怎么修改图片？',
    placeholder: '例如：把背景换成浅色办公室，保持人物不变',
    promptTemplate: '{need}',
    negativePrompt: '',
    recommendedSize: '1024x1024',
  },
]

const quickCreateOpen = ref(false)
const selectedQuickTask = ref<QuickTask | null>(null)
const quickTaskInput = ref('')
const quickTaskRatio = ref('1:1')
const useQuickAI = ref(false)
const quickAIWorking = ref(false)
const quickAIResult = ref<OptimizeResult | null>(null)
const settingsCollapseOpen = ref<string[]>([])

/** 模板填充后的提示词 */
const generatedQuickPrompt = computed(() => {
  if (!selectedQuickTask.value || !quickTaskInput.value.trim()) return ''
  return selectedQuickTask.value.promptTemplate.replace('{need}', quickTaskInput.value.trim())
})

let userEditedMainPrompt = false

function onMainPromptInput() {
  userEditedMainPrompt = true
}

/** 实时自动填入主表单（不覆盖用户手动编辑） */
watch(quickTaskInput, (val) => {
  if (!selectedQuickTask.value || !val.trim() || selectedQuickTask.value.type !== 'image') return
  if (userEditedMainPrompt) return
  generatorStore.prompt = selectedQuickTask.value.promptTemplate.replace('{need}', val.trim())
})

/** 展开快捷创作时自动收起"更多参数" */
watch(quickCreateOpen, (open) => {
  if (!open) {
    settingsCollapseOpen.value = []
  }
})

/** 快捷创作比例实时同步到主表单尺寸 */
watch(quickTaskRatio, (ratio) => {
  if (!selectedQuickTask.value) return
  generatorStore.size = resolveQuickSize(ratio)
})

function selectQuickTask(task: QuickTask) {
  if (selectedQuickTask.value?.id === task.id) return
  // 保存当前任务状态
  const prevInput = quickTaskInput.value
  const prevAI = useQuickAI.value
  const prevAIResult = quickAIResult.value

  selectedQuickTask.value = task
  quickTaskInput.value = prevInput || ''
  useQuickAI.value = prevAI
  quickAIResult.value = prevAIResult
  userEditedMainPrompt = false // 切换任务时重置标志
  if (task.recommendedSize === '1440x2560') quickTaskRatio.value = '9:16'
  else if (task.recommendedSize === '2560x1440') quickTaskRatio.value = '16:9'
  else quickTaskRatio.value = '1:1'

  // 写入创作上下文：场景 + 意图
  const scene = TASK_SCENE_MAP[task.id] || 'general'
  setScene(scene)
}

function applyAIResult() {
  if (!quickAIResult.value) return
  if (quickAIResult.value.optimizedPrompt) {
    generatorStore.prompt = quickAIResult.value.optimizedPrompt
  }
  if (quickAIResult.value.negativePrompt) {
    generatorStore.negativePrompt = quickAIResult.value.negativePrompt
  }
  message.success('已应用到主表单')
}

async function onQuickAIChange(val: boolean) {
  if (val && !quickAIResult.value && quickTaskInput.value.trim()) {
    await doQuickAIOptimize()
  }
}

async function doQuickAIOptimize() {
  const llmProvider = providerStore.defaultLLMProvider
  if (!llmProvider?.apiKey) {
    message.warning('请先配置大语言模型（在"配置能力"中设置）')
    useQuickAI.value = false
    return
  }
  if (!generatedQuickPrompt.value) return

  quickAIWorking.value = true
  quickAIResult.value = null

  try {
    const sceneMap: Record<string, 'product' | 'marketing' | 'presentation' | 'portrait' | 'general'> = {
      ecommerce: 'product',
      'social-poster': 'marketing',
      presentation: 'presentation',
      portrait: 'portrait',
    }
    const result = await optimizePrompt(
      generatedQuickPrompt.value,
      llmProvider,
      {
        scene: sceneMap[selectedQuickTask.value?.id || ''] || 'general',
        style: 'professional',
      }
    )
    if (result.success) {
      quickAIResult.value = result
      // 写入创作上下文：优化历史
      if (result.optimizedPrompt) {
        addContextOptimization(result.optimizedPrompt, result.explanation || 'AI 优化')
      }
      message.success('AI 优化完成')
    } else {
      message.error(result.error || '优化失败')
      useQuickAI.value = false
    }
  } catch {
    message.error('优化请求失败')
    useQuickAI.value = false
  } finally {
    quickAIWorking.value = false
  }
}

/** 应用模板：填入提示词并直接生成 */
async function applyQuickTask() {
  if (!selectedQuickTask.value || !quickTaskInput.value.trim()) return

  if (selectedQuickTask.value.type === 'video') {
    emit('navigateToVideo', generatedQuickPrompt.value, '')
    return
  }

  if (selectedQuickTask.value.type === 'edit') {
    emit('navigateToEdit', generatedQuickPrompt.value)
    return
  }

  // 图像任务：填提示词 → 直接生成（像旧版向导一样一条龙完成）
  const finalPrompt = useQuickAI.value && quickAIResult.value?.optimizedPrompt
    ? quickAIResult.value.optimizedPrompt
    : generatedQuickPrompt.value
  const finalNegative = useQuickAI.value && quickAIResult.value?.negativePrompt
    ? quickAIResult.value.negativePrompt
    : selectedQuickTask.value.negativePrompt

  generatorStore.prompt = finalPrompt
  generatorStore.negativePrompt = finalNegative

  // 收起快捷创作区，让用户看到下方主表单的生成进度
  quickCreateOpen.value = false

  const success = await generatorStore.generate()
  if (success) {
    message.success('生成成功！')
  }
}

function resolveQuickSize(ratio: string): string {
  const map: Record<string, string> = {
    '1:1': '1024x1024',
    '3:4': '768x1024',
    '16:9': '1792x1024',
    '9:16': '1024x1792',
  }
  return map[ratio] || '1024x1024'
}

/**
 * 基于当前提示词匹配相关知识条目（取前 8 条）
 * 评分逻辑（参考 useTermSuggestions.localMatch）：
 *   - 名字完全匹配: 1.0
 *   - 名字子串匹配: 0.6
 *   - 描述关键词匹配: 按命中数 × 0.3 上限 0.9
 * 案例权重 ×1.5（案例比术语更有学习价值）
 */
const learningItems = computed(() => {
  const text = generatorStore.prompt.trim()
  if (!text || !dataStore.loaded) return []
  const textLower = text.toLowerCase()

  function scoreItem(item: any): number {
    const name = item.name || item.title || item.content || ''
    const desc = item.description || ''
    if (!name && !desc) return 0

    let score = 0
    if (name && name.length >= 2) {
      if (text.includes(name)) score = Math.max(score, 1.0)
      else if (textLower.includes(name.toLowerCase())) score = Math.max(score, 0.6)
    }
    if (desc) {
      const words = desc.split(/[，,、。.；;！!？?\s]+/).filter((w: string) => w.length >= 2)
      let hit = 0
      for (const w of words) {
        if (text.includes(w)) hit++
      }
      if (hit > 0) {
        const descScore = Math.min(0.9, 0.3 * hit)
        if (descScore > score) score = descScore
      }
    }
    return score
  }

  const scored: Array<{ item: any; score: number }> = []
  for (const term of dataStore.terms as any[]) {
    const s = scoreItem(term)
    if (s > 0) scored.push({ item: term, score: s })
  }
  for (const c of dataStore.caseEntries as any[]) {
    const s = scoreItem(c)
    if (s > 0) {
      // 案例权重 +50%（更实用）
      scored.push({ item: c, score: s * 1.5 })
    }
  }

  scored.sort((a, b) => b.score - a.score)
  return scored.slice(0, 8).map((s) => s.item)
})

function insertTerm(item: any) {
  const term = item.content || item.title || item.name || ''
  if (!term) return
  const current = generatorStore.prompt
  const suffix = current && !current.endsWith('，') && !current.endsWith(',') ? '，' : ''
  generatorStore.prompt = current + suffix + term
}

const fullscreenContainerRef = ref<HTMLElement | null>(null)
const imageDimensions = ref<{ width: number; height: number } | null>(null)
const showFullscreen = ref(false)

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

/** 将用户自定义 Provider 中的模型合并到模型下拉列表 */
/** 当前默认的图像生成供应商 */
const defaultImageProvider = computed(() =>
  providerStore.getDefaultProviderByCapability('image')
)

/** 已配置的图像供应商列表（含状态） */
const activeImageProviders = computed(() =>
  providerStore.providers.filter(p => p.capabilities?.includes('image') && p.apiKey)
)

function stripeDotClass(status?: string): string {
  if (status === 'active') return 'stripe-active'
  if (status === 'error') return 'stripe-error'
  if (status === 'checking') return 'stripe-checking'
  return 'stripe-idle'
}

function statusClass(status?: string): string {
  const map: Record<string, string> = {
    active: 'status-active',
    error: 'status-error',
    checking: 'status-checking',
    inactive: 'status-inactive',
  }
  return map[status || 'inactive'] || 'status-inactive'
}

function statusLabel(status?: string): string {
  const map: Record<string, string> = {
    active: '已连接',
    error: '连接失败',
    checking: '检测中',
    inactive: '未检测',
  }
  return map[status || 'inactive'] || '未检测'
}

const modelOptions = computed(() => {
  const providerLabels: Record<string, string> = {
    doubao: '豆包', zhipu: '智谱', aliyun: '通义', openai: 'OpenAI',
    kling: '可灵', jimeng: '即梦', runway: 'Runway'
  }

  /** 从 providerPresets 反向推断 ProviderType */
  function inferProviderType(modelId: string): string {
    if (modelId.startsWith('doubao')) return 'doubao'
    if (modelId.startsWith('cogview')) return 'zhipu'
    if (modelId.startsWith('wanx')) return 'aliyun'
    if (modelId.startsWith('dall-e')) return 'openai'
    if (modelId.includes('stable-diffusion')) return 'custom'
    return ''
  }

  /** 获取某类型 Provider 是否已配置且连通 */
  function isProviderReady(providerType: string): boolean {
    if (!providerType) return true
    const found = providerStore.providers.find(p => p.type === providerType)
    if (!found) return false
    if (found.status === 'active') return true
    return !!found.apiKey
  }

  // 1) 后端定义的模型列表
  const serverModelIds = new Set<string>()
  const serverModels = (configStore.serverConfig?.models || []).map(m => {
    serverModelIds.add(m.id)
    const provider = inferProviderType(m.id)
    return {
      label: providerLabels[provider]
        ? `${m.name} [${providerLabels[provider]}]`
        : m.name,
      value: m.id,
      disabled: !isProviderReady(provider),
      provider: provider || undefined,
    }
  })

  // 2) 用户自定义 Provider 中的模型（不在 serverModels 中的）
  const imageProviders = providerStore.providers.filter(
    p => p.capabilities?.includes('image') && p.apiKey
  )
  const customModels: { label: string; value: string; disabled: boolean; provider?: string }[] = []
  for (const prov of imageProviders) {
    for (const mId of (prov.models || [])) {
      if (!serverModelIds.has(mId)) {
        const statusIcon = prov.status === 'active' ? '✅ ' : prov.status === 'error' ? '❌ ' : ''
        customModels.push({
          label: `${statusIcon}${mId} [${prov.name}]`,
          value: mId,
          disabled: prov.status === 'error' || !prov.apiKey,
          provider: prov.type,
        })
      }
    }
  }

  // 3) 当前默认 Provider 的 defaultModel（前面都没出现时兜底）
  const defaultImageProvider = providerStore.getDefaultProviderByCapability('image')
  if (defaultImageProvider?.defaultModel && !serverModelIds.has(defaultImageProvider.defaultModel)) {
    const already = customModels.some(m => m.value === defaultImageProvider.defaultModel)
    if (!already) {
      customModels.push({
        label: `${defaultImageProvider.defaultModel} [${defaultImageProvider.name}]`,
        value: defaultImageProvider.defaultModel,
        disabled: !defaultImageProvider.apiKey,
        provider: defaultImageProvider.type,
      })
    }
  }

  // 按 provider 分组
  const all = [...serverModels, ...customModels]
  const grouped = new Map<string, typeof all>()
  for (const m of all) {
    const key = m.provider || 'other'
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(m)
  }

  return Array.from(grouped.entries()).map(([key, children]) => ({
    type: 'group' as const,
    label: providerLabels[key] || (key === 'other' ? '其他' : key),
    children: children.map(({ provider: _, ...rest }) => rest),
  }))
})

const SIZE_META: Record<string, { ratio: string; label: string; platforms: string }> = {
  '1024x1024': { ratio: '1:1', label: '正方', platforms: '1:1' },
  '2048x2048': { ratio: '1:1', label: '正方(高清)', platforms: '1:1 高清' },
  '1024x1792': { ratio: '9:16', label: '竖版', platforms: '9:16' },
  '1792x1024': { ratio: '16:9', label: '横版', platforms: '16:9' },
  '1440x2560': { ratio: '9:16', label: '竖版(高清)', platforms: '9:16 高清' },
  '2560x1440': { ratio: '16:9', label: '横版(高清)', platforms: '16:9 高清' },
  '1920x2560': { ratio: '3:4', label: '竖版(3:4)', platforms: '3:4' },
  '512x512':   { ratio: '1:1', label: '小图', platforms: '预览' },
  '768x1024':  { ratio: '3:4', label: '竖版(3:4)', platforms: '3:4' },
  '1024x768':  { ratio: '4:3', label: '横版(4:3)', platforms: '4:3' },
}

const RatioList = [
  { ratio: '1:1', label: '1:1' },
  { ratio: '3:4', label: '3:4' },
  { ratio: '4:3', label: '4:3' },
  { ratio: '9:16', label: '9:16' },
  { ratio: '16:9', label: '16:9' },
]

const sizeOptions = computed(() => {
  const modelId = generatorStore.model
  const allSizes = configStore.serverConfig?.sizes || ['1024x1024', '1024x1792', '1792x1024', '2048x2048']
  const manifestModel = configStore.modelManifest?.models.find(m => m.id === modelId)
  
  let filtered: string[]
  if (manifestModel?.supported_sizes?.length) {
    filtered = allSizes.filter(s => manifestModel.supported_sizes.includes(s))
  } else {
    const modelConfig = getModelSizeConfig(modelId)
    if (modelConfig) {
      filtered = allSizes.filter(s => modelConfig.supportedSizes.includes(s))
    } else {
      filtered = allSizes
    }
  }

  return filtered.map(size => {
    const meta = SIZE_META[size]
    const valid = validateSizeForModel(modelId, size)
    const modelConfig = getModelSizeConfig(modelId)
    const isRecommended = manifestModel?.recommended_sizes?.includes(size) ||
      modelConfig?.recommendedSizes.includes(size)
    let label = `${size} [${meta ? meta.platforms : ''}]`
    if (isRecommended) label += ' [推荐]'

    return { label, value: size, disabled: !valid.valid }
  })
})

function validateSizeForModel(modelId: string, size: string): { valid: boolean; reason?: string } {
  const manifestModel = configStore.modelManifest?.models.find(m => m.id === modelId)
  if (!manifestModel?.min_pixels && !manifestModel?.max_pixels) {
    return isSizeValidForModel(modelId, size)
  }

  const [width = 0, height = 0] = size.split('x').map(v => Number.parseInt(v, 10))
  const pixels = width * height
  if (manifestModel.min_pixels && pixels < manifestModel.min_pixels) {
    return {
      valid: false,
      reason: `该模型要求最小 ${manifestModel.min_pixels.toLocaleString()} 像素`
    }
  }
  if (manifestModel.max_pixels && pixels > manifestModel.max_pixels) {
    return {
      valid: false,
      reason: `该模型最大支持 ${manifestModel.max_pixels.toLocaleString()} 像素`
    }
  }
  return { valid: true }
}

const ratioActive = computed(() => {
  const size = generatorStore.size
  const meta = SIZE_META[size]
  return meta?.ratio || ''
})

function pickRatio(ratio: string) {
  const targets = ratio === '1:1' ? ['2048x2048', '1024x1024', '512x512'] :
                  ratio === '3:4' ? ['1920x2560', '768x1024'] :
                  ratio === '9:16' ? ['1440x2560', '1024x1792'] :
                  ratio === '16:9' ? ['2560x1440', '1792x1024'] :
                  ratio === '4:3' ? ['1024x768'] : []
  const avail = sizeOptions.value
  for (const t of targets) {
    const m = avail.find(o => o.value === t && !o.disabled)
    if (m) { generatorStore.size = m.value; return }
  }
}

const supportsAdvancedParams = computed(() => {
  const modelId = generatorStore.model
  if (!modelId || modelId === 'default') return false
  return modelId.includes('dall-e') || modelId.includes('stable-diffusion')
})

const currentModelNote = computed(() => {
  const modelId = generatorStore.model
  const manifestModel = configStore.modelManifest?.models.find(m => m.id === modelId)
  if (manifestModel?.limitations) return manifestModel.limitations
  const config = getModelSizeConfig(modelId)
  return config?.note || null
})

function handleModelChange(modelId: string | undefined) {
  if (!modelId) return
  const opts = sizeOptions.value
  const currentSize = generatorStore.size
  const stillAvailable = opts.some(o => o.value === currentSize && !o.disabled)
  if (stillAvailable) return
  const config = getModelSizeConfig(modelId)
  const manifestModel = configStore.modelManifest?.models.find(m => m.id === modelId)
  const recommendedSize = manifestModel?.recommended_sizes?.[0] || config?.recommendedSizes[0]
  if (recommendedSize) {
    generatorStore.size = recommendedSize
  }
}

async function handleGenerate() {
  const success = await generatorStore.generate()
  if (success) {
    message.success('生成成功！')
  }
}

function handleQuickInsert(text: string) {
  const currentPrompt = generatorStore.prompt
  if (currentPrompt && !currentPrompt.endsWith('，') && !currentPrompt.endsWith(',')) {
    generatorStore.prompt = currentPrompt + '，' + text
  } else {
    generatorStore.prompt = currentPrompt + text
  }
}

function handleApplyOptimize(prompt: string, negativePrompt?: string) {
  generatorStore.prompt = prompt
  if (negativePrompt) {
    generatorStore.negativePrompt = negativePrompt
  }
}

function onImageLoaded(dimensions: { width: number; height: number }) {
  imageDimensions.value = dimensions
}

function openFullscreen() {
  showFullscreen.value = true
  resetFullscreen()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && showFullscreen.value) {
    showFullscreen.value = false
  }
}

function downloadImage() {
  if (!generatorStore.lastImage) return
  const link = document.createElement('a')
  link.href = generatorStore.lastImage
  link.download = `ai-image-${Date.now()}.png`
  link.click()
  message.success('开始下载')
}

const showSaveCaseModal = ref(false)
const savingCase = ref(false)
const caseTitle = ref('')
const caseTags = ref('')
const caseTips = ref('')
const casePrompt = ref('')

function openSaveCaseModal() {
  caseTitle.value = ''
  caseTags.value = ''
  caseTips.value = ''
  casePrompt.value = generatorStore.prompt
  showSaveCaseModal.value = true
}

async function handleSaveCase() {
  if (!caseTitle.value.trim() || !casePrompt.value.trim()) {
    message.warning('请填写标题和提示词')
    return
  }

  savingCase.value = true
  try {
    const res = await axios.post(`${appConfig.apiBaseUrl}/api/cases`, {
      title: caseTitle.value.trim(),
      prompt: casePrompt.value.trim(),
      negativePrompt: generatorStore.negativePrompt || '',
      model: generatorStore.model,
      size: generatorStore.size,
      tips: caseTips.value.split('\n').filter(Boolean).map((s: string) => s.trim()),
      tags: caseTags.value.split(',').filter(Boolean).map((s: string) => s.trim()),
    })
    if (res.data.success) {
      message.success('案例已收录到知识库！')
      showSaveCaseModal.value = false
    } else {
      message.error(res.data.error || '保存失败')
    }
  } catch {
    message.error('收录失败，请检查后端服务')
  } finally {
    savingCase.value = false
  }
}

const emit = defineEmits<{
  editImage: [imageUrl: string]
  generateVideo: [imageUrl: string, prompt: string]
  navigateToVideo: [prompt: string, negativePrompt: string]
  navigateToEdit: [instruction: string]
}>()

function editImage() {
  if (!generatorStore.lastImage) return
  emit('editImage', generatorStore.lastImage)
}

function generateVideo() {
  if (!generatorStore.lastImage) return
  emit('generateVideo', generatorStore.lastImage, generatorStore.prompt)
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  window.addEventListener('resize', () => {
    if (showFullscreen.value) {
      fitFullscreen()
    }
  })
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.generate-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sider-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ── Provider Status Stripe ── */
.provider-stripe {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stripe-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  cursor: help;
}

.stripe-active { background: #22c55e; }
.stripe-error { background: #ef4444; }
.stripe-checking { background: #f59e0b; animation: pulse-dot 1s ease-in-out infinite; }
.stripe-idle { background: #d1d5db; }
.stripe-none { background: #d1d5db; opacity: 0.4; }

/* ── Result Area ── */
.image-result {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* ── Prompt Field ── */
.prompt-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.prompt-field {
  margin-bottom: 4px;
}
.prompt-field :deep(.n-input__textarea-el) {
  min-height: 120px !important;
  font-size: 14px;
  line-height: 1.6;
}

/* ── Generate Button ── */
.generate-btn {
  height: 44px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-md) !important;
  margin-top: 12px;
  letter-spacing: 0.3px;
  box-shadow: 0 2px 8px rgba(79, 125, 243, 0.25), 0 1px 3px rgba(79, 125, 243, 0.15);
}
.generate-btn:hover {
  box-shadow: 0 4px 16px rgba(79, 125, 243, 0.35), 0 2px 6px rgba(79, 125, 243, 0.2);
  transform: translateY(-1px);
}
.generate-btn:active {
  transform: translateY(0);
}

/* ── Action Buttons ── */
.image-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  flex-wrap: wrap;
}

/* ── Learning Recommendations ── */
.learning-section {
  margin-top: 14px;
  padding: 12px 14px;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}

.learning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.learning-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}
.learning-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* ── Fullscreen ── */
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

:deep(.n-card-body) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

:deep(.n-modal .n-card) {
  height: 100vh;
}

.term-suggestions {
  margin-top: 6px;
}

.term-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-tertiary, #94a3b8);
}

.term-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.suggestions-label {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.size-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ratio-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* ── Model Status Bar ── */
.model-status-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin-top: 4px;
}

.provider-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-active .status-dot { background: #22c55e; box-shadow: 0 0 4px rgba(34,197,94,0.4); }
.status-error .status-dot { background: #ef4444; box-shadow: 0 0 4px rgba(239,68,68,0.4); }
.status-checking .status-dot { background: #f59e0b; animation: pulse-dot 1s ease-in-out infinite; }
.status-inactive .status-dot { background: #d1d5db; }

.status-active { color: #16a34a; }
.status-error { color: #dc2626; }
.status-checking { color: #d97706; }
.status-inactive { color: #9ca3af; }

.latency { color: #9ca3af; }

@keyframes pulse-dot {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.prompt-optimizer-section {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: linear-gradient(135deg, var(--brand-50) 0%, var(--bg-card) 100%);
  border-radius: var(--radius-md);
  border: 1px solid var(--brand-200);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

:deep(.n-modal .n-card-body) {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

/* ═══════════════════════════════════════════════
   快捷创作模板区
   ═══════════════════════════════════════════════ */
.quick-create {
  margin-bottom: 16px;
  border: 1px solid var(--border-light, #eef0f4);
  border-radius: var(--radius-md, 10px);
  background: var(--bg-card, #fff);
  transition: box-shadow var(--duration-base) var(--ease-out);
}
.quick-create:hover {
  box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}

.qc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--bg-card, #fff);
  transition: background var(--duration-fast) var(--ease-out);
}
.qc-header:hover {
  background: var(--gray-50, #f8f9fc);
}
.qc-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.qc-header-left :deep(.n-icon) {
  color: var(--brand-500, #4f7df3);
  flex-shrink: 0;
}
.qc-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #1a1a2e);
  white-space: nowrap;
}
.qc-desc {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.qc-toggle {
  flex-shrink: 0;
}

.qc-body {
  padding: 0 12px 12px;
  border-top: 1px solid var(--border-light, #eef0f4);
}

/* ── 任务卡片网格 ── */
.qc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 10px 0;
}

.qc-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 10px;
  border: 1px solid var(--border-light, #eef0f4);
  border-radius: var(--radius-sm, 8px);
  background: transparent;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  font-family: inherit;
  text-align: center;
}
.qc-card:hover {
  border-color: var(--brand-300, #a0bcf8);
  background: var(--brand-50, #f0f4ff);
}
.qc-card.selected {
  border-color: var(--brand-500, #4f7df3);
  background: var(--brand-50, #f0f4ff);
  box-shadow: 0 0 0 1px var(--brand-500, #4f7df3);
}
.qc-card-icon {
  color: var(--text-secondary, #64748b);
  transition: color var(--duration-fast) var(--ease-out);
}
.qc-card:hover .qc-card-icon,
.qc-card.selected .qc-card-icon {
  color: var(--brand-500, #4f7df3);
}
.qc-card-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.qc-card-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary, #1a1a2e);
  line-height: 1.3;
}
.qc-card-desc {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  line-height: 1.3;
}

/* ── 选中任务后的表单 ── */
.qc-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.qc-form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.qc-form-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary, #64748b);
}
.qc-ratio-row {
  display: flex;
  gap: 4px;
}
.qc-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.qc-ai-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary, #64748b);
}
.qc-ai-toggle :deep(.n-icon) {
  color: #f59e0b;
  flex-shrink: 0;
}
.qc-ai-label {
  white-space: nowrap;
}

/* ── AI 优化结果 ── */
.qc-ai-result {
  margin-top: 2px;
}
.qc-ai-result-text {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary, #64748b);
}

/* ── 模板预览 ── */
.qc-preview {
  padding: 8px 10px;
  background: var(--gray-50, #f8f9fc);
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--border-light, #eef0f4);
}
.qc-preview-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-tertiary, #9ca3af);
  margin-bottom: 3px;
}
.qc-preview-text {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary, #64748b);
  word-break: break-all;
}

/* ── 提示文字 ── */
.qc-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--brand-500, #4f7df3);
  opacity: 0.8;
}

/* ── 生成过程反馈 ── */
.generation-feedback {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  background: var(--brand-50, #f0f4ff);
  border-radius: var(--radius-md, 10px);
  border: 1px solid var(--brand-100, #e0e7ff);
  position: relative;
  overflow: hidden;
}

.feedback-pulse {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--brand-500, #4f7df3), transparent);
  animation: pulse-sweep 2s ease-in-out infinite;
}

@keyframes pulse-sweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.feedback-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feedback-stage {
  font-size: 13px;
  font-weight: 500;
  color: var(--brand-600, #4f46e5);
}

.feedback-eta {
  font-size: 12px;
  color: var(--text-tertiary, #94a3b8);
}

/* ── 错误卡片 ── */
.error-card {
  padding: 12px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md, 10px);
}

.error-title {
  font-size: 13px;
  font-weight: 600;
  color: #dc2626;
  margin-bottom: 4px;
}

.error-message {
  font-size: 12px;
  color: #7f1d1d;
  line-height: 1.5;
}
</style>
