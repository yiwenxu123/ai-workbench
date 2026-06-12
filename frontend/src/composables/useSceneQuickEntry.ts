/**
 * 场景创作快捷入口逻辑
 */
import { ref, computed, watch } from 'vue'
import type { Component } from 'vue'
import { useMessage } from 'naive-ui'
import { ShoppingBag, Megaphone, BarChart3, User, Film, Pencil } from 'lucide-vue-next'
import { useGeneratorStore, useProviderStore } from '../stores'
import { useCreationContext, type CreationScene } from './useCreationContext'
import { optimizePrompt, type OptimizeResult } from '../api/optimize'

export type QuickTaskType = 'image' | 'video' | 'edit'

export interface QuickTask {
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

const TASK_SCENE_MAP: Record<string, CreationScene> = {
  ecommerce: 'ecommerce',
  'social-poster': 'social',
  presentation: 'presentation',
  portrait: 'portrait',
  'image-to-video': 'video',
  'edit-image': 'edit',
}

export const QUICK_TASKS: QuickTask[] = [
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

export function resolveQuickSize(ratio: string): string {
  const map: Record<string, string> = {
    '1:1': '1024x1024',
    '3:4': '768x1024',
    '16:9': '1792x1024',
    '9:16': '1024x1792',
  }
  return map[ratio] || '1024x1024'
}

export function useSceneQuickEntry(options: {
  onNavigateToVideo: (prompt: string, negativePrompt: string) => void
  onNavigateToEdit: (instruction: string) => void
}) {
  const generatorStore = useGeneratorStore()
  const providerStore = useProviderStore()
  const message = useMessage()
  const { setScene, addOptimization } = useCreationContext()

  const showQuickModal = ref(false)
  const selectedQuickTask = ref<QuickTask | null>(null)
  const quickTaskInput = ref('')
  const quickTaskRatio = ref('1:1')
  const useQuickAI = ref(false)
  const quickAIWorking = ref(false)
  const quickAIResult = ref<OptimizeResult | null>(null)
  let userEditedMainPrompt = false

  const generatedQuickPrompt = computed(() => {
    if (!selectedQuickTask.value || !quickTaskInput.value.trim()) return ''
    return selectedQuickTask.value.promptTemplate.replace('{need}', quickTaskInput.value.trim())
  })

  const promptExplanation = computed(() => {
    if (!selectedQuickTask.value || !quickTaskInput.value.trim()) return ''
    const need = quickTaskInput.value.trim()
    const explanations: Record<string, string> = {
      ecommerce: `主体：${need} | 风格：商业产品摄影，干净背景突出产品 | 构图：产品居中清晰可见 | 光线：柔和棚拍光 | 用途：电商主图上架展示`,
      'social-poster': `主体：${need} | 风格：视觉冲击力，现代社交媒体风格 | 构图：视觉焦点明确，留出文字排版空间 | 光线：明亮饱满 | 用途：小红书/社媒传播`,
      presentation: `主体：${need} | 风格：简洁商务科技感，不抢正文 | 构图：清晰留白充足 | 光线：均匀专业 | 用途：PPT演示配图`,
      portrait: `主体：${need} | 风格：专业形象照，真实自然 | 构图：半身/肩部以上 | 光线：柔和自然 | 用途：头像/个人介绍`,
      'image-to-video': `动作：${need} | 风格：自然连贯，电影感 | 镜头：稳定推进 | 节奏：5秒短视频，细节连贯`,
      'edit-image': `编辑意图：${need}`,
    }
    return explanations[selectedQuickTask.value.id] || ''
  })

  watch(quickTaskInput, (val) => {
    if (!selectedQuickTask.value || !val.trim() || selectedQuickTask.value.type !== 'image') return
    if (userEditedMainPrompt) return
    generatorStore.prompt = selectedQuickTask.value.promptTemplate.replace('{need}', val.trim())
  })

  watch(quickTaskRatio, (ratio) => {
    if (!selectedQuickTask.value) return
    generatorStore.size = resolveQuickSize(ratio)
  })

  function onMainPromptInput() {
    userEditedMainPrompt = true
  }

  function selectQuickTask(task: QuickTask) {
    if (selectedQuickTask.value?.id === task.id) return
    const prevInput = quickTaskInput.value
    const prevAI = useQuickAI.value
    const prevAIResult = quickAIResult.value

    selectedQuickTask.value = task
    quickTaskInput.value = prevInput || ''
    useQuickAI.value = prevAI
    quickAIResult.value = prevAIResult
    userEditedMainPrompt = false

    if (task.recommendedSize === '1440x2560') quickTaskRatio.value = '9:16'
    else if (task.recommendedSize === '2560x1440') quickTaskRatio.value = '16:9'
    else quickTaskRatio.value = '1:1'

    setScene(TASK_SCENE_MAP[task.id] || 'general')
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
        if (result.optimizedPrompt) {
          addOptimization(result.optimizedPrompt, result.explanation || 'AI 优化')
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

  async function applyQuickTask() {
    if (!selectedQuickTask.value || !quickTaskInput.value.trim()) return

    if (selectedQuickTask.value.type === 'video') {
      showQuickModal.value = false
      options.onNavigateToVideo(generatedQuickPrompt.value, '')
      return
    }

    if (selectedQuickTask.value.type === 'edit') {
      showQuickModal.value = false
      options.onNavigateToEdit(generatedQuickPrompt.value)
      return
    }

    const finalPrompt = useQuickAI.value && quickAIResult.value?.optimizedPrompt
      ? quickAIResult.value.optimizedPrompt
      : generatedQuickPrompt.value
    const finalNegative = useQuickAI.value && quickAIResult.value?.negativePrompt
      ? quickAIResult.value.negativePrompt
      : selectedQuickTask.value.negativePrompt

    generatorStore.prompt = finalPrompt
    generatorStore.negativePrompt = finalNegative
    showQuickModal.value = false

    const success = await generatorStore.generate()
    if (success) {
      message.success('生成成功！')
    }
  }

  return {
    showQuickModal,
    selectedQuickTask,
    quickTaskInput,
    quickTaskRatio,
    useQuickAI,
    quickAIWorking,
    quickAIResult,
    generatedQuickPrompt,
    promptExplanation,
    onMainPromptInput,
    selectQuickTask,
    onQuickAIChange,
    applyQuickTask,
  }
}
