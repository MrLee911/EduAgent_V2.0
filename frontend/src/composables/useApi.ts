// frontend/src/composables/useApi.ts — 通用 API 调用 Composable（loading/error/execute）
import { ref, type Ref } from 'vue'

export function useApi<T = any>(
  fn: (...args: any[]) => Promise<T>,
) {
  const data: Ref<T | null> = ref(null)
  const error: Ref<string | null> = ref(null)
  const isLoading = ref(false)
  const isReady = ref(false)

  async function execute(...args: any[]): Promise<T | null> {
    isLoading.value = true
    error.value = null
    isReady.value = false
    try {
      const result = await fn(...args)
      data.value = result
      isReady.value = true
      return result
    } catch (e: any) {
      const msg = e?.response?.data?.message ?? e?.message ?? '请求失败'
      error.value = msg
      return null
    } finally {
      isLoading.value = false
    }
  }

  function reset() {
    data.value = null
    error.value = null
    isLoading.value = false
    isReady.value = false
  }

  return { data, error, isLoading, isReady, execute, reset }
}
