/**
 * 参数预设配置
 * 包含模型、尺寸等参数的解释和预设建议
 */

export interface ParamPreset {
  value: string
  label: string
  description: string
  tips?: string
}

export interface ParamConfig {
  name: string
  description: string
  presets: ParamPreset[]
}

export const modelPresets: ParamConfig = {
  name: '模型',
  description: '不同模型有不同的风格倾向和生成特点',
  presets: [
    {
      value: 'doubao-seedream-4-5-251128',
      label: '豆包 Seedream 4.5',
      description: '字节跳动最新模型，支持4K高清，中文理解优秀',
      tips: '适合：高质量写实、中文提示词、角色一致性'
    },
    {
      value: 'doubao-seedream-4-0-250828',
      label: '豆包 Seedream 4.0',
      description: '稳定版本，生成速度快',
      tips: '适合：日常使用、快速出图'
    },
    {
      value: 'cogview-3-flash',
      label: '智谱 CogView-3-Flash',
      description: '免费模型，速度快',
      tips: '适合：测试、学习、快速预览'
    },
    {
      value: 'cogview-3-plus',
      label: '智谱 CogView-3-Plus',
      description: '高质量模型，细节丰富',
      tips: '适合：高质量出图、商业用途'
    },
    {
      value: 'dall-e-3',
      label: 'DALL-E 3',
      description: 'OpenAI最新模型，创意性强',
      tips: '适合：创意设计、艺术创作'
    },
    {
      value: 'dall-e-2',
      label: 'DALL-E 2',
      description: '经典模型，性价比高',
      tips: '适合：日常使用、快速生成'
    }
  ]
}

export const sizePresets: ParamConfig = {
  name: '尺寸',
  description: '图片分辨率，影响构图和用途',
  presets: [
    {
      value: '1024x1024',
      label: '正方形 (1:1)',
      description: '标准正方形，适合头像、产品图',
      tips: '适合：社交媒体头像、产品展示'
    },
    {
      value: '1024x1792',
      label: '竖版 (9:16)',
      description: '手机屏幕比例，适合手机壁纸',
      tips: '适合：手机壁纸、短视频封面'
    },
    {
      value: '1792x1024',
      label: '横版 (16:9)',
      description: '宽屏比例，适合风景、横幅',
      tips: '适合：文章配图、网站横幅'
    },
    {
      value: '2048x2048',
      label: '高清正方形 (2K)',
      description: '高清版本，细节更丰富',
      tips: '适合：高质量输出、打印'
    },
    {
      value: '1440x2560',
      label: '小红书封面 (9:16高清)',
      description: '小红书推荐尺寸，高清竖版',
      tips: '适合：小红书封面、抖音封面'
    },
    {
      value: '1920x2560',
      label: '高清竖版 (3:4)',
      description: '高清竖版，适合电商主图',
      tips: '适合：电商主图、海报'
    },
    {
      value: '2560x1440',
      label: '高清横版 (16:9)',
      description: '2K横版，适合桌面壁纸',
      tips: '适合：桌面壁纸、演示文稿'
    },
    {
      value: '512x512',
      label: '小图 (512px)',
      description: '快速生成，适合预览',
      tips: '适合：快速测试、批量预览'
    }
  ]
}

export const stylePresets = [
  { value: '写实风格，照片级真实感', label: '写实' },
  { value: '动漫风格，二次元', label: '动漫' },
  { value: '水彩画风格', label: '水彩' },
  { value: '油画风格', label: '油画' },
  { value: '赛博朋克风格', label: '赛博朋克' },
  { value: '中国水墨风格', label: '国风水墨' },
  { value: '像素艺术风格', label: '像素风' },
  { value: '概念艺术风格', label: '概念艺术' },
  { value: '极简主义风格', label: '极简' },
  { value: '电影感，电影级光效', label: '电影感' }
]

export const qualityKeywords = [
  { value: '4K超高清', label: '4K' },
  { value: '细节丰富', label: '高细节' },
  { value: '杰作，最佳质量', label: '杰作' },
  { value: '专业摄影', label: '专业' },
  { value: '虚化背景，景深效果', label: '景深' }
]

export const lightingKeywords = [
  { value: '丁达尔效应，光束穿透', label: '丁达尔' },
  { value: '逆光，轮廓光', label: '逆光' },
  { value: '电影感光效', label: '电影光' },
  { value: '霓虹灯光', label: '霓虹' },
  { value: '黄金时刻，日落光线', label: '黄金时刻' },
  { value: '柔和光线', label: '柔光' }
]

export function getModelDescription(modelId: string): string | undefined {
  return modelPresets.presets.find(p => p.value === modelId)?.description
}

export function getSizeDescription(size: string): string | undefined {
  return sizePresets.presets.find(p => p.value === size)?.description
}
