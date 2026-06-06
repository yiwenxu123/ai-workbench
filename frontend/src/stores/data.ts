import { defineStore } from 'pinia'
import axios from 'axios'
import { config } from '../config'

export const useDataStore = defineStore('data', {
  state: () => ({
    cases: [] as any[],
    templates: [] as any[],
    videoTemplates: [] as any[],
    workTemplates: [] as any[],
    festivalTemplates: [] as any[],
    knowledge: [] as any[],
    loaded: false,
    loading: false
  }),
  getters: {
    terms: (state) => state.knowledge.filter((e: any) => e.type === 'term'),
    formulas: (state) => state.knowledge.filter((e: any) => e.type === 'formula'),
    industries: (state) => state.knowledge.filter((e: any) => e.type === 'industry'),
    negativePacks: (state) => state.knowledge.filter((e: any) => e.type === 'negative_pack'),
    caseEntries: (state) => state.knowledge.filter((e: any) => e.type === 'case'),
  },
  actions: {
    async loadAll() {
      if (this.loaded) return
      this.loading = true
      const baseURL = config.apiBaseUrl
      try {
        const [casesRes, templatesRes, videoTemplatesRes, knowledgeRes, workTemplatesRes, festivalTemplatesRes] = await Promise.all([
          axios.get(`${baseURL}/api/cases`).catch(() => ({ data: [] })),
          axios.get(`${baseURL}/api/templates`).catch(() => ({ data: [] })),
          axios.get(`${baseURL}/api/video-templates`).catch(() => ({ data: [] })),
          axios.get(`${baseURL}/api/knowledge`).catch(() => ({ data: [] })),
          axios.get(`${baseURL}/api/work-templates`).catch(() => ({ data: [] })),
          axios.get(`${baseURL}/api/festival-templates`).catch(() => ({ data: [] }))
        ])
        
        this.cases = casesRes.data || []
        this.templates = templatesRes.data || []
        this.videoTemplates = videoTemplatesRes.data || []
        this.knowledge = knowledgeRes.data || []
        this.workTemplates = workTemplatesRes.data || []
        this.festivalTemplates = festivalTemplatesRes.data || []
        this.loaded = true
      } catch (error) {
        console.error('Failed to load data from backend:', error)
      } finally {
        this.loading = false
      }
    }
  }
})
