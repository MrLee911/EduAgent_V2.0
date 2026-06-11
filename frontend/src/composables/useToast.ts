// frontend/src/composables/useToast.ts — Toast 通知 Composable（success/error/warning/info）
import { ref } from 'vue'
import type { Toast } from '@/types'

const toasts = ref<Toast[]>([])
let toastId = 0

export function useToast() {
  function addToast(type: Toast['type'], message: string, title?: string, duration = 3000) {
    const id = String(++toastId)
    const toast: Toast = { id, type, message, title, duration }
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
    return id
  }

  function removeToast(id: string) {
    const idx = toasts.value.findIndex((t) => t.id === id)
    if (idx > -1) toasts.value.splice(idx, 1)
  }

  const success = (message: string, title?: string) => addToast('success', message, title)
  const error = (message: string, title?: string) => addToast('error', message, title, 5000)
  const warning = (message: string, title?: string) => addToast('warning', message, title, 4000)
  const info = (message: string, title?: string) => addToast('info', message, title)

  return { toasts, success, error, warning, info, removeToast }
}
