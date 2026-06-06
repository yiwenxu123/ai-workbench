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
import { useDataStore } from '../../stores'

const negativePromptCategories = [
  { value: 'quality', label: '质量优化', icon: 'Sparkles' },
  { value: 'style', label: '风格净化', icon: 'Palette' },
  { value: 'composition', label: '构图优化', icon: 'Ruler' },
  { value: 'scene', label: '场景专用', icon: 'Film' },
  { value: 'custom', label: '自定义', icon: 'Settings' }
]

const quickNegativePresets = [
  {
    name: '高质量写实',
    packIds: ['neg-general', 'neg-realistic'],
    description: '适合需要真实照片效果的场景'
  },
  {
    name: '产品电商',
    packIds: ['neg-general', 'neg-ecommerce', 'neg-composition'],
    description: '适合电商产品图生成'
  },
  {
    name: '人物肖像',
    packIds: ['neg-general', 'neg-portrait', 'neg-realistic'],
    description: '适合人物肖像生成'
  },
  {
    name: '视频生成',
    packIds: ['neg-general', 'neg-video'],
    description: '适合视频生成场景'
  }
]

const emit = defineEmits<{
  apply: [negativePrompt: string]
}>()

const dataStore = useDataStore()

const selectedCategory = ref('all')
const selectedPacks = reactive<Record<string, boolean>>({})

const CATEGORY_MAP: Record<string, string> = {
  general: 'quality', portrait: 'style', composition: 'composition',
  ecommerce: 'scene', video: 'scene', style: 'style', quality: 'quality',
}

const storePacks = computed(() => {
  return dataStore.negativePacks.map((p: any) => ({
    id: p.id,
    name: p.title,
    description: p.content,
    prompts: typeof p.negative_prompt === 'string' && p.negative_prompt
      ? p.negative_prompt.split(',').map((s: string) => s.trim()).filter(Boolean)
      : [],
    category: CATEGORY_MAP[p.category] || 'custom',
    isDefault: p.category === 'general',
  }))
})

// Select default packs after store loads
dataStore.$subscribe(() => {
  storePacks.value.forEach(pack => {
    if (pack.isDefault && !(pack.id in selectedPacks)) {
      selectedPacks[pack.id] = true
    }
  })
})

const filteredPacks = computed(() => {
  if (selectedCategory.value === 'all') {
    return storePacks.value
  }
  return storePacks.value.filter(p => p.category === selectedCategory.value)
})

const selectedCount = computed(() => {
  return Object.values(selectedPacks).filter(Boolean).length
})

function mergePromptsByIds(ids: string[]): string {
  const prompts = new Set<string>()
  ids.forEach(id => {
    const pack = storePacks.value.find((p: any) => p.id === id)
    if (pack) {
      pack.prompts.forEach((p: string) => prompts.add(p))
    }
  })
  return Array.from(prompts).join(', ')
}

function updateSelection() {
}

function applySelected() {
  const packIds = Object.entries(selectedPacks)
    .filter(([_, checked]) => checked)
    .map(([id]) => id)
  emit('apply', mergePromptsByIds(packIds))
}

function applyPreset(preset: typeof quickNegativePresets[0]) {
  emit('apply', mergePromptsByIds(preset.packIds))
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
