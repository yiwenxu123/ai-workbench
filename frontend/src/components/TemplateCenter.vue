<template>
  <div class="template-center">
    <n-tabs v-model:value="activeCategory" type="line" animated>
      <n-tab-pane name="quick" tab="场景模板">
        <n-grid :cols="3" :x-gap="8" :y-gap="8">
          <n-gi v-for="cat in sceneCategories" :key="cat.id">
            <n-card
              size="small"
              hoverable
              class="category-card"
              :class="{ 'category-selected': selectedSceneCategory === cat.id }"
              @click="selectSceneCategory(cat.id)"
            >
              <div class="category-content">
                <n-icon :component="cat.icon" class="category-icon" />
                <span class="category-name">{{ cat.name }}</span>
              </div>
            </n-card>
          </n-gi>
        </n-grid>

        <n-collapse v-if="selectedSceneCategory" class="mt-3">
          <n-collapse-item title="选择模板" name="templates">
            <n-list bordered>
              <n-list-item v-for="template in filteredTemplates" :key="template.id">
                <n-thing :title="template.name" :description="template.description">
                  <template #avatar>
                    <n-tag type="info" size="small">{{ template.type === 'image' ? '图' : '视频' }}</n-tag>
                  </template>
                  <template #action>
                    <n-button size="small" type="primary" @click="applyTemplate(template)">
                      使用
                    </n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-collapse-item>
        </n-collapse>
      </n-tab-pane>

      <n-tab-pane name="festival" tab="节庆营销">
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
                <n-icon :component="getLucideIconComponent(cat.icon)" class="festival-icon" />
                <span class="festival-name">{{ cat.name }}</span>
              </div>
            </n-card>
          </n-gi>
        </n-grid>

        <n-collapse v-if="selectedFestivalTemplates.length > 0" class="mt-3">
          <n-collapse-item title="节庆模板" name="festival-templates">
            <n-list bordered>
              <n-list-item v-for="template in selectedFestivalTemplates" :key="template.id">
                <n-thing :title="template.name" :description="template.description">
                  <template #avatar>
                    <n-tag :color="{ color: template.colorScheme[0], textColor: '#fff' }" size="small">
                      {{ template.festivalName }}
                    </n-tag>
                  </template>
                  <template #action>
                    <n-button size="small" type="primary" @click="applyFestivalTemplate(template)">
                      使用
                    </n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-collapse-item>
        </n-collapse>
      </n-tab-pane>

      <n-tab-pane name="mine" tab="我的模板">
        <n-space justify="space-between" class="mb-3">
          <n-input
            v-model:value="myTemplateSearch"
            placeholder="搜索我的模板..."
            clearable
            size="small"
            style="width: 200px"
          />
          <n-button type="primary" size="small" @click="showMyTemplateModal = true; editingTemplate = null; myTemplateForm = { name: '', description: '', category: 'social', promptTemplate: '', negativePrompt: '', size: '1024x1024', model: 'doubao-seedream-4-5-251128', tags: [] }">
            + 新建模板
          </n-button>
        </n-space>

        <n-space class="mb-3">
          <n-tag
            v-for="cat in myCategories"
            :key="cat.value"
            size="small"
            :type="selectedMyCategory === cat.value ? 'primary' : 'default'"
            @click="selectedMyCategory = cat.value"
          >
            {{ cat.label }}
          </n-tag>
        </n-space>

        <n-scrollbar style="max-height: 300px">
          <n-empty v-if="filteredMyTemplates.length === 0" description="暂无模板，点击上方新建" />
          <n-list bordered v-else>
            <n-list-item v-for="template in filteredMyTemplates" :key="template.id">
              <n-thing :title="template.name" :description="template.description">
                <template #avatar>
                  <n-tag size="small">{{ getCategoryLabel(template.category) }}</n-tag>
                </template>
                <template #action>
                  <n-space>
                    <n-button size="small" type="primary" @click="applyMyTemplate(template)">
                      使用
                    </n-button>
                    <n-button size="small" @click="editMyTemplate(template)">
                      编辑
                    </n-button>
                    <n-button size="small" type="error" @click="deleteMyTemplate(template)">
                      删除
                    </n-button>
                  </n-space>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-scrollbar>
      </n-tab-pane>

      <n-tab-pane name="formula" tab="提示词公式">
        <n-grid :cols="4" :x-gap="8" :y-gap="8">
          <n-gi v-for="cat in formulaCategories" :key="cat.id">
            <n-card
              size="small"
              hoverable
              :class="{ 'category-selected': selectedFormulaCategory === cat.id }"
              @click="selectedFormulaCategory = cat.id"
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
                    <n-button size="small" type="primary" @click="showFormulaBuilder(formula)">
                      使用公式
                    </n-button>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-collapse-item>
        </n-collapse>
      </n-tab-pane>

      <n-tab-pane name="keywords" tab="关键词库">
        <n-card size="small" title="风格代码" class="mb-3">
          <n-space wrap>
            <n-tag
              v-for="style in quickStyleCodes"
              :key="style.code"
              round
              type="info"
              class="clickable-tag"
              @click="insertCode(style.code)"
            >
              {{ style.name }}
            </n-tag>
          </n-space>
        </n-card>

        <n-card size="small" title="质量关键词" class="mb-3">
          <n-space wrap>
            <n-tag
              v-for="quality in qualityKeywords"
              :key="quality.code"
              round
              type="success"
              class="clickable-tag"
              @click="insertCode(quality.code)"
            >
              {{ quality.name }}
            </n-tag>
          </n-space>
        </n-card>

        <n-card size="small" title="光线关键词">
          <n-space wrap>
            <n-tag
              v-for="light in lightingKeywords"
              :key="light.code"
              round
              type="warning"
              class="clickable-tag"
              @click="insertCode(light.code)"
            >
              {{ light.name }}
            </n-tag>
          </n-space>
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <n-modal
      v-model:show="showFormulaModal"
      preset="card"
      :title="currentFormula?.name"
      style="width: 600px"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item
          v-for="part in currentFormula?.structure"
          :key="part.key"
          :label="part.label"
          :required="part.required"
        >
          <n-select
            v-if="part.options"
            v-model:value="formulaValues[part.key]"
            :options="part.options.map(o => ({ label: o, value: o }))"
            :placeholder="part.placeholder"
            clearable
          />
          <n-input
            v-else
            v-model:value="formulaValues[part.key]"
            :placeholder="part.placeholder"
          />
        </n-form-item>
      </n-form>

      <n-card size="small" title="生成预览" class="mt-3">
        <n-text>{{ generatedFormulaPrompt }}</n-text>
      </n-card>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showFormulaModal = false">取消</n-button>
          <n-button type="primary" @click="applyFormulaPrompt">应用到提示词</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showFestivalModal"
      preset="card"
      :title="currentFestivalTemplate?.name"
      style="width: 600px"
    >
      <n-alert type="info" class="mb-3">
        <template #header>配色方案</template>
        {{ currentFestivalTemplate?.colorScheme.join(' / ') }}
      </n-alert>

      <n-form label-placement="left" label-width="80">
        <n-form-item label="品牌名">
          <n-input v-model:value="festivalValues.brandName" placeholder="输入品牌名称" />
        </n-form-item>
        <n-form-item label="Slogan">
          <n-input v-model:value="festivalValues.slogan" placeholder="输入品牌Slogan" />
        </n-form-item>
        <n-form-item label="产品">
          <n-input v-model:value="festivalValues.product" placeholder="输入产品名称" />
        </n-form-item>
      </n-form>

      <n-card size="small" title="生成预览" class="mt-3">
        <n-text>{{ generatedFestivalPrompt }}</n-text>
      </n-card>

      <n-card size="small" title="小贴士" class="mt-3">
        <ul class="tips-list">
          <li v-for="(tip, index) in currentFestivalTemplate?.tips" :key="index">{{ tip }}</li>
        </ul>
      </n-card>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showFestivalModal = false">取消</n-button>
          <n-button type="primary" @click="applyFestivalPrompt">应用到提示词</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showMyTemplateModal"
      preset="card"
      :title="editingTemplate ? '编辑模板' : '新建模板'"
      style="width: 600px"
    >
      <n-form label-placement="left" label-width="80">
        <n-form-item label="模板名称" required>
          <n-input v-model:value="myTemplateForm.name" placeholder="如：小红书封面" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="myTemplateForm.description" placeholder="模板用途描述" />
        </n-form-item>
        <n-form-item label="分类">
          <n-select
            v-model:value="myTemplateForm.category"
            :options="myCategories.map(c => ({ label: c.label, value: c.value }))"
          />
        </n-form-item>
        <n-form-item label="提示词模板" required>
          <n-input
            v-model:value="myTemplateForm.promptTemplate"
            type="textarea"
            :rows="4"
            placeholder="使用 {变量名} 表示可替换变量，如：{主题}，鲜艳色彩，高级感"
          />
        </n-form-item>
        <n-form-item label="负面提示词">
          <n-input
            v-model:value="myTemplateForm.negativePrompt"
            type="textarea"
            :rows="2"
            placeholder="不想要的内容（可选）"
          />
        </n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="尺寸">
              <n-select
                v-model:value="myTemplateForm.size"
                :options="sizeOptions"
              />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="模型">
              <n-select
                v-model:value="myTemplateForm.model"
                :options="modelOptions"
              />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="myTemplateForm.tags" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showMyTemplateModal = false">取消</n-button>
          <n-button type="primary" @click="saveMyTemplate">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showApplyMyTemplateModal"
      preset="card"
      title="应用模板"
      style="width: 500px"
    >
      <template v-if="applyingTemplate">
        <div class="apply-preview">
          <div class="preview-name">{{ applyingTemplate.name }}</div>
          <div class="preview-desc">{{ applyingTemplate.description }}</div>
          
          <n-divider />

          <n-form label-placement="left" label-width="80">
            <n-form-item label="变量替换">
              <div class="variable-inputs">
                <div
                  v-for="variable in extractedVariables"
                  :key="variable"
                  class="variable-item"
                >
                  <span class="variable-label">{{ variable }}:</span>
                  <n-input
                    v-model:value="variableValues[variable]"
                    :placeholder="`输入${variable}`"
                    size="small"
                  />
                </div>
              </div>
            </n-form-item>
          </n-form>

          <n-card size="small" title="预览">
            <n-text>{{ previewPrompt }}</n-text>
          </n-card>
        </div>
      </template>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showApplyMyTemplateModal = false">取消</n-button>
          <n-button type="primary" @click="confirmApplyMyTemplate">应用到生成面板</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showTemplateFieldModal"
      preset="card"
      :title="currentFieldTemplate?.name"
      style="width: 500px"
    >
      <n-alert type="info" class="mb-3" :show-icon="false">
        {{ currentFieldTemplate?.description }}
      </n-alert>

      <n-form label-placement="left" label-width="80">
        <n-form-item
          v-for="field in currentFieldTemplate?.fields"
          :key="field.key"
          :label="field.label"
          :required="field.required"
        >
          <n-select
            v-if="field.options"
            v-model:value="templateFieldValues[field.key]"
            :options="field.options.map((o: string) => ({ label: o, value: o }))"
            :placeholder="field.placeholder"
            clearable
          />
          <n-input
            v-else
            v-model:value="templateFieldValues[field.key]"
            :placeholder="field.placeholder"
          />
        </n-form-item>
      </n-form>

      <n-card size="small" title="生成预览" class="mt-3">
        <n-text>{{ generatedTemplatePrompt }}</n-text>
      </n-card>

      <n-card size="small" title="小贴士" class="mt-3" v-if="currentFieldTemplate?.tips?.length">
        <ul class="tips-list">
          <li v-for="(tip, index) in currentFieldTemplate.tips" :key="index">{{ tip }}</li>
        </ul>
      </n-card>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showTemplateFieldModal = false">取消</n-button>
          <n-button type="primary" @click="applyFieldTemplate">应用到提示词</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore, useDataStore } from '../stores'
import { useWorkflowStore, type WorkflowTemplate } from '../stores/workflow'
import { Lightbulb, Palette, Smartphone, Package, Building2, BookOpen, User } from 'lucide-vue-next'
import { getLucideIconComponent } from '../utils/icons'
import {
  festivalCategories,
  getCurrentFestival,
  generateFestivalPrompt,
  type FestivalTemplate,
  type FestivalType
} from '../data/festivalTemplates'
import {
  promptFormulas,
  formulaCategories,
  quickStyleCodes,
  qualityKeywords,
  lightingKeywords,
  generatePromptFromFormula,
  type PromptFormula
} from '../data/promptFormulas'

const emit = defineEmits<{
  select: [prompt: string]
}>()

const message = useMessage()
const generatorStore = useGeneratorStore()
const workflowStore = useWorkflowStore()
const dataStore = useDataStore()

const activeCategory = ref('quick')
const selectedSceneCategory = ref<string | null>(null)
const selectedFestival = ref<FestivalType>(getCurrentFestival() || 'spring_festival')
const selectedFormulaCategory = ref('基础')
const selectedMyCategory = ref('all')

const showFormulaModal = ref(false)
const showFestivalModal = ref(false)
const showMyTemplateModal = ref(false)
const showApplyMyTemplateModal = ref(false)
const showTemplateFieldModal = ref(false)
const currentFormula = ref<PromptFormula | null>(null)
const currentFestivalTemplate = ref<FestivalTemplate | null>(null)
const currentFieldTemplate = ref<any>(null)
const formulaValues = ref<Record<string, string>>({})
const templateFieldValues = ref<Record<string, string>>({})
const festivalValues = ref({
  brandName: '',
  slogan: '',
  product: ''
})

const myTemplateSearch = ref('')
const editingTemplate = ref<WorkflowTemplate | null>(null)
const applyingTemplate = ref<WorkflowTemplate | null>(null)
const variableValues = ref<Record<string, string>>({})
const myTemplateForm = ref({
  name: '',
  description: '',
  category: 'social',
  promptTemplate: '',
  negativePrompt: '',
  size: '1024x1024',
  model: 'doubao-seedream-4-5-251128',
  tags: [] as string[]
})

const sceneCategories = [
  { id: 'product', name: '产品展示', icon: Package },
  { id: 'brand', name: '企业品牌', icon: Building2 },
  { id: 'education', name: '科普教育', icon: BookOpen },
  { id: 'culture', name: '文化内容', icon: Palette },
  { id: 'social', name: '社媒内容', icon: Smartphone },
  { id: 'portrait', name: '人物肖像', icon: User }
]

const myCategories = [
  { label: '全部', value: 'all' },
  { label: '社媒', value: 'social' },
  { label: '电商', value: 'ecommerce' },
  { label: '设计', value: 'design' },
  { label: '其他', value: 'other' }
]

const sizeOptions = [
  { label: '1024x1024 (正方形)', value: '1024x1024' },
  { label: '1024x1792 (竖版)', value: '1024x1792' },
  { label: '1792x1024 (横版)', value: '1792x1024' },
  { label: '2048x2048 (高清正方形)', value: '2048x2048' },
  { label: '1440x2560 (小红书封面)', value: '1440x2560' }
]

const modelOptions = [
  { label: '豆包 Seedream 4.5', value: 'doubao-seedream-4-5-251128' },
  { label: '豆包 Seedream 4.0', value: 'doubao-seedream-4-0-250828' },
  { label: '智谱 CogView-3-Flash', value: 'cogview-3-flash' },
  { label: '通义万相 V1', value: 'wanx-v1' }
]

const currentFestivalName = computed(() => {
  const current = getCurrentFestival()
  const cat = festivalCategories.find(c => c.id === current)
  return cat ? cat.name : '春节'
})

const filteredTemplates = computed(() => {
  if (!selectedSceneCategory.value) return []
  
  const imageTemplates = (dataStore.workTemplates || [])
    .filter(t => t.category === selectedSceneCategory.value)
    .map(t => ({ ...t, type: 'image' as const }))
  
  const videoTemplatesFiltered = (dataStore.videoTemplates || [])
    .filter(t => t.category === selectedSceneCategory.value)
    .map(t => ({ ...t, type: 'video' as const }))
  
  return [...imageTemplates, ...videoTemplatesFiltered]
})

const selectedFestivalTemplates = computed(() => 
  (dataStore.festivalTemplates || []).filter(t => t.festival === selectedFestival.value)
)

const selectedFormulas = computed(() => 
  promptFormulas.filter(f => f.category === selectedFormulaCategory.value)
)

const filteredMyTemplates = computed(() => {
  let templates = workflowStore.templates
  
  if (selectedMyCategory.value !== 'all') {
    templates = templates.filter(t => t.category === selectedMyCategory.value)
  }
  
  if (myTemplateSearch.value) {
    const search = myTemplateSearch.value.toLowerCase()
    templates = templates.filter(t => 
      t.name.toLowerCase().includes(search) ||
      t.description.toLowerCase().includes(search)
    )
  }
  
  return templates
})

const generatedFormulaPrompt = computed(() => {
  if (!currentFormula.value) return ''
  return generatePromptFromFormula(currentFormula.value, formulaValues.value)
})

const generatedFestivalPrompt = computed(() => {
  if (!currentFestivalTemplate.value) return ''
  
  const values: Record<string, string> = {}
  if (festivalValues.value.brandName) values['品牌名'] = festivalValues.value.brandName
  if (festivalValues.value.slogan) values['品牌Slogan'] = festivalValues.value.slogan
  if (festivalValues.value.product) values['产品名称'] = festivalValues.value.product
  
  return generateFestivalPrompt(currentFestivalTemplate.value, values)
})

const extractedVariables = computed(() => {
  if (!applyingTemplate.value) return []
  const matches = applyingTemplate.value.config.promptTemplate.match(/\{([^}]+)\}/g) || []
  return matches.map(m => m.slice(1, -1))
})

const previewPrompt = computed(() => {
  if (!applyingTemplate.value) return ''
  let prompt = applyingTemplate.value.config.promptTemplate
  for (const [key, value] of Object.entries(variableValues.value)) {
    prompt = prompt.replace(`{${key}}`, value)
  }
  return prompt
})

const generatedTemplatePrompt = computed(() => {
  if (!currentFieldTemplate.value) return ''
  let prompt = currentFieldTemplate.value.prompt
  for (const [key, value] of Object.entries(templateFieldValues.value)) {
    prompt = prompt.replace(`{${key}}`, value)
  }
  return prompt
})

function selectSceneCategory(id: string) {
  selectedSceneCategory.value = id
}

function applyTemplate(template: any) {
  if (template.fields && template.fields.length > 0) {
    currentFieldTemplate.value = template
    templateFieldValues.value = {}
    showTemplateFieldModal.value = true
    return
  }
  
  if (template.content || template.prompt) {
    generatorStore.prompt = template.content || template.prompt || ''
    if (template.negativePrompt) {
      generatorStore.negativePrompt = template.negativePrompt
    }
  } else if (template.promptTemplate) {
    generatorStore.prompt = template.promptTemplate
    if (template.negativePrompt) {
      generatorStore.negativePrompt = template.negativePrompt
    }
  }
  message.success('模板已应用')
  emit('select', generatorStore.prompt)
}

function showFormulaBuilder(formula: PromptFormula) {
  currentFormula.value = formula
  formulaValues.value = {}
  showFormulaModal.value = true
}

function applyFormulaPrompt() {
  if (generatedFormulaPrompt.value) {
    generatorStore.prompt = generatedFormulaPrompt.value
    message.success('公式已应用')
    showFormulaModal.value = false
    emit('select', generatorStore.prompt)
  }
}

function applyFestivalTemplate(template: FestivalTemplate) {
  currentFestivalTemplate.value = template
  festivalValues.value = { brandName: '', slogan: '', product: '' }
  showFestivalModal.value = true
}

function applyFestivalPrompt() {
  if (generatedFestivalPrompt.value) {
    generatorStore.prompt = generatedFestivalPrompt.value
    if (currentFestivalTemplate.value?.negativePrompt) {
      generatorStore.negativePrompt = currentFestivalTemplate.value.negativePrompt
    }
    message.success('节庆模板已应用')
    showFestivalModal.value = false
    emit('select', generatorStore.prompt)
  }
}

function applyFieldTemplate() {
  if (generatedTemplatePrompt.value && currentFieldTemplate.value) {
    const requiredFields = currentFieldTemplate.value.fields?.filter((f: any) => f.required) || []
    const missingFields = requiredFields.filter((f: any) => !templateFieldValues.value[f.key])
    
    if (missingFields.length > 0) {
      message.warning(`请填写必填项：${missingFields.map((f: any) => f.label).join('、')}`)
      return
    }
    
    generatorStore.prompt = generatedTemplatePrompt.value
    if (currentFieldTemplate.value.negativePrompt) {
      generatorStore.negativePrompt = currentFieldTemplate.value.negativePrompt
    }
    message.success('模板已应用')
    showTemplateFieldModal.value = false
    emit('select', generatorStore.prompt)
  }
}

function insertCode(code: string) {
  const current = generatorStore.prompt
  if (current && !current.endsWith('，') && !current.endsWith(',')) {
    generatorStore.prompt = current + '，' + code
  } else {
    generatorStore.prompt = current + code
  }
  message.success(`已插入: ${code}`)
}

function getCategoryLabel(category: string): string {
  const cat = myCategories.find(c => c.value === category)
  return cat?.label || category
}

function applyMyTemplate(template: WorkflowTemplate) {
  applyingTemplate.value = template
  variableValues.value = {}
  showApplyMyTemplateModal.value = true
}

function confirmApplyMyTemplate() {
  if (!applyingTemplate.value) return
  
  let prompt = applyingTemplate.value.config.promptTemplate
  for (const [key, value] of Object.entries(variableValues.value)) {
    prompt = prompt.replace(`{${key}}`, value)
  }
  
  generatorStore.prompt = prompt
  if (applyingTemplate.value.config.negativePrompt) {
    generatorStore.negativePrompt = applyingTemplate.value.config.negativePrompt
  }
  
  message.success('模板已应用')
  showApplyMyTemplateModal.value = false
  emit('select', generatorStore.prompt)
}

function editMyTemplate(template: WorkflowTemplate) {
  editingTemplate.value = template
  myTemplateForm.value = {
    name: template.name,
    description: template.description,
    category: template.category,
    promptTemplate: template.config.promptTemplate,
    negativePrompt: template.config.negativePrompt || '',
    size: template.config.size,
    model: template.config.model,
    tags: template.tags
  }
  showMyTemplateModal.value = true
}

function deleteMyTemplate(template: WorkflowTemplate) {
  workflowStore.remove(template.id!)
  message.success('模板已删除')
}

function saveMyTemplate() {
  if (!myTemplateForm.value.name || !myTemplateForm.value.promptTemplate) {
    message.warning('请填写模板名称和提示词模板')
    return
  }
  
  const templateData = {
    name: myTemplateForm.value.name,
    description: myTemplateForm.value.description,
    category: myTemplateForm.value.category,
    config: {
      model: myTemplateForm.value.model,
      size: myTemplateForm.value.size,
      promptTemplate: myTemplateForm.value.promptTemplate,
      negativePrompt: myTemplateForm.value.negativePrompt
    },
    tags: myTemplateForm.value.tags
  }
  
  if (editingTemplate.value) {
    workflowStore.update(editingTemplate.value.id!, templateData)
    message.success('模板已更新')
  } else {
    workflowStore.add(templateData)
    message.success('模板已创建')
  }
  
  showMyTemplateModal.value = false
  editingTemplate.value = null
  myTemplateForm.value = {
    name: '',
    description: '',
    category: 'social',
    promptTemplate: '',
    negativePrompt: '',
    size: '1024x1024',
    model: 'doubao-seedream-4-5-251128',
    tags: []
  }
}

onMounted(() => {
  workflowStore.load()
})
</script>

<style scoped>
.template-center { width: 100%; }

.category-card {
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.16,1,0.3,1),
              box-shadow 0.2s cubic-bezier(0.16,1,0.3,1),
              border-color 0.15s ease;
}

.category-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--brand-400);
}

.category-selected {
  border: 2px solid var(--brand-500) !important;
  box-shadow: 0 0 0 3px rgba(79, 125, 243, 0.12) !important;
}

.category-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.category-icon {
  font-size: 26px;
  transition: transform 0.2s ease;
}

.category-card:hover .category-icon {
  transform: scale(1.15);
}

.category-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--gray-600);
}

.festival-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  border-left: 3px solid;
  padding-left: 8px;
}

.festival-icon { font-size: 22px; }

.festival-name {
  font-size: 11px;
  font-weight: 500;
  color: var(--gray-600);
}

.formula-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.formula-icon { font-size: 22px; }

.formula-name {
  font-size: 11px;
  font-weight: 500;
  color: var(--gray-600);
}

.clickable-tag {
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);
}

.clickable-tag:hover {
  transform: translateY(-1px) scale(1.04);
  box-shadow: var(--shadow-md);
}

.tips-list { margin: 0; padding-left: 16px; }
.tips-list li { margin: 4px 0; color: var(--gray-500); font-size: 13px; }

.variable-inputs { display: flex; flex-direction: column; gap: 8px; width: 100%; }
.variable-item { display: flex; align-items: center; gap: 8px; }
.variable-label { min-width: 60px; font-weight: 500; }

.apply-preview { padding: 8px 0; }
.preview-name { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.preview-desc { color: var(--gray-500); font-size: 14px; }

.mt-3 { margin-top: 12px; }
.mb-3 { margin-bottom: 12px; }
</style>
