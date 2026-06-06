/**
 * 提示词模板状态管理
 * 统一管理官方模板和用户模板
 */

import { defineStore } from 'pinia'
import { ref, computed, toRaw } from 'vue'
import { db } from '../db'
import type { PromptTemplate, TemplateFormData, TemplateCategory } from '../types'
import { workTemplates } from '../data/workTemplates'

const OFFICIAL_TEMPLATES_KEY = 'ai_studio_official_templates_initialized'

export const useTemplateStore = defineStore('template', () => {
  const templates = ref<PromptTemplate[]>([])
  const searchText = ref('')
  const selectedCategory = ref<TemplateCategory | 'all'>('all')
  const showModal = ref(false)
  const editingTemplate = ref<PromptTemplate | null>(null)

  const officialTemplates = computed(() => 
    templates.value.filter(t => t.isOfficial)
  )

  const userTemplates = computed(() => 
    templates.value.filter(t => !t.isOfficial)
  )

  const filteredTemplates = computed(() => {
    let result = templates.value

    if (selectedCategory.value !== 'all') {
      result = result.filter(t => t.category === selectedCategory.value)
    }

    if (searchText.value) {
      const query = searchText.value.toLowerCase()
      result = result.filter(t =>
        t.name.toLowerCase().includes(query) ||
        t.content.toLowerCase().includes(query) ||
        t.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    return result
  })

  async function load(): Promise<void> {
    const userTemplatesData = await db.templates
      .where('isOfficial')
      .equals(0)
      .toArray()
    
    const officialFromDb = await db.templates
      .where('isOfficial')
      .equals(1)
      .toArray()

    const initialized = localStorage.getItem(OFFICIAL_TEMPLATES_KEY)
    
    if (!initialized) {
      await initOfficialTemplates()
      templates.value = [...convertWorkTemplates(), ...userTemplatesData]
    } else {
      templates.value = [...officialFromDb, ...userTemplatesData]
    }
  }

  function convertWorkTemplates(): PromptTemplate[] {
    return workTemplates.map(t => ({
      name: t.name,
      content: t.prompt,
      category: t.category as TemplateCategory,
      tags: [...t.tags],
      isOfficial: true,
      negativePrompt: t.negativePrompt,
      recommendedSize: t.recommendedSize,
      tips: [...t.tips],
      placeholders: extractPlaceholders(t.prompt),
      createdAt: new Date(),
      updatedAt: new Date()
    }))
  }

  function extractPlaceholders(content: string): string[] {
    const matches = content.match(/\[([A-Z_]+)\]/g)
    return matches ? [...new Set(matches.map(m => m.slice(1, -1)))] : []
  }

  async function initOfficialTemplates(): Promise<void> {
    const officialData = convertWorkTemplates()
    
    for (const template of officialData) {
      await db.templates.add(template)
    }
    
    localStorage.setItem(OFFICIAL_TEMPLATES_KEY, 'true')
  }

  async function add(data: TemplateFormData): Promise<void> {
    const now = new Date()
    await db.templates.add({
      name: data.name,
      content: data.content,
      category: data.category,
      tags: [...toRaw(data.tags)],
      isOfficial: false,
      negativePrompt: data.negativePrompt,
      recommendedSize: data.recommendedSize,
      tips: data.tips ? [...toRaw(data.tips)] : undefined,
      placeholders: extractPlaceholders(data.content),
      createdAt: now,
      updatedAt: now
    })
    await load()
  }

  async function update(id: number, data: TemplateFormData): Promise<void> {
    await db.templates.update(id, {
      name: data.name,
      content: data.content,
      category: data.category,
      tags: [...toRaw(data.tags)],
      negativePrompt: data.negativePrompt,
      recommendedSize: data.recommendedSize,
      tips: data.tips ? [...toRaw(data.tips)] : undefined,
      placeholders: extractPlaceholders(data.content),
      updatedAt: new Date()
    })
    await load()
  }

  async function remove(id: number): Promise<void> {
    await db.templates.delete(id)
    await load()
  }

  async function duplicate(id: number): Promise<void> {
    const template = templates.value.find(t => t.id === id)
    if (!template) return

    await add({
      name: `${template.name} (副本)`,
      content: template.content,
      category: template.category,
      tags: [...template.tags],
      negativePrompt: template.negativePrompt,
      recommendedSize: template.recommendedSize,
      tips: template.tips ? [...template.tips] : undefined
    })
  }

  function startEdit(template: PromptTemplate): void {
    editingTemplate.value = template
    showModal.value = true
  }

  function cancelEdit(): void {
    editingTemplate.value = null
    showModal.value = false
  }

  return {
    templates,
    searchText,
    selectedCategory,
    showModal,
    editingTemplate,
    officialTemplates,
    userTemplates,
    filteredTemplates,
    load,
    add,
    update,
    remove,
    duplicate,
    startEdit,
    cancelEdit,
    extractPlaceholders
  }
})
