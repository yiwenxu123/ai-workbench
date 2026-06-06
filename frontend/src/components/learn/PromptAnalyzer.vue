<template>
  <div class="prompt-analyzer" v-if="prompt.trim()">
    <div v-if="loading" class="loading-hint">
      <n-spin size="small" />
      <n-text depth="3" style="font-size: 12px; margin-left: 6px">分析中...</n-text>
    </div>

    <template v-else>
      <div v-if="missingElements.length > 0" class="missing-section">
        <div class="section-title">还缺少什么</div>
        <div class="element-tags">
          <n-tag v-for="el in missingElements" :key="el" size="small" type="warning" style="margin: 2px">
            {{ el }}
          </n-tag>
          <n-text depth="3" style="font-size: 12px; margin-left: 4px">
            — 添加这些要素能让模型更准确理解你的意图
          </n-text>
        </div>
      </div>

      <div v-if="presentElements.length > 0" class="present-section">
        <div class="section-title">已包含</div>
        <div class="element-tags">
          <n-tag v-for="el in presentElements" :key="el" size="small" type="success" style="margin: 2px">
            {{ el }}
          </n-tag>
        </div>
      </div>

      <div v-if="suggestedTerms.length > 0" class="suggest-section">
        <div class="section-title">试试加入这些术语</div>
        <div class="suggest-tags">
          <n-tag
            v-for="t in suggestedTerms"
            :key="t.id"
            size="small"
            bordered
            style="margin: 2px; cursor: pointer"
            @click="emit('insert', t.title)"
          >
            + {{ t.title }}
          </n-tag>
        </div>
      </div>

      <div v-if="prompt.length < 20 && !loading" class="tip-text">
        <n-text depth="3" style="font-size: 12px">
          提示词太短了，建议补充主体、场景、风格、光线等描述
        </n-text>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NTag, NText, NSpin } from 'naive-ui'
import { searchKnowledge } from '../../api/knowledge'
import type { KnowledgeEntry } from '../../types/api'

const props = defineProps<{
  prompt: string
}>()

const emit = defineEmits<{
  (e: 'insert', text: string): void
}>()

const loading = ref(false)
const suggestedTerms = ref<KnowledgeEntry[]>([])
const presentElements = ref<string[]>([])
const missingElements = ref<string[]>([])

const CATEGORY_KEYWORDS: { [key: string]: string[] } = {
  subject: ['女孩', '男孩', '猫', '狗', '人', '男人', '女人', '少女', '少年', '美女', '帅哥',
    '产品', '商品', '汽车', '机器人', '动物', '植物', '花', '建筑', '城堡', '龙', '天使',
    'portrait', 'person', 'woman', 'man', 'girl', 'boy', 'cat', 'dog', 'product'],
  scene: ['森林', '城市', '海边', '山顶', '沙漠', '雪地', '花园', '街道', '室内', '房间',
    '背景', '户外', '室内', '夜景', '星空', '宇宙', '海滩', '草原', '竹林',
    'background', 'scene', 'landscape', 'city', 'nature', 'indoor', 'outdoor'],
  style: ['写实', '动漫', '水彩', '油画', '水墨', '像素', '赛博朋克', '蒸汽朋克',
    '卡通', '插画', '极简', '概念艺术', '电影感', '复古', '未来',
    'realistic', 'anime', 'cartoon', 'watercolor', 'oil painting', 'style', 'cinematic'],
  lighting: ['光线', '光', '逆光', '轮廓光', '霓虹', '丁达尔', '柔和', '暖光',
    '光照', '阴影', '自然光', '棚拍', 'studio lighting', 'rim light',
    'golden hour', 'neon', 'soft', 'dramatic lighting'],
  quality: ['4K', '8K', '高清', 'HD', '细节', '高分辨率', '专业', '高画质', '高质量',
    'high quality', 'detailed', 'sharp', 'professional', '8k', 'hdr',
    'ultra', 'high resolution']
}

function detectPromptElements(text: string) {
  const lower = text.toLowerCase()
  const present: string[] = []
  const missing: string[] = []

  const checks: Array<{ label: string; keywords: string[] }> = [
    { label: '主体(subject)', keywords: CATEGORY_KEYWORDS['subject'] || [] },
    { label: '场景(scene)', keywords: CATEGORY_KEYWORDS['scene'] || [] },
    { label: '风格(style)', keywords: CATEGORY_KEYWORDS['style'] || [] },
    { label: '光线(lighting)', keywords: CATEGORY_KEYWORDS['lighting'] || [] },
    { label: '画质(quality)', keywords: CATEGORY_KEYWORDS['quality'] || [] },
  ]

  for (const { label, keywords } of checks) {
    const found = keywords.some(kw => lower.includes(kw.toLowerCase()))
    if (found) {
      present.push(label)
    } else {
      missing.push(label)
    }
  }

  presentElements.value = present
  missingElements.value = missing
}

watch(() => props.prompt, async (val) => {
  if (!val.trim()) {
    presentElements.value = []
    missingElements.value = []
    suggestedTerms.value = []
    return
  }

  detectPromptElements(val)

  loading.value = true
  try {
    const results = await searchKnowledge(val, { limit: 4 })
    suggestedTerms.value = results.filter(r => r.type === 'term' || r.type === 'industry').slice(0, 4)
  } catch {
    suggestedTerms.value = []
  } finally {
    loading.value = false
  }
}, { immediate: true })
</script>

<style scoped>
.prompt-analyzer {
  background: #fafafa;
  border-radius: 8px;
  padding: 10px 12px;
  margin-top: 8px;
  border: 1px solid #e8e8e8;
}

.loading-hint {
  display: flex;
  align-items: center;
  padding: 4px 0;
}

.missing-section {
  margin-bottom: 8px;
}

.present-section {
  margin-bottom: 8px;
}

.section-title {
  font-size: 12px;
  font-weight: 500;
  color: #555;
  margin-bottom: 4px;
}

.element-tags,
.suggest-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.suggest-section {
  padding-top: 6px;
  border-top: 1px dashed #e8e8e8;
  margin-top: 6px;
}

.tip-text {
  padding: 4px 0;
}
</style>
