<template>
  <div class="knowledge-base">
    <n-tabs v-model:value="activeTab" type="line" size="small" animated>
      <n-tab-pane name="cases">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="BookOpen" />
            <span>案例库</span>
          </n-space>
        </template>
        <CaseLibraryPanel @use-case="handleUseCase" />
      </n-tab-pane>
      <n-tab-pane name="terms">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Library" />
            <span>术语词典</span>
          </n-space>
        </template>
        <TermDictionaryPanel @insert="handleInsert" />
      </n-tab-pane>
      <n-tab-pane name="shots">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Film" />
            <span>镜头语言</span>
          </n-space>
        </template>
        <ShotLanguagePanel @insert="handleInsert" />
      </n-tab-pane>
      <n-tab-pane name="templates">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="FileText" />
            <span>提示词模板</span>
          </n-space>
        </template>
        <PromptTemplatePanel @insert="handleInsert" />
      </n-tab-pane>
      <n-tab-pane name="negative">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Ban" />
            <span>负面词包</span>
          </n-space>
        </template>
        <NegativePromptPanel @apply="handleApplyNegative" />
      </n-tab-pane>
      <n-tab-pane name="industry">
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="Building2" />
            <span>行业知识</span>
          </n-space>
        </template>
        <IndustryKnowledgePanel />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore } from '../stores'
import { BookOpen, Library, Building2, Film, FileText, Ban } from 'lucide-vue-next'
import TermDictionaryPanel from './knowledge/TermDictionaryPanel.vue'
import ShotLanguagePanel from './knowledge/ShotLanguagePanel.vue'
import PromptTemplatePanel from './knowledge/PromptTemplatePanel.vue'
import NegativePromptPanel from './knowledge/NegativePromptPanel.vue'
import IndustryKnowledgePanel from './knowledge/IndustryKnowledgePanel.vue'
import CaseLibraryPanel from './knowledge/CaseLibraryPanel.vue'
import type { CaseExample } from '../data/caseLibrary'

const emit = defineEmits<{
  insert: [keyword: string]
}>()

const message = useMessage()
const generatorStore = useGeneratorStore()
const activeTab = ref('terms')

function handleInsert(keyword: string) {
  const current = generatorStore.prompt
  if (current && !current.endsWith(' ') && !current.endsWith(',')) {
    generatorStore.prompt = current + ', ' + keyword
  } else {
    generatorStore.prompt = current + ' ' + keyword
  }
  message.success(`已插入: ${keyword}`)
  emit('insert', keyword)
}

function handleApplyNegative(negativePrompt: string) {
  generatorStore.negativePrompt = negativePrompt
  message.success('负面提示词已应用')
}

function handleUseCase(caseExample: CaseExample) {
  generatorStore.prompt = caseExample.prompt
  if (caseExample.negativePrompt) {
    generatorStore.negativePrompt = caseExample.negativePrompt
  }
  message.success('案例提示词已应用')
}
</script>

<style scoped>
.knowledge-base {
  width: 100%;
  height: 100%;
}
</style>
