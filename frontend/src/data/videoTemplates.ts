/**
 * 视频生成模板库
 * 包含电商、企业、科普、文化等行业场景模板
 */

import type { ShotType, CameraMovement, CameraAngle } from './shotLanguage'

export type VideoTemplateCategory = 'product' | 'brand' | 'education' | 'culture' | 'social' | 'festival'

export interface VideoTemplateField {
  key: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'multiselect'
  placeholder: string
  options?: { value: string; label: string }[]
  required: boolean
  defaultValue?: string
}

export interface VideoTemplateShot {
  type: ShotType
  movement: CameraMovement
  angle?: CameraAngle
  duration: number
  description: string
}

export interface VideoTemplate {
  id: string
  name: string
  category: VideoTemplateCategory
  description: string
  icon: string
  fields: VideoTemplateField[]
  recommendedShots: VideoTemplateShot[]
  promptTemplate: string
  negativePrompt?: string
  recommendedDuration: number
  recommendedResolution: string
  tips: string[]
  tags: string[]
}

export const videoTemplateCategories = [
  { id: 'product', name: '电商产品', icon: 'Package', description: '产品展示、商品广告' },
  { id: 'brand', name: '企业品牌', icon: 'Building2', description: '企业宣传、品牌故事' },
  { id: 'education', name: '科普教育', icon: 'BookOpen', description: '知识科普、教学视频' },
  { id: 'culture', name: '文化内容', icon: 'Palette', description: '非遗展示、文化传承' },
  { id: 'social', name: '社媒内容', icon: 'Smartphone', description: '短视频、社交媒体' },
  { id: 'festival', name: '节庆营销', icon: 'PartyPopper', description: '节日活动、营销视频' }
]

export const videoTemplates: VideoTemplate[] = [
  {
    id: 'product-showcase',
    name: '高端产品展示片',
    category: 'product',
    description: '适合电商产品、科技产品的专业展示视频',
    icon: 'Package',
    fields: [
      { key: 'productName', label: '产品名称', type: 'text', placeholder: '如：智能手表', required: true },
      { key: 'material', label: '材质描述', type: 'text', placeholder: '如：钛合金、玻璃', required: false },
      { key: 'features', label: '核心卖点', type: 'textarea', placeholder: '如：健康监测、防水', required: false },
      {
        key: 'scene',
        label: '展示场景',
        type: 'select',
        placeholder: '选择场景',
        required: true,
        options: [
          { value: 'studio', label: '简约工作室' },
          { value: 'nature', label: '自然光场景' },
          { value: 'tech', label: '科技感背景' },
          { value: 'lifestyle', label: '生活场景' }
        ],
        defaultValue: 'studio'
      }
    ],
    recommendedShots: [
      { type: 'full', movement: 'static', angle: 'low_angle', duration: 2, description: '低角度全景展示' },
      { type: 'close_up', movement: 'dolly_in', duration: 3, description: '缓慢推近特写' },
      { type: 'extreme_close_up', movement: 'tracking', duration: 3, description: '环绕展示细节' }
    ],
    promptTemplate: '{productName}，{material}材质，{features}，在{scene}中缓慢旋转，镜头从低角度仰拍开始，缓慢推近至特写，微距展示纹理，电影感商业广告风格，4K高清，studio lighting',
    negativePrompt: 'blurry, low quality, distorted, watermark, text, logo',
    recommendedDuration: 8,
    recommendedResolution: '1080p',
    tips: ['建议时长5-10秒', '可添加品牌Logo', '适合抖音/视频号'],
    tags: ['电商', '产品', '科技']
  },
  {
    id: 'brand-story',
    name: '企业使命开场片',
    category: 'brand',
    description: '适合企业宣传、品牌故事的开场视频',
    icon: 'Building2',
    fields: [
      { key: 'companyName', label: '企业名称', type: 'text', placeholder: '如：XX科技', required: true },
      { key: 'mission', label: '企业使命', type: 'textarea', placeholder: '如：用科技改变生活', required: false },
      {
        key: 'scene',
        label: '展示场景',
        type: 'select',
        placeholder: '选择场景',
        required: true,
        options: [
          { value: 'office', label: '现代化办公室' },
          { value: 'lab', label: '实验室' },
          { value: 'factory', label: '生产车间' },
          { value: 'outdoor', label: '户外场景' }
        ],
        defaultValue: 'office'
      }
    ],
    recommendedShots: [
      { type: 'extreme_long', movement: 'crane_down', duration: 3, description: '无人机远景进入大楼' },
      { type: 'medium', movement: 'tracking', duration: 4, description: '中景跟拍团队协作' },
      { type: 'close_up', movement: 'static', duration: 3, description: '特写面部表情' }
    ],
    promptTemplate: '{companyName}企业宣传片，{mission}，{scene}场景，团队协作讨论，专注工作特写，产品研发过程，纪实电影感，鼓舞人心，暖色调，cinematic documentary, motivational, warm color grading',
    negativePrompt: 'blurry, low quality, cluttered background, unprofessional',
    recommendedDuration: 10,
    recommendedResolution: '1080p',
    tips: ['突出企业文化', '展示团队精神', '适合官网/展会'],
    tags: ['企业', '品牌', '宣传']
  },
  {
    id: 'education-science',
    name: '科学原理图解动画',
    category: 'education',
    description: '适合知识科普、教学视频的动画展示',
    icon: 'BookOpen',
    fields: [
      { key: 'concept', label: '科学概念', type: 'text', placeholder: '如：光合作用', required: true },
      { key: 'process', label: '过程描述', type: 'textarea', placeholder: '描述科学过程', required: false },
      {
        key: 'style',
        label: '动画风格',
        type: 'select',
        placeholder: '选择风格',
        required: true,
        options: [
          { value: '3d', label: '3D实验室' },
          { value: 'flat', label: '扁平化设计' },
          { value: 'infographic', label: '信息图表风格' }
        ],
        defaultValue: '3d'
      }
    ],
    recommendedShots: [
      { type: 'full', movement: 'static', duration: 2, description: '全景展示整体' },
      { type: 'medium', movement: 'dolly_in', duration: 4, description: '特写关键步骤' },
      { type: 'close_up', movement: 'tracking', duration: 3, description: '动态转场' }
    ],
    promptTemplate: '{concept}科学原理图解，{process}，{style}风格，3D模型分解展示，动态箭头指示，粒子流动效果，教育动画，简洁明了，educational animation, infographic style, motion graphics',
    negativePrompt: 'blurry, low quality, complex, confusing',
    recommendedDuration: 10,
    recommendedResolution: '1080p',
    tips: ['保持简洁明了', '突出关键信息', '适合教学场景'],
    tags: ['科普', '教育', '动画']
  },
  {
    id: 'culture-craft',
    name: '传统工艺制作流程',
    category: 'culture',
    description: '适合非遗展示、文化传承的视频',
    icon: 'Palette',
    fields: [
      { key: 'craftName', label: '工艺名称', type: 'text', placeholder: '如：陶瓷制作', required: true },
      { key: 'materials', label: '制作材料', type: 'text', placeholder: '如：陶土、釉料', required: false },
      {
        key: 'scene',
        label: '展示场景',
        type: 'select',
        placeholder: '选择场景',
        required: true,
        options: [
          { value: 'workshop', label: '古风作坊' },
          { value: 'nature', label: '自然光环境' },
          { value: 'modern', label: '现代工作室' }
        ],
        defaultValue: 'workshop'
      }
    ],
    recommendedShots: [
      { type: 'extreme_close_up', movement: 'static', duration: 3, description: '特写手部动作' },
      { type: 'medium', movement: 'tracking', duration: 4, description: '中景人物与环境' },
      { type: 'full', movement: 'dolly_out', duration: 3, description: '缓慢拉远展示成品' }
    ],
    promptTemplate: '{craftName}传统工艺制作，{materials}，{scene}场景，手工艺人专注制作特写，工具使用细节，成品展示，纪录片质感，中国风，自然光效，documentary style, Chinese traditional aesthetic, natural lighting',
    negativePrompt: 'blurry, low quality, historically inaccurate, disrespectful',
    recommendedDuration: 10,
    recommendedResolution: '1080p',
    tips: ['尊重传统文化', '展示工艺细节', '适合文化推广'],
    tags: ['文化', '非遗', '传统']
  },
  {
    id: 'social-product',
    name: '短视频产品种草',
    category: 'social',
    description: '适合抖音、小红书的产品种草视频',
    icon: 'Smartphone',
    fields: [
      { key: 'productName', label: '产品名称', type: 'text', placeholder: '如：口红', required: true },
      { key: 'highlight', label: '产品亮点', type: 'textarea', placeholder: '如：显白、持久', required: false },
      {
        key: 'vibe',
        label: '视频氛围',
        type: 'select',
        placeholder: '选择氛围',
        required: true,
        options: [
          { value: 'fresh', label: '清新自然' },
          { value: 'trendy', label: '潮流时尚' },
          { value: 'cozy', label: '温馨舒适' }
        ],
        defaultValue: 'fresh'
      }
    ],
    recommendedShots: [
      { type: 'close_up', movement: 'dolly_in', duration: 2, description: '产品特写' },
      { type: 'medium', movement: 'tracking', duration: 3, description: '使用场景展示' },
      { type: 'close_up', movement: 'static', duration: 2, description: '效果展示' }
    ],
    promptTemplate: '{productName}产品种草视频，{highlight}，{vibe}氛围，产品特写，使用场景展示，效果对比，小红书风格，INS风，vlog封面风格，活泼可爱，xiaohongshu style, aesthetic, lifestyle',
    negativePrompt: 'blurry, low quality, watermark, text, distorted',
    recommendedDuration: 5,
    recommendedResolution: '1080p',
    tips: ['节奏要快', '突出产品亮点', '适合竖版视频'],
    tags: ['种草', '社媒', '短视频']
  },
  {
    id: 'festival-spring',
    name: '春节营销视频',
    category: 'festival',
    description: '适合春节、新年营销活动视频',
    icon: 'Gift',
    fields: [
      { key: 'brandName', label: '品牌名称', type: 'text', placeholder: '如：XX品牌', required: true },
      { key: 'slogan', label: '活动Slogan', type: 'text', placeholder: '如：新春快乐', required: false },
      {
        key: 'element',
        label: '节日元素',
        type: 'multiselect',
        placeholder: '选择元素',
        required: true,
        options: [
          { value: 'lantern', label: '灯笼' },
          { value: 'firework', label: '烟花' },
          { value: 'couplet', label: '春联' },
          { value: 'zodiac', label: '生肖' }
        ],
        defaultValue: 'lantern'
      }
    ],
    recommendedShots: [
      { type: 'extreme_long', movement: 'crane_down', duration: 3, description: '城市夜景全景' },
      { type: 'medium', movement: 'dolly_in', duration: 3, description: '节日氛围特写' },
      { type: 'close_up', movement: 'static', duration: 2, description: '品牌展示' }
    ],
    promptTemplate: '{brandName}春节营销视频，{slogan}，{element}元素，朱红色金色主色调，节日氛围浓厚，烟花绽放，灯笼高挂，现代国潮风格，温暖喜庆，Chinese New Year, festive, red and gold',
    negativePrompt: 'blurry, low quality, tacky, gaudy, overly decorated',
    recommendedDuration: 8,
    recommendedResolution: '1080p',
    tips: ['色彩要喜庆', '突出节日氛围', '适合朋友圈传播'],
    tags: ['春节', '节日', '营销']
  }
]

export function getVideoTemplatesByCategory(category: VideoTemplateCategory): VideoTemplate[] {
  return videoTemplates.filter(t => t.category === category)
}

export function getVideoTemplateById(id: string): VideoTemplate | undefined {
  return videoTemplates.find(t => t.id === id)
}

export function searchVideoTemplates(query: string): VideoTemplate[] {
  const lowerQuery = query.toLowerCase()
  return videoTemplates.filter(t => 
    t.name.toLowerCase().includes(lowerQuery) ||
    t.description.toLowerCase().includes(lowerQuery) ||
    t.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
  )
}

export function generatePromptFromTemplate(
  template: VideoTemplate,
  fieldValues: Record<string, string | string[]>
): string {
  let prompt = template.promptTemplate
  
  for (const field of template.fields) {
    const value = fieldValues[field.key]
    const replacement = Array.isArray(value)
      ? value.join('、')
      : value || field.defaultValue || ''
    
    prompt = prompt.replace(`{${field.key}}`, replacement)
  }
  
  return prompt
}

export const videoModels = [
  { value: 'kling-v1', label: '可灵 V1', description: '性价比高，适合日常使用', provider: 'kling' },
  { value: 'kling-v1-5', label: '可灵 V1.5', description: '画质提升，适合高质量需求', provider: 'kling' },
  { value: 'jimeng-v1', label: '即梦 V1', description: '字节跳动，中文理解好', provider: 'jimeng' },
  { value: 'runway-gen3', label: 'Runway Gen-3', description: '专业级，运镜丰富', provider: 'runway' },
  { value: 'vidu-v1', label: 'Vidu V1', description: '动漫风格专精', provider: 'vidu' }
]

export const videoNegativePrompts = {
  common: 'blurry, low quality, distorted, watermark, text, logo, deformed, bad anatomy, disfigured, mutation',
  product: 'unprofessional logo placement, distorted product shape, unrealistic lighting, cheap looking, low quality render',
  person: 'unrealistic facial features, unnatural skin texture, inconsistent clothing, awkward pose',
  corporate: 'cluttered background, messy office, unprofessional attire, low resolution'
}
