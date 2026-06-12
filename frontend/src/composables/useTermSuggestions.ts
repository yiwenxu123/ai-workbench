/**
 * 术语智能推荐
 * 优先使用后端 FTS5 搜索 API，降级到 dataStore 本地匹配
 */

import { ref, watch, type Ref } from 'vue'
import axios from 'axios'
import { config } from '../config'
import { useDataStore } from '../stores'
import type { TermCategory } from '../types/knowledge'

interface LocalTermEntry {
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
  term: LocalTermEntry
  relevance: number
  keyword: string
  scene?: string
}

/** 从用户输入中检测场景 */
function detectScene(text: string): string | undefined {
  for (const [sceneName, keywords] of Object.entries(SCENE_KEYWORDS)) {
    for (const kw of keywords) {
      if (text.includes(kw)) return sceneName
    }
  }
  return undefined
}

/** 将 API 返回的 KnowledgeEntry 映射为 LocalTermEntry */
function mapToLocalTermEntry(item: any): LocalTermEntry {
  return {
    id: item.id || '',
    name: item.title || '',
    nameEn: item.tags?.[0] || '',
    category: item.category || 'style',
    description: item.content || '',
    usage: Array.isArray(item.tips) ? item.tips.join('；') : (item.tips || ''),
    examples: item.examples || [],
    relatedTerms: item.relatedTerms || [],
    tips: Array.isArray(item.tips) ? item.tips[0] : item.tips,
  }
}

/** 本地客户端匹配（降级方案） */
function localMatch(text: string, terms: LocalTermEntry[]): TermSuggestion[] {
  const scene = detectScene(text)
  const scored: { term: LocalTermEntry; score: number; keyword: string; scene?: string }[] = []

  for (const term of terms) {
    let bestScore = 0
    let bestKeyword = ''

    if (text.includes(term.name)) {
      bestScore = 1
      bestKeyword = term.name
    }

    if (term.nameEn && text.toLowerCase().includes(term.nameEn.toLowerCase())) {
      if (1 > bestScore) {
        bestScore = 1
        bestKeyword = term.nameEn
      }
    }

    if (term.relatedTerms) {
      for (const related of term.relatedTerms) {
        if (text.includes(related) && 0.5 > bestScore) {
          bestScore = 0.5
          bestKeyword = related
        }
      }
    }

    for (const example of term.examples) {
      const words = example.split(/[，,、。.；;！!？?\s]/)
      for (const word of words) {
        if (word.length >= 2 && text.includes(word) && 0.3 > bestScore) {
          bestScore = 0.3
          bestKeyword = word
        }
      }
    }

    if (bestScore > 0) {
      scored.push({ term, score: bestScore, keyword: bestKeyword, scene })
    }
  }

  scored.sort((a, b) => b.score - a.score)
  const top = scored.slice(0, 6)
  const matched = new Map<string, TermSuggestion>()

  for (const item of top) {
    matched.set(item.term.id, {
      term: item.term,
      relevance: item.score,
      keyword: item.keyword,
      scene: item.scene,
    })
  }

  // 补充场景相关术语
  if (matched.size < 3 && scene) {
    const sceneTerms = terms.filter(t => {
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
}

export function useTermSuggestions(prompt: Ref<string>) {
  const suggestions = ref<TermSuggestion[]>([])
  const dataStore = useDataStore()
  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  async function fetchSuggestions(text: string) {
    if (!text) {
      suggestions.value = []
      return
    }

    const scene = detectScene(text)

    try {
      const resp = await axios.post(`${config.apiBaseUrl}/api/knowledge/search`, {
        query: text,
        scene: scene || 'general',
        types: ['term'],
        limit: 10,
      })

      if (resp.data?.items?.length) {
        const mapped = resp.data.items.map((item: any) => mapToLocalTermEntry(item))
        // 用本地匹配逻辑对 API 结果重新评分
        const result = localMatch(text, mapped)
        suggestions.value = result
        return
      }
    } catch {
      // API 不可用，降级到本地匹配
    }

    // 降级：使用 dataStore 中的术语数据（KnowledgeEntry → LocalTermEntry）
    const localTerms = dataStore.terms.map(mapToLocalTermEntry)
    if (localTerms.length) {
      suggestions.value = localMatch(text, localTerms)
    } else {
      suggestions.value = []
    }
  }

  watch(prompt, (newVal) => {
    if (debounceTimer) clearTimeout(debounceTimer)
    const text = newVal.trim()
    if (!text) {
      suggestions.value = []
      return
    }
    debounceTimer = setTimeout(() => fetchSuggestions(text), 300)
  })

  return {
    suggestions,
  }
}
