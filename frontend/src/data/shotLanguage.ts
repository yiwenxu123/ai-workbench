/**
 * 镜头语言知识库
 * 包含景别、运镜、视角等专业术语
 */

export type ShotType = 'extreme_long' | 'full' | 'medium' | 'close_up' | 'extreme_close_up'
export type CameraMovement = 'dolly_in' | 'dolly_out' | 'pan_left' | 'pan_right' | 'truck_left' | 'truck_right' | 'tracking' | 'crane_up' | 'crane_down' | 'static' | 'handheld' | 'dolly_zoom'
export type CameraAngle = 'eye_level' | 'low_angle' | 'high_angle' | 'dutch_angle' | 'pov' | 'over_shoulder'

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
  keywords: string[]
  useCase: string
  icon: string
}

export interface CameraAngleOption {
  id: CameraAngle
  name: string
  nameEn: string
  keywords: string[]
  useCase: string
  icon: string
}

export interface ShotCombination {
  id: string
  name: string
  description: string
  shots: {
    type: ShotType
    movement: CameraMovement
    duration: number
  }[]
  suitableFor: string[]
}

export const shotTypes: ShotTypeOption[] = [
  {
    id: 'extreme_long',
    name: '远景',
    nameEn: 'Extreme Long Shot',
    keywords: ['extreme long shot', 'wide establishing shot', '全景远景', '大远景'],
    useCase: '开场定调、展示宏大环境、企业总部外景',
    icon: 'Mountain'
  },
  {
    id: 'full',
    name: '全景',
    nameEn: 'Full Shot',
    keywords: ['full body shot', 'full shot', '人物全身', '产品完整展示'],
    useCase: '展示人物全身与环境关系、产品全貌',
    icon: 'User'
  },
  {
    id: 'medium',
    name: '中景',
    nameEn: 'Medium Shot',
    keywords: ['medium shot', 'waist-up', '腰部以上', '中景镜头'],
    useCase: '人物对话、产品细节展示、操作演示',
    icon: 'User'
  },
  {
    id: 'close_up',
    name: '近景',
    nameEn: 'Close-Up',
    keywords: ['close-up', 'close up', '面部特写', '产品特写镜头'],
    useCase: '突出情感、产品局部特写、强调细节',
    icon: 'Search'
  },
  {
    id: 'extreme_close_up',
    name: '特写',
    nameEn: 'Extreme Close-Up',
    keywords: ['extreme close-up', 'extreme close up', '眼部特写', '微观细节'],
    useCase: '极致细节、情绪张力、logo/标识展示',
    icon: 'Eye'
  }
]

export const cameraMovements: CameraMovementOption[] = [
  {
    id: 'dolly_in',
    name: '推镜头',
    nameEn: 'Dolly In',
    keywords: ['dolly in', 'slow zoom in', '镜头缓慢推进', 'zoom in'],
    useCase: '逐步聚焦主体、引导观众注意力、揭示细节',
    icon: 'ArrowRight'
  },
  {
    id: 'dolly_out',
    name: '拉镜头',
    nameEn: 'Dolly Out',
    keywords: ['dolly out', 'zoom out', '镜头拉远', 'pull back'],
    useCase: '展现环境、结束场景、从细节到全局',
    icon: 'ArrowLeft'
  },
  {
    id: 'pan_left',
    name: '左摇',
    nameEn: 'Pan Left',
    keywords: ['pan left', 'pan left', '向左摇镜', '水平左摇'],
    useCase: '展示横向空间、跟随运动、扫描场景',
    icon: 'ArrowLeft'
  },
  {
    id: 'pan_right',
    name: '右摇',
    nameEn: 'Pan Right',
    keywords: ['pan right', 'pan right', '向右摇镜', '水平右摇'],
    useCase: '展示横向空间、跟随运动、扫描场景',
    icon: 'ArrowRight'
  },
  {
    id: 'truck_left',
    name: '左移',
    nameEn: 'Truck Left',
    keywords: ['truck left', 'sideways movement left', '左侧移动'],
    useCase: '平行移动展示、保持主体大小不变',
    icon: 'ArrowLeft'
  },
  {
    id: 'truck_right',
    name: '右移',
    nameEn: 'Truck Right',
    keywords: ['truck right', 'sideways movement right', '右侧移动'],
    useCase: '平行移动展示、保持主体大小不变',
    icon: 'ArrowRight'
  },
  {
    id: 'tracking',
    name: '跟镜头',
    nameEn: 'Tracking Shot',
    keywords: ['tracking shot', 'follow shot', '跟随镜头', '跟拍'],
    useCase: '跟随主体运动、营造临场感、产品使用跟拍',
    icon: 'User'
  },
  {
    id: 'crane_up',
    name: '升镜头',
    nameEn: 'Crane Up',
    keywords: ['crane up', 'boom up', '升降镜头上升', '升起'],
    useCase: '垂直空间展示、从低到高视角变化',
    icon: 'ArrowUp'
  },
  {
    id: 'crane_down',
    name: '降镜头',
    nameEn: 'Crane Down',
    keywords: ['crane down', 'boom down', '升降镜头下降', '降落'],
    useCase: '垂直空间展示、从高到低视角变化',
    icon: 'ArrowDown'
  },
  {
    id: 'static',
    name: '固定镜头',
    nameEn: 'Static Shot',
    keywords: ['static shot', 'fixed camera', '固定机位', '静止镜头'],
    useCase: '稳定展示、对话场景、产品静态展示',
    icon: 'Camera'
  },
  {
    id: 'handheld',
    name: '手持镜头',
    nameEn: 'Handheld',
    keywords: ['handheld camera', 'slight shake', '轻微晃动', '手持摄影'],
    useCase: '营造真实感、临场感、纪录片风格',
    icon: 'Film'
  },
  {
    id: 'dolly_zoom',
    name: '希区柯克变焦',
    nameEn: 'Dolly Zoom',
    keywords: ['dolly zoom', 'vertigo effect', '滑动变焦', '眩晕效果'],
    useCase: '制造眩晕、紧张感，用于产品悬念或情绪转折',
    icon: 'CircleDot'
  }
]

export const cameraAngles: CameraAngleOption[] = [
  {
    id: 'eye_level',
    name: '平视',
    nameEn: 'Eye Level',
    keywords: ['eye level', '平视视角', '水平视角'],
    useCase: '自然、客观的视角，适合大多数场景',
    icon: 'Eye'
  },
  {
    id: 'low_angle',
    name: '仰拍',
    nameEn: 'Low Angle',
    keywords: ['low angle shot', 'looking up', '仰视视角', '低角度'],
    useCase: '塑造权威、宏伟感，用于企业领袖或产品',
    icon: 'ArrowUp'
  },
  {
    id: 'high_angle',
    name: '俯拍',
    nameEn: 'High Angle',
    keywords: ['high angle shot', 'overhead view', '俯视', '高角度'],
    useCase: '表现渺小、脆弱感，或展示全局布局',
    icon: 'ArrowDown'
  },
  {
    id: 'dutch_angle',
    name: '荷兰角',
    nameEn: 'Dutch Angle',
    keywords: ['dutch angle', 'tilted angle', '倾斜角度', '斜角镜头'],
    useCase: '制造不安、紧张感，用于特殊情绪表达',
    icon: 'ArrowUpRight'
  },
  {
    id: 'pov',
    name: '第一人称视角',
    nameEn: 'POV',
    keywords: ['first-person view', 'POV', '主观视角', '第一人称'],
    useCase: '增强代入感，产品体验模拟',
    icon: 'Eye'
  },
  {
    id: 'over_shoulder',
    name: '过肩镜头',
    nameEn: 'Over the Shoulder',
    keywords: ['over the shoulder', 'peeking through', '过肩视角'],
    useCase: '营造神秘、好奇感，对话场景',
    icon: 'MessageSquare'
  }
]

export const shotCombinations: ShotCombination[] = [
  {
    id: 'product_showcase',
    name: '产品展示组合',
    description: '低角度仰拍 → 缓慢推近 → 环绕展示细节',
    shots: [
      { type: 'full', movement: 'static', duration: 2 },
      { type: 'close_up', movement: 'dolly_in', duration: 3 },
      { type: 'extreme_close_up', movement: 'tracking', duration: 3 }
    ],
    suitableFor: ['电商产品', '科技产品', '高端商品']
  },
  {
    id: 'brand_story',
    name: '品牌故事组合',
    description: '无人机远景进入 → 中景跟拍团队 → 特写面部表情',
    shots: [
      { type: 'extreme_long', movement: 'crane_down', duration: 3 },
      { type: 'medium', movement: 'tracking', duration: 4 },
      { type: 'close_up', movement: 'static', duration: 3 }
    ],
    suitableFor: ['企业宣传', '品牌故事', '团队展示']
  },
  {
    id: 'emotional_dramatic',
    name: '情感戏剧组合',
    description: '特写表情 → 缓慢拉远 → 环境全景',
    shots: [
      { type: 'extreme_close_up', movement: 'static', duration: 2 },
      { type: 'close_up', movement: 'dolly_out', duration: 3 },
      { type: 'full', movement: 'static', duration: 3 }
    ],
    suitableFor: ['人物情感', '戏剧场景', '情绪表达']
  },
  {
    id: 'action_dynamic',
    name: '动态动作组合',
    description: '全景展示 → 跟随运动 → 特写细节',
    shots: [
      { type: 'full', movement: 'static', duration: 2 },
      { type: 'medium', movement: 'tracking', duration: 4 },
      { type: 'close_up', movement: 'dolly_in', duration: 2 }
    ],
    suitableFor: ['运动场景', '产品使用', '动态展示']
  },
  {
    id: 'documentary',
    name: '纪录片风格',
    description: '手持镜头 → 自然光线 → 真实感',
    shots: [
      { type: 'medium', movement: 'handheld', duration: 3 },
      { type: 'close_up', movement: 'handheld', duration: 3 },
      { type: 'full', movement: 'handheld', duration: 2 }
    ],
    suitableFor: ['纪录片', '真实记录', '工艺展示']
  }
]

export function getShotTypeById(id: ShotType): ShotTypeOption | undefined {
  return shotTypes.find(s => s.id === id)
}

export function getCameraMovementById(id: CameraMovement): CameraMovementOption | undefined {
  return cameraMovements.find(m => m.id === id)
}

export function getCameraAngleById(id: CameraAngle): CameraAngleOption | undefined {
  return cameraAngles.find(a => a.id === id)
}

export function generatePromptWithShot(
  basePrompt: string,
  shotType?: ShotType,
  movement?: CameraMovement,
  angle?: CameraAngle
): string {
  const parts: string[] = [basePrompt]
  
  if (shotType) {
    const shot = getShotTypeById(shotType)
    if (shot && shot.keywords[0]) {
      parts.push(shot.keywords[0])
    }
  }
  
  if (movement && movement !== 'static') {
    const move = getCameraMovementById(movement)
    if (move && move.keywords[0]) {
      parts.push(move.keywords[0])
    }
  }
  
  if (angle && angle !== 'eye_level') {
    const ang = getCameraAngleById(angle)
    if (ang && ang.keywords[0]) {
      parts.push(ang.keywords[0])
    }
  }
  
  return parts.join(', ')
}

export const videoStyles = [
  { value: 'cinematic', label: '电影感', description: '电影级画面质感' },
  { value: 'commercial', label: '商业广告', description: '专业商业广告风格' },
  { value: 'documentary', label: '纪录片', description: '真实记录风格' },
  { value: 'anime', label: '动漫风格', description: '二次元动画风格' },
  { value: '3d_render', label: '3D渲染', description: '三维渲染效果' },
  { value: 'vintage', label: '复古风格', description: '怀旧复古效果' }
]

export const videoResolutions = [
  { value: '720p', label: '720p', description: '1280x720，适合测试预览' },
  { value: '1080p', label: '1080p (推荐)', description: '1920x1080，平衡质量与成本' },
  { value: '4k', label: '4K', description: '3840x2160，高质量输出' }
]

export const videoDurations = [
  { value: 3, label: '3秒', description: '快速展示' },
  { value: 5, label: '5秒 (推荐)', description: '标准短视频' },
  { value: 10, label: '10秒', description: '详细展示' },
  { value: 15, label: '15秒', description: '完整叙事' }
]
