/**
 * 知识库 UI 配置 — 分类标签、颜色映射、工具函数
 * 原 data/terminology.ts 和 data/caseLibrary.ts 中的 UI 配置迁移到此处
 */

import type { TermCategory, CaseExample } from '../types/knowledge'

// ── 术语分类配置 ──

export const termCategoryConfig: Record<TermCategory, { label: string; icon: string; color: string }> = {
  style: { label: '风格', icon: 'Palette', color: '#1890ff' },
  lighting: { label: '光影', icon: 'Lightbulb', color: '#fadb14' },
  composition: { label: '构图', icon: 'Ruler', color: '#722ed1' },
  color: { label: '色彩', icon: 'Rainbow', color: '#eb2f96' },
  material: { label: '材质', icon: 'BrickWall', color: '#fa8c16' },
  mood: { label: '氛围', icon: 'Moon', color: '#13c2c2' },
  technique: { label: '技法', icon: 'Wrench', color: '#52c41a' }
}

// ── 案例分类配置 ──

export const caseCategories = [
  { value: 'ecommerce', label: '电商投流', icon: 'ShoppingCart' },
  { value: 'brand', label: '品牌广告', icon: 'Clapperboard' },
  { value: 'product', label: '产品广告', icon: 'Package' },
  { value: 'drama', label: '短剧叙事', icon: 'Theater' },
  { value: 'animation', label: '动画方向', icon: 'Palette' },
  { value: 'film', label: '影视类', icon: 'Film' },
  { value: 'social', label: '社媒玩法', icon: 'Smartphone' }
]

// ── 工具函数 ──

export function adaptPrompt(caseExample: CaseExample, newSubject: string): string {
  return caseExample.prompt.replace(/\{主体\}/g, newSubject)
}
