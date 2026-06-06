<template>
  <div class="content-ingest">
    <n-alert type="info" :show-icon="false" class="mb-3">
      粘贴文章链接或内容，AI 自动提取为案例/知识/模板，智能去重后一键入库
    </n-alert>

    <!-- Step 1: 输入来源 -->
    <n-card size="small" title="① 输入来源" class="mb-3">
      <n-tabs v-model:value="inputMode" type="segment" size="small" class="mb-2">
        <n-tab-pane name="url" tab="网页链接" />
        <n-tab-pane name="text" tab="粘贴文本" />
      </n-tabs>

      <template v-if="inputMode === 'url'">
        <n-input-group>
          <n-input
            v-model:value="sourceUrl"
            placeholder="粘贴文章链接，如 https://mp.weixin.qq.com/..."
            clearable
          />
          <n-button type="primary" :loading="fetching" @click="fetchUrl" :disabled="!sourceUrl">
            抓取
          </n-button>
        </n-input-group>
      </template>

      <template v-else>
        <n-input
          v-model:value="articleContent"
          type="textarea"
          :rows="6"
          placeholder="直接粘贴文章内容..."
        />
      </template>

      <n-collapse-transition :show="!!articleContent && inputMode === 'url'">
        <n-card size="small" class="mt-2" title="已抓取内容预览">
          <n-ellipsis :line-clamp="4" :tooltip="false">
            {{ articleContent }}
          </n-ellipsis>
          <template #action>
            <n-text depth="3">共 {{ articleContent.length }} 字</n-text>
          </template>
        </n-card>
      </n-collapse-transition>
    </n-card>

    <!-- Step 2: 选择提取类型 -->
    <n-card size="small" title="② 提取目标" class="mb-3">
      <n-radio-group v-model:value="targetType" size="small">
        <n-radio-button value="cases">案例</n-radio-button>
        <n-radio-button value="knowledge">知识库</n-radio-button>
        <n-radio-button value="templates">模板</n-radio-button>
      </n-radio-group>
      <n-text depth="3" class="type-hint">
        {{ typeHints[targetType] }}
      </n-text>
    </n-card>

    <!-- Step 3: LLM 配置 & 提取 -->
    <n-card size="small" title="③ AI 提取" class="mb-3">
      <template v-if="!providerStore.hasConfiguredLLM">
        <n-alert type="warning" :show-icon="true">
          请先在「设置 → 大模型配置」中添加 LLM 供应商（如 DeepSeek、智谱等）
        </n-alert>
      </template>
      <template v-else>
        <n-space align="center" class="mb-2">
          <n-text depth="3">使用模型：</n-text>
          <n-select
            v-if="providerStore.llmProviders.length > 1"
            v-model:value="selectedLLMId"
            :options="llmOptions"
            size="small"
            style="width: 200px"
          />
          <n-tag v-else type="info" size="small">
            {{ providerStore.defaultLLMProvider?.name }}
          </n-tag>
        </n-space>
        <n-button
          type="primary"
          block
          :loading="extracting"
          :disabled="!articleContent || !hasLLM"
          @click="extractContent"
        >
          AI 智能提取 + 去重对比
        </n-button>
      </template>
    </n-card>

    <!-- Step 4: 对比统计 -->
    <n-card v-if="extractStats" size="small" title="对比结果" class="mb-3">
      <n-space>
        <n-tag type="success" round>新增 {{ extractStats.new }}</n-tag>
        <n-tag type="warning" round>建议替换 {{ extractStats.replace }}</n-tag>
        <n-tag type="error" round>重复 {{ extractStats.duplicate }}</n-tag>
        <n-tag type="info" round v-if="extractStats.keep_both">各有特色 {{ extractStats.keep_both }}</n-tag>
      </n-space>
    </n-card>

    <!-- Step 5: 预览 & 编辑 -->
    <n-card v-if="extractedItems.length > 0" size="small" :title="`④ 预览结果（${extractedItems.length} 条）`" class="mb-3">
      <n-scrollbar style="max-height: 500px">
        <div v-for="(item, index) in extractedItems" :key="index" class="item-row" :class="'verdict-' + getVerdict(item)">
          <div class="item-header">
            <n-checkbox v-model:checked="itemChecked[index]" />
            <n-tag :type="verdictTagType(getVerdict(item))" size="small" class="verdict-tag">
              {{ verdictLabel(getVerdict(item)) }}
            </n-tag>
            <span class="item-name">{{ item.name || item.id }}</span>
            <n-space size="small" class="item-actions">
              <n-button size="tiny" @click="previewItem(item)">详情</n-button>
              <n-button v-if="getMatchedExisting(item)" size="tiny" type="info" @click="showCompare(item)">
                对比
              </n-button>
              <n-button size="tiny" type="error" @click="removeItem(index)">移除</n-button>
            </n-space>
          </div>

          <div class="item-reason">
            <n-text depth="3" style="font-size: 12px">
              {{ getComparisonReason(item) }}
            </n-text>
          </div>

          <div class="item-desc" v-if="item.description">
            <n-ellipsis :line-clamp="1" :tooltip="false">
              {{ item.description }}
            </n-ellipsis>
          </div>

          <n-space v-if="item.tags" size="small" class="item-tags">
            <n-tag v-for="tag in (item.tags || []).slice(0, 5)" :key="tag" size="tiny">{{ tag }}</n-tag>
          </n-space>
        </div>
      </n-scrollbar>

      <n-space justify="space-between" class="mt-2">
        <n-space>
          <n-button size="small" @click="selectRecommended">智能选择</n-button>
          <n-button size="small" @click="selectAll">全选</n-button>
          <n-button size="small" @click="deselectAll">取消</n-button>
        </n-space>
        <n-button type="primary" :loading="saving" @click="saveSelected" :disabled="selectedCount === 0">
          保存选中 ({{ selectedCount }})
        </n-button>
      </n-space>
    </n-card>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showPreviewModal" preset="card" title="条目详情" style="width: 600px; max-width: 90vw">
      <n-scrollbar style="max-height: 70vh">
        <pre class="json-preview">{{ JSON.stringify(previewingItem, null, 2) }}</pre>
      </n-scrollbar>
    </n-modal>

    <!-- 对比弹窗 -->
    <n-modal v-model:show="showCompareModal" preset="card" title="新旧内容对比" style="width: 800px; max-width: 95vw">
      <template v-if="comparingItem">
        <n-grid :cols="2" :x-gap="12">
          <n-gi>
            <n-card size="small" title="新提取的内容" :bordered="true">
              <n-descriptions :column="1" label-placement="left" size="small" bordered>
                <n-descriptions-item label="名称">{{ comparingItem.name }}</n-descriptions-item>
                <n-descriptions-item label="描述">{{ comparingItem.description }}</n-descriptions-item>
                <n-descriptions-item v-if="comparingItem.prompt" label="提示词">
                  <n-ellipsis :line-clamp="4" :tooltip="false">{{ comparingItem.prompt }}</n-ellipsis>
                </n-descriptions-item>
                <n-descriptions-item v-if="comparingItem.tips" label="技巧">
                  {{ Array.isArray(comparingItem.tips) ? comparingItem.tips.join('；') : comparingItem.tips }}
                </n-descriptions-item>
              </n-descriptions>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card size="small" title="已有的内容" :bordered="true">
              <template v-if="comparingExisting">
                <n-descriptions :column="1" label-placement="left" size="small" bordered>
                  <n-descriptions-item label="名称">{{ comparingExisting.name }}</n-descriptions-item>
                  <n-descriptions-item label="描述">{{ comparingExisting.description }}</n-descriptions-item>
                  <n-descriptions-item v-if="comparingExisting.prompt" label="提示词">
                    <n-ellipsis :line-clamp="4" :tooltip="false">{{ comparingExisting.prompt }}</n-ellipsis>
                  </n-descriptions-item>
                  <n-descriptions-item v-if="comparingExisting.tips" label="技巧">
                    {{ Array.isArray(comparingExisting.tips) ? comparingExisting.tips.join('；') : comparingExisting.tips }}
                  </n-descriptions-item>
                </n-descriptions>
              </template>
            </n-card>
          </n-gi>
        </n-grid>

        <n-card size="small" class="mt-2">
          <n-space align="center">
            <n-tag :type="verdictTagType(getVerdict(comparingItem))" size="small">
              {{ verdictLabel(getVerdict(comparingItem)) }}
            </n-tag>
            <n-text>{{ getComparisonReason(comparingItem) }}</n-text>
          </n-space>
          <n-text v-if="comparingItem._comparison?.match_reason" depth="3" style="display: block; margin-top: 4px; font-size: 12px">
            匹配依据：{{ comparingItem._comparison.match_reason }}
            <template v-if="comparingItem._comparison.similarity_score">
              （相似度 {{ (comparingItem._comparison.similarity_score * 100).toFixed(0) }}%）
            </template>
          </n-text>
        </n-card>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import axios from 'axios'
import { useProviderStore, useDataStore } from '../../stores'
import { config } from '../../config'

const message = useMessage()
const providerStore = useProviderStore()
const dataStore = useDataStore()

const inputMode = ref<'url' | 'text'>('url')
const sourceUrl = ref('')
const articleContent = ref('')
const targetType = ref('cases')
const selectedLLMId = ref(providerStore.defaultLLMProviderId || '')

const fetching = ref(false)
const extracting = ref(false)
const saving = ref(false)

const extractedItems = ref<any[]>([])
const itemChecked = ref<boolean[]>([])
const extractStats = ref<any>(null)

const showPreviewModal = ref(false)
const previewingItem = ref<any>(null)
const showCompareModal = ref(false)
const comparingItem = ref<any>(null)
const comparingExisting = ref<any>(null)

const typeHints: Record<string, string> = {
  cases: '从文章中提取 AI 生图/视频案例，包含完整提示词、参数和技巧',
  knowledge: '提取 AI 绘图术语、技法知识点，丰富知识库',
  templates: '提取可复用的提示词模板，带有可替换变量',
}

const baseURL = computed(() => config.apiBaseUrl)

const currentLLM = computed(() => {
  if (selectedLLMId.value) {
    return providerStore.getLLMProviderById(selectedLLMId.value)
  }
  return providerStore.defaultLLMProvider
})

const hasLLM = computed(() => !!currentLLM.value?.apiKey)

const llmOptions = computed(() =>
  providerStore.llmProviders.map(p => ({
    label: `${p.name}${p.isFree ? ' (免费)' : ''}`,
    value: p.id
  }))
)

const selectedCount = computed(() => itemChecked.value.filter(Boolean).length)

// ── 对比相关辅助函数 ─────────────────────────────────────────────────

function getVerdict(item: any): string {
  return item?._comparison?.verdict || 'new'
}

function getComparisonReason(item: any): string {
  return item?._comparison?.reason || ''
}

function getMatchedExisting(item: any): any {
  return item?._comparison?.matched_existing || null
}

function verdictLabel(verdict: string): string {
  const map: Record<string, string> = {
    new: '新内容',
    replace: '建议替换',
    duplicate: '重复',
    keep_both: '各有特色',
  }
  return map[verdict] || verdict
}

function verdictTagType(verdict: string): 'success' | 'warning' | 'error' | 'info' | 'default' {
  const map: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    new: 'success',
    replace: 'warning',
    duplicate: 'error',
    keep_both: 'info',
  }
  return map[verdict] || 'default'
}

/** 智能选择：自动勾选 new + replace + keep_both，取消 duplicate */
function selectRecommended() {
  itemChecked.value = extractedItems.value.map(item => {
    const verdict = getVerdict(item)
    return verdict !== 'duplicate'
  })
  message.info('已智能选择：采纳新内容和建议替换项，跳过重复项')
}

// ── 网络请求 ─────────────────────────────────────────────────────────

async function fetchUrl() {
  if (!sourceUrl.value) return
  fetching.value = true
  try {
    const res = await axios.post(`${baseURL.value}/api/ingest/fetch-url`, {
      url: sourceUrl.value
    })
    if (res.data.success) {
      articleContent.value = res.data.content
      message.success(`抓取成功，共 ${res.data.length} 字`)
    } else {
      message.error(res.data.error || '抓取失败')
    }
  } catch (e: any) {
    message.error('抓取失败：' + (e.userMessage || e.message || '网络错误'))
  } finally {
    fetching.value = false
  }
}

async function extractContent() {
  if (!articleContent.value || !currentLLM.value) return
  extracting.value = true
  extractStats.value = null
  try {
    const llm = currentLLM.value
    const res = await axios.post(`${baseURL.value}/api/ingest/extract`, {
      content: articleContent.value,
      source_url: sourceUrl.value || undefined,
      target_type: targetType.value,
      llm_endpoint: llm.llmEndpoint || llm.endpoint,
      llm_api_key: llm.apiKey,
      llm_model: llm.llmModel || llm.defaultModel
    }, { timeout: 180000 })
    
    if (res.data.success) {
      extractedItems.value = res.data.items
      extractStats.value = res.data.stats

      // 根据对比结果智能默认勾选
      itemChecked.value = res.data.items.map((item: any) => {
        const verdict = getVerdict(item)
        return verdict !== 'duplicate' // duplicate 默认不勾选
      })

      const total = res.data.count
      const dupCount = res.data.stats?.duplicate || 0
      if (dupCount > 0) {
        message.info(`AI 提取到 ${total} 条，其中 ${dupCount} 条与已有内容重复已自动跳过`)
      } else {
        message.success(`AI 提取到 ${total} 条内容，全部为新数据！`)
      }
    } else {
      message.error(res.data.error || '提取失败')
    }
  } catch (e: any) {
    message.error('提取失败：' + (e.userMessage || e.response?.data?.error || e.message || '网络错误'))
  } finally {
    extracting.value = false
  }
}

async function saveSelected() {
  const selectedItems = extractedItems.value.filter((_, i) => itemChecked.value[i])
  if (selectedItems.length === 0) {
    message.warning('请至少选择一条')
    return
  }

  // 收集需要替换的 ID（verdict 为 replace 的条目，用已有条目的 id）
  const replaceIds: string[] = []
  for (const item of selectedItems) {
    if (getVerdict(item) === 'replace') {
      const existing = getMatchedExisting(item)
      if (existing?.id) {
        replaceIds.push(existing.id)
        // 用被替换条目的 id 来覆盖新条目的 id，确保替换而非新增
        item.id = existing.id
      }
    }
  }

  saving.value = true
  try {
    const res = await axios.post(`${baseURL.value}/api/ingest/save`, {
      target_type: targetType.value,
      items: selectedItems,
      replace_ids: replaceIds.length > 0 ? replaceIds : undefined
    })
    if (res.data.success) {
      message.success(res.data.message)
      await dataStore.loadAll()
      // 移除已保存的
      extractedItems.value = extractedItems.value.filter((_, i) => !itemChecked.value[i])
      itemChecked.value = extractedItems.value.map(() => true)
      extractStats.value = null
    } else {
      message.error(res.data.error || '保存失败')
    }
  } catch (e: any) {
    message.error('保存失败：' + (e.userMessage || e.message || '网络错误'))
  } finally {
    saving.value = false
  }
}

function previewItem(item: any) {
  // 展示时去掉 _comparison 以保持干净
  const clean = { ...item }
  delete clean._comparison
  previewingItem.value = clean
  showPreviewModal.value = true
}

function showCompare(item: any) {
  comparingItem.value = item
  comparingExisting.value = getMatchedExisting(item)
  showCompareModal.value = true
}

function removeItem(index: number) {
  extractedItems.value.splice(index, 1)
  itemChecked.value.splice(index, 1)
}

function selectAll() {
  itemChecked.value = itemChecked.value.map(() => true)
}

function deselectAll() {
  itemChecked.value = itemChecked.value.map(() => false)
}
</script>

<style scoped>
.content-ingest {
  padding: 8px 0;
}


.type-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
}

.item-row {
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  border-left: 3px solid transparent;
  transition: all 0.2s;
}

.item-row:hover {
  background: rgba(0, 0, 0, 0.02);
}

.verdict-new {
  border-left-color: #18a058;
  background: rgba(24, 160, 88, 0.04);
}

.verdict-replace {
  border-left-color: #f0a020;
  background: rgba(240, 160, 32, 0.04);
}

.verdict-duplicate {
  border-left-color: #d03050;
  background: rgba(208, 48, 80, 0.04);
  opacity: 0.7;
}

.verdict-keep_both {
  border-left-color: #2080f0;
  background: rgba(32, 128, 240, 0.04);
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.verdict-tag {
  flex-shrink: 0;
}

.item-name {
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-actions {
  flex-shrink: 0;
}

.item-reason {
  margin: 4px 0 4px 28px;
}

.item-desc {
  margin: 2px 0 2px 28px;
  font-size: 13px;
  color: #666;
}

.item-tags {
  margin: 4px 0 0 28px;
}

.json-preview {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  padding: 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
}
</style>
