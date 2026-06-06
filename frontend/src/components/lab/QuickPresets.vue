<template>
  <div class="quick-presets">
    <n-collapse>
      <n-collapse-item title="快捷预设" name="presets">
        <div class="preset-section">
          <div class="section-title">风格预设</div>
          <div class="preset-tags">
            <n-tag
              v-for="style in stylePresets"
              :key="style.value"
              size="small"
              class="preset-tag"
              @click="insertText(style.value)"
            >
              {{ style.label }}
            </n-tag>
          </div>
        </div>

        <div class="preset-section">
          <div class="section-title">画质关键词</div>
          <div class="preset-tags">
            <n-tag
              v-for="quality in qualityKeywords"
              :key="quality.value"
              size="small"
              class="preset-tag"
              @click="insertText(quality.value)"
            >
              {{ quality.label }}
            </n-tag>
          </div>
        </div>

        <div class="preset-section">
          <div class="section-title">光影效果</div>
          <div class="preset-tags">
            <n-tag
              v-for="light in lightingKeywords"
              :key="light.value"
              size="small"
              class="preset-tag"
              @click="insertText(light.value)"
            >
              {{ light.label }}
            </n-tag>
          </div>
        </div>
      </n-collapse-item>
    </n-collapse>
  </div>
</template>

<script setup lang="ts">
import { NCollapse, NCollapseItem, NTag } from 'naive-ui'
import { stylePresets, qualityKeywords, lightingKeywords } from '../../data/presets'

const emit = defineEmits<{
  (e: 'insert', text: string): void
}>()

function insertText(text: string) {
  emit('insert', text)
}
</script>

<style scoped>
.quick-presets {
  margin-top: 8px;
}

.preset-section {
  margin-bottom: 12px;
}

.section-title {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.preset-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.preset-tag:hover {
  opacity: 0.8;
  transform: scale(1.05);
}
</style>
