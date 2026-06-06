<template>
  <div class="image-gallery">
    <n-space justify="space-between" class="mb-2">
      <n-input
        v-model:value="searchText"
        placeholder="搜索提示词..."
        clearable
        size="small"
        style="width: 150px"
      />
      <n-button size="small" quaternary @click="clearAll">
        清空全部
      </n-button>
    </n-space>

    <n-scrollbar style="max-height: 350px">
      <n-empty v-if="filteredItems.length === 0" description="暂无图片" />
      <n-grid :cols="2" :x-gap="8" :y-gap="8" v-else>
        <n-gi v-for="item in filteredItems" :key="item.id">
          <n-card size="small" hoverable class="image-card">
            <template #cover>
              <n-image
                :src="item.imageUrl"
                object-fit="cover"
                class="cover-image"
                preview-disabled
                @click="showPreview(item)"
              />
            </template>
            <div class="card-content">
              <n-ellipsis :line-clamp="1" class="prompt-text">
                {{ item.prompt }}
              </n-ellipsis>
              <n-space class="card-actions">
                <n-button size="tiny" @click="handleEdit(item)">
                  <template #icon><n-icon :component="Pencil" /></template>编辑
                </n-button>
                <n-button size="tiny" @click="handleConvertToVideo(item)">
                  <template #icon><n-icon :component="Film" /></template>视频
                </n-button>
                <n-button size="tiny" @click="toggleFavorite(item)">
                  <template #icon><n-icon :component="item.isFavorite ? Star : StarOff" /></template>
                </n-button>
                <n-button size="tiny" type="error" @click="handleDelete(item)">
                  删除
                </n-button>
              </n-space>
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
import { useHistoryStore } from '../../stores'
import { Pencil, Film, Star } from 'lucide-vue-next'
import type { History } from '../../types'

const StarOff = Star

const emit = defineEmits<{
  selectForVideo: [imageUrl: string, prompt: string]
  editImage: [imageUrl: string]
}>()

const historyStore = useHistoryStore()
const searchText = ref('')
const showPreviewModal = ref(false)
const previewItem = ref<History | null>(null)

const filteredItems = computed(() => {
  if (!searchText.value) return historyStore.items
  const search = searchText.value.toLowerCase()
  return historyStore.items.filter(item => 
    item.prompt.toLowerCase().includes(search)
  )
})

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

async function clearAll() {
  for (const item of historyStore.items) {
    await historyStore.remove(item.id!)
  }
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

.image-card {
  cursor: pointer;
}

.cover-image {
  width: 100%;
  height: 100px;
}

.card-content {
  padding: 4px 0;
}

.prompt-text {
  font-size: 12px;
  color: #666;
}

.card-actions {
  margin-top: 4px;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
