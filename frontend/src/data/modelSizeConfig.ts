/**
 * 模型尺寸配置
 * 定义每个模型支持的尺寸、最小像素要求、推荐尺寸等
 */

export interface ModelSizeConfig {
  modelId: string
  modelName: string
  provider: string
  minPixels: number
  maxPixels: number
  recommendedSizes: string[]
  supportedSizes: string[]
  autoScale: boolean
  scaleNote?: string
  note?: string
}

export const modelSizeConfigs: ModelSizeConfig[] = [
  {
    modelId: 'doubao-seedream-4-5-251128',
    modelName: '豆包 Seedream 4.5',
    provider: 'doubao',
    minPixels: 1024 * 1024,
    maxPixels: 4096 * 4096,
    recommendedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    supportedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440', '1024x1024', '1024x1792', '1792x1024'],
    autoScale: true,
    scaleNote: '小于 2048 的尺寸会自动放大',
    note: '豆包模型支持 2K/4K 高清输出'
  },
  {
    modelId: 'doubao-seedream-4-0-250828',
    modelName: '豆包 Seedream 4.0',
    provider: 'doubao',
    minPixels: 1024 * 1024,
    maxPixels: 4096 * 4096,
    recommendedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    supportedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440', '1024x1024', '1024x1792', '1792x1024'],
    autoScale: true,
    scaleNote: '小于 2048 的尺寸会自动放大',
    note: '豆包模型稳定版本'
  },
  {
    modelId: 'cogview-3-flash',
    modelName: '智谱 CogView-3-Flash',
    provider: 'zhipu',
    minPixels: 512 * 512,
    maxPixels: 2048 * 2048,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
    autoScale: false,
    note: '免费模型，速度快'
  },
  {
    modelId: 'cogview-3-plus',
    modelName: '智谱 CogView-3-Plus',
    provider: 'zhipu',
    minPixels: 512 * 512,
    maxPixels: 2048 * 2048,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
    autoScale: false,
    note: '高质量模型，细节丰富'
  },
  {
    modelId: 'wanx-v1',
    modelName: '通义万相 V1',
    provider: 'aliyun',
    minPixels: 3686400,
    maxPixels: 4096 * 4096,
    recommendedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    supportedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    autoScale: false,
    note: '图片尺寸至少需要 1920x1920 像素 (约 369 万像素)'
  },
  {
    modelId: 'wanx-xl',
    modelName: '通义万相 XL',
    provider: 'aliyun',
    minPixels: 3686400,
    maxPixels: 4096 * 4096,
    recommendedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    supportedSizes: ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    autoScale: false,
    note: '图片尺寸至少需要 1920x1920 像素 (约 369 万像素)'
  },
  {
    modelId: 'dall-e-3',
    modelName: 'DALL-E 3',
    provider: 'openai',
    minPixels: 1024 * 1024,
    maxPixels: 1792 * 1024,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    autoScale: false,
    note: 'OpenAI 最新模型，创意性强'
  },
  {
    modelId: 'dall-e-2',
    modelName: 'DALL-E 2',
    provider: 'openai',
    minPixels: 512 * 512,
    maxPixels: 1024 * 1024,
    recommendedSizes: ['1024x1024', '512x512'],
    supportedSizes: ['1024x1024', '512x512', '256x256'],
    autoScale: false,
    note: '经典模型，性价比高'
  },
  {
    modelId: 'qwen-image-plus',
    modelName: '通义千问 Qwen-Image-Plus',
    provider: 'aliyun',
    minPixels: 512 * 512,
    maxPixels: 4096 * 4096,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    autoScale: false,
    note: '阿里云通义千问图像模型，支持中英文提示词，画质优秀'
  },
  {
    modelId: 'qwen-image',
    modelName: '通义千问 Qwen-Image',
    provider: 'aliyun',
    minPixels: 512 * 512,
    maxPixels: 4096 * 4096,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048', '1440x2560', '1920x2560', '2560x1440'],
    autoScale: false,
    note: '通义千问标准图像模型，性价比之选'
  },
  {
    modelId: 'qwen-image-2.0-pro',
    modelName: '通义千问 Qwen-Image-2.0-Pro',
    provider: 'aliyun',
    minPixels: 512 * 512,
    maxPixels: 2048 * 2048,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048'],
    autoScale: false,
    note: '通义千问 2.0 Pro，文字渲染、真实质感更强'
  },
  {
    modelId: 'qwen-image-2.0',
    modelName: '通义千问 Qwen-Image-2.0',
    provider: 'aliyun',
    minPixels: 512 * 512,
    maxPixels: 2048 * 2048,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048'],
    autoScale: false,
    note: '通义千问 2.0 标准版，轻量化兼顾效果'
  },
  {
    modelId: 'cogview-4',
    modelName: '智谱 CogView-4',
    provider: 'zhipu',
    minPixels: 512 * 512,
    maxPixels: 2048 * 2048,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
    autoScale: false,
    note: '智谱 CogView 最新版，支持中文提示词'
  },
  {
    modelId: 'cogview-4-plus',
    modelName: '智谱 CogView-4-Plus',
    provider: 'zhipu',
    minPixels: 512 * 512,
    maxPixels: 2048 * 2048,
    recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
    supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
    autoScale: false,
    note: 'CogView-4 增强版，细节和光影表现更丰富'
  }
]

export function getModelSizeConfig(modelId: string): ModelSizeConfig | undefined {
  return modelSizeConfigs.find(c => c.modelId === modelId)
}

export function getSizesForModel(modelId: string): string[] {
  const config = getModelSizeConfig(modelId)
  return config?.supportedSizes || ['1024x1024', '1024x1792', '1792x1024', '2048x2048']
}

export function getRecommendedSizesForModel(modelId: string): string[] {
  const config = getModelSizeConfig(modelId)
  return config?.recommendedSizes || ['1024x1024']
}

export function isSizeValidForModel(modelId: string, size: string): { valid: boolean; reason?: string } {
  const config = getModelSizeConfig(modelId)
  if (!config) {
    return { valid: true }
  }
  
  const parts = size.split('x')
  const width = parseInt(parts[0] || '0', 10)
  const height = parseInt(parts[1] || '0', 10)
  const pixels = width * height
  
  if (pixels < config.minPixels) {
    return {
      valid: false,
      reason: `该模型要求最小 ${config.minPixels.toLocaleString()} 像素，当前尺寸 ${pixels.toLocaleString()} 像素不足`
    }
  }
  
  if (pixels > config.maxPixels) {
    return {
      valid: false,
      reason: `该模型最大支持 ${config.maxPixels.toLocaleString()} 像素，当前尺寸超出限制`
    }
  }
  
  return { valid: true }
}

export function getSizeOptionsForModel(modelId: string): Array<{ value: string; label: string; recommended: boolean; warning?: string }> {
  const config = getModelSizeConfig(modelId)
  const allSizes = ['2048x2048', '1440x2560', '1920x2560', '2560x1440', '1024x1024', '1024x1792', '1792x1024', '512x512']
  
  return allSizes
    .filter(size => config ? config.supportedSizes.includes(size) : true)
    .map(size => {
      const parts = size.split('x')
      const width = parseInt(parts[0] || '0', 10)
      const height = parseInt(parts[1] || '0', 10)
      const pixels = width * height
      const isRecommended = config?.recommendedSizes.includes(size) || false
      const ratio = width > height ? '横版' : (width < height ? '竖版' : '正方形')
      
      let warning: string | undefined
      if (config && pixels < config.minPixels) {
        warning = `尺寸不足`
      }
      
      const label = `${size} (${ratio})${isRecommended ? ' 推荐' : ''}${warning ? ' ' + warning : ''}`
      
      return {
        value: size,
        label,
        recommended: isRecommended,
        warning
      }
    })
}

export const defaultSizeConfig: ModelSizeConfig = {
  modelId: 'default',
  modelName: '默认模型',
  provider: 'generic',
  minPixels: 512 * 512,
  maxPixels: 4096 * 4096,
  recommendedSizes: ['1024x1024', '1024x1792', '1792x1024'],
  supportedSizes: ['1024x1024', '1024x1792', '1792x1024', '2048x2048', '1440x2560', '1920x2560', '2560x1440'],
  autoScale: false
}
