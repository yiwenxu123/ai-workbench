/**
 * 提示词库状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed, toRaw } from 'vue'
import { db } from '../db'
import type { Prompt, PromptFormData } from '../types'

export const usePromptStore = defineStore('prompt', () => {
  const items = ref<Prompt[]>([])
  const searchText = ref('')
  const selectedIds = ref<number[]>([])
  const showModal = ref(false)
  const editingPrompt = ref<Prompt | null>(null)

  const filteredItems = computed(() => {
    if (!searchText.value) return items.value
    const search = searchText.value.toLowerCase()
    return items.value.filter(p =>
      p.title.toLowerCase().includes(search) ||
      p.content.toLowerCase().includes(search) ||
      p.tags.some(t => t.toLowerCase().includes(search))
    )
  })

  async function load(): Promise<void> {
    items.value = await db.prompts.orderBy('updatedAt').reverse().toArray()
  }

  async function add(data: PromptFormData): Promise<void> {
    const now = new Date()
    await db.prompts.add({
      title: data.title,
      content: data.content,
      category: data.category,
      tags: [...toRaw(data.tags)],
      createdAt: now,
      updatedAt: now
    })
    await load()
  }

  async function update(id: number, data: Partial<PromptFormData>): Promise<void> {
    const updateData: Partial<Prompt> = {
      updatedAt: new Date()
    }
    if (data.title !== undefined) updateData.title = data.title
    if (data.content !== undefined) updateData.content = data.content
    if (data.category !== undefined) updateData.category = data.category
    if (data.tags !== undefined) updateData.tags = [...toRaw(data.tags)]
    
    await db.prompts.update(id, updateData)
    await load()
  }

  async function remove(id: number): Promise<void> {
    await db.prompts.delete(id)
    await load()
  }

  async function removeMany(ids: number[]): Promise<void> {
    await Promise.all(ids.map(id => db.prompts.delete(id)))
    await load()
  }

  function toggleSelect(id: number): void {
    const idx = selectedIds.value.indexOf(id)
    if (idx >= 0) selectedIds.value.splice(idx, 1)
    else selectedIds.value.push(id)
  }

  function selectAll(): void {
    selectedIds.value = filteredItems.value.map(item => item.id!)
  }

  function clearSelection(): void {
    selectedIds.value = []
  }

  async function deleteSelected(): Promise<void> {
    await removeMany(selectedIds.value)
    selectedIds.value = []
  }

  function startEdit(prompt: Prompt): void {
    editingPrompt.value = { ...prompt }
    showModal.value = true
  }

  function cancelEdit(): void {
    editingPrompt.value = null
    showModal.value = false
  }

  return {
    items,
    searchText,
    selectedIds,
    showModal,
    editingPrompt,
    filteredItems,
    load,
    add,
    update,
    remove,
    removeMany,
    toggleSelect,
    selectAll,
    clearSelection,
    deleteSelected,
    startEdit,
    cancelEdit,
  }
})
