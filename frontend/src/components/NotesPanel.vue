<template>
  <div class="notes-panel">
    <n-card title="我的笔记" size="small">
      <template #header-extra>
        <n-button size="small" type="primary" @click="showAddModal = true">
          新建笔记
        </n-button>
      </template>

      <n-space vertical size="small">
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索笔记..."
          clearable
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>

        <n-tabs v-model:value="activeTab" type="line" size="small">
          <n-tab-pane name="all" tab="全部">
            <NotesList
              :notes="filteredNotes"
              @edit="editNote"
              @delete="handleDelete"
            />
          </n-tab-pane>
          <n-tab-pane name="history" tab="历史记录">
            <NotesList
              :notes="historyNotes"
              @edit="editNote"
              @delete="handleDelete"
            />
          </n-tab-pane>
          <n-tab-pane name="prompt" tab="提示词">
            <NotesList
              :notes="promptNotes"
              @edit="editNote"
              @delete="handleDelete"
            />
          </n-tab-pane>
        </n-tabs>
      </n-space>
    </n-card>

    <n-modal
      v-model:show="showAddModal"
      preset="card"
      :title="editingNote ? '编辑笔记' : '新建笔记'"
      style="width: 500px; max-width: 90vw"
      :bordered="false"
    >
      <n-form ref="formRef" :model="noteForm" label-placement="left" label-width="80">
        <n-form-item label="关联类型" path="targetType">
          <n-select
            v-model:value="noteForm.targetType"
            :options="targetTypeOptions"
            placeholder="选择关联类型"
          />
        </n-form-item>
        <n-form-item v-if="noteForm.targetType !== 'prompt'" label="关联ID" path="targetId">
          <n-input-number
            v-model:value="noteForm.targetId"
            placeholder="输入关联记录ID"
            style="width: 100%"
          />
        </n-form-item>
        <n-form-item label="标题" path="title">
          <n-input v-model:value="noteForm.title" placeholder="笔记标题（可选）" />
        </n-form-item>
        <n-form-item label="内容" path="content">
          <n-input
            v-model:value="noteForm.content"
            type="textarea"
            placeholder="输入笔记内容..."
            :autosize="{ minRows: 4, maxRows: 10 }"
          />
        </n-form-item>
        <n-form-item label="标签" path="tags">
          <n-dynamic-tags v-model:value="noteForm.tags" />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="cancelEdit">取消</n-button>
          <n-button type="primary" @click="saveNote" :disabled="!noteForm.content">
            保存
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, toRaw } from 'vue'
import {
  NCard, NButton, NSpace, NInput, NTabs, NTabPane, NModal, NForm,
  NFormItem, NSelect, NInputNumber, NDynamicTags, NIcon, useMessage, useDialog
} from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import { db } from '../db'
import type { Note } from '../types/history'
import NotesList from './NotesList.vue'

const message = useMessage()
const dialog = useDialog()

const notes = ref<Note[]>([])
const searchKeyword = ref('')
const activeTab = ref('all')
const showAddModal = ref(false)
const editingNote = ref<Note | null>(null)

const noteForm = ref({
  targetType: 'history' as Note['targetType'],
  targetId: 0,
  title: '',
  content: '',
  tags: [] as string[]
})

const targetTypeOptions = [
  { label: '历史记录', value: 'history' },
  { label: '提示词', value: 'prompt' },
  { label: '工作流', value: 'workflow' }
]

const filteredNotes = computed(() => {
  if (!searchKeyword.value) return notes.value
  const keyword = searchKeyword.value.toLowerCase()
  return notes.value.filter(note =>
    note.content.toLowerCase().includes(keyword) ||
    note.title?.toLowerCase().includes(keyword) ||
    note.tags.some(t => t.toLowerCase().includes(keyword))
  )
})

const historyNotes = computed(() =>
  filteredNotes.value.filter(n => n.targetType === 'history')
)

const promptNotes = computed(() =>
  filteredNotes.value.filter(n => n.targetType === 'prompt')
)

async function loadNotes(): Promise<void> {
  notes.value = await db.notes.orderBy('updatedAt').reverse().toArray()
}

function editNote(note: Note): void {
  editingNote.value = note
  noteForm.value = {
    targetType: note.targetType,
    targetId: note.targetId,
    title: note.title || '',
    content: note.content,
    tags: [...note.tags]
  }
  showAddModal.value = true
}

function cancelEdit(): void {
  showAddModal.value = false
  editingNote.value = null
  noteForm.value = {
    targetType: 'history',
    targetId: 0,
    title: '',
    content: '',
    tags: []
  }
}

async function saveNote(): Promise<void> {
  if (!noteForm.value.content) return

  const now = new Date()
  const plainTags = toRaw(noteForm.value.tags)
  
  if (editingNote.value && editingNote.value.id) {
    await db.notes.update(editingNote.value.id, {
      targetType: noteForm.value.targetType,
      targetId: noteForm.value.targetId || 0,
      title: noteForm.value.title || undefined,
      content: noteForm.value.content,
      tags: plainTags,
      updatedAt: now
    })
    message.success('笔记已更新')
  } else {
    await db.notes.add({
      targetType: noteForm.value.targetType,
      targetId: noteForm.value.targetId || 0,
      title: noteForm.value.title || undefined,
      content: noteForm.value.content,
      tags: plainTags,
      createdAt: now,
      updatedAt: now
    })
    message.success('笔记已创建')
  }

  await loadNotes()
  cancelEdit()
}

function handleDelete(id: number): void {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这条笔记吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await db.notes.delete(id)
      await loadNotes()
      message.success('笔记已删除')
    }
  })
}

onMounted(() => {
  loadNotes()
})
</script>

<style scoped>
.notes-panel {
  height: 100%;
}
</style>
