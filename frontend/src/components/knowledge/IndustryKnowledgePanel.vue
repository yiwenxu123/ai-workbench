<template>
  <div class="industry-knowledge-panel">
    <n-input
      v-model:value="searchText"
      placeholder="搜索行业知识..."
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
        v-for="cat in industryCategories"
        :key="cat.value"
        size="small"
        :type="selectedCategory === cat.value ? 'primary' : 'default'"
        @click="selectedCategory = cat.value"
      >
        {{ cat.icon }} {{ cat.label }}
      </n-tag>
    </n-space>

    <n-scrollbar style="max-height: 400px">
      <n-collapse>
        <n-collapse-item
          v-for="knowledge in filteredKnowledge"
          :key="knowledge.id"
          :name="knowledge.id"
        >
          <template #header>
            <div class="knowledge-header">
              <span class="knowledge-title">{{ knowledge.title }}</span>
            </div>
          </template>
          
          <div class="knowledge-content">
            <p class="knowledge-desc">{{ knowledge.content }}</p>
            
            <div class="knowledge-section">
              <strong>要点</strong>
              <ul>
                <li v-for="(tip, idx) in knowledge.tips" :key="idx">{{ tip }}</li>
              </ul>
            </div>
            
            <div class="knowledge-section">
              <strong>最佳实践</strong>
              <ul>
                <li v-for="(practice, idx) in knowledge.bestPractices" :key="idx">{{ practice }}</li>
              </ul>
            </div>
            
            <div class="knowledge-section">
              <strong>常见错误</strong>
              <ul>
                <li v-for="(mistake, idx) in knowledge.commonMistakes" :key="idx">{{ mistake }}</li>
              </ul>
            </div>
            
            <div class="knowledge-section" v-if="knowledge.relatedTemplates.length > 0">
              <strong>相关模板</strong>
              <n-space>
                <n-tag
                  v-for="template in knowledge.relatedTemplates"
                  :key="template"
                  size="small"
                  type="info"
                >
                  {{ template }}
                </n-tag>
              </n-space>
            </div>
          </div>
        </n-collapse-item>
      </n-collapse>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { industryKnowledge, industryCategories, searchKnowledge } from '../../data/industryKnowledge'

const searchText = ref('')
const selectedCategory = ref('all')

const filteredKnowledge = computed(() => {
  let knowledge = industryKnowledge
  
  if (selectedCategory.value !== 'all') {
    knowledge = knowledge.filter(k => k.category === selectedCategory.value)
  }
  
  if (searchText.value) {
    knowledge = searchKnowledge(searchText.value)
  }
  
  return knowledge
})
</script>

<style scoped>
.industry-knowledge-panel {
  padding: 8px 0;
}

.knowledge-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.knowledge-title {
  font-weight: 500;
}

.knowledge-content {
  padding: 8px 0;
}

.knowledge-desc {
  color: #666;
  margin-bottom: 12px;
}

.knowledge-section {
  margin-bottom: 12px;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 4px;
}

.knowledge-section strong {
  display: block;
  margin-bottom: 8px;
  color: #333;
}

.knowledge-section ul {
  margin: 0;
  padding-left: 16px;
}

.knowledge-section li {
  font-size: 13px;
  color: #666;
  margin: 4px 0;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
