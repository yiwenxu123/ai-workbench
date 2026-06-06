/**
 * IndexedDB 数据库配置 (使用 Dexie.js)
 * 存储：提示词、生成历史、用户设置、笔记、模板、视频历史、作品库、用户案例
 */

import Dexie, { type Table } from 'dexie'
import type { Prompt, History, PromptTemplate, VideoHistory, GalleryItem, VideoTemplate } from '../types'
import type { Note } from '../types/history'

export interface UserCase {
  id?: number
  name: string
  category: string
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
  videoUrl?: string
  embedUrl?: string
  thumbnailUrl?: string
  createdAt: Date
  updatedAt?: Date
}

class AppDatabase extends Dexie {
  prompts!: Table<Prompt, number>
  history!: Table<History, number>
  notes!: Table<Note, number>
  templates!: Table<PromptTemplate, number>
  videoHistory!: Table<VideoHistory, number>
  gallery!: Table<GalleryItem, number>
  videoTemplates!: Table<VideoTemplate, number>
  userCases!: Table<UserCase, number>

  constructor() {
    super('AIDrawingStudio')
    
    this.version(7).stores({
      prompts: '++id, title, content, *tags, category, createdAt, updatedAt',
      history: '++id, prompt, model, size, imageUrl, providerId, *tags, isFavorite, rating, createdAt',
      notes: '++id, targetType, targetId, *tags, createdAt, updatedAt',
      templates: '++id, name, content, category, isOfficial, *tags, createdAt, updatedAt',
      videoHistory: '++id, prompt, model, duration, resolution, videoUrl, sourceImageId, providerId, *tags, isFavorite, rating, createdAt',
      gallery: '++id, type, itemId, prompt, *tags, isFavorite, createdAt',
      videoTemplates: '++id, name, category, isOfficial, *tags, createdAt, updatedAt',
      userCases: '++id, name, category, *tags, createdAt'
    })
  }
}

export const db = new AppDatabase()

export async function initDatabase(): Promise<void> {
  try {
    const count = await db.prompts.count()
    console.log(`Database initialized with ${count} prompts`)
  } catch (error) {
    console.error('Database initialization error:', error)
    await Dexie.delete('AIDrawingStudio')
    console.log('Database reset complete, please refresh the page')
    const resetError = new Error('数据库已重置，请刷新页面') as Error & { cause?: unknown }
    resetError.cause = error
    throw resetError
  }
}
