<template>
  <div class="template-center">
    <n-tabs v-model:value="activeCategory" type="line" animated>
      <n-tab-pane name="quick" tab="场景模板">
        <SceneTemplates @select="onSelect" />
      </n-tab-pane>
      <n-tab-pane name="festival" tab="节庆营销">
        <FestivalTemplates @select="onSelect" />
      </n-tab-pane>
      <n-tab-pane name="mine" tab="我的模板">
        <MyTemplates @select="onSelect" />
      </n-tab-pane>
      <n-tab-pane name="formula" tab="提示词公式">
        <FormulaTemplates @select="onSelect" />
      </n-tab-pane>
      <n-tab-pane name="keywords" tab="关键词库">
        <KeywordLibrary />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent } from 'vue'

const SceneTemplates = defineAsyncComponent(() => import('./template/SceneTemplates.vue'))
const FestivalTemplates = defineAsyncComponent(() => import('./template/FestivalTemplates.vue'))
const MyTemplates = defineAsyncComponent(() => import('./template/MyTemplates.vue'))
const FormulaTemplates = defineAsyncComponent(() => import('./template/FormulaTemplates.vue'))
const KeywordLibrary = defineAsyncComponent(() => import('./template/KeywordLibrary.vue'))

const emit = defineEmits<{
  select: [prompt: string]
}>()

const activeCategory = ref('quick')

function onSelect(prompt: string) {
  emit('select', prompt)
}
</script>

<style scoped>
.template-center { width: 100%; }
</style>
