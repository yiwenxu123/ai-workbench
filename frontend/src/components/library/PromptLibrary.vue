<template>
  <div class="prompt-library">
    <n-space justify="space-between" class="mb-2">
      <n-input
        v-model:value="searchText"
        placeholder="搜索提示词..."
        clearable
        size="small"
        style="width: 150px"
      />
      <n-button size="small" type="primary" @click="showAddModal = true">
        + 新建
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
        v-for="cat in categories"
        :key="cat.value"
        size="small"
        :type="selectedCategory === cat.value ? 'primary' : 'default'"
        @click="selectedCategory = cat.value"
      >
        {{ cat.label }}
      </n-tag>
    </n-space>

    <n-scrollbar style="max-height: 350px">
      <n-empty v-if="filteredPrompts.length === 0" description="暂无提示词" />
      <n-list bordered v-else>
        <n-list-item v-for="prompt in filteredPrompts" :key="prompt.id">
          <n-thing :title="prompt.title">
            <template #description>
              <n-ellipsis :line-clamp="2">{{ prompt.content }}</n-ellipsis>
            </template>
            <template #action>
              <n-space>
                <n-button size="tiny" type="primary" @click="applyPrompt(prompt)">
                  使用
                </n-button>
                <n-button size="tiny" @click="copyPrompt(prompt)">
                  复制
                </n-button>
                <n-button size="tiny" type="error" @click="deletePrompt(prompt)">
                  删除
                </n-button>
              </n-space>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </n-scrollbar>

    <n-modal v-model:show="showAddModal" preset="card" title="新建提示词" style="width: 500px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="标题" required>
          <n-input v-model:value="newPrompt.title" placeholder="提示词标题" />
        </n-form-item>
        <n-form-item label="内容" required>
          <n-input
            v-model:value="newPrompt.content"
            type="textarea"
            :rows="4"
            placeholder="提示词内容"
          />
        </n-form-item>
        <n-form-item label="分类">
          <n-select
            v-model:value="newPrompt.category"
            :options="categories"
          />
        </n-form-item>
        <n-form-item label="标签">
          <n-dynamic-tags v-model:value="newPrompt.tags" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="savePrompt">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { usePromptStore, useGeneratorStore } from '../../stores'
import type { Prompt } from '../../types'

const emit = defineEmits<{
  select: [prompt: string]
}>()

const message = useMessage()
const promptStore = usePromptStore()
const generatorStore = useGeneratorStore()

const searchText = ref('')
const selectedCategory = ref('all')
const showAddModal = ref(false)
const newPrompt = ref({
  title: '',
  content: '',
  category: 'general',
  tags: [] as string[]
})

const categories = [
  { label: '通用', value: 'general' },
  { label: '人物', value: 'character' },
  { label: '风景', value: 'landscape' },
  { label: '艺术', value: 'art' },
  { label: '其他', value: 'other' }
]

const filteredPrompts = computed(() => {
  let prompts = promptStore.items
  
  if (selectedCategory.value !== 'all') {
    prompts = prompts.filter(p => p.category === selectedCategory.value)
  }
  
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    prompts = prompts.filter(p => 
      p.title.toLowerCase().includes(search) ||
      p.content.toLowerCase().includes(search)
    )
  }
  
  return prompts
})

function applyPrompt(prompt: Prompt) {
  generatorStore.prompt = prompt.content
  message.success('提示词已应用')
  emit('select', prompt.content)
}

async function copyPrompt(prompt: Prompt) {
  try {
    await navigator.clipboard.writeText(prompt.content)
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败')
  }
}

async function deletePrompt(prompt: Prompt) {
  await promptStore.remove(prompt.id!)
  message.success('已删除')
}

async function savePrompt() {
  if (!newPrompt.value.title || !newPrompt.value.content) {
    message.warning('请填写标题和内容')
    return
  }
  
  await promptStore.add({
    title: newPrompt.value.title,
    content: newPrompt.value.content,
    category: newPrompt.value.category as any,
    tags: newPrompt.value.tags
  })
  
  message.success('已保存')
  showAddModal.value = false
  newPrompt.value = {
    title: '',
    content: '',
    category: 'general',
    tags: []
  }
}

onMounted(() => {
  promptStore.load()
})
</script>

<style scoped>
.prompt-library {
  width: 100%;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>
