<template>
  <div class="video-gallery">
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
      <n-empty v-if="filteredItems.length === 0" description="暂无视频" />
      <n-grid :cols="2" :x-gap="8" :y-gap="8" v-else>
        <n-gi v-for="item in filteredItems" :key="item.id">
          <n-card size="small" hoverable class="video-card">
            <template #cover>
              <div class="video-cover" @click="playVideo(item)">
                <video
                  :src="item.videoUrl"
                  class="cover-video"
                  muted
                  @mouseenter="($event.target as HTMLVideoElement).play()"
                  @mouseleave="($event.target as HTMLVideoElement).pause()"
                />
                <div class="play-overlay">
                  <n-icon size="24"><PlayCircleOutline /></n-icon>
                </div>
              </div>
            </template>
            <div class="card-content">
              <n-ellipsis :line-clamp="1" class="prompt-text">
                {{ item.prompt }}
              </n-ellipsis>
              <n-space class="card-actions">
                <n-button size="tiny" @click="downloadVideo(item)">
                  下载
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

    <n-modal v-model:show="showVideoModal" preset="card" style="width: 700px">
      <video
        v-if="playingItem"
        :src="playingItem.videoUrl"
        controls
        autoplay
        style="width: 100%"
      />
      <template #footer>
        <n-space justify="space-between">
          <n-ellipsis style="max-width: 400px">{{ playingItem?.prompt }}</n-ellipsis>
          <n-button @click="downloadVideo(playingItem)">下载</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { PlayCircleOutline } from '@vicons/ionicons5'
import { db } from '../../db'
import type { VideoHistory } from '../../types/db'

const searchText = ref('')
const showVideoModal = ref(false)
const playingItem = ref<VideoHistory | null>(null)
const videos = ref<VideoHistory[]>([])

const filteredItems = computed(() => {
  if (!searchText.value) return videos.value
  const search = searchText.value.toLowerCase()
  return videos.value.filter(item => 
    item.prompt.toLowerCase().includes(search)
  )
})

async function loadVideos() {
  const allVideos = await db.videoHistory.orderBy('createdAt').reverse().toArray()
  videos.value = allVideos.filter(v => v.videoUrl)
}

function playVideo(item: VideoHistory) {
  if (!item.videoUrl) return
  playingItem.value = item
  showVideoModal.value = true
}

async function handleDelete(item: VideoHistory) {
  await db.videoHistory.delete(item.id!)
  await loadVideos()
}

async function clearAll() {
  await db.videoHistory.clear()
  videos.value = []
}

function downloadVideo(item: VideoHistory | null) {
  if (!item?.videoUrl) return
  const link = document.createElement('a')
  link.href = item.videoUrl
  link.download = `video_${item.id}.mp4`
  link.click()
}

onMounted(() => {
  loadVideos()
})
</script>

<style scoped>
.video-gallery {
  width: 100%;
}

.video-card {
  cursor: pointer;
}

.video-cover {
  position: relative;
  width: 100%;
  height: 100px;
  overflow: hidden;
}

.cover-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  opacity: 0.8;
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
