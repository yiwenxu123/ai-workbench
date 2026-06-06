<template>
  <div class="gallery-panel">
    <n-tabs v-model:value="activeTab" type="line" size="small">
      <n-tab-pane name="images">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Image" />
            <span>图片</span>
          </n-space>
        </template>
        <ImageGallery @select-for-video="handleSelectForVideo" @edit-image="handleEditImage" />
      </n-tab-pane>
      <n-tab-pane name="videos">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Film" />
            <span>视频</span>
          </n-space>
        </template>
        <VideoGallery />
      </n-tab-pane>
      <n-tab-pane name="favorites">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Star" />
            <span>收藏</span>
          </n-space>
        </template>
        <FavoriteGallery @select-for-video="handleSelectForVideo" />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import ImageGallery from './gallery/ImageGallery.vue'
import VideoGallery from './gallery/VideoGallery.vue'
import FavoriteGallery from './gallery/FavoriteGallery.vue'
import { useVideoStore } from '../stores/video'
import { Image, Film, Star } from 'lucide-vue-next'

const emit = defineEmits<{
  convertToVideo: [imageUrl: string, prompt: string]
  editImage: [imageUrl: string]
}>()

const message = useMessage()
const videoStore = useVideoStore()
const activeTab = ref('images')

function handleSelectForVideo(imageUrl: string, prompt: string) {
  videoStore.sourceImage = imageUrl
  videoStore.prompt = convertPromptToVideo(prompt)
  message.success('已添加到视频生成，请切换到视频生成页面')
  emit('convertToVideo', imageUrl, prompt)
}

function handleEditImage(imageUrl: string) {
  emit('editImage', imageUrl)
}

function convertPromptToVideo(imagePrompt: string): string {
  let videoPrompt = imagePrompt
  
  videoPrompt = videoPrompt.replace(/4K|8K|高清|超高清/g, '')
  videoPrompt = videoPrompt.replace(/静态|静止|照片|图片/g, '')
  
  videoPrompt = videoPrompt + '，动态画面，镜头缓慢推进'
  
  return videoPrompt.trim()
}
</script>

<style scoped>
.gallery-panel {
  width: 100%;
  height: 100%;
}
</style>
