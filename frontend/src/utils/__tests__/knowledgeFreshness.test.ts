import { describe, it, expect } from 'vitest'
import { isKnowledgeStale, staleKnowledgeLabel, KNOWLEDGE_STALE_DAYS } from '../knowledgeFreshness'

describe('knowledgeFreshness', () => {
  it('marks missing date as stale', () => {
    expect(isKnowledgeStale()).toBe(true)
    expect(staleKnowledgeLabel()).toBe('待核验')
  })

  it('marks old date as stale', () => {
    const old = new Date()
    old.setDate(old.getDate() - KNOWLEDGE_STALE_DAYS - 1)
    const label = staleKnowledgeLabel(old.toISOString().slice(0, 10))
    expect(label).toBe('可能过时')
  })

  it('accepts recent verification', () => {
    const recent = new Date().toISOString().slice(0, 10)
    expect(isKnowledgeStale(recent)).toBe(false)
    expect(staleKnowledgeLabel(recent)).toBeNull()
  })
})
