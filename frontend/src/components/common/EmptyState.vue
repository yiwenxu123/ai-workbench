<template>
  <div class="empty-state">
    <div class="empty-illustration">
      <div class="empty-glow"></div>
      <slot name="icon">
        <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
          <defs>
            <linearGradient :id="gradId" x1="0" y1="0" x2="80" y2="80">
              <stop offset="0%" class="grad-stop-1"/>
              <stop offset="100%" class="grad-stop-2"/>
            </linearGradient>
          </defs>
          <rect x="12" y="24" width="56" height="40" rx="10" :stroke="`url(#${gradId})`" stroke-width="1.5" stroke-dasharray="4 4"/>
          <circle cx="30" cy="40" r="6" class="grad-stroke-1" stroke-width="1.5" fill="none"/>
          <polygon points="28,52 44,52 50,42 36,42" class="grad-stroke-2" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
        </svg>
      </slot>
    </div>
    <div class="empty-title">{{ title }}</div>
    <div v-if="hint" class="empty-hint">{{ hint }}</div>
    <div v-if="shortcut" class="empty-shortcut">
      <span class="shortcut-key">{{ shortcut.key }}</span>
      <span class="shortcut-label">{{ shortcut.label }}</span>
    </div>
    <div v-if="$slots.actions" class="empty-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineProps<{
  title: string
  hint?: string
  shortcut?: { key: string; label: string }
}>()

const gradId = computed(() => `emptyGrad_${Math.random().toString(36).slice(2, 8)}`)
</script>

<style scoped>
.empty-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
</style>
