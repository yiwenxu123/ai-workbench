<template>
  <div class="section-block">
    <div class="section-header">
      <n-icon :component="Image" class="section-icon" />
      <span class="section-title">图像生成</span>
      <n-tag v-if="providerStore.hasConfiguredImageProvider" type="success" size="small">已配置</n-tag>
      <n-tag v-if="configStore.isBackendConfigured('image')" type="info" size="small">已由后端配置</n-tag>
    </div>

    <!-- 后端已配置 Key → 隐藏手动配置 -->
    <template v-if="configStore.isBackendConfigured('image')">
      <n-alert type="success" size="small" class="mb-2">
        后端已配置图像生成 API Key，开发者无需在此处重复配置。
      </n-alert>
    </template>

    <!-- 后端未配置 → 显示手动配置界面 -->
    <template v-else>
      <n-alert type="info" size="small" class="mb-2">
        电商主图、海报、PPT 配图等图片生成任务，首次使用只需配置这一项。
      </n-alert>
      <ProviderManager />
    </template>
  </div>
</template>

<script setup lang="ts">
import { Image } from 'lucide-vue-next'
import { useProviderStore, useConfigStore } from '../../stores'
import ProviderManager from '../ProviderManager.vue'

const providerStore = useProviderStore()
const configStore = useConfigStore()
</script>

<style scoped>
.section-block {
  margin-bottom: 4px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.section-icon {
  font-size: 18px;
  color: var(--brand-500);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
