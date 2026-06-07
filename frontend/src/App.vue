<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="BRAND_THEME_OVERRIDES">
    <n-dialog-provider>
      <n-message-provider>
        <!-- 加载骨架屏 -->
        <div v-if="isInitializing" class="loading-skeleton">
          <div class="sk-header">
            <div class="sk-logo"></div>
            <div class="sk-actions">
              <div class="sk-btn"></div>
              <div class="sk-btn sk-btn-primary"></div>
            </div>
          </div>
          <div class="sk-body">
            <div class="sk-sider">
              <div class="sk-line sk-line-short"></div>
              <div class="sk-block"></div>
              <div class="sk-block sk-block-sm"></div>
              <div class="sk-btn sk-btn-wide"></div>
            </div>
            <div class="sk-content">
              <div class="sk-block sk-block-tall"></div>
            </div>
          </div>
          <div class="sk-loading-text">正在加载工作台...</div>
        </div>

        <n-layout v-else class="app-layout">
          <n-layout-header class="app-header">
            <div class="header-content">
              <div class="header-left">
                <div class="app-logo">
                  <span class="logo-icon"><n-icon><Sparkles /></n-icon></span>
                  <span class="logo-text">AI 绘图工作台</span>
                </div>
              </div>
              <div class="header-actions">
                <n-button class="header-btn" size="small" quaternary @click="togglePanel">
                  <template #icon>
                    <n-icon :component="panelOpen ? CloseOutline : GridOutline" />
                  </template>
                  {{ panelOpen ? '收起面板' : '展开面板' }}
                </n-button>
                <n-button class="header-btn header-btn--primary" size="small" @click="configStore.showConfigModal = true">
                  <template #icon><n-icon :component="SettingsOutline" /></template>
                  配置能力
                </n-button>
              </div>
            </div>
          </n-layout-header>
          <n-layout class="app-body">
            <n-layout-content class="app-content">
              <div class="content-wrapper">
                <n-tabs v-model:value="mainTab" type="line" animated class="main-tabs">
                  <n-tab-pane name="image">
                    <template #tab>
                      <div class="tab-label"><n-icon><ImageOutline /></n-icon>图像生成</div>
                    </template>
                    <GeneratePanel ref="generatePanelRef" @edit-image="handleEditImage" @generate-video="handleGenerateVideo" @navigate-to-video="handleQuickNavToVideo" @navigate-to-edit="handleQuickNavToEdit" />
                  </n-tab-pane>
                  <n-tab-pane name="video">
                    <template #tab>
                      <div class="tab-label"><n-icon><FilmOutline /></n-icon>视频生成</div>
                    </template>
                    <VideoPanel />
                  </n-tab-pane>
                  <n-tab-pane name="edit">
                    <template #tab>
                      <div class="tab-label"><n-icon><ColorWandOutline /></n-icon>图片编辑</div>
                    </template>
                    <ImageEditor />
                  </n-tab-pane>
                </n-tabs>
              </div>
            </n-layout-content>
          </n-layout>

          <n-drawer v-model:show="panelOpen" :width="drawerWidth" placement="right" :trap-focus="false" :block-scroll="false">
            <n-drawer-content title="资源与工具" closable>
              <n-tabs v-model:value="rightTab" type="line" size="small" class="drawer-tabs">
                <n-tab-pane name="templates">
                  <template #tab><div class="tab-label"><n-icon><LibraryOutline /></n-icon>模板</div></template>
                </n-tab-pane>
                <n-tab-pane name="knowledge">
                  <template #tab><div class="tab-label"><n-icon><BookOutline /></n-icon>知识</div></template>
                </n-tab-pane>
                <n-tab-pane name="analyzer">
                  <template #tab><div class="tab-label"><n-icon><ScanOutline /></n-icon>分析</div></template>
                </n-tab-pane>
                <n-tab-pane name="history">
                  <template #tab><div class="tab-label"><n-icon><ImagesOutline /></n-icon>作品</div></template>
                </n-tab-pane>
                <n-tab-pane v-if="adminModeEnabled" name="ingest">
                  <template #tab><div class="tab-label"><n-icon><CloudDownloadOutline /></n-icon>入库</div></template>
                </n-tab-pane>
              </n-tabs>
              <div class="drawer-body">
                <div v-show="rightTab === 'templates'">
                  <TemplateCenter @select="handleTemplateSelect" />
                </div>
                <div v-show="rightTab === 'knowledge'">
                  <KnowledgeBase @insert="handleTermInsert" />
                </div>
                <div v-show="rightTab === 'analyzer'">
                  <ImageAnalyzer />
                </div>
                <div v-show="rightTab === 'history'">
                  <GalleryPanel @convert-to-video="handleGenerateVideo" @edit-image="handleEditImageFromGallery" />
                </div>
                <div v-if="adminModeEnabled" v-show="rightTab === 'ingest'">
                  <ContentIngest />
                </div>
              </div>
            </n-drawer-content>
          </n-drawer>
        </n-layout>

        <ConfigModal />
      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, defineAsyncComponent, onMounted, onUnmounted } from 'vue'
import { NConfigProvider, NDialogProvider, NMessageProvider, NLayout, NLayoutHeader, NLayoutContent, NButton, NIcon, NTabs, NTabPane, NDrawer, NDrawerContent } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useConfigStore, useHistoryStore, useGeneratorStore, useProviderStore, useVideoStore, useEditorStore, useDataStore } from './stores'
import {
  SettingsOutline, GridOutline, CloseOutline,
  ImageOutline, FilmOutline, ColorWandOutline,
  LibraryOutline, BookOutline, ScanOutline, ImagesOutline, CloudDownloadOutline
} from '@vicons/ionicons5'
import { Sparkles } from 'lucide-vue-next'
import GeneratePanel from './components/GeneratePanel.vue'
import { initDatabase } from './db'

const KnowledgeBase = defineAsyncComponent(() => import('./components/KnowledgeBase.vue'))
const TemplateCenter = defineAsyncComponent(() => import('./components/TemplateCenter.vue'))
const VideoPanel = defineAsyncComponent(() => import('./components/VideoPanel.vue'))
const ImageEditor = defineAsyncComponent(() => import('./components/ImageEditor.vue'))
const GalleryPanel = defineAsyncComponent(() => import('./components/GalleryPanel.vue'))
const ImageAnalyzer = defineAsyncComponent(() => import('./components/ImageAnalyzer.vue'))
const ConfigModal = defineAsyncComponent(() => import('./components/ConfigModal.vue'))
const ContentIngest = defineAsyncComponent(() => import('./components/admin/ContentIngest.vue'))

const configStore = useConfigStore()
const historyStore = useHistoryStore()
const generatorStore = useGeneratorStore()
const providerStore = useProviderStore()
const videoStore = useVideoStore()
const editorStore = useEditorStore()
const dataStore = useDataStore()

const isInitializing = ref(true)
const mainTab = ref('image')
const rightTab = ref('templates')

const SK = 'ai_studio_panel_'
const adminModeEnabled = ref(localStorage.getItem('ai_studio_admin_mode') === 'true')
// 首次访问默认展开右侧面板（让模板/知识/作品/分析等核心功能可见）
const storedPanelOpen = localStorage.getItem(SK + 'open')
const panelOpen = ref(storedPanelOpen === null ? true : storedPanelOpen === 'true')
const windowWidth = ref(typeof window === 'undefined' ? 520 : window.innerWidth)
const drawerWidth = computed(() => Math.min(520, windowWidth.value))

function updateWindowWidth() {
  windowWidth.value = window.innerWidth
}

function saveState() {
  localStorage.setItem(SK + 'open', String(panelOpen.value))
}

function togglePanel() {
  panelOpen.value = !panelOpen.value
  saveState()
}

const BRAND_THEME_OVERRIDES: GlobalThemeOverrides = {
  common: {
    primaryColor: '#4f7df3',
    primaryColorHover: '#6b8ff5',
    primaryColorPressed: '#3d6ce0',
    primaryColorSuppl: '#8b5cf6',
    borderRadius: '10px',
    borderRadiusSmall: '6px',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: '14px',
    fontSizeSmall: '13px',
  },
  Button: { borderRadiusMedium: '10px', borderRadiusSmall: '6px', fontWeightMedium: '600' },
  Card: { borderRadius: '14px' },
  Modal: { borderRadius: '16px' },
  Input: { borderRadius: '10px', border: '1px solid #e2e8f0' },
  Select: { menuBorderRadius: '10px' },
  Tabs: { tabBorderRadius: '8px' },
  Tag: { borderRadius: '6px' },
}

const naiveTheme = computed(() => null)



/* ---- 事件处理 ---- */
function handleTermInsert(text: string) {
  const currentPrompt = mainTab.value === 'video' ? videoStore.prompt : generatorStore.prompt
  const targetStore = mainTab.value === 'video' ? videoStore : generatorStore
  if (currentPrompt && !currentPrompt.endsWith('，') && !currentPrompt.endsWith(',')) {
    targetStore.prompt = currentPrompt + '，' + text
  } else {
    targetStore.prompt = currentPrompt + text
  }
}
function handleTemplateSelect(prompt: string) { generatorStore.prompt = prompt }
function handleEditImage(imageUrl: string) { mainTab.value = 'edit'; editorStore.setSourceImage(imageUrl) }
function handleEditImageFromGallery(imageUrl: string) { mainTab.value = 'edit'; editorStore.setSourceImage(imageUrl) }
function handleGenerateVideo(imageUrl: string, prompt: string) { mainTab.value = 'video'; videoStore.sourceImage = imageUrl; videoStore.prompt = prompt }
function handleQuickNavToVideo(prompt: string) { mainTab.value = 'video'; videoStore.prompt = prompt }
function handleQuickNavToEdit(instruction: string) { mainTab.value = 'edit'; editorStore.setInstruction(instruction) }

onMounted(async () => {
  window.addEventListener('resize', updateWindowWidth)
  providerStore.init()
  try {
    await initDatabase()
    await Promise.all([configStore.loadServerConfig(), historyStore.load(), dataStore.loadAll()])
  } catch (error) { console.error('App initialization error:', error) }
  // 确保骨架屏至少显示 600ms，避免闪烁
  await new Promise(r => setTimeout(r, 600))
  isInitializing.value = false
})

onUnmounted(() => {
  window.removeEventListener('resize', updateWindowWidth)
})


</script>

<style scoped>
/* ── Loading Skeleton ── */
@keyframes sk-shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

.loading-skeleton {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
}

.sk-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1e1b4b 100%);
}

.sk-logo {
  width: 140px;
  height: 28px;
  border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.08) 25%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0.08) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}

.sk-actions { display: flex; gap: 10px; }
.sk-btn {
  width: 80px; height: 28px; border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.06) 25%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.06) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-btn-primary {
  width: 100px;
  background: linear-gradient(90deg, rgba(79,125,243,0.15) 25%, rgba(79,125,243,0.25) 50%, rgba(79,125,243,0.15) 75%);
  background-size: 400px 100%;
}
.sk-btn-wide {
  width: 100%; height: 40px; margin-top: 16px;
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-body {
  display: flex; gap: var(--panel-gap); padding: 24px 32px; flex: 1; min-height: 0;
}
.sk-sider { flex: 0 0 380px; display: flex; flex-direction: column; gap: 12px; }
.sk-line {
  height: 14px; border-radius: 4px;
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-line-short { width: 60%; }
.sk-block {
  flex: 1; border-radius: 10px;
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-block-sm { flex: 0.5; }
.sk-block-tall { flex: 1; min-height: 300px; }
.sk-content { flex: 1; border-radius: 10px; display: flex; flex-direction: column; }
.sk-loading-text {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  font-size: 13px; color: var(--text-secondary);
}

/* ═══════════════════════════════════════════════
   Layout — Clean, Seamless
   ═══════════════════════════════════════════════ */
.app-layout {
  height: 100vh;
  background: var(--bg-page);
}

/* ── Header — Clean dark bar ── */
.app-header {
  height: var(--header-height);
  padding: 0 24px;
  display: flex;
  align-items: center;
  background: #111827;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  position: relative;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-left { display: flex; align-items: center; gap: 10px; }

.app-logo { display: flex; align-items: center; gap: 8px; }

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: var(--brand-500);
  border-radius: 6px;
  font-size: 14px;
  color: #fff;
  flex-shrink: 0;
}
.logo-icon :deep(.n-icon) {
  color: #fff;
}

.logo-text {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255,255,255,0.85);
  letter-spacing: -0.2px;
}

.header-actions { display: flex; align-items: center; gap: 6px; }

.header-btn {
  height: 30px !important;
  font-size: 12px !important;
  color: rgba(255,255,255,0.55) !important;
  border-color: rgba(255,255,255,0.08) !important;
}
.header-btn:hover {
  color: #fff !important;
  background: rgba(255,255,255,0.08) !important;
}
.header-btn--primary {
  height: 30px !important;
  font-size: 12px !important;
  background: rgba(79,125,243,0.12) !important;
  border: 1px solid rgba(79,125,243,0.25) !important;
  color: #93bbfd !important;
}
.header-btn--primary:hover {
  background: rgba(79,125,243,0.2) !important;
  border-color: rgba(79,125,243,0.4) !important;
}

/* ── Body / Content — seamless ── */
.app-body { height: calc(100vh - var(--header-height)); }

.app-content {
  background: transparent;
  height: 100%;
}

.content-wrapper {
  padding: 0 var(--content-padding);
  height: 100%;
  box-sizing: border-box;
}

@media (min-width: 1600px) {
  .content-wrapper { padding: 0 40px; }
}

/* ── Tabs — App-style navigation ── */
.main-tabs {
  height: 100%;
}

.main-tabs :deep(.n-tabs-nav) {
  padding: 0;
  border-bottom: 1px solid var(--border-light);
}

.main-tabs :deep(.n-tabs-tab) {
  font-size: 13px;
  font-weight: 500;
  padding: 10px 16px;
  transition: color var(--duration-fast) var(--ease-out), opacity var(--duration-fast) var(--ease-out);
  opacity: 0.55;
}

.main-tabs :deep(.n-tabs-tab:hover) {
  opacity: 0.8;
  background: transparent;
}

.main-tabs :deep(.n-tabs-tab--active) {
  opacity: 1;
  font-weight: 600;
}

.main-tabs :deep(.n-tabs-tab--active .n-icon) {
  color: var(--brand-500);
}

.main-tabs :deep(.n-tabs-bar) {
  height: 2px;
  background: var(--brand-500);
}

.main-tabs :deep(.n-tabs-pane-wrapper) {
  height: calc(100% - 45px);
  padding: 20px 0;
  overflow: auto;
}

:deep(.n-tab-pane) {
  height: 100%;
}

/* ── Tab 切换淡入动画 ── */
:deep(.n-tabs-pane-wrapper) {
  transition: opacity var(--duration-base) var(--ease-out);
}

:deep(.n-tabs-pane-wrapper:has(.n-tab-pane-transition-enter-active)) {
  opacity: 0;
}

:deep(.n-tabs-pane-wrapper:has(.n-tab-pane-transition-enter-to)) {
  opacity: 1;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.drawer-tabs { margin-bottom: 16px; }
.drawer-body { height: 100%; overflow-y: auto; }
</style>
