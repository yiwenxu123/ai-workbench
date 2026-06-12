/**
 * 知识库类型定义
 * 原 data/terminology.ts 和 data/caseLibrary.ts 中的类型迁移到此处
 */

// ── 术语词典 ──

export type TermCategory = 'style' | 'lighting' | 'composition' | 'color' | 'material' | 'mood' | 'technique'

export interface TermEntry {
  id: string
  name: string
  nameEn?: string
  category: TermCategory
  description: string
  usage: string
  examples: string[]
  relatedTerms?: string[]
  tips?: string
  lastVerified?: string
}

// ── 案例库 ──

export interface CaseExample {
  id: string
  name: string
  category: 'product' | 'drama' | 'animation' | 'film' | 'social' | 'ecommerce' | 'brand'
  description: string
  prompt: string
  negativePrompt?: string
  model: string
  parameters: {
    size?: string
    duration?: string
    style?: string
  }
  tips: string[]
  tags: string[]
  author?: string
  videoUrl?: string
  embedUrl?: string
  thumbnailUrl?: string
  isUserCase?: boolean
  subjectPlaceholder?: string
  lastVerified?: string
}
