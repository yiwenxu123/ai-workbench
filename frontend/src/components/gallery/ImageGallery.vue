<template>
  <div class="image-gallery">
    <!-- 工具栏 -->
    <div class="gallery-toolbar">
      <n-input
        v-model:value="searchText"
        placeholder="搜索提示词..."
        clearable
        size="small"
        style="flex: 1"
      />
      <n-select
        v-model:value="filter"
        :options="filterOptions"
        size="small"
        style="width: 90px"
      />
      <n-button
        size="small"
        :type="selectMode ? 'primary' : 'default'"
        :quaternary="!selectMode"
        @click="toggleSelectMode"
      >
        {{ selectMode ? `已选 ${selectedIds.size}` : '多选' }}
      </n-button>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectMode && selectedIds.size > 0" class="batch-bar">
      <n-space size="small">
        <n-button size="tiny" @click="batchFavorite">
          <template #icon><n-icon :component="Star" /></template>
          收藏
        </n-button>
        <n-button size="tiny" type="error" @click="batchDelete">
          删除 ({{ selectedIds.size }})
        </n-button>
      </n-space>
      <n-button size="tiny" quaternary @click="selectedIds.clear()">取消选择</n-button>
    </div>

    <n-scrollbar style="max-height: 320px">
      <EmptyState v-if="filteredItems.length === 0" title="暂无图片" hint="使用左侧生成面板创作第一张图片" />
      <n-grid :cols="2" :x-gap="8" :y-gap="8" v-else>
        <n-gi v-for="item in filteredItems" :key="item.id">
          <n-card
            size="small"
            hoverable
            class="image-card"
            :class="{ selected: selectedIds.has(item.id!) }"
            @click="selectMode ? toggleSelect(item.id!) : showPreview(item)"
          >
            <template #cover>
              <div class="cover-wrapper">
                <n-image
                  :src="item.imageUrl"
                  object-fit="cover"
                  class="cover-image"
                  preview-disabled
                />
                <div v-if="selectMode" class="select-check">
                  <n-icon
                    :component="selectedIds.has(item.id!) ? CheckCircle : CircleOutline"
                    size="20"
                    :color="selectedIds.has(item.id!) ? '#4f7df3' : '#94a3b8'"
                  />
                </div>
                <div v-if="item.isFavorite" class="favorite-badge">
                  <n-icon :component="Star" size="12" color="#f59e0b" />
                </div>
              </div>
            </template>
            <div class="card-content">
              <n-ellipsis :line-clamp="1" class="prompt-text">
                {{ item.prompt }}
              </n-ellipsis>
              <div v-if="!selectMode" class="card-actions">
                <n-button size="tiny" quaternary @click.stop="handleEdit(item)">
                  <template #icon><n-icon :component="Pencil" size="12" /></template>
                </n-button>
                <n-button size="tiny" quaternary @click.stop="handleConvertToVideo(item)">
                  <template #icon><n-icon :component="Film" size="12" /></template>
                </n-button>
                <n-button size="tiny" quaternary @click.stop="toggleFavorite(item)">
                  <template #icon><n-icon :component="item.isFavorite ? Star : StarOff" size="12" /></template>
                </n-button>
                <n-button size="tiny" quaternary type="error" @click.stop="handleDelete(item)">
                  <template #icon><n-icon :component="TrashOutline" size="12" /></template>
                </n-button>
              </div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-scrollbar>

    <n-modal v-model:show="showPreviewModal" preset="card" style="width: 600px">
      <n-image :src="previewItem?.imageUrl" object-fit="contain" style="width: 100%" />
      <template #footer>
        <n-space justify="space-between">
          <n-ellipsis style="max-width: 400px">{{ previewItem?.prompt }}</n-ellipsis>
          <n-space>
            <n-button @click="downloadImage(previewItem)">下载</n-button>
            <n-button type="primary" @click="handleConvertToVideo(previewItem!)">
              转视频
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { Pencil, Film, Star, StarOff } from 'lucide-vue-next'
import { TrashOutline, CheckmarkCircleOutline as CheckCircle, EllipseOutline as CircleOutline } from '@vicons/ionicons5'
import { useHistoryStore } from '../../stores'
import EmptyState from '../common/EmptyState.vue'
import type { History } from '../../types'

const emit = defineEmits<{
  selectForVideo: [imageUrl: string, prompt: string]
  editImage: [imageUrl: string]
}>()

const message = useMessage()
const dialog = useDialog()
const historyStore = useHistoryStore()

const searchText = ref('')
const filter = ref<'all' | 'favorite' | 'today' | 'week'>('all')
const selectMode = ref(false)
const selectedIds = ref(new Set<number>())
const showPreviewModal = ref(false)
const previewItem = ref<History | null>(null)

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '收藏', value: 'favorite' },
  { label: '今天', value: 'today' },
  { label: '本周', value: 'week' },
]

const filteredItems = computed(() => {
  let items = historyStore.items

  // 时间筛选
  if (filter.value === 'favorite') {
    items = items.filter(i => i.isFavorite)
  } else if (filter.value === 'today') {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    items = items.filter(i => i.createdAt && new Date(i.createdAt) >= today)
  } else if (filter.value === 'week') {
    const weekAgo = new Date()
    weekAgo.setDate(weekAgo.getDate() - 7)
    items = items.filter(i => i.createdAt && new Date(i.createdAt) >= weekAgo)
  }

  // 搜索
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    items = items.filter(i => i.prompt.toLowerCase().includes(search))
  }

  return items
})

function toggleSelectMode() {
  selectMode.value = !selectMode.value
  if (!selectMode.value) selectedIds.value.clear()
}

function toggleSelect(id: number) {
  if (selectedIds.value.has(id)) {
    selectedIds.value.delete(id)
  } else {
    selectedIds.value.add(id)
  }
  // 触发响应式
  selectedIds.value = new Set(selectedIds.value)
}

function showPreview(item: History) {
  previewItem.value = item
  showPreviewModal.value = true
}

function handleConvertToVideo(item: History) {
  if (!item.imageUrl) return
  emit('selectForVideo', item.imageUrl, item.prompt)
}

function handleEdit(item: History) {
  if (!item.imageUrl) return
  emit('editImage', item.imageUrl)
}

async function toggleFavorite(item: History) {
  await historyStore.update(item.id!, { isFavorite: !item.isFavorite })
}

async function handleDelete(item: History) {
  await historyStore.remove(item.id!)
}

async function batchDelete() {
  const count = selectedIds.value.size
  dialog.warning({
    title: '批量删除',
    content: `确定删除选中的 ${count} 张图片？此操作不可撤销。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      for (const id of selectedIds.value) {
        await historyStore.remove(id)
      }
      selectedIds.value.clear()
      selectMode.value = false
      message.success(`已删除 ${count} 张图片`)
    },
  })
}

async function batchFavorite() {
  for (const id of selectedIds.value) {
    const item = historyStore.items.find(i => i.id === id)
    if (item && !item.isFavorite) {
      await historyStore.update(id, { isFavorite: true })
    }
  }
  message.success(`已收藏 ${selectedIds.value.size} 张图片`)
}

function downloadImage(item: History | null) {
  if (!item?.imageUrl) return
  const link = document.createElement('a')
  link.href = item.imageUrl
  link.download = `image_${item.id}.png`
  link.click()
}
</script>

<style scoped>
.image-gallery {
  width: 100%;
}

.gallery-toolbar {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-bottom: 8px;
}

.batch-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  margin-bottom: 8px;
  background: var(--brand-50, #f0f4ff);
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--brand-100, #e0e7ff);
}

.image-card {
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out);
}

.image-card.selected {
  border-color: var(--brand-500, #4f7df3);
  box-shadow: 0 0 0 1px var(--brand-500, #4f7df3);
}

.cover-wrapper {
  position: relative;
}

.cover-image {
  width: 100%;
  height: 100px;
}

.select-check {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favorite-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-content {
  padding: 4px 0;
}

.prompt-text {
  font-size: 12px;
  color: #666;
}

.card-actions {
  display: flex;
  gap: 2px;
  margin-top: 4px;
}
</style>
