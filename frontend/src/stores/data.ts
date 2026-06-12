import { defineStore } from 'pinia'
import { apiService } from '../api'
import type { UnifiedTemplate, KnowledgeEntry } from '../types/api'

export const useDataStore = defineStore('data', {
  state: () => ({
    /** 统一模板库（来自 /api/unified-templates） */
    unifiedTemplates: [] as UnifiedTemplate[],
    /** 知识库（术语/公式/案例等，来自 /api/knowledge） */
    knowledge: [] as KnowledgeEntry[],
    loaded: false,
    loading: false
  }),
  getters: {
    /** 向后兼容：cases = knowledge 中 type=case 的条目 */
    cases: (state) => state.knowledge.filter((e) => e.type === 'case'),
    /** 向后兼容：模板按 source 分组 */
    workTemplates: (state) =>
      state.unifiedTemplates.filter((t) => t.source === 'work_templates'),
    videoTemplates: (state) =>
      state.unifiedTemplates.filter((t) => t.type === 'video'),
    festivalTemplates: (state) =>
      state.unifiedTemplates.filter((t) => t.source === 'festival_templates'),
    /** 向后兼容：旧 templates 字段 = 所有 image 模板 */
    templates: (state) =>
      state.unifiedTemplates.filter((t) => t.type === 'image'),
    /** 知识子集 */
    terms: (state) => state.knowledge.filter((e) => e.type === 'term'),
    formulas: (state) => state.knowledge.filter((e) => e.type === 'formula'),
    industries: (state) => state.knowledge.filter((e) => e.type === 'industry'),
    negativePacks: (state) => state.knowledge.filter((e) => e.type === 'negative_pack'),
    caseEntries: (state) => state.knowledge.filter((e) => e.type === 'case'),
  },
  actions: {
    async loadAll() {
      if (this.loaded) return
      this.loading = true
      try {
        const [templates, knowledge] = await Promise.all([
          apiService.getUnifiedTemplates().catch(() => [] as UnifiedTemplate[]),
          apiService.getKnowledge().catch(() => [] as KnowledgeEntry[]),
        ])
        this.unifiedTemplates = templates
        this.knowledge = knowledge
        this.loaded = true
      } catch (error) {
        console.error('Failed to load data from backend:', error)
      } finally {
        this.loading = false
      }
    }
  }
})
