/**
 * 节庆营销模板库
 * 包含春节、端午、中秋、双十一、圣诞等节日营销模板
 */

export type FestivalType = 'spring_festival' | 'lantern' | 'qingming' | 'labor' | 'dragon_boat' | 'mid_autumn' | 'national' | 'double_11' | 'christmas' | 'new_year'

export interface FestivalTemplate {
  id: string
  name: string
  festival: FestivalType
  festivalName: string
  description: string
  promptTemplate: string
  negativePrompt: string
  tips: string[]
  tags: string[]
  colorScheme: string[]
  elements: string[]
}

export const festivalTemplates: FestivalTemplate[] = [
  {
    id: 'spring-festival-kv',
    name: '春节主视觉KV',
    festival: 'spring_festival',
    festivalName: '春节',
    description: '适合品牌春节营销主视觉设计',
    promptTemplate: '为{品牌名}设计一张春节主视觉KV，主题为"{品牌Slogan}，喜迎新春"。画面中央是{艺术化生肖形象或品牌产品}，背景采用{朱红色/鎏金色}渐变，点缀{简约的烟花光点或祥云纹样}。风格为{现代国潮/温暖插画}，字体使用{大气书法字体}，整体充满节日感但保持品牌高级感。',
    negativePrompt: 'tacky, gaudy, overly decorated, cluttered, messy, low quality, distorted',
    tips: ['避免土味设计', '保持品牌调性', '色彩以红金为主', '字体要有力量感'],
    tags: ['春节', 'KV', '主视觉', '国潮'],
    colorScheme: ['朱红', '鎏金', '深红', '金色'],
    elements: ['生肖', '祥云', '烟花', '灯笼', '福字']
  },
  {
    id: 'spring-festival-product',
    name: '春节产品海报',
    festival: 'spring_festival',
    festivalName: '春节',
    description: '适合春节产品促销海报',
    promptTemplate: '{产品名称}春节促销海报，产品置于画面中央，周围环绕{春节元素：红包、灯笼、烟花}，背景为{喜庆的红色渐变}，产品上方有{金色立体字"新春特惠"}，整体风格{现代简约}，突出产品质感，4K高清，商业摄影风格。',
    negativePrompt: 'blurry, low quality, distorted product, unprofessional, messy background',
    tips: ['产品要清晰', '促销信息突出', '节日氛围浓厚'],
    tags: ['春节', '产品海报', '促销'],
    colorScheme: ['红色', '金色', '白色'],
    elements: ['红包', '灯笼', '烟花', '福字']
  },
  {
    id: 'lantern-festival',
    name: '元宵节海报',
    festival: 'lantern',
    festivalName: '元宵节',
    description: '适合元宵节品牌营销',
    promptTemplate: '元宵节主题海报，画面中央是{品牌产品或吉祥物}，背景是{璀璨的灯笼海洋}，天空中飘浮着{发光的孔明灯}，整体色调为{暖黄与橙红渐变}，营造{温馨团圆的氛围}，{中国风插画风格}，高清细腻。',
    negativePrompt: 'dark, gloomy, scary, low quality, distorted',
    tips: ['灯笼要精致', '氛围温馨', '色彩温暖'],
    tags: ['元宵节', '灯笼', '团圆'],
    colorScheme: ['暖黄', '橙红', '金色'],
    elements: ['灯笼', '孔明灯', '汤圆', '月亮']
  },
  {
    id: 'dragon-boat',
    name: '端午节海报',
    festival: 'dragon_boat',
    festivalName: '端午节',
    description: '适合端午节品牌营销',
    promptTemplate: '端午节主题海报，画面展现{龙舟竞渡的场景}，{品牌产品}巧妙融入画面，背景是{波光粼粼的江面}，点缀{粽叶元素}，色调以{青绿与金色为主}，风格为{现代国潮插画}，动感有力。',
    negativePrompt: 'blurry, low quality, distorted, scary, violent',
    tips: ['龙舟要有动感', '粽叶元素点缀', '青绿色调'],
    tags: ['端午节', '龙舟', '粽子'],
    colorScheme: ['青绿', '金色', '深绿'],
    elements: ['龙舟', '粽叶', '粽子', '江水']
  },
  {
    id: 'mid-autumn',
    name: '中秋节海报',
    festival: 'mid_autumn',
    festivalName: '中秋节',
    description: '适合中秋节品牌营销',
    promptTemplate: '中秋节主题海报，画面中央是{巨大的满月}，{品牌产品}置于{精美的月饼礼盒}旁，背景是{桂花飘香的庭院}，点缀{玉兔元素}，色调以{深蓝与金色为主}，营造{团圆温馨的氛围}，{唯美插画风格}。',
    negativePrompt: 'blurry, low quality, distorted, dark, scary',
    tips: ['月亮要圆润', '桂花点缀', '温馨氛围'],
    tags: ['中秋节', '月亮', '月饼'],
    colorScheme: ['深蓝', '金色', '暖黄'],
    elements: ['满月', '月饼', '桂花', '玉兔']
  },
  {
    id: 'national-day',
    name: '国庆节海报',
    festival: 'national',
    festivalName: '国庆节',
    description: '适合国庆节品牌营销',
    promptTemplate: '国庆节主题海报，画面展现{壮丽的祖国山河}，{品牌产品}巧妙融入场景，背景是{飘扬的红旗}和{璀璨的烟花}，色调以{中国红与金色为主}，风格为{大气磅礴的商业摄影}，充满{爱国情怀与民族自豪感}。',
    negativePrompt: 'blurry, low quality, distorted, disrespectful, political controversy',
    tips: ['红旗要飘扬', '烟花璀璨', '大气磅礴'],
    tags: ['国庆节', '爱国', '庆典'],
    colorScheme: ['中国红', '金色', '深蓝'],
    elements: ['红旗', '烟花', '天安门', '山河']
  },
  {
    id: 'double-11',
    name: '双十一促销海报',
    festival: 'double_11',
    festivalName: '双十一',
    description: '适合双十一电商促销',
    promptTemplate: '双十一购物节促销海报，画面中央是{品牌产品}，周围环绕{漂浮的礼盒和优惠券}，背景是{炫酷的科技感光效}，色调以{橙红与紫色渐变}为主，大字标题"{狂欢价}"，风格为{现代电商风}，充满{购物狂欢的氛围}。',
    negativePrompt: 'blurry, low quality, distorted product, unprofessional',
    tips: ['促销信息突出', '礼盒元素丰富', '购物氛围'],
    tags: ['双十一', '促销', '电商'],
    colorScheme: ['橙红', '紫色', '金色'],
    elements: ['礼盒', '优惠券', '购物车', '数字11']
  },
  {
    id: 'christmas',
    name: '圣诞节海报',
    festival: 'christmas',
    festivalName: '圣诞节',
    description: '适合圣诞节品牌营销',
    promptTemplate: '圣诞节主题海报，画面中央是{品牌产品}，周围环绕{圣诞树、礼物盒、雪花}，背景是{温馨的圣诞夜场景}，点缀{闪烁的彩灯}，色调以{红绿与金色为主}，风格为{温暖治愈的插画风格}，充满{节日祝福的氛围}。',
    negativePrompt: 'blurry, low quality, distorted, scary, dark',
    tips: ['圣诞元素丰富', '温馨氛围', '红绿色调'],
    tags: ['圣诞节', '礼物', '祝福'],
    colorScheme: ['红色', '绿色', '金色', '白色'],
    elements: ['圣诞树', '礼物', '雪花', '彩灯', '驯鹿']
  },
  {
    id: 'new-year',
    name: '元旦海报',
    festival: 'new_year',
    festivalName: '元旦',
    description: '适合元旦新年营销',
    promptTemplate: '元旦新年主题海报，画面展现{璀璨的城市夜景}，{品牌产品}置于前景，天空中绽放{绚烂的烟花}，背景有{倒计时的数字}，色调以{蓝紫与金色为主}，风格为{现代时尚的商业摄影}，充满{新年新气象的氛围}。',
    negativePrompt: 'blurry, low quality, distorted, dark, gloomy',
    tips: ['烟花要绚烂', '新年氛围', '时尚现代'],
    tags: ['元旦', '新年', '烟花'],
    colorScheme: ['蓝紫', '金色', '银色'],
    elements: ['烟花', '倒计时', '城市夜景', '钟表']
  }
]

export function getFestivalTemplatesByType(festival: FestivalType): FestivalTemplate[] {
  return festivalTemplates.filter(t => t.festival === festival)
}

export function getFestivalTemplateById(id: string): FestivalTemplate | undefined {
  return festivalTemplates.find(t => t.id === id)
}

export function getCurrentFestival(): FestivalType | null {
  const now = new Date()
  const month = now.getMonth() + 1
  const day = now.getDate()
  
  if (month === 1 && day >= 1 && day <= 15) return 'spring_festival'
  if (month === 1 && day >= 15 && day <= 20) return 'lantern'
  if (month === 6 && day >= 1 && day <= 10) return 'dragon_boat'
  if (month === 9 && day >= 15 && day <= 25) return 'mid_autumn'
  if (month === 10 && day >= 1 && day <= 7) return 'national'
  if (month === 11 && day >= 1 && day <= 15) return 'double_11'
  if (month === 12 && day >= 20 && day <= 26) return 'christmas'
  if (month === 12 && day >= 28) return 'new_year'
  
  return null
}

export function generateFestivalPrompt(template: FestivalTemplate, values: Record<string, string>): string {
  let prompt = template.promptTemplate
  
  for (const [key, value] of Object.entries(values)) {
    prompt = prompt.replace(`{${key}}`, value)
  }
  
  return prompt
}

export const festivalCategories = [
  { id: 'spring_festival', name: '春节', icon: 'Gift', color: '#E74C3C' },
  { id: 'lantern', name: '元宵节', icon: 'Lantern', color: '#F39C12' },
  { id: 'dragon_boat', name: '端午节', icon: 'Sparkles', color: '#27AE60' },
  { id: 'mid_autumn', name: '中秋节', icon: 'Moon', color: '#3498DB' },
  { id: 'national', name: '国庆节', icon: 'Flag', color: '#E74C3C' },
  { id: 'double_11', name: '双十一', icon: 'ShoppingCart', color: '#9B59B6' },
  { id: 'christmas', name: '圣诞节', icon: 'TreePine', color: '#27AE60' },
  { id: 'new_year', name: '元旦', icon: 'Sparkles', color: '#3498DB' }
]
