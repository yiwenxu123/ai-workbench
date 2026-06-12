<template>
  <div>
    <n-card size="small" title="风格代码" class="mb-3">
      <n-space wrap>
        <n-tag v-for="style in quickStyleCodes" :key="style.code" round type="info" class="clickable-tag" @click="insert(style.code)">
          {{ style.name }}
        </n-tag>
      </n-space>
    </n-card>

    <n-card size="small" title="质量关键词" class="mb-3">
      <n-space wrap>
        <n-tag v-for="quality in qualityKeywords" :key="quality.code" round type="success" class="clickable-tag" @click="insert(quality.code)">
          {{ quality.name }}
        </n-tag>
      </n-space>
    </n-card>

    <n-card size="small" title="光线关键词">
      <n-space wrap>
        <n-tag v-for="light in lightingKeywords" :key="light.code" round type="warning" class="clickable-tag" @click="insert(light.code)">
          {{ light.name }}
        </n-tag>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { useGeneratorStore } from '../../stores'

const message = useMessage()
const generatorStore = useGeneratorStore()

const quickStyleCodes = [
  { code: 'photorealistic', name: '写实摄影' },
  { code: 'cinematic', name: '电影感' },
  { code: 'anime', name: '动漫风格' },
  { code: 'oil painting', name: '油画风格' },
  { code: 'watercolor', name: '水彩风格' },
  { code: 'digital art', name: '数字艺术' },
  { code: 'concept art', name: '概念艺术' },
  { code: '3D render', name: '3D渲染' },
  { code: 'illustration', name: '插画风格' },
  { code: 'minimalist', name: '极简风格' }
]

const qualityKeywords = [
  { code: '4K', name: '4K高清' },
  { code: '8K', name: '8K超清' },
  { code: 'highly detailed', name: '高细节' },
  { code: 'masterpiece', name: '杰作' },
  { code: 'best quality', name: '最佳质量' },
  { code: 'ultra realistic', name: '超写实' },
  { code: 'professional', name: '专业级' },
  { code: 'studio quality', name: '工作室质量' }
]

const lightingKeywords = [
  { code: 'natural lighting', name: '自然光' },
  { code: 'studio lighting', name: '影棚光' },
  { code: 'golden hour', name: '黄金时刻' },
  { code: 'soft lighting', name: '柔光' },
  { code: 'dramatic lighting', name: '戏剧光' },
  { code: 'rim lighting', name: '轮廓光' },
  { code: 'backlight', name: '逆光' },
  { code: 'volumetric lighting', name: '体积光' }
]

function insert(code: string) {
  const current = generatorStore.prompt
  if (current && !current.endsWith('，') && !current.endsWith(',')) {
    generatorStore.prompt = current + '，' + code
  } else {
    generatorStore.prompt = current + code
  }
  message.success(`已插入: ${code}`)
}
</script>

<style scoped>
.clickable-tag {
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);
}
.clickable-tag:hover {
  transform: translateY(-1px) scale(1.04);
  box-shadow: var(--shadow-md);
}
.mb-3 { margin-bottom: 12px; }
</style>
