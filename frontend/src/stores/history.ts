/**
 * 历史记录状态管理
 * 支持收藏、评分、标签、笔记等增强功能
 */

import { defineStore } from 'pinia'
import { ref, computed, toRaw } from 'vue'
import { db } from '../db'
import { config } from '../config'
import type { History } from '../types'
import type { Note } from '../types/history'

export const useHistoryStore = defineStore('history', () => {
  const items = ref<History[]>([])
  const selectedIds = ref<number[]>([])
  const detailItemId = ref<number | null>(null)

  const favorites = computed(() => items.value.filter(item => item.isFavorite))
  const recentItems = computed(() => items.value.slice(0, 10))

  async function load(): Promise<void> {
    items.value = await db.history
      .orderBy('createdAt')
      .reverse()
      .limit(config.history.maxItems)
      .toArray()
  }

  async function add(item: Omit<History, 'id' | 'createdAt' | 'tags' | 'isFavorite'> & { tags?: string[] }): Promise<number> {
    const id = await db.history.add({
      prompt: item.prompt,
      model: item.model,
      size: item.size,
      imageUrl: item.imageUrl,
      thumbnail: item.thumbnail,
      seed: item.seed,
      steps: item.steps,
      cfgScale: item.cfgScale,
      sampler: item.sampler,
      negativePrompt: item.negativePrompt,
      providerId: item.providerId,
      providerName: item.providerName,
      generationTime: item.generationTime,
      notes: item.notes,
      rating: item.rating,
      tags: [...(toRaw(item.tags) || [])],
      isFavorite: false,
      createdAt: new Date(),
    })
    // 直接在本地数组前端插入，避免全量重新加载
    const newItem: History = {
      prompt: item.prompt,
      model: item.model,
      size: item.size,
      imageUrl: item.imageUrl,
      thumbnail: item.thumbnail,
      seed: item.seed,
      steps: item.steps,
      cfgScale: item.cfgScale,
      sampler: item.sampler,
      negativePrompt: item.negativePrompt,
      providerId: item.providerId,
      providerName: item.providerName,
      generationTime: item.generationTime,
      notes: item.notes,
      rating: item.rating,
      id: id as number,
      tags: [...(toRaw(item.tags) || [])],
      isFavorite: false,
      createdAt: new Date(),
    }
    items.value.unshift(newItem as History)
    if (items.value.length > config.history.maxItems) {
      items.value.pop()
    }
    return id as number
  }

  async function update(id: number, updates: Partial<History>): Promise<void> {
    const cleanUpdates = { ...updates }
    // toRaw 确保数组字段不会包含 Vue proxy
    if (cleanUpdates.tags) cleanUpdates.tags = [...toRaw(cleanUpdates.tags)]
    await db.history.update(id, cleanUpdates)
    // 直接在本地数组更新，避免全量重新加载
    const idx = items.value.findIndex(i => i.id === id)
    const current = items.value[idx]
    if (idx !== -1 && current) {
      items.value[idx] = { ...current, ...cleanUpdates }
    }
  }

  async function remove(id: number): Promise<void> {
    await db.history.delete(id)
    await db.notes.where('targetId').equals(id).delete()
    items.value = items.value.filter(i => i.id !== id)
  }

  async function removeMany(ids: number[]): Promise<void> {
    await Promise.all(ids.map(id => db.history.delete(id)))
    await db.notes.where('targetId').anyOf(ids).delete()
    const idSet = new Set(ids)
    items.value = items.value.filter(i => !idSet.has(i.id!))
  }

  async function clear(): Promise<void> {
    await db.history.clear()
    await db.notes.clear()
    items.value = []
  }

  /** 使用数组代替 Set，确保 Vue 响应式 */
  function toggleSelect(id: number): void {
    const idx = selectedIds.value.indexOf(id)
    if (idx >= 0) selectedIds.value.splice(idx, 1)
    else selectedIds.value.push(id)
  }

  function selectAll(): void {
    selectedIds.value = items.value.map(item => item.id!)
  }

  function clearSelection(): void {
    selectedIds.value = []
  }

  async function deleteSelected(): Promise<void> {
    await removeMany(selectedIds.value)
    selectedIds.value = []
  }

  async function toggleFavorite(id: number): Promise<void> {
    const item = items.value.find(i => i.id === id)
    if (item) {
      await update(id, { isFavorite: !item.isFavorite })
    }
  }

  async function setRating(id: number, rating: number): Promise<void> {
    await update(id, { rating: rating >= 1 && rating <= 5 ? rating : undefined })
  }

  async function setTags(id: number, tags: string[]): Promise<void> {
    await update(id, { tags })
  }

  async function setNotes(id: number, notes: string): Promise<void> {
    await update(id, { notes })
  }

  async function getNotes(historyId: number): Promise<Note[]> {
    return db.notes
      .where('targetId')
      .equals(historyId)
      .toArray()
  }

  async function addNote(note: Omit<Note, 'id' | 'createdAt' | 'updatedAt'>): Promise<number> {
    const now = new Date()
    const id = await db.notes.add({
      targetType: note.targetType,
      targetId: note.targetId,
      title: note.title,
      content: note.content,
      tags: [...toRaw(note.tags)],
      createdAt: now,
      updatedAt: now
    })
    return id as number
  }

  async function updateNote(id: number, content: string, tags?: string[]): Promise<void> {
    const updateData: Partial<Note> = {
      content,
      updatedAt: new Date()
    }
    if (tags !== undefined) {
      updateData.tags = [...toRaw(tags)]
    }
    await db.notes.update(id, updateData)
  }

  async function deleteNote(id: number): Promise<void> {
    await db.notes.delete(id)
  }

  async function searchByTag(tag: string): Promise<History[]> {
    return db.history
      .where('tags')
      .equals(tag)
      .reverse()
      .toArray()
  }

  async function searchByKeyword(keyword: string): Promise<History[]> {
    const lowerKeyword = keyword.toLowerCase()
    return items.value.filter(item =>
      item.prompt.toLowerCase().includes(lowerKeyword) ||
      item.notes?.toLowerCase().includes(lowerKeyword) ||
      item.tags.some(t => t.toLowerCase().includes(lowerKeyword))
    )
  }

  function setDetailItem(id: number | null): void {
    detailItemId.value = id
  }

  const detailItem = computed(() => {
    if (detailItemId.value === null) return null
    return items.value.find(item => item.id === detailItemId.value) || null
  })

  return {
    items,
    selectedIds,
    detailItemId,
    detailItem,
    favorites,
    recentItems,
    load,
    add,
    update,
    remove,
    removeMany,
    clear,
    toggleSelect,
    selectAll,
    clearSelection,
    deleteSelected,
    toggleFavorite,
    setRating,
    setTags,
    setNotes,
    getNotes,
    addNote,
    updateNote,
    deleteNote,
    searchByTag,
    searchByKeyword,
    setDetailItem,
  }
})
