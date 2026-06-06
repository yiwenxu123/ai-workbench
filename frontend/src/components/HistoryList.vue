<template>
  <n-scrollbar style="max-height: 350px">
    <n-empty v-if="items.length === 0" description="暂无历史记录" />
    <div v-else class="history-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="history-item"
        :class="{ selected: selectedIds.includes(item.id!) }"
      >
        <n-checkbox
          :checked="selectedIds.includes(item.id!)"
          @update:checked="$emit('toggle-select', item.id!)"
        />
        <div class="history-preview" v-if="item.imageUrl" @click="$emit('detail', item.id!)">
          <n-image
            :src="item.imageUrl"
            alt="generated"
            lazy
            object-fit="cover"
            :preview-disabled="true"
          />
        </div>
        <div class="history-info" @click="$emit('detail', item.id!)">
          <div class="history-prompt">{{ item.prompt.slice(0, 50) }}{{ item.prompt.length > 50 ? '...' : '' }}</div>
          <div class="history-meta">
            <n-tag size="tiny">{{ item.model }}</n-tag>
            <n-tag size="tiny" type="info">{{ item.size }}</n-tag>
            <n-tag v-if="item.providerName" size="tiny" type="warning">{{ item.providerName }}</n-tag>
          </div>
          <div v-if="item.tags.length > 0" class="history-tags">
            <n-tag v-for="tag in item.tags.slice(0, 3)" :key="tag" size="tiny" type="success">
              {{ tag }}
            </n-tag>
            <span v-if="item.tags.length > 3" class="more-tags">+{{ item.tags.length - 3 }}</span>
          </div>
        </div>
        <div class="history-actions">
          <n-button text size="tiny" @click="$emit('reuse', item.prompt)">
            复用
          </n-button>
          <n-button
            text
            size="tiny"
            :type="item.isFavorite ? 'warning' : 'default'"
            @click="$emit('favorite', item.id!)"
          >
            {{ item.isFavorite ? '取消收藏' : '收藏' }}
          </n-button>
          <n-button text size="tiny" type="error" @click="$emit('delete', item.id!)">
            删除
          </n-button>
        </div>
        <div v-if="item.rating" class="history-rating">
          <n-rate :value="item.rating" size="small" readonly />
        </div>
      </div>
    </div>
  </n-scrollbar>
</template>

<script setup lang="ts">
import { NScrollbar, NEmpty, NTag, NButton, NCheckbox, NImage, NRate } from 'naive-ui'
import type { History } from '../types'

defineProps<{
  items: History[]
  selectedIds: number[]
}>()

defineEmits<{
  (e: 'toggle-select', id: number): void
  (e: 'reuse', prompt: string): void
  (e: 'delete', id: number): void
  (e: 'favorite', id: number): void
  (e: 'detail', id: number): void
}>()
</script>

<style scoped>
.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  gap: 8px;
  padding: 8px;
  border-radius: 8px;
  background: #f5f5f5;
  align-items: flex-start;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #e8e8e8;
}

.history-item.selected {
  background: #e6f7ff;
  border: 1px solid #1890ff;
}

.history-preview {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}

.history-preview :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-prompt {
  font-size: 12px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.history-meta {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.history-tags {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-wrap: wrap;
}

.more-tags {
  font-size: 10px;
  color: #999;
}

.history-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.history-rating {
  position: absolute;
  bottom: 4px;
  right: 8px;
}
</style>
