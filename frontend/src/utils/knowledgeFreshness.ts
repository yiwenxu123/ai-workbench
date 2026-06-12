/** 知识条目超过此天数未核验则标记为可能过时 */
export const KNOWLEDGE_STALE_DAYS = 90

export function isKnowledgeStale(lastVerified?: string): boolean {
  if (!lastVerified) return true
  const verified = new Date(lastVerified)
  if (Number.isNaN(verified.getTime())) return true
  const ageMs = Date.now() - verified.getTime()
  return ageMs > KNOWLEDGE_STALE_DAYS * 24 * 60 * 60 * 1000
}

export function staleKnowledgeLabel(lastVerified?: string): string | null {
  if (!lastVerified) return '待核验'
  if (isKnowledgeStale(lastVerified)) return '可能过时'
  return null
}
