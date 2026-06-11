<script setup lang="ts">
/**
 * CourseQAView.vue — 智能问答聊天页 (T8.6)
 * 左侧历史对话侧边栏 + 右侧聊天区域
 */
import { ref, nextTick, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'
import { qaApi } from '@/api/qa'
import { useToast } from '@/composables/useToast'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ConversationItem } from '@/types'

const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()
const toast = useToast()

// ── State ──
interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources?: { resource_name: string; score: number; text_preview?: string }[]
  feedback?: 'none' | 'like' | 'dislike'
  qaId?: string
  isStreaming?: boolean
  createdAt: string
}

const messages = ref<Message[]>([])
const inputText = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const streamingSources = ref<any[]>([])
const streamingMessageId = ref('')
const isLoading = ref(false)
const loadError = ref('')
const convId = ref<string>('')

// ── Sidebar State ──
const conversations = ref<ConversationItem[]>([])
const sidebarOpen = ref(true)
const loadingConversations = ref(false)
const deletingConvId = ref<string | null>(null)

const chatContainer = ref<HTMLElement | null>(null)

// ── Suggested questions ──
const suggestedQuestions = [
  '这门课程主要涵盖哪些内容？',
  '请帮我总结一下课程的重点知识',
  '最近有哪些重要的教学资源？',
]

// ── Computed ──
const courseId = computed(() => route.params.courseId as string)
const isTeacher = computed(() => courseStore.isTeacherOfCourse)

// ── Sidebar Methods ──
async function loadConversations() {
  loadingConversations.value = true
  try {
    const res = await qaApi.conversations(courseId.value)
    conversations.value = res.data || []
  } catch {
    conversations.value = []
  } finally {
    loadingConversations.value = false
  }
}

async function selectConversation(conv: ConversationItem) {
  if (conv.conversation_id === convId.value) return
  convId.value = conv.conversation_id
  messages.value = []

  // 加载该对话的历史消息
  isLoading.value = true
  try {
    const res = await qaApi.history({
      course_id: courseId.value,
      conversation_id: conv.conversation_id,
      page: 1,
      page_size: 50,
    })
    if (res.data && res.data.length > 0) {
      // 按时间升序排列，转为 Message 格式
      const sorted = [...res.data].reverse()
      for (const item of sorted) {
        messages.value.push({
          id: item.id,
          role: 'user',
          content: item.question,
          feedback: 'none',
          createdAt: item.created_at,
        })
        messages.value.push({
          id: `${item.id}_ans`,
          role: 'assistant',
          content: item.answer_excerpt || '(无回答内容)',
          feedback: item.feedback,
          qaId: item.id,
          createdAt: item.created_at,
        })
      }
    }
  } catch (e: any) {
    toast.error('加载对话记录失败')
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

async function deleteConversation(conv: ConversationItem, e?: Event) {
  e?.stopPropagation()
  if (deletingConvId.value) return

  const confirmed = window.confirm(`确定要删除此对话吗？包含 ${conv.message_count} 条问答记录，删除后不可恢复。`)
  if (!confirmed) return

  deletingConvId.value = conv.conversation_id
  try {
    await qaApi.deleteConversation(courseId.value, conv.conversation_id)
    conversations.value = conversations.value.filter(
      c => c.conversation_id !== conv.conversation_id
    )
    // 如果删除的是当前对话，清空聊天区域
    if (convId.value === conv.conversation_id) {
      messages.value = []
      convId.value = ''
    }
    toast.success('对话已删除')
  } catch {
    toast.error('删除对话失败')
  } finally {
    deletingConvId.value = null
  }
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 7) return `${diffDay}天前`

  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

// ── Chat Methods ──
function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function generateId() {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

async function sendMessage(question?: string) {
  const text = (question || inputText.value).trim()
  if (!text || isStreaming.value) return

  // Add user message
  const userMsg: Message = {
    id: generateId(),
    role: 'user',
    content: text,
    createdAt: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputText.value = ''
  scrollToBottom()

  // Add assistant placeholder
  const assistantId = generateId()
  const assistantMsg: Message = {
    id: assistantId,
    role: 'assistant',
    content: '',
    isStreaming: true,
    createdAt: new Date().toISOString(),
  }
  messages.value.push(assistantMsg)
  streamingContent.value = ''
  streamingSources.value = []
  isStreaming.value = true
  streamingMessageId.value = assistantId
  scrollToBottom()

  // SSE Stream
  const url = qaApi.askStreamUrl(courseId.value)
  const token = localStorage.getItem('access_token')
  const abortController = new AbortController()

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        question: text,
        conversation_id: convId.value || undefined,
      }),
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
      buffer = lines.pop() || ''

      let eventType = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim()
          if (!dataStr) continue

          try {
            const data = JSON.parse(dataStr)
            handleSSEEvent(eventType, data)
          } catch {
            // Skip unparseable data
          }
          eventType = ''
        }
      }
    }
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      handleSSEEvent('error', { message: '网络连接中断，请重试', code: 'NETWORK_ERROR' })
    }
  }
}

function handleSSEEvent(type: string, data: any) {
  const idx = messages.value.findIndex(m => m.id === streamingMessageId.value)
  if (idx === -1) return

  switch (type) {
    case 'thinking':
      break

    case 'sources':
      if (Array.isArray(data)) {
        streamingSources.value = data
        messages.value[idx].sources = data.map((s: any) => ({
          resource_name: s.resource_name || s.resourceName,
          score: s.score || 0,
          text_preview: s.text_preview || s.textPreview,
        }))
      }
      break

    case 'token':
      streamingContent.value += data.content || data || ''
      messages.value[idx].content = streamingContent.value
      scrollToBottom()
      break

    case 'done':
      messages.value[idx].content = data.full_content || streamingContent.value
      messages.value[idx].isStreaming = false
      if (data.message_id) {
        messages.value[idx].qaId = data.message_id
      }
      if (data.conversation_id) {
        convId.value = data.conversation_id
      }
      isStreaming.value = false
      streamingMessageId.value = ''
      scrollToBottom()
      // 刷新侧边栏对话列表
      loadConversations()
      break

    case 'error':
      messages.value[idx].content = `❌ **生成失败**：${data.message || '未知错误'}`
      messages.value[idx].isStreaming = false
      isStreaming.value = false
      streamingMessageId.value = ''
      toast.error(data.message || '生成回答失败')
      break
  }
}

function stopStreaming() {
  isStreaming.value = false
  const idx = messages.value.findIndex(m => m.id === streamingMessageId.value)
  if (idx !== -1) {
    messages.value[idx].isStreaming = false
    if (!messages.value[idx].content) {
      messages.value[idx].content = '⏸ _已停止生成_'
    }
  }
  streamingMessageId.value = ''
}

async function retryLast() {
  const lastUser = [...messages.value].reverse().find(m => m.role === 'user')
  if (lastUser) {
    const lastAiIdx = [...messages.value].reverse().findIndex(m => m.role === 'assistant')
    if (lastAiIdx !== -1) {
      messages.value.splice(messages.value.length - 1 - lastAiIdx, 1)
    }
    await sendMessage(lastUser.content)
  }
}

async function submitFeedback(msg: Message, feedback: 'like' | 'dislike') {
  if (!msg.qaId) return
  try {
    await qaApi.feedback(courseId.value, msg.qaId, feedback)
    msg.feedback = feedback
    toast.success(feedback === 'like' ? '感谢你的反馈！' : '已收到你的反馈')
  } catch {
    toast.error('反馈提交失败')
  }
}

async function newConversation() {
  messages.value = []
  convId.value = ''
  toast.info('已开始新对话')
}

// ── Keyboard shortcuts ──
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
  if (e.key === 'Escape') {
    if (isStreaming.value) {
      stopStreaming()
    }
    inputText.value = ''
  }
}

// ── Lifecycle ──
onMounted(async () => {
  if (courseId.value && !courseStore.currentCourse) {
    await courseStore.fetchCourseDetail(courseId.value)
  }
  await loadConversations()
})
</script>

<template>
  <div class="flex h-full bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <!-- ── Left Sidebar: Conversation List ── -->
    <div
      :class="[
        'flex flex-col border-r border-gray-200 bg-gray-50 transition-all duration-200 flex-shrink-0',
        sidebarOpen ? 'w-64' : 'w-0 overflow-hidden border-r-0'
      ]"
    >
      <!-- Sidebar Header -->
      <div class="flex items-center justify-between px-3 py-3 border-b border-gray-200">
        <h3 class="text-sm font-semibold text-gray-700 truncate">历史对话</h3>
        <button
          @click="newConversation"
          class="p-1 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
          title="新建对话"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>

      <!-- Conversation List -->
      <div class="flex-1 overflow-y-auto">
        <LoadingSpinner v-if="loadingConversations" text="加载中..." />

        <div v-else-if="conversations.length === 0" class="p-4 text-center">
          <p class="text-xs text-gray-400">暂无历史对话</p>
          <p class="text-xs text-gray-400 mt-1">提问后将自动保存</p>
        </div>

        <div v-else class="py-1">
          <div
            v-for="conv in conversations"
            :key="conv.conversation_id"
            @click="selectConversation(conv)"
            :class="[
              'group relative px-3 py-2.5 mx-1.5 rounded-lg cursor-pointer transition-colors',
              convId === conv.conversation_id
                ? 'bg-primary-50 border border-primary-200'
                : 'hover:bg-gray-100 border border-transparent'
            ]"
          >
            <!-- 对话标题 -->
            <p class="text-sm text-gray-800 font-medium truncate pr-6">
              {{ conv.first_question || '新对话' }}
            </p>
            <!-- 对话元信息 -->
            <div class="flex items-center gap-2 mt-1">
              <span class="text-xs text-gray-400">{{ conv.message_count }} 条问答</span>
              <span class="text-xs text-gray-300">·</span>
              <span class="text-xs text-gray-400">{{ formatTime(conv.last_active_at) }}</span>
            </div>
            <!-- 删除按钮 -->
            <button
              @click="deleteConversation(conv, $event)"
              :disabled="deletingConvId === conv.conversation_id"
              class="absolute top-2 right-2 p-1 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100 transition-all"
              title="删除对话"
            >
              <svg
                v-if="deletingConvId !== conv.conversation_id"
                xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Right: Chat Area ── -->
    <div class="flex flex-col flex-1 min-w-0">
      <!-- Chat Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50/50">
        <div class="flex items-center gap-2">
          <!-- Toggle Sidebar Button -->
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
            :title="sidebarOpen ? '收起侧边栏' : '展开侧边栏'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path v-if="sidebarOpen" stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
          <span class="text-lg">💬</span>
          <h2 class="text-base font-semibold text-gray-800">智能问答</h2>
          <span class="text-xs text-gray-400 ml-1">| AI 助教</span>
          <span v-if="conversations.length > 0" class="text-xs text-gray-400 ml-1">({{ conversations.length }} 个对话)</span>
        </div>
        <button
          @click="newConversation"
          class="text-xs text-gray-500 hover:text-primary-600 transition-colors flex items-center gap-1"
          title="新建对话"
        >
          <span class="i-lucide-plus w-3.5 h-3.5">+</span>
          新对话
        </button>
      </div>

      <!-- Loading State -->
      <LoadingSpinner v-if="isLoading" text="加载对话历史..." />

      <!-- Empty State -->
      <div
        v-else-if="messages.length === 0"
        class="flex-1 flex items-center justify-center p-8"
      >
        <div class="text-center max-w-md">
          <div class="text-5xl mb-4">🤖</div>
          <h3 class="text-lg font-semibold text-gray-700 mb-2">向课程 AI 助教提问</h3>
          <p class="text-sm text-gray-400 mb-6">
            我可以帮你解答课程问题、总结知识点、查找资料等
          </p>
          <div class="space-y-2">
            <button
              v-for="q in suggestedQuestions"
              :key="q"
              @click="sendMessage(q)"
              class="block w-full text-left px-4 py-2.5 text-sm text-gray-600 bg-gray-50 hover:bg-primary-50 hover:text-primary-700 rounded-lg transition-colors border border-gray-100 hover:border-primary-200"
            >
              {{ q }}
            </button>
          </div>
          <p class="text-xs text-gray-400 mt-4">
            该课程暂无知识库资源，问答将基于 AI 通用知识回答
          </p>
        </div>
      </div>

      <!-- Error State -->
      <div
        v-else-if="loadError"
        class="flex-1 flex items-center justify-center p-8"
      >
        <EmptyState
          icon="⚠️"
          title="加载失败"
          :description="loadError"
        />
        <button
          @click="loadConversations"
          class="mt-4 px-4 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >
          重试
        </button>
      </div>

      <!-- Chat Messages -->
      <div
        v-else
        ref="chatContainer"
        class="flex-1 overflow-y-auto px-4 py-4 space-y-4"
      >
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="[
            'flex gap-3',
            msg.role === 'user' ? 'justify-end' : 'justify-start'
          ]"
        >
          <!-- Assistant Avatar -->
          <div
            v-if="msg.role === 'assistant'"
            class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 text-sm"
          >
            🤖
          </div>

          <!-- Message Bubble -->
          <div
            :class="[
              'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
              msg.role === 'user'
                ? 'bg-primary-500 text-white rounded-br-md'
                : msg.isStreaming && !msg.content
                  ? 'bg-gray-100 text-gray-400 rounded-bl-md'
                  : 'bg-gray-100 text-gray-800 rounded-bl-md'
            ]"
          >
            <!-- User message -->
            <template v-if="msg.role === 'user'">
              {{ msg.content }}
            </template>

            <!-- Assistant: Thinking -->
            <template v-else-if="msg.isStreaming && !msg.content">
              <div class="flex items-center gap-1 py-1">
                <span class="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot"></span>
                <span class="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot" style="animation-delay: 0.2s"></span>
                <span class="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot" style="animation-delay: 0.4s"></span>
              </div>
            </template>

            <!-- Assistant: Markdown Content -->
            <template v-else-if="msg.role === 'assistant'">
              <MarkdownRenderer
                :content="msg.content"
                :class="{ 'cursor-blink-after': msg.isStreaming }"
              />

              <!-- Sources -->
              <div
                v-if="msg.sources && msg.sources.length > 0 && !msg.isStreaming"
                class="mt-3 pt-3 border-t border-gray-200"
              >
                <p class="text-xs font-medium text-gray-500 mb-1.5">📚 参考来源</p>
                <div class="space-y-1">
                  <a
                    v-for="(src, si) in msg.sources"
                    :key="si"
                    href="#"
                    class="block text-xs text-primary-600 hover:text-primary-800 truncate"
                    :title="src.resource_name"
                  >
                    {{ src.resource_name }}
                    <span class="text-gray-400 ml-1">(相关度: {{ (src.score * 100).toFixed(0) }}%)</span>
                  </a>
                </div>
              </div>

              <!-- Feedback -->
              <div
                v-if="!msg.isStreaming && msg.content"
                class="flex items-center gap-2 mt-2 pt-2 border-t border-gray-200"
              >
                <button
                  @click="submitFeedback(msg, 'like')"
                  :class="[
                    'text-xs p-1 rounded transition-colors',
                    msg.feedback === 'like'
                      ? 'text-green-600 bg-green-50'
                      : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
                  ]"
                  title="有帮助"
                >
                  👍
                </button>
                <button
                  @click="submitFeedback(msg, 'dislike')"
                  :class="[
                    'text-xs p-1 rounded transition-colors',
                    msg.feedback === 'dislike'
                      ? 'text-red-600 bg-red-50'
                      : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                  ]"
                  title="无帮助"
                >
                  👎
                </button>
              </div>
            </template>
          </div>

          <!-- User Avatar -->
          <div
            v-if="msg.role === 'user'"
            class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 text-sm"
          >
            👤
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="border-t border-gray-200 p-3">
        <div class="flex items-end gap-2">
          <textarea
            v-model="inputText"
            @keydown="onKeydown"
            :disabled="isStreaming"
            placeholder="输入你的问题... (Enter 发送，Shift+Enter 换行)"
            rows="1"
            class="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/40 focus:border-primary-400 disabled:bg-gray-100 disabled:cursor-not-allowed placeholder-gray-400"
          ></textarea>
          <button
            v-if="!isStreaming"
            @click="sendMessage()"
            :disabled="!inputText.trim()"
            class="px-4 py-2.5 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            发送
          </button>
          <button
            v-else
            @click="stopStreaming"
            class="px-4 py-2.5 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors flex-shrink-0"
          >
            ⏸ 停止
          </button>
        </div>
        <p class="text-xs text-gray-400 mt-1.5">
          Enter 发送 · Shift+Enter 换行 · Esc 清空
        </p>
      </div>
    </div>
  </div>
</template>
