<template>
  <div class="prompt-template-panel">
    <n-alert type="info" class="mb-2" :show-icon="false">
      专业提示词模板，按结构填写即可生成高质量视频
    </n-alert>

    <n-space class="mb-2">
      <n-tag
        size="small"
        :type="selectedCategory === 'all' ? 'primary' : 'default'"
        @click="selectedCategory = 'all'"
      >
        全部
      </n-tag>
      <n-tag
        v-for="cat in templateCategories"
        :key="cat.value"
        size="small"
        :type="selectedCategory === cat.value ? 'primary' : 'default'"
        @click="selectedCategory = cat.value"
      >
        {{ cat.icon }} {{ cat.label }}
      </n-tag>
    </n-space>

    <n-scrollbar style="max-height: 350px">
      <n-collapse>
        <n-collapse-item
          v-for="template in filteredTemplates"
          :key="template.id"
          :name="template.id"
        >
          <template #header>
            <div class="template-header">
              <span class="template-name">{{ template.name }}</span>
            </div>
          </template>
          
          <div class="template-content">
            <div class="structure-box">
              <strong>结构公式：</strong>
              <div class="structure-text">{{ template.structure }}</div>
            </div>

            <div class="elements-section">
              <strong>必填元素：</strong>
              <div
                v-for="element in template.elements.filter(e => e.required)"
                :key="element.name"
                class="element-item"
              >
                <div class="element-name">{{ element.name }}</div>
                <div class="element-desc">{{ element.description }}</div>
                <div class="element-examples">
                  <n-tag
                    v-for="(example, idx) in element.examples.slice(0, 2)"
                    :key="idx"
                    size="tiny"
                    class="example-tag"
                    @click="insertExample(example)"
                  >
                    {{ example.slice(0, 20) }}{{ example.length > 20 ? '...' : '' }}
                  </n-tag>
                </div>
              </div>
            </div>

            <n-card size="small" title="完整示例" class="example-card">
              <n-ellipsis :line-clamp="3">{{ template.example }}</n-ellipsis>
            </n-card>

            <div class="tips-section">
              <strong>技巧：</strong>
              <ul>
                <li v-for="(tip, idx) in template.tips" :key="idx">{{ tip }}</li>
              </ul>
            </div>

            <n-button type="primary" size="small" block @click="useTemplate(template)">
              使用此模板
            </n-button>
          </div>
        </n-collapse-item>
      </n-collapse>
    </n-scrollbar>

    <n-modal v-model:show="showUseModal" preset="card" :title="currentTemplate?.name" style="width: 600px">
      <template v-if="currentTemplate">
        <n-form label-placement="top">
          <n-form-item
            v-for="element in currentTemplate.elements"
            :key="element.name"
            :label="element.name + (element.required ? ' *' : '')"
          >
            <n-input
              v-model:value="formValues[element.name]"
              type="textarea"
              :rows="2"
              :placeholder="element.description"
            />
            <div class="example-hints">
              <span class="hint-label">示例：</span>
              <n-tag
                v-for="(example, idx) in element.examples"
                :key="idx"
                size="tiny"
                class="hint-tag"
                @click="formValues[element.name] = example"
              >
                {{ example.slice(0, 15) }}{{ example.length > 15 ? '...' : '' }}
              </n-tag>
            </div>
          </n-form-item>
        </n-form>

        <n-card size="small" title="生成预览" class="preview-card">
          <n-ellipsis :line-clamp="4">{{ generatedPrompt }}</n-ellipsis>
        </n-card>
      </template>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showUseModal = false">取消</n-button>
          <n-button type="primary" @click="applyPrompt">应用到提示词</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { useGeneratorStore } from '../../stores'
import { promptTemplates, templateCategories, type PromptTemplate } from '../../data/promptTemplates'

const emit = defineEmits<{
  insert: [keyword: string]
}>()

const message = useMessage()
const generatorStore = useGeneratorStore()

const selectedCategory = ref('all')
const showUseModal = ref(false)
const currentTemplate = ref<PromptTemplate | null>(null)
const formValues = reactive<Record<string, string>>({})

const filteredTemplates = computed(() => {
  if (selectedCategory.value === 'all') {
    return promptTemplates
  }
  return promptTemplates.filter(t => t.category === selectedCategory.value)
})

const generatedPrompt = computed(() => {
  if (!currentTemplate.value) return ''
  
  const elements = currentTemplate.value.elements
  const parts: string[] = []
  
  elements.forEach(element => {
    const value = formValues[element.name]
    if (value) {
      parts.push(value)
    }
  })
  
  return parts.join('。')
})

function insertExample(example: string) {
  emit('insert', example)
}

function useTemplate(template: PromptTemplate) {
  currentTemplate.value = template
  
  template.elements.forEach(element => {
    formValues[element.name] = ''
  })
  
  showUseModal.value = true
}

function applyPrompt() {
  if (!currentTemplate.value) return
  
  const requiredElements = currentTemplate.value.elements.filter(e => e.required)
  const missingElements = requiredElements.filter(e => !formValues[e.name])
  
  if (missingElements.length > 0) {
    message.warning(`请填写必填项：${missingElements.map(e => e.name).join('、')}`)
    return
  }
  
  generatorStore.prompt = generatedPrompt.value
  message.success('提示词已应用')
  showUseModal.value = false
}
</script>

<style scoped>
.prompt-template-panel {
  padding: 8px 0;
}

.template-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-name {
  font-weight: 500;
}

.template-content {
  padding: 8px 0;
}

.structure-box {
  background: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.structure-text {
  margin-top: 4px;
  color: #18a058;
  font-weight: 500;
}

.elements-section {
  margin-bottom: 12px;
}

.element-item {
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
  margin: 4px 0;
}

.element-name {
  font-weight: 500;
  color: #333;
}

.element-desc {
  font-size: 12px;
  color: #888;
  margin: 4px 0;
}

.element-examples {
  margin-top: 4px;
}

.example-tag {
  cursor: pointer;
  margin: 2px;
}

.example-tag:hover {
  opacity: 0.8;
}

.example-card {
  margin-bottom: 12px;
}

.tips-section {
  margin-bottom: 12px;
}

.tips-section ul {
  margin: 4px 0;
  padding-left: 16px;
}

.tips-section li {
  font-size: 12px;
  color: #666;
  margin: 2px 0;
}

.example-hints {
  margin-top: 4px;
}

.hint-label {
  font-size: 12px;
  color: #888;
}

.hint-tag {
  cursor: pointer;
  margin: 2px;
}

.hint-tag:hover {
  opacity: 0.8;
}

.preview-card {
  margin-top: 12px;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
