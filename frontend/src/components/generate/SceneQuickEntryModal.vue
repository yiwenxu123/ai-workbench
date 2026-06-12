<template>
  <div>
    <div class="quick-entry-bar" @click="showQuickModal = true">
      <n-icon :component="Zap" size="14" class="quick-entry-icon" />
      <span class="quick-entry-text">场景创作</span>
      <span class="quick-entry-tags">电商主图 · 社媒海报 · PPT配图 · 头像 · 动图 · 改图</span>
      <n-icon :component="ChevronDown" size="14" class="quick-entry-arrow" />
    </div>

    <n-modal v-model:show="showQuickModal" preset="card" title="选择创作场景" style="width: 580px">
      <div class="qc-grid">
        <button
          v-for="task in QUICK_TASKS"
          :key="task.id"
          type="button"
          class="qc-card"
          :class="{ selected: selectedQuickTask?.id === task.id }"
          @click="selectQuickTask(task)"
        >
          <n-icon :component="task.icon" size="24" class="qc-card-icon" />
          <div class="qc-card-text">
            <span class="qc-card-title">{{ task.title }}</span>
            <span class="qc-card-desc">{{ task.description }}</span>
          </div>
        </button>
      </div>

      <div v-if="selectedQuickTask" class="qc-form mt-3">
        <div class="qc-form-field">
          <div class="qc-form-label">{{ selectedQuickTask.question }}</div>
          <n-input
            v-model:value="quickTaskInput"
            type="textarea"
            :rows="2"
            :placeholder="selectedQuickTask.placeholder"
            size="small"
          />
        </div>

        <div v-if="selectedQuickTask.type === 'image'" class="qc-ratio-row mt-2">
          <n-radio-group v-model:value="quickTaskRatio" size="small">
            <n-radio-button value="1:1">1:1</n-radio-button>
            <n-radio-button value="3:4">3:4</n-radio-button>
            <n-radio-button value="4:3">4:3</n-radio-button>
            <n-radio-button value="16:9">16:9</n-radio-button>
            <n-radio-button value="9:16">9:16</n-radio-button>
          </n-radio-group>
        </div>

        <div class="qc-actions mt-2">
          <div class="qc-ai-toggle">
            <n-icon :component="Sparkles" size="14" />
            <span class="qc-ai-label">AI 智能调优</span>
            <n-switch v-model:value="useQuickAI" size="small" @update:value="onQuickAIChange" />
          </div>
        </div>

        <div v-if="useQuickAI && quickAIResult && !quickAIWorking" class="qc-ai-result mt-2">
          <n-alert type="success" :show-icon="false" size="small">
            <div class="qc-ai-result-text">
              {{ quickAIResult.optimizedPromptCN || quickAIResult.explanation || '已优化' }}
            </div>
          </n-alert>
        </div>

        <div v-if="quickTaskInput.trim()" class="qc-explanation mt-2">
          <div class="qc-explanation-label">
            <n-icon :component="Sparkles" size="12" />
            <span>为什么这样写</span>
          </div>
          <div v-if="useQuickAI && quickAIResult?.optimizedPrompt" class="qc-explanation-text">
            {{ quickAIResult.explanation || promptExplanation }}
          </div>
          <div v-else class="qc-explanation-text">{{ promptExplanation }}</div>
          <div class="qc-explanation-prompt">
            <span class="qc-ep-label">完整提示词：</span>
            <span class="qc-ep-text">{{ quickAIResult?.optimizedPrompt || generatedQuickPrompt }}</span>
          </div>
        </div>

        <div v-if="!useQuickAI && quickTaskInput.trim() && !promptExplanation" class="qc-preview mt-2">
          <div class="qc-preview-label">模板预览：</div>
          <div class="qc-preview-text">{{ generatedQuickPrompt }}</div>
        </div>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showQuickModal = false">取消</n-button>
          <n-button
            v-if="selectedQuickTask"
            type="primary"
            :disabled="!quickTaskInput.trim() || generatorStore.status === 'generating'"
            :loading="quickAIWorking || generatorStore.status === 'generating'"
            @click="applyQuickTask"
          >
            {{ selectedQuickTask.type === 'video' ? '生成视频' : selectedQuickTask.type === 'edit' ? '前往图片编辑' : '生成图片' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import {
  NModal, NInput, NButton, NSpace, NIcon, NAlert, NRadioGroup, NRadioButton, NSwitch,
} from 'naive-ui'
import { Sparkles, Zap, ChevronDown } from 'lucide-vue-next'
import { useGeneratorStore } from '../../stores'
import { QUICK_TASKS, useSceneQuickEntry } from '../../composables/useSceneQuickEntry'

const emit = defineEmits<{
  navigateToVideo: [prompt: string, negativePrompt: string]
  navigateToEdit: [instruction: string]
}>()

const generatorStore = useGeneratorStore()

const {
  showQuickModal,
  selectedQuickTask,
  quickTaskInput,
  quickTaskRatio,
  useQuickAI,
  quickAIWorking,
  quickAIResult,
  generatedQuickPrompt,
  promptExplanation,
  onMainPromptInput,
  selectQuickTask,
  onQuickAIChange,
  applyQuickTask,
} = useSceneQuickEntry({
  onNavigateToVideo: (prompt, negative) => emit('navigateToVideo', prompt, negative),
  onNavigateToEdit: (instruction) => emit('navigateToEdit', instruction),
})

defineExpose({ onMainPromptInput })
</script>

<style scoped>
.quick-entry-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}
.quick-entry-bar:hover {
  background: var(--brand-50);
  border-color: var(--brand-200);
}
.quick-entry-icon { color: var(--brand-500); flex-shrink: 0; }
.quick-entry-text { font-size: 13px; font-weight: 600; color: var(--text-primary); white-space: nowrap; }
.quick-entry-tags { font-size: 11px; color: var(--text-tertiary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.quick-entry-arrow { margin-left: auto; color: var(--text-tertiary); flex-shrink: 0; }
.qc-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.qc-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 12px 10px; border: 1px solid var(--border-light, #eef0f4);
  border-radius: var(--radius-sm, 8px); background: transparent; cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out); font-family: inherit; text-align: center;
}
.qc-card:hover { border-color: var(--brand-300, #a0bcf8); background: var(--brand-50, #f0f4ff); }
.qc-card.selected {
  border-color: var(--brand-500, #4f7df3); background: var(--brand-50, #f0f4ff);
  box-shadow: 0 0 0 1px var(--brand-500, #4f7df3);
}
.qc-card-icon { color: var(--text-secondary, #64748b); }
.qc-card:hover .qc-card-icon, .qc-card.selected .qc-card-icon { color: var(--brand-500, #4f7df3); }
.qc-card-text { display: flex; flex-direction: column; gap: 1px; }
.qc-card-title { font-size: 12px; font-weight: 600; color: var(--text-primary, #1a1a2e); }
.qc-card-desc { font-size: 11px; color: var(--text-tertiary, #9ca3af); }
.qc-form { display: flex; flex-direction: column; gap: 8px; }
.qc-form-label { font-size: 12px; font-weight: 500; color: var(--text-secondary, #64748b); }
.qc-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.qc-ai-toggle { display: flex; align-items: center; gap: 4px; font-size: 12px; color: var(--text-secondary, #64748b); }
.qc-ai-toggle :deep(.n-icon) { color: #f59e0b; }
.qc-ai-result-text { font-size: 12px; line-height: 1.5; color: var(--text-secondary, #64748b); }
.qc-preview { padding: 8px 10px; background: var(--gray-50, #f8f9fc); border-radius: var(--radius-sm, 6px); border: 1px solid var(--border-light, #eef0f4); }
.qc-preview-label { font-size: 11px; font-weight: 500; color: var(--text-tertiary, #9ca3af); margin-bottom: 3px; }
.qc-preview-text { font-size: 12px; line-height: 1.5; color: var(--text-secondary, #64748b); word-break: break-all; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.qc-explanation {
  padding: 10px 12px;
  background: linear-gradient(135deg, #f0f4ff 0%, #fafbff 100%);
  border-radius: var(--radius-sm, 8px);
  border: 1px solid #dbe4f5;
}
.qc-explanation-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--brand-600, #4f7df3);
  margin-bottom: 5px;
}
.qc-explanation-text {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary, #475569);
  word-break: break-word;
}
.qc-explanation-prompt {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed #dbe4f5;
}
.qc-ep-label {
  font-size: 11px;
  color: var(--text-tertiary, #94a3b8);
}
.qc-ep-text {
  font-size: 11px;
  color: var(--text-tertiary, #94a3b8);
  word-break: break-all;
}
</style>
