<template>
  <div class="shot-language-panel">
    <n-input
      v-model:value="searchText"
      placeholder="搜索镜头语言..."
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
        v-for="cat in shotCategories"
        :key="cat.value"
        size="small"
        :type="selectedCategory === cat.value ? 'primary' : 'default'"
        @click="selectedCategory = cat.value"
      >
        {{ cat.icon }} {{ cat.label }}
      </n-tag>
    </n-space>

    <n-collapse>
      <n-collapse-item
        v-for="shot in filteredShots"
        :key="shot.id"
        :name="shot.id"
      >
        <template #header>
          <div class="shot-header">
            <span class="shot-name">{{ shot.name }}</span>
            <n-tag size="tiny" type="info">{{ shot.nameEn }}</n-tag>
          </div>
        </template>
        
        <div class="shot-content">
          <p class="shot-desc">{{ shot.description }}</p>
          <p class="shot-usage"><strong>用途：</strong>{{ shot.usage }}</p>
          
          <div class="shot-keywords">
            <span class="label">关键词：</span>
            <n-tag
              v-for="keyword in shot.keywords"
              :key="keyword"
              size="small"
              class="keyword-tag"
              @click="emit('insert', keyword)"
            >
              {{ keyword }}
            </n-tag>
          </div>
          
          <div class="shot-examples">
            <span class="label">示例：</span>
            <div
              v-for="(example, idx) in shot.examples"
              :key="idx"
              class="example-item"
              @click="emit('insert', example)"
            >
              {{ example }}
            </div>
          </div>
        </div>
      </n-collapse-item>
    </n-collapse>

    <n-divider>推荐组合</n-divider>
    
    <n-list bordered size="small">
      <n-list-item v-for="combo in shotCombinations" :key="combo.name">
        <n-thing :title="combo.name" :description="combo.description">
          <template #action>
            <n-button size="tiny" @click="showComboPreview(combo)">
              预览
            </n-button>
            <n-button size="tiny" type="primary" @click="emit('insert', combo.prompt)">
              使用
            </n-button>
          </template>
        </n-thing>
      </n-list-item>
    </n-list>

    <n-modal v-model:show="showPreviewModal" preset="card" :title="currentCombo?.name" style="width: 500px">
      <template v-if="currentCombo">
        <n-alert type="info" class="mb-2" :show-icon="false">
          {{ currentCombo.description }}
        </n-alert>
        
        <n-card size="small" title="包含镜头" class="mb-2">
          <n-space>
            <n-tag v-for="shotId in currentCombo.shots" :key="shotId" type="info">
              {{ getShotName(shotId) }}
            </n-tag>
          </n-space>
        </n-card>
        
        <n-card size="small" title="完整提示词">
          <n-ellipsis :line-clamp="4">{{ currentCombo.prompt }}</n-ellipsis>
        </n-card>
      </template>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showPreviewModal = false">取消</n-button>
          <n-button type="primary" @click="applyCombo">
            应用到提示词
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { shotTypes, shotCategories, shotCombinations, searchShots, getShotById } from '../../data/shotLanguageData'

const emit = defineEmits<{
  insert: [keyword: string]
}>()

const searchText = ref('')
const selectedCategory = ref('all')
const showPreviewModal = ref(false)
const currentCombo = ref<typeof shotCombinations[0] | null>(null)

const filteredShots = computed(() => {
  let shots = shotTypes
  
  if (selectedCategory.value !== 'all') {
    shots = shots.filter(s => s.category === selectedCategory.value)
  }
  
  if (searchText.value) {
    shots = searchShots(searchText.value)
  }
  
  return shots
})

function showComboPreview(combo: typeof shotCombinations[0]) {
  currentCombo.value = combo
  showPreviewModal.value = true
}

function getShotName(shotId: string): string {
  const shot = getShotById(shotId)
  return shot?.name || shotId
}

function applyCombo() {
  if (currentCombo.value) {
    emit('insert', currentCombo.value.prompt)
    showPreviewModal.value = false
  }
}
</script>

<style scoped>
.shot-language-panel {
  padding: 8px 0;
}

.shot-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.shot-name {
  font-weight: 500;
}

.shot-content {
  padding: 8px 0;
}

.shot-desc {
  color: #666;
  margin-bottom: 8px;
}

.shot-usage {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
}

.shot-keywords {
  margin-bottom: 8px;
}

.keyword-tag {
  cursor: pointer;
  margin: 2px;
}

.keyword-tag:hover {
  opacity: 0.8;
}

.shot-examples {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 8px;
}

.example-item {
  font-size: 12px;
  color: #666;
  padding: 4px 0;
  cursor: pointer;
}

.example-item:hover {
  color: #18a058;
}

.label {
  font-weight: 500;
  font-size: 12px;
  color: #333;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
