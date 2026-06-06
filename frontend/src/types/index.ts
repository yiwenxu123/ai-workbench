/**
 * 应用类型定义
 */

export type ThemeMode = 'light' | 'dark'

export interface AppConfig {
  apiKey: string
  apiEndpoint: string
  theme: ThemeMode
}

export type { Prompt, History, PromptCategory, PromptFormData, PromptTemplate, TemplateCategory, TemplateFormData, VideoHistory, GalleryItem, VideoTemplate, VideoTemplateCategory } from './db'
export type { GenerateParams, GenerateResult, ConfigResult, ApiError, ModelManifest, ModelCapability } from './api'
export type { ApiProvider, VisionProvider, LLMProvider, ProviderType, ProviderCapability } from './provider'
export type { EnhancedHistory, Note } from './history'
