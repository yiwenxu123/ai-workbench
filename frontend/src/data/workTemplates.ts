/**
 * 工作场景模板库
 * 针对产品图、营销图、PPT配图等商业场景
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

export const workTemplates: WorkTemplate[] = [
  {
    id: 'product-white-bg',
    name: '白底产品图',
    category: 'product',
    description: '纯净白底产品展示，适合电商主图',
    prompt: 'professional product photography, {SUBJECT}, clean white background, studio lighting, soft shadows, high detail, commercial quality, 4K resolution',
    negativePrompt: 'blurry, low quality, watermark, text, logo, distorted, background objects',
    recommendedSize: '1024x1024',
    tips: ['确保产品主体清晰', '光线均匀柔和', '适合淘宝、京东主图'],
    tags: ['电商', '白底', '产品图'],
    fields: [
      { key: 'SUBJECT', label: '产品名称', placeholder: '如：智能手表、口红、耳机', required: true }
    ]
  },
  {
    id: 'product-lifestyle',
    name: '场景化产品图',
    category: 'product',
    description: '产品在真实场景中的展示效果',
    prompt: 'lifestyle product photography, {SUBJECT} in {SCENE}, natural lighting, warm atmosphere, professional composition, shallow depth of field, commercial quality',
    negativePrompt: 'blurry, low quality, watermark, text, distorted, messy background',
    recommendedSize: '1024x1024',
    tips: ['选择与产品调性匹配的场景', '自然光效果更真实', '适合详情页展示'],
    tags: ['场景', '生活化', '详情页'],
    fields: [
      { key: 'SUBJECT', label: '产品名称', placeholder: '如：咖啡杯、香水', required: true },
      { key: 'SCENE', label: '展示场景', placeholder: '如：温馨的咖啡厅、阳光明媚的花园', required: true }
    ]
  },
  {
    id: 'product-closeup',
    name: '产品细节特写',
    category: 'product',
    description: '突出产品细节和质感',
    prompt: 'macro product photography, {SUBJECT} detail shot, extreme close-up, texture visible, studio lighting, sharp focus, commercial quality, high resolution',
    negativePrompt: 'blurry, out of focus, low quality, watermark, text',
    recommendedSize: '1024x1024',
    tips: ['展示材质纹理', '突出工艺细节', '适合高端产品'],
    tags: ['特写', '细节', '质感'],
    fields: [
      { key: 'SUBJECT', label: '产品名称', placeholder: '如：手表机芯、皮革纹理', required: true }
    ]
  },
  {
    id: 'marketing-banner',
    name: '促销横幅',
    category: 'marketing',
    description: '大促活动横幅背景图',
    prompt: 'promotional banner design, {THEME} theme, vibrant colors, dynamic composition, festive atmosphere, professional graphic design, clean space for text, 4K quality',
    negativePrompt: 'blurry, low quality, watermark, text, logo, cluttered',
    recommendedSize: '1792x1024',
    tips: ['预留文字空间', '色彩要吸引眼球', '适合618、双11等大促'],
    tags: ['促销', '横幅', '活动'],
    fields: [
      { key: 'THEME', label: '活动主题', placeholder: '如：双11、春节、618', required: true, options: ['双11', '春节', '618', '中秋', '国庆', '圣诞', '新年'] }
    ]
  },
  {
    id: 'marketing-poster',
    name: '品牌海报',
    category: 'marketing',
    description: '品牌形象宣传海报',
    prompt: 'brand poster design, {BRAND} concept, minimalist style, professional photography, high-end atmosphere, clean composition, corporate quality, 4K resolution',
    negativePrompt: 'blurry, low quality, watermark, text, distorted, amateur',
    recommendedSize: '1024x1792',
    tips: ['符合品牌调性', '构图简洁大气', '适合品牌宣传'],
    tags: ['品牌', '海报', '宣传'],
    fields: [
      { key: 'BRAND', label: '品牌概念', placeholder: '如：科技、时尚、环保', required: true, options: ['科技', '时尚', '环保', '健康', '奢华', '年轻'] }
    ]
  },
  {
    id: 'marketing-social',
    name: '社媒广告图',
    category: 'marketing',
    description: '社交媒体广告配图',
    prompt: 'social media advertisement, {PRODUCT} showcase, eye-catching, vibrant colors, modern design, professional quality, square format, Instagram style',
    negativePrompt: 'blurry, low quality, watermark, text, distorted',
    recommendedSize: '1024x1024',
    tips: ['视觉冲击力强', '适合信息流广告', '3秒内吸引注意'],
    tags: ['社媒', '广告', '信息流'],
    fields: [
      { key: 'PRODUCT', label: '推广产品', placeholder: '如：护肤品、电子产品', required: true }
    ]
  },
  {
    id: 'ppt-cover',
    name: 'PPT封面',
    category: 'presentation',
    description: '专业演示文稿封面背景',
    prompt: 'professional presentation cover, {TOPIC} theme, business style, clean background, modern design, corporate blue tones, minimalist, space for title, 16:9 format',
    negativePrompt: 'blurry, low quality, watermark, text, cluttered, cartoon',
    recommendedSize: '1792x1024',
    tips: ['预留标题空间', '色调专业稳重', '适合商务汇报'],
    tags: ['封面', '商务', '汇报'],
    fields: [
      { key: 'TOPIC', label: '演示主题', placeholder: '如：年度总结、项目汇报、产品发布', required: true }
    ]
  },
  {
    id: 'ppt-content',
    name: 'PPT内容页背景',
    category: 'presentation',
    description: '简洁的内容页背景图',
    prompt: 'presentation slide background, subtle gradient, professional business style, clean and minimal, soft colors, not distracting, corporate design',
    negativePrompt: 'busy, colorful, text, watermark, low quality, distracting',
    recommendedSize: '1792x1024',
    tips: ['背景简洁不抢眼', '色调柔和', '适合文字内容页'],
    tags: ['内容页', '背景', '简洁']
  },
  {
    id: 'ppt-data',
    name: '数据可视化背景',
    category: 'presentation',
    description: '数据展示页面背景',
    prompt: 'data visualization background, tech style, abstract geometric patterns, blue and white tones, modern design, clean space for charts, professional quality',
    negativePrompt: 'blurry, low quality, watermark, text, cluttered',
    recommendedSize: '1792x1024',
    tips: ['适合数据图表页', '科技感设计', '不干扰数据阅读'],
    tags: ['数据', '图表', '科技']
  },
  {
    id: 'portrait-business',
    name: '职业形象照',
    category: 'portrait',
    description: '专业商务形象照背景',
    prompt: 'professional business portrait background, {GENDER}, {AGE}, {STYLE}, studio lighting, neutral background, corporate style, high quality, sharp focus',
    negativePrompt: 'blurry, low quality, watermark, text, distorted, unprofessional',
    recommendedSize: '1024x1024',
    tips: ['背景简洁专业', '光线均匀', '适合LinkedIn、企业官网'],
    tags: ['职业', '形象', '商务'],
    fields: [
      { key: 'GENDER', label: '性别', placeholder: '选择性别', required: true, options: ['女性', '男性'] },
      { key: 'AGE', label: '年龄段', placeholder: '选择年龄段', required: false, options: ['青年', '中年', '成熟'] },
      { key: 'STYLE', label: '风格', placeholder: '选择风格', required: false, options: ['正装商务', '休闲商务', '创意时尚'] }
    ]
  },
  {
    id: 'portrait-team',
    name: '团队合影背景',
    category: 'portrait',
    description: '企业团队合影场景',
    prompt: 'corporate team photo background, {SCENE}, professional atmosphere, clean environment, natural lighting, business style',
    negativePrompt: 'blurry, low quality, watermark, text, cluttered, messy',
    recommendedSize: '1792x1024',
    tips: ['办公场景背景', '专业大气', '适合企业宣传'],
    tags: ['团队', '合影', '企业'],
    fields: [
      { key: 'SCENE', label: '场景', placeholder: '选择场景', required: true, options: ['现代办公室', '会议室', '公司前台', '落地窗前'] }
    ]
  },
  {
    id: 'illustration-brand',
    name: '品牌插画',
    category: 'illustration',
    description: '企业品牌风格插画',
    prompt: 'brand illustration, {BRAND} style, modern flat design, corporate colors, clean lines, professional quality, vector style, minimal and elegant',
    negativePrompt: 'blurry, low quality, watermark, text, realistic, photo',
    recommendedSize: '1024x1024',
    tips: ['符合品牌VI', '风格统一', '适合官网、PPT'],
    tags: ['品牌', '插画', 'VI'],
    fields: [
      { key: 'BRAND', label: '品牌风格', placeholder: '如：科技、金融、教育', required: true, options: ['科技', '金融', '教育', '医疗', '零售', '餐饮'] }
    ]
  },
  {
    id: 'illustration-concept',
    name: '概念插画',
    category: 'illustration',
    description: '抽象概念表达插画',
    prompt: 'conceptual illustration, {CONCEPT} theme, abstract geometric shapes, modern design, corporate colors, professional quality, clean composition',
    negativePrompt: 'blurry, low quality, watermark, text, realistic, photo',
    recommendedSize: '1024x1024',
    tips: ['表达抽象概念', '适合文章配图', '现代简约风格'],
    tags: ['概念', '抽象', '配图'],
    fields: [
      { key: 'CONCEPT', label: '概念主题', placeholder: '如：创新、合作、成长', required: true, options: ['创新', '合作', '成长', '成功', '团队', '未来'] }
    ]
  },
  {
    id: 'social-xiaohongshu',
    name: '小红书封面',
    category: 'social',
    description: '小红书风格封面图',
    prompt: 'xiaohongshu style cover, [TOPIC] theme, aesthetic, soft pastel colors, lifestyle photography, clean composition, Instagram worthy, high quality',
    negativePrompt: 'blurry, low quality, watermark, text, distorted',
    recommendedSize: '1024x1024',
    tips: ['清新ins风', '色调柔和', '适合生活方式内容'],
    tags: ['小红书', '封面', '生活方式']
  },
  {
    id: 'social-wechat',
    name: '公众号配图',
    category: 'social',
    description: '微信公众号文章配图',
    prompt: 'wechat article cover, [TOPIC] theme, professional style, clean design, suitable for reading, modern aesthetic, high quality',
    negativePrompt: 'blurry, low quality, watermark, text, distorted',
    recommendedSize: '1024x1024',
    tips: ['适合文章封面', '专业简洁', '预留标题空间'],
    tags: ['公众号', '封面', '文章']
  },
  {
    id: 'social-thumbnail',
    name: '视频封面',
    category: 'social',
    description: '短视频封面图',
    prompt: 'video thumbnail, [TOPIC] theme, eye-catching, vibrant colors, dynamic composition, professional quality, 16:9 format, YouTube style',
    negativePrompt: 'blurry, low quality, watermark, text, distorted',
    recommendedSize: '1792x1024',
    tips: ['视觉吸引力强', '适合B站、抖音', '突出主题'],
    tags: ['视频', '封面', '缩略图']
  }
]

export function getTemplatesByCategory(category: string): WorkTemplate[] {
  return workTemplates.filter(t => t.category === category)
}

export function searchTemplates(query: string): WorkTemplate[] {
  const lowerQuery = query.toLowerCase()
  return workTemplates.filter(t => 
    t.name.toLowerCase().includes(lowerQuery) ||
    t.description.toLowerCase().includes(lowerQuery) ||
    t.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
  )
}

export function getTemplateById(id: string): WorkTemplate | undefined {
  return workTemplates.find(t => t.id === id)
}
