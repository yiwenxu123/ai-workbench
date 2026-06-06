/**
 * 批量生成 composable
 * 支持变量替换批量生成图片
 */

import { ref, computed } from 'vue'

export interface BatchVariable {
  name: string
  values: string[]
}

export interface BatchTask {
  id: string
  prompt: string
  variables: Record<string, string>
  status: 'pending' | 'generating' | 'success' | 'error'
  imageUrl: string | null
  error: string | null
}

export function useBatchGenerator() {
  const template = ref('')
  const variables = ref<BatchVariable[]>([])
  const tasks = ref<BatchTask[]>([])
  const isGenerating = ref(false)
  const currentIndex = ref(0)

  const totalCombinations = computed(() => {
    if (variables.value.length === 0) return 0
    return variables.value.reduce((acc, v) => acc * v.values.filter(s => s.trim()).length, 1)
  })

  const progress = computed(() => {
    if (tasks.value.length === 0) return 0
    const completed = tasks.value.filter(t => t.status === 'success' || t.status === 'error').length
    return Math.round((completed / tasks.value.length) * 100)
  })

  function extractVariables(templateText: string): string[] {
    const matches = templateText.match(/\{(\w+)\}/g)
    return matches ? [...new Set(matches.map(m => m.slice(1, -1)))] : []
  }

  function setTemplate(templateText: string): void {
    template.value = templateText
    const extracted = extractVariables(templateText)
    
    variables.value = extracted.map(name => {
      const existing = variables.value.find(v => v.name === name)
      return {
        name,
        values: existing?.values || ['']
      }
    })
  }

  function generateCombinations(): Record<string, string>[] {
    if (variables.value.length === 0) return []

    const validVariables = variables.value.filter(v => v.values.some(s => s.trim()))
    if (validVariables.length === 0) return []

    function combine(index: number, current: Record<string, string>): Record<string, string>[] {
      if (index >= validVariables.length) return [current]

      const variable = validVariables[index]
      if (!variable) return [current]
      
      const results: Record<string, string>[] = []

      for (const value of variable.values) {
        if (value.trim()) {
          results.push(...combine(index + 1, { ...current, [variable.name]: value.trim() }))
        }
      }

      return results
    }

    return combine(0, {})
  }

  function prepareTasks(): void {
    const combinations = generateCombinations()
    
    tasks.value = combinations.map((combo, index) => {
      let prompt = template.value
      Object.entries(combo).forEach(([key, value]) => {
        prompt = prompt.replace(new RegExp(`\\{${key}\\}`, 'g'), value)
      })

      return {
        id: `batch-${Date.now()}-${index}`,
        prompt,
        variables: combo,
        status: 'pending',
        imageUrl: null,
        error: null
      }
    })
  }

  function clear(): void {
    tasks.value = []
    currentIndex.value = 0
  }

  return {
    template,
    variables,
    tasks,
    isGenerating,
    currentIndex,
    totalCombinations,
    progress,
    setTemplate,
    extractVariables,
    generateCombinations,
    prepareTasks,
    clear
  }
}
