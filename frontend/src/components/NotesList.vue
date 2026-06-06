<template>
  <n-scrollbar style="max-height: 400px">
    <n-empty v-if="notes.length === 0" description="暂无笔记" />
    <div v-else class="notes-list">
      <div
        v-for="note in notes"
        :key="note.id"
        class="note-item"
        @click="$emit('edit', note)"
      >
        <div class="note-header">
          <span class="note-title">{{ note.title || '无标题笔记' }}</span>
          <n-tag size="tiny" :type="getTargetTypeColor(note.targetType)">
            {{ getTargetTypeLabel(note.targetType) }}
          </n-tag>
        </div>
        <div class="note-content">
          <n-ellipsis :line-clamp="2">{{ note.content }}</n-ellipsis>
        </div>
        <div class="note-footer">
          <div class="note-tags">
            <n-tag v-for="tag in note.tags.slice(0, 3)" :key="tag" size="tiny" type="info">
              {{ tag }}
            </n-tag>
            <span v-if="note.tags.length > 3" class="more-tags">+{{ note.tags.length - 3 }}</span>
          </div>
          <div class="note-meta">
            <span class="note-time">{{ formatTime(note.updatedAt) }}</span>
            <n-button text size="tiny" type="error" @click.stop="$emit('delete', note.id!)">
              删除
            </n-button>
          </div>
        </div>
      </div>
    </div>
  </n-scrollbar>
</template>

<script setup lang="ts">
import { NScrollbar, NEmpty, NTag, NEllipsis, NButton } from 'naive-ui'
import type { Note } from '../types/history'

defineProps<{
  notes: Note[]
}>()

defineEmits<{
  (e: 'edit', note: Note): void
  (e: 'delete', id: number): void
}>()

function getTargetTypeLabel(type: Note['targetType']): string {
  const labels: Record<Note['targetType'], string> = {
    history: '历史',
    prompt: '提示词',
    workflow: '工作流'
  }
  return labels[type]
}

function getTargetTypeColor(type: Note['targetType']): 'default' | 'info' | 'success' | 'warning' | 'error' {
  const colors: Record<Note['targetType'], 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    history: 'info',
    prompt: 'success',
    workflow: 'warning'
  }
  return colors[type]
}

function formatTime(date: Date): string {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  
  return d.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.notes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-item {
  padding: 12px;
  border-radius: 8px;
  background: #f5f5f5;
  cursor: pointer;
  transition: background 0.2s;
}

.note-item:hover {
  background: #e8e8e8;
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.note-title {
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.note-content {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.note-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.note-tags {
  display: flex;
  gap: 4px;
  align-items: center;
}

.more-tags {
  font-size: 10px;
  color: #999;
}

.note-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-time {
  font-size: 11px;
  color: #999;
}
</style>
