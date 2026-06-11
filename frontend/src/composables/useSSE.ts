// frontend/src/composables/useSSE.ts — SSE 流式连接 Composable（fetch+ReadableStream+AbortController+5 事件）
import { ref, type Ref } from 'vue'
import type { SSEMessage, QASource } from '@/types'

export interface SSEOptions {
  onThinking?: (message: string) => void
  onSources?: (sources: QASource[]) => void
  onToken?: (content: string) => void
  onDone?: (data: { id: string; conversation_id: string; sources: any[]; created_at: string }) => void
  onError?: (error: { type: string; message: string }) => void
}

export function useSSE() {
  const isStreaming = ref(false)
  const streamContent = ref('')
  const streamSources = ref<QASource[]>([])
  const streamError: Ref<string | null> = ref(null)
  let abortController: AbortController | null = null

  async function startStream(url: string, body: Record<string, any>, options: SSEOptions = {}) {
    isStreaming.value = true
    streamContent.value = ''
    streamSources.value = []
    streamError.value = null
    abortController = new AbortController()

    const token = localStorage.getItem('access_token')

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim()
          if (!line.startsWith('event: ') && !line.startsWith('data: ')) continue

          // 收集 event 和 data
          if (line.startsWith('event: ')) {
            const eventType = line.slice(7)
            const dataLine = lines[i + 1]?.trim()
            if (dataLine?.startsWith('data: ')) {
              const dataStr = dataLine.slice(6)
              try {
                const data = JSON.parse(dataStr)
                handleEvent(eventType, data, options)
              } catch {
                // skip malformed
              }
              i++ // skip data line
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        streamError.value = e.message || '连接异常'
        options.onError?.({ type: 'NETWORK_ERROR', message: streamError.value! })
      }
    } finally {
      isStreaming.value = false
    }
  }

  function handleEvent(type: string, data: any, options: SSEOptions) {
    switch (type) {
      case 'thinking':
        options.onThinking?.(data.message)
        break
      case 'sources':
        streamSources.value = data.sources ?? []
        options.onSources?.(data.sources)
        break
      case 'token':
        streamContent.value += data.content
        options.onToken?.(data.content)
        break
      case 'done':
        options.onDone?.(data)
        break
      case 'error':
        streamError.value = data.message
        options.onError?.(data)
        break
    }
  }

  function abortStream() {
    abortController?.abort()
    isStreaming.value = false
  }

  function reset() {
    streamContent.value = ''
    streamSources.value = []
    streamError.value = null
  }

  return {
    isStreaming, streamContent, streamSources, streamError,
    startStream, abortStream, reset,
  }
}
