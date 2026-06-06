<template>
  <div class="negative-prompt-panel">
    <n-alert type="info" class="mb-2" :show-icon="false">
      选择负面词包，一键应用到生成面板
    </n-alert>

    <n-space class="mb-2">
      <n-tag
        size="small"
        :type="selectedCategory === 'all' ? 'primary' : 'default'"
        @click="selectedCategory = 'all'"
      >
        全部
      </n-tag>
      <n-tag
        v-for="cat in negativePromptCategories"
        :key="cat.value"
        size="small"
        :type="selectedCategory === cat.value ? 'primary' : 'default'"
        @click="selectedCategory = cat.value"
      >
        {{ cat.icon }} {{ cat.label }}
      </n-tag>
    </n-space>

    <n-divider>快捷预设</n-divider>
    
    <n-grid :cols="1" :x-gap="8" :y-gap="8" class="mb-2">
      <n-gi v-for="preset in quickNegativePresets" :key="preset.name">
        <n-card size="small" hoverable @click="applyPreset(preset)">
          <div class="preset-card">
            <div class="preset-name">{{ preset.name }}</div>
            <div class="preset-desc">{{ preset.description }}</div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-divider>负面词包</n-divider>

    <n-list bordered>
      <n-list-item v-for="pack in filteredPacks" :key="pack.id">
        <template #prefix>
          <n-checkbox
            v-model:checked="selectedPacks[pack.id]"
            @update:checked="updateSelection"
          />
        </template>
        <n-thing :title="pack.name" :description="pack.description">
          <template #header-extra>
            <n-tag v-if="pack.isDefault" size="tiny" type="success">默认</n-tag>
          </template>
          <n-ellipsis :line-clamp="2" class="pack-prompts">
            {{ pack.prompts.slice(0, 5).join(', ') }}...
          </n-ellipsis>
        </n-thing>
      </n-list-item>
    </n-list>

    <div class="action-bar">
      <n-button type="primary" size="small" @click="applySelected" :disabled="selectedCount === 0">
        应用选中 ({{ selectedCount }}个词包)
      </n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { negativePromptPacks, negativePromptCategories, quickNegativePresets, mergePrompts } from '../../data/negativePrompts'

const emit = defineEmits<{
  apply: [negativePrompt: string]
}>()

const selectedCategory = ref('all')
const selectedPacks = reactive<Record<string, boolean>>({})

negativePromptPacks.forEach(pack => {
  if (pack.isDefault) {
    selectedPacks[pack.id] = true
  }
})

const filteredPacks = computed(() => {
  if (selectedCategory.value === 'all') {
    return negativePromptPacks
  }
  return negativePromptPacks.filter(p => p.category === selectedCategory.value)
})

const selectedCount = computed(() => {
  return Object.values(selectedPacks).filter(Boolean).length
})

function updateSelection() {
}

function applySelected() {
  const packIds = Object.entries(selectedPacks)
    .filter(([_, checked]) => checked)
    .map(([id]) => id)
  
  const mergedPrompt = mergePrompts(packIds)
  emit('apply', mergedPrompt)
}

function applyPreset(preset: typeof quickNegativePresets[0]) {
  const mergedPrompt = mergePrompts(preset.packs)
  emit('apply', mergedPrompt)
}
</script>

<style scoped>
.negative-prompt-panel {
  padding: 8px 0;
}

.preset-card {
  cursor: pointer;
}

.preset-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.preset-desc {
  font-size: 12px;
  color: #888;
}

.pack-prompts {
  font-size: 12px;
  color: #666;
}

.action-bar {
  margin-top: 12px;
  text-align: center;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
