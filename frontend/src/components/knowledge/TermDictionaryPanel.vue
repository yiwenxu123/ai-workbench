<template>
  <div class="term-dictionary-panel">
    <n-input
      v-model:value="searchQuery"
      placeholder="搜索术语..."
      clearable
      size="small"
      class="mb-2"
    />

    <n-space class="mb-2">
      <n-tag
        size="small"
        :type="selectedCategory === 'all' ? 'primary' : 'default'"
        @click="selectedCategory = 'all'"
      >
        全部
      </n-tag>
      <n-tag
        v-for="(config, key) in termCategoryConfig"
        :key="key"
        size="small"
        :type="selectedCategory === key ? 'primary' : 'default'"
        @click="selectedCategory = key"
      >
        {{ config.icon }} {{ config.label }}
      </n-tag>
    </n-space>

    <n-scrollbar style="max-height: 350px">
      <n-collapse>
        <n-collapse-item
          v-for="term in filteredTerms"
          :key="term.id"
          :name="term.id"
        >
          <template #header>
            <div class="term-header">
              <span class="term-name">{{ term.name }}</span>
              <n-tag size="tiny" :style="{ color: getCategoryColor(term.category) }">
                {{ getCategoryLabel(term.category) }}
              </n-tag>
            </div>
          </template>
          
          <div class="term-content">
            <p class="term-name-en" v-if="term.nameEn">{{ term.nameEn }}</p>
            <p class="term-desc">{{ term.description }}</p>
            <p class="term-usage"><strong>用法：</strong>{{ term.usage }}</p>
            
            <div class="term-examples">
              <span class="label">示例：</span>
              <n-tag
                v-for="(example, idx) in term.examples.slice(0, 3)"
                :key="idx"
                size="small"
                class="example-tag"
                @click="emit('insert', example)"
              >
                {{ example }}
              </n-tag>
            </div>
            
            <div class="term-tips" v-if="term.tips">
              <span class="label">提示：</span>{{ term.tips }}
            </div>
            
            <div class="term-related" v-if="term.relatedTerms?.length">
              <span class="label">相关：</span>
              <n-tag
                v-for="related in term.relatedTerms"
                :key="related"
                size="tiny"
                @click="emit('insert', related)"
              >
                {{ related }}
              </n-tag>
            </div>
          </div>
        </n-collapse-item>
      </n-collapse>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { terminology, termCategoryConfig, type TermCategory } from '../../data/terminology'

const emit = defineEmits<{
  insert: [keyword: string]
}>()

const searchQuery = ref('')
const selectedCategory = ref<string | TermCategory>('all')

const filteredTerms = computed(() => {
  let terms = terminology
  
  if (selectedCategory.value !== 'all') {
    terms = terms.filter(t => t.category === selectedCategory.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    terms = terms.filter(t => 
      t.name.toLowerCase().includes(query) ||
      t.nameEn?.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  }
  
  return terms
})

function getCategoryLabel(category: TermCategory): string {
  return termCategoryConfig[category]?.label || category
}

function getCategoryColor(category: TermCategory): string {
  return termCategoryConfig[category]?.color || '#666'
}
</script>

<style scoped>
.term-dictionary-panel {
  padding: 8px 0;
}

.term-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.term-name {
  font-weight: 500;
}

.term-content {
  padding: 8px 0;
}

.term-name-en {
  font-size: 12px;
  color: #888;
  font-style: italic;
  margin-bottom: 4px;
}

.term-desc {
  color: #666;
  margin-bottom: 8px;
}

.term-usage {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

.term-examples {
  margin-bottom: 8px;
}

.example-tag {
  cursor: pointer;
  margin: 2px;
}

.example-tag:hover {
  opacity: 0.8;
}

.term-tips {
  font-size: 12px;
  color: #18a058;
  background: #f0faf4;
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.term-related {
  margin-top: 4px;
}

.label {
  font-weight: 500;
  font-size: 12px;
  color: #333;
  margin-right: 4px;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
