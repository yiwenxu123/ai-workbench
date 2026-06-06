import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEditorStore = defineStore('editor', () => {
  const sourceImage = ref<string | null>(null)
  const instruction = ref('')
  const isEditing = ref(false)

  function setSourceImage(imageUrl: string) {
    sourceImage.value = imageUrl
  }

  function clearSourceImage() {
    sourceImage.value = null
  }

  function setInstruction(value: string) {
    instruction.value = value
  }

  function clearInstruction() {
    instruction.value = ''
  }

  return {
    sourceImage,
    instruction,
    isEditing,
    setSourceImage,
    clearSourceImage,
    setInstruction,
    clearInstruction
  }
})
