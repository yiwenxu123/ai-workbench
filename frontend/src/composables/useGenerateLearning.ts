/**
 * 生成结果区的相关知识推荐
 */
import { computed } from 'vue'
import { useGeneratorStore, useDataStore } from '../stores'

export function useGenerateLearning() {
  const generatorStore = useGeneratorStore()
  const dataStore = useDataStore()

  const learningItems = computed(() => {
    const text = generatorStore.prompt.trim()
    if (!text || !dataStore.loaded) return []
    const textLower = text.toLowerCase()

    function scoreItem(item: { name?: string; title?: string; content?: string; description?: string }): number {
      const name = item.name || item.title || item.content || ''
      const desc = item.description || ''
      if (!name && !desc) return 0

      let score = 0
      if (name && name.length >= 2) {
        if (text.includes(name)) score = Math.max(score, 1.0)
        else if (textLower.includes(name.toLowerCase())) score = Math.max(score, 0.6)
      }
      if (desc) {
        const words = desc.split(/[，,、。.；;！!？?\s]+/).filter((w) => w.length >= 2)
        let hit = 0
        for (const w of words) {
          if (text.includes(w)) hit++
        }
        if (hit > 0) {
          const descScore = Math.min(0.9, 0.3 * hit)
          if (descScore > score) score = descScore
        }
      }
      return score
    }

    const scored: Array<{ item: typeof dataStore.terms[number]; score: number }> = []
    for (const term of dataStore.terms) {
      const s = scoreItem(term)
      if (s > 0) scored.push({ item: term, score: s })
    }
    for (const c of dataStore.caseEntries) {
      const s = scoreItem(c)
      if (s > 0) scored.push({ item: c, score: s * 1.5 })
    }

    scored.sort((a, b) => b.score - a.score)
    return scored.slice(0, 8).map((s) => s.item)
  })

  function insertLearningTerm(item: { content?: string; title?: string; name?: string }) {
    const term = item.content || item.title || item.name || ''
    if (!term) return
    const current = generatorStore.prompt
    const suffix = current && !current.endsWith('，') && !current.endsWith(',') ? '，' : ''
    generatorStore.prompt = current + suffix + term
  }

  return { learningItems, insertLearningTerm }
}
