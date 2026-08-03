/**
 * 镜头语言知识库
 * 包含景别、运镜、视角等专业术语
 * 运镜按6大类组织：基础方向、空间移动、人物跟随、升降环绕、情绪强化、转场衔接
 */

export type ShotType =
  | 'extreme_long'
  | 'full'
  | 'medium'
  | 'close_up'
  | 'extreme_close_up'

export type CameraMovementCategory =
  | 'basic_direction'
  | 'spatial_movement'
  | 'character_follow'
  | 'crane_orbit'
  | 'emotion_intensify'
  | 'transition'

export type CameraMovement =
  | 'dolly_in'
  | 'dolly_out'
  | 'pan_left'
  | 'pan_right'
  | 'tilt_up'
  | 'tilt_down'
  | 'zoom_in'
  | 'zoom_out'
  | 'static'
  | 'dolly'
  | 'truck_left'
  | 'truck_right'
  | 'tracking'
  | 'pedestal_up'
  | 'pedestal_down'
  | 'crane_jib'
  | 'orbit'
  | 'follow_shot'
  | 'chase_shot'
  | 'lead_shot'
  | 'side_follow'
  | 'over_shoulder_follow'
  | 'pov_move'
  | 'rising_shot'
  | 'descending_shot'
  | 'rise_reveal'
  | 'dive_down'
  | 'arc_orbit'
  | 'top_down'
  | 'dutch_angle'
  | 'whip_pan'
  | 'slow_push'
  | 'handheld'
  | 'crash_zoom'
  | 'close_up_push'
  | 'reveal'
  | 'foreground_wipe'
  | 'rack_focus'
  | 'parallax'
  | 'match_move'
  | 'speed_ramp'

export type CameraAngle =
  | 'eye_level'
  | 'low_angle'
  | 'high_angle'
  | 'dutch_angle'
  | 'pov'
  | 'over_shoulder'

export type MovementSpeed = 'very_slow' | 'slow' | 'medium' | 'fast' | 'very_fast'

export type EmotionTag =
  | 'calm'
  | 'tense'
  | 'warm'
  | 'shocking'
  | 'grand'
  | 'mysterious'
  | 'immersive'
  | 'documentary'
  | 'dynamic'
  | 'delicate'

export interface ShotTypeOption {
  id: ShotType
  name: string
  nameEn: string
  keywords: string[]
  useCase: string
  icon: string
}

export interface CameraMovementOption {
  id: CameraMovement
  name: string
  nameEn: string
  category: CameraMovementCategory
  keywords: string[]
  useCase: string
  tips: string[]
  examples: string[]
  suitableEmotions: EmotionTag[]
  recommendedSpeed: MovementSpeed
  icon: string
  isHighFrequency?: boolean
}

export interface CameraAngleOption {
  id: CameraAngle
  name: string
  nameEn: string
  keywords: string[]
  useCase: string
  icon: string
}

export interface MovementCategoryMeta {
  id: CameraMovementCategory
  name: string
  description: string
  purpose: string
  icon: string
}

export interface ShotCombination {
  id: string
  name: string
  description: string
  icon: string
  shots: {
    type: ShotType
    movement: CameraMovement
    duration: number
  }[]
  suitableFor: string[]
  prompt: string
}

export interface StoryboardShot {
  id: string
  name: string
  prompt: string
  negativePrompt?: string
  shotType?: ShotType
  cameraMovement?: CameraMovement
  cameraAngle?: CameraAngle
  movementSpeed?: MovementSpeed
  emotionTag?: EmotionTag
  duration: number
  transition?: string
  notes?: string
}

export interface QuizQuestion {
  id: string
  question: string
  options: { label: string; value: string }[]
  correctAnswer: string
  explanation: string
  category: 'basic' | 'intermediate' | 'advanced'
  relatedMovement?: CameraMovement
}

export const shotLanguageQuiz: QuizQuestion[] = [
  {
    id: 'q1',
    question: '想要突出产品的高端质感，让观众觉得产品很有分量，应该使用哪种运镜？',
    options: [
      { label: '快速变焦（Zoom In Fast）', value: 'zoom_in_fast' },
      { label: '慢推镜头（Slow Push）', value: 'slow_push' },
      { label: '环绕运镜（Orbit）', value: 'orbit' },
      { label: '静态镜头（Static）', value: 'static' },
    ],
    correctAnswer: 'slow_push',
    explanation: '慢推镜头通过缓慢靠近主体，逐步揭示细节，能营造高级感和仪式感，非常适合高端产品展示。环绕运镜适合360度展示产品全貌，但慢推在"质感"营造上更胜一筹。',
    category: 'basic',
    relatedMovement: 'slow_push',
  },
  {
    id: 'q2',
    question: '以下哪种运镜最适合营造"悬疑、未知"的情绪？',
    options: [
      { label: '推镜头（Dolly In）', value: 'dolly_in' },
      { label: '拉镜头（Dolly Out）', value: 'dolly_out' },
      { label: '横摇（Pan Horizontal）', value: 'pan_horizontal' },
      { label: '手持抖动（Handheld）', value: 'handheld' },
    ],
    correctAnswer: 'dolly_out',
    explanation: '拉镜头逐步揭示环境，让观众看到越来越多的信息，这种"逐渐发现"的感觉天然带有悬疑感。同时主体在画面中逐渐变小，会产生孤独、渺小的感觉，进一步强化未知情绪。',
    category: 'basic',
    relatedMovement: 'dolly_out',
  },
  {
    id: 'q3',
    question: '拍摄美食视频时，想要展示食物的细节纹理和热气腾腾的感觉，最合适的组合是？',
    options: [
      { label: '全景 + 快速变焦', value: 'a' },
      { label: '特写 + 慢推', value: 'b' },
      { label: '中景 + 横摇', value: 'c' },
      { label: '大远景 + 升降', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '特写镜头能聚焦食物纹理，慢推逐步靠近让观众"发现"细节，加上蒸汽动态，最能勾起食欲。这是美食短视频的经典组合。',
    category: 'basic',
    relatedMovement: 'slow_push',
  },
  {
    id: 'q4',
    question: '"希区柯克式变焦"（Dolly Zoom）的核心视觉效果是什么？',
    options: [
      { label: '画面越来越清晰', value: 'a' },
      { label: '主体大小不变，背景空间透视变化', value: 'b' },
      { label: '画面逐渐模糊', value: 'c' },
      { label: '颜色逐渐饱和', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '滑动变焦的精髓在于：镜头一边移动一边变焦，让主体在画面中的大小保持不变，但背景的透视关系剧烈变化，从而产生晕眩、不安、超现实的感觉。',
    category: 'intermediate',
    relatedMovement: 'dolly_zoom',
  },
  {
    id: 'q5',
    question: '想要展示一个空间的宏大和壮阔，以下哪种运镜组合效果最好？',
    options: [
      { label: '特写 + 快推', value: 'a' },
      { label: '大远景 + 慢拉', value: 'b' },
      { label: '中景 + 横摇', value: 'c' },
      { label: '近景 + 环绕', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '大远景本身就展现空间的广阔，再加上慢拉逐步揭示更多环境，会让观众感受到强烈的空间震撼。常用于电影开场、自然风景、建筑展示等场景。',
    category: 'basic',
  },
  {
    id: 'q6',
    question: '在人物对话场景中，使用"过肩镜头"（OTS）配合缓慢推近，主要目的是什么？',
    options: [
      { label: '展示人物的全身穿搭', value: 'a' },
      { label: '将观众带入对话，增强代入感和亲密感', value: 'b' },
      { label: '展示环境背景', value: 'c' },
      { label: '节省拍摄成本', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '过肩镜头让观众站在"偷听者"的角度，加上慢推逐步靠近，会增强对话的私密感和紧张感，是影视剧对话场景的标准手法。',
    category: 'intermediate',
  },
  {
    id: 'q7',
    question: '跟随镜头（Follow Shot）和侧跟镜头（Side Follow）的主要区别是什么？',
    options: [
      { label: '使用的摄像机不同', value: 'a' },
      { label: '摄像机相对于主体的运动方向不同', value: 'b' },
      { label: '拍摄时长不同', value: 'c' },
      { label: '没有区别', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '跟拍镜头是在主体正后方（或前方）跟随，强调"代入感"；侧跟镜头是在主体侧面平行移动，强调"动作展示"和速度感。两者的情绪效果完全不同。',
    category: 'intermediate',
    relatedMovement: 'follow_shot',
  },
  {
    id: 'q8',
    question: '想要营造"真实感、纪实感、粗糙感"，最适合使用哪种运镜方式？',
    options: [
      { label: '轨道推进（Tracking Shot）', value: 'tracking_shot' },
      { label: '斯坦尼康稳定跟拍', value: 'follow_shot' },
      { label: '手持运镜（Handheld）', value: 'handheld' },
      { label: '升降镜头（Crane/Jib）', value: 'crane_jib' },
    ],
    correctAnswer: 'handheld',
    explanation: '手持运镜的轻微抖动模拟了人眼观察的"不完美"，会让观众觉得画面是"真实捕捉"的，而非刻意安排。纪录片、战地题材、伪纪实电影常用这种手法。',
    category: 'basic',
    relatedMovement: 'handheld',
  },
  {
    id: 'q9',
    question: '电商产品主图视频，时长5秒，想要在短时间内抓住注意力并展示产品全貌，最优运镜方案是？',
    options: [
      { label: '静态展示5秒', value: 'a' },
      { label: '开头快推钩子 + 环绕展示细节', value: 'b' },
      { label: '全程缓慢横摇', value: 'c' },
      { label: '希区柯克变焦', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '短视频时代，前1秒决定生死。快速变焦（快推）能瞬间抓住眼球（钩子），然后用环绕运镜360度展示产品，在5秒内最大化信息传递。这是电商短视频的黄金公式。',
    category: 'intermediate',
    relatedMovement: 'zoom_in_fast',
  },
  {
    id: 'q10',
    question: '"匹配剪辑"（Match Cut）配合运镜的核心原理是什么？',
    options: [
      { label: '让两个镜头的颜色完全一致', value: 'a' },
      { label: '利用运动方向或形状的相似性连接两个镜头', value: 'b' },
      { label: '用同样的演员', value: 'c' },
      { label: '用同样的背景音乐', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '匹配剪辑利用视觉上的相似性（形状、运动方向、构图）来连接两个不同时空的镜头，让转场流畅自然。运镜方向的延续是最常用的匹配剪辑手法之一。',
    category: 'advanced',
  },
  {
    id: 'q11',
    question: '低角度仰拍（Low Angle）通常会给观众什么心理感受？',
    options: [
      { label: '亲切感、平等感', value: 'a' },
      { label: '压迫感、权威感、高大感', value: 'b' },
      { label: '脆弱感、渺小感', value: 'c' },
      { label: '客观感、中立感', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '低角度让观众"仰望"主体，主体在画面中显得高大、有力量，天然带有权威感和压迫感。常用于英雄登场、反派特写、展示建筑宏伟等场景。',
    category: 'basic',
    relatedMovement: 'low_angle',
  },
  {
    id: 'q12',
    question: '以下哪种场景最适合使用"一镜到底"（Long Take）？',
    options: [
      { label: '快速剪辑的动作片', value: 'a' },
      { label: '需要营造真实感和沉浸感的长场景', value: 'b' },
      { label: '产品特写展示', value: 'c' },
      { label: '美食制作过程', value: 'd' },
    ],
    correctAnswer: 'b',
    explanation: '一镜到底不通过剪辑打断时间和空间，观众会感觉"这是真实发生的"，代入感极强。但难度高、成本高，适合关键场景使用，而非全片都是。',
    category: 'advanced',
  },
]


export const movementCategories: MovementCategoryMeta[] = [
  {
    id: 'basic_direction',
    name: '基础方向类',
    description: '先控制镜头往哪动、画面怎么变',
    purpose: '掌握上下左右的基本控制',
    icon: 'Move',
  },
  {
    id: 'spatial_movement',
    name: '空间移动类',
    description: '决定镜头路径，也决定空间关系',
    purpose: '强化空间关系，让画面更有路径感',
    icon: 'Map',
  },
  {
    id: 'character_follow',
    name: '人物跟随类',
    description: '让观众跟着人物进入场景',
    purpose: '主体关系、节奏和路线',
    icon: 'User',
  },
  {
    id: 'crane_orbit',
    name: '升降环绕类',
    description: '突出层次、气势和空间揭示',
    purpose: '制造悬念或仪式感',
    icon: 'Orbit',
  },
  {
    id: 'emotion_intensify',
    name: '情绪强化类',
    description: '不是为了炫，是为了强化情绪',
    purpose: '服务紧张、压迫、亲密、冲击',
    icon: 'Zap',
  },
  {
    id: 'transition',
    name: '转场衔接类',
    description: '让镜头之间更顺、更有连续性',
    purpose: '动作、焦点和遮挡的衔接',
    icon: 'ArrowRightLeft',
  },
]

export const shotTypes: ShotTypeOption[] = [
  {
    id: 'extreme_long',
    name: '远景',
    nameEn: 'Extreme Long Shot',
    keywords: ['extreme long shot', 'wide establishing shot', '全景远景', '大远景'],
    useCase: '开场定调、展示宏大环境、企业总部外景',
    icon: 'Mountain',
  },
  {
    id: 'full',
    name: '全景',
    nameEn: 'Full Shot',
    keywords: ['full body shot', 'full shot', '人物全身', '产品完整展示'],
    useCase: '展示人物全身与环境关系、产品全貌',
    icon: 'User',
  },
  {
    id: 'medium',
    name: '中景',
    nameEn: 'Medium Shot',
    keywords: ['medium shot', 'waist-up', '腰部以上', '中景镜头'],
    useCase: '人物对话、产品细节展示、操作演示',
    icon: 'User',
  },
  {
    id: 'close_up',
    name: '近景',
    nameEn: 'Close-Up',
    keywords: ['close-up', 'close up', '面部特写', '产品特写镜头'],
    useCase: '突出情感、产品局部特写、强调细节',
    icon: 'Search',
  },
  {
    id: 'extreme_close_up',
    name: '特写',
    nameEn: 'Extreme Close-Up',
    keywords: ['extreme close-up', 'extreme close up', '眼部特写', '微观细节'],
    useCase: '极致细节、情绪张力、logo/标识展示',
    icon: 'Eye',
  },
]

export const cameraMovements: CameraMovementOption[] = [
  // ── A. 基础方向类（6个）──
  {
    id: 'dolly_in',
    name: '推镜',
    nameEn: 'Push in / Dolly In',
    category: 'basic_direction',
    keywords: ['dolly in', 'slow push in', '镜头缓慢推进', 'camera moves forward'],
    useCase: '靠近主体，突出细节，情绪逐渐集中',
    tips: [
      '主体、方向、速度要写清',
      '推镜是镜头位置移动，不是变焦',
      '速度要稳，避免忽快忽慢',
    ],
    examples: [
      '年轻女生站在海边，镜头缓慢推近，从中景到近景，风吹动头发，突出安静又有情绪的氛围',
    ],
    suitableEmotions: ['delicate', 'calm', 'tense'],
    recommendedSpeed: 'slow',
    icon: 'ArrowRight',
    isHighFrequency: true,
  },
  {
    id: 'dolly_out',
    name: '拉镜',
    nameEn: 'Pull out / Dolly Out',
    category: 'basic_direction',
    keywords: ['dolly out', 'pull back', '镜头拉远', 'camera pulls back'],
    useCase: '拉远主体，交代环境，适合结尾、反转、环境交代',
    tips: [
      '后退要平稳，避免乱抖',
      '从细节到全局，营造揭示感',
    ],
    examples: [
      '从人物特写缓慢拉远，逐渐展现周围的宏大环境，交代故事背景',
    ],
    suitableEmotions: ['grand', 'calm'],
    recommendedSpeed: 'slow',
    icon: 'ArrowLeft',
    isHighFrequency: true,
  },
  {
    id: 'pan_left',
    name: '左摇',
    nameEn: 'Pan Left',
    category: 'basic_direction',
    keywords: ['pan left', 'pan to the left', '向左摇镜', '水平左摇'],
    useCase: '展示横向空间、跟随运动、扫描场景',
    tips: ['转动速度要均匀', '交代空间、连接多个对象'],
    examples: [
      '镜头从左向右缓慢摇动，展示整条街道的环境和人物',
    ],
    suitableEmotions: ['calm', 'documentary'],
    recommendedSpeed: 'medium',
    icon: 'ArrowLeft',
    isHighFrequency: true,
  },
  {
    id: 'pan_right',
    name: '右摇',
    nameEn: 'Pan Right',
    category: 'basic_direction',
    keywords: ['pan right', 'pan to the right', '向右摇镜', '水平右摇'],
    useCase: '展示横向空间、跟随运动、扫描场景',
    tips: ['转动速度要均匀', '交代空间、连接多个对象'],
    examples: [
      '镜头从左向右缓慢摇动，展示整条街道的环境和人物',
    ],
    suitableEmotions: ['calm', 'documentary'],
    recommendedSpeed: 'medium',
    icon: 'ArrowRight',
    isHighFrequency: true,
  },
  {
    id: 'tilt_up',
    name: '上摇（俯仰）',
    nameEn: 'Tilt Up',
    category: 'basic_direction',
    keywords: ['tilt up', 'tilt upward', '镜头向上摇动', '俯仰上摇'],
    useCase: '上下转动，展示高低，从脚到脸、从低到高',
    tips: ['起止点要明确', '适合展示高大建筑或人物全貌'],
    examples: [
      '镜头从人物脚部缓慢向上摇动，展示全身造型和气势',
    ],
    suitableEmotions: ['grand'],
    recommendedSpeed: 'medium',
    icon: 'ArrowUp',
    isHighFrequency: true,
  },
  {
    id: 'tilt_down',
    name: '下摇（俯仰）',
    nameEn: 'Tilt Down',
    category: 'basic_direction',
    keywords: ['tilt down', 'tilt downward', '镜头向下摇动', '俯仰下摇'],
    useCase: '上下转动，展示高低，从高到低、揭示细节',
    tips: ['起止点要明确', '从整体到细节的揭示'],
    examples: [
      '镜头从天空缓慢向下摇动，落在地面的人物身上',
    ],
    suitableEmotions: ['mysterious'],
    recommendedSpeed: 'medium',
    icon: 'ArrowDown',
  },
  {
    id: 'zoom_in',
    name: '变焦拉近',
    nameEn: 'Zoom in',
    category: 'basic_direction',
    keywords: ['zoom in', 'zoom in physically', '变焦拉近', '焦距放大'],
    useCase: '通过焦距变化让画面放大，快速聚焦重点',
    tips: [
      '注意：变焦≠推镜，推镜是空间关系变化，变焦是视野改变',
      '容易产生压缩感，使用时注意',
    ],
    examples: [
      '镜头变焦拉近，聚焦在人物手中的物品上',
    ],
    suitableEmotions: ['shocking', 'tense'],
    recommendedSpeed: 'medium',
    icon: 'Maximize2',
  },
  {
    id: 'zoom_out',
    name: '变焦拉远',
    nameEn: 'Zoom out',
    category: 'basic_direction',
    keywords: ['zoom out', 'zoom out physically', '变焦拉远', '焦距缩小'],
    useCase: '通过焦距变化让画面缩小，拉出更宽的视野',
    tips: [
      '注意：变焦≠拉镜，拉镜是空间关系变化',
      '不要和推拉混为一谈',
    ],
    examples: [
      '从细节处变焦拉远，展现更广阔的环境',
    ],
    suitableEmotions: ['grand'],
    recommendedSpeed: 'medium',
    icon: 'Minimize2',
  },
  {
    id: 'static',
    name: '固定镜头',
    nameEn: 'Static Shot',
    category: 'basic_direction',
    keywords: ['static shot', 'fixed camera', '固定机位', '静止镜头'],
    useCase: '稳定展示、对话场景、产品静态展示',
    tips: ['画面稳定，适合需要观众专注内容的场景'],
    examples: [],
    suitableEmotions: ['calm', 'documentary'],
    recommendedSpeed: 'medium',
    icon: 'Camera',
  },

  // ── B. 空间移动类（6个）──
  {
    id: 'dolly',
    name: '轨道推进',
    nameEn: 'Dolly',
    category: 'spatial_movement',
    keywords: ['dolly shot', 'dolly move', '轨道移动', '沿轨道前进'],
    useCase: '摄影机沿前后路径平稳移动，空间关系变化明显，制造沉浸感',
    tips: [
      '前后路径要稳定',
      '前进推近拉近距离，后移拉远展示空间',
      'Dolly是前后路径移动，不是变焦Zoom',
    ],
    examples: [
      '摄影机沿轨道向前推进，逐渐靠近站在场景中的人物，空间层次逐渐展开',
    ],
    suitableEmotions: ['immersive', 'calm'],
    recommendedSpeed: 'slow',
    icon: 'MoveHorizontal',
    isHighFrequency: true,
  },
  {
    id: 'truck_right',
    name: '侧向平移',
    nameEn: 'Truck / Truck Right',
    category: 'spatial_movement',
    keywords: ['truck right', 'sideways movement', '横向平移', '侧向移动'],
    useCase: '摄影机与主体大致平行地左右移动，展示横向空间、并行观察人物或场景',
    tips: [
      '保持主体关系，不要漂移太乱',
      'Truck是左右平移，不是环绕Orbit',
    ],
    examples: [
      '镜头从人物左侧向右侧平行移动，保持侧面中景，展现步行状态和街道延伸感',
    ],
    suitableEmotions: ['dynamic', 'documentary'],
    recommendedSpeed: 'medium',
    icon: 'MoveHorizontal',
    isHighFrequency: true,
  },
  {
    id: 'truck_left',
    name: '左向平移',
    nameEn: 'Truck Left',
    category: 'spatial_movement',
    keywords: ['truck left', 'sideways movement left', '左侧平移'],
    useCase: '摄影机向左平行移动，展示横向空间',
    tips: ['保持主体大小不变，背景移动营造速度感'],
    examples: [],
    suitableEmotions: ['dynamic'],
    recommendedSpeed: 'medium',
    icon: 'MoveHorizontal',
  },
  {
    id: 'tracking',
    name: '跟轨',
    nameEn: 'Track / Tracking',
    category: 'spatial_movement',
    keywords: ['tracking shot', 'track move', '跟轨移动', '路径跟随移动'],
    useCase: '摄影机沿人物或车辆的路径跟随移动，机位高度变化，适合行走、奔跑、穿越场景',
    tips: [
      '路径和节奏要跟上主体',
      '跟轨是沿路径移动，不是环绕',
    ],
    examples: [
      '摄影机沿人物行走的路径同步前进，保持主体在画面中，背景不断变化',
    ],
    suitableEmotions: ['immersive', 'dynamic'],
    recommendedSpeed: 'medium',
    icon: 'Route',
    isHighFrequency: true,
  },
  {
    id: 'pedestal_up',
    name: '垂直升降（升）',
    nameEn: 'Pedestal Up',
    category: 'spatial_movement',
    keywords: ['pedestal up', 'vertical rise', '垂直上升', '机位升高'],
    useCase: '摄影机整体向上或向下移动，机位高度变化，展示身高差、空间层次、从低到高揭示',
    tips: [
      '它是机位升降，不是镜头抬头低头（不是Tilt）',
      '机位高低变化，不是镜头指向变化',
    ],
    examples: [
      '摄影机从低位缓慢垂直上升，逐渐展现更多环境空间',
    ],
    suitableEmotions: ['grand'],
    recommendedSpeed: 'slow',
    icon: 'ArrowUp',
    isHighFrequency: true,
  },
  {
    id: 'pedestal_down',
    name: '垂直升降（降）',
    nameEn: 'Pedestal Down',
    category: 'spatial_movement',
    keywords: ['pedestal down', 'vertical drop', '垂直下降', '机位降低'],
    useCase: '摄影机整体向下移动，从高到低揭示细节',
    tips: ['它是机位升降，不是俯仰Tilt'],
    examples: [],
    suitableEmotions: ['mysterious'],
    recommendedSpeed: 'slow',
    icon: 'ArrowDown',
  },
  {
    id: 'crane_jib',
    name: '大幅升降',
    nameEn: 'Crane / Jib',
    category: 'spatial_movement',
    keywords: ['crane shot', 'jib shot', '摇臂升降', '大升降镜头'],
    useCase: '借助长臂或升降结构做更大范围的升降与揭示，适合开场气势、从局部到全景、越过前景揭示空间',
    tips: [
      '常用于空间揭示，不宜乱用',
      '大范围升降，适合开场或转场',
    ],
    examples: [
      '开场气势，从局部特写通过摇臂大幅上升，展开整个场景的全景',
    ],
    suitableEmotions: ['grand', 'shocking'],
    recommendedSpeed: 'slow',
    icon: 'ArrowUpDown',
  },
  {
    id: 'orbit',
    name: '环绕',
    nameEn: 'Orbit / Orbit around',
    category: 'spatial_movement',
    keywords: ['orbit shot', 'orbit around subject', '环绕镜头', '围绕主体旋转'],
    useCase: '摄影机围绕主体移动，形成包围圈，展示立体感和多面角度，制造悬念或仪式感',
    tips: [
      '主体要明确，运动路径要清楚',
      '环绕是围绕主体，不是平移Truck',
    ],
    examples: [
      '镜头围绕产品缓慢环绕360度，多维度展示产品外观和细节',
    ],
    suitableEmotions: ['grand', 'delicate'],
    recommendedSpeed: 'very_slow',
    icon: 'Orbit',
    isHighFrequency: true,
  },

  // ── C. 人物跟随类（6个）──
  {
    id: 'follow_shot',
    name: '跟拍',
    nameEn: 'Follow shot',
    category: 'character_follow',
    keywords: ['follow shot', 'following shot', '跟随拍摄', '跟拍镜头'],
    useCase: '镜头跟随人物一起移动，保持主体在画面内，强化主体、营造代入感，适合走路、奔跑、进入场景',
    tips: [
      '跟拍节奏要贴合人物',
      '靠近拉远关系：靠近拉近关系，远离开关系',
    ],
    examples: [
      '镜头从身后跟拍人物走进走廊，保持人物在画面中央，营造跟随探索感',
    ],
    suitableEmotions: ['immersive', 'dynamic'],
    recommendedSpeed: 'medium',
    icon: 'User',
    isHighFrequency: true,
  },
  {
    id: 'chase_shot',
    name: '追拍',
    nameEn: 'Chase shot',
    category: 'character_follow',
    keywords: ['chase shot', 'chase camera', '追逐镜头', '追拍'],
    useCase: '镜头从后方或侧后方追随主体，速度略增，适合运动、逃跑、追逐',
    tips: ['速度常拍增快，速度常决定紧张感', '距离别忽远忽近'],
    examples: [
      '镜头从后方快速追随奔跑的人物，营造紧张的追逐感',
    ],
    suitableEmotions: ['tense', 'dynamic'],
    recommendedSpeed: 'fast',
    icon: 'Zap',
  },
  {
    id: 'lead_shot',
    name: '前导跟拍',
    nameEn: 'Lead shot',
    category: 'character_follow',
    keywords: ['lead shot', 'leading camera', '前导镜头', '前方跟拍'],
    useCase: '镜头在人物前方移动，边退边拍主体，人物出场、边走边说',
    tips: ['保持主体稳定居中', '适合人物面向镜头说话的场景'],
    examples: [
      '镜头在人物前方后退移动，人物面向镜头边走边说，充满互动感',
    ],
    suitableEmotions: ['immersive', 'warm'],
    recommendedSpeed: 'medium',
    icon: 'ArrowLeft',
  },
  {
    id: 'side_follow',
    name: '侧跟',
    nameEn: 'Side follow',
    category: 'character_follow',
    keywords: ['side follow', 'side tracking', '侧面跟拍', '平行跟随'],
    useCase: '镜头与人物大致平行移动，表现动作状态，适合步行、骑行、跑步',
    tips: ['背景移动方向要明确', '保持与主体的距离一致'],
    examples: [
      '镜头从人物侧面平行跟随，展现跑步的动态和背景流动感',
    ],
    suitableEmotions: ['dynamic', 'documentary'],
    recommendedSpeed: 'medium',
    icon: 'MoveRight',
    isHighFrequency: true,
  },
  {
    id: 'over_shoulder_follow',
    name: '肩后跟随',
    nameEn: 'Over-shoulder follow',
    category: 'character_follow',
    keywords: ['over-the-shoulder follow', 'over shoulder tracking', '肩后跟随', '过肩跟拍'],
    useCase: '从角色肩后或背后跟随，带入主观感，进入新空间、观察前方目标',
    tips: ['前景肩部不能挡太多', '适度露出前景增加代入感'],
    examples: [
      '从人物肩后视角跟随其进入房间，观察前方环境，充满探索感',
    ],
    suitableEmotions: ['immersive', 'mysterious'],
    recommendedSpeed: 'slow',
    icon: 'UserCheck',
  },
  {
    id: 'pov_move',
    name: '主观镜头',
    nameEn: 'POV move',
    category: 'character_follow',
    keywords: ['POV shot', 'first-person view move', '主观视角移动', '第一人称视角'],
    useCase: '用主观视角移动，模拟角色看到的路线，探索、寻找、沉浸式视角',
    tips: ['移动过快会眩晕', '越贴近角色感受，越容易沉浸'],
    examples: [
      '第一人称视角，模拟人物在走廊中行走探索的所见所感',
    ],
    suitableEmotions: ['immersive', 'mysterious'],
    recommendedSpeed: 'medium',
    icon: 'Eye',
    isHighFrequency: true,
  },

  // ── D. 升降环绕类（6个）──
  {
    id: 'rising_shot',
    name: '上升',
    nameEn: 'Rising shot',
    category: 'crane_orbit',
    keywords: ['rising shot', 'camera rises', '镜头上升', '上升镜头'],
    useCase: '镜头从低向上升起，展示高度、揭示更广阔空间',
    tips: ['上升速度要平稳', '适合展示宏大场景'],
    examples: [
      '镜头从地面缓缓上升，逐渐展现城市天际线的全貌',
    ],
    suitableEmotions: ['grand', 'shocking'],
    recommendedSpeed: 'slow',
    icon: 'ArrowUp',
  },
  {
    id: 'descending_shot',
    name: '下降',
    nameEn: 'Descending shot',
    category: 'crane_orbit',
    keywords: ['descending shot', 'camera descends', '镜头下降', '下降镜头'],
    useCase: '镜头从高向下降落，从全局落到具体人物或物体上',
    tips: ['下降过程要稳', '从全局到局部的聚焦'],
    examples: [
      '镜头从高空缓缓下降，最终聚焦在地面站立的人物身上',
    ],
    suitableEmotions: ['mysterious'],
    recommendedSpeed: 'slow',
    icon: 'ArrowDown',
  },
  {
    id: 'rise_reveal',
    name: '抬升揭示',
    nameEn: 'Rise reveal',
    category: 'crane_orbit',
    keywords: ['rise reveal', 'rising reveal', '抬升揭示', '升起揭示'],
    useCase: '镜头抬升的同时揭示被遮挡的事物，制造悬念后揭示答案',
    tips: ['先藏后露才有效', '前景遮挡物要自然'],
    examples: [
      '镜头从遮挡物后缓缓升起，揭示出远方壮丽的景色',
    ],
    suitableEmotions: ['shocking', 'mysterious'],
    recommendedSpeed: 'slow',
    icon: 'Eye',
  },
  {
    id: 'dive_down',
    name: '俯冲',
    nameEn: 'Dive down',
    category: 'crane_orbit',
    keywords: ['dive down', 'diving shot', '俯冲镜头', '向下俯冲'],
    useCase: '镜头从高处快速向下俯冲，制造冲击感、进入场景',
    tips: ['速度控制好，太快会晕眩', '适合强冲击力的开场'],
    examples: [
      '镜头从高空快速俯冲而下，直接进入场景中心，充满冲击力',
    ],
    suitableEmotions: ['shocking', 'dynamic'],
    recommendedSpeed: 'fast',
    icon: 'ArrowDown',
  },
  {
    id: 'arc_orbit',
    name: '环绕（弧形）',
    nameEn: 'Arc / Orbit',
    category: 'crane_orbit',
    keywords: ['arc shot', 'arc orbit', '弧形环绕', '弧线运动'],
    useCase: '镜头沿弧线围绕主体移动，突出主体、增强立体感',
    tips: ['主体要明确', '运勔路径保持平滑弧线'],
    examples: [
      '镜头以人物为中心做弧形环绕，展示人物与环境的关系',
    ],
    suitableEmotions: ['grand', 'delicate'],
    recommendedSpeed: 'slow',
    icon: 'Orbit',
  },
  {
    id: 'top_down',
    name: '顶部俯拍',
    nameEn: 'Top-down',
    category: 'crane_orbit',
    keywords: ['top-down shot', 'bird eye view', '上帝视角', '顶部俯拍'],
    useCase: '从正上方向下拍摄，展示全局布局、对称美感',
    tips: ['正上方视角，构图对称效果好', '适合展示平面布局'],
    examples: [
      '顶部俯拍视角，展示整个房间的布局和人物位置关系',
    ],
    suitableEmotions: ['grand', 'calm'],
    recommendedSpeed: 'very_slow',
    icon: 'MonitorDot',
  },

  // ── E. 情绪强化类（6个）──
  {
    id: 'dutch_angle',
    name: '倾斜镜头',
    nameEn: 'Dutch angle',
    category: 'emotion_intensify',
    keywords: ['dutch angle', 'tilted camera', '荷兰角', '倾斜镜头'],
    useCase: '画面倾斜，打破稳定感，危险、不安、失衡',
    tips: ['不要全片滥用', '用于特定情绪场景效果更佳'],
    examples: [
      '画面倾斜构图，人物走在昏暗的走廊中，营造不安和紧张的氛围',
    ],
    suitableEmotions: ['tense', 'mysterious'],
    recommendedSpeed: 'medium',
    icon: 'TrendingUp',
  },
  {
    id: 'whip_pan',
    name: '快速摇镜',
    nameEn: 'Whip pan',
    category: 'emotion_intensify',
    keywords: ['whip pan', 'swish pan', '快速摇镜', '甩镜'],
    useCase: '快速摇动镜头形成动势或转接，紧张切换、突发反应',
    tips: ['太快会看不清', '适合转场或强调突然性'],
    examples: [
      '镜头快速从左甩向右，人物突然转头看向声音来源，充满爆发力',
    ],
    suitableEmotions: ['shocking', 'tense', 'dynamic'],
    recommendedSpeed: 'very_fast',
    icon: 'Zap',
  },
  {
    id: 'slow_push',
    name: '慢推',
    nameEn: 'Slow push',
    category: 'emotion_intensify',
    keywords: ['slow push in', 'gentle push', '缓慢推进', '慢推镜头'],
    useCase: '镜头缓慢向主体推进，情绪逐渐集中，独白、情绪酝酿',
    tips: ['速度要稳，不能看出明显跳动', '情绪渐进式增强'],
    examples: [
      '镜头缓慢推向人物面部，从中景到近景，突出人物内心的情绪起伏',
    ],
    suitableEmotions: ['delicate', 'tense', 'warm'],
    recommendedSpeed: 'very_slow',
    icon: 'ArrowRight',
    isHighFrequency: true,
  },
  {
    id: 'handheld',
    name: '手持镜头',
    nameEn: 'Handheld',
    category: 'emotion_intensify',
    keywords: ['handheld camera', 'slight shake', '轻微晃动', '手持摄影'],
    useCase: '带一点晃动感，模拟现场感，纪实、混乱、追踪',
    tips: [
      '晃动感不能失控',
      '适度的晃动增加真实感，过度会眩晕',
    ],
    examples: [
      '手持跟拍感，轻微晃动，人物穿梭在拥挤的街道中，充满真实临场感',
    ],
    suitableEmotions: ['documentary', 'tense', 'immersive'],
    recommendedSpeed: 'medium',
    icon: 'Film',
    isHighFrequency: true,
  },
  {
    id: 'crash_zoom',
    name: '冲击变焦',
    nameEn: 'Crash zoom',
    category: 'emotion_intensify',
    keywords: ['crash zoom', 'crash zoom effect', '冲击变焦', '突发变焦'],
    useCase: '快速变焦到主体，形成突然强调，惊讶、发现重点',
    tips: ['只在强情绪时用', '用于强调重要发现或转折'],
    examples: [
      '镜头突然快速变焦推近人物面部，强调惊讶的表情和瞬间的冲击感',
    ],
    suitableEmotions: ['shocking', 'tense'],
    recommendedSpeed: 'very_fast',
    icon: 'Maximize2',
  },
  {
    id: 'close_up_push',
    name: '近景逼近',
    nameEn: 'Close-up push',
    category: 'emotion_intensify',
    keywords: ['close-up push in', 'close up push', '近景推近', '逼近特写'],
    useCase: '在近景或特写中继续逼近面部或细节，压迫感、情绪爆点、细节强调',
    tips: ['主体要清晰，别裁得太怪', '用于情绪最高点'],
    examples: [
      '近景继续向人物眼部推近，最终定格在眼神的特写上，压迫感十足',
    ],
    suitableEmotions: ['tense', 'delicate', 'shocking'],
    recommendedSpeed: 'slow',
    icon: 'Search',
  },

  // ── F. 转场衔接类（6个）──
  {
    id: 'reveal',
    name: '揭示',
    nameEn: 'Reveal',
    category: 'transition',
    keywords: ['reveal shot', 'reveal transition', '揭示转场', '遮罩揭示'],
    useCase: '通过移动或遮挡逐渐露出主体或关键信息，人物出场、场景揭晓',
    tips: ['先藏后露才有效', '遮挡物要自然合理'],
    examples: [
      '用前景树叶擦过完成转场，后镜头揭示远处的建筑，节奏自然衔接',
    ],
    suitableEmotions: ['mysterious', 'shocking'],
    recommendedSpeed: 'medium',
    icon: 'Eye',
  },
  {
    id: 'foreground_wipe',
    name: '前景擦过',
    nameEn: 'Foreground wipe',
    category: 'transition',
    keywords: ['foreground wipe', 'wipe transition', '前景转场', '遮挡转场'],
    useCase: '利用前景物体从镜头前划过完成遮挡转接，场景切换、节奏连接',
    tips: ['前景要自然', '物体划过的方向要统一'],
    examples: [
      '人物从镜头前走过，利用身体遮挡完成场景切换，流畅自然',
    ],
    suitableEmotions: ['dynamic'],
    recommendedSpeed: 'medium',
    icon: 'ArrowRightLeft',
  },
  {
    id: 'rack_focus',
    name: '焦点切换',
    nameEn: 'Rack focus',
    category: 'transition',
    keywords: ['rack focus', 'focus pull', '焦点转移', '焦距切换'],
    useCase: '在前景和背景之间切换焦点，引导注意力，关系变化、信息转移',
    tips: ['焦点对象要明确', '虚化过渡要自然'],
    examples: [
      '焦点从前景的物品缓慢转移到背景的人物身上，引导观众视线转移',
    ],
    suitableEmotions: ['delicate', 'mysterious'],
    recommendedSpeed: 'slow',
    icon: 'Focus',
  },
  {
    id: 'parallax',
    name: '视差',
    nameEn: 'Parallax',
    category: 'transition',
    keywords: ['parallax effect', 'parallax move', '视差运动', '视差转场'],
    useCase: '通过前后中景的相对运动制造层次和转场感，空间展示、氛围转接',
    tips: ['层次至少要有两层以上', '各层运动速度要有差异'],
    examples: [
      '镜头缓慢推进，前景、中景、背景以不同速度移动，营造丰富的空间层次感',
    ],
    suitableEmotions: ['calm', 'immersive'],
    recommendedSpeed: 'slow',
    icon: 'Layers',
  },
  {
    id: 'match_move',
    name: '动作匹配',
    nameEn: 'Match move',
    category: 'transition',
    keywords: ['match cut', 'match move', '动作匹配', '相似动作转场'],
    useCase: '利用相似动作或运动方向连接前后镜头，动作衔接、节奏流畅',
    tips: ['动作方向要统一', '前后镜头的运动趋势要匹配'],
    examples: [
      '人物开门的动作与下个镜头推镜头的方向匹配，流畅衔接两个场景',
    ],
    suitableEmotions: ['dynamic'],
    recommendedSpeed: 'medium',
    icon: 'ArrowRight',
  },
  {
    id: 'speed_ramp',
    name: '速度变化',
    nameEn: 'Speed ramp',
    category: 'transition',
    keywords: ['speed ramp', 'speed change', '速度曲线', '变速转场'],
    useCase: '在同一镜头或衔接点调整速度，强化节奏、打点、强调',
    tips: ['不要过度炫技', '速度变化服务于节奏和情绪'],
    examples: [
      '人物动作在关键时刻从正常速度突然变慢，强化动作的力量感和视觉冲击',
    ],
    suitableEmotions: ['dynamic', 'shocking'],
    recommendedSpeed: 'medium',
    icon: 'Gauge',
  },
]

export const cameraAngles: CameraAngleOption[] = [
  {
    id: 'eye_level',
    name: '平视',
    nameEn: 'Eye Level',
    keywords: ['eye level', '平视视角', '水平视角'],
    useCase: '自然、客观的视角，适合大多数场景',
    icon: 'Eye',
  },
  {
    id: 'low_angle',
    name: '仰拍',
    nameEn: 'Low Angle',
    keywords: ['low angle shot', 'looking up', '仰视视角', '低角度'],
    useCase: '塑造权威、宏伟感，用于企业领袖或产品',
    icon: 'ArrowUp',
  },
  {
    id: 'high_angle',
    name: '俯拍',
    nameEn: 'High Angle',
    keywords: ['high angle shot', 'overhead view', '俯视', '高角度'],
    useCase: '表现渺小、脆弱感，或展示全局布局',
    icon: 'ArrowDown',
  },
  {
    id: 'dutch_angle',
    name: '荷兰角',
    nameEn: 'Dutch Angle',
    keywords: ['dutch angle', 'tilted angle', '倾斜角度', '斜角镜头'],
    useCase: '制造不安、紧张感，用于特殊情绪表达',
    icon: 'ArrowUpRight',
  },
  {
    id: 'pov',
    name: '第一人称视角',
    nameEn: 'POV',
    keywords: ['first-person view', 'POV', '主观视角', '第一人称'],
    useCase: '增强代入感，产品体验模拟',
    icon: 'Eye',
  },
  {
    id: 'over_shoulder',
    name: '过肩镜头',
    nameEn: 'Over the Shoulder',
    keywords: ['over the shoulder', 'peeking through', '过肩视角'],
    useCase: '营造神秘、好奇感，对话场景',
    icon: 'MessageSquare',
  },
]

export const movementSpeeds = [
  { value: 'very_slow', label: '极慢', description: '极其缓慢，适合仪式感、强调' },
  { value: 'slow', label: '慢', description: '舒缓节奏，适合情绪铺垫' },
  { value: 'medium', label: '中等', description: '自然节奏，大多数场景适用' },
  { value: 'fast', label: '快', description: '动感节奏，适合动作场景' },
  { value: 'very_fast', label: '极快', description: '爆发力，适合冲击和转场' },
] as const

export const emotionTags = [
  { value: 'calm', label: '平静/舒缓', icon: 'Waves' },
  { value: 'tense', label: '紧张/压迫', icon: 'AlertTriangle' },
  { value: 'warm', label: '温馨/治愈', icon: 'Heart' },
  { value: 'shocking', label: '震撼/冲击', icon: 'Zap' },
  { value: 'grand', label: '宏大/气势', icon: 'Mountain' },
  { value: 'mysterious', label: '神秘/悬念', icon: 'HelpCircle' },
  { value: 'immersive', label: '沉浸/代入', icon: 'Eye' },
  { value: 'documentary', label: '真实/纪实', icon: 'Film' },
  { value: 'dynamic', label: '动感/活力', icon: 'Activity' },
  { value: 'delicate', label: '细腻/精致', icon: 'Sparkles' },
] as const

export const shotCombinations: ShotCombination[] = [
  {
    id: 'product_showcase',
    name: '产品展示组合',
    description: '低角度仰拍 → 缓慢推近 → 环绕展示细节，突出产品高端感',
    icon: '📦',
    shots: [
      { type: 'full', movement: 'static', duration: 2 },
      { type: 'close_up', movement: 'slow_push', duration: 3 },
      { type: 'extreme_close_up', movement: 'orbit', duration: 3 },
    ],
    suitableFor: ['电商产品', '科技产品', '高端商品'],
    prompt: 'low angle shot of product, slow dolly in to detail, orbit around product, cinematic product lighting, 4K quality',
  },
  {
    id: 'brand_story',
    name: '品牌故事组合',
    description: '大升降开场 → 中景跟拍团队 → 特写面部表情，传递品牌温度',
    icon: '🏢',
    shots: [
      { type: 'extreme_long', movement: 'crane_jib', duration: 3 },
      { type: 'medium', movement: 'follow_shot', duration: 4 },
      { type: 'close_up', movement: 'static', duration: 3 },
    ],
    suitableFor: ['企业宣传', '品牌故事', '团队展示'],
    prompt: 'crane up revealing office building, medium tracking shot of team working, close-up of smiling face, warm professional atmosphere, cinematic color grading',
  },
  {
    id: 'emotional_dramatic',
    name: '情感戏剧组合',
    description: '特写表情 → 缓慢拉远 → 环境全景，营造情绪张力',
    icon: '🎭',
    shots: [
      { type: 'extreme_close_up', movement: 'static', duration: 2 },
      { type: 'close_up', movement: 'dolly_out', duration: 3 },
      { type: 'full', movement: 'static', duration: 3 },
    ],
    suitableFor: ['人物情感', '戏剧场景', '情绪表达'],
    prompt: 'extreme close-up of eyes, slow dolly out revealing face, full shot of person in environment, emotional atmosphere, soft cinematic lighting',
  },
  {
    id: 'action_dynamic',
    name: '动态动作组合',
    description: '全景展示 → 跟随运动 → 特写细节，充满动感能量',
    icon: '⚡',
    shots: [
      { type: 'full', movement: 'static', duration: 2 },
      { type: 'medium', movement: 'side_follow', duration: 4 },
      { type: 'close_up', movement: 'dolly_in', duration: 2 },
    ],
    suitableFor: ['运动场景', '产品使用', '动态展示'],
    prompt: 'full shot of action scene, side tracking shot following movement, close-up dolly in to detail, dynamic energy, high contrast lighting',
  },
  {
    id: 'documentary',
    name: '纪录片风格',
    description: '手持跟拍 → 自然光线 → 真实记录感，质朴真诚',
    icon: '🎬',
    shots: [
      { type: 'medium', movement: 'handheld', duration: 3 },
      { type: 'close_up', movement: 'handheld', duration: 3 },
      { type: 'full', movement: 'handheld', duration: 2 },
    ],
    suitableFor: ['纪录片', '真实记录', '工艺展示'],
    prompt: 'handheld documentary style, medium shot of craft process, close-up of hands working, natural lighting, authentic and realistic feel',
  },
  {
    id: 'epic_cinematic',
    name: '电影级史诗组合',
    description: '航拍大景 → 轨道推进 → 低角度英雄镜头，震撼大气',
    icon: '🎥',
    shots: [
      { type: 'extreme_long', movement: 'aerial_drone', duration: 3 },
      { type: 'full', movement: 'tracking_shot', duration: 3 },
      { type: 'medium', movement: 'low_angle', duration: 2 },
    ],
    suitableFor: ['宏大场景', '英雄时刻', '电影感'],
    prompt: 'aerial wide shot of epic landscape, low tracking shot moving forward, low angle hero shot, cinematic lighting, epic atmosphere',
  },
  {
    id: 'social_media_reel',
    name: '社媒短视频',
    description: '开场钩子 → 快速转场 → 产品特写，适合15秒短视频',
    icon: '📱',
    shots: [
      { type: 'close_up', movement: 'zoom_in_fast', duration: 1 },
      { type: 'medium', movement: 'pan_horizontal', duration: 2 },
      { type: 'close_up', movement: 'slow_push', duration: 3 },
    ],
    suitableFor: ['抖音', '小红书', '短视频'],
    prompt: 'fast zoom in hook shot, quick pan horizontal, slow push in to product detail, snappy pacing, vibrant colors, vertical format',
  },
  {
    id: 'food_showcase',
    name: '美食展示组合',
    description: '俯拍摆盘 → 蒸汽慢推 → 特写拉丝，展现诱人质感',
    icon: '🍜',
    shots: [
      { type: 'full', movement: 'top_down', duration: 2 },
      { type: 'medium', movement: 'slow_push', duration: 3 },
      { type: 'extreme_close_up', movement: 'static', duration: 2 },
    ],
    suitableFor: ['美食', '餐饮', '料理展示'],
    prompt: 'top down flat lay of food dish, slow push in with steam rising, extreme close-up of texture, warm lighting, appetizing presentation',
  },
  {
    id: 'fashion_walk',
    name: '时尚街拍',
    description: '全景入场 → 中景跟拍 → 细节特写，展现穿搭品味',
    icon: '👗',
    shots: [
      { type: 'full', movement: 'slow_push', duration: 2 },
      { type: 'medium', movement: 'follow_shot', duration: 3 },
      { type: 'close_up', movement: 'static', duration: 2 },
    ],
    suitableFor: ['时尚穿搭', '街拍', '服饰展示'],
    prompt: 'full body slow push in fashion walk, medium tracking shot from side, close-up of outfit details, stylish urban background, natural lighting',
  },
  {
    id: 'real_estate_tour',
    name: '房产空间漫游',
    description: '大门推入 → 空间扫视 → 细节特写，沉浸式看房',
    icon: '🏠',
    shots: [
      { type: 'full', movement: 'slow_push', duration: 3 },
      { type: 'medium', movement: 'pan_horizontal', duration: 4 },
      { type: 'close_up', movement: 'dolly_in', duration: 2 },
    ],
    suitableFor: ['房产展示', '空间设计', '室内装修'],
    prompt: 'slow push through doorway into room, slow pan across interior space, dolly in to design detail, bright natural lighting, clean modern aesthetic',
  },
  {
    id: 'education_explainer',
    name: '知识讲解',
    description: '主讲人中景 → 细节特写 → 全景总结，清晰传递信息',
    icon: '📚',
    shots: [
      { type: 'medium', movement: 'static', duration: 3 },
      { type: 'close_up', movement: 'dolly_in', duration: 2 },
      { type: 'full', movement: 'static', duration: 2 },
    ],
    suitableFor: ['知识付费', '在线教育', '产品讲解'],
    prompt: 'medium shot of speaker, close-up dolly in to hands demonstrating, full shot of complete setup, professional lighting, clear and engaging',
  },
  {
    id: 'vlog_intro',
    name: 'Vlog开场',
    description: '自拍开场 → 环境环视 → 主题引入，轻松有代入感',
    icon: '🎒',
    shots: [
      { type: 'close_up', movement: 'handheld', duration: 2 },
      { type: 'full', movement: 'pan_horizontal', duration: 3 },
      { type: 'medium', movement: 'follow_shot', duration: 3 },
    ],
    suitableFor: ['Vlog', '旅行记录', '日常分享'],
    prompt: 'handheld selfie vlog intro, slow pan revealing surroundings, follow shot walking forward, casual and energetic, natural sunlight',
  },
]

export function getShotTypeById(id: ShotType): ShotTypeOption | undefined {
  return shotTypes.find((s) => s.id === id)
}

export function getCameraMovementById(
  id: CameraMovement,
): CameraMovementOption | undefined {
  return cameraMovements.find((m) => m.id === id)
}

export function getCameraAngleById(id: CameraAngle): CameraAngleOption | undefined {
  return cameraAngles.find((a) => a.id === id)
}

export function getMovementSpeedById(id: MovementSpeed): { value: string; label: string; description: string } | undefined {
  return movementSpeeds.find((s) => s.value === id)
}

export function getMovementsByCategory(
  category: CameraMovementCategory,
): CameraMovementOption[] {
  return cameraMovements.filter((m) => m.category === category)
}

export function getHighFrequencyMovements(): CameraMovementOption[] {
  return cameraMovements.filter((m) => m.isHighFrequency)
}

export function getMovementsByEmotion(
  emotion: EmotionTag,
): CameraMovementOption[] {
  return cameraMovements.filter((m) => m.suitableEmotions.includes(emotion))
}

export function getCategoryMeta(
  categoryId: CameraMovementCategory,
): MovementCategoryMeta | undefined {
  return movementCategories.find((c) => c.id === categoryId)
}

export interface ShotPromptParams {
  basePrompt: string
  shotType?: ShotType
  movement?: CameraMovement
  angle?: CameraAngle
  speed?: MovementSpeed
  emotion?: EmotionTag
  subject?: string
  direction?: string
}

export function generatePromptWithShot(params: ShotPromptParams): string {
  const { basePrompt, shotType, movement, angle, speed, emotion, subject, direction } =
    params

  const parts: string[] = [basePrompt]

  if (subject) {
    parts.unshift(subject)
  }

  if (movement && movement !== 'static') {
    const move = getCameraMovementById(movement)
    if (move && move.keywords[0]) {
      let movementDesc = move.keywords[0]

      if (speed) {
        const speedMap: Record<MovementSpeed, string> = {
          very_slow: 'very slow speed',
          slow: 'slow speed',
          medium: 'medium speed',
          fast: 'fast speed',
          very_fast: 'very fast speed',
        }
        movementDesc = `${movementDesc}, ${speedMap[speed]}`
      }

      if (direction) {
        movementDesc = `${movementDesc}, ${direction}`
      }

      parts.push(movementDesc)
    }
  }

  if (shotType) {
    const shot = getShotTypeById(shotType)
    if (shot && shot.keywords[0]) {
      parts.push(shot.keywords[0])
    }
  }

  if (angle && angle !== 'eye_level') {
    const ang = getCameraAngleById(angle)
    if (ang && ang.keywords[0]) {
      parts.push(ang.keywords[0])
    }
  }

  if (emotion) {
    const emotionMap: Record<EmotionTag, string> = {
      calm: 'calm and peaceful atmosphere',
      tense: 'tense and suspenseful mood',
      warm: 'warm and cozy feeling',
      shocking: 'dramatic and impactful',
      grand: 'grand and epic scale',
      mysterious: 'mysterious and intriguing',
      immersive: 'immersive and engaging',
      documentary: 'documentary realism style',
      dynamic: 'dynamic and energetic',
      delicate: 'delicate and exquisite',
    }
    parts.push(emotionMap[emotion])
  }

  return parts.join(', ')
}

export function getPromptQualityCheck(prompt: string): {
  missing: string[]
  suggestions: string[]
} {
  const missing: string[] = []
  const suggestions: string[] = []

  const lower = prompt.toLowerCase()

  const hasMovement = /(dolly|pan|tilt|zoom|track|orbit|follow|push|pull|move|camera)/i.test(
    prompt,
  )
  if (!hasMovement) {
    missing.push('运镜描述')
    suggestions.push('建议添加运镜描述，例如 slow push in（缓慢推进）或 orbit（环绕）')
  }

  const hasShot = /(shot|close.?up|medium|full|wide|long\s*shot|特写|近景|中景|全景|远景)/i.test(
    prompt,
  )
  if (!hasShot) {
    missing.push('景别描述')
    suggestions.push('建议添加景别，例如 close-up（近景）或 medium shot（中景）')
  }

  const hasSpeed = /(slow|fast|speed|gradual|slowly|quickly|缓慢|快速|速度)/i.test(prompt)
  if (hasMovement && !hasSpeed) {
    missing.push('运镜速度')
    suggestions.push('建议添加运镜速度，例如 slowly（缓慢）或 fast（快速）')
  }

  const hasSubjectDetail = lower.length > 30
  if (!hasSubjectDetail) {
    suggestions.push('提示词描述较短，建议补充更多主体和环境细节')
  }

  return { missing, suggestions }
}

export const videoStyles = [
  { value: 'cinematic', label: '电影感', description: '电影级画面质感' },
  { value: 'commercial', label: '商业广告', description: '专业商业广告风格' },
  { value: 'documentary', label: '纪录片', description: '真实记录风格' },
  { value: 'anime', label: '动漫风格', description: '二次元动画风格' },
  { value: '3d_render', label: '3D渲染', description: '三维渲染效果' },
  { value: 'vintage', label: '复古风格', description: '怀旧复古效果' },
]

export const videoResolutions = [
  { value: '720p', label: '720p', description: '1280x720，适合测试预览' },
  { value: '1080p', label: '1080p (推荐)', description: '1920x1080，平衡质量与成本' },
  { value: '4k', label: '4K', description: '3840x2160，高质量输出' },
]

export const videoDurations = [
  { value: 3, label: '3秒', description: '快速展示' },
  { value: 5, label: '5秒 (推荐)', description: '标准短视频' },
  { value: 10, label: '10秒', description: '详细展示' },
  { value: 15, label: '15秒', description: '完整叙事' },
]
