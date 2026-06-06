export interface ShotType {
  id: string
  name: string
  nameEn: string
  description: string
  usage: string
  keywords: string[]
  category: 'shot_size' | 'camera_movement' | 'advanced' | 'angle'
  examples: string[]
}

export const shotTypes: ShotType[] = [
  {
    id: 'extreme-long-shot',
    name: '远景',
    nameEn: 'Extreme Long Shot',
    description: '展示宏大环境、开场定调的镜头',
    usage: '适合展示企业总部外景、城市全貌、自然风光',
    keywords: ['extreme long shot', 'wide establishing shot', '全景远景'],
    category: 'shot_size',
    examples: ['extreme long shot of city skyline', 'wide establishing shot of mountain range']
  },
  {
    id: 'full-shot',
    name: '全景',
    nameEn: 'Full Shot',
    description: '展示人物全身与环境关系的镜头',
    usage: '适合展示产品全貌、人物全身、团队合影',
    keywords: ['full body shot', '人物全身', '产品完整展示'],
    category: 'shot_size',
    examples: ['full body shot of model', 'full shot of product display']
  },
  {
    id: 'medium-shot',
    name: '中景',
    nameEn: 'Medium Shot',
    description: '展示人物腰部以上的镜头',
    usage: '适合人物对话、产品细节展示、操作演示',
    keywords: ['medium shot', 'waist-up', '腰部以上'],
    category: 'shot_size',
    examples: ['medium shot of presenter', 'waist-up shot of chef cooking']
  },
  {
    id: 'close-up',
    name: '近景',
    nameEn: 'Close-Up',
    description: '突出情感、产品局部特写的镜头',
    usage: '适合突出情感表达、产品局部特写、强调细节',
    keywords: ['close-up', '面部特写', '产品特写镜头'],
    category: 'shot_size',
    examples: ['close-up of face', 'product detail close-up']
  },
  {
    id: 'extreme-close-up',
    name: '特写',
    nameEn: 'Extreme Close-Up',
    description: '极致细节、情绪张力的镜头',
    usage: '适合展示微观细节、情绪张力、logo/标识展示',
    keywords: ['extreme close-up', '眼部特写', '微观细节'],
    category: 'shot_size',
    examples: ['extreme close-up of eye', 'macro shot of product texture']
  },
  {
    id: 'dolly-in',
    name: '推镜头',
    nameEn: 'Dolly In',
    description: '镜头向主体靠近，逐步聚焦',
    usage: '适合聚焦主体、引导观众注意力、揭示细节',
    keywords: ['dolly in', 'slow zoom in', '镜头缓慢推进'],
    category: 'camera_movement',
    examples: ['slow dolly in to face', 'camera pushes in on product']
  },
  {
    id: 'dolly-out',
    name: '拉镜头',
    nameEn: 'Dolly Out',
    description: '镜头远离主体，展现环境',
    usage: '适合展现环境、结束场景、从细节到全局',
    keywords: ['dolly out', 'zoom out', '镜头拉远'],
    category: 'camera_movement',
    examples: ['dolly out revealing environment', 'zoom out from detail to wide']
  },
  {
    id: 'pan',
    name: '摇镜头',
    nameEn: 'Pan',
    description: '镜头水平转动，展示横向空间',
    usage: '适合展示横向空间、跟随运动、扫描场景',
    keywords: ['pan left', 'pan right', 'horizontal pan', '水平摇镜'],
    category: 'camera_movement',
    examples: ['pan left across landscape', 'horizontal pan following subject']
  },
  {
    id: 'truck',
    name: '移镜头',
    nameEn: 'Truck',
    description: '镜头平行移动，保持主体大小不变',
    usage: '适合平行移动展示、保持主体大小不变',
    keywords: ['truck left', 'truck right', 'sideways movement'],
    category: 'camera_movement',
    examples: ['truck right following walking subject', 'sideways tracking shot']
  },
  {
    id: 'tracking',
    name: '跟镜头',
    nameEn: 'Tracking Shot',
    description: '跟随主体运动的镜头',
    usage: '适合跟随主体运动、营造临场感、产品使用跟拍',
    keywords: ['tracking shot', 'follow shot', '跟随镜头'],
    category: 'camera_movement',
    examples: ['tracking shot following runner', 'follow shot behind car']
  },
  {
    id: 'crane',
    name: '升降镜头',
    nameEn: 'Crane/Boom Shot',
    description: '镜头垂直移动，展示空间高度',
    usage: '适合垂直空间展示、从低到高视角变化',
    keywords: ['crane up', 'crane down', 'boom shot', '升降镜头'],
    category: 'camera_movement',
    examples: ['crane up from ground to rooftop', 'boom shot descending']
  },
  {
    id: 'dolly-zoom',
    name: '希区柯克变焦',
    nameEn: 'Dolly Zoom',
    description: '推拉镜头同时变焦，制造眩晕感',
    usage: '适合制造眩晕、紧张感，用于产品悬念或情绪转折',
    keywords: ['dolly zoom', 'vertigo effect', '滑动变焦'],
    category: 'advanced',
    examples: ['dolly zoom on surprised face', 'vertigo effect reveal']
  },
  {
    id: 'handheld',
    name: '手持镜头',
    nameEn: 'Handheld',
    description: '模拟手持拍摄的轻微晃动',
    usage: '适合营造真实感、临场感，纪录片风格',
    keywords: ['handheld camera', 'slight shake', '轻微晃动'],
    category: 'advanced',
    examples: ['handheld documentary style', 'shaky cam action sequence']
  },
  {
    id: 'low-angle',
    name: '低角度仰拍',
    nameEn: 'Low Angle',
    description: '从低处向上拍摄',
    usage: '适合塑造权威、宏伟感，用于企业领袖或产品',
    keywords: ['low angle shot', 'looking up', '仰视视角'],
    category: 'angle',
    examples: ['low angle hero shot', 'looking up at skyscraper']
  },
  {
    id: 'high-angle',
    name: '高角度俯拍',
    nameEn: 'High Angle',
    description: '从高处向下拍摄',
    usage: '适合表现渺小、脆弱感，或展示全局布局',
    keywords: ['high angle shot', 'overhead view', '俯视'],
    category: 'angle',
    examples: ['high angle city view', 'overhead shot of workspace']
  },
  {
    id: 'pov',
    name: '第一人称视角',
    nameEn: 'POV (Point of View)',
    description: '模拟角色视角的镜头',
    usage: '适合增强代入感，产品体验模拟',
    keywords: ['first-person view', 'POV', '主观视角'],
    category: 'angle',
    examples: ['POV walking through forest', 'first-person driving view']
  },
  {
    id: 'peeking',
    name: '窥视镜头',
    nameEn: 'Peeking Shot',
    description: '模拟从遮挡物后窥视的视角',
    usage: '适合营造神秘、好奇感',
    keywords: ['peeking through', 'over the shoulder'],
    category: 'advanced',
    examples: ['peeking through door', 'over the shoulder shot']
  },
  {
    id: 'aerial',
    name: '航拍',
    nameEn: 'Aerial/Drone Shot',
    description: '从空中俯瞰的镜头',
    usage: '适合展示大场景、建筑全貌、自然风光',
    keywords: ['aerial shot', 'drone shot', 'bird eye view', '航拍'],
    category: 'advanced',
    examples: ['aerial view of campus', 'drone shot over ocean']
  },
  {
    id: 'orbit',
    name: '环绕镜头',
    nameEn: 'Orbit/360 Shot',
    description: '围绕主体旋转的镜头',
    usage: '适合全方位展示产品、人物英雄时刻',
    keywords: ['orbit shot', '360 degree', '环绕镜头', 'circling'],
    category: 'camera_movement',
    examples: ['orbit around product', '360 shot around character']
  }
]

export const shotCategories = [
  { value: 'shot_size', label: '景别', icon: 'Ruler' },
  { value: 'camera_movement', label: '运镜', icon: 'Film' },
  { value: 'angle', label: '视角', icon: 'Eye' },
  { value: 'advanced', label: '高级', icon: 'Sparkles' }
]

export function getShotById(id: string): ShotType | undefined {
  return shotTypes.find(shot => shot.id === id)
}

export function getShotsByCategory(category: string): ShotType[] {
  return shotTypes.filter(shot => shot.category === category)
}

export function searchShots(query: string): ShotType[] {
  const lowerQuery = query.toLowerCase()
  return shotTypes.filter(shot => 
    shot.name.includes(query) ||
    shot.nameEn.toLowerCase().includes(lowerQuery) ||
    shot.description.includes(query) ||
    shot.keywords.some(k => k.toLowerCase().includes(lowerQuery))
  )
}

export const shotCombinations = [
  {
    name: '产品展示组合',
    description: '突出产品高端感',
    shots: ['low-angle', 'dolly-in', 'orbit'],
    prompt: 'low angle shot of product, slow dolly in to detail, orbit around product'
  },
  {
    name: '企业宣传组合',
    description: '展示企业规模和团队',
    shots: ['aerial', 'tracking', 'medium-shot'],
    prompt: 'aerial view of building, tracking shot through office, medium shot of team'
  },
  {
    name: '情感叙事组合',
    description: '营造情绪氛围',
    shots: ['close-up', 'dolly-in', 'handheld'],
    prompt: 'close-up of face, slow dolly in, handheld documentary style'
  },
  {
    name: '开场定调组合',
    description: '视频开场',
    shots: ['extreme-long-shot', 'crane', 'dolly-in'],
    prompt: 'extreme long shot of location, crane down to entrance, dolly in through door'
  }
]
