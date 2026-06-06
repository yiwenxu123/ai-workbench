<template>
  <div class="beginner-wizard">
    <div class="wizard-heading">
      <h2>我是新手，我想...</h2>
      <p class="heading-desc">不用先懂模型、参数和镜头语言。先选目标，说一句人话需求，工作台会帮你整理成可生成的提示词。</p>
    </div>

    <!-- 任务卡片网格 -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <n-gi v-for="task in tasks" :key="task.id">
        <button
          type="button"
          class="task-card"
          :class="{ selected: selectedTask?.id === task.id }"
          @click="selectTask(task)"
        >
          <div class="task-icon">
            <n-icon :component="task.icon" />
          </div>
          <div class="task-info">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-desc">{{ task.description }}</div>
          </div>
        </button>
      </n-gi>
    </n-grid>

    <!-- 工作区：左右分栏 -->
    <div v-if="selectedTask" class="wizard-workspace mt-4">
      <!-- 左侧：表单 -->
      <div class="workspace-sider">
        <h3 class="sider-title">描述需求</h3>
        <n-form label-placement="top">
          <n-form-item :label="selectedTask.question">
            <n-input
              v-model:value="userNeed"
              type="textarea"
              :rows="3"
              :placeholder="selectedTask.placeholder"
            />
          </n-form-item>
        </n-form>

        <div class="ai-box" v-if="providerStore.hasConfiguredLLM && userNeed">
          <div class="ai-box-header">
            <div class="ai-title">
              <n-icon :component="Sparkles" /> AI 智能调优
            </div>
            <n-switch v-model:value="useAI" size="small" @update:value="onAIChange" />
          </div>
          <div class="ai-box-body" v-if="useAI">
            <div v-if="aiOptimizing" class="ai-loading">
              <n-spin size="small" />
              <n-text depth="3">正在优化提示词...</n-text>
            </div>
            <div v-else-if="aiResult" class="ai-result">
              <n-alert type="success" :show-icon="false" class="mb-2">
                {{ aiResult.optimizedPromptCN || aiResult.explanation || '已生成专业提示词' }}
              </n-alert>
            </div>
            <div v-else class="ai-empty">
              <n-button size="small" type="primary" secondary @click="handleAIOptimize" :loading="aiOptimizing">
                开始深度优化
              </n-button>
            </div>
          </div>
        </div>

        <div class="template-prompt" v-if="!useAI && userNeed">
          <n-alert type="info" :show-icon="false">
            将使用模板结构：<br/>
            <span style="font-size: 12px; color: #666">{{ activePrompt }}</span>
          </n-alert>
        </div>

        <n-form-item label="生成比例" class="mt-3" v-if="selectedTask.type === 'image'">
          <n-radio-group v-model:value="selectedRatio" size="small">
            <n-radio-button value="1:1">1:1 正方</n-radio-button>
            <n-radio-button value="3:4">3:4 竖版</n-radio-button>
            <n-radio-button value="16:9">16:9 横版</n-radio-button>
          </n-radio-group>
        </n-form-item>

        <n-button 
          type="primary" 
          block 
          size="large" 
          class="mt-4" 
          :loading="isGenerating"
          :disabled="!userNeed"
          @click="handleGenerate"
        >
          {{ selectedTask.actionLabel }}
        </n-button>
      </div>

      <!-- 右侧：画布 -->
      <div class="workspace-content">
        <div class="result-header">
          <span class="result-title">生成结果</span>
        </div>
        
        <div v-if="generatorStore.error" class="error-state">
          <n-alert type="error" :show-icon="true" closable @close="generatorStore.error = null">
            {{ generatorStore.error }}
          </n-alert>
        </div>
        
        <div v-else-if="isGenerating" class="generating-state">
          <n-progress
            type="circle"
            :percentage="Math.round(currentProgress)"
            :show-indicator="true"
            status="success"
          />
          <span class="mt-3">正在生成中...</span>
        </div>
        
        <div v-else-if="currentResult" class="result-display">
          <template v-if="selectedTask.type === 'image'">
            <img :src="currentResult" class="result-image" />
          </template>
          <template v-else-if="selectedTask.type === 'video'">
            <video :src="currentResult" controls class="result-video" />
          </template>
        </div>
        
        <div v-else class="empty-state">
          <div class="empty-icon"><n-icon :component="Sparkles" /></div>
          <div class="empty-text">填写需求并点击生成</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NAlert, NButton, NForm, NFormItem, NGi, NGrid, NSpin,
  NInput, NText, NSwitch, NRadioGroup, NRadioButton, NProgress, useMessage, NIcon
} from 'naive-ui'
import { ShoppingBag, Megaphone, BarChart3, User, Film, Pencil, Sparkles } from 'lucide-vue-next'
import { useProviderStore } from '../stores/provider'
import { useGeneratorStore } from '../stores/generator'
import { useVideoStore } from '../stores/video'
import { optimizePrompt, type OptimizeResult } from '../api/optimize'

type BeginnerTaskType = 'image' | 'video' | 'edit'

interface BeginnerTask {
  id: string
  type: BeginnerTaskType
  icon: any
  title: string
  description: string
  question: string
  placeholder: string
  promptTemplate: string
  negativePrompt: string
  recommendedSize: string
  actionLabel: string
  explanation: string
}

const emit = defineEmits<{
  applyEdit: [instruction: string]
}>()

const message = useMessage()
const providerStore = useProviderStore()
const generatorStore = useGeneratorStore()
const videoStore = useVideoStore()

const userNeed = ref('')
const aiOptimizing = ref(false)
const aiResult = ref<OptimizeResult | null>(null)
const useAI = ref(false)
const selectedRatio = ref('1:1')

/** 按任务 ID 保存用户输入，切换任务时不丢失 */
const taskCache = ref<Record<string, { userNeed: string; aiResult: OptimizeResult | null; useAI: boolean; ratio: string }>>({})

const tasks: BeginnerTask[] = [
  {
    id: 'ecommerce',
    type: 'image',
    icon: ShoppingBag,
    title: '做电商主图',
    description: '商品清晰、背景干净、适合上架',
    question: '你要卖什么？希望什么风格？',
    placeholder: '例如：一款白色保温杯，适合年轻女性，干净高级感',
    promptTemplate: '电商产品主图，主体是「{need}」，干净背景，商业摄影，产品细节清晰，柔和棚拍光，高级质感，适合电商上架',
    negativePrompt: '模糊，低质量，水印，文字，变形，杂乱背景',
    recommendedSize: '1024x1024',
    actionLabel: '生成图片',
    explanation: '提示词补齐了主体、用途、背景、光线和质感，模型更容易生成可用的商品图。'
  },
  {
    id: 'social-poster',
    type: 'image',
    icon: Megaphone,
    title: '做社媒海报',
    description: '有冲击力，适合小红书/公众号',
    question: '你要宣传什么内容？',
    placeholder: '例如：春季咖啡新品上市，温暖、有活力、适合小红书',
    promptTemplate: '社交媒体宣传海报，主题是「{need}」，视觉焦点明确，色彩吸引人，现代设计，留出文字排版空间，高质量商业视觉',
    negativePrompt: '低清晰度，文字错误，水印，画面拥挤，主体不清',
    recommendedSize: '1440x2560',
    actionLabel: '生成图片',
    explanation: '提示词强调主题、视觉焦点和排版空间，适合后续再加标题文案。'
  },
  {
    id: 'presentation',
    type: 'image',
    icon: BarChart3,
    title: '做PPT配图',
    description: '简洁专业，不抢正文',
    question: '这页 PPT 想表达什么？',
    placeholder: '例如：AI 正在帮助团队提升内容生产效率',
    promptTemplate: 'PPT 专业配图，表达「{need}」，简洁构图，商务科技感，低干扰背景，留白充足，清晰高级，适合演示文稿',
    negativePrompt: '过度复杂，刺眼颜色，水印，错误文字，低质量',
    recommendedSize: '2560x1440',
    actionLabel: '生成图片',
    explanation: '提示词降低了画面噪音，并要求留白，方便直接放进演示文稿。'
  },
  {
    id: 'portrait',
    type: 'image',
    icon: User,
    title: '做头像/形象照',
    description: '专业头像、个人 IP、团队照风格',
    question: '你想要什么人物形象？',
    placeholder: '例如：一位内容运营女生，亲和、专业、浅色背景',
    promptTemplate: '专业人物形象照，人物设定「{need}」，自然表情，干净背景，柔和光线，真实质感，适合头像和个人介绍页',
    negativePrompt: '畸形五官，多余手指，低质量，过度美颜，水印',
    recommendedSize: '1024x1024',
    actionLabel: '生成图片',
    explanation: '提示词明确人物定位、表情、背景和用途，能减少跑偏和过度风格化。'
  },
  {
    id: 'image-to-video',
    type: 'video',
    icon: Film,
    title: '让图片动起来',
    description: '把图片变成短视频片段',
    question: '你希望画面怎么动？',
    placeholder: '例如：人物轻轻微笑，头发随风飘动，镜头慢慢推进',
    promptTemplate: '图生视频，画面动作是「{need}」，自然运动，镜头稳定，细节连贯，电影感，5秒短视频',
    negativePrompt: '',
    recommendedSize: '1440x2560',
    actionLabel: '生成视频',
    explanation: '视频提示词强调动作、镜头和连贯性，能帮助模型减少闪烁和突变。'
  },
  {
    id: 'edit-image',
    type: 'edit',
    icon: Pencil,
    title: '修改一张图',
    description: '换背景、改局部、扩图',
    question: '你想怎么修改图片？',
    placeholder: '例如：把背景换成浅色办公室，保持人物不变',
    promptTemplate: '{need}',
    negativePrompt: '',
    recommendedSize: '1024x1024',
    actionLabel: '前往图片编辑',
    explanation: '图片编辑更适合用直接指令，清楚说明保留什么、修改什么即可。'
  }
]

const selectedTask = ref<BeginnerTask | null>(tasks[0] ?? null)

const generatedPrompt = computed(() => {
  if (!selectedTask.value || !userNeed.value.trim()) return ''
  return selectedTask.value.promptTemplate.replace('{need}', userNeed.value.trim())
})

const activePrompt = computed(() => {
  if (useAI.value && aiResult.value?.optimizedPrompt) return aiResult.value.optimizedPrompt
  return generatedPrompt.value
})

const activeNegativePrompt = computed(() => {
  if (useAI.value && aiResult.value?.negativePrompt) return aiResult.value.negativePrompt
  return selectedTask.value?.negativePrompt || ''
})

const isGenerating = computed(() => {
  if (!selectedTask.value) return false
  if (selectedTask.value.type === 'video') return videoStore.status === 'generating'
  return generatorStore.status === 'generating'
})

const currentProgress = computed(() => {
  if (!selectedTask.value) return 0
  if (selectedTask.value.type === 'video') return videoStore.progress
  return generatorStore.progress
})

const currentResult = computed(() => {
  if (!selectedTask.value) return null
  if (selectedTask.value.type === 'video') return videoStore.lastVideo
  return generatorStore.lastImage
})

function selectTask(task: BeginnerTask) {
  // 保存当前任务的状态
  if (selectedTask.value) {
    taskCache.value[selectedTask.value.id] = {
      userNeed: userNeed.value,
      aiResult: aiResult.value,
      useAI: useAI.value,
      ratio: selectedRatio.value,
    }
  }

  selectedTask.value = task

  // 恢复新任务的状态
  const cached = taskCache.value[task.id]
  if (cached) {
    userNeed.value = cached.userNeed
    aiResult.value = cached.aiResult
    useAI.value = cached.useAI
    selectedRatio.value = cached.ratio
  } else {
    userNeed.value = ''
    aiResult.value = null
    useAI.value = false
    if (task.recommendedSize === '1024x1024') selectedRatio.value = '1:1'
    else if (task.recommendedSize === '1440x2560') selectedRatio.value = '9:16'
    else if (task.recommendedSize === '2560x1440') selectedRatio.value = '16:9'
  }
}

function onAIChange(val: boolean) {
  if (val && !aiResult.value && userNeed.value) {
    handleAIOptimize()
  }
}

async function handleAIOptimize() {
  const llmProvider = providerStore.defaultLLMProvider
  if (!llmProvider?.apiKey) {
    message.warning('请先在设置中配置大语言模型')
    useAI.value = false
    return
  }
  if (!generatedPrompt.value) return

  aiOptimizing.value = true
  aiResult.value = null

  try {
    const sceneMap: Record<string, 'product' | 'marketing' | 'presentation' | 'portrait' | 'illustration' | 'general'> = {
      ecommerce: 'product',
      'social-poster': 'marketing',
      presentation: 'presentation',
      portrait: 'portrait',
      'image-to-video': 'general',
      'edit-image': 'general'
    }
    const result = await optimizePrompt(
      generatedPrompt.value,
      llmProvider,
      {
        scene: sceneMap[selectedTask.value?.id || ''] || 'general',
        style: 'professional'
      }
    )
    if (result.success) {
      aiResult.value = result
      message.success('AI 深度优化完成')
    } else {
      message.error(result.error || '优化失败')
      useAI.value = false
    }
  } catch {
    message.error('优化请求失败')
    useAI.value = false
  } finally {
    aiOptimizing.value = false
  }
}

function resolveSize(ratio: string) {
  if (ratio === '1:1') return '1024x1024'
  if (ratio === '3:4') return '768x1024'
  if (ratio === '16:9') return '1792x1024'
  if (ratio === '9:16') return '1024x1792'
  return '1024x1024'
}

async function handleGenerate() {
  if (!selectedTask.value || !activePrompt.value) return
  
  if (selectedTask.value.type === 'video') {
    videoStore.prompt = activePrompt.value
    await videoStore.generate()
  } else if (selectedTask.value.type === 'edit') {
    emit('applyEdit', activePrompt.value)
  } else {
    generatorStore.prompt = activePrompt.value
    generatorStore.negativePrompt = activeNegativePrompt.value
    generatorStore.size = resolveSize(selectedRatio.value)
    await generatorStore.generate()
  }
}
</script>

<style scoped>
.beginner-wizard {
  width: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.wizard-heading {
  margin-bottom: 24px;
}

.wizard-heading h2 {
  margin: 0 0 6px 0;
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 700;
}

.heading-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.task-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  width: 100%;
  padding: 18px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s var(--ease-out);
}
.task-card:hover {
  border-color: var(--gray-300);
  box-shadow: var(--shadow-sm);
}
.task-card.selected {
  border-color: var(--brand-500);
  background: var(--brand-50);
  box-shadow: 0 0 0 1px var(--brand-500);
}

.task-icon { font-size: 28px; line-height: 1; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.task-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 3px;
}
.task-desc {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.wizard-workspace {
  display: flex;
  gap: var(--panel-gap, 20px);
  flex: 1;
  min-height: 400px;
}

.workspace-sider {
  flex: 0 0 380px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}

.sider-title {
  margin: 0 0 16px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.ai-box {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-top: 12px;
}
.ai-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--gray-50);
  border-bottom: 1px solid var(--border);
}
.ai-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.ai-box-body { padding: 14px; background: var(--bg-card); }

.ai-loading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-prompt {
  margin-top: 12px;
}

.workspace-content {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  position: relative;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.result-title {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.error-state {
  margin-bottom: 14px;
}

.empty-state, .generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  gap: 14px;
}
.empty-icon { font-size: 48px; margin-bottom: 4px; opacity: 0.35; display: flex; align-items: center; justify-content: center; color: var(--brand-400); }
.empty-text { font-size: 14px; color: var(--gray-400); }

.result-display {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.result-image, .result-video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

</style>
