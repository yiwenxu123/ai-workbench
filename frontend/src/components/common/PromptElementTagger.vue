<!--
  提示词元素可视化标签
  - 基于 usePromptParser 在本地实时拆解提示词
  - 显示已识别的元素类别（主体/风格/光影/色彩...）和数量
  - 不发起网络请求，性能可忽略
-->
<template>
  <div v-if="visibleStats.length > 0" class="prompt-element-tagger">
    <span class="tagger-hint">已识别</span>
    <span
      v-for="stat in visibleStats"
      :key="stat.category"
      class="tagger-chip"
      :style="{
        backgroundColor: stat.color + '15',
        borderColor: stat.color,
        color: stat.color,
      }"
      :title="`${stat.label}：识别到 ${stat.count} 个元素`"
    >
      <span class="chip-label">{{ stat.label }}</span>
      <span class="chip-count">{{ stat.count }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { usePromptParser } from '../../composables/usePromptParser'

const props = withDefaults(
  defineProps<{
    /** 监听的提示词文本 */
    prompt: string
    /** 至少多少字符才启用分析（避免空/极短文本闪烁） */
    minLength?: number
  }>(),
  { minLength: 2 }
)

const { prompt: promptRef, categoryStats } = usePromptParser()

// 把外部 prompt 同步进 composable（composable 内部 watch 会触发解析）
watch(
  () => props.prompt,
  (val) => {
    promptRef.value = val
  },
  { immediate: true }
)

const visibleStats = computed(() => {
  if (props.prompt.trim().length < props.minLength) return []
  return categoryStats.value
})
</script>

<style scoped>
.prompt-element-tagger {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.4;
}
.tagger-hint {
  color: var(--text-color-secondary, #64748b);
  margin-right: 2px;
  font-size: 11px;
  opacity: 0.7;
}
.tagger-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid;
  font-weight: 500;
  white-space: nowrap;
  transition: opacity 0.15s ease;
}
.tagger-chip:hover {
  opacity: 0.85;
}
.chip-label {
  font-size: 11px;
}
.chip-count {
  font-size: 10px;
  opacity: 0.7;
}
</style>
