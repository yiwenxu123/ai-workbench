<template>
  <div>
    <n-grid :cols="4" :x-gap="8" :y-gap="8">
      <n-gi v-for="cat in formulaCategories" :key="cat.id">
        <n-card
          size="small"
          hoverable
          :class="{ 'category-selected': selectedCategory === cat.id }"
          @click="selectedCategory = cat.id"
        >
          <div class="formula-card">
            <n-icon :component="cat.icon" class="formula-icon" />
            <span class="formula-name">{{ cat.name }}</span>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-collapse v-if="selectedFormulas.length > 0" class="mt-3">
      <n-collapse-item title="公式列表" name="formulas">
        <n-list bordered>
          <n-list-item v-for="formula in selectedFormulas" :key="formula.id">
            <n-thing :title="formula.name" :description="formula.description">
              <template #action>
                <n-button size="small" type="primary" @click="showBuilder(formula)">使用公式</n-button>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-collapse-item>
    </n-collapse>

    <n-modal v-model:show="showModal" preset="card" :title="currentFormula?.name" style="width: 600px">
      <n-form label-placement="left" label-width="80">
        <n-form-item v-for="part in currentFormula?.structure" :key="part.key" :label="part.label" :required="part.required">
          <n-select v-if="part.options" v-model:value="formValues[part.key]" :options="part.options.map(o => ({ label: o, value: o }))" :placeholder="part.placeholder" clearable />
          <n-input v-else v-model:value="formValues[part.key]" :placeholder="part.placeholder" />
        </n-form-item>
      </n-form>
      <n-card size="small" title="生成预览" class="mt-3"><n-text>{{ generatedPrompt }}</n-text></n-card>
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
import { useMessage } from 'naive-ui'
import { useGeneratorStore, useDataStore } from '../../stores'
import { FileText, User, Package, Mountain, Landmark, UtensilsCrossed, Palette, Lightbulb } from 'lucide-vue-next'

const emit = defineEmits<{ select: [prompt: string] }>()
const message = useMessage()
const generatorStore = useGeneratorStore()
const dataStore = useDataStore()

interface PromptFormula {
  id: string; name: string; category: string; description: string
  structure: { key: string; label: string; description: string; required: boolean; options?: string[]; placeholder: string }[]
  example: string; tips: string[]
}

const categoryDefs = [
  { id: '基础', name: '基础公式', icon: FileText },
  { id: '人物', name: '人物肖像', icon: User },
  { id: '商业', name: '商业产品', icon: Package },
  { id: '风景', name: '风景场景', icon: Mountain },
  { id: '建筑', name: '建筑设计', icon: Landmark },
  { id: '美食', name: '美食摄影', icon: UtensilsCrossed },
  { id: '动漫', name: '动漫角色', icon: Palette },
  { id: '概念', name: '概念艺术', icon: Lightbulb }
]

const selectedCategory = ref('基础')
const showModal = ref(false)
const currentFormula = ref<PromptFormula | null>(null)
const formValues = ref<Record<string, string>>({})

function parseJsonArray(val: any): any[] {
  if (Array.isArray(val)) return val
  if (typeof val === 'string' && val) { try { const p = JSON.parse(val); return Array.isArray(p) ? p : [] } catch { return [] } }
  return []
}

function extractStructure(content: string) {
  if (!content) return []
  const match = content.match(/公式[：:](.+)/)
  let parts: string[] = []
  if (match?.[1]) parts = match[1].split('+').map(s => s.trim()).filter(Boolean)
  else if (content.includes('+')) parts = content.split('+').map(s => s.trim()).filter(Boolean)
  return parts.map((p, i) => ({ key: `part${i}`, label: p, description: p, required: i < 3, placeholder: `请输入${p}` }))
}

const formulas = computed<PromptFormula[]>(() =>
  (dataStore.formulas || []).map((f: any) => ({
    id: f.id, name: f.title, category: f.category, description: f.content,
    structure: extractStructure(f.content || ''),
    example: parseJsonArray(f.examples)[0] || '',
    tips: parseJsonArray(f.tips),
  }))
)

const formulaCategories = computed(() => {
  const cats = new Set(formulas.value.map(f => f.category))
  return categoryDefs.filter(c => cats.has(c.id))
})

const selectedFormulas = computed(() => formulas.value.filter(f => f.category === selectedCategory.value))

const generatedPrompt = computed(() => {
  if (!currentFormula.value) return ''
  const parts: string[] = []
  for (const part of currentFormula.value.structure) {
    const value = formValues.value[part.key]
    if (value) parts.push(value)
  }
  return parts.join('，')
})

function showBuilder(formula: PromptFormula) {
  currentFormula.value = formula
  formValues.value = {}
  showModal.value = true
}

function applyPrompt() {
  if (!generatedPrompt.value) return
  generatorStore.prompt = generatedPrompt.value
  message.success('公式已应用')
  showModal.value = false
  emit('select', generatorStore.prompt)
}
</script>

<style scoped>
.formula-card { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.formula-icon { font-size: 22px; }
.formula-name { font-size: 11px; font-weight: 500; color: var(--gray-600); }
.category-selected { border: 2px solid var(--brand-500) !important; box-shadow: 0 0 0 3px rgba(79, 125, 243, 0.12) !important; }
.mt-3 { margin-top: 12px; }
</style>
