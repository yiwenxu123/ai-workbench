<template>
  <div class="config-sidebar">
    <button
      v-for="item in cards"
      :key="item.tab"
      type="button"
      class="sidebar-item"
      :class="{ active: activeTab === item.tab, ready: item.ready }"
      @click="$emit('update:activeTab', item.tab)"
    >
      <div class="sidebar-item-content">
        <n-icon :component="item.icon" class="capability-icon" />
        <div class="capability-text">
          <span class="capability-title">{{ item.title }}</span>
          <span class="capability-desc">{{ item.desc }}</span>
        </div>
      </div>
      <n-tag :type="item.tagType || (item.ready ? 'success' : 'default')" size="small" class="sidebar-tag">
        {{ item.label || (item.ready ? '已配置' : '未配置') }}
      </n-tag>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { NIcon, NTag } from 'naive-ui'

export interface CapabilityCard {
  tab: string
  icon: Component
  title: string
  desc: string
  ready: boolean
  label: string
  tagType: 'success' | 'error' | 'warning' | 'default'
}

defineProps<{
  activeTab: string
  cards: CapabilityCard[]
}>()

defineEmits<{
  'update:activeTab': [value: string]
}>()
</script>

<style scoped>
.config-sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-right: 1px solid var(--border);
  padding-right: 16px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
}
.sidebar-item:hover {
  background: var(--bg-subtle);
}
.sidebar-item.active {
  background: var(--brand-50);
  border-color: var(--brand-200);
}

.sidebar-item-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.capability-icon {
  font-size: 20px;
  margin-top: 2px;
}

.capability-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.capability-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.sidebar-item.active .capability-title {
  color: var(--brand-600);
}

.capability-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.sidebar-tag {
  flex-shrink: 0;
}
</style>
