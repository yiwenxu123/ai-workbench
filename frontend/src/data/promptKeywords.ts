/**
 * 提示词关键词词库
 * 用于解析提示词结构，识别不同类型的元素
 */

export type KeywordCategory = 'subject' | 'detail' | 'scene' | 'style' | 'composition' | 'lighting' | 'quality' | 'color' | 'mood' | 'negative'

export interface KeywordEntry {
  word: string
  aliases?: string[]
  category: KeywordCategory
  description?: string
  examples?: string[]
}

export const categoryConfig: Record<KeywordCategory, { label: string; color: string; icon: string }> = {
  subject: { label: '主体', color: '#f5222d', icon: 'Target' },
  detail: { label: '细节', color: '#fa8c16', icon: 'Sparkles' },
  scene: { label: '场景', color: '#52c41a', icon: 'Mountain' },
  style: { label: '风格', color: '#1890ff', icon: 'Palette' },
  composition: { label: '构图', color: '#722ed1', icon: 'Ruler' },
  lighting: { label: '光影', color: '#fadb14', icon: 'Lightbulb' },
  quality: { label: '画质', color: '#8c8c8c', icon: 'Camera' },
  color: { label: '色彩', color: '#eb2f96', icon: 'Rainbow' },
  mood: { label: '氛围', color: '#13c2c2', icon: 'Moon' },
  negative: { label: '负面', color: '#434343', icon: 'Ban' }
}

export const promptKeywords: KeywordEntry[] = [
  // 主体类
  { word: '女孩', aliases: ['少女', '女生', '美女'], category: 'subject', description: '女性人物主体' },
  { word: '男孩', aliases: ['少年', '男生', '帅哥'], category: 'subject', description: '男性人物主体' },
  { word: '猫', aliases: ['猫咪', '小猫'], category: 'subject', description: '猫科动物' },
  { word: '狗', aliases: ['狗狗', '小狗', '犬'], category: 'subject', description: '犬科动物' },
  { word: '城堡', category: 'subject', description: '建筑主体' },
  { word: '汽车', aliases: ['轿车', '跑车'], category: 'subject', description: '交通工具主体' },
  { word: '机器人', aliases: ['机甲', '机械人'], category: 'subject', description: '科幻主体' },
  { word: '龙', aliases: ['神龙', '飞龙'], category: 'subject', description: '神话生物' },
  { word: '天使', category: 'subject', description: '神话人物' },
  { word: '恶魔', category: 'subject', description: '神话人物' },
  { word: '武士', aliases: ['剑客', '战士'], category: 'subject', description: '人物角色' },
  { word: '公主', category: 'subject', description: '人物角色' },
  { word: '王子', category: 'subject', description: '人物角色' },
  { word: '精灵', category: 'subject', description: '奇幻生物' },
  { word: '独角兽', category: 'subject', description: '神话生物' },
  { word: '凤凰', category: 'subject', description: '神话生物' },
  
  // 细节类
  { word: '长发', aliases: ['飘逸长发'], category: 'detail', description: '头发细节' },
  { word: '短发', category: 'detail', description: '头发细节' },
  { word: '蓝眼睛', aliases: ['蓝色眼睛', '碧眼'], category: 'detail', description: '眼睛颜色' },
  { word: '红裙', aliases: ['红色裙子'], category: 'detail', description: '服装细节' },
  { word: '白裙', aliases: ['白色裙子'], category: 'detail', description: '服装细节' },
  { word: '皇冠', category: 'detail', description: '配饰细节' },
  { word: '翅膀', aliases: ['羽翼'], category: 'detail', description: '身体特征' },
  { word: '角', aliases: ['犄角'], category: 'detail', description: '身体特征' },
  { word: '尾巴', category: 'detail', description: '身体特征' },
  { word: '毛发蓬松', category: 'detail', description: '毛发质感' },
  { word: '肌肉', aliases: ['肌肉发达'], category: 'detail', description: '身体特征' },
  { word: '纹身', category: 'detail', description: '皮肤装饰' },
  { word: '伤疤', category: 'detail', description: '皮肤特征' },
  { word: '眼镜', category: 'detail', description: '配饰' },
  { word: '耳环', category: 'detail', description: '配饰' },
  { word: '项链', category: 'detail', description: '配饰' },
  
  // 场景类
  { word: '森林', aliases: ['树林', '密林'], category: 'scene', description: '自然环境' },
  { word: '城市', aliases: ['都市', '城市街道'], category: 'scene', description: '城市环境' },
  { word: '海边', aliases: ['海滩', '海岸'], category: 'scene', description: '自然环境' },
  { word: '山顶', aliases: ['山峰', '高山'], category: 'scene', description: '自然环境' },
  { word: '沙漠', category: 'scene', description: '自然环境' },
  { word: '雪地', aliases: ['雪原', '冰原'], category: 'scene', description: '自然环境' },
  { word: '夜空', aliases: ['星空'], category: 'scene', description: '天空场景' },
  { word: '日落', aliases: ['黄昏', '夕阳'], category: 'scene', description: '时间场景' },
  { word: '日出', aliases: ['黎明', '晨曦'], category: 'scene', description: '时间场景' },
  { word: '月球', aliases: ['月亮'], category: 'scene', description: '太空场景' },
  { word: '宇宙', aliases: ['太空', '星际'], category: 'scene', description: '太空场景' },
  { word: '废墟', aliases: ['遗迹'], category: 'scene', description: '建筑场景' },
  { word: '花园', aliases: ['花园'], category: 'scene', description: '自然环境' },
  { word: '宫殿', aliases: ['皇宫'], category: 'scene', description: '建筑场景' },
  { word: '街道', aliases: ['马路', '道路'], category: 'scene', description: '城市环境' },
  { word: '室内', aliases: ['房间', '屋内'], category: 'scene', description: '室内环境' },
  { word: '客厅', category: 'scene', description: '室内环境' },
  { word: '卧室', category: 'scene', description: '室内环境' },
  
  // 风格类
  { word: '赛博朋克', aliases: ['cyberpunk'], category: 'style', description: '科幻风格，霓虹灯、高科技' },
  { word: '蒸汽朋克', aliases: ['steampunk'], category: 'style', description: '复古未来主义风格' },
  { word: '水彩', aliases: ['水彩画', '水彩风格'], category: 'style', description: '绘画风格' },
  { word: '油画', aliases: ['油画风格'], category: 'style', description: '绘画风格' },
  { word: '素描', aliases: ['素描风格', '铅笔素描'], category: 'style', description: '绘画风格' },
  { word: '动漫', aliases: ['动画风格', '日漫', '二次元'], category: 'style', description: '动画风格' },
  { word: '写实', aliases: ['写实风格', '照片级'], category: 'style', description: '逼真风格' },
  { word: '卡通', aliases: ['卡通风格', 'Q版'], category: 'style', description: '卡通风格' },
  { word: '极简主义', aliases: ['极简风格', '简约'], category: 'style', description: '简约风格' },
  { word: '巴洛克', aliases: ['巴洛克风格'], category: 'style', description: '古典华丽风格' },
  { word: '哥特', aliases: ['哥特风格', '哥特式'], category: 'style', description: '暗黑华丽风格' },
  { word: '印象派', aliases: ['印象派风格'], category: 'style', description: '绘画流派' },
  { word: '浮世绘', aliases: ['日式浮世绘'], category: 'style', description: '日本传统绘画风格' },
  { word: '国风', aliases: ['中国风', '国潮'], category: 'style', description: '中国传统风格' },
  { word: '古风', aliases: ['古典风格'], category: 'style', description: '古典风格' },
  { word: '像素', aliases: ['像素风格', '像素艺术'], category: 'style', description: '复古游戏风格' },
  { word: '低多边形', aliases: ['low poly', '低模'], category: 'style', description: '3D风格' },
  { word: '概念艺术', aliases: ['concept art'], category: 'style', description: '概念设计风格' },
  { word: '插画', aliases: ['插画风格'], category: 'style', description: '插画风格' },
  { word: '水墨', aliases: ['水墨画', '中国水墨'], category: 'style', description: '中国传统绘画' },
  
  // 构图类
  { word: '特写', aliases: ['近景', '大头照'], category: 'composition', description: '近距离拍摄' },
  { word: '广角', aliases: ['广角镜头', '全景'], category: 'composition', description: '广阔视野' },
  { word: '俯视', aliases: ['俯拍', '鸟瞰'], category: 'composition', description: '从上往下看' },
  { word: '仰视', aliases: ['仰拍', '低角度'], category: 'composition', description: '从下往上看' },
  { word: '侧视', aliases: ['侧面', '侧脸'], category: 'composition', description: '侧面角度' },
  { word: '背影', aliases: ['背面'], category: 'composition', description: '背面视角' },
  { word: '全身', aliases: ['全身照'], category: 'composition', description: '完整身体' },
  { word: '半身', aliases: ['半身照', '胸像'], category: 'composition', description: '上半身' },
  { word: '三分法', aliases: ['三分构图'], category: 'composition', description: '经典构图法则' },
  { word: '对称', aliases: ['对称构图'], category: 'composition', description: '对称布局' },
  { word: '对角线', aliases: ['对角线构图'], category: 'composition', description: '动态构图' },
  { word: '黄金分割', aliases: ['黄金比例'], category: 'composition', description: '经典构图法则' },
  { word: '居中', aliases: ['中心构图'], category: 'composition', description: '主体居中' },
  
  // 光影类
  { word: '丁达尔效应', aliases: ['耶稣光', '光束'], category: 'lighting', description: '光线穿透效果' },
  { word: '逆光', aliases: ['背光'], category: 'lighting', description: '光源在主体后方' },
  { word: '侧光', category: 'lighting', description: '侧面光源' },
  { word: '柔光', aliases: ['柔和光线'], category: 'lighting', description: '柔和的光线' },
  { word: '硬光', aliases: ['硬质光线'], category: 'lighting', description: '强烈的光线' },
  { word: '霓虹', aliases: ['霓虹灯', '霓虹光'], category: 'lighting', description: '霓虹灯光效果' },
  { word: '伦勃朗光', category: 'lighting', description: '经典人像布光' },
  { word: '轮廓光', category: 'lighting', description: '勾勒轮廓的光' },
  { word: '电影感', aliases: ['电影光效'], category: 'lighting', description: '电影级光效' },
  { word: '黄昏光', aliases: ['黄金时刻'], category: 'lighting', description: '日落时分的光线' },
  { word: '月光', aliases: ['月光照明'], category: 'lighting', description: '月光效果' },
  { word: '烛光', category: 'lighting', description: '烛光效果' },
  { word: '体积光', aliases: ['体积光效'], category: 'lighting', description: '3D光效' },
  { word: '光晕', aliases: ['耀斑'], category: 'lighting', description: '光晕效果' },
  { word: '阴影', aliases: ['投影'], category: 'lighting', description: '阴影效果' },
  
  // 画质类
  { word: '4K', aliases: ['4k', '超高清'], category: 'quality', description: '高分辨率' },
  { word: '8K', aliases: ['8k'], category: 'quality', description: '超高分辨率' },
  { word: '高清', aliases: ['HD'], category: 'quality', description: '高清晰度' },
  { word: '细节丰富', aliases: ['高细节', '精细'], category: 'quality', description: '丰富的细节' },
  { word: '锐利', aliases: ['清晰', '锐化'], category: 'quality', description: '清晰的边缘' },
  { word: '高分辨率', aliases: ['高解析度'], category: 'quality', description: '高分辨率' },
  { word: '杰作', aliases: ['masterpiece'], category: 'quality', description: '高质量作品' },
  { word: '最佳质量', aliases: ['best quality'], category: 'quality', description: '最高质量' },
  { word: '专业', aliases: ['professional'], category: 'quality', description: '专业级别' },
  { word: '虚化', aliases: ['景深', '背景虚化'], category: 'quality', description: '景深效果' },
  { word: '动态模糊', aliases: ['运动模糊'], category: 'quality', description: '运动效果' },
  
  // 色彩类
  { word: '莫兰迪色', aliases: ['莫兰迪', '高级灰'], category: 'color', description: '低饱和高级色调' },
  { word: '高饱和', aliases: ['鲜艳', '饱和度高'], category: 'color', description: '鲜艳的色彩' },
  { word: '低饱和', aliases: ['淡雅', '饱和度低'], category: 'color', description: '淡雅的色彩' },
  { word: '冷暖对比', aliases: ['冷暖色调'], category: 'color', description: '冷暖色对比' },
  { word: '单色调', aliases: ['单色'], category: 'color', description: '单一色调' },
  { word: '黑白', aliases: ['黑白照片', '黑白风格'], category: 'color', description: '黑白色调' },
  { word: '复古色', aliases: ['复古色调'], category: 'color', description: '复古色调' },
  { word: '暖色调', aliases: ['暖色'], category: 'color', description: '温暖色调' },
  { word: '冷色调', aliases: ['冷色'], category: 'color', description: '冷色色调' },
  { word: '深蓝', category: 'color', description: '颜色描述' },
  { word: '金色', aliases: ['金黄'], category: 'color', description: '颜色描述' },
  { word: '银色', aliases: ['银白'], category: 'color', description: '颜色描述' },
  
  // 氛围类
  { word: '梦幻', aliases: ['梦幻感', '童话'], category: 'mood', description: '梦幻氛围' },
  { word: '末日', aliases: ['末日感', '末世'], category: 'mood', description: '末日氛围' },
  { word: '温馨', aliases: ['温暖', '温馨感'], category: 'mood', description: '温馨氛围' },
  { word: '神秘', aliases: ['神秘感'], category: 'mood', description: '神秘氛围' },
  { word: '恐怖', aliases: ['恐怖感', '惊悚'], category: 'mood', description: '恐怖氛围' },
  { word: '浪漫', aliases: ['浪漫感'], category: 'mood', description: '浪漫氛围' },
  { word: '史诗', aliases: ['史诗感', '史诗级'], category: 'mood', description: '史诗氛围' },
  { word: '宁静', aliases: ['平静', '安详'], category: 'mood', description: '宁静氛围' },
  { word: '紧张', aliases: ['紧张感'], category: 'mood', description: '紧张氛围' },
  { word: '动感', aliases: ['动态', '动感十足'], category: 'mood', description: '动感氛围' },
  
  // 负面词
  { word: '低质量', aliases: ['low quality', '低画质'], category: 'negative', description: '负面词' },
  { word: '模糊', aliases: ['blurry', '不清晰'], category: 'negative', description: '负面词' },
  { word: '畸形', aliases: ['deformed', '变形'], category: 'negative', description: '负面词' },
  { word: '多余手指', aliases: ['extra fingers', '多指'], category: 'negative', description: '负面词' },
  { word: '坏手', aliases: ['bad hands', '手部错误'], category: 'negative', description: '负面词' },
  { word: '水印', aliases: ['watermark', 'logo'], category: 'negative', description: '负面词' },
  { word: '文字', aliases: ['text', 'signature'], category: 'negative', description: '负面词' },
  { word: '裁剪', aliases: ['cropped', '截断'], category: 'negative', description: '负面词' },
  { word: '丑陋', aliases: ['ugly', '难看'], category: 'negative', description: '负面词' },
  { word: '解剖错误', aliases: ['bad anatomy'], category: 'negative', description: '负面词' },
]

export function findKeyword(word: string): KeywordEntry | undefined {
  const lowerWord = word.toLowerCase()
  return promptKeywords.find(entry => 
    entry.word === word || 
    entry.word.toLowerCase() === lowerWord ||
    entry.aliases?.some(alias => alias === word || alias.toLowerCase() === lowerWord)
  )
}

export function getKeywordsByCategory(category: KeywordCategory): KeywordEntry[] {
  return promptKeywords.filter(entry => entry.category === category)
}
