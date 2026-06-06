<template>
  <div class="history-panel">
    <n-card title="生成历史" size="small">
      <template #header-extra>
        <n-space>
          <n-button
            v-if="historyStore.selectedIds.length > 0"
            size="small"
            type="error"
            @click="handleDeleteSelected"
          >
            删除选中 ({{ historyStore.selectedIds.length }})
          </n-button>
          <n-button
            v-else-if="historyStore.items.length > 0"
            size="small"
            @click="historyStore.selectAll"
          >
            全选
          </n-button>
        </n-space>
      </template>

      <n-tabs v-model:value="activeTab" type="line" size="small">
        <n-tab-pane name="all" tab="全部">
          <HistoryList
            :items="historyStore.items"
            :selected-ids="historyStore.selectedIds"
            @toggle-select="historyStore.toggleSelect"
            @reuse="reusePrompt"
            @delete="handleDelete"
            @favorite="historyStore.toggleFavorite"
            @detail="showDetail"
          />
        </n-tab-pane>
        <n-tab-pane name="favorites" tab="收藏">
          <HistoryList
            :items="historyStore.favorites"
            :selected-ids="historyStore.selectedIds"
            @toggle-select="historyStore.toggleSelect"
            @reuse="reusePrompt"
            @delete="handleDelete"
            @favorite="historyStore.toggleFavorite"
            @detail="showDetail"
          />
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <n-modal
      v-model:show="showDetailModal"
      preset="card"
      title="历史详情"
      style="width: 700px; max-width: 95vw"
      :bordered="false"
    >
      <template v-if="detailItem">
        <div class="detail-content">
          <div v-if="detailItem.imageUrl" class="detail-image">
            <n-image
              :src="detailItem.imageUrl"
              alt="generated"
              object-fit="contain"
              style="max-height: 300px"
            />
          </div>
          
          <n-descriptions label-placement="left" :column="2" bordered size="small">
            <n-descriptions-item label="提示词" :span="2">
              <n-ellipsis :line-clamp="3">{{ detailItem.prompt }}</n-ellipsis>
            </n-descriptions-item>
            <n-descriptions-item label="模型">{{ detailItem.model }}</n-descriptions-item>
            <n-descriptions-item label="尺寸">{{ detailItem.size }}</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.seed" label="Seed">{{ detailItem.seed }}</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.steps" label="步数">{{ detailItem.steps }}</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.cfgScale" label="CFG">{{ detailItem.cfgScale }}</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.sampler" label="采样器">{{ detailItem.sampler }}</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.providerName" label="供应商">{{ detailItem.providerName }}</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.generationTime" label="耗时">{{ detailItem.generationTime.toFixed(2) }}s</n-descriptions-item>
            <n-descriptions-item v-if="detailItem.negativePrompt" label="负面提示词" :span="2">
              <n-ellipsis :line-clamp="2">{{ detailItem.negativePrompt }}</n-ellipsis>
            </n-descriptions-item>
          </n-descriptions>

          <n-collapse>
            <n-collapse-item title="反推提示词" name="reverse">
              <PromptReverse
                v-if="detailItem.imageUrl"
                :image-url="detailItem.imageUrl"
                @use-prompt="handleUseReversePrompt"
              />
              <n-empty v-else description="无图片可分析" />
            </n-collapse-item>
          </n-collapse>

          <div class="detail-section">
            <div class="section-label">评分</div>
            <n-rate
              :value="detailItem.rating"
              @update:value="(val: number) => detailItem?.id && historyStore.setRating(detailItem.id, val)"
            />
          </div>

          <div class="detail-section">
            <div class="section-label">标签</div>
            <n-space>
              <n-tag
                v-for="tag in detailItem.tags"
                :key="tag"
                closable
                @close="removeTag(detailItem.id!, tag)"
              >
                {{ tag }}
              </n-tag>
              <n-input
                v-model:value="newTag"
                size="small"
                placeholder="添加标签"
                style="width: 100px"
                @keyup.enter="addTag(detailItem.id!)"
              />
            </n-space>
          </div>

          <div class="detail-section">
            <div class="section-label">备注</div>
            <n-input
              :value="detailItem.notes"
              type="textarea"
              placeholder="添加备注..."
              :autosize="{ minRows: 2, maxRows: 4 }"
              @blur="saveNotes(detailItem.id!, $event)"
            />
          </div>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NCard, NSpace, NButton, NTabs, NTabPane, NModal, NDescriptions,
  NDescriptionsItem, NImage, NEllipsis, NRate, NTag, NInput, NCollapse,
  NCollapseItem, useMessage, useDialog
} from 'naive-ui'
import { useHistoryStore, useGeneratorStore } from '../stores'
import HistoryList from './HistoryList.vue'
import PromptReverse from './PromptReverse.vue'

const historyStore = useHistoryStore()
const generatorStore = useGeneratorStore()
const message = useMessage()
const dialog = useDialog()

const activeTab = ref('all')
const showDetailModal = ref(false)
const newTag = ref('')

const detailItem = computed(() => historyStore.detailItem)

function reusePrompt(prompt: string) {
  generatorStore.prompt = prompt
  message.success('已复用提示词')
}

function handleUseReversePrompt(prompt: string) {
  generatorStore.prompt = prompt
  message.success('已应用反推的提示词')
  showDetailModal.value = false
}

function handleDelete(id: number) {
  dialog.warning({
    title: '确认删除',
    content: '确定要删除这条历史记录吗？',
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await historyStore.remove(id)
      message.success('已删除')
    }
  })
}

function handleDeleteSelected() {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除选中的 ${historyStore.selectedIds.length} 条记录吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await historyStore.deleteSelected()
      message.success('已删除')
    }
  })
}

function showDetail(id: number) {
  historyStore.setDetailItem(id)
  showDetailModal.value = true
}

async function addTag(id: number) {
  if (!newTag.value.trim()) return
  const item = historyStore.items.find(i => i.id === id)
  if (item) {
    const tags = [...item.tags, newTag.value.trim()]
    await historyStore.setTags(id, tags)
    newTag.value = ''
  }
}

async function removeTag(id: number, tag: string) {
  const item = historyStore.items.find(i => i.id === id)
  if (item) {
    const tags = item.tags.filter(t => t !== tag)
    await historyStore.setTags(id, tags)
  }
}

async function saveNotes(id: number, event: FocusEvent) {
  const target = event.target as HTMLTextAreaElement
  await historyStore.setNotes(id, target.value)
}
</script>

<style scoped>
.history-panel {
  height: 100%;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-image {
  display: flex;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 8px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-weight: 500;
  color: #666;
  font-size: 13px;
}
</style>
