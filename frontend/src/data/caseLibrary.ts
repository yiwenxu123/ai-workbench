import casesData from './cases.json'

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
}

export const caseExamples: CaseExample[] = casesData as CaseExample[]

export const caseCategories = [
  { value: 'ecommerce', label: '电商投流', icon: 'ShoppingCart' },
  { value: 'brand', label: '品牌广告', icon: 'Clapperboard' },
  { value: 'product', label: '产品广告', icon: 'Package' },
  { value: 'drama', label: '短剧叙事', icon: 'Theater' },
  { value: 'animation', label: '动画方向', icon: 'Palette' },
  { value: 'film', label: '影视类', icon: 'Film' },
  { value: 'social', label: '社媒玩法', icon: 'Smartphone' }
]

export function adaptPrompt(caseExample: CaseExample, newSubject: string): string {
  return caseExample.prompt.replace(/\{主体\}/g, newSubject)
}
