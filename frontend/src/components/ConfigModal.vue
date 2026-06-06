<template>
  <div class="config-modal">
    <n-modal v-model:show="configStore.showConfigModal" preset="card" style="width: 760px" title="配置创作能力">
      <div v-if="!hasAnyConfig" class="quick-start-banner mb-3">
        <n-alert type="info" :show-icon="false">
          <div class="quick-start-title">首次使用，先配置一个生成图片能力</div>
          <div class="quick-start-copy">
            选择一个平台预设，填入 API Key 保存。模型和 Endpoint 会自动带出，通常不用修改。
          </div>
        </n-alert>
      </div>

      <div class="config-layout">
        <div class="config-sidebar">
          <button
            v-for="item in capabilityCards"
            :key="item.tab"
            type="button"
            class="sidebar-item"
            :class="{ active: activeTab === item.tab, ready: item.ready }"
            @click="activeTab = item.tab"
          >
            <div class="sidebar-item-content">
              <n-icon :component="item.icon" class="capability-icon" />
              <div class="capability-text">
                <span class="capability-title">{{ item.title }}</span>
                <span class="capability-desc">{{ item.desc }}</span>
              </div>
            </div>
            <n-tag :type="item.tagType || (item.ready ? 'success' : 'default')" size="small" class="sidebar-tag">
              {{ item.label || (item.ready ? '已配置' : '未配置') }}
            </n-tag>
          </button>
        </div>

        <div class="config-content-area">
          <!-- 生成能力：图像 + 视频 + 编辑 -->
          <div v-show="activeTab === 'generation'">
            <div class="section-block">
              <div class="section-header">
                <n-icon :component="Image" class="section-icon" />
                <span class="section-title">图像生成</span>
                <n-tag v-if="providerStore.hasConfiguredImageProvider" type="success" size="small">已配置</n-tag>
              </div>
              <n-alert type="info" size="small" class="mb-2">
                电商主图、海报、PPT 配图等图片生成任务，首次使用只需配置这一项。
              </n-alert>
              <ProviderManager />
            </div>

            <n-divider />

            <div class="section-block">
              <div class="section-header">
                <n-icon :component="Film" class="section-icon" />
                <span class="section-title">视频生成</span>
                <n-tag v-if="providerStore.hasConfiguredVideoProvider" type="success" size="small">已配置</n-tag>
              </div>
              <n-list bordered>
                <n-list-item v-for="preset in videoPresets" :key="preset.type">
                  <n-thing :title="preset.name">
                    <template #avatar>
                      <n-tag :type="preset.recommended ? 'success' : 'default'">
                        {{ preset.recommended ? '推荐' : '可选' }}
                      </n-tag>
                    </template>
                    <template #description>{{ preset.description }}</template>
                    <template #header-extra>
                      <n-space align="center">
                        <n-tag v-if="isVideoConfigured(preset.type)" type="success" size="small">已配置</n-tag>
                        <n-button size="small" :type="isVideoConfigured(preset.type) ? 'default' : 'primary'" @click="showVideoConfigModal(preset)">
                          {{ isVideoConfigured(preset.type) ? '修改' : '配置' }}
                        </n-button>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
              <n-button block dashed class="mt-2" @click="openCustomProvider('video')">+ 自定义视频供应商</n-button>
            </div>

            <n-divider />

            <div class="section-block">
              <div class="section-header">
                <n-icon :component="Pencil" class="section-icon" />
                <span class="section-title">图片编辑</span>
                <n-tag v-if="providerStore.hasConfiguredEditProvider" type="success" size="small">已配置</n-tag>
              </div>
              <n-list bordered>
                <n-list-item v-for="preset in editPresets" :key="preset.type">
                  <n-thing :title="preset.name">
                    <template #avatar><n-tag type="success">推荐</n-tag></template>
                    <template #description>{{ preset.description }}</template>
                    <template #header-extra>
                      <n-space align="center">
                        <n-tag v-if="isEditConfigured(preset.type)" type="success" size="small">已配置</n-tag>
                        <n-button size="small" :type="isEditConfigured(preset.type) ? 'default' : 'primary'" @click="showEditConfigModal(preset)">
                          {{ isEditConfigured(preset.type) ? '修改' : '配置' }}
                        </n-button>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
              <n-button block dashed class="mt-2" @click="openCustomProvider('edit')">+ 自定义编辑供应商</n-button>
            </div>
          </div>

          <!-- AI 能力：视觉模型 + LLM -->
          <div v-show="activeTab === 'ai'">
            <div class="section-block">
              <div class="section-header">
                <n-icon :component="Eye" class="section-icon" />
                <span class="section-title">图片分析（视觉模型）</span>
                <n-tag v-if="hasConfiguredVision" type="success" size="small">已配置</n-tag>
              </div>
              <n-alert type="info" size="small" class="mb-2">
                上传图片后自动分析并反推提示词。
              </n-alert>
              <n-list bordered>
                <n-list-item v-for="preset in visionPresets" :key="preset.type">
                  <n-thing :title="preset.name">
                    <template #avatar>
                      <n-tag :type="preset.type === 'zhipu' ? 'success' : 'default'">
                        {{ preset.type === 'zhipu' ? '免费' : '付费' }}
                      </n-tag>
                    </template>
                    <template #description>{{ preset.description }}</template>
                    <template #header-extra>
                      <n-space align="center">
                        <n-tag v-if="isConfigured(preset.type)" type="success" size="small">已配置</n-tag>
                        <n-button size="small" :type="isConfigured(preset.type) ? 'default' : 'primary'" @click="showConfigModal(preset)">
                          {{ isConfigured(preset.type) ? '修改' : '配置' }}
                        </n-button>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
              <n-button block dashed class="mt-2" @click="openCustomProvider('vision')">+ 自定义视觉供应商</n-button>
            </div>

            <n-divider />

            <div class="section-block">
              <div class="section-header">
                <n-icon :component="Brain" class="section-icon" />
                <span class="section-title">提示词优化（LLM）</span>
                <n-tag v-if="providerStore.hasConfiguredLLM" type="success" size="small">已配置</n-tag>
              </div>
              <n-alert type="info" size="small" class="mb-2">
                把中文需求优化成专业提示词，也用于 AI 入库的智能提取和去重。
              </n-alert>
              <n-list bordered>
                <n-list-item v-for="preset in llmPresets" :key="preset.type + preset.name">
                  <n-thing :title="preset.name">
                    <template #avatar><n-tag :type="preset.tagType">{{ preset.tagLabel }}</n-tag></template>
                    <template #description>{{ preset.description }}</template>
                    <template #header-extra>
                      <n-space align="center">
                        <n-tag v-if="isLLMConfigured(preset.name)" type="success" size="small">已配置</n-tag>
                        <n-button size="small" :type="isLLMConfigured(preset.name) ? 'default' : 'primary'" @click="showLLMConfigModal(preset)">
                          {{ isLLMConfigured(preset.name) ? '修改' : '配置' }}
                        </n-button>
                        <n-button v-if="isLLMConfigured(preset.name)" size="small" type="error" @click="removeLLMConfig(preset.name)">删除</n-button>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
            </div>
          </div>

          <!-- 高级设置 -->
          <div v-show="activeTab === 'advanced'">
            <n-card size="small" title="内容管理" class="mb-3">
              <n-space vertical>
                <n-space align="center" justify="space-between">
                  <n-text>启用 AI 内容入库</n-text>
                  <n-switch v-model:value="adminModeEnabled" @update:value="toggleAdminMode" />
                </n-space>
                <n-text depth="3" style="font-size: 13px">
                  开启后右侧面板将显示"入库"标签，支持从网页链接或粘贴文本中 AI 提取案例、知识库条目和模板。
                </n-text>
              </n-space>
            </n-card>

            <n-card v-if="!providerStore.hasConfiguredLLM" size="small">
              <template #header>
                <n-space align="center" :size="4">
                  <n-icon :component="AlertTriangle" />
                  <span>前提条件</span>
                </n-space>
              </template>
              <n-text depth="3">
                内容入库需要配置大语言模型（LLM）才能使用。请在「AI 能力」中先配置一个 LLM 供应商。
              </n-text>
            </n-card>
          </div>
        </div>
      </div>
    </n-modal>

    <n-modal
      v-model:show="showApiKeyModal"
      preset="card"
      :title="`配置 ${currentPreset?.name}`"
      style="width: 450px"
    >
      <n-form label-placement="left" label-width="100">
        <n-form-item label="API Key">
          <n-input
            v-model:value="apiKeyInput"
            type="password"
            show-password-on="click"
            :placeholder="currentPreset?.keyPlaceholder || '请输入 API Key'"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-input
            v-model:value="visionModelInput"
            :placeholder="currentPreset?.visionModel || '请输入模型名称'"
          />
        </n-form-item>
        <n-form-item label="API Endpoint">
          <n-input
            v-model:value="endpointInput"
            :placeholder="currentPreset?.visionEndpoint || '自定义 API Endpoint'"
          />
        </n-form-item>
      </n-form>
      
      <template v-if="currentPreset?.helpUrl">
        <n-divider />
        <n-space vertical>
          <n-text depth="3">获取 API Key：</n-text>
          <n-button text type="primary" tag="a" :href="currentPreset.helpUrl" target="_blank">
            {{ currentPreset.helpText || '点击前往获取' }}
          </n-button>
        </n-space>
      </template>

      <template #footer>
        <n-space justify="space-between" style="width: 100%">
          <div>
            <n-button
              :loading="testingVision"
              :disabled="!apiKeyInput"
              @click="testConnection(endpointInput || currentPreset?.visionEndpoint || '', apiKeyInput, currentPreset?.type || 'image', 'vision')"
            >
              <template #icon><n-icon :component="testingVision ? undefined : (testTarget === 'vision' && testResult?.success ? CheckCircle : XCircle)" /></template>
              测试连接
            </n-button>
          </div>
          <n-space>
            <n-button @click="showApiKeyModal = false">取消</n-button>
            <n-button type="primary" @click="saveVisionConfig" :disabled="!apiKeyInput">
              保存
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>
    
    <!-- ── 视频自定义配置弹窗 ── -->
    <n-modal
      v-model:show="showVideoModal"
      preset="card"
      :title="`配置 ${currentVideoPreset?.name || '视频供应商'}`"
      style="width: 450px"
    >
      <n-form label-placement="left" label-width="100">
        <n-form-item label="API Key">
          <n-input
            v-model:value="videoApiKeyInput"
            type="password"
            show-password-on="click"
            :placeholder="currentVideoPreset?.keyPlaceholder || '请输入 API Key'"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-input
            v-model:value="videoModelInput"
            :placeholder="currentVideoPreset?.defaultModel || '请输入模型名称'"
          />
        </n-form-item>
        <n-form-item label="API Endpoint">
          <n-input
            v-model:value="videoEndpointInput"
            :placeholder="currentVideoPreset?.endpoint || 'API Endpoint'"
          />
        </n-form-item>
      </n-form>
      
      <template v-if="currentVideoPreset?.helpUrl">
        <n-divider />
        <n-space vertical>
          <n-text depth="3">获取 API Key：</n-text>
          <n-button text type="primary" tag="a" :href="currentVideoPreset.helpUrl" target="_blank">
            {{ currentVideoPreset.helpText || '点击前往获取' }}
          </n-button>
        </n-space>
      </template>

      <template #footer>
        <n-space justify="space-between" style="width: 100%">
          <div>
            <n-button
              :loading="testingVideo"
              :disabled="!videoApiKeyInput"
              @click="testConnection(videoEndpointInput, videoApiKeyInput, currentVideoPreset?.type || 'video', 'video')"
            >
              测试连接
            </n-button>
          </div>
          <n-space>
            <n-button @click="showVideoModal = false">取消</n-button>
            <n-button type="primary" @click="saveVideoConfig" :disabled="!videoApiKeyInput">
              保存
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>
    
    <!-- ── 图片编辑自定义配置弹窗 ── -->
    <n-modal
      v-model:show="showEditModal"
      preset="card"
      :title="`配置 ${currentEditPreset?.name || '图片编辑供应商'}`"
      style="width: 450px"
    >
      <n-form label-placement="left" label-width="100">
        <n-form-item label="API Key">
          <n-input
            v-model:value="editApiKeyInput"
            type="password"
            show-password-on="click"
            :placeholder="currentEditPreset?.keyPlaceholder || '请输入 API Key'"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-input
            v-model:value="editModelInput"
            :placeholder="currentEditPreset?.defaultModel || '请输入模型名称'"
          />
        </n-form-item>
        <n-form-item label="API Endpoint">
          <n-input
            v-model:value="editEndpointInput"
            :placeholder="currentEditPreset?.endpoint || 'API Endpoint'"
          />
        </n-form-item>
      </n-form>
      
      <template v-if="currentEditPreset?.helpUrl">
        <n-divider />
        <n-space vertical>
          <n-text depth="3">获取 API Key：</n-text>
          <n-button text type="primary" tag="a" :href="currentEditPreset.helpUrl" target="_blank">
            {{ currentEditPreset.helpText || '点击前往获取' }}
          </n-button>
        </n-space>
      </template>

      <template #footer>
        <n-space justify="space-between" style="width: 100%">
          <div>
            <n-button
              :loading="testingEdit"
              :disabled="!editApiKeyInput"
              @click="testConnection(editEndpointInput, editApiKeyInput, currentEditPreset?.type || 'edit', 'edit')"
            >
              测试连接
            </n-button>
          </div>
          <n-space>
            <n-button @click="showEditModal = false">取消</n-button>
            <n-button type="primary" @click="saveEditConfig" :disabled="!editApiKeyInput">
              保存
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <!-- ── LLM 配置弹窗 ── -->
    <n-modal
      v-model:show="showLLMModal"
      preset="card"
      :title="`配置 ${currentLLMPreset?.name || 'LLM 供应商'}`"
      style="width: 450px"
    >
      <n-form label-placement="left" label-width="100">
        <n-form-item label="API Key">
          <n-input
            v-model:value="llmApiKeyInput"
            type="password"
            show-password-on="click"
            :placeholder="currentLLMPreset?.keyPlaceholder || '请输入 API Key'"
          />
        </n-form-item>
        <n-form-item label="模型">
          <n-input
            v-model:value="llmModelInput"
            :placeholder="currentLLMPreset?.defaultModel || '请输入模型名称'"
          />
          <template #feedback>
            <n-text depth="3" style="font-size: 12px">常用：{{ (currentLLMPreset?.models ?? []).map(m => m.value).join(' / ') }}</n-text>
          </template>
        </n-form-item>
        <n-form-item label="Endpoint">
          <n-input
            v-model:value="llmEndpointInput"
            :placeholder="currentLLMPreset?.endpoint || 'API Endpoint'"
          />
          <template #feedback>
            <n-text depth="3" style="font-size: 12px">通常无需修改，使用默认值即可</n-text>
          </template>
        </n-form-item>
      </n-form>
      
      <template v-if="currentLLMPreset?.helpUrl">
        <n-divider />
        <n-space vertical>
          <n-text depth="3">获取 API Key：</n-text>
          <n-button text type="primary" tag="a" :href="currentLLMPreset.helpUrl" target="_blank">
            {{ currentLLMPreset.helpText || '点击前往获取' }}
          </n-button>
        </n-space>
      </template>

      <template #footer>
        <n-space justify="space-between" style="width: 100%">
          <div>
            <n-button
              :loading="testingLLM"
              :disabled="!llmApiKeyInput"
              @click="testConnection(llmEndpointInput, llmApiKeyInput, 'llm', 'llm')"
            >
              测试连接
            </n-button>
          </div>
          <n-space>
            <n-button @click="showLLMModal = false">取消</n-button>
            <n-button type="primary" @click="saveLLMConfig" :disabled="!llmApiKeyInput">
              保存
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <!-- ── 自定义供应商弹窗 ── -->
    <n-modal
      v-model:show="showCustomModal"
      preset="card"
      title="自定义供应商"
      style="width: 480px"
    >
      <p class="custom-modal-hint mb-3">填写以下信息接入自定义 API 供应商（适用于未列出的模型平台）</p>
      <n-form label-placement="left" label-width="100">
        <n-form-item label="供应商名称">
          <n-input v-model:value="customForm.name" placeholder="例如：Stability AI、Midjourney 代理" />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input
            v-model:value="customForm.apiKey"
            type="password"
            show-password-on="click"
            placeholder="输入 API Key"
          />
        </n-form-item>
        <n-form-item label="API Endpoint">
          <n-input
            v-model:value="customForm.endpoint"
            placeholder="https://api.example.com/v1/generate"
          />
        </n-form-item>
        <n-form-item label="模型名称">
          <n-input
            v-model:value="customForm.model"
            placeholder="例如：stable-diffusion-xl"
          />
          <template #feedback>
            <n-text depth="3" style="font-size: 12px">用于生成时选择使用的具体模型</n-text>
          </template>
        </n-form-item>
        <n-form-item label="类型">
          <n-tag type="info">{{ customCapability === 'video' ? '视频生成' : customCapability === 'edit' ? '图片编辑' : '图片分析' }}</n-tag>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="space-between" style="width: 100%">
          <div>
            <n-button
              :loading="testingCustom"
              :disabled="!customForm.apiKey || !customForm.endpoint"
              @click="testConnection(customForm.endpoint, customForm.apiKey, customCapability, 'custom')"
            >
              测试连接
            </n-button>
          </div>
          <n-space>
            <n-button @click="showCustomModal = false">取消</n-button>
            <n-button type="primary" @click="saveCustomProvider" :disabled="!customForm.name || !customForm.apiKey">
              保存
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Component } from 'vue'
import {
  NModal, NForm, NFormItem, NInput,
  NAlert, NCard, NTag, NList, NListItem, NThing, NButton, NSpace, NText, NDivider, NSwitch,
  useMessage
} from 'naive-ui'
import { useConfigStore, useProviderStore } from '../stores'
import ProviderManager from './ProviderManager.vue'
import { apiService } from '../api'
import type { ProviderType, ProviderCapability } from '../types/provider'
import { Image, Film, Pencil, Brain, Eye, Settings, AlertTriangle, CheckCircle, XCircle } from 'lucide-vue-next'

const message = useMessage()

const configStore = useConfigStore()
const providerStore = useProviderStore()

const activeTab = ref('generation')
type TagType = 'success' | 'error' | 'warning' | 'default'
interface CapabilityCard {
  tab: string
  icon: Component
  title: string
  desc: string
  ready: boolean
  label: string
  tagType: TagType
}

/** 管理端开关 */
const adminModeEnabled = ref(localStorage.getItem('ai_studio_admin') === 'true')
function toggleAdminMode(val: boolean) {
  localStorage.setItem('ai_studio_admin', String(val))
  adminModeEnabled.value = val
  if (val) message.success('内容管理已开启，右侧面板将显示"入库"标签')
  else message.info('内容管理已关闭')
}

const hasAnyConfig = computed(() =>
  providerStore.hasConfiguredImageProvider ||
  providerStore.hasConfiguredVideoProvider ||
  providerStore.hasConfiguredEditProvider ||
  providerStore.hasConfiguredLLM
)

const hasConfiguredVision = computed(() =>
  providerStore.visionProviderPresets.some(p => providerStore.providers.find(vp => vp.type === p.type)?.apiKey)
)

/** 获取某能力供应商的状态摘要 */
function capabilityStatus(cap: ProviderCapability): { ready: boolean; label: string; tagType: TagType } {
  const providers = providerStore.getProvidersByCapability(cap).filter(p => p.apiKey)
  if (providers.length === 0) return { ready: false, label: '未配置', tagType: 'default' }
  const allActive = providers.every(p => p.status === 'active')
  const anyError = providers.some(p => p.status === 'error')
  if (allActive) return { ready: true, label: '已连接', tagType: 'success' }
  if (anyError) return { ready: true, label: '有异常', tagType: 'error' }
  return { ready: true, label: '待检测', tagType: 'warning' }
}

const capabilityCards = computed<CapabilityCard[]>(() => {
  const genReady = providerStore.hasConfiguredImageProvider || providerStore.hasConfiguredVideoProvider || providerStore.hasConfiguredEditProvider
  const genStatus = capabilityStatus('image')
  const aiReady = providerStore.hasConfiguredLLM || hasConfiguredVision.value
  return [
    {
      tab: 'generation',
      icon: Image,
      title: '生成能力',
      desc: '图像 / 视频 / 编辑',
      ready: genReady,
      label: genReady ? genStatus.label : '未配置',
      tagType: genReady ? genStatus.tagType : 'default',
    },
    {
      tab: 'ai',
      icon: Brain,
      title: 'AI 能力',
      desc: '视觉分析 / 提示词优化',
      ready: aiReady,
      label: aiReady ? '已配置' : '未配置',
      tagType: aiReady ? 'success' : 'default',
    },
    {
      tab: 'advanced',
      icon: Settings,
      title: '高级设置',
      desc: '内容管理',
      ready: true,
      label: '',
      tagType: 'default',
    },
  ]
})
const showApiKeyModal = ref(false)
const showVideoModal = ref(false)
const showEditModal = ref(false)
const showLLMModal = ref(false)
const currentPreset = ref<VisionPreset | null>(null)
const currentVideoPreset = ref<VideoPreset | null>(null)
const currentEditPreset = ref<EditPreset | null>(null)
const currentLLMPreset = ref<LLMPreset | null>(null)
const apiKeyInput = ref('')
const endpointInput = ref('')
const videoApiKeyInput = ref('')
const videoEndpointInput = ref('')
const editApiKeyInput = ref('')
const editEndpointInput = ref('')
const llmApiKeyInput = ref('')
const llmEndpointInput = ref('')
const llmModelInput = ref('')
const visionModelInput = ref('')
const videoModelInput = ref('')
const editModelInput = ref('')

/* ── 自定义供应商状态 ── */
const showCustomModal = ref(false)
const testingCustom = ref(false)
const customCapability = ref<'video' | 'edit' | 'vision'>('video')
const customForm = ref({
  name: '',
  apiKey: '',
  endpoint: '',
  model: ''
})

function openCustomProvider(capability: 'video' | 'edit' | 'vision') {
  customCapability.value = capability
  customForm.value = { name: '', apiKey: '', endpoint: '', model: '' }
  showCustomModal.value = true
}

function saveCustomProvider() {
  if (!customForm.value.name || !customForm.value.apiKey) return
  
  const capability = customCapability.value
  const capMap: Record<'video' | 'edit' | 'vision', ProviderCapability> = {
    video: 'video',
    edit: 'edit',
    vision: 'vision'
  }
  
  providerStore.upsertCapabilityProvider({
    name: customForm.value.name,
    type: 'custom' as ProviderType,
    apiKey: customForm.value.apiKey,
    endpoint: customForm.value.endpoint,
    defaultModel: customForm.value.model || undefined,
    capability: capMap[capability]
  })
  
  showCustomModal.value = false
  message.success(`自定义供应商 ${customForm.value.name} 配置成功！`)
}

/* ── 连通性检测状态 ── */
const testingVision = ref(false)
const testingVideo = ref(false)
const testingEdit = ref(false)
const testingLLM = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const testTarget = ref<string | null>(null) // 哪个弹窗的测试结果

async function testConnection(endpoint: string, apiKey: string, providerType: string, target: string) {
  if (!apiKey || !endpoint) {
    message.warning('请先填写 API Key 和 Endpoint')
    return
  }
  testResult.value = null
  testTarget.value = target
  
  if (target === 'vision') testingVision.value = true
  else if (target === 'video') testingVideo.value = true
  else if (target === 'edit') testingEdit.value = true
  else if (target === 'llm') testingLLM.value = true
  
  try {
    const res = await apiService.validateApi({
      api_key: apiKey,
      api_endpoint: endpoint,
      provider_type: providerType
    })
    testResult.value = {
      success: res.valid,
      message: res.valid ? `✅ 连接成功` : `❌ ${res.message}`
    }
    if (res.valid) message.success('连接成功！')
    else message.error(res.message)
  } catch (e: any) {
    const errMsg = e?.response?.data?.error || e?.userMessage || '连接测试失败'
    testResult.value = { success: false, message: `❌ ${errMsg}` }
    message.error(errMsg)
  } finally {
    testingVision.value = false
    testingVideo.value = false
    testingEdit.value = false
    testingLLM.value = false
  }
}

interface VisionPreset {
  type: ProviderType
  name: string
  description: string
  keyPlaceholder: string
  helpUrl?: string
  helpText?: string
  customEndpoint?: boolean
  visionModel: string
  visionEndpoint: string
}

interface VideoPreset {
  type: string
  name: string
  description: string
  keyPlaceholder: string
  endpoint: string
  defaultModel?: string
  helpUrl?: string
  helpText?: string
  recommended?: boolean
}

interface EditPreset {
  type: string
  name: string
  description: string
  keyPlaceholder: string
  endpoint: string
  defaultModel?: string
  helpUrl?: string
  helpText?: string
}

interface LLMPreset {
  type: ProviderType
  name: string
  description: string
  keyPlaceholder: string
  endpoint: string
  models: { label: string; value: string }[]
  defaultModel: string
  helpUrl?: string
  helpText?: string
  tagType: 'success' | 'info' | 'default' | 'warning'
  tagLabel: string
  isFree?: boolean
}

const llmPresets: LLMPreset[] = [
  {
    type: 'custom' as ProviderType,
    name: 'DeepSeek (推荐)',
    description: '性价比极高，中文理解优秀，注册即送 500 万 tokens',
    keyPlaceholder: 'sk-...',
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    models: [
      { label: 'DeepSeek Chat (推荐)', value: 'deepseek-chat' },
      { label: 'DeepSeek Reasoner', value: 'deepseek-reasoner' },
    ],
    defaultModel: 'deepseek-chat',
    helpUrl: 'https://platform.deepseek.com/api_keys',
    helpText: 'DeepSeek 开放平台 - 注册即送免费额度',
    tagType: 'success',
    tagLabel: '推荐',
  },
  {
    type: 'zhipu' as ProviderType,
    name: '智谱 GLM-4-Flash (免费)',
    description: '完全免费模型，适合体验和轻度使用',
    keyPlaceholder: '智谱 API Key',
    endpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    models: [
      { label: 'GLM-4-Flash (免费)', value: 'glm-4-flash' },
      { label: 'GLM-4-Air', value: 'glm-4-air' },
      { label: 'GLM-4-Plus', value: 'glm-4-plus' },
    ],
    defaultModel: 'glm-4-flash',
    helpUrl: 'https://open.bigmodel.cn/',
    helpText: '智谱开放平台 - 注册即可免费使用',
    tagType: 'info',
    tagLabel: '免费',
    isFree: true,
  },
  {
    type: 'aliyun' as ProviderType,
    name: '通义千问',
    description: '阿里云出品，中文能力强，价格低',
    keyPlaceholder: '阿里云 DashScope API Key',
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    models: [
      { label: 'Qwen Turbo', value: 'qwen-turbo' },
      { label: 'Qwen Plus', value: 'qwen-plus' },
      { label: 'Qwen Max', value: 'qwen-max' },
    ],
    defaultModel: 'qwen-turbo',
    helpUrl: 'https://dashscope.console.aliyun.com/',
    helpText: '阿里云 DashScope 控制台',
    tagType: 'default',
    tagLabel: '可选',
  },
  {
    type: 'doubao' as ProviderType,
    name: '豆包大模型',
    description: '字节跳动出品，低价高效',
    keyPlaceholder: '火山引擎 API Key',
    endpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
    models: [
      { label: 'Doubao Pro 32K', value: 'doubao-pro-32k' },
      { label: 'Doubao Lite 32K', value: 'doubao-lite-32k' },
    ],
    defaultModel: 'doubao-pro-32k',
    helpUrl: 'https://console.volcengine.com/ark',
    helpText: '火山引擎控制台',
    tagType: 'default',
    tagLabel: '可选',
  },
]

const videoPresets: VideoPreset[] = [
  {
    type: 'kling',
    name: '可灵AI',
    description: '国内领先的视频生成平台，性价比高，¥0.5-2/条',
    keyPlaceholder: '可灵 API Key',
    endpoint: 'https://api.klingai.com/v1/videos/generations',
    defaultModel: 'kling-v1',
    helpUrl: 'https://platform.klingai.com/',
    helpText: '可灵开放平台 - 注册即送免费额度',
    recommended: true
  },
  {
    type: 'jimeng',
    name: '即梦AI',
    description: '字节跳动出品，中文理解好，积分制',
    keyPlaceholder: '即梦 API Key',
    endpoint: 'https://api.jimeng.ai/v1/videos/generations',
    defaultModel: 'jimeng-2.1',
    helpUrl: 'https://jimeng.jianying.com/',
    helpText: '即梦AI官网'
  },
  {
    type: 'runway',
    name: 'Runway',
    description: '国际领先的视频生成平台，专业级',
    keyPlaceholder: 'Runway API Key',
    endpoint: 'https://api.runwayml.com/v1/generate',
    defaultModel: 'gen3a',
    helpUrl: 'https://runwayml.com/',
    helpText: 'Runway官网'
  }
]

const editPresets: EditPreset[] = [
  {
    type: 'aliyun-wanx',
    name: '阿里云万相编辑',
    description: '支持指令编辑、局部重绘、扩图，¥0.14/张',
    keyPlaceholder: '阿里云 DashScope API Key',
    endpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-edit',
    defaultModel: 'wanx-background-generation-v2',
    helpUrl: 'https://dashscope.console.aliyun.com/',
    helpText: '阿里云 DashScope 控制台'
  }
]

const visionPresets: VisionPreset[] = [
  {
    type: 'zhipu',
    name: '智谱 GLM-4V-Flash',
    description: '免费模型，新用户赠送额度，1元可处理约300张图',
    keyPlaceholder: '智谱 API Key (如: xxx.xxx)',
    helpUrl: 'https://open.bigmodel.cn/',
    helpText: '智谱开放平台 - 注册即送免费额度',
    visionModel: 'glm-4v-flash',
    visionEndpoint: 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
  },
  {
    type: 'doubao',
    name: '豆包视觉理解',
    description: '火山引擎出品，低价高效，约0.003元/千tokens',
    keyPlaceholder: '火山引擎 API Key',
    helpUrl: 'https://console.volcengine.com/ark',
    helpText: '火山引擎控制台 - 开通视觉理解服务',
    visionModel: 'doubao-vision-pro-32k',
    visionEndpoint: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
  },
  {
    type: 'aliyun',
    name: '通义千问 VL',
    description: '阿里云出品，多模态理解能力强',
    keyPlaceholder: '阿里云 DashScope API Key',
    helpUrl: 'https://dashscope.console.aliyun.com/',
    helpText: '阿里云 DashScope 控制台',
    visionModel: 'qwen-vl-plus',
    visionEndpoint: 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
  }
]

function isConfigured(type: ProviderType): boolean {
  const provider = providerStore.providers.find(p => p.type === type)
  return !!provider?.apiKey
}

function isVideoConfigured(type: string): boolean {
  return providerStore.providers.some(p => p.type === type && p.capabilities?.includes('video') && p.apiKey)
}

function isEditConfigured(type: string): boolean {
  return providerStore.providers.some(p => p.type === type && p.capabilities?.includes('edit') && p.apiKey)
}

function showConfigModal(preset: VisionPreset): void {
  currentPreset.value = preset
  const existing = providerStore.providers.find(p => p.type === preset.type)
  apiKeyInput.value = existing?.apiKey || ''
  endpointInput.value = existing?.endpoint || preset.visionEndpoint
  visionModelInput.value = existing?.defaultModel || preset.visionModel
  showApiKeyModal.value = true
}

function showVideoConfigModal(preset: VideoPreset): void {
  currentVideoPreset.value = preset
  const existing = providerStore.providers.find(p => p.type === preset.type && p.capabilities?.includes('video'))
  videoApiKeyInput.value = existing?.apiKey || localStorage.getItem(`video_${preset.type}_apiKey`) || ''
  videoEndpointInput.value = existing?.endpoint || localStorage.getItem(`video_${preset.type}_endpoint`) || preset.endpoint
  videoModelInput.value = existing?.defaultModel || localStorage.getItem(`video_${preset.type}_model`) || preset.defaultModel || ''
  showVideoModal.value = true
}

function showEditConfigModal(preset: EditPreset): void {
  currentEditPreset.value = preset
  const existing = providerStore.providers.find(p => p.type === preset.type && p.capabilities?.includes('edit'))
  editApiKeyInput.value = existing?.apiKey || localStorage.getItem(`edit_${preset.type}_apiKey`) || ''
  editEndpointInput.value = existing?.endpoint || localStorage.getItem(`edit_${preset.type}_endpoint`) || preset.endpoint
  editModelInput.value = existing?.defaultModel || localStorage.getItem(`edit_${preset.type}_model`) || preset.defaultModel || ''
  showEditModal.value = true
}

async function saveVisionConfig(): Promise<void> {
  if (!currentPreset.value || !apiKeyInput.value) return
  
  const existing = providerStore.providers.find(p => p.type === currentPreset.value!.type)
  
  if (existing) {
    providerStore.updateProvider(existing.id, {
      apiKey: apiKeyInput.value,
      endpoint: endpointInput.value || currentPreset.value!.visionEndpoint,
      models: [visionModelInput.value || currentPreset.value!.visionModel],
      defaultModel: visionModelInput.value || currentPreset.value!.visionModel,
      capabilities: [...new Set([...(existing.capabilities || []), 'vision' as const])] as ProviderCapability[]
    })
  } else {
    providerStore.addProvider({
      name: currentPreset.value.name,
      type: currentPreset.value.type,
      apiKey: apiKeyInput.value,
      endpoint: endpointInput.value || currentPreset.value.visionEndpoint,
      models: [visionModelInput.value || currentPreset.value.visionModel],
      defaultModel: visionModelInput.value || currentPreset.value.visionModel,
      capabilities: ['vision']
    })
  }
  
  showApiKeyModal.value = false
}

function saveVideoConfig(): void {
  if (!currentVideoPreset.value || !videoApiKeyInput.value) return
  
  providerStore.upsertCapabilityProvider({
    name: currentVideoPreset.value.name,
    type: currentVideoPreset.value.type as ProviderType,
    apiKey: videoApiKeyInput.value,
    endpoint: videoEndpointInput.value || currentVideoPreset.value.endpoint,
    defaultModel: videoModelInput.value || currentVideoPreset.value.defaultModel || '',
    capability: 'video'
  })
  
  showVideoModal.value = false
  message.success(`${currentVideoPreset.value.name} 视频配置已保存`)
}

function saveEditConfig(): void {
  if (!currentEditPreset.value || !editApiKeyInput.value) return
  
  providerStore.upsertCapabilityProvider({
    name: currentEditPreset.value.name,
    type: currentEditPreset.value.type as ProviderType,
    apiKey: editApiKeyInput.value,
    endpoint: editEndpointInput.value || currentEditPreset.value.endpoint,
    defaultModel: editModelInput.value || currentEditPreset.value.defaultModel || '',
    capability: 'edit'
  })
  
  showEditModal.value = false
  message.success(`${currentEditPreset.value.name} 编辑配置已保存`)
}

// ── LLM 配置 ─────────────────────────────────────────────────────────

function isLLMConfigured(name: string): boolean {
  return providerStore.llmProviders.some(p => p.name === name && p.apiKey)
}

function showLLMConfigModal(preset: LLMPreset): void {
  currentLLMPreset.value = preset
  const existing = providerStore.llmProviders.find(p => p.name === preset.name)
  llmApiKeyInput.value = existing?.apiKey || ''
  llmEndpointInput.value = existing?.llmEndpoint || preset.endpoint
  llmModelInput.value = existing?.llmModel || preset.defaultModel
  showLLMModal.value = true
}

function saveLLMConfig(): void {
  if (!currentLLMPreset.value || !llmApiKeyInput.value) return
  
  const preset = currentLLMPreset.value
  const existing = providerStore.llmProviders.find(p => p.name === preset.name)
  
  if (existing) {
    providerStore.updateLLMProvider(existing.id, {
      apiKey: llmApiKeyInput.value,
      llmEndpoint: llmEndpointInput.value || preset.endpoint,
      endpoint: llmEndpointInput.value || preset.endpoint,
      llmModel: llmModelInput.value || preset.defaultModel,
      defaultModel: llmModelInput.value || preset.defaultModel,
    })
    message.success(`${preset.name} 配置已更新`)
  } else {
    providerStore.addLLMProvider({
      name: preset.name,
      type: preset.type,
      apiKey: llmApiKeyInput.value,
      llmEndpoint: llmEndpointInput.value || preset.endpoint,
      models: [llmModelInput.value || preset.defaultModel],
      llmModel: llmModelInput.value || preset.defaultModel,
      isFree: preset.isFree,
    })
    message.success(`${preset.name} 配置成功！`)
  }
  
  showLLMModal.value = false
}

function removeLLMConfig(name: string): void {
  const existing = providerStore.llmProviders.find(p => p.name === name)
  if (existing) {
    providerStore.removeLLMProvider(existing.id)
    message.info(`已删除 ${name} 配置`)
  }
}
</script>

<style scoped>
.config-modal { height: 100%; }

.quick-start-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 4px;
}

.quick-start-copy {
  font-size: 13px;
  line-height: 1.7;
}

:deep(.quick-start-banner .n-alert) {
  background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%);
  border-color: #bbf7d0;
}

.config-layout {
  display: flex;
  gap: 20px;
  min-height: 480px;
}

.config-sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-right: 1px solid var(--border);
  padding-right: 16px;
}

.sidebar-divider {
  height: 1px;
  background: var(--border);
  margin: 4px 0;
}

.sidebar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
}

.sidebar-item:hover {
  background: var(--bg-subtle);
}

.sidebar-item.active {
  background: var(--brand-50);
  border-color: var(--brand-200);
}

.sidebar-item-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.capability-icon {
  font-size: 20px;
  margin-top: 2px;
}

.capability-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.capability-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.sidebar-item.active .capability-title {
  color: var(--brand-600);
}

.capability-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.sidebar-tag {
  flex-shrink: 0;
}

.config-content-area {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}

.section-block {
  margin-bottom: 4px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.section-icon {
  font-size: 18px;
  color: var(--brand-500);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

:deep(.n-list-item) {
  border-radius: 8px;
  transition: background 0.15s ease;
  padding: 12px 16px !important;
}

:deep(.n-list-item:hover) {
  background: var(--bg-subtle);
}
</style>
