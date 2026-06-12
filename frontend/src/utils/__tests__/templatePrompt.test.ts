import { describe, it, expect } from 'vitest'
import { extractPlaceholders, fillPromptTemplate } from '../templatePrompt'

describe('templatePrompt', () => {
  it('extracts unique placeholders', () => {
    expect(extractPlaceholders('{产品}在{场景}中展示，{产品}')).toEqual(['产品', '场景'])
  })

  it('fills template values', () => {
    const prompt = '{产品名称}在{场景}中旋转展示'
    expect(fillPromptTemplate(prompt, { 产品名称: '手表', 场景: '工作室' }))
      .toBe('手表在工作室中旋转展示')
  })
})
