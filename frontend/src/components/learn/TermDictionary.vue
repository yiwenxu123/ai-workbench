<template>
  <div class="term-dictionary">
    <n-card v-if="showCard" title="术语词典" size="small">
      <template #header-extra>
        <n-button size="tiny" text @click="showHelp = !showHelp">
          <n-icon :component="HelpCircleOutline" />
        </n-button>
      </template>

      <n-input
        v-model:value="searchQuery"
        placeholder="搜索术语..."
        clearable
        size="small"
        class="search-input"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>

      <n-tabs v-model:value="activeCategory" type="line" size="small" class="category-tabs">
        <n-tab-pane name="all" tab="全部" />
        <n-tab-pane
          v-for="cat in categories"
          :key="cat.value"
          :name="cat.value"
          :tab="cat.label"
        />
      </n-tabs>

      <n-scrollbar style="max-height: 400px" class="term-list">
        <n-empty v-if="filteredTerms.length === 0" description="未找到相关术语" size="small" />
        
        <div
          v-for="term in filteredTerms"
          :key="term.id"
          class="term-item"
          @click="selectTerm(term)"
        >
          <div class="term-header">
            <span class="term-name">{{ term.name }}</span>
            <n-space :size="4">
              <n-tag
                size="tiny"
                :style="{ 
                  backgroundColor: getCategoryColor(term.category) + '20',
                  color: getCategoryColor(term.category)
                }"
              >
                {{ getCategoryLabel(term.category) }}
              </n-tag>
              <n-tag v-if="staleKnowledgeLabel(term.lastVerified)" size="tiny" type="warning">
                {{ staleKnowledgeLabel(term.lastVerified) }}
              </n-tag>
            </n-space>
          </div>
          <div class="term-name-en" v-if="term.nameEn">{{ term.nameEn }}</div>
          <div class="term-desc">{{ term.description }}</div>
          <div class="term-examples">
            <span class="example-label">示例：</span>
            <span
              v-for="(example, idx) in term.examples.slice(0, 2)"
              :key="idx"
              class="example-tag"
              @click.stop="insertExample(example)"
            >
              {{ example }}
            </span>
          </div>
        </div>
      </n-scrollbar>
    </n-card>

    <template v-else>
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索术语..."
        clearable
        size="small"
        class="search-input"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>

      <n-tabs v-model:value="activeCategory" type="line" size="small" class="category-tabs">
        <n-tab-pane name="all" tab="全部" />
        <n-tab-pane
          v-for="cat in categories"
          :key="cat.value"
          :name="cat.value"
          :tab="cat.label"
        />
      </n-tabs>

      <n-scrollbar style="max-height: 350px" class="term-list">
        <n-empty v-if="filteredTerms.length === 0" description="未找到相关术语" size="small" />
        
        <div
          v-for="term in filteredTerms"
          :key="term.id"
          class="term-item"
          @click="selectTerm(term)"
        >
          <div class="term-header">
            <span class="term-name">{{ term.name }}</span>
            <n-space :size="4">
              <n-tag
                size="tiny"
                :style="{ 
                  backgroundColor: getCategoryColor(term.category) + '20',
                  color: getCategoryColor(term.category)
                }"
              >
                {{ getCategoryLabel(term.category) }}
              </n-tag>
              <n-tag v-if="staleKnowledgeLabel(term.lastVerified)" size="tiny" type="warning">
                {{ staleKnowledgeLabel(term.lastVerified) }}
              </n-tag>
            </n-space>
          </div>
          <div class="term-name-en" v-if="term.nameEn">{{ term.nameEn }}</div>
          <div class="term-desc">{{ term.description }}</div>
          <div class="term-examples">
            <span class="example-label">示例：</span>
            <span
              v-for="(example, idx) in term.examples.slice(0, 2)"
              :key="idx"
              class="example-tag"
              @click.stop="insertExample(example)"
            >
              {{ example }}
            </span>
          </div>
        </div>
      </n-scrollbar>
    </template>

    <n-modal v-model:show="showTermDetail" preset="card" style="width: 500px" title="术语详情">
      <template v-if="selectedTerm">
        <div class="detail-header">
          <h3>{{ selectedTerm.name }}</h3>
          <n-tag :style="{ 
            backgroundColor: getCategoryColor(selectedTerm.category) + '20',
            color: getCategoryColor(selectedTerm.category)
          }">
            {{ getCategoryLabel(selectedTerm.category) }}
          </n-tag>
        </div>
        <p class="detail-name-en" v-if="selectedTerm.nameEn">{{ selectedTerm.nameEn }}</p>
        
        <n-divider />

        <div class="detail-section">
          <div class="section-title">描述</div>
          <p>{{ selectedTerm.description }}</p>
        </div>

        <div class="detail-section">
          <div class="section-title">使用建议</div>
          <p>{{ selectedTerm.usage }}</p>
        </div>

        <div class="detail-section">
          <div class="section-title">示例</div>
          <div class="example-list">
            <n-tag
              v-for="(example, idx) in selectedTerm.examples"
              :key="idx"
              class="example-item"
              @click="insertExample(example)"
            >
              {{ example }}
            </n-tag>
          </div>
        </div>

        <div class="detail-section" v-if="selectedTerm.tips">
          <div class="section-title">小技巧</div>
          <n-alert type="info" size="small">{{ selectedTerm.tips }}</n-alert>
        </div>

        <div class="detail-section" v-if="selectedTerm.relatedTerms?.length">
          <div class="section-title">相关术语</div>
          <div class="related-terms">
            <n-tag
              v-for="(related, idx) in selectedTerm.relatedTerms"
              :key="idx"
              size="small"
              round
            >
              {{ related }}
            </n-tag>
          </div>
        </div>
      </template>

      <template #footer>
        <n-button @click="insertTerm">插入到提示词</n-button>
        <n-button type="primary" @click="showTermDetail = false">关闭</n-button>
      </template>
    </n-modal>

    <n-modal v-model:show="showHelp" preset="card" style="width: 400px" title="使用帮助">
      <div class="help-content">
        <p><strong>搜索</strong>：输入关键词搜索相关术语</p>
        <p><strong>分类</strong>：点击标签页按类别浏览</p>
        <p><strong>使用</strong>：点击术语查看详情，或直接点击示例插入</p>
        <p><strong>提示</strong>：术语词典帮助你理解专业词汇，快速构建高质量提示词</p>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NCard, NInput, NIcon, NTag, NTabs, NTabPane, NScrollbar, NEmpty, NModal, NDivider, NAlert, NButton, NSpace } from 'naive-ui'
import { staleKnowledgeLabel } from '../../utils/knowledgeFreshness'
import { SearchOutline, HelpCircleOutline } from '@vicons/ionicons5'
import { termCategoryConfig } from '../../config/categories'
import type { TermEntry, TermCategory } from '../../types/knowledge'
import { useDataStore } from '../../stores'

withDefaults(defineProps<{
  showCard?: boolean
}>(), {
  showCard: true
})

const emit = defineEmits<{
  (e: 'insert', text: string): void
}>()

const dataStore = useDataStore()
const searchQuery = ref('')
const activeCategory = ref<string>('all')
const showTermDetail = ref(false)
const showHelp = ref(false)
const selectedTerm = ref<TermEntry | null>(null)

const categories = computed(() => 
  Object.entries(termCategoryConfig).map(([value, config]) => ({
    value,
    label: `${(config as { icon: string; label: string; color: string }).icon} ${(config as { icon: string; label: string; color: string }).label}`
  }))
)

/** 将 API KnowledgeEntry 映射为 TermEntry */
function mapToTerm(item: any): TermEntry {
  return {
    id: item.id || '',
    name: item.title || '',
    nameEn: item.tags?.[0] || '',
    category: item.category || 'style',
    description: item.content || '',
    usage: Array.isArray(item.tips) ? item.tips.join('；') : (item.tips || ''),
    examples: item.examples || [],
    relatedTerms: item.relatedTerms || [],
    tips: Array.isArray(item.tips) ? item.tips[0] : item.tips,
    lastVerified: item.lastVerified || '',
  }
}

const filteredTerms = computed(() => {
  const raw = dataStore.terms as any[] || []
  const allTerms = raw.map(mapToTerm)
  const q = searchQuery.value.toLowerCase().trim()
  
  const filtered = activeCategory.value === 'all'
    ? allTerms
    : allTerms.filter(t => t.category === activeCategory.value)
  
  if (!q) return filtered
  
  return filtered.filter(t =>
    t.name.includes(q) ||
    t.nameEn?.toLowerCase().includes(q) ||
    t.description.includes(q) ||
    t.examples.some(ex => ex.includes(q))
  )
})

function getCategoryColor(category: TermCategory): string {
  return termCategoryConfig[category]?.color || '#999'
}

function getCategoryLabel(category: TermCategory): string {
  return termCategoryConfig[category]?.label || category
}

function selectTerm(term: TermEntry) {
  selectedTerm.value = term
  showTermDetail.value = true
}

function insertExample(example: string) {
  emit('insert', example)
}

function insertTerm() {
  if (selectedTerm.value) {
    emit('insert', selectedTerm.value.name)
    showTermDetail.value = false
  }
}
</script>

<style scoped>
.term-dictionary {
  height: 100%;
}

.search-input {
  margin-bottom: 8px;
}

.category-tabs {
  margin-bottom: 8px;
}

.term-list {
  margin-top: 8px;
}

.term-item {
  padding: 10px;
  border-radius: 6px;
  background: var(--bg-subtle);
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.term-item:hover {
  background: #f0f0f0;
  border-color: #e0e0e0;
}

.term-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.term-name {
  font-weight: 600;
  font-size: 14px;
}

.term-name-en {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.term-desc {
  font-size: 12px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 6px;
}

.term-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.example-label {
  font-size: 11px;
  color: #999;
}

.example-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #e6f7ff;
  border-radius: 4px;
  color: #1890ff;
  cursor: pointer;
}

.example-tag:hover {
  background: #bae7ff;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header h3 {
  margin: 0;
}

.detail-name-en {
  color: #999;
  font-size: 14px;
  margin-top: 4px;
}

.detail-section {
  margin-bottom: 16px;
}

.section-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-item {
  cursor: pointer;
}

.example-item:hover {
  opacity: 0.8;
}

.related-terms {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.help-content p {
  margin-bottom: 12px;
  line-height: 1.6;
}
</style>
