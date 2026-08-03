<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="BRAND_THEME_OVERRIDES">
    <n-dialog-provider>
      <n-message-provider>
        <!-- 加载骨架屏：匹配真实 Tab + 内容区布局 -->
        <div v-if="isInitializing" class="loading-skeleton">
          <div class="sk-header">
            <div class="sk-logo"></div>
            <div class="sk-actions">
              <div class="sk-btn"></div>
              <div class="sk-btn sk-btn-primary"></div>
            </div>
          </div>
          <div class="sk-tabs">
            <div class="sk-tab sk-tab-active"></div>
            <div class="sk-tab"></div>
            <div class="sk-tab"></div>
          </div>
          <div class="sk-body">
            <div class="sk-panel">
              <div class="sk-line sk-line-short"></div>
              <div class="sk-block sk-block-input"></div>
              <div class="sk-btn sk-btn-wide"></div>
            </div>
            <div class="sk-result">
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
                  <span class="logo-badge">BETA</span>
                </div>
                <span
                  v-if="configReady"
                  class="header-status header-status--ready"
                  :title="`生成能力已就绪 (${activeProviderCount} 个供应商)`"
                >
                  <span class="header-status__dot"></span>
                  {{ activeProviderCount }} 个能力已就绪
                </span>
                <span
                  v-else
                  class="header-status header-status--warning"
                  title="尚未配置生成能力"
                >
                  <span class="header-status__dot"></span>
                  未配置
                </span>
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
                <n-tabs v-model:value="mainTab" type="line" class="main-tabs">
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
            <n-drawer-content title="创作资源" closable>
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
                  <KnowledgeBase @insert="handleTermInsert" @goto-video="handleGotoVideoFromKnowledge" />
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
import { useKeyboard } from './composables/useKeyboard'

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
// 面板默认隐藏，让任务入口（图像/视频/编辑）占据主视野
const storedPanelOpen = localStorage.getItem(SK + 'open')
const panelOpen = ref(storedPanelOpen === null ? false : storedPanelOpen === 'true')
const windowWidth = ref(typeof window === 'undefined' ? 1024 : window.innerWidth)
// 桌面端默认 520,平板 420,移动端全屏
const drawerWidth = computed(() => {
  if (windowWidth.value < 640) return windowWidth.value
  if (windowWidth.value < 1024) return 420
  return Math.min(520, windowWidth.value - 80)
})

// 顶部状态指示:聚合"已配置且可用"的能力数量(图像/视频/编辑/LLM)
const activeProviderCount = computed(() => {
  let count = 0
  if (providerStore.hasConfiguredImageProvider) count++
  if (providerStore.hasConfiguredVideoProvider) count++
  if (providerStore.hasConfiguredEditProvider) count++
  if (providerStore.hasConfiguredLLM) count++
  if (providerStore.visionProviderPresets.some(p => providerStore.providers.find(vp => vp.type === p.type)?.apiKey)) count++
  return count
})
const configReady = computed(() => activeProviderCount.value > 0)

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

function closeDrawer() {
  if (panelOpen.value) {
    panelOpen.value = false
    saveState()
  }
}

function openConfig() {
  configStore.showConfigModal = true
}

/* ---- 全局快捷键 ---- */
useKeyboard([
  {
    key: ',',
    ctrl: true,
    handler: () => openConfig(),
    description: '打开配置',
  },
  {
    key: 'Escape',
    handler: (e) => {
      // 优先关闭 Drawer（如果打开），再让 n-modal/drawer 处理其他 Esc
      if (panelOpen.value) {
        closeDrawer()
        e.preventDefault()
      }
    },
    description: '关闭抽屉/弹窗',
  },
])

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
    successColor: '#10b981',
    successColorHover: '#059669',
    successColorPressed: '#047857',
    successColorSuppl: '#34d399',
    warningColor: '#f59e0b',
    warningColorHover: '#d97706',
    warningColorPressed: '#b45309',
    warningColorSuppl: '#fbbf24',
    errorColor: '#ef4444',
    errorColorHover: '#dc2626',
    errorColorPressed: '#b91c1c',
    errorColorSuppl: '#f87171',
    infoColor: '#3b82f6',
    infoColorHover: '#2563eb',
    infoColorPressed: '#1d4ed8',
    infoColorSuppl: '#60a5fa',
  },
  Button: { borderRadiusMedium: '10px', borderRadiusSmall: '6px', fontWeightMedium: '600' },
  Card: { borderRadius: '14px' },
  Modal: { borderRadius: '16px' },
  Drawer: { borderRadius: '16px' },
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
function handleGotoVideoFromKnowledge(movement?: any) {
  mainTab.value = 'video'
  closeDrawer()
  if (movement && movement.id) {
    videoStore.applyMovementWithRecommendedSpeed(movement)
  }
}

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
  background: var(--header-bg);
}

.sk-logo {
  width: 140px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, rgba(255,255,255,0.08) 25%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0.08) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}

.sk-actions { display: flex; gap: var(--space-3); }
.sk-btn {
  width: 80px; height: 28px; border-radius: var(--radius-sm);
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
  width: 100%; height: 40px; margin-top: var(--space-4);
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
/* ── 骨架屏 Tabs ── */
.sk-tabs {
  display: flex; gap: var(--space-2); padding: 12px 32px 0;
  border-bottom: 1px solid var(--border);
}
.sk-tab {
  width: 100px; height: 32px; border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-tab-active {
  background: linear-gradient(90deg, var(--brand-100) 25%, var(--brand-50) 50%, var(--brand-100) 75%);
  background-size: 400px 100%;
}
.sk-body {
  display: flex; gap: var(--panel-gap); padding: 20px 32px; flex: 1; min-height: 0;
}
.sk-panel { flex: 0 0 380px; display: flex; flex-direction: column; gap: var(--space-3); }
.sk-line {
  height: 14px; border-radius: var(--radius-xs);
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-line-short { width: 60%; }
.sk-block {
  flex: 1; border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--gray-200) 25%, var(--gray-100) 50%, var(--gray-200) 75%);
  background-size: 400px 100%;
  animation: sk-shimmer 1.5s ease-in-out infinite;
}
.sk-block-input { flex: 0 0 120px; }
.sk-block-tall { flex: 1; min-height: 300px; }
.sk-result { flex: 1; border-radius: var(--radius-md); display: flex; flex-direction: column; }
.sk-loading-text {
  position: fixed; bottom: var(--space-6); left: 50%; transform: translateX(-50%);
  font-size: var(--font-size-sm); color: var(--text-secondary);
}

/* ═══════════════════════════════════════════════
   Layout — Clean, Seamless
   ═══════════════════════════════════════════════ */
.app-layout {
  height: 100vh;
  background: var(--bg-page);
}

/* ── Header — Dark immersive bar ── */
.app-header {
  height: var(--header-height);
  padding: 0 var(--content-padding);
  display: flex;
  align-items: center;
  background: var(--header-bg);
  background-image:
    radial-gradient(circle at 0% 50%, rgba(79, 125, 243, 0.18) 0%, transparent 40%),
    radial-gradient(circle at 100% 50%, rgba(139, 92, 246, 0.15) 0%, transparent 40%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  position: relative;
  z-index: var(--z-header);
  color: var(--header-fg);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

.header-left { display: flex; align-items: center; gap: var(--space-3); }

.app-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  user-select: none;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, var(--brand-500) 0%, var(--accent-500) 100%);
  border-radius: var(--radius-sm);
  font-size: 16px;
  color: #fff;
  flex-shrink: 0;
  box-shadow: var(--shadow-glow);
  transition: transform var(--duration-base) var(--ease-out);
}
.logo-icon :deep(.n-icon) { color: #fff; }
.app-logo:hover .logo-icon {
  transform: rotate(-8deg) scale(1.05);
}

.logo-text {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: -0.3px;
}

.logo-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  color: var(--brand-300);
  background: rgba(79, 125, 243, 0.12);
  border: 1px solid rgba(79, 125, 243, 0.25);
  border-radius: var(--radius-full);
  letter-spacing: 0.5px;
  margin-left: var(--space-1);
}

.header-actions { display: flex; align-items: center; gap: var(--space-2); }

.header-btn {
  height: 32px !important;
  padding: 0 12px !important;
  font-size: var(--font-size-sm) !important;
  font-weight: 500 !important;
  color: rgba(255, 255, 255, 0.7) !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  border-radius: var(--radius-md) !important;
}
.header-btn:hover {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  transform: translateY(0) !important;
}

.header-btn--primary {
  background: linear-gradient(135deg, var(--brand-500) 0%, var(--brand-600) 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(79, 125, 243, 0.25);
}
.header-btn--primary:hover {
  background: linear-gradient(135deg, var(--brand-400) 0%, var(--brand-500) 100%) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
  box-shadow: 0 4px 12px rgba(79, 125, 243, 0.35);
  transform: translateY(-1px) !important;
}

.header-status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 4px 10px;
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  background: var(--bg-subtle);
  border-radius: var(--radius-full);
  margin-right: var(--space-2);
}
.header-status__dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--gray-400);
}
.header-status--ready { color: var(--success-600); background: var(--success-50); }
.header-status--ready .header-status__dot {
  background: var(--success-500);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}
.header-status--warning { color: var(--warning-600); background: var(--warning-50); }
.header-status--warning .header-status__dot { background: var(--warning-500); }
.header-status--error { color: var(--error-600); background: var(--error-50); }
.header-status--error .header-status__dot { background: var(--error-500); }

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

/* ── Tabs — Modern line style ── */
.main-tabs {
  height: 100%;
}

.main-tabs :deep(.n-tabs-nav) {
  padding: 0 0 0 var(--space-2);
  background: transparent;
}

.main-tabs :deep(.n-tabs-tab) {
  font-size: var(--font-size-md);
  font-weight: 500;
  padding: 10px 18px;
  color: var(--text-secondary);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: color var(--duration-fast) var(--ease-out),
              background var(--duration-fast) var(--ease-out);
}

.main-tabs :deep(.n-tabs-tab:hover) {
  color: var(--text-primary);
  background: var(--bg-subtle);
}

.main-tabs :deep(.n-tabs-tab--active) {
  font-weight: 600;
  color: var(--brand-600);
}
[theme="dark"] .main-tabs :deep(.n-tabs-tab--active),
:global(.dark) .main-tabs :deep(.n-tabs-tab--active) {
  color: var(--brand-300);
}

.main-tabs :deep(.n-tabs-tab--active .n-icon) {
  color: var(--brand-500);
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
  gap: var(--space-2);
}

.drawer-tabs { margin-bottom: var(--space-4); }
.drawer-body { height: 100%; overflow-y: auto; }

/* ── Mobile responsive header ── */
@media (max-width: 768px) {
  .header-content { padding: 0; }
  .logo-text { display: none; }
  .logo-badge { display: none; }
  .header-btn :deep(span) { display: none; }
  .header-btn { padding: 0 8px !important; }
  .header-status { display: none; }
}
</style>
