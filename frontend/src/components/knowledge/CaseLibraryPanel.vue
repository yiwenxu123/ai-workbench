<template>
  <div class="case-library-panel">
    <n-space justify="space-between" class="mb-2">
      <n-input
        v-model:value="searchText"
        placeholder="搜索案例..."
        clearable
        size="small"
        style="width: 120px"
      />
      <n-button size="small" type="primary" @click="openAddModal">
        + 添加案例
      </n-button>
    </n-space>

    <n-space class="mb-2">
      <n-tag
        size="small"
        :type="selectedCategory === 'all' ? 'primary' : 'default'"
        @click="selectedCategory = 'all'"
      >
        全部
      </n-tag>
      <n-tag
        v-for="cat in caseCategories"
        :key="cat.value"
        size="small"
        :type="selectedCategory === cat.value ? 'primary' : 'default'"
        @click="selectedCategory = cat.value"
      >
        {{ cat.icon }} {{ cat.label }}
      </n-tag>
      <n-tag
        v-if="userCases.length > 0"
        size="small"
        :type="selectedCategory === 'user' ? 'primary' : 'default'"
        @click="selectedCategory = 'user'"
      >
        我的案例 ({{ userCases.length }})
      </n-tag>
    </n-space>

    <n-scrollbar style="max-height: 400px">
      <n-list bordered>
        <n-list-item v-for="caseItem in filteredCases" :key="caseItem.id">
          <n-thing :title="caseItem.name" :description="caseItem.description">
            <template #avatar>
              <n-tag :type="getCategoryType(caseItem.category)" size="small">
                {{ getCategoryLabel(caseItem.category) }}
              </n-tag>
            </template>
            <template #action>
              <n-space>
                <n-button 
                  v-if="caseItem.videoUrl || caseItem.embedUrl" 
                  size="tiny" 
                  type="info"
                  @click="showVideoPreview(caseItem)"
                >
                  预览
                </n-button>
                <n-button size="tiny" @click="showCaseDetail(caseItem)">
                  详情
                </n-button>
                <n-button size="tiny" type="primary" @click="useCase(caseItem)">
                  使用
                </n-button>
                <n-button 
                  v-if="caseItem.isUserCase" 
                  size="tiny" 
                  @click="editUserCase(caseItem)"
                >
                  编辑
                </n-button>
                <n-popconfirm
                  v-if="caseItem.isUserCase"
                  @positive-click="deleteUserCase(caseItem)"
                >
                  <template #trigger>
                    <n-button size="tiny" type="error">删除</n-button>
                  </template>
                  确定删除此案例吗？
                </n-popconfirm>
              </n-space>
            </template>
            <div class="case-tags">
              <n-tag v-for="tag in caseItem.tags" :key="tag" size="tiny">
                {{ tag }}
              </n-tag>
            </div>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-scrollbar>

    <n-modal v-model:show="showDetailModal" preset="card" :title="currentCase?.name" style="width: 600px">
      <template v-if="currentCase">
        <n-descriptions label-placement="left" :column="1" bordered>
          <n-descriptions-item label="描述">{{ currentCase.description }}</n-descriptions-item>
          <n-descriptions-item label="推荐模型">{{ currentCase.model }}</n-descriptions-item>
          <n-descriptions-item label="参数">
            尺寸: {{ currentCase.parameters?.size || '-' }} | 
            时长: {{ currentCase.parameters?.duration || '-' }} | 
            风格: {{ currentCase.parameters?.style || '-' }}
          </n-descriptions-item>
        </n-descriptions>

        <n-card size="small" title="提示词" class="mt-2">
          <n-ellipsis :line-clamp="4">{{ currentCase.prompt }}</n-ellipsis>
        </n-card>

        <n-card size="small" title="负面提示词" class="mt-2" v-if="currentCase.negativePrompt">
          <n-ellipsis :line-clamp="2">{{ currentCase.negativePrompt }}</n-ellipsis>
        </n-card>

        <n-card size="small" title="技巧提示" class="mt-2">
          <ul class="tips-list">
            <li v-for="(tip, idx) in currentCase.tips" :key="idx">{{ tip }}</li>
          </ul>
        </n-card>

        <n-divider>照葫芦画瓢</n-divider>
        
        <n-form label-placement="left" label-width="80">
          <n-form-item label="替换主体">
            <n-input v-model:value="customSubject" placeholder="输入新的主体名称" />
          </n-form-item>
        </n-form>
        
        <n-card size="small" title="生成预览" v-if="customSubject">
          <n-ellipsis :line-clamp="3">{{ adaptedPrompt }}</n-ellipsis>
        </n-card>
      </template>

      <template #footer>
        <n-space justify="space-between">
          <n-button v-if="!currentCase?.isUserCase" @click="copyToMyCases">
            复制到我的案例
          </n-button>
          <div v-else></div>
          <n-space>
            <n-button @click="showDetailModal = false">取消</n-button>
            <n-button type="primary" @click="useAdaptedPrompt">应用提示词</n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showAddModal" preset="card" :title="editingCase ? '编辑案例' : '添加我的案例'" style="width: 600px">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="案例名称" required>
          <n-input v-model:value="formData.name" placeholder="如：我的产品广告" />
        </n-form-item>
        <n-form-item label="分类" required>
          <n-select
            v-model:value="formData.category"
            :options="caseCategories.map(c => ({ label: c.label, value: c.value }))"
          />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="formData.description" placeholder="案例描述" />
        </n-form-item>
        <n-form-item label="提示词" required>
          <n-input
            v-model:value="formData.prompt"
            type="textarea"
            :rows="4"
            placeholder="完整的提示词"
          />
        </n-form-item>
        <n-form-item label="负面词">
          <n-input
            v-model:value="formData.negativePrompt"
            type="textarea"
            :rows="2"
            placeholder="负面提示词（可选）"
          />
        </n-form-item>
        <n-form-item label="推荐模型">
          <n-input v-model:value="formData.model" placeholder="如：可灵 V1" />
        </n-form-item>
        <n-form-item label="视频链接">
          <n-input v-model:value="formData.videoUrl" placeholder="外部视频链接（如飞书、百度网盘分享链接）" />
        </n-form-item>
        <n-form-item label="嵌入链接">
          <n-input v-model:value="formData.embedUrl" placeholder="嵌入播放链接（如B站嵌入链接）" />
        </n-form-item>
        <n-form-item label="技巧提示">
          <n-dynamic-tags v-model:value="formData.tips" />
        </n-form-item>
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="formData.tags" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="closeAddModal">取消</n-button>
          <n-button type="primary" @click="saveUserCase">保存案例</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showVideoModal" preset="card" :title="videoCase?.name" style="width: 700px">
      <template v-if="videoCase">
        <div v-if="videoCase.embedUrl" class="video-container">
          <iframe
            :src="videoCase.embedUrl"
            frameborder="0"
            allowfullscreen
            class="video-iframe"
          ></iframe>
        </div>
        <div v-else class="video-link-container">
          <n-alert type="info" :show-icon="false">
            <p>视频托管在外部平台，点击下方按钮跳转观看</p>
          </n-alert>
          <n-button type="primary" tag="a" :href="videoCase.videoUrl" target="_blank" class="mt-2">
            打开视频链接
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { caseCategories, adaptPrompt } from '../../data/caseLibrary'
import { db, type UserCase } from '../../db'
import type { CaseExample } from '../../data/caseLibrary'
import { useDataStore } from '../../stores'

const emit = defineEmits<{
  useCase: [caseExample: CaseExample]
}>()

const message = useMessage()
const dataStore = useDataStore()
const searchText = ref('')
const selectedCategory = ref('all')
const showDetailModal = ref(false)
const showAddModal = ref(false)
const showVideoModal = ref(false)
const currentCase = ref<CaseExample | null>(null)
const videoCase = ref<CaseExample | null>(null)
const customSubject = ref('')
const userCases = ref<UserCase[]>([])
const editingCase = ref<UserCase | null>(null)

const formData = reactive({
  name: '',
  category: 'product',
  description: '',
  prompt: '',
  negativePrompt: '',
  model: '',
  videoUrl: '',
  embedUrl: '',
  tips: [] as string[],
  tags: [] as string[]
})

/** 将 API case 映射为 CaseExample 格式 */
function mapApiCase(c: any): CaseExample {
  return {
    id: c.id || '',
    name: c.name || '',
    category: c.category || 'product',
    description: c.description || '',
    prompt: c.prompt || '',
    negativePrompt: c.negativePrompt || c.negative_prompt || '',
    model: c.model || '',
    parameters: {
      size: c.size || c.parameters?.size || '',
      duration: c.parameters?.duration || '',
      style: c.parameters?.style || '',
    },
    tips: Array.isArray(c.tips) ? c.tips : (typeof c.tips === 'string' && c.tips ? [c.tips] : []),
    tags: Array.isArray(c.tags) ? c.tags : [],
    videoUrl: c.videoUrl,
    embedUrl: c.embedUrl,
    thumbnailUrl: c.thumbnailUrl,
    isUserCase: false,
  }
}

const filteredCases = computed(() => {
  let cases: CaseExample[]

  if (selectedCategory.value === 'user') {
    cases = userCases.value.map(uc => ({
      id: `user-${uc.id}`,
      name: uc.name,
      category: uc.category as any,
      description: uc.description,
      prompt: uc.prompt,
      negativePrompt: uc.negativePrompt,
      model: uc.model || '自定义',
      parameters: uc.parameters || {},
      tips: uc.tips,
      tags: uc.tags,
      videoUrl: uc.videoUrl,
      embedUrl: uc.embedUrl,
      thumbnailUrl: uc.thumbnailUrl,
      isUserCase: true
    }))
  } else if (selectedCategory.value !== 'all') {
    cases = (dataStore.cases || [])
      .filter((c: any) => c.category === selectedCategory.value)
      .map(mapApiCase)
  } else {
    cases = [
      ...(dataStore.cases || []).map(mapApiCase),
      ...userCases.value.map(uc => ({
        id: `user-${uc.id}`,
        name: uc.name,
        category: uc.category as any,
        description: uc.description,
        prompt: uc.prompt,
        negativePrompt: uc.negativePrompt,
        model: uc.model || '自定义',
        parameters: uc.parameters || {},
        tips: uc.tips,
        tags: uc.tags,
        videoUrl: uc.videoUrl,
        embedUrl: uc.embedUrl,
        thumbnailUrl: uc.thumbnailUrl,
        isUserCase: true
      }))
    ]
  }

  if (searchText.value) {
    const query = searchText.value.toLowerCase()
    cases = cases.filter(c =>
      (c.name || '').toLowerCase().includes(query) ||
      (c.description || '').toLowerCase().includes(query)
    )
  }

  return cases
})

const adaptedPrompt = computed(() => {
  if (!currentCase.value || !customSubject.value) return ''
  return adaptPrompt(currentCase.value, customSubject.value)
})

function getCategoryType(category: string): 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error' {
  const types: Record<string, 'default' | 'primary' | 'info' | 'success' | 'warning' | 'error'> = {
    product: 'info',
    drama: 'warning',
    animation: 'success',
    film: 'error',
    social: 'primary',
    ecommerce: 'info',
    brand: 'warning'
  }
  return types[category] || 'default'
}

function getCategoryLabel(category: string): string {
  const cat = caseCategories.find(c => c.value === category)
  return cat ? cat.label : category
}

function showCaseDetail(caseItem: CaseExample) {
  currentCase.value = caseItem
  customSubject.value = ''
  showDetailModal.value = true
}

function showVideoPreview(caseItem: CaseExample) {
  videoCase.value = caseItem
  showVideoModal.value = true
}

function useCase(caseItem: CaseExample) {
  emit('useCase', caseItem)
}

function useAdaptedPrompt() {
  if (currentCase.value) {
    const prompt = customSubject.value ? adaptedPrompt.value : currentCase.value.prompt
    emit('useCase', {
      ...currentCase.value,
      prompt
    })
    showDetailModal.value = false
  }
}

function openAddModal() {
  editingCase.value = null
  resetFormData()
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
  editingCase.value = null
  resetFormData()
}

function resetFormData() {
  formData.name = ''
  formData.category = 'product'
  formData.description = ''
  formData.prompt = ''
  formData.negativePrompt = ''
  formData.model = ''
  formData.videoUrl = ''
  formData.embedUrl = ''
  formData.tips = []
  formData.tags = []
}

function editUserCase(caseItem: CaseExample) {
  const id = parseInt(caseItem.id.replace('user-', ''))
  const uc = userCases.value.find(u => u.id === id)
  if (uc) {
    editingCase.value = uc
    formData.name = uc.name
    formData.category = uc.category
    formData.description = uc.description
    formData.prompt = uc.prompt
    formData.negativePrompt = uc.negativePrompt || ''
    formData.model = uc.model || ''
    formData.videoUrl = uc.videoUrl || ''
    formData.embedUrl = uc.embedUrl || ''
    formData.tips = uc.tips || []
    formData.tags = uc.tags || []
    showAddModal.value = true
  }
}

async function loadUserCases() {
  try {
    userCases.value = await db.userCases.orderBy('createdAt').reverse().toArray()
    console.log('Loaded user cases:', userCases.value.length)
  } catch (error) {
    console.error('Failed to load user cases:', error)
    userCases.value = []
  }
}

async function saveUserCase() {
  if (!formData.name || !formData.prompt) {
    message.warning('请填写案例名称和提示词')
    return
  }
  
  try {
    const caseData = {
      name: String(formData.name),
      category: String(formData.category || 'product'),
      description: String(formData.description || ''),
      prompt: String(formData.prompt),
      negativePrompt: formData.negativePrompt ? String(formData.negativePrompt) : undefined,
      model: String(formData.model || ''),
      parameters: {
        size: '',
        duration: '',
        style: ''
      },
      tips: Array.isArray(formData.tips) ? [...formData.tips] : [],
      tags: Array.isArray(formData.tags) ? [...formData.tags] : [],
      videoUrl: formData.videoUrl ? String(formData.videoUrl) : undefined,
      embedUrl: formData.embedUrl ? String(formData.embedUrl) : undefined,
      createdAt: new Date()
    }
    
    if (editingCase.value) {
      await db.userCases.update(editingCase.value.id!, {
        ...caseData,
        updatedAt: new Date()
      })
      message.success('案例已更新')
    } else {
      await db.userCases.add(caseData)
      message.success('案例已保存')
    }
    
    showAddModal.value = false
    resetFormData()
    await loadUserCases()
  } catch (error) {
    console.error('Failed to save user case:', error)
    message.error('保存失败，请刷新页面后重试')
  }
}

async function deleteUserCase(caseItem: CaseExample) {
  try {
    const id = parseInt(caseItem.id.replace('user-', ''))
    await db.userCases.delete(id)
    message.success('案例已删除')
    await loadUserCases()
  } catch (error) {
    console.error('Failed to delete user case:', error)
    message.error('删除失败')
  }
}

async function copyToMyCases() {
  if (!currentCase.value) {
    message.warning('没有选中的案例')
    return
  }
  
  try {
    console.log('Copying case:', currentCase.value.name)
    
    const caseData = {
      name: currentCase.value.name + ' (副本)',
      category: String(currentCase.value.category || 'product'),
      description: String(currentCase.value.description || ''),
      prompt: String(currentCase.value.prompt || ''),
      negativePrompt: currentCase.value.negativePrompt ? String(currentCase.value.negativePrompt) : undefined,
      model: String(currentCase.value.model || ''),
      parameters: {
        size: currentCase.value.parameters?.size || '',
        duration: currentCase.value.parameters?.duration || '',
        style: currentCase.value.parameters?.style || ''
      },
      tips: Array.isArray(currentCase.value.tips) ? [...currentCase.value.tips] : [],
      tags: Array.isArray(currentCase.value.tags) ? [...currentCase.value.tags] : [],
      videoUrl: currentCase.value.videoUrl ? String(currentCase.value.videoUrl) : undefined,
      embedUrl: currentCase.value.embedUrl ? String(currentCase.value.embedUrl) : undefined,
      createdAt: new Date()
    }
    
    await db.userCases.add(caseData)
    
    message.success('已复制到我的案例')
    showDetailModal.value = false
    await loadUserCases()
  } catch (error) {
    console.error('Failed to copy case:', error)
    message.error('复制失败，请刷新页面后重试')
  }
}

onMounted(() => {
  loadUserCases()
})
</script>

<style scoped>
.case-library-panel {
  padding: 8px 0;
}

.case-tags {
  margin-top: 4px;
}

.tips-list {
  margin: 0;
  padding-left: 16px;
}

.tips-list li {
  margin: 4px 0;
  font-size: 13px;
  color: #666;
}

.video-container {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%;
  height: 0;
}

.video-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.video-link-container {
  text-align: center;
  padding: 20px;
}

.mt-2 {
  margin-top: 8px;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
