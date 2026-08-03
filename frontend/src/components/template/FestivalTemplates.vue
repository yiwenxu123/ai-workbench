<template>
  <div>
    <n-alert type="info" class="mb-3" :show-icon="false">
      <n-icon :component="Lightbulb" /> 当前推荐：<n-tag type="success">{{ currentFestivalName }}</n-tag>
    </n-alert>

    <n-grid :cols="4" :x-gap="8" :y-gap="8">
      <n-gi v-for="cat in festivalCategories" :key="cat.id">
        <n-card
          size="small"
          hoverable
          :class="{ 'category-selected': selectedFestival === cat.id }"
          @click="selectedFestival = cat.id as FestivalType"
        >
          <div class="festival-card" :style="{ borderColor: cat.color }">
            <n-icon :component="festivalIcons[cat.icon] || Lightbulb" class="festival-icon" />
            <span class="festival-name">{{ cat.name }}</span>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-collapse v-if="selectedFestivalTemplates.length > 0" class="mt-3">
      <n-collapse-item title="节庆模板" name="festival-templates">
        <n-list bordered>
          <n-list-item v-for="template in selectedFestivalTemplates" :key="template.id">
            <n-thing :title="template.title || template.name" :description="template.description">
              <template #avatar>
                <n-tag :color="{ color: (template.colorScheme || ['#E74C3C'])[0], textColor: '#fff' }" size="small">{{ template.festivalName || (template.tags || ['节日'])[0] }}</n-tag>
              </template>
              <template #action>
                <n-button size="small" type="primary" @click="applyFestivalTemplate(template)">使用</n-button>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-collapse-item>
    </n-collapse>

    <n-modal v-model:show="showModal" preset="card" :title="currentTemplate?.name" style="width: 600px">
      <n-alert type="info" class="mb-3">
        <template #header>配色方案</template>
        {{ (currentTemplate?.colorScheme || []).join(' / ') }}
      </n-alert>
      <n-form label-placement="left" label-width="80">
        <n-form-item label="品牌名"><n-input v-model:value="formValues.brandName" placeholder="输入品牌名称" /></n-form-item>
        <n-form-item label="Slogan"><n-input v-model:value="formValues.slogan" placeholder="输入品牌Slogan" /></n-form-item>
        <n-form-item label="产品"><n-input v-model:value="formValues.product" placeholder="输入产品名称" /></n-form-item>
      </n-form>
      <n-card size="small" title="生成预览" class="mt-3"><n-text>{{ generatedPrompt }}</n-text></n-card>
      <n-card size="small" title="小贴士" class="mt-3">
        <ul class="tips-list"><li v-for="(tip, index) in currentTemplate?.tips" :key="index">{{ tip }}</li></ul>
      </n-card>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="applyPrompt">应用到提示词</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Component } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore, useDataStore } from '../../stores'
import { Lightbulb, Gift, Lamp, Sparkles, Moon, Flag, ShoppingCart, TreePine } from 'lucide-vue-next'
import type { UnifiedTemplate } from '../../types/api'

const festivalIcons: Record<string, Component> = { Gift, Lantern: Lamp, Sparkles, Moon, Flag, ShoppingCart, TreePine }

const emit = defineEmits<{ select: [prompt: string] }>()
const message = useMessage()
const generatorStore = useGeneratorStore()
const dataStore = useDataStore()

type FestivalType = 'spring_festival' | 'lantern' | 'qingming' | 'labor' | 'dragon_boat' | 'mid_autumn' | 'national' | 'double_11' | 'christmas' | 'new_year'

const festivalDefs = [
  { id: 'spring_festival', name: '春节', icon: 'Gift', color: '#E74C3C' },
  { id: 'lantern', name: '元宵节', icon: 'Lantern', color: '#F39C12' },
  { id: 'dragon_boat', name: '端午节', icon: 'Sparkles', color: '#27AE60' },
  { id: 'mid_autumn', name: '中秋节', icon: 'Moon', color: '#3498DB' },
  { id: 'national', name: '国庆节', icon: 'Flag', color: '#E74C3C' },
  { id: 'double_11', name: '双十一', icon: 'ShoppingCart', color: '#9B59B6' },
  { id: 'christmas', name: '圣诞节', icon: 'TreePine', color: '#27AE60' },
  { id: 'new_year', name: '元旦', icon: 'Sparkles', color: '#3498DB' }
]

function getCurrentFestival(): FestivalType | null {
  const now = new Date(), month = now.getMonth() + 1, day = now.getDate()
  if (month === 1 && day >= 1 && day <= 15) return 'spring_festival'
  if (month === 1 && day >= 15 && day <= 20) return 'lantern'
  if (month === 6 && day >= 1 && day <= 10) return 'dragon_boat'
  if (month === 9 && day >= 15 && day <= 25) return 'mid_autumn'
  if (month === 10 && day >= 1 && day <= 7) return 'national'
  if (month === 11 && day >= 1 && day <= 15) return 'double_11'
  if (month === 12 && day >= 20 && day <= 26) return 'christmas'
  if (month === 12 && day >= 28) return 'new_year'
  return null
}

const selectedFestival = ref<FestivalType>(getCurrentFestival() || 'spring_festival')
const showModal = ref(false)
const currentTemplate = ref<UnifiedTemplate | null>(null)
const formValues = ref({ brandName: '', slogan: '', product: '' })

const festivalCategories = computed(() => {
  const festivals = new Set((dataStore.festivalTemplates || []).map((t) => t.festival))
  return festivalDefs.filter(c => festivals.has(c.id))
})

const selectedFestivalTemplates = computed(() =>
  (dataStore.festivalTemplates || []).filter((t) => t.festival === selectedFestival.value)
)

const currentFestivalName = computed(() => {
  const current = getCurrentFestival()
  const cat = festivalCategories.value.find(c => c.id === current)
  return cat ? cat.name : '春节'
})

const generatedPrompt = computed(() => {
  if (!currentTemplate.value) return ''
  let prompt = currentTemplate.value.promptTemplate
  const values: Record<string, string> = {}
  if (formValues.value.brandName) values['品牌名'] = formValues.value.brandName
  if (formValues.value.slogan) values['品牌Slogan'] = formValues.value.slogan
  if (formValues.value.product) values['产品名称'] = formValues.value.product
  for (const [key, value] of Object.entries(values)) {
    prompt = prompt.replace(`{${key}}`, value)
  }
  return prompt
})

function applyFestivalTemplate(template: UnifiedTemplate) {
  currentTemplate.value = template
  formValues.value = { brandName: '', slogan: '', product: '' }
  showModal.value = true
}

function applyPrompt() {
  if (!generatedPrompt.value) return
  generatorStore.prompt = generatedPrompt.value
  if (currentTemplate.value?.negativePrompt) generatorStore.negativePrompt = currentTemplate.value.negativePrompt
  message.success('节庆模板已应用')
  showModal.value = false
  emit('select', generatorStore.prompt)
}
</script>

<style scoped>
.festival-card { display: flex; flex-direction: column; align-items: center; gap: 4px; border-left: 3px solid; padding-left: 8px; }
.festival-icon { font-size: 22px; }
.festival-name { font-size: 11px; font-weight: 500; color: var(--gray-600); }
.category-selected { border: 2px solid var(--brand-500) !important; box-shadow: 0 0 0 3px rgba(79, 125, 243, 0.12) !important; }
.tips-list { margin: 0; padding-left: 16px; }
.tips-list li { margin: 4px 0; color: var(--gray-500); font-size: 13px; }
.mb-3 { margin-bottom: 12px; }
.mt-3 { margin-top: 12px; }
</style>
