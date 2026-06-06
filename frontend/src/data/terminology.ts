/**
 * AI绘图术语词典
 * 包含风格、光影、构图、色彩等专业术语的解释和使用建议
 */

export type TermCategory = 'style' | 'lighting' | 'composition' | 'color' | 'material' | 'mood' | 'technique'

export interface TermEntry {
  id: string
  name: string
  nameEn?: string
  category: TermCategory
  description: string
  usage: string
  examples: string[]
  relatedTerms?: string[]
  tips?: string
}

export const termCategoryConfig: Record<TermCategory, { label: string; icon: string; color: string }> = {
  style: { label: '风格', icon: 'Palette', color: '#1890ff' },
  lighting: { label: '光影', icon: 'Lightbulb', color: '#fadb14' },
  composition: { label: '构图', icon: 'Ruler', color: '#722ed1' },
  color: { label: '色彩', icon: 'Rainbow', color: '#eb2f96' },
  material: { label: '材质', icon: 'BrickWall', color: '#fa8c16' },
  mood: { label: '氛围', icon: 'Moon', color: '#13c2c2' },
  technique: { label: '技法', icon: 'Wrench', color: '#52c41a' }
}

export const terminology: TermEntry[] = [
  // 风格类
  {
    id: 'cyberpunk',
    name: '赛博朋克',
    nameEn: 'Cyberpunk',
    category: 'style',
    description: '科幻风格的一种，以高科技与低生活为特征，常见霓虹灯、机械改造、未来城市元素。',
    usage: '适合表现未来科技、反乌托邦主题，常搭配霓虹光效、金属质感。',
    examples: ['赛博朋克城市夜景', '赛博朋克风格的机械少女', '霓虹闪烁的赛博朋克街道'],
    relatedTerms: ['霓虹', '机械', '未来城市'],
    tips: '搭配"霓虹"、"全息投影"、"机械臂"等关键词效果更佳'
  },
  {
    id: 'steampunk',
    name: '蒸汽朋克',
    nameEn: 'Steampunk',
    category: 'style',
    description: '复古未来主义风格，以蒸汽动力和维多利亚时代美学为特征。',
    usage: '适合表现复古机械、冒险主题，常搭配齿轮、黄铜、皮革元素。',
    examples: ['蒸汽朋克飞艇', '维多利亚时代的蒸汽机器人', '蒸汽朋克风格的怀表'],
    relatedTerms: ['齿轮', '黄铜', '复古'],
    tips: '搭配"齿轮"、"蒸汽"、"黄铜"等关键词'
  },
  {
    id: 'watercolor',
    name: '水彩风格',
    nameEn: 'Watercolor',
    category: 'style',
    description: '模拟水彩画效果，色彩透明流动，边缘柔和晕染。',
    usage: '适合表现轻盈、梦幻的场景，人物肖像也很适合。',
    examples: ['水彩风格的森林', '水彩花卉', '水彩人像'],
    relatedTerms: ['晕染', '透明', '柔和'],
    tips: '搭配"晕染"、"淡雅"、"流动"等关键词'
  },
  {
    id: 'oil-painting',
    name: '油画风格',
    nameEn: 'Oil Painting',
    category: 'style',
    description: '模拟传统油画效果，笔触厚重，色彩饱和度高。',
    usage: '适合表现古典、庄重的主题，肖像和风景都很适合。',
    examples: ['油画风格的向日葵', '古典油画人像', '印象派油画风景'],
    relatedTerms: ['笔触', '厚涂', '古典'],
    tips: '可指定"印象派"、"古典主义"等细分风格'
  },
  {
    id: 'anime',
    name: '动漫风格',
    nameEn: 'Anime',
    category: 'style',
    description: '日本动画风格，特征是大眼睛、夸张的表情、鲜艳的色彩。',
    usage: '适合表现可爱、活泼的角色，二次元场景。',
    examples: ['动漫风格的少女', '日漫风格的校园场景', '二次元角色设计'],
    relatedTerms: ['二次元', '日漫', '卡通'],
    tips: '可搭配"赛璐璐风格"、"吉卜力风格"等细分'
  },
  {
    id: 'realistic',
    name: '写实风格',
    nameEn: 'Realistic',
    category: 'style',
    description: '追求照片级真实感，细节丰富，光影准确。',
    usage: '适合需要真实感的场景，如产品展示、人像摄影。',
    examples: ['写实风格的人像', '照片级真实风景', '超写实产品渲染'],
    relatedTerms: ['照片级', '超高清', '细节丰富'],
    tips: '搭配"8K"、"超高清"、"细节丰富"提升画质'
  },
  {
    id: 'chinese-ink',
    name: '中国水墨',
    nameEn: 'Chinese Ink Painting',
    category: 'style',
    description: '中国传统水墨画风格，以墨色浓淡表现意境。',
    usage: '适合表现山水、花鸟、传统意境。',
    examples: ['水墨山水画', '水墨竹子', '中国风人物'],
    relatedTerms: ['国风', '写意', '留白'],
    tips: '搭配"留白"、"意境"、"淡雅"等关键词'
  },
  {
    id: 'pixel-art',
    name: '像素风格',
    nameEn: 'Pixel Art',
    category: 'style',
    description: '复古游戏风格，由像素点构成的画面。',
    usage: '适合游戏角色、场景设计，复古主题。',
    examples: ['像素风格的角色', '8-bit游戏场景', '像素艺术风景'],
    relatedTerms: ['复古', '游戏', '8-bit'],
    tips: '可指定像素密度如"16-bit"、"32-bit"'
  },
  {
    id: 'concept-art',
    name: '概念艺术',
    nameEn: 'Concept Art',
    category: 'style',
    description: '游戏、电影前期概念设计风格，注重氛围和创意。',
    usage: '适合角色设计、场景概念、世界观构建。',
    examples: ['游戏角色概念设计', '科幻场景概念图', '怪物设计'],
    relatedTerms: ['游戏设计', '电影概念', '数字绘画'],
    tips: '搭配具体游戏或电影风格参考'
  },
  
  // 光影类
  {
    id: 'tyndall-effect',
    name: '丁达尔效应',
    nameEn: 'Tyndall Effect',
    category: 'lighting',
    description: '光线穿过烟雾或尘埃时形成可见光束的效果，也称"耶稣光"。',
    usage: '适合表现神圣、梦幻、神秘的氛围。',
    examples: ['森林中的丁达尔光束', '教堂里的神圣光线', '清晨的阳光穿透薄雾'],
    relatedTerms: ['光束', '耶稣光', '体积光'],
    tips: '搭配"薄雾"、"烟雾"、"尘埃"效果更明显'
  },
  {
    id: 'rim-light',
    name: '轮廓光',
    nameEn: 'Rim Light',
    category: 'lighting',
    description: '从主体后方照射的光线，勾勒出主体轮廓。',
    usage: '适合分离主体与背景，增加立体感。',
    examples: ['轮廓光人像', '逆光剪影', '边缘发光效果'],
    relatedTerms: ['逆光', '剪影', '边缘光'],
    tips: '常与"逆光"搭配使用'
  },
  {
    id: 'rembrandt-lighting',
    name: '伦勃朗光',
    nameEn: 'Rembrandt Lighting',
    category: 'lighting',
    description: '经典人像布光方式，在阴影侧脸颊形成三角形光斑。',
    usage: '适合戏剧性人像，表现立体感和神秘感。',
    examples: ['伦勃朗光人像', '戏剧性肖像', '古典油画光效'],
    relatedTerms: ['戏剧光', '三角光', '人像布光'],
    tips: '适合搭配"古典"、"戏剧性"风格'
  },
  {
    id: 'neon-lighting',
    name: '霓虹光效',
    nameEn: 'Neon Lighting',
    category: 'lighting',
    description: '霓虹灯管发出的彩色光线效果。',
    usage: '适合赛博朋克、夜店、城市夜景主题。',
    examples: ['霓虹灯下的街道', '赛博朋克霓虹', '粉色霓虹光'],
    relatedTerms: ['赛博朋克', '城市夜景', '霓虹'],
    tips: '可指定霓虹颜色如"粉色霓虹"、"蓝色霓虹"'
  },
  {
    id: 'golden-hour',
    name: '黄金时刻',
    nameEn: 'Golden Hour',
    category: 'lighting',
    description: '日出后或日落前约一小时的柔和暖光。',
    usage: '适合表现温暖、浪漫、梦幻的氛围。',
    examples: ['黄金时刻的人像', '日落时分的风景', '黄昏暖光'],
    relatedTerms: ['日落', '黄昏', '暖光'],
    tips: '搭配"逆光"、"剪影"效果更佳'
  },
  {
    id: 'cinematic-lighting',
    name: '电影光效',
    nameEn: 'Cinematic Lighting',
    category: 'lighting',
    description: '电影级别的布光效果，注重氛围和情绪表达。',
    usage: '适合叙事性画面，营造电影感。',
    examples: ['电影感人像', '好莱坞布光', '戏剧性光影'],
    relatedTerms: ['电影感', '戏剧光', '氛围光'],
    tips: '搭配"电影感"、"宽银幕"等关键词'
  },
  
  // 构图类
  {
    id: 'rule-of-thirds',
    name: '三分法构图',
    nameEn: 'Rule of Thirds',
    category: 'composition',
    description: '将画面分成九宫格，主体放在交叉点或线上。',
    usage: '最常用的构图法则，适合大多数场景。',
    examples: ['三分法人像构图', '风景三分法', '主体位于右侧三分之一处'],
    relatedTerms: ['九宫格', '黄金分割'],
    tips: '人像通常将眼睛放在上三分之一线上'
  },
  {
    id: 'symmetry',
    name: '对称构图',
    nameEn: 'Symmetry',
    category: 'composition',
    description: '画面左右或上下对称，形成平衡感。',
    usage: '适合建筑、倒影、正式肖像。',
    examples: ['对称建筑', '水面倒影', '正面肖像'],
    relatedTerms: ['镜像', '平衡', '对称'],
    tips: '建筑和风景中效果显著'
  },
  {
    id: 'close-up',
    name: '特写镜头',
    nameEn: 'Close-up',
    category: 'composition',
    description: '近距离拍摄主体，突出细节。',
    usage: '适合表现表情、细节、产品特征。',
    examples: ['面部特写', '眼睛特写', '产品细节特写'],
    relatedTerms: ['近景', '细节', '大头照'],
    tips: '人像特写注意眼睛的清晰度'
  },
  {
    id: 'wide-angle',
    name: '广角镜头',
    nameEn: 'Wide Angle',
    category: 'composition',
    description: '广阔的视野，适合大场景。',
    usage: '适合风景、建筑、环境人像。',
    examples: ['广角风景', '城市全景', '广角建筑'],
    relatedTerms: ['全景', '大场景'],
    tips: '注意边缘畸变，人像慎用'
  },
  {
    id: 'bird-eye',
    name: '鸟瞰视角',
    nameEn: 'Bird\'s Eye View',
    category: 'composition',
    description: '从高处向下俯视的视角。',
    usage: '适合城市、风景、群像。',
    examples: ['城市鸟瞰', '森林俯视', '人群鸟瞰'],
    relatedTerms: ['俯视', '上帝视角', '航拍'],
    tips: '适合表现规模和空间关系'
  },
  
  // 色彩类
  {
    id: 'morandi-colors',
    name: '莫兰迪色',
    nameEn: 'Morandi Colors',
    category: 'color',
    description: '低饱和度、高级灰调的色彩风格，以意大利画家莫兰迪命名。',
    usage: '适合表现高级、优雅、宁静的氛围。',
    examples: ['莫兰迪色系人像', '莫兰迪风格静物', '高级灰调风景'],
    relatedTerms: ['高级灰', '低饱和', '淡雅'],
    tips: '适合时尚、家居、艺术类主题'
  },
  {
    id: 'high-saturation',
    name: '高饱和度',
    nameEn: 'High Saturation',
    category: 'color',
    description: '色彩鲜艳浓郁，视觉冲击力强。',
    usage: '适合活泼、热烈、吸引眼球的场景。',
    examples: ['高饱和度风景', '鲜艳的色彩', '浓郁色调'],
    relatedTerms: ['鲜艳', '浓郁', '明亮'],
    tips: '注意色彩搭配避免过于杂乱'
  },
  {
    id: 'warm-cool-contrast',
    name: '冷暖对比',
    nameEn: 'Warm-Cool Contrast',
    category: 'color',
    description: '暖色与冷色在同一画面中形成对比。',
    usage: '适合表现冲突、层次、戏剧性。',
    examples: ['冷暖对比人像', '日落时的冷暖对比', '室内外光线对比'],
    relatedTerms: ['色彩对比', '互补色'],
    tips: '常见于日落、室内外场景'
  },
  {
    id: 'monochrome',
    name: '单色调',
    nameEn: 'Monochrome',
    category: 'color',
    description: '画面以单一色调为主，形成统一感。',
    usage: '适合表现专注、简约、艺术感。',
    examples: ['蓝色调风景', '红色调人像', '单色艺术'],
    relatedTerms: ['单色', '统一色调'],
    tips: '可指定具体颜色如"蓝色调"、"金色调"'
  },
  
  // 材质类
  {
    id: 'metallic',
    name: '金属质感',
    nameEn: 'Metallic',
    category: 'material',
    description: '金属表面的光泽和反射效果。',
    usage: '适合机械、科技、奢华主题。',
    examples: ['金属质感机器人', '金色金属表面', '银色金属'],
    relatedTerms: ['光泽', '反射', '金属'],
    tips: '可指定金属类型如"黄金"、"银"、"铜"'
  },
  {
    id: 'glass',
    name: '玻璃质感',
    nameEn: 'Glass',
    category: 'material',
    description: '透明或半透明的玻璃材质效果。',
    usage: '适合产品、建筑、艺术效果。',
    examples: ['玻璃质感物体', '透明玻璃', '磨砂玻璃'],
    relatedTerms: ['透明', '折射', '反射'],
    tips: '注意表现折射和反射'
  },
  {
    id: 'fur',
    name: '毛绒质感',
    nameEn: 'Fur',
    category: 'material',
    description: '动物毛发或毛绒材质的柔软效果。',
    usage: '适合动物、毛绒玩具、服装。',
    examples: ['毛绒质感的小猫', '柔软的毛发', '毛绒玩具'],
    relatedTerms: ['柔软', '蓬松', '毛发'],
    tips: '搭配"蓬松"、"柔软"等形容词'
  },
  
  // 氛围类
  {
    id: 'dreamy',
    name: '梦幻氛围',
    nameEn: 'Dreamy',
    category: 'mood',
    description: '朦胧、柔和、超现实的梦幻感觉。',
    usage: '适合童话、幻想、浪漫主题。',
    examples: ['梦幻森林', '童话氛围', '梦幻人像'],
    relatedTerms: ['朦胧', '柔焦', '童话'],
    tips: '搭配"柔焦"、"光晕"、"薄雾"效果'
  },
  {
    id: 'epic',
    name: '史诗氛围',
    nameEn: 'Epic',
    category: 'mood',
    description: '宏大、壮观、震撼的氛围。',
    usage: '适合战争、神话、大片主题。',
    examples: ['史诗级战斗场景', '宏大的史诗风景', '史诗级人物'],
    relatedTerms: ['宏大', '壮观', '震撼'],
    tips: '搭配"广角"、"大场景"构图'
  },
  {
    id: 'horror',
    name: '恐怖氛围',
    nameEn: 'Horror',
    category: 'mood',
    description: '阴森、诡异、令人不安的氛围。',
    usage: '适合恐怖、悬疑、黑暗主题。',
    examples: ['恐怖森林', '诡异的人偶', '黑暗走廊'],
    relatedTerms: ['阴森', '诡异', '黑暗'],
    tips: '搭配"暗调"、"阴影"、"冷色"'
  },
  
  // 技法类
  {
    id: 'bokeh',
    name: '背景虚化',
    nameEn: 'Bokeh',
    category: 'technique',
    description: '主体清晰，背景模糊的光学效果。',
    usage: '适合人像、产品、特写。',
    examples: ['背景虚化的人像', '景深效果', '散景光斑'],
    relatedTerms: ['景深', '散景', '虚化'],
    tips: '搭配"大光圈"、"浅景深"'
  },
  {
    id: 'motion-blur',
    name: '动态模糊',
    nameEn: 'Motion Blur',
    category: 'technique',
    description: '运动物体产生的模糊效果，表现速度感。',
    usage: '适合运动、速度、动态主题。',
    examples: ['动态模糊的赛车', '运动模糊效果', '速度感'],
    relatedTerms: ['速度', '动感', '运动'],
    tips: '适合表现运动和速度'
  },
  {
    id: 'hdr',
    name: 'HDR效果',
    nameEn: 'HDR',
    category: 'technique',
    description: '高动态范围效果，亮部和暗部细节都清晰可见。',
    usage: '适合风景、建筑、需要高对比度的场景。',
    examples: ['HDR风景', 'HDR建筑', '高动态范围人像'],
    relatedTerms: ['高动态', '细节丰富'],
    tips: '注意避免过度处理'
  }
]

export function searchTerms(query: string): TermEntry[] {
  const lowerQuery = query.toLowerCase()
  return terminology.filter(term => 
    term.name.includes(query) ||
    term.nameEn?.toLowerCase().includes(lowerQuery) ||
    term.description.includes(query) ||
    term.examples.some(ex => ex.includes(query))
  )
}

export function getTermsByCategory(category: TermCategory): TermEntry[] {
  return terminology.filter(term => term.category === category)
}

export function getTermById(id: string): TermEntry | undefined {
  return terminology.find(term => term.id === id)
}
