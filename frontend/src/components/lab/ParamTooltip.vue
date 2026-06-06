<template>
  <n-tooltip trigger="hover" placement="top">
    <template #trigger>
      <slot />
    </template>
    <div class="param-tooltip">
      <div class="tooltip-title">{{ config.name }}</div>
      <div class="tooltip-desc">{{ config.description }}</div>
      <div class="tooltip-presets" v-if="showPresets">
        <div class="presets-title">快捷预设：</div>
        <div class="presets-list">
          <div
            v-for="preset in config.presets"
            :key="preset.value"
            class="preset-item"
            @click="selectPreset(preset)"
          >
            <span class="preset-label">{{ preset.label }}</span>
            <span class="preset-desc">{{ preset.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </n-tooltip>
</template>

<script setup lang="ts">
import { NTooltip } from 'naive-ui'
import type { ParamConfig, ParamPreset } from '../../data/presets'

defineProps<{
  config: ParamConfig
  showPresets?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', preset: ParamPreset): void
}>()

function selectPreset(preset: ParamPreset) {
  emit('select', preset)
}
</script>

<style scoped>
.param-tooltip {
  max-width: 300px;
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.tooltip-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.tooltip-presets {
  border-top: 1px solid #e8e8e8;
  padding-top: 8px;
}

.presets-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
}

.presets-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preset-item {
  padding: 6px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.preset-item:hover {
  background: #e6f7ff;
}

.preset-label {
  font-weight: 500;
  font-size: 12px;
  display: block;
}

.preset-desc {
  font-size: 11px;
  color: #666;
}
</style>
