/**
 * 全局键盘快捷键 Composable
 */
import { onMounted, onUnmounted } from 'vue'

export type ShortcutHandler = (e: KeyboardEvent) => void | boolean

interface Shortcut {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  handler: ShortcutHandler
  /** 仅在特定元素聚焦时生效，默认全局 */
  target?: HTMLElement | null
  /** 描述（用于帮助面板） */
  description?: string
}

/**
 * 注册全局键盘快捷键。
 * handler 返回 false 可阻止事件冒泡。
 */
export function useKeyboard(shortcuts: Shortcut[]) {
  function onKeydown(e: KeyboardEvent) {
    for (const s of shortcuts) {
      // 如果指定了 target，仅在聚焦时触发
      if (s.target && s.target !== document.activeElement) continue

      const matchKey = e.key.toLowerCase() === s.key.toLowerCase()
      const matchCtrl = !!s.ctrl === (e.metaKey || e.ctrlKey)
      const matchShift = !!s.shift === e.shiftKey
      const matchAlt = !!s.alt === e.altKey

      if (matchKey && matchCtrl && matchShift && matchAlt) {
        const result = s.handler(e)
        if (result !== false) break
      }
    }
  }

  onMounted(() => document.addEventListener('keydown', onKeydown))
  onUnmounted(() => document.removeEventListener('keydown', onKeydown))

  return { shortcuts }
}
