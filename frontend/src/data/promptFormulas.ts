/**
 * 提示词公式库
 * 基于AI绘图资料.md模块一的结构化提示词公式
 */

export interface PromptFormula {
  id: string
  name: string
  category: string
  description: string
  structure: FormulaPart[]
  example: string
  tips: string[]
}

export interface FormulaPart {
  key: string
  label: string
  description: string
  required: boolean
  options?: string[]
  placeholder: string
}

export const promptFormulas: PromptFormula[] = [
  {
    id: 'basic-structure',
    name: '基础结构公式',
    category: '基础',
    description: '最通用的提示词结构，适合大多数场景',
    structure: [
      { key: 'subject', label: '主体', description: '画面的核心对象', required: true, placeholder: '如：一只猫咪、一位少女' },
      { key: 'action', label: '动作/状态', description: '主体在做什么', required: false, placeholder: '如：在花园里玩耍、坐在窗边' },
      { key: 'scene', label: '场景', description: '背景环境', required: false, placeholder: '如：日式庭院、现代城市' },
      { key: 'style', label: '风格', description: '艺术风格', required: false, options: ['写实', '插画', '水彩', '油画', '动漫', '3D'], placeholder: '选择风格' },
      { key: 'quality', label: '质量词', description: '画质描述', required: false, placeholder: '如：4K高清、细节丰富' }
    ],
    example: '一只橘猫，在阳光明媚的花园里追逐蝴蝶，日式庭院风格，水彩质感，4K高清，细节丰富',
    tips: ['主体必须明确', '风格和质量词可以提升效果', '描述越具体效果越好']
  },
  {
    id: 'character-portrait',
    name: '人物肖像公式',
    category: '人物',
    description: '专门用于生成人物肖像的公式',
    structure: [
      { key: 'gender', label: '性别', description: '人物性别', required: true, options: ['女性', '男性', '中性'], placeholder: '选择性别' },
      { key: 'age', label: '年龄', description: '大致年龄', required: false, placeholder: '如：20岁左右、中年' },
      { key: 'appearance', label: '外貌特征', description: '面部特征、发型等', required: false, placeholder: '如：长发、蓝眼睛、高鼻梁' },
      { key: 'clothing', label: '服装', description: '穿着打扮', required: false, placeholder: '如：白色连衣裙、西装' },
      { key: 'expression', label: '表情', description: '面部表情', required: false, options: ['微笑', '严肃', '惊讶', '悲伤', '自信'], placeholder: '选择表情' },
      { key: 'pose', label: '姿势', description: '身体姿态', required: false, placeholder: '如：侧脸、正面、回眸' },
      { key: 'lighting', label: '光线', description: '光照效果', required: false, options: ['自然光', '柔光', '逆光', '侧光', '电影光'], placeholder: '选择光线' },
      { key: 'background', label: '背景', description: '背景环境', required: false, placeholder: '如：纯色背景、城市街道' }
    ],
    example: '一位20岁左右的女性，长发飘飘，蓝色眼睛，穿着白色连衣裙，微笑着看向镜头，自然光照射，纯色背景，高清人像摄影',
    tips: ['年龄和外貌描述要具体', '光线对人物效果影响很大', '背景简洁能突出人物']
  },
  {
    id: 'product-showcase',
    name: '产品展示公式',
    category: '商业',
    description: '用于电商产品展示的公式',
    structure: [
      { key: 'product', label: '产品名称', description: '具体产品', required: true, placeholder: '如：智能手表、口红' },
      { key: 'material', label: '材质', description: '产品材质', required: false, placeholder: '如：钛合金、玻璃、皮革' },
      { key: 'color', label: '颜色', description: '产品颜色', required: false, placeholder: '如：银色、玫瑰金' },
      { key: 'angle', label: '展示角度', description: '拍摄角度', required: false, options: ['正面', '侧面', '45度角', '俯视', '仰视'], placeholder: '选择角度' },
      { key: 'scene', label: '场景', description: '展示环境', required: false, options: ['简约工作室', '自然光场景', '科技感背景', '生活场景'], placeholder: '选择场景' },
      { key: 'lighting', label: '光线', description: '布光方式', required: false, placeholder: '如：studio lighting, 软光箱' },
      { key: 'style', label: '风格', description: '整体风格', required: false, options: ['商业广告', '极简风', '高端奢华', '清新自然'], placeholder: '选择风格' }
    ],
    example: '高端智能手表，钛合金表壳，银色表盘，45度角展示，简约工作室场景，studio lighting，商业广告风格，4K高清产品摄影',
    tips: ['材质描述要专业', '光线对产品质感影响大', '背景要简洁不抢镜']
  },
  {
    id: 'landscape-scene',
    name: '风景场景公式',
    category: '风景',
    description: '用于生成风景画面的公式',
    structure: [
      { key: 'mainScene', label: '主景', description: '画面的核心景观', required: true, placeholder: '如：雪山、海滩、森林' },
      { key: 'time', label: '时间', description: '一天中的时间', required: false, options: ['日出', '上午', '正午', '下午', '日落', '夜晚'], placeholder: '选择时间' },
      { key: 'weather', label: '天气', description: '天气状况', required: false, options: ['晴天', '多云', '阴天', '雨天', '雪天', '雾天'], placeholder: '选择天气' },
      { key: 'season', label: '季节', description: '季节特征', required: false, options: ['春', '夏', '秋', '冬'], placeholder: '选择季节' },
      { key: 'atmosphere', label: '氛围', description: '整体氛围', required: false, placeholder: '如：宁静、壮阔、神秘' },
      { key: 'style', label: '风格', description: '艺术风格', required: false, options: ['写实摄影', '油画', '水彩', '动漫', '概念艺术'], placeholder: '选择风格' }
    ],
    example: '壮丽的雪山，日落时分，晴天，冬季，宁静壮阔的氛围，写实摄影风格，8K高清，细节丰富',
    tips: ['时间和天气对氛围影响大', '季节特征要明显', '风格选择决定整体效果']
  },
  {
    id: 'architectural',
    name: '建筑设计公式',
    category: '建筑',
    description: '用于生成建筑相关画面的公式',
    structure: [
      { key: 'building', label: '建筑类型', description: '建筑种类', required: true, placeholder: '如：现代别墅、古典教堂' },
      { key: 'style', label: '建筑风格', description: '设计风格', required: false, options: ['现代简约', '古典欧式', '中式传统', '日式', '工业风'], placeholder: '选择风格' },
      { key: 'material', label: '材质', description: '主要建材', required: false, placeholder: '如：玻璃幕墙、红砖、木质' },
      { key: 'surrounding', label: '周边环境', description: '周围景观', required: false, placeholder: '如：城市街道、山林、湖边' },
      { key: 'time', label: '时间', description: '拍摄时间', required: false, options: ['白天', '黄昏', '夜晚'], placeholder: '选择时间' },
      { key: 'angle', label: '拍摄角度', description: '视角选择', required: false, options: ['正面', '侧面', '鸟瞰', '仰视'], placeholder: '选择角度' }
    ],
    example: '现代简约风格别墅，玻璃幕墙和白色混凝土材质，坐落在山林之间，黄昏时分，正面拍摄，建筑摄影，8K高清',
    tips: ['建筑风格要明确', '材质描述要专业', '周边环境要协调']
  },
  {
    id: 'food-photography',
    name: '美食摄影公式',
    category: '美食',
    description: '用于生成美食画面的公式',
    structure: [
      { key: 'food', label: '食物名称', description: '具体菜品', required: true, placeholder: '如：牛排、蛋糕、拉面' },
      { key: 'plating', label: '摆盘', description: '摆盘方式', required: false, placeholder: '如：精致摆盘、家庭风格' },
      { key: 'props', label: '道具', description: '配套餐具', required: false, placeholder: '如：木质餐盘、白色瓷盘' },
      { key: 'background', label: '背景', description: '桌面背景', required: false, options: ['木质桌面', '大理石', '纯色布', '自然场景'], placeholder: '选择背景' },
      { key: 'lighting', label: '光线', description: '布光方式', required: false, options: ['自然光', '侧光', '逆光', '柔光'], placeholder: '选择光线' },
      { key: 'angle', label: '角度', description: '拍摄角度', required: false, options: ['俯视', '45度', '侧面', '特写'], placeholder: '选择角度' },
      { key: 'style', label: '风格', description: '整体风格', required: false, options: ['商业美食', '温馨家庭', '清新自然', '高级餐厅'], placeholder: '选择风格' }
    ],
    example: '精致牛排，完美摆盘，配以烤蔬菜和红酒酱汁，白色瓷盘，木质桌面背景，侧光照射，45度角拍摄，商业美食摄影风格，4K高清',
    tips: ['食物要有食欲感', '摆盘要精致', '光线要突出食物质感']
  },
  {
    id: 'anime-character',
    name: '动漫角色公式',
    category: '动漫',
    description: '用于生成动漫角色的公式',
    structure: [
      { key: 'character', label: '角色描述', description: '角色基本特征', required: true, placeholder: '如：少女、少年、奇幻角色' },
      { key: 'hair', label: '发型发色', description: '头发特征', required: false, placeholder: '如：银色长发、粉色短发' },
      { key: 'eyes', label: '眼睛', description: '眼睛特征', required: false, placeholder: '如：蓝色大眼睛、金色瞳孔' },
      { key: 'clothing', label: '服装', description: '穿着打扮', required: false, placeholder: '如：校服、战斗服、和服' },
      { key: 'accessories', label: '配饰', description: '装饰物品', required: false, placeholder: '如：翅膀、魔法杖、耳环' },
      { key: 'pose', label: '姿势', description: '身体姿态', required: false, placeholder: '如：战斗姿态、可爱姿势' },
      { key: 'background', label: '背景', description: '背景环境', required: false, placeholder: '如：魔法森林、城市' },
      { key: 'style', label: '画风', description: '动漫风格', required: false, options: ['日系动漫', '韩系', '美漫', '赛璐璐', '厚涂'], placeholder: '选择画风' }
    ],
    example: '奇幻少女，银色长发飘逸，紫色大眼睛，穿着华丽的魔法长裙，手持发光魔法杖，优雅的施法姿态，魔法森林背景，日系动漫风格，精致细腻',
    tips: ['眼睛是动漫角色的灵魂', '发型和服装要有特色', '背景要配合角色气质']
  },
  {
    id: 'concept-art',
    name: '概念艺术公式',
    category: '概念',
    description: '用于生成概念艺术画面的公式',
    structure: [
      { key: 'concept', label: '概念主题', description: '核心概念', required: true, placeholder: '如：未来城市、外星世界' },
      { key: 'elements', label: '关键元素', description: '重要组成部分', required: false, placeholder: '如：飞行器、巨型建筑' },
      { key: 'mood', label: '情绪氛围', description: '整体感觉', required: false, options: ['神秘', '壮阔', '黑暗', '希望', '恐惧'], placeholder: '选择氛围' },
      { key: 'color', label: '色调', description: '色彩倾向', required: false, placeholder: '如：冷色调、暖色调、赛博朋克' },
      { key: 'style', label: '风格', description: '艺术风格', required: false, options: ['科幻', '奇幻', '赛博朋克', '蒸汽朋克', '废土'], placeholder: '选择风格' },
      { key: 'detail', label: '细节程度', description: '画面精细度', required: false, options: ['简约', '中等', '复杂', '超精细'], placeholder: '选择细节程度' }
    ],
    example: '未来城市概念，悬浮的巨型建筑群和穿梭的飞行器，神秘壮阔的氛围，蓝紫色赛博朋克色调，科幻风格，超精细细节，8K概念艺术',
    tips: ['概念要独特有创意', '元素要配合主题', '色调决定整体氛围']
  }
]

export function getFormulasByCategory(category: string): PromptFormula[] {
  return promptFormulas.filter(f => f.category === category)
}

export function getFormulaById(id: string): PromptFormula | undefined {
  return promptFormulas.find(f => f.id === id)
}

export function generatePromptFromFormula(formula: PromptFormula, values: Record<string, string>): string {
  const parts: string[] = []
  
  for (const part of formula.structure) {
    const value = values[part.key]
    if (value) {
      parts.push(value)
    }
  }
  
  return parts.join('，')
}

export const formulaCategories = [
  { id: '基础', name: '基础公式', icon: 'FileText', description: '通用提示词结构' },
  { id: '人物', name: '人物肖像', icon: 'User', description: '人物相关公式' },
  { id: '商业', name: '商业产品', icon: 'Package', description: '产品展示公式' },
  { id: '风景', name: '风景场景', icon: 'Mountain', description: '自然风景公式' },
  { id: '建筑', name: '建筑设计', icon: 'Landmark', description: '建筑相关公式' },
  { id: '美食', name: '美食摄影', icon: 'UtensilsCrossed', description: '美食相关公式' },
  { id: '动漫', name: '动漫角色', icon: 'Palette', description: '动漫风格公式' },
  { id: '概念', name: '概念艺术', icon: 'Lightbulb', description: '概念设计公式' }
]

export const quickStyleCodes = [
  { code: 'photorealistic', name: '写实摄影', description: '真实照片效果' },
  { code: 'cinematic', name: '电影感', description: '电影画面质感' },
  { code: 'anime', name: '动漫风格', description: '日系动漫效果' },
  { code: 'oil painting', name: '油画风格', description: '经典油画质感' },
  { code: 'watercolor', name: '水彩风格', description: '水彩画效果' },
  { code: 'digital art', name: '数字艺术', description: '现代数字绘画' },
  { code: 'concept art', name: '概念艺术', description: '游戏电影概念图' },
  { code: '3D render', name: '3D渲染', description: '三维渲染效果' },
  { code: 'illustration', name: '插画风格', description: '现代插画效果' },
  { code: 'minimalist', name: '极简风格', description: '简约设计风格' }
]

export const qualityKeywords = [
  { code: '4K', name: '4K高清', description: '高分辨率' },
  { code: '8K', name: '8K超清', description: '超高分辨率' },
  { code: 'highly detailed', name: '高细节', description: '细节丰富' },
  { code: 'masterpiece', name: '杰作', description: '顶级质量' },
  { code: 'best quality', name: '最佳质量', description: '最优效果' },
  { code: 'ultra realistic', name: '超写实', description: '极度真实' },
  { code: 'professional', name: '专业级', description: '专业品质' },
  { code: 'studio quality', name: '工作室质量', description: '商业级品质' }
]

export const lightingKeywords = [
  { code: 'natural lighting', name: '自然光', description: '自然光照' },
  { code: 'studio lighting', name: '影棚光', description: '专业布光' },
  { code: 'golden hour', name: '黄金时刻', description: '日出日落光线' },
  { code: 'soft lighting', name: '柔光', description: '柔和光线' },
  { code: 'dramatic lighting', name: '戏剧光', description: '强烈对比光' },
  { code: 'rim lighting', name: '轮廓光', description: '边缘光效' },
  { code: 'backlight', name: '逆光', description: '背面光源' },
  { code: 'volumetric lighting', name: '体积光', description: '光束效果' }
]
