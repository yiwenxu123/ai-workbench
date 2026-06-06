/**
 * 术语智能推荐
 * 根据用户输入的提示词，从术语库中匹配相关术语
 */

import { computed, type Ref } from 'vue'
import { terminology, type TermEntry } from '../data/terminology'

const SCENE_KEYWORDS: Record<string, string[]> = {
  ecommerce: ['电商', '商品', '产品', '上架', '主图', '卖货', '店铺', '淘宝', '京东', '白底', '场景图'],
  social: ['小红书', '公众号', '海报', '宣传', '社交媒体', '推广', '分享', '朋友圈', '封面', '社媒'],
  ppt: ['PPT', '演示', '配图', '幻灯片', '商务', '汇报', '演讲', '提案', '数据', '图表'],
  portrait: ['头像', '形象照', '人物', '证件照', '个人IP', '自拍', '写真', '半身像', '全身像'],
  video: ['视频', '动画', '动起来', '镜头', '运镜', '推拉', '摇移', '转场', '短片'],
  edit: ['修改', '换背景', '重绘', '抠图', '去水印', '修复', '调色', '裁切', '扩图', '替换'],
  architecture: ['建筑', '室内', '装修', '空间', '设计', '房屋', '酒店', '办公室', '客厅', '卧室'],
  food: ['美食', '食物', '菜品', '烹饪', '餐厅', '甜点', '饮料', '咖啡', '蛋糕', '食材'],
  nature: ['自然', '风景', '山水', '森林', '海洋', '天空', '日落', '日出', '花', '动物', '植物'],
  fashion: ['时尚', '穿搭', '服装', '配饰', '走秀', '模特', '潮流', '奢侈品', '包包', '鞋子'],
  technology: ['科技', 'AI', '人工智能', '数据', '芯片', '机器人', '未来', '数字', '智能', '程序'],
}

export interface TermSuggestion {
  term: TermEntry
  relevance: number
  keyword: string
  scene?: string
}

export function useTermSuggestions(prompt: Ref<string>) {
  const suggestions = computed<TermSuggestion[]>(() => {
    const text = prompt.value.trim()
    if (!text) return []

    const matched: Map<string, TermSuggestion> = new Map()
    const scored: { term: TermEntry; score: number; keyword: string; scene?: string }[] = []

    // 检测场景
    let scene: string | undefined
    for (const [sceneName, keywords] of Object.entries(SCENE_KEYWORDS)) {
      for (const kw of keywords) {
        if (text.includes(kw)) {
          scene = sceneName
        }
      }
    }

    // 匹配术语
    for (const term of terminology) {
      let bestScore = 0
      let bestKeyword = ''

      // 检查术语名是否在提示词中
      if (text.includes(term.name)) {
        bestScore = 1
        bestKeyword = term.name
      }

      // 检查英文名
      if (term.nameEn && text.toLowerCase().includes(term.nameEn.toLowerCase())) {
        const score = 1
        if (score > bestScore) {
          bestScore = score
          bestKeyword = term.nameEn
        }
      }

      // 检查相关术语
      if (term.relatedTerms) {
        for (const related of term.relatedTerms) {
          if (text.includes(related)) {
            const score = 0.5
            if (score > bestScore) {
              bestScore = score
              bestKeyword = related
            }
          }
        }
      }

      // 检查示例中的词
      for (const example of term.examples) {
        const words = example.split(/[，,、。.；;！!？?\s]/)
        for (const word of words) {
          if (word.length >= 2 && text.includes(word)) {
            const score = 0.3
            if (score > bestScore) {
              bestScore = score
              bestKeyword = word
            }
          }
        }
      }

      if (bestScore > 0 && !matched.has(term.id)) {
        scored.push({ term, score: bestScore, keyword: bestKeyword, scene })
      }
    }

    // 按相关度排序，取前6个
    scored.sort((a, b) => b.score - a.score)
    const top = scored.slice(0, 6)

    for (const item of top) {
      matched.set(item.term.id, {
        term: item.term,
        relevance: item.score,
        keyword: item.keyword,
        scene: item.scene,
      })
    }

    // 如果匹配太少，补充场景相关术语
    if (matched.size < 3 && scene) {
      const sceneTerms = terminology.filter(t => {
        for (const [sceneName, kw] of Object.entries(SCENE_KEYWORDS)) {
          const firstKeyword = kw[0]
          if (sceneName === scene && firstKeyword && t.description.includes(firstKeyword)) return true
        }
        return false
      })

      for (const term of sceneTerms) {
        if (!matched.has(term.id)) {
          matched.set(term.id, {
            term,
            relevance: 0.2,
            keyword: scene,
            scene,
          })
        }
        if (matched.size >= 4) break
      }
    }

    return Array.from(matched.values())
  })

  return {
    suggestions,
  }
}
