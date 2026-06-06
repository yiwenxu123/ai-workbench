<template>
  <div class="template-gallery">
    <n-tabs v-model:value="activeCategory" type="line" animated>
      <n-tab-pane name="all" tab="全部">
        <template #default>
          <div class="template-grid">
            <div
              v-for="template in filteredTemplates"
              :key="template.id"
              class="template-card"
              @click="selectTemplate(template)"
            >
              <div class="template-header">
                <span class="template-name">{{ template.name }}</span>
                <n-tag size="small" :bordered="false">
                  {{ getCategoryName(template.category) }}
                </n-tag>
              </div>
              <div class="template-desc">{{ template.description }}</div>
              <div class="template-tags">
                <n-tag
                  v-for="tag in template.tags.slice(0, 3)"
                  :key="tag"
                  size="tiny"
                  type="info"
                  :bordered="false"
                >
                  {{ tag }}
                </n-tag>
              </div>
            </div>
          </div>
        </template>
      </n-tab-pane>
      
      <n-tab-pane
        v-for="category in categories"
        :key="category.id"
        :name="category.id"
      >
        <template #tab>
          <n-space align="center" :size="4">
            <n-icon :component="getLucideIconComponent(category.icon)" />
            <span>{{ category.name }}</span>
          </n-space>
        </template>
        <div class="template-grid">
          <div
            v-for="template in getTemplatesByCategory(category.id)"
            :key="template.id"
            class="template-card"
            @click="selectTemplate(template)"
          >
            <div class="template-header">
              <span class="template-name">{{ template.name }}</span>
            </div>
            <div class="template-desc">{{ template.description }}</div>
            <div class="template-tags">
              <n-tag
                v-for="tag in template.tags.slice(0, 3)"
                :key="tag"
                size="tiny"
                type="info"
                :bordered="false"
              >
                {{ tag }}
              </n-tag>
            </div>
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>

    <n-modal
      v-model:show="showDetail"
      preset="card"
      :title="selectedTemplate?.name"
      style="width: 600px"
      :bordered="false"
    >
      <template v-if="selectedTemplate">
        <n-descriptions :column="1" label-placement="left" bordered size="small">
          <n-descriptions-item label="描述">
            {{ selectedTemplate.description }}
          </n-descriptions-item>
          <n-descriptions-item label="推荐尺寸">
            {{ selectedTemplate.recommendedSize }}
          </n-descriptions-item>
        </n-descriptions>

        <n-divider style="margin: 12px 0">提示词模板</n-divider>
        
        <n-input
          :value="customizedPrompt"
          type="textarea"
          :rows="4"
          placeholder="点击占位符进行替换..."
          @update:value="customizedPrompt = $event"
        />

        <div class="placeholders" v-if="placeholders.length > 0">
          <n-text depth="3" style="font-size: 12px">点击替换占位符：</n-text>
          <n-space>
            <n-tag
              v-for="ph in placeholders"
              :key="ph"
              size="small"
              type="warning"
              style="cursor: pointer"
              @click="editPlaceholder(ph)"
            >
              {{ ph }}
            </n-tag>
          </n-space>
        </div>

        <div v-if="selectedTemplate.negativePrompt" class="negative-section">
          <n-text depth="3" style="font-size: 12px">负面提示词：</n-text>
          <n-text style="font-size: 12px">{{ selectedTemplate.negativePrompt }}</n-text>
        </div>

        <n-divider style="margin: 12px 0">使用提示</n-divider>
        
        <ul class="tips-list">
          <li v-for="(tip, i) in selectedTemplate.tips" :key="i">{{ tip }}</li>
        </ul>
      </template>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showDetail = false">取消</n-button>
          <n-button type="primary" @click="applyTemplate">
            应用模板
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      v-model:show="showPlaceholderInput"
      preset="card"
      :title="`替换 ${currentPlaceholder}`"
      style="width: 400px"
    >
      <n-input
        v-model:value="placeholderValue"
        :placeholder="`输入${currentPlaceholder}的值...`"
        @keydown.enter="confirmPlaceholder"
      />
      <template #footer>
        <n-space justify="end">
          <n-button @click="showPlaceholderInput = false">取消</n-button>
          <n-button type="primary" @click="confirmPlaceholder">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NTabs, NTabPane, NTag, NModal, NDescriptions, NDescriptionsItem, NDivider,
  NInput, NText, NSpace, NButton, useMessage
} from 'naive-ui'
import {
  workTemplates,
  templateCategories,
  getTemplatesByCategory,
  type WorkTemplate
} from '../data/workTemplates'
import { getLucideIconComponent } from '../utils/icons'

const emit = defineEmits<{
  (e: 'select', template: WorkTemplate, prompt: string): void
}>()

const message = useMessage()

const activeCategory = ref('all')
const showDetail = ref(false)
const selectedTemplate = ref<WorkTemplate | null>(null)
const customizedPrompt = ref('')
const showPlaceholderInput = ref(false)
const currentPlaceholder = ref('')
const placeholderValue = ref('')

const categories = templateCategories

const filteredTemplates = computed(() => {
  if (activeCategory.value === 'all') {
    return workTemplates
  }
  return getTemplatesByCategory(activeCategory.value)
})

const placeholders = computed(() => {
  const matches = customizedPrompt.value.match(/\[([A-Z_]+)\]/g)
  if (!matches) return []
  return [...new Set(matches.map(m => m.slice(1, -1)))]
})

function getCategoryName(categoryId: string): string {
  const cat = categories.find(c => c.id === categoryId)
  return cat ? cat.name : categoryId
}

function selectTemplate(template: WorkTemplate): void {
  selectedTemplate.value = template
  customizedPrompt.value = template.prompt
  showDetail.value = true
}

function editPlaceholder(ph: string): void {
  currentPlaceholder.value = ph
  placeholderValue.value = ''
  showPlaceholderInput.value = true
}

function confirmPlaceholder(): void {
  if (!currentPlaceholder.value || !placeholderValue.value.trim()) return
  
  customizedPrompt.value = customizedPrompt.value.replace(
    new RegExp(`\\[${currentPlaceholder.value}\\]`, 'g'),
    placeholderValue.value.trim()
  )
  
  showPlaceholderInput.value = false
  message.success(`已替换 [${currentPlaceholder.value}]`)
}

function applyTemplate(): void {
  if (!selectedTemplate.value) return
  
  if (placeholders.value.length > 0) {
    message.warning('请先替换所有占位符')
    return
  }
  
  emit('select', selectedTemplate.value, customizedPrompt.value)
  showDetail.value = false
  message.success('已应用模板')
}

watch(showDetail, (val) => {
  if (!val) {
    selectedTemplate.value = null
    customizedPrompt.value = ''
  }
})
</script>

<style scoped>
.template-gallery {
  height: 100%;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  padding: 12px 0;
}

.template-card {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.template-card:hover {
  background: #f0f0f0;
  border-color: #e0e0e0;
  transform: translateY(-2px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 500;
  font-size: 14px;
}

.template-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.4;
}

.template-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.placeholders {
  margin-top: 12px;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.negative-section {
  margin-top: 12px;
  padding: 8px;
  background: #fefce8;
  border-radius: var(--radius-sm);
}

.tips-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: var(--gray-500);
}

.tips-list li {
  margin-bottom: 4px;
}
</style>
