<template>
  <div class="favorite-gallery">
    <n-scrollbar style="max-height: 350px">
      <n-empty v-if="favorites.length === 0" description="暂无收藏" />
      <n-grid :cols="2" :x-gap="8" :y-gap="8" v-else>
        <n-gi v-for="item in favorites" :key="item.id">
          <n-card size="small" hoverable class="favorite-card">
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
                <n-button size="tiny" @click="handleConvertToVideo(item)">
                  转视频
                </n-button>
                <n-button size="tiny" @click="toggleFavorite(item)">
                  取消收藏
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
import type { History } from '../../types'

const emit = defineEmits<{
  selectForVideo: [imageUrl: string, prompt: string]
}>()

const historyStore = useHistoryStore()
const showPreviewModal = ref(false)
const previewItem = ref<History | null>(null)

const favorites = computed(() => historyStore.favorites)

function showPreview(item: History) {
  previewItem.value = item
  showPreviewModal.value = true
}

function handleConvertToVideo(item: History) {
  if (!item.imageUrl) return
  emit('selectForVideo', item.imageUrl, item.prompt)
}

async function toggleFavorite(item: History) {
  await historyStore.update(item.id!, { isFavorite: !item.isFavorite })
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
.favorite-gallery {
  width: 100%;
}

.favorite-card {
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
</style>
