<template>
  <n-scrollbar style="max-height: 350px">
    <n-empty v-if="templates.length === 0" description="暂无模板" size="small" />
    <div v-else class="template-list">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-item"
        @click="$emit('select', template)"
      >
        <div class="template-header">
          <span class="template-name">{{ template.name }}</span>
          <div class="template-actions">
            <n-tag v-if="template.isOfficial" size="tiny" type="info">官方</n-tag>
            <template v-if="!readonly">
              <n-button text size="tiny" @click.stop="$emit('edit', template)">
                <n-icon :component="CreateOutline" color="#666" />
              </n-button>
              <n-button v-if="!template.isOfficial && template.id" text size="tiny" @click.stop="$emit('delete', template.id)">
                <n-icon :component="TrashOutline" color="#999" />
              </n-button>
            </template>
            <n-button v-if="template.isOfficial && template.id" text size="tiny" @click.stop="$emit('duplicate', template.id)">
              <n-icon :component="CopyOutline" color="#1890ff" />
            </n-button>
          </div>
        </div>
        <div class="template-content">{{ template.content.slice(0, 60) }}...</div>
        <div class="template-meta">
          <n-tag v-if="template.recommendedSize" size="tiny" :bordered="false">
            {{ template.recommendedSize }}
          </n-tag>
          <n-tag v-for="tag in template.tags.slice(0, 2)" :key="tag" size="tiny" round>
            {{ tag }}
          </n-tag>
        </div>
      </div>
    </div>
  </n-scrollbar>
</template>

<script setup lang="ts">
import { NScrollbar, NEmpty, NTag, NButton, NIcon } from 'naive-ui'
import { CreateOutline, TrashOutline, CopyOutline } from '@vicons/ionicons5'
import type { PromptTemplate } from '../types'

defineProps<{
  templates: PromptTemplate[]
  readonly?: boolean
}>()

defineEmits<{
  (e: 'select', template: PromptTemplate): void
  (e: 'edit', template: PromptTemplate): void
  (e: 'delete', id: number): void
  (e: 'duplicate', id: number): void
}>()
</script>

<style scoped>
.template-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-item {
  padding: 12px;
  border-radius: 8px;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  background: #e8e8e8;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.template-name {
  font-weight: 500;
  font-size: 14px;
}

.template-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.template-content {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
  line-height: 1.4;
}

.template-meta {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
</style>
