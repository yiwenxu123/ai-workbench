<template>
  <n-modal v-model:show="show" preset="card" style="width: 500px">
    <template #header>
      <n-space align="center" :size="4">
        <n-icon :component="StarOutline" />
        <span>收录为案例</span>
      </n-space>
    </template>
    <n-form label-placement="top">
      <n-form-item label="案例标题">
        <n-input v-model:value="caseTitle" placeholder="例如：白色保温杯电商主图" />
      </n-form-item>
      <n-form-item label="标签（用逗号分隔）">
        <n-input v-model:value="caseTags" placeholder="例如：电商, 产品, 保温杯, 白色" />
      </n-form-item>
      <n-form-item label="使用技巧">
        <n-input v-model:value="caseTips" type="textarea" :rows="3" placeholder="分享你的使用心得和技巧..." />
      </n-form-item>
      <n-form-item label="将收录的提示词">
        <n-input v-model:value="casePrompt" type="textarea" :rows="3" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="show = false">取消</n-button>
        <n-button type="primary" :loading="saving" @click="handleSave">
          <template #icon><n-icon :component="CheckmarkCircle" /></template>
          确认收录
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import axios from 'axios'
import { NModal, NForm, NFormItem, NInput, NButton, NSpace, NIcon, useMessage } from 'naive-ui'
import { StarOutline, CheckmarkCircle } from '@vicons/ionicons5'
import { config } from '../../config'
import { useGeneratorStore } from '../../stores'

const show = defineModel<boolean>('show', { default: false })

const generatorStore = useGeneratorStore()
const message = useMessage()

const saving = ref(false)
const caseTitle = ref('')
const caseTags = ref('')
const caseTips = ref('')
const casePrompt = ref('')

watch(show, (val) => {
  if (val) {
    caseTitle.value = ''
    caseTags.value = ''
    caseTips.value = ''
    casePrompt.value = generatorStore.prompt
  }
})

async function handleSave() {
  if (!caseTitle.value.trim() || !casePrompt.value.trim()) {
    message.warning('请填写标题和提示词')
    return
  }

  saving.value = true
  try {
    const res = await axios.post(`${config.apiBaseUrl}/api/cases`, {
      title: caseTitle.value.trim(),
      prompt: casePrompt.value.trim(),
      negativePrompt: generatorStore.negativePrompt || '',
      model: generatorStore.model,
      size: generatorStore.size,
      tips: caseTips.value.split('\n').filter(Boolean).map((s) => s.trim()),
      tags: caseTags.value.split(',').filter(Boolean).map((s) => s.trim()),
    })
    if (res.data.success) {
      message.success('案例已收录到知识库！')
      show.value = false
    } else {
      message.error(res.data.error || '保存失败')
    }
  } catch {
    message.error('收录失败，请检查后端服务')
  } finally {
    saving.value = false
  }
}
</script>
