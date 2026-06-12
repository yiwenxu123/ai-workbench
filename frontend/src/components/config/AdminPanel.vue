<template>
  <n-card size="small" title="内容管理" class="mb-3">
    <n-space vertical>
      <n-space align="center" justify="space-between">
        <n-text>启用 AI 内容入库</n-text>
        <n-switch v-model:value="adminModeEnabled" @update:value="toggleAdminMode" />
      </n-space>
      <n-text depth="3" style="font-size: 13px">
        开启后右侧面板将显示"入库"标签，支持从网页链接或粘贴文本中 AI 提取案例、知识库条目和模板。
      </n-text>
    </n-space>
  </n-card>

  <n-card v-if="!providerStore.hasConfiguredLLM" size="small">
    <template #header>
      <n-space align="center" :size="4">
        <n-icon :component="AlertTriangle" />
        <span>前提条件</span>
      </n-space>
    </template>
    <n-text depth="3">
      内容入库需要配置大语言模型（LLM）才能使用。请在「AI 能力」中先配置一个 LLM 供应商。
    </n-text>
  </n-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NSpace, NText, NSwitch, NIcon, useMessage } from 'naive-ui'
import { useProviderStore } from '../../stores'
import { AlertTriangle } from 'lucide-vue-next'

const message = useMessage()
const providerStore = useProviderStore()

const adminModeEnabled = ref(localStorage.getItem('ai_studio_admin') === 'true')
function toggleAdminMode(val: boolean) {
  localStorage.setItem('ai_studio_admin', String(val))
  adminModeEnabled.value = val
  if (val) message.success('内容管理已开启，右侧面板将显示"入库"标签')
  else message.info('内容管理已关闭')
}
</script>
