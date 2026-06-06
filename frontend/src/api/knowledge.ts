import axios from 'axios'
import { config } from '../config'
import type { KnowledgeEntry, KnowledgeSearchRequest, KnowledgeSearchResponse } from '../types/api'

export async function searchKnowledge(
  query: string,
  options: Omit<KnowledgeSearchRequest, 'query'> = {}
): Promise<KnowledgeEntry[]> {
  const body: KnowledgeSearchRequest = { query, ...options }
  try {
    const res = await axios.post<KnowledgeSearchResponse>(
      `${config.apiBaseUrl}/api/knowledge/search`,
      body,
      { timeout: 5000 }
    )
    return res.data.items || []
  } catch {
    return []
  }
}

function escapePrompt(s: string): string {
  return s.replace(/{/g, '{{').replace(/}/g, '}}')
}

export function buildKnowledgeContext(
  entries: KnowledgeEntry[],
  _scene: string
): string {
  const groups: Record<string, KnowledgeEntry[]> = {}
  for (const e of entries) {
    const t = e.type || 'other'
    if (!groups[t]) groups[t] = []
    groups[t].push(e)
  }

  const parts: string[] = []

  if (groups.industry) {
    parts.push('【行业知识】')
    for (const e of groups.industry) {
      parts.push(`- ${e.content}`)
      if (e.tips && e.tips.length > 0) {
        parts.push(`  技巧：${e.tips.slice(0, 3).join('；')}`)
      }
    }
  }

  if (groups.term) {
    parts.push('【推荐术语】')
    for (const e of groups.term) {
      const usage = e.examples?.length ? `（例：${e.examples.slice(0, 2).join('、')}）` : ''
      parts.push(`- ${e.title}${usage}`)
    }
  }

  if (groups.formula) {
    parts.push('【提示词结构公式】')
    for (const e of groups.formula) {
      parts.push(`- ${e.content}`)
      if (e.examples?.length) {
        parts.push(`  示例：${e.examples[0]}`)
      }
    }
  }

  if (groups.case) {
    parts.push('【优秀案例参考】')
    for (const e of groups.case.slice(0, 3)) {
      parts.push(`- 案例：${e.title}`)
      if (e.prompt) parts.push(`  提示词：${escapePrompt(e.prompt)}`)
      if (e.tips?.length) parts.push(`  技巧：${e.tips.slice(0, 2).join('；')}`)
    }
  }

  if (groups.negative_pack) {
    const merged = groups.negative_pack.map(e => e.negativePrompt).filter(Boolean).join(', ')
    if (merged) {
      parts.push('【负面词参考】')
      parts.push(`- ${merged}`)
    }
  }

  return parts.join('\n')
}
