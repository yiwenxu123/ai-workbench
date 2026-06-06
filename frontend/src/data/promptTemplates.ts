export interface PromptTemplate {
  id: string
  name: string
  category: 'tvc' | 'ecommerce' | 'social' | 'documentary' | 'animation'
  structure: string
  elements: {
    name: string
    description: string
    required: boolean
    examples: string[]
  }[]
  example: string
  tips: string[]
}

export const promptTemplates: PromptTemplate[] = [
  {
    id: 'tvc-ad',
    name: 'TVC广告片模板',
    category: 'tvc',
    structure: '【画质设定】+ 【视觉调性】+ 【时间轴分镜】+ 【音效配乐】',
    elements: [
      {
        name: '画质设定',
        description: '分辨率、帧率、画幅比例',
        required: true,
        examples: ['电影级 4K 画质，24fps 帧率，画幅比例 9:16', '1080p高清，30fps，16:9横屏']
      },
      {
        name: '视觉调性',
        description: '整体风格、色调、美学风格',
        required: true,
        examples: ['现代主义国风视觉调性，冷蓝、极简白、磨砂黑三色', '赛博朋克风格，霓虹色调', '温馨家庭风，暖色调']
      },
      {
        name: '时间轴分镜',
        description: '按秒数描述每个镜头的内容和运镜',
        required: true,
        examples: ['0-3秒：微距开场，镜头快推\n3-7秒：匹配剪辑转场\n7-15秒：品牌定格']
      },
      {
        name: '音效配乐',
        description: '背景音乐、音效、口播',
        required: false,
        examples: ['BGM为强工业重低音，每逢重音进行卡点', '男性口播浑厚有力，央视纪录片风格']
      }
    ],
    example: '电影级 4K 画质，24fps 帧率，画幅比例 9:16。全片采用"现代主义国风"视觉调性。冷蓝、极简白、磨砂黑三色构成核心色盘。0-3秒：微距开场，镜头采用 100mm 微距镜头快推。3-7秒：空间跃迁，执行3组快速匹配剪辑。7-11秒：动态交互与材质表达。11-15秒：品牌定格，镜头采用希区柯克变焦。',
    tips: [
      '时间轴分镜要精确到秒',
      '运镜描述要专业（如：希区柯克变焦、匹配剪辑）',
      '品牌露出放在结尾更有效'
    ]
  },
  {
    id: 'ecommerce-product',
    name: '电商产品广告模板',
    category: 'ecommerce',
    structure: '【产品描述】+ 【场景设定】+ 【运镜方式】+ 【卖点展示】',
    elements: [
      {
        name: '产品描述',
        description: '产品名称、材质、核心卖点',
        required: true,
        examples: ['高端钛合金智能手表，具有健康监测功能', '新疆兵团土蜂蜜，阿尔泰山自然成熟']
      },
      {
        name: '场景设定',
        description: '拍摄场景、背景、环境',
        required: true,
        examples: ['简约科技感工作室', '明亮厨房场景', '纯白背景']
      },
      {
        name: '运镜方式',
        description: '镜头运动方式',
        required: true,
        examples: ['低角度仰拍开始，缓慢推近至特写', '360度环绕展示', '微距镜头快推']
      },
      {
        name: '卖点展示',
        description: '产品卖点如何呈现',
        required: false,
        examples: ['微距展示纹理细节', '悬浮展示高级感', '蒸汽升起增加动态感']
      }
    ],
    example: '高端钛合金智能手表，在简约科技感工作室中缓慢旋转，镜头从低角度仰拍开始，缓慢推近至表盘特写，微距展示纹理，电影感商业广告风格，4K高清。',
    tips: [
      '产品要占据画面主体',
      '运镜要流畅不突兀',
      '卖点展示要自然融入'
    ]
  },
  {
    id: 'documentary-style',
    name: '纪录片风格模板',
    category: 'documentary',
    structure: '【口播设定】+ 【画面描述】+ 【时间轴】+ 【氛围营造】',
    elements: [
      {
        name: '口播设定',
        description: '配音音色、语调风格',
        required: true,
        examples: ['男性口播浑厚有力，央视纪录片风格', '女性口播温柔亲切']
      },
      {
        name: '画面描述',
        description: '画面内容、构图、光影',
        required: true,
        examples: ['产品悬浮于画面中央，顶光打下', '雪山、花海的虚化背景']
      },
      {
        name: '时间轴',
        description: '按秒数描述画面变化',
        required: true,
        examples: ['0-2秒：产品缓缓升起\n3-5秒：360度旋转展示\n6-10秒：品牌定格']
      },
      {
        name: '氛围营造',
        description: '整体氛围、情感基调',
        required: false,
        examples: ['庄重大气有文化底蕴', '温馨治愈', '神秘高级']
      }
    ],
    example: '央视纪录片风格，男性口播浑厚有力。0-2秒：黑色背景渐亮，蜂蜜瓶从画面下方缓缓升起悬浮于画面中央，顶光打下。口播："一年，只取一次。"3-5秒：镜头继续推近至瓶身特写，蜂蜜瓶360度顺时针缓慢旋转。',
    tips: [
      '口播文案要简洁有力',
      '画面与口播要配合',
      '纪录片风格增加信任感'
    ]
  },
  {
    id: 'costume-change',
    name: '换装视频模板',
    category: 'social',
    structure: '【@素材引用】+ 【转场方式】+ 【节奏设定】+ 【风格描述】',
    elements: [
      {
        name: '@素材引用',
        description: '使用@符号指定素材用途',
        required: true,
        examples: ['@图一 模特穿上 图23456789 8套衣服', '服装参考@图片1@图片2的样式']
      },
      {
        name: '转场方式',
        description: '服装切换的转场效果',
        required: true,
        examples: ['每0.5秒自动切换服装，加入粒子消散特效', '转身瞬间切换', '闪光特效转场']
      },
      {
        name: '节奏设定',
        description: '视频节奏、卡点',
        required: false,
        examples: ['BGM卡点转场', '每逢重音进行切换', '视频节奏参考@视频1']
      },
      {
        name: '风格描述',
        description: '整体视觉风格',
        required: false,
        examples: ['黑白高反光影，极简主义冷白空间', '时尚感十足', '电影质感']
      }
    ],
    example: '@图一 模特穿上 图23456789 8套衣服，保持模特面部和姿势一致，只更换服装款式和颜色，流畅转场，时尚感十足。',
    tips: [
      '使用@符号明确指定素材用途',
      '保持模特一致性是关键',
      '转场要流畅自然'
    ]
  },
  {
    id: 'story-ad',
    name: '故事型广告模板',
    category: 'tvc',
    structure: '【场景设定】+ 【人物描述】+ 【情节发展】+ 【产品露出】',
    elements: [
      {
        name: '场景设定',
        description: '故事发生的场景',
        required: true,
        examples: ['昏暗客厅，几位年轻人围坐在沙发上看恐怖片', '篮球比赛更衣室']
      },
      {
        name: '人物描述',
        description: '人物、表情、动作',
        required: true,
        examples: ['有人抱枕捂脸、有人尖叫、有人跳起来', '矫情造作的甄嬛传里的华妃']
      },
      {
        name: '情节发展',
        description: '故事如何展开',
        required: true,
        examples: ['主角淡定吃薯片，咔嚓一声极其响亮', '华妃吃士力架后变成运动猛男']
      },
      {
        name: '产品露出',
        description: '产品如何出现',
        required: true,
        examples: ['背景虚化的一群人，乐事产品呈现', '片尾士力架落版']
      }
    ],
    example: '昏暗客厅，几位年轻人围坐在沙发上看恐怖片。年轻人有人抱枕捂脸、有人尖叫。主角特写，只有一个女生坐在沙发角落，一手拿着乐事桶装，一手依旧淡定地吃薯片，"咔嚓"一声，极其响亮。其他人齐刷刷回头看他。背景虚化的一群人，乐事产品呈现。',
    tips: [
      '故事要有反转或幽默点',
      '产品出现要自然不突兀',
      '结尾要有品牌露出'
    ]
  }
]

export const templateCategories = [
  { value: 'tvc', label: 'TVC广告', icon: 'Clapperboard' },
  { value: 'ecommerce', label: '电商产品', icon: 'ShoppingCart' },
  { value: 'documentary', label: '纪录片', icon: 'Video' },
  { value: 'social', label: '社媒玩法', icon: 'Smartphone' },
  { value: 'animation', label: '动画', icon: 'Palette' }
]

export function getTemplateById(id: string): PromptTemplate | undefined {
  return promptTemplates.find(t => t.id === id)
}

export function getTemplatesByCategory(category: string): PromptTemplate[] {
  return promptTemplates.filter(t => t.category === category)
}
