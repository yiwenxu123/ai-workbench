/**
 * 提示词解析器
 * 将提示词拆解为不同类型的元素，支持可视化展示
 */

import { ref, computed, watch } from 'vue'
import { findKeyword, categoryConfig, type KeywordCategory } from '../data/promptKeywords'

export interface ParsedToken {
  text: string
  category: KeywordCategory | 'unknown'
  color: string
  label: string
  startIndex: number
  endIndex: number
}

export interface ParsedPrompt {
  tokens: ParsedToken[]
  categories: Map<KeywordCategory, string[]>
  stats: Record<KeywordCategory, number>
  rawText: string
}

const separators = ['，', ',', '、', '。', '.', '；', ';', '！', '!', '？', '?', '\n', '\t']

export function usePromptParser() {
  const prompt = ref('')
  const parsedResult = ref<ParsedPrompt | null>(null)

  function parse(text: string): ParsedPrompt {
    const tokens: ParsedToken[] = []
    const categories = new Map<KeywordCategory, string[]>()
    const stats: Record<KeywordCategory, number> = {
      subject: 0,
      detail: 0,
      scene: 0,
      style: 0,
      composition: 0,
      lighting: 0,
      quality: 0,
      color: 0,
      mood: 0,
      negative: 0
    }

    const segments = text.split(new RegExp(`[${separators.join('')}]`))
      .map(s => s.trim())
      .filter(s => s.length > 0)

    let currentIndex = 0

    segments.forEach(segment => {
      const startIndex = text.indexOf(segment, currentIndex)
      const endIndex = startIndex + segment.length
      currentIndex = endIndex

      const keyword = findKeyword(segment)
      
      if (keyword) {
        const config = categoryConfig[keyword.category]
        tokens.push({
          text: segment,
          category: keyword.category,
          color: config.color,
          label: config.label,
          startIndex,
          endIndex
        })
        
        const existing = categories.get(keyword.category) || []
        existing.push(segment)
        categories.set(keyword.category, existing)
        stats[keyword.category]++
      } else {
        tokens.push({
          text: segment,
          category: 'unknown',
          color: '#d9d9d9',
          label: '未识别',
          startIndex,
          endIndex
        })
      }
    })

    return {
      tokens,
      categories,
      stats,
      rawText: text
    }
  }

  function parsePrompt(text: string): ParsedPrompt {
    return parse(text)
  }

  watch(prompt, (newVal) => {
    if (newVal.trim()) {
      parsedResult.value = parse(newVal)
    } else {
      parsedResult.value = null
    }
  })

  const hasResult = computed(() => parsedResult.value !== null)
  
  const categoryStats = computed(() => {
    if (!parsedResult.value) return []
    
    return Object.entries(parsedResult.value.stats)
      .filter(([_, count]) => count > 0)
      .map(([category, count]) => ({
        category: category as KeywordCategory,
        count,
        ...categoryConfig[category as KeywordCategory]
      }))
  })

  return {
    prompt,
    parsedResult,
    hasResult,
    categoryStats,
    parse,
    parsePrompt
  }
}
