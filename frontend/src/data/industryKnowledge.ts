export interface IndustryKnowledge {
  id: string
  title: string
  category: 'ecommerce' | 'corporate' | 'social' | 'culture' | 'education'
  content: string
  tips: string[]
  bestPractices: string[]
  commonMistakes: string[]
  relatedTemplates: string[]
}

export const industryKnowledge: IndustryKnowledge[] = [
  {
    id: 'ecommerce-product-photo',
    title: '电商产品摄影要点',
    category: 'ecommerce',
    content: '电商产品图是影响购买决策的关键因素。高质量的产品图能提升转化率30%以上。',
    tips: [
      '主图必须白底，产品占比70-80%',
      '光线均匀柔和，避免强烈阴影',
      '产品细节清晰，材质纹理可见',
      '多角度展示，至少5张图片'
    ],
    bestPractices: [
      '使用影棚柔光箱或自然光',
      '产品放置在画面中心',
      '保持产品与背景距离，避免阴影',
      '后期微调曝光和对比度'
    ],
    commonMistakes: [
      '背景杂乱干扰产品展示',
      '光线不均匀导致色差',
      '产品变形或比例失真',
      '过度修图失去真实感'
    ],
    relatedTemplates: ['product-white-bg', 'product-lifestyle', 'product-closeup']
  },
  {
    id: 'ecommerce-video-ad',
    title: '电商投流视频制作',
    category: 'ecommerce',
    content: '电商投流视频是抖音/淘宝投手日更10条的核心武器。3秒完播率决定广告效果，前3秒必须抓住用户注意力。',
    tips: [
      '前3秒必须有视觉冲击或悬念',
      '产品要在前5秒出现',
      '时长控制在15秒以内',
      '结尾要有明确的购买引导'
    ],
    bestPractices: [
      '使用微距开场展示产品细节',
      '匹配剪辑保持节奏感',
      '产品悬浮展示增加高级感',
      '口播文案简洁有力'
    ],
    commonMistakes: [
      '开场拖沓，用户划走',
      '产品出现太晚',
      '节奏混乱无卡点',
      '缺少购买引导'
    ],
    relatedTemplates: ['milk-tea-brand-ad', 'honey-documentary-ad']
  },
  {
    id: 'ecommerce-costume-change',
    title: '服装换装视频技巧',
    category: 'ecommerce',
    content: '服装换装视频是电商服装类目最有效的展示方式，一个模特可以展示多套服装，节省拍摄成本。',
    tips: [
      '使用@符号指定素材用途',
      '保持模特面部和姿势一致',
      '转场要流畅自然',
      '每套服装展示时间0.5-1秒'
    ],
    bestPractices: [
      '黑白高反光影增强时尚感',
      '粒子消散特效增加视觉冲击',
      'BGM卡点转场保持节奏',
      '低角度环绕运镜展示细节'
    ],
    commonMistakes: [
      '模特面部不一致',
      '转场生硬不流畅',
      '服装展示时间过长',
      '缺少节奏感'
    ],
    relatedTemplates: ['fashion-quick-change', 'model-costume-change']
  },
  {
    id: 'ecommerce-detail-page',
    title: '详情页设计原则',
    category: 'ecommerce',
    content: '详情页是转化的核心阵地，需要通过视觉引导用户完成购买决策。',
    tips: [
      '首屏展示核心卖点',
      '使用场景图增强代入感',
      '细节图展示品质',
      '对比图突出优势'
    ],
    bestPractices: [
      '信息层级清晰，重点突出',
      '图文结合，避免纯文字',
      '保持品牌风格统一',
      '移动端优先设计'
    ],
    commonMistakes: [
      '信息过载，用户找不到重点',
      '图片质量参差不齐',
      '卖点描述不清晰',
      '缺少购买引导'
    ],
    relatedTemplates: ['product-lifestyle']
  },
  {
    id: 'brand-tvc-ad',
    title: 'TVC广告制作要点',
    category: 'corporate',
    content: 'TVC（电视商业广告）是品牌广告的最高形式，需要4A公司级别的制作质量。电影级画质、专业运镜、品牌调性是核心要素。',
    tips: [
      '画质设定：4K、24fps、电影级调色',
      '运镜要专业：希区柯克变焦、匹配剪辑、环绕镜头',
      '品牌露出放在结尾更有效',
      '时长15-30秒为宜'
    ],
    bestPractices: [
      '时间轴分镜精确到秒',
      '视觉调性要与品牌一致',
      '音效配乐要配合画面',
      '产品/品牌露出要自然'
    ],
    commonMistakes: [
      '画质不够专业',
      '运镜混乱无逻辑',
      '品牌露出太突兀',
      '时长过长用户流失'
    ],
    relatedTemplates: ['milk-tea-brand-ad', 'glasses-brand-ad', 'tea-brand-ad']
  },
  {
    id: 'brand-story-ad',
    title: '故事型广告技巧',
    category: 'corporate',
    content: '故事型广告通过情节发展吸引观众，产品自然融入故事中，比硬广更有效。反转和幽默是关键元素。',
    tips: [
      '场景设定要有代入感',
      '人物表情动作要自然',
      '情节要有反转或幽默点',
      '产品出现要自然不突兀'
    ],
    bestPractices: [
      '恐怖片氛围制造悬念',
      '反差萌制造趣味',
      '产品解决故事中的问题',
      '结尾要有品牌露出'
    ],
    commonMistakes: [
      '故事与产品无关',
      '产品出现太突兀',
      '缺少反转或幽默',
      '结尾没有品牌露出'
    ],
    relatedTemplates: ['snickers-ad', 'lays-ad', 'diapers-ad']
  },
  {
    id: 'brand-documentary',
    title: '纪录片风格广告',
    category: 'corporate',
    content: '纪录片风格广告增加信任感和权威感，适合食品、农产品、健康产品等需要建立信任的品牌。',
    tips: [
      '口播音色要浑厚有力',
      '画面要真实自然',
      '文案要简洁有力',
      '整体氛围要庄重大气'
    ],
    bestPractices: [
      '央视纪录片风格增加权威感',
      '产品悬浮展示增加高级感',
      '环境背景增加故事性',
      '口播与画面要配合'
    ],
    commonMistakes: [
      '口播与画面不配合',
      '画面过于花哨',
      '文案冗长无重点',
      '缺少情感共鸣'
    ],
    relatedTemplates: ['honey-documentary-ad']
  },
  {
    id: 'corporate-brand-image',
    title: '品牌形象设计',
    category: 'corporate',
    content: '品牌形象是企业视觉识别的核心，需要在所有触点保持一致性。',
    tips: [
      '确定品牌主色调和辅助色',
      '设计统一的视觉元素',
      '保持字体使用规范',
      '建立品牌图片风格指南'
    ],
    bestPractices: [
      '创建品牌视觉手册',
      '统一所有渠道视觉风格',
      '定期审核品牌一致性',
      '根据品牌调性选择图片风格'
    ],
    commonMistakes: [
      '视觉风格不统一',
      '频繁更换品牌形象',
      '忽视品牌调性',
      '过度设计失去辨识度'
    ],
    relatedTemplates: ['marketing-poster', 'illustration-brand']
  },
  {
    id: 'corporate-team-photo',
    title: '团队展示技巧',
    category: 'corporate',
    content: '团队照片是企业文化和专业形象的重要展示窗口。',
    tips: [
      '选择专业的拍摄环境',
      '着装统一或协调',
      '表情自然自信',
      '构图体现团队氛围'
    ],
    bestPractices: [
      '提前沟通着装要求',
      '选择光线充足的环境',
      '多拍几组备选',
      '后期统一调色风格'
    ],
    commonMistakes: [
      '背景杂乱不专业',
      '表情僵硬不自然',
      '着装风格不统一',
      '光线不足或过曝'
    ],
    relatedTemplates: ['portrait-team', 'portrait-business']
  },
  {
    id: 'social-xiaohongshu',
    title: '小红书封面规范',
    category: 'social',
    content: '小红书封面是吸引点击的第一要素，需要在信息流中脱颖而出。',
    tips: [
      '尺寸比例3:4，竖版展示',
      '标题醒目，字体清晰',
      '色彩鲜艳，吸引眼球',
      '人物出镜增加亲和力'
    ],
    bestPractices: [
      '使用对比色突出标题',
      '封面与内容强相关',
      '保持系列内容风格统一',
      '添加品牌水印或标识'
    ],
    commonMistakes: [
      '标题过小看不清',
      '图片与内容不符',
      '风格过于杂乱',
      '忽视移动端展示效果'
    ],
    relatedTemplates: []
  },
  {
    id: 'social-video-viral',
    title: '社媒爆款视频公式',
    category: 'social',
    content: '社媒爆款视频需要Viral内容公式：玩梗、变装、特效是三大核心玩法。3秒内必须抓住用户注意力。',
    tips: [
      '前3秒必须有视觉冲击',
      '变装转场要流畅',
      '特效要酷炫但不浮夸',
      '时长控制在10秒以内'
    ],
    bestPractices: [
      '能量波、火花等特效增加视觉冲击',
      '慢动作突出特效细节',
      '转身/闪光作为转场点',
      'BGM卡点保持节奏'
    ],
    commonMistakes: [
      '开场拖沓无冲击',
      '转场生硬不流畅',
      '特效过多过杂',
      '时长过长用户流失'
    ],
    relatedTemplates: ['fight-effect', 'costume-change', 'fashion-poster-change']
  },
  {
    id: 'social-wechat-article',
    title: '公众号配图技巧',
    category: 'social',
    content: '公众号配图需要与文章内容呼应，提升阅读体验。',
    tips: [
      '封面图尺寸900x500',
      '配图风格与文章调性一致',
      '适当使用信息图',
      '保持系列文章风格统一'
    ],
    bestPractices: [
      '封面图突出主题',
      '正文配图辅助理解',
      '使用原创图片或授权素材',
      '压缩图片保证加载速度'
    ],
    commonMistakes: [
      '配图与内容无关',
      '图片质量过低',
      '版权问题',
      '风格不统一'
    ],
    relatedTemplates: ['ppt-cover', 'ppt-content']
  },
  {
    id: 'culture-intangible',
    title: '非遗展示方法',
    category: 'culture',
    content: '非物质文化遗产展示需要尊重传统，同时符合现代审美。',
    tips: [
      '尊重传统工艺和文化内涵',
      '突出技艺的独特性',
      '讲述传承人故事',
      '结合现代设计元素'
    ],
    bestPractices: [
      '深入了解文化背景',
      '与传承人充分沟通',
      '保持真实性',
      '创新表达方式'
    ],
    commonMistakes: [
      '过度商业化失去文化内涵',
      '展示方式过于陈旧',
      '忽视文化背景介绍',
      '风格与内容不匹配'
    ],
    relatedTemplates: ['illustration-concept']
  },
  {
    id: 'culture-festival',
    title: '节庆营销策略',
    category: 'culture',
    content: '节庆营销需要把握时机，创造与节日氛围契合的内容。',
    tips: [
      '提前规划节日内容日历',
      '结合品牌特色设计',
      '注意文化敏感性',
      '把握节日热点时机'
    ],
    bestPractices: [
      '提前2周开始预热',
      '设计系列内容',
      '结合促销活动',
      '保持品牌调性'
    ],
    commonMistakes: [
      '临时抱佛脚',
      '设计过于俗套',
      '忽视文化禁忌',
      '与品牌调性不符'
    ],
    relatedTemplates: ['marketing-banner']
  },
  {
    id: 'education-infographic',
    title: '科普图解设计',
    category: 'education',
    content: '科普图解需要将复杂概念可视化，让知识易于理解。',
    tips: [
      '信息层级清晰',
      '使用简洁的视觉元素',
      '配色协调不花哨',
      '文字精炼准确'
    ],
    bestPractices: [
      '先梳理信息结构',
      '使用图标和图表',
      '保持视觉一致性',
      '适当留白'
    ],
    commonMistakes: [
      '信息过载',
      '视觉元素过多',
      '配色混乱',
      '文字冗长'
    ],
    relatedTemplates: ['ppt-data']
  }
]

export const industryCategories = [
  { value: 'ecommerce', label: '电商行业', icon: 'ShoppingCart' },
  { value: 'corporate', label: '企业宣传', icon: 'Building2' },
  { value: 'social', label: '新媒体', icon: 'Smartphone' },
  { value: 'culture', label: '文化内容', icon: 'Palette' },
  { value: 'education', label: '教育科普', icon: 'BookOpen' }
]

export function getKnowledgeById(id: string): IndustryKnowledge | undefined {
  return industryKnowledge.find(k => k.id === id)
}

export function getKnowledgeByCategory(category: string): IndustryKnowledge[] {
  return industryKnowledge.filter(k => k.category === category)
}

export function searchKnowledge(query: string): IndustryKnowledge[] {
  const lowerQuery = query.toLowerCase()
  return industryKnowledge.filter(k => 
    k.title.toLowerCase().includes(lowerQuery) ||
    k.content.toLowerCase().includes(lowerQuery) ||
    k.tips.some(t => t.toLowerCase().includes(lowerQuery))
  )
}
