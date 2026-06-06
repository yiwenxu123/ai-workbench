import { ref } from 'vue'
import type { KnowledgeEntry } from '../types/api'

export type CreationScene =
  | 'ecommerce'
  | 'social'
  | 'presentation'
  | 'portrait'
  | 'illustration'
  | 'video'
  | 'edit'
  | 'general'

export interface CreationContextState {
  scene: CreationScene
  userIntent: string
  matchedTemplateId: string
  recommendedKnowledge: KnowledgeEntry[]
  optimizationHistory: Array<{ prompt: string; explanation: string }>
  lastGeneratedImageUrl: string
  generationModel: string
  generationSize: string
}

const state = ref<CreationContextState>({
  scene: 'general',
  userIntent: '',
  matchedTemplateId: '',
  recommendedKnowledge: [],
  optimizationHistory: [],
  lastGeneratedImageUrl: '',
  generationModel: '',
  generationSize: '',
})

export function useCreationContext() {
  function setScene(scene: CreationScene) {
    state.value.scene = scene
  }

  function setIntent(intent: string) {
    state.value.userIntent = intent
  }

  function setTemplate(templateId: string) {
    state.value.matchedTemplateId = templateId
  }

  function addKnowledgeRefs(entries: KnowledgeEntry[]) {
    state.value.recommendedKnowledge = entries
  }

  function addOptimization(prompt: string, explanation: string) {
    state.value.optimizationHistory.push({ prompt, explanation })
  }

  function setGenerationResult(imageUrl: string, model: string, size: string) {
    state.value.lastGeneratedImageUrl = imageUrl
    state.value.generationModel = model
    state.value.generationSize = size
  }

  function clear() {
    state.value = {
      scene: 'general',
      userIntent: '',
      matchedTemplateId: '',
      recommendedKnowledge: [],
      optimizationHistory: [],
      lastGeneratedImageUrl: '',
      generationModel: '',
      generationSize: '',
    }
  }

  function clearOptimization() {
    state.value.optimizationHistory = []
    state.value.recommendedKnowledge = []
  }

  return {
    context: state,
    setScene,
    setIntent,
    setTemplate,
    addKnowledgeRefs,
    addOptimization,
    setGenerationResult,
    clear,
    clearOptimization,
  }
}
