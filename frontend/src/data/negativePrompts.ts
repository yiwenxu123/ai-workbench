export interface NegativePromptPack {
  id: string
  name: string
  description: string
  prompts: string[]
  category: 'quality' | 'style' | 'composition' | 'scene' | 'custom'
  isDefault?: boolean
}

export const negativePromptPacks: NegativePromptPack[] = [
  {
    id: 'general-quality',
    name: '通用质量包',
    description: '提升整体生成质量，适用于所有场景',
    prompts: [
      'low quality',
      'blurry',
      'ugly',
      'deformed',
      'mutated',
      'text',
      'watermark',
      'signature',
      'bad anatomy',
      'disfigured',
      'poorly drawn face',
      'mutation',
      'extra limb',
      'poorly drawn hands',
      'missing limb',
      'floating limbs',
      'disconnected limbs',
      'malformed hands',
      'out of focus',
      'long neck',
      'long body',
      'disgusting',
      'poorly drawn',
      'childish',
      'weird'
    ],
    category: 'quality',
    isDefault: true
  },
  {
    id: 'realism-purify',
    name: '写实净化包',
    description: '去除非写实风格元素，适用于需要真实照片效果',
    prompts: [
      '3D render',
      'cartoon',
      'anime',
      'painting',
      'drawing',
      'illustration',
      'sketch',
      'digital art',
      'artificial',
      'rendered',
      'CGI',
      'computer generated',
      'stylized',
      'exaggerated',
      'caricature'
    ],
    category: 'style'
  },
  {
    id: 'composition-purify',
    name: '构图净化包',
    description: '去除干扰元素，获得干净画面',
    prompts: [
      'border',
      'frame',
      'out of frame',
      'duplicate',
      'multiple subjects',
      'cropped',
      'cut off',
      'cluttered',
      'messy',
      'busy background',
      'distracting elements',
      'crowded'
    ],
    category: 'composition'
  },
  {
    id: 'festival-purify',
    name: '节庆专用包',
    description: '避免节庆设计过于俗气',
    prompts: [
      'tacky',
      'gaudy',
      'overly decorated',
      'cluttered',
      'messy',
      'cheap looking',
      'tasteless',
      'excessive',
      'overdone',
      'kitsch'
    ],
    category: 'scene'
  },
  {
    id: 'ecommerce-product',
    name: '电商产品专用',
    description: '提升产品图专业度',
    prompts: [
      'unprofessional logo placement',
      'distorted product shape',
      'unrealistic lighting',
      'cheap looking',
      'low quality render',
      'blurry product',
      'wrong proportions',
      'artificial looking',
      'fake reflection',
      'bad shadows'
    ],
    category: 'scene'
  },
  {
    id: 'portrait-purify',
    name: '人物肖像专用',
    description: '提升人物生成质量',
    prompts: [
      'unrealistic facial features',
      'unnatural skin texture',
      'inconsistent clothing',
      'awkward pose',
      'wrong eye color',
      'asymmetrical face',
      'bad teeth',
      'weird smile',
      'unnatural expression',
      'plastic skin',
      'over-smoothed skin',
      'alien eyes'
    ],
    category: 'scene'
  },
  {
    id: 'corporate-purify',
    name: '企业场景专用',
    description: '提升企业宣传图质量',
    prompts: [
      'cluttered background',
      'messy office',
      'unprofessional attire',
      'low resolution',
      'dated interior',
      'dirty environment',
      'disorganized workspace',
      'casual setting',
      'home office look'
    ],
    category: 'scene'
  },
  {
    id: 'cultural-purify',
    name: '文化内容专用',
    description: '避免文化内容失真',
    prompts: [
      'historically inaccurate clothing',
      'anachronistic elements',
      'disrespectful portrayal',
      'stereotypical representation',
      'culturally insensitive',
      'wrong traditional elements',
      'mixed cultural symbols',
      'inauthentic details'
    ],
    category: 'scene'
  },
  {
    id: 'video-specific',
    name: '视频专用',
    description: '视频生成常见问题规避',
    prompts: [
      'static image',
      'frozen frame',
      'jump cut',
      'flickering',
      'morphing artifacts',
      'inconsistent motion',
      'unnatural movement',
      'glitchy',
      'distortion',
      'warped geometry'
    ],
    category: 'quality'
  }
]

export const negativePromptCategories = [
  { value: 'quality', label: '质量优化', icon: 'Sparkles' },
  { value: 'style', label: '风格净化', icon: 'Palette' },
  { value: 'composition', label: '构图优化', icon: 'Ruler' },
  { value: 'scene', label: '场景专用', icon: 'Film' },
  { value: 'custom', label: '自定义', icon: 'Settings' }
]

export function getPackById(id: string): NegativePromptPack | undefined {
  return negativePromptPacks.find(pack => pack.id === id)
}

export function getPacksByCategory(category: string): NegativePromptPack[] {
  return negativePromptPacks.filter(pack => pack.category === category)
}

export function getDefaultPacks(): NegativePromptPack[] {
  return negativePromptPacks.filter(pack => pack.isDefault)
}

export function mergePrompts(packIds: string[]): string {
  const prompts = new Set<string>()
  
  packIds.forEach(id => {
    const pack = getPackById(id)
    if (pack) {
      pack.prompts.forEach(p => prompts.add(p))
    }
  })
  
  return Array.from(prompts).join(', ')
}

export const quickNegativePresets = [
  {
    name: '高质量写实',
    packs: ['general-quality', 'realism-purify'],
    description: '适合需要真实照片效果的场景'
  },
  {
    name: '产品电商',
    packs: ['general-quality', 'ecommerce-product', 'composition-purify'],
    description: '适合电商产品图生成'
  },
  {
    name: '人物肖像',
    packs: ['general-quality', 'portrait-purify', 'realism-purify'],
    description: '适合人物肖像生成'
  },
  {
    name: '企业宣传',
    packs: ['general-quality', 'corporate-purify', 'composition-purify'],
    description: '适合企业宣传图生成'
  },
  {
    name: '视频生成',
    packs: ['general-quality', 'video-specific'],
    description: '适合视频生成场景'
  }
]
