/**
 * 工作流模板状态管理
 * 保存和管理可复用的生成配置
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Dexie, { type Table } from 'dexie'

export interface WorkflowTemplate {
  id?: number
  name: string
  description: string
  category: string
  config: {
    model: string
    size: string
    promptTemplate: string
    negativePrompt?: string
  }
  tags: string[]
  createdAt: Date
  updatedAt: Date
}

class WorkflowDB extends Dexie {
  workflows!: Table<WorkflowTemplate, number>

  constructor() {
    super('AIStudioWorkflows')
    this.version(1).stores({
      workflows: '++id, name, category, *tags, createdAt, updatedAt'
    })
  }
}

const workflowDB = new WorkflowDB()

export const defaultTemplates: WorkflowTemplate[] = [
  {
    name: '小红书封面',
    description: '适合小红书平台的封面图片，鲜艳吸睛',
    category: 'social',
    config: {
      model: 'doubao-seedream-4-5-251128',
      size: '1024x1792',
      promptTemplate: '{主题}，鲜艳色彩，时尚感，高级感，社交媒体风格，吸引眼球',
    },
    tags: ['社交媒体', '小红书', '封面'],
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: '公众号配图',
    description: '适合微信公众号文章配图，简约大气',
    category: 'social',
    config: {
      model: 'doubao-seedream-4-5-251128',
      size: '1792x1024',
      promptTemplate: '{主题}，简约风格，干净背景，专业感，适合文章配图',
    },
    tags: ['社交媒体', '公众号', '配图'],
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: '电商主图',
    description: '电商产品主图，白底干净',
    category: 'ecommerce',
    config: {
      model: 'doubao-seedream-4-5-251128',
      size: '1024x1024',
      promptTemplate: '{产品}，白底，产品摄影，专业打光，高清细节，电商主图',
    },
    tags: ['电商', '产品', '主图'],
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: '头像生成',
    description: '个人头像，人像优化',
    category: 'portrait',
    config: {
      model: 'doubao-seedream-4-5-251128',
      size: '1024x1024',
      promptTemplate: '{描述}，头像，人像摄影，柔和光效，细节丰富，高质量',
    },
    tags: ['人像', '头像', '个人'],
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: '概念艺术',
    description: '游戏/电影概念设计风格',
    category: 'art',
    config: {
      model: 'doubao-seedream-4-5-251128',
      size: '2048x2048',
      promptTemplate: '{主题}，概念艺术，电影感，史诗氛围，细节丰富，专业概念设计',
    },
    tags: ['艺术', '概念', '设计'],
    createdAt: new Date(),
    updatedAt: new Date()
  }
]

export const useWorkflowStore = defineStore('workflow', () => {
  const templates = ref<WorkflowTemplate[]>([])
  const searchText = ref('')
  const selectedCategory = ref('all')

  const categories = [
    { value: 'all', label: '全部' },
    { value: 'social', label: '社交媒体' },
    { value: 'ecommerce', label: '电商' },
    { value: 'portrait', label: '人像' },
    { value: 'art', label: '艺术创作' },
    { value: 'custom', label: '自定义' }
  ]

  const filteredTemplates = computed(() => {
    let result = templates.value
    
    if (selectedCategory.value !== 'all') {
      result = result.filter(t => t.category === selectedCategory.value)
    }
    
    if (searchText.value) {
      const search = searchText.value.toLowerCase()
      result = result.filter(t =>
        t.name.toLowerCase().includes(search) ||
        t.description.toLowerCase().includes(search) ||
        t.tags.some(tag => tag.toLowerCase().includes(search))
      )
    }
    
    return result
  })

  async function load(): Promise<void> {
    const saved = await workflowDB.workflows.toArray()
    
    if (saved.length === 0) {
      for (const template of defaultTemplates) {
        await workflowDB.workflows.add(template)
      }
      templates.value = defaultTemplates
    } else {
      templates.value = saved
    }
  }

  async function add(template: Omit<WorkflowTemplate, 'id' | 'createdAt' | 'updatedAt'>): Promise<void> {
    const now = new Date()
    await workflowDB.workflows.add({
      ...template,
      createdAt: now,
      updatedAt: now
    })
    await load()
  }

  async function update(id: number, data: Partial<WorkflowTemplate>): Promise<void> {
    await workflowDB.workflows.update(id, {
      ...data,
      updatedAt: new Date()
    })
    await load()
  }

  async function remove(id: number): Promise<void> {
    await workflowDB.workflows.delete(id)
    await load()
  }

  function applyTemplate(template: WorkflowTemplate, variables: Record<string, string> = {}): string {
    let prompt = template.config.promptTemplate
    
    Object.entries(variables).forEach(([key, value]) => {
      prompt = prompt.replace(new RegExp(`\\{${key}\\}`, 'g'), value)
    })
    
    return prompt
  }

  return {
    templates,
    searchText,
    selectedCategory,
    categories,
    filteredTemplates,
    load,
    add,
    update,
    remove,
    applyTemplate
  }
})
