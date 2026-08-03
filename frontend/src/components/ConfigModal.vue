<template>
  <div class="config-modal">
    <n-modal v-model:show="configStore.showConfigModal" preset="card" style="width: 760px" title="配置创作能力">
      <div v-if="!hasAnyConfig" class="quick-start-banner mb-3">
        <n-alert type="info" :show-icon="false">
          <div class="quick-start-title">首次使用，先配置一个生成图片能力</div>
          <div class="quick-start-copy">
            选择一个平台预设，填入 API Key 保存。模型和 Endpoint 会自动带出，通常不用修改。
          </div>
        </n-alert>
      </div>

      <div class="config-layout">
        <ConfigSidebar :active-tab="activeTab" :cards="capabilityCards" @update:active-tab="activeTab = $event" />

        <div class="config-content-area">
          <div v-show="activeTab === 'generation'">
            <GenerationProviders />
            <n-divider />
            <VideoProviders @open-custom="openCustomProvider" />
            <n-divider />
            <EditProviders @open-custom="openCustomProvider" />
          </div>

          <div v-show="activeTab === 'ai'">
            <VisionProviders @open-custom="openCustomProvider" />
            <n-divider />
            <LLMProviders />
          </div>

          <div v-show="activeTab === 'advanced'">
            <AdminPanel />
          </div>
        </div>
      </div>
    </n-modal>

    <CustomProviderModal v-model:show="showCustomModal" :capability="customCapability" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NModal, NAlert, NDivider } from 'naive-ui'
import { useConfigStore, useProviderStore } from '../stores'
import { Image, Brain, Settings } from 'lucide-vue-next'
import type { ProviderCapability } from '../types/provider'

import ConfigSidebar from './config/ConfigSidebar.vue'
import type { CapabilityCard } from './config/ConfigSidebar.vue'
import GenerationProviders from './config/GenerationProviders.vue'
import VideoProviders from './config/VideoProviders.vue'
import EditProviders from './config/EditProviders.vue'
import LLMProviders from './config/LLMProviders.vue'
import VisionProviders from './config/VisionProviders.vue'
import AdminPanel from './config/AdminPanel.vue'
import CustomProviderModal from './config/CustomProviderModal.vue'

const configStore = useConfigStore()
const providerStore = useProviderStore()

const activeTab = ref('generation')

const hasAnyConfig = computed(() =>
  providerStore.hasConfiguredImageProvider ||
  providerStore.hasConfiguredVideoProvider ||
  providerStore.hasConfiguredEditProvider ||
  providerStore.hasConfiguredLLM ||
  configStore.isBackendConfigured('image') ||
  configStore.isBackendConfigured('video') ||
  configStore.isBackendConfigured('edit')
)

function capabilityStatus(cap: ProviderCapability): { ready: boolean; label: string; tagType: CapabilityCard['tagType'] } {
  const providers = providerStore.getProvidersByCapability(cap).filter(p => p.apiKey)
  if (providers.length === 0) return { ready: false, label: '未配置', tagType: 'default' }
  const allActive = providers.every(p => p.status === 'active')
  const anyError = providers.some(p => p.status === 'error')
  if (allActive) return { ready: true, label: '已连接', tagType: 'success' }
  if (anyError) return { ready: true, label: '有异常', tagType: 'error' }
  return { ready: true, label: '待检测', tagType: 'warning' }
}

const capabilityCards = computed<CapabilityCard[]>(() => {
  const genReady =
    providerStore.hasConfiguredImageProvider ||
    providerStore.hasConfiguredVideoProvider ||
    providerStore.hasConfiguredEditProvider ||
    configStore.isBackendConfigured('image') ||
    configStore.isBackendConfigured('video') ||
    configStore.isBackendConfigured('edit')
  const genStatus = capabilityStatus('image')
  const aiReady = providerStore.hasConfiguredLLM || providerStore.visionProviderPresets.some(p => providerStore.providers.find(vp => vp.type === p.type)?.apiKey)
  return [
    {
      tab: 'generation',
      icon: Image,
      title: '生成能力',
      desc: '图像 / 视频 / 编辑',
      ready: genReady,
      label: genReady ? genStatus.label : '未配置',
      tagType: genReady ? genStatus.tagType : 'default',
    },
    {
      tab: 'ai',
      icon: Brain,
      title: 'AI 能力',
      desc: '视觉分析 / 提示词优化',
      ready: aiReady,
      label: aiReady ? '已配置' : '未配置',
      tagType: aiReady ? 'success' : 'default',
    },
    {
      tab: 'advanced',
      icon: Settings,
      title: '高级设置',
      desc: '内容管理',
      ready: true,
      label: '',
      tagType: 'default',
    },
  ]
})

/* ── 自定义供应商 ── */
const showCustomModal = ref(false)
const customCapability = ref<'video' | 'edit' | 'vision'>('video')

function openCustomProvider(capability: 'video' | 'edit' | 'vision') {
  customCapability.value = capability
  showCustomModal.value = true
}
</script>

<style scoped>
.config-modal { height: 100%; }

.quick-start-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
}
.quick-start-copy {
  font-size: 13px;
  line-height: 1.7;
}

:deep(.quick-start-banner .n-alert) {
  background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%);
  border-color: #bbf7d0;
}

.config-layout {
  display: flex;
  gap: 20px;
  min-height: 480px;
}

.config-content-area {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}
</style>
