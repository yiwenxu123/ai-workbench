/**
 * 应用配置
 * 集中管理环境变量和常量配置
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  appTitle: import.meta.env.VITE_APP_TITLE || 'AI绘图工作台',
  
  request: {
    timeout: 120000,
    maxRetries: 3,
    retryDelay: 1000,
  },
  
  prompt: {
    maxLength: 4000,
    minLength: 1,
  },
  
  history: {
    maxItems: 50,
    imagePreviewSize: 48,
  },
  
  storage: {
    apiKey: 'ai_studio_api_key',
    apiEndpoint: 'ai_studio_api_endpoint',
    theme: 'ai_studio_theme',
  },
} as const

export type Config = typeof config
