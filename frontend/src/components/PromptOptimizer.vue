<template>
  <div class="prompt-optimizer">
    <n-space vertical>
      <n-space align="center" justify="space-between">
        <n-text strong>提示词优化</n-text>
        <n-space>
          <n-select
            v-model:value="selectedScene"
            :options="sceneOptions"
            placeholder="场景"
            style="width: 120px"
            size="small"
          />
          <n-select
            v-model:value="selectedStyle"
            :options="styleOptions"
            placeholder="风格"
            style="width: 120px"
            size="small"
          />
        </n-space>
      </n-space>

      <n-space>
        <n-select
          v-model:value="selectedLLMId"
          :options="llmOptions"
          placeholder="选择大模型"
          style="width: 180px"
          size="small"
        />
        <n-button
          type="primary"
          size="small"
          :loading="optimizing"
          :disabled="!selectedLLMId || !localPrompt.trim()"
          @click="handleOptimize"
        >
          <template #icon><n-icon :component="SparklesOutline" /></template>
          AI优化
        </n-button>
        <n-button
          size="small"
          :disabled="!localPrompt.trim()"
          @click="handleQuickOptimize"
        >
          快速优化
        </n-button>
      </n-space>

      <n-alert v-if="!providerStore.hasConfiguredLLM" type="warning" size="small">
        请先配置大语言模型 API Key
        <n-button text type="primary" size="small" @click="showConfigModal = true">
          立即配置
        </n-button>
      </n-alert>

      <n-progress
        v-if="optimizing"
        type="line"
        :percentage="progress"
        :show-indicator="false"
        status="info"
      />

      <n-alert v-if="error" type="error" size="small">
        {{ error }}
      </n-alert>

      <div v-if="!history.length && !optimizing && !error" class="optimizer-hint">
        <n-text depth="3" style="font-size: 12px">
          点击「AI优化」后，优化后的提示词会自动填入文本框，可反复调整方向进行多轮优化
        </n-text>
      </div>

      <div v-if="history.length > 0" class="result-section">
        <div class="result-header">
          <n-space align="center">
            <n-text strong>优化结果</n-text>
            <n-tag v-if="history.length > 1" size="small" type="success">
              {{ currentRound + 1 }} / {{ history.length }}
            </n-tag>
          </n-space>
          <n-space>
            <n-button size="tiny" @click="copyResult">复制</n-button>
            <n-button v-if="currentRound < history.length - 1" size="tiny" type="primary" @click="switchToLatest">
              用最新版
            </n-button>
          </n-space>
        </div>

        <div class="round-nav" v-if="history.length > 1">
          <n-button size="tiny" :disabled="currentRound === 0" @click="currentRound--">← 上一版</n-button>
          <n-button size="tiny" :disabled="currentRound === history.length - 1" @click="currentRound++">下一版 →</n-button>
          <n-button size="tiny" secondary @click="handleRollback" :disabled="currentRound === history.length - 1">回退到此版</n-button>
        </div>

        <n-card size="small" class="result-card">
          <div class="result-item result-main">
            <n-text depth="1" style="font-size: 14px; font-weight: 500; line-height: 1.7; word-break: break-word">
              {{ currentEntry?.result.optimizedPrompt || '' }}
            </n-text>
          </div>

          <n-divider v-if="currentEntry?.result.optimizedPromptCN" style="margin: 8px 0" />

          <div v-if="currentEntry?.result.optimizedPromptCN" class="result-item result-chinese">
            <n-text depth="3" style="font-size: 12px">🇨🇳 中文解释：</n-text>
            <n-text depth="2" style="font-size: 13px; line-height: 1.7; word-break: break-word">
              {{ currentEntry?.result.optimizedPromptCN }}
            </n-text>
          </div>

          <div v-if="(currentEntry?.diffAdded?.length ?? 0) + (currentEntry?.diffRemoved?.length ?? 0) > 0" class="result-item diff-box">
            <n-text depth="3" style="font-size: 12px">相比上一版的变化：</n-text>
            <div class="diff-content">
              <div v-if="currentEntry?.diffAdded && currentEntry.diffAdded.length > 0" class="diff-added">
                <n-text style="color: #52c41a">+</n-text>
                <n-text depth="2" style="font-size: 12px">{{ currentEntry.diffAdded.slice(0, 8).join(', ') }}</n-text>
              </div>
              <div v-if="currentEntry?.diffRemoved && currentEntry.diffRemoved.length > 0" class="diff-removed">
                <n-text style="color: #ff4d4f">-</n-text>
                <n-text depth="2" style="font-size: 12px">{{ currentEntry.diffRemoved.slice(0, 8).join(', ') }}</n-text>
              </div>
            </div>
          </div>

          <div v-if="currentEntry?.result.negativePrompt" class="result-item neg-box">
            <n-text depth="3" style="font-size: 12px">负面词：</n-text>
            <n-text depth="2" style="font-size: 12px">{{ currentEntry?.result.negativePrompt }}</n-text>
          </div>

          <div v-if="currentEntry?.result.explanation" class="result-item explanation-box">
            <n-text depth="3" style="font-size: 12px">为什么这样写：</n-text>
            <n-text depth="2" style="font-size: 13px; line-height: 1.6">{{ currentEntry?.result.explanation }}</n-text>
          </div>

          <div v-if="currentEntry?.result.knowledgeRefs && currentEntry.result.knowledgeRefs.length > 0" class="result-item knowledge-refs">
            <n-collapse>
              <n-collapse-item title="参考的知识">
                <div v-for="knowledgeRef in (currentEntry?.result.knowledgeRefs || [])" :key="knowledgeRef.id" class="knowledge-tag-row">
                  <n-tag
                    :type="knowledgeRef.type === 'industry' ? 'info' : knowledgeRef.type === 'term' ? 'success' : 'warning'"
                    size="small" style="margin: 2px 4px 2px 0"
                  >
                    {{ knowledgeRef.title }}
                  </n-tag>
                </div>
              </n-collapse-item>
            </n-collapse>
          </div>

          <div v-if="history[currentRound]?.followUpHint" class="result-item adjustment-hint">
            <n-tag size="small" type="info">{{ history[currentRound]?.followUpHint }}</n-tag>
          </div>

          <div class="result-item follow-up">
            <n-text depth="3" style="font-size: 12px; margin-bottom: 4px; display: block">继续调整：</n-text>
            <n-space wrap size="small" style="margin-bottom: 6px">
              <n-button size="tiny" @click="quickAdjust('只改光线，换成暖色调')">换暖色调</n-button>
              <n-button size="tiny" @click="quickAdjust('增强画面细节和质感')">增强细节</n-button>
              <n-button size="tiny" @click="quickAdjust('改成极简风格，更多留白')">极简风格</n-button>
              <n-button size="tiny" @click="quickAdjust('加入景深和背景虚化效果')">景深虚化</n-button>
              <n-button size="tiny" @click="quickAdjust('主体更突出，背景更简洁')">突出主体</n-button>
            </n-space>
            <n-input
              v-model:value="followUpQuestion"
              placeholder="或用文字描述你想怎么调整..."
              size="small"
              @keydown.enter="handleFollowUp"
            />
            <n-button
              size="small" type="primary"
              :loading="optimizing"
              :disabled="!followUpQuestion.trim()"
              @click="handleFollowUp"
              style="margin-top: 6px"
            >
              继续调整
            </n-button>
          </div>

          <div v-if="currentEntry?.result.suggestions && currentEntry.result.suggestions.length > 0" class="suggestions">
            <n-text depth="3" style="font-size: 12px">优化建议：</n-text>
            <ul>
              <li v-for="(s, i) in currentEntry?.result.suggestions" :key="i">{{ s }}</li>
            </ul>
          </div>
        </n-card>
      </div>
    </n-space>

    <n-modal
      v-model:show="showConfigModal"
      preset="card"
      title="配置大语言模型"
      style="width: 500px"
    >
      <n-space vertical>
        <n-alert type="info" size="small">
          大语言模型用于提示词优化，推荐使用免费的 GLM-4-Flash
        </n-alert>
        <div v-for="preset in providerStore.llmProviderPresets" :key="preset.type" class="llm-preset-item">
          <div class="preset-header">
            <span>{{ preset.name }}</span>
            <n-tag v-if="preset.isFree" size="small" type="success">免费</n-tag>
          </div>
          <n-input-group>
            <n-input
              v-model:value="llmApiKeys[preset.type]"
              :placeholder="`输入 ${preset.name} API Key`"
              type="password"
              show-password-on="click"
            />
            <n-button type="primary" @click="saveLLMConfig(preset)">保存</n-button>
          </n-input-group>
        </div>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  NSpace, NText, NSelect, NButton, NProgress, NAlert, NCard, NIcon,
  NModal, NInputGroup, NInput, NTag, NCollapse, NCollapseItem, NDivider, useMessage
} from 'naive-ui'
import { SparklesOutline } from '@vicons/ionicons5'
import { useProviderStore } from '../stores/provider'
import { useGeneratorStore } from '../stores/generator'
import { optimizePrompt, quickOptimize, type OptimizeOptions, type OptimizeResult } from '../api/optimize'
import type { LLMProvider } from '../types/provider'

interface HistoryEntry {
  input: string
  result: OptimizeResult
  followUpHint: string
  diffAdded: string[]
  diffRemoved: string[]
}

const props = defineProps<{
  prompt: string
}>()

const emit = defineEmits<{
  (e: 'update:prompt', prompt: string): void
  (e: 'apply', prompt: string, negativePrompt?: string): void
}>()

const message = useMessage()
const providerStore = useProviderStore()
const generatorStore = useGeneratorStore()

const localPrompt = ref(props.prompt)
const selectedLLMId = ref<string | null>(null)
const selectedScene = ref<string>('general')
const selectedStyle = ref<string>('general')
const optimizing = ref(false)
const progress = ref(0)
const error = ref<string | null>(null)
const showConfigModal = ref(false)
const llmApiKeys = ref<Record<string, string>>({})
const followUpQuestion = ref('')

const history = ref<HistoryEntry[]>([])
const currentRound = ref(0)

const currentEntry = computed((): HistoryEntry | null => history.value[currentRound.value] ?? null)

const sceneOptions = [
  { label: '通用', value: 'general' },
  { label: '产品展示', value: 'product' },
  { label: '营销宣传', value: 'marketing' },
  { label: 'PPT配图', value: 'presentation' },
  { label: '人物肖像', value: 'portrait' },
  { label: '商业插画', value: 'illustration' }
]

const styleOptions = [
  { label: '通用风格', value: 'general' },
  { label: '专业商务', value: 'professional' },
  { label: '极简风格', value: 'minimalist' },
  { label: '创意风格', value: 'creative' },
  { label: '企业风格', value: 'corporate' },
  { label: '轻松风格', value: 'casual' }
]

const llmOptions = computed(() => {
  return providerStore.llmProviders
    .filter(p => p.apiKey)
    .map(p => ({
      label: `${p.name}${p.isFree ? ' (免费)' : ''}`,
      value: p.id
    }))
})

const selectedLLM = computed((): LLMProvider | null => {
  if (!selectedLLMId.value) return null
  return providerStore.getLLMProviderById(selectedLLMId.value) || null
})

watch(() => props.prompt, (val) => { localPrompt.value = val })
watch(localPrompt, (val) => { emit('update:prompt', val) })

function computeDiff(before: string, after: string): { added: string[]; removed: string[] } {
  const tokenize = (s: string) => s.toLowerCase().split(/[,\s]+/).filter(Boolean)
  const beforeTokens = new Set(tokenize(before))
  const afterTokens = new Set(tokenize(after))
  const added: string[] = []
  const removed: string[] = []
  for (const t of afterTokens) { if (!beforeTokens.has(t)) added.push(t) }
  for (const t of beforeTokens) { if (!afterTokens.has(t)) removed.push(t) }
  return { added, removed }
}

function pushHistory(input: string, result: OptimizeResult, followUpHint: string = ''): void {
  const last = history.value.length > 0 ? history.value[history.value.length - 1] : null
  const prevResult = last?.result?.optimizedPrompt || input
  const diff = result.optimizedPrompt ? computeDiff(prevResult, result.optimizedPrompt) : { added: [], removed: [] }
  history.value.push({ input, result, followUpHint, diffAdded: diff.added, diffRemoved: diff.removed })
  currentRound.value = history.value.length - 1
}

function applyToStore(result: OptimizeResult) {
  if (result.optimizedPrompt) {
    localPrompt.value = result.optimizedPrompt
    emit('apply', result.optimizedPrompt, result.negativePrompt || '')
  }
  if (result.negativePrompt) {
    generatorStore.negativePrompt = result.negativePrompt
  }
}

async function doOptimize(input: string, followUpHint?: string): Promise<void> {
  const llm = selectedLLM.value
  if (!llm) return

  optimizing.value = true
  progress.value = 0
  error.value = null

  const progressInterval = setInterval(() => {
    if (progress.value < 90) progress.value += Math.random() * 10
  }, 300)

  try {
    const options: OptimizeOptions = {
      scene: selectedScene.value as OptimizeOptions['scene'],
      style: selectedStyle.value as OptimizeOptions['style']
    }
    const optimizeResult = await optimizePrompt(input, llm, { ...options, modelType: generatorStore.model || '' })
    progress.value = 100

    if (optimizeResult.success) {
      pushHistory(input, optimizeResult, followUpHint || '')
      applyToStore(optimizeResult)
      message.success('优化完成，已自动填入')
    } else {
      error.value = optimizeResult.error || '优化失败'
    }
  } catch (e: unknown) {
    error.value = (e as Error).message || '请求失败'
  } finally {
    clearInterval(progressInterval)
    optimizing.value = false
  }
}

async function handleOptimize(): Promise<void> {
  if (!selectedLLM.value || !localPrompt.value.trim()) return
  await doOptimize(localPrompt.value)
}

async function handleFollowUp(): Promise<void> {
  if (!followUpQuestion.value.trim()) return
  const lastIdx = history.value.length - 1
  if (lastIdx < 0) return
  const lastEntry = history.value[lastIdx]
  if (!lastEntry) return
  const previousPrompt = lastEntry.result.optimizedPrompt || lastEntry.input
  const inputText = `[当前提示词] ${previousPrompt}\n[调整要求] ${followUpQuestion.value}`
  const hint = followUpQuestion.value
  followUpQuestion.value = ''
  await doOptimize(inputText, hint)
}

function handleQuickOptimize(): void {
  if (!localPrompt.value.trim()) return
  const options: OptimizeOptions = {
    scene: selectedScene.value as OptimizeOptions['scene'],
    style: selectedStyle.value as OptimizeOptions['style']
  }
  const optimized = quickOptimize(localPrompt.value, options)
  localPrompt.value = optimized
  message.success('已快速优化')
}

function quickAdjust(text: string): void {
  followUpQuestion.value = text
  handleFollowUp()
}

function currentEntryData(): HistoryEntry | null {
  return history.value[currentRound.value] ?? null
}

function copyResult(): void {
  const entry = currentEntryData()
  if (!entry?.result.optimizedPrompt) return
  navigator.clipboard.writeText(entry.result.optimizedPrompt)
    .then(() => message.success('已复制'))
    .catch(() => message.error('复制失败'))
}

function switchToLatest(): void {
  currentRound.value = history.value.length - 1
  const entry = history.value[history.value.length - 1]
  if (entry) applyToStore(entry.result)
}

function handleRollback(): void {
  const target = currentEntryData()
  if (!target) return
  history.value = history.value.slice(0, currentRound.value + 1)
  applyToStore(target.result)
  message.success(`已回退到第 ${currentRound.value + 1} 版`)
}

function saveLLMConfig(preset: typeof providerStore.llmProviderPresets[0]): void {
  const apiKey = llmApiKeys.value[preset.type]
  if (!apiKey) { message.warning('请输入 API Key'); return }
  const existing = providerStore.llmProviders.find(p => p.type === preset.type)
  if (existing) {
    providerStore.updateLLMProvider(existing.id, { apiKey })
  } else {
    providerStore.addLLMProvider({
      name: preset.name, type: preset.type, llmEndpoint: preset.llmEndpoint,
      apiKey, models: preset.models, llmModel: preset.llmModel, isFree: preset.isFree
    })
  }
  message.success('配置已保存')
  showConfigModal.value = false
}

onMounted(() => {
  const firstAvailable = llmOptions.value[0]
  if (firstAvailable) selectedLLMId.value = firstAvailable.value
  providerStore.llmProviders.forEach(p => { llmApiKeys.value[p.type] = p.apiKey || '' })
})
</script>

<style scoped>
.prompt-optimizer {
  padding: 8px;
  background: #fafafa;
  border-radius: 8px;
}

.optimizer-hint {
  padding: 8px 12px;
  background: #fffbe6;
  border-radius: 6px;
  border: 1px solid #ffe58f;
  margin-top: 8px;
}

.result-section { margin-top: 12px; }
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-card { background: var(--bg-card); max-height: 500px; overflow-y: auto; }
.result-item { margin-bottom: 8px; }

.result-main {
  padding: 6px 8px;
  background: var(--brand-50);
  border-radius: var(--radius-sm);
  border: 1px solid var(--brand-200);
}

.result-chinese {
  padding: 6px 8px;
  background: #eef2ff;
  border-radius: var(--radius-sm);
  border: 1px solid #c7d2fe;
}

.neg-box {
  padding: 4px 8px;
  background: #fef2f2;
  border-radius: var(--radius-sm);
  border: 1px solid #fecaca;
}

.round-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: var(--bg-subtle);
  border-radius: var(--radius-sm);
}

.diff-box {
  background: #fafbfc;
  border-radius: 6px;
  padding: 6px;
  border: 1px solid #eee;
}

.diff-content { margin-top: 2px; }
.diff-added { margin-bottom: 2px; }
.diff-removed { margin-bottom: 2px; }
.adjustment-hint { margin-bottom: 4px; }

.suggestions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e8e8e8;
}

.suggestions ul {
  margin: 4px 0 0 0;
  padding-left: 16px;
  font-size: 12px;
  color: #666;
}

.suggestions li { margin-bottom: 2px; }

.explanation-box {
  background: #f8fdf8;
  border-radius: 6px;
  padding: 8px;
  border-left: 3px solid #52c41a;
}

.follow-up {
  padding-top: 8px;
  border-top: 1px dashed #e8e8e8;
  margin-bottom: 8px;
}

.knowledge-refs { margin-bottom: 8px; }

.knowledge-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 0;
}

.llm-preset-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 8px;
}

.preset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 500;
}
</style>
