<template>
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
                :title="`${p.name}: ${providerStatusLabel(p.status)}${p.latency ? ' (' + p.latency + 'ms)' : ''}`"
              />
            </template>
            <span v-else class="stripe-dot stripe-none" title="未配置供应商" />
          </div>
        </div>
      </div>

      <slot name="quick-entry" />

      <div v-if="!canUseImage" class="status-banner mb-3" role="status">
        <div class="status-banner__icon">
          <n-icon :component="AlertCircle" size="16" />
        </div>
        <div class="status-banner__content">
          <div class="font-semibold">请先配置生成图片能力</div>
          <div class="text-xs mt-1" style="opacity: 0.85">选择一个平台预设并填入 API Key 即可开始创作</div>
        </div>
        <n-button class="status-banner__action" type="primary" size="small" @click="configStore.showConfigModal = true">
          立即配置
        </n-button>
      </div>

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
            @keydown.enter.ctrl="emit('generate')"
            @input="emit('prompt-input')"
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
                <PromptOptimizer v-model:prompt="generatorStore.prompt" @apply="(p, n) => emit('apply-optimize', p, n)" />
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
              v-if="generatorStore.prompt.trim()"
              :prompt="generatorStore.prompt"
              @insert="(text) => emit('quick-insert', text)"
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
                  <span
                    v-if="defaultImageProvider"
                    class="provider-status"
                    :class="providerStatusClass(defaultImageProvider.status)"
                  >
                    <span class="status-dot" />
                    {{ defaultImageProvider.name }}:
                    {{ providerStatusLabel(defaultImageProvider.status) }}
                    <span v-if="defaultImageProvider.latency" class="latency">· {{ defaultImageProvider.latency }}ms</span>
                  </span>
                  <span v-else class="provider-status status-inactive">
                    <span class="status-dot" />
                    尚未配置图像生成供应商
                  </span>
                  <n-button size="tiny" text type="primary" @click="configStore.showConfigModal = true">配置</n-button>
                </div>
              </template>
            </n-form-item>

            <n-form-item label="尺寸">
              <div class="size-field">
                <div class="ratio-presets">
                  <n-button
                    v-for="r in RATIO_LIST"
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

            <n-alert v-if="currentModelNote" type="info" class="mb-3" :show-icon="false" size="small">
              {{ currentModelNote }}
            </n-alert>

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
                    <n-input-number v-model:value="generatorStore.seed" placeholder="随机" :min="0" :max="2147483647" clearable size="small" :show-button="false" />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="步数" label-placement="top">
                    <n-input-number v-model:value="generatorStore.steps" placeholder="默认" :min="1" :max="150" clearable size="small" :show-button="false" />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="CFG" label-placement="top">
                    <n-input-number v-model:value="generatorStore.cfgScale" placeholder="默认" :min="1" :max="30" :step="0.5" clearable size="small" :show-button="false" />
                  </n-form-item>
                </n-gi>
              </n-grid>
            </n-collapse-item>
          </n-collapse-item>
        </n-collapse>
      </n-form>
    </div>

    <div class="panel-sider-footer">
      <n-button
        type="primary"
        block
        size="large"
        class="generate-btn"
        :loading="generatorStore.status === 'generating'"
        :disabled="!generatorStore.prompt.trim() || !canUseImage"
        @click="generatorStore.generate()"
      >
        <template #icon v-if="generatorStore.status !== 'generating'">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </template>
        {{ generatorStore.status === 'generating' ? (generatorStore.stageLabel || '生成中') + '...' : '生成图片' }}
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NForm, NFormItem, NInput, NInputNumber, NSelect, NButton, NGrid, NGi, NAlert, NIcon,
  NCollapse, NCollapseItem, NCollapseTransition, NTag, NSpace, NText,
} from 'naive-ui'
import { Settings, Sparkles, Zap, ChevronDown, ChevronUp, AlertCircle } from 'lucide-vue-next'
import { useConfigStore, useGeneratorStore } from '../../stores'
import { useCapabilityReady } from '../../composables/useCapabilityReady'
import PromptAnalyzer from '../learn/PromptAnalyzer.vue'
import PromptOptimizer from '../PromptOptimizer.vue'
import PromptElementTagger from '../common/PromptElementTagger.vue'
import { useTermSuggestions } from '../../composables/useTermSuggestions'
import {
  useImageGenerationForm,
  RATIO_LIST,
  providerStatusClass,
  providerStatusLabel,
  stripeDotClass,
} from '../../composables/useImageGenerationForm'
import { termCategoryConfig } from '../../config/categories'
import type { TermCategory, TermEntry } from '../../types/knowledge'

const emit = defineEmits<{
  generate: []
  'prompt-input': []
  'apply-optimize': [prompt: string, negativePrompt?: string]
  'quick-insert': [text: string]
}>()

const configStore = useConfigStore()
const generatorStore = useGeneratorStore()
const { canUseImage } = useCapabilityReady()

const {
  defaultImageProvider,
  activeImageProviders,
  modelOptions,
  sizeOptions,
  ratioActive,
  supportsAdvancedParams,
  currentModelNote,
  pickRatio,
  handleModelChange,
} = useImageGenerationForm()

const { suggestions: termSuggestions } = useTermSuggestions(computed(() => generatorStore.prompt))
const showAllTerms = ref(false)
const termSuggestOpen = ref(false)
const showOptimizer = ref(false)
const settingsCollapseOpen = ref<string[]>([])

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
</script>

<style scoped>
.sider-header-row { display: flex; align-items: center; justify-content: space-between; }
.provider-stripe { display: flex; align-items: center; gap: 4px; }
.stripe-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; cursor: help; }
.stripe-active { background: #22c55e; }
.stripe-error { background: #ef4444; }
.stripe-checking { background: #f59e0b; animation: pulse-dot 1s ease-in-out infinite; }
.stripe-idle { background: #d1d5db; }
.stripe-none { background: #d1d5db; opacity: 0.4; }
.prompt-label { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.prompt-field { margin-bottom: 4px; }
.prompt-field :deep(.n-input__textarea-el) { min-height: 120px !important; font-size: 14px; line-height: 1.6; }
.panel-sider-footer { flex-shrink: 0; padding: 12px 0 0; border-top: 1px solid var(--border-light); background: var(--bg-card); }
.generate-btn {
  height: 44px !important; font-size: 14px !important; font-weight: 600 !important;
  border-radius: var(--radius-md) !important; letter-spacing: 0.3px;
  box-shadow: 0 2px 8px rgba(79, 125, 243, 0.25), 0 1px 3px rgba(79, 125, 243, 0.15);
}
.term-suggestions { margin-top: 6px; }
.term-toggle { display: inline-flex; align-items: center; gap: 4px; color: var(--text-tertiary, #94a3b8); }
.term-tags { display: flex; align-items: center; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
.suggestions-label { font-size: 12px; color: #999; white-space: nowrap; }
.size-field { display: flex; flex-direction: column; gap: 6px; }
.ratio-presets { display: flex; flex-wrap: wrap; gap: 4px; }
.model-status-bar { display: flex; align-items: center; gap: 6px; font-size: 12px; margin-top: 4px; }
.provider-status { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; }
.status-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.status-active .status-dot { background: #22c55e; }
.status-error .status-dot { background: #ef4444; }
.status-checking .status-dot { background: #f59e0b; animation: pulse-dot 1s ease-in-out infinite; }
.status-inactive .status-dot { background: #d1d5db; }
.status-active { color: #16a34a; }
.status-error { color: #dc2626; }
.status-checking { color: #d97706; }
.status-inactive { color: #9ca3af; }
.latency { color: #9ca3af; }
.prompt-optimizer-section {
  margin-bottom: 12px; padding: 10px 12px;
  background: linear-gradient(135deg, var(--brand-50) 0%, var(--bg-card) 100%);
  border-radius: var(--radius-md); border: 1px solid var(--brand-200);
}
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.mb-3 { margin-bottom: 12px; }
@keyframes pulse-dot { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
</style>
