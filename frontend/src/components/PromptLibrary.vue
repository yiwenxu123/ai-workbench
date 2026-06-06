<template>
  <div class="prompt-library">
    <n-card title="提示词库" size="small">
      <template #header-extra>
        <n-button size="small" @click="promptStore.showModal = true">
          <template #icon><n-icon :component="AddOutline" /></template>
          新建
        </n-button>
      </template>

      <n-input
        v-model:value="promptStore.searchText"
        placeholder="搜索提示词..."
        clearable
        class="mb-3"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>

      <n-scrollbar style="max-height: 400px">
        <n-empty v-if="promptStore.filteredItems.length === 0" description="暂无提示词" />
        <div v-else class="prompt-list">
          <div
            v-for="prompt in promptStore.filteredItems"
            :key="prompt.id"
            class="prompt-item"
            @click="selectPrompt(prompt)"
          >
            <div class="prompt-header">
              <span class="prompt-title">{{ prompt.title }}</span>
              <div class="prompt-actions">
                <n-button text size="tiny" @click.stop="promptStore.startEdit(prompt)">
                  <n-icon :component="CreateOutline" color="#666" />
                </n-button>
                <n-button text size="tiny" @click.stop="handleDelete(prompt.id!)">
                  <n-icon :component="TrashOutline" color="#999" />
                </n-button>
              </div>
            </div>
            <div class="prompt-content">{{ prompt.content.slice(0, 60) }}...</div>
            <div class="prompt-tags">
              <n-tag v-for="tag in prompt.tags" :key="tag" size="tiny" round>{{ tag }}</n-tag>
            </div>
          </div>
        </div>
      </n-scrollbar>
    </n-card>

    <n-modal v-model:show="promptStore.showModal" preset="card" :title="promptStore.editingPrompt ? '编辑提示词' : '新建提示词'" style="width: 500px">
      <n-form ref="formRef" :model="formData" label-placement="left" label-width="60">
        <n-form-item label="标题" path="title">
          <n-input v-model:value="formData.title" placeholder="给提示词起个名字" />
        </n-form-item>
        <n-form-item label="内容" path="content">
          <n-input
            v-model:value="formData.content"
            type="textarea"
            placeholder="输入提示词内容..."
            :rows="4"
          />
        </n-form-item>
        <n-form-item label="分类" path="category">
          <n-select v-model:value="formData.category" :options="categoryOptions" />
        </n-form-item>
        <n-form-item label="标签" path="tags">
          <n-dynamic-tags v-model:value="formData.tags" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-button @click="handleCancel">取消</n-button>
        <n-button type="primary" @click="handleSave" style="margin-left: 8px">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NCard, NButton, NIcon, NInput, NScrollbar, NEmpty, NTag, NModal, NForm, NFormItem, NSelect, NDynamicTags, useMessage, useDialog } from 'naive-ui'
import { AddOutline, SearchOutline, TrashOutline, CreateOutline } from '@vicons/ionicons5'
import { usePromptStore, useGeneratorStore } from '../stores'
import type { Prompt, PromptFormData } from '../types'

const promptStore = usePromptStore()
const generatorStore = useGeneratorStore()
const message = useMessage()
const dialog = useDialog()

const formData = ref<PromptFormData>({
  title: '',
  content: '',
  category: 'general',
  tags: []
})

const categoryOptions = [
  { label: '通用', value: 'general' },
  { label: '人物', value: 'character' },
  { label: '风景', value: 'landscape' },
  { label: '艺术', value: 'art' },
  { label: '其他', value: 'other' }
]

watch(() => promptStore.showModal, (val) => {
  if (val && promptStore.editingPrompt) {
    formData.value = {
      title: promptStore.editingPrompt.title,
      content: promptStore.editingPrompt.content,
      category: promptStore.editingPrompt.category as PromptFormData['category'],
      tags: [...promptStore.editingPrompt.tags]
    }
  } else if (val) {
    formData.value = { title: '', content: '', category: 'general', tags: [] }
  }
})

function selectPrompt(prompt: Prompt) {
  generatorStore.prompt = prompt.content
  message.success(`已加载: ${prompt.title}`)
}

function handleDelete(id: number) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这个提示词吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await promptStore.remove(id)
      message.success('已删除')
    }
  })
}

function handleCancel() {
  promptStore.cancelEdit()
  formData.value = { title: '', content: '', category: 'general', tags: [] }
}

async function handleSave() {
  if (!formData.value.title || !formData.value.content) {
    message.warning('请填写标题和内容')
    return
  }

  if (promptStore.editingPrompt) {
    await promptStore.update(promptStore.editingPrompt.id!, formData.value)
    message.success('更新成功')
  } else {
    await promptStore.add(formData.value)
    message.success('保存成功')
  }

  promptStore.cancelEdit()
  formData.value = { title: '', content: '', category: 'general', tags: [] }
}
</script>

<style scoped>
.prompt-library {
  height: 100%;
}

.mb-3 {
  margin-bottom: 12px;
}

.prompt-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-item {
  padding: 12px;
  border-radius: 8px;
  background: #f5f5f5;
  cursor: pointer;
  transition: all 0.2s;
}

.prompt-item:hover {
  background: #e8e8e8;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.prompt-title {
  font-weight: 500;
  font-size: 14px;
}

.prompt-actions {
  display: flex;
  gap: 4px;
}

.prompt-content {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
}

.prompt-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
</style>
