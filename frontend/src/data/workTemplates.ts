/**
 * 工作场景模板 — 类型定义和分类配置
 * 数据已迁移到 SQLite，通过 useDataStore 从 API 获取
 */

export interface TemplateField {
  key: string
  label: string
  placeholder: string
  required: boolean
  options?: string[]
  description?: string
}

export interface WorkTemplate {
  id: string
  name: string
  category: 'product' | 'marketing' | 'presentation' | 'portrait' | 'illustration' | 'social'
  description: string
  prompt: string
  negativePrompt?: string
  recommendedSize: string
  recommendedModel?: string
  tips: string[]
  tags: string[]
  preview?: string
  fields?: TemplateField[]
}

export interface TemplateCategory {
  id: string
  name: string
  icon: string
  description: string
}

export const templateCategories: TemplateCategory[] = [
  { id: 'product', name: '产品展示', icon: 'Package', description: '电商产品图、商品展示' },
  { id: 'marketing', name: '营销宣传', icon: 'Megaphone', description: '广告图、促销海报' },
  { id: 'presentation', name: 'PPT配图', icon: 'BarChart3', description: '演示文稿、报告配图' },
  { id: 'portrait', name: '人物肖像', icon: 'User', description: '职业照、形象照' },
  { id: 'illustration', name: '商业插画', icon: 'Palette', description: '品牌插画、创意设计' },
  { id: 'social', name: '社媒素材', icon: 'Smartphone', description: '公众号、小红书配图' }
]

// 数据已迁移到 SQLite，通过 useDataStore.workTemplates 从 API 获取
