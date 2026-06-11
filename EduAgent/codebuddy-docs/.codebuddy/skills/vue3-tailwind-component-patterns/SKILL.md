---
name: vue3-tailwind-component-patterns
description: >
  Vue 3 + Tailwind CSS + Pinia 前端组件专家级实施模式——当 CodeBuddy 开始编写前端代码、
  Vue 3 组件（`.vue` SFC）、Composable、Pinia Store、TypeScript 类型定义或 Tailwind 样式时触发。
  覆盖：项目脚手架初始化（Vite + TS + Router + Pinia）、Tailwind 配置映射 CSS 变量系统、
  TypeScript 接口定义（与 03 数据模型联动）、Axios 客户端封装（JWT + 统一响应 + 错误处理）、
  Pinia Store 模式（auth + course）、6 个 Composable（useAuth / useApi / useSSE / useToast / useCourse / useTheme）、
  Router 导航守卫（未登录/已登录/课程成员三级检查）、
  12 个通用/课程组件模板、SSE 流式 `fetch` + `ReadableStream` 实现（QA 核心）、
  响应式 5 断点适配 + 移动端 TabBar 模式、CSS 动画 6 类 @keyframes。
  **本项目 EduAgent 教学智能体专用。**
agent_created: true
---

# Vue 3 + Tailwind CSS + Pinia Frontend Component Patterns

## Purpose

本 Skill 提供 **课程资源与教学任务智能体（EduAgent）** 前端项目的专家级实施模式。从项目脚手架到每一个 Composable、每一个组件的写法，都给出了本项目特定的最佳实践和代码模板。

CodeBuddy 应使用本 Skill 作为前端开发的主参考——它覆盖了 07_页面流程图.md 定义的所有 15 个页面所需的底层模式。

## When to Use

在以下场景中触发本 Skill：

- CodeBuddy 开始创建前端项目（`npm create vue@latest`）
- CodeBuddy 开始编写 Vue 3 单文件组件（`.vue`）
- CodeBuddy 需要封装 Composable（useAuth / useApi / useSSE / useToast / useCourse）
- CodeBuddy 需要定义 TypeScript 接口（User / Course / Resource / Task / Message 等）
- CodeBuddy 需要配置 Vue Router 导航守卫
- CodeBuddy 需要实现 SSE 流式问答（QA 聊天页核心功能）
- CodeBuddy 需要编写 Tailwind 暗色模式切换
- CodeBuddy 需要实现响应式布局（5 断点适配）

---

## Pattern 1: Project Scaffold（项目脚手架）

### 创建命令（一步到位）

```bash
npm create vue@latest frontend -- --typescript --router --pinia
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/typography postcss autoprefixer
npx tailwindcss init -p
```

### 安装运行时依赖

```bash
npm install axios markdown-it highlight.js katex lucide-vue-next
npm install -D @types/markdown-it
```

### Tailwind 配置文件（关键！）

**必须将 07_页面流程图.md §1.2 的 CSS 变量映射到 Tailwind `extend`**：

```typescript
// frontend/tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',  // 通过 .dark class 切换
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        accent: {
          50: '#fff7ed',
          100: '#ffedd5',
          500: '#f97316',
          600: '#ea580c',
        },
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#6366f1',
      },
      borderRadius: {
        sm: '6px',
        md: '10px',
        lg: '16px',
        xl: '24px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(0,0,0,0.05)',
        md: '0 4px 6px rgba(0,0,0,0.07)',
        lg: '0 10px 25px rgba(0,0,0,0.1)',
        xl: '0 20px 50px rgba(0,0,0,0.15)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
} satisfies Config
```

### 入口 CSS（全局样式变量）

```css
/* frontend/src/assets/main.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50 text-gray-900 font-sans antialiased;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  .dark body {
    @apply bg-gray-900 text-gray-100;
  }
}
```

---

## Pattern 2: TypeScript Type Definitions（类型定义）

### 文件位置：`frontend/src/types/index.ts`

**必须与 03_数据模型与数据库设计.md 的表结构 + 04_API接口文档.md §9 通用结构精确对齐**：

```typescript
// ============================================================
// Enums (from 03 §3)
// ============================================================
export type UserRole = 'admin' | 'teacher' | 'student'
export type ResourceStatus = 'uploading' | 'parsing' | 'ready' | 'failed'
export type TaskStatus = 'draft' | 'published' | 'archived'
export type TaskDifficulty = 'easy' | 'medium' | 'hard'
export type TaskType = 'choice' | 'short_answer' | 'essay' | 'coding' | 'discussion'
export type ReportPeriod = 'week' | 'month' | 'semester'
export type FeedbackType = 'like' | 'dislike'

// ============================================================
// User (from 03 §4.1 users 表)
// ============================================================
export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  avatar_url: string | null
  is_active: boolean
  created_at: string   // ISO 8601
  updated_at: string
}

export interface UserSummary {
  id: string
  username: string
  avatar_url: string | null
  role: UserRole
}

// ============================================================
// Course (from 03 §4.2 courses 表)
// ============================================================
export interface Course {
  id: string
  name: string
  description: string | null
  invite_code: string
  created_by: string
  member_count: number
  resource_count: number
  created_at: string
  updated_at: string
}

export interface CourseMember {
  id: string
  user: UserSummary
  role: 'teacher' | 'student'
  joined_at: string
}

// ============================================================
// Resource (from 03 §4.3 resources 表)
// ============================================================
export interface Resource {
  id: string
  course_id: string
  file_name: string
  file_type: string       // 'pdf' | 'pptx' | 'docx' | 'md' | 'txt'
  file_size: number       // bytes
  status: ResourceStatus
  chunk_count: number
  error_message: string | null
  uploaded_by: string
  created_at: string
}

export interface UploadProgress {
  resource_id: string    // 临时 ID（上传完成后替换）
  file_name: string
  progress: number       // 0-100
  status: 'uploading' | 'parsing' | 'ready' | 'failed'
}

// ============================================================
// QA / Chat (from 03 §4.6 qa_records 表)
// ============================================================
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string         // Markdown
  sources?: Source[]
  feedback?: FeedbackType | null
  created_at: string
}

export interface Source {
  resource_id: string
  resource_name: string
  chunk_id: string
  page?: number
  chapter?: string
  score: number
}

export interface QASession {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

// ============================================================
// Task (from 03 §4.5 tasks 表)
// ============================================================
export interface Task {
  id: string
  course_id: string
  title: string
  description: string    // Markdown
  task_type: TaskType
  difficulty: TaskDifficulty
  status: TaskStatus
  reference_answer: string | null
  reference_resources: Source[]
  statistics: {
    generated_count: number
    avg_difficulty: number
  }
  created_by: string
  created_at: string
}

export interface TaskGenerationRequest {
  topic: string
  task_type: TaskType
  difficulty: TaskDifficulty
  count: number          // default 3, max 10
}

// ============================================================
// Report (from 03 §4.7 reports 表)
// ============================================================
export interface Report {
  id: string
  course_id: string
  title: string
  period: ReportPeriod
  summary: string        // Markdown
  content: string        // Markdown full
  statistics: {
    qa_count: number
    task_count: number
    active_students: number
    hot_topics: HotTopic[]
  }
  created_at: string
}

export interface HotTopic {
  topic: string
  frequency: number
}

// ============================================================
// API Response (from 04 §1.2 统一响应格式)
// ============================================================
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  items: T[]
  meta: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface ApiError {
  code: number
  message: string
  error: {
    type: string
    detail: string
    field?: string
  }
}

// ============================================================
// SSE Stream Events (from 04 §5.2 流式问答)
// ============================================================
export type SSEEventType = 'thinking' | 'sources' | 'token' | 'done' | 'error'

export interface SSEEvent {
  type: SSEEventType
  data: SSEThinkingData | SSESourcesData | SSETokenData | SSEDoneData | SSEErrorData
}

export interface SSEThinkingData { message: string }
export interface SSESourcesData { sources: Source[] }
export interface SSETokenData { content: string }
export interface SSEDoneData { message_id: string; full_content: string }
export interface SSEErrorData { message: string; code: string }
```

### 关键对齐

| 类型 | 来源 |
|------|------|
| `User` / `Course` / `Resource` / `Task` / `Report` | 03 §4 表结构 |
| `ApiResponse<T>` / `PaginatedData<T>` | 04 §1.2 统一响应格式 |
| `SSEEvent*` | 04 §5.2 流式问答 SSE 事件 |
| `Source` | 04 §9.2 Source 通用结构 |
| 所有枚举值 | 03 §3 枚举类型 |

---

## Pattern 3: Axios HTTP Client（API 客户端封装）

### 文件位置：`frontend/src/api/client.ts`

```typescript
// frontend/src/api/client.ts
import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse, ApiError } from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ============================================================
// Request Interceptor: 注入 JWT Token
// ============================================================
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ============================================================
// Response Interceptor: 统一解包 + Token 过期处理
// ============================================================
client.interceptors.response.use(
  (response) => {
    // 统一解包：返回 ApiResponse.data，调用方无需再 .data.data
    return response.data
  },
  async (error: AxiosError<ApiError>) => {
    const status = error.response?.status

    // Token 过期 → 尝试 refresh（仅一次，防止死循环）
    if (status === 401 && !(error.config as any)?._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token: newRefresh } = (res.data as any).data
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', newRefresh)

          if (error.config) {
            (error.config as any)._retry = true
            error.config.headers!.Authorization = `Bearer ${access_token}`
            return client(error.config)
          }
        } catch {
          // Refresh 失败 → 清除 Token → 跳转登录
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }

    // 其他错误 → 提取 message
    const message = error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(message))
  }
)

export default client
```

### API 函数组织方式（按模块分文件）

```typescript
// frontend/src/api/auth.ts
import client from './client'
import type { ApiResponse, User } from '@/types'

export const authApi = {
  login: (data: { username: string; password: string }) =>
    client.post<any, ApiResponse<{ access_token: string; refresh_token: string; user: User }>>('/auth/login', data),

  register: (data: { username: string; email: string; password: string; role: string }) =>
    client.post<any, ApiResponse<User>>('/auth/register', data),

  getMe: () =>
    client.get<any, ApiResponse<User>>('/auth/me'),

  refresh: (refresh_token: string) =>
    client.post<any, ApiResponse<{ access_token: string; refresh_token: string }>>('/auth/refresh', { refresh_token }),
}
```

**⚠️ 关键约定**：
- 所有 API 函数必须定义返回类型（`ApiResponse<T>`），利用 Axios 泛型确保类型安全
- `client.post` 的三个泛型参数：`<TRequest, TResponse>`（因为 interceptors 已经解包）
- 按 04 API 文档的模块拆分：`api/auth.ts` / `api/courses.ts` / `api/resources.ts` / `api/qa.ts` / `api/tasks.ts` / `api/reports.ts` / `api/admin.ts`

---

## Pattern 4: Pinia Stores（状态管理）

### 4.1 Auth Store

**文件：`frontend/src/stores/auth.ts`**

```typescript
// frontend/src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => !!user.value)
  const userRole = computed(() => user.value?.role || null)

  // Actions
  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    user.value = res.data.user
    router.push('/home')
  }

  async function fetchMe() {
    try {
      const res = await authApi.getMe()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
    router.push('/login')
  }

  async function register(data: { username: string; email: string; password: string; role: string }) {
    const res = await authApi.register(data)
    return res.data
  }

  return { user, isAuthenticated, userRole, login, logout, fetchMe, register }
})
```

### 4.2 Course Store

**文件：`frontend/src/stores/course.ts`**

```typescript
// frontend/src/stores/course.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Course } from '@/types'
import { coursesApi } from '@/api/courses'

export const useCourseStore = defineStore('course', () => {
  const currentCourse = ref<Course | null>(null)
  const courseList = ref<Course[]>([])

  async function fetchCourses() {
    const res = await coursesApi.list()
    courseList.value = res.data.items
  }

  async function setCurrentCourse(courseId: string) {
    const res = await coursesApi.get(courseId)
    currentCourse.value = res.data
  }

  function clearCurrentCourse() {
    currentCourse.value = null
  }

  return { currentCourse, courseList, fetchCourses, setCurrentCourse, clearCurrentCourse }
})
```

### ⚠️ Store 定义规则

- **必须用 Composition API 风格**（`defineStore('name', () => { ... })`），不用 Options API
- **不要用 Vuex**——本项目不能引入 Vuex 依赖
- **Store 拆分原则**：按业务域，不按页面。auth / course / theme 各一个 store

---

## Pattern 5: Composables（组合式函数）

### 5.1 useApi（通用 API 调用封装）

**文件：`frontend/src/composables/useApi.ts`**

```typescript
// frontend/src/composables/useApi.ts
import { ref } from 'vue'

export function useApi<T>() {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute(promise: Promise<T>) {
    loading.value = true
    error.value = null
    try {
      data.value = await promise
      return data.value
    } catch (e: any) {
      error.value = e.message || '请求失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
```

**使用示例**：

```typescript
const { data: courses, loading, error, execute } = useApi<PaginatedData<Course>>()

onMounted(() => {
  execute(coursesApi.list())
})

// 模板中使用：
// <LoadingSpinner v-if="loading" />
// <EmptyState v-else-if="error" :title="error" />
// <CourseCard v-else v-for="c in courses?.items" :course="c" />
```

### 5.2 useToast（Toast 通知）

**文件：`frontend/src/composables/useToast.ts`**

```typescript
// frontend/src/composables/useToast.ts
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: number
  type: ToastType
  message: string
  duration: number
}

let nextId = 0
const toasts = ref<Toast[]>([])

export function useToast() {
  function show(type: ToastType, message: string, duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, type, message, duration })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  const success = (msg: string) => show('success', msg)
  const error   = (msg: string) => show('error', msg, 5000)
  const warning = (msg: string) => show('warning', msg, 4000)
  const info    = (msg: string) => show('info', msg, 3000)

  return { toasts, success, error, warning, info }
}
```

### 5.3 useSSE（流式问答核心！）

**这是本项目最重要的 Composable，直接决定 QA 聊天体验。**

**文件：`frontend/src/composables/useSSE.ts`**

```typescript
// frontend/src/composables/useSSE.ts
import { ref } from 'vue'
import type { Source } from '@/types'

export interface SSEState {
  isStreaming: boolean
  thinking: string | null
  content: string
  sources: Source[]
  messageId: string | null
  error: string | null
}

export function useSSE() {
  const state = ref<SSEState>({
    isStreaming: false,
    thinking: null,
    content: '',
    sources: [],
    messageId: null,
    error: null,
  })

  let abortController: AbortController | null = null

  async function startStream(url: string, body: Record<string, any>) {
    // Reset state
    state.value = {
      isStreaming: true,
      thinking: '正在检索知识库...',
      content: '',
      sources: [],
      messageId: null,
      error: null,
    }

    abortController = new AbortController()
    const token = localStorage.getItem('access_token')

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Split SSE events by double newline
        const events = buffer.split('\n\n')
        buffer = events.pop() || '' // Keep incomplete event in buffer

        for (const event of events) {
          if (!event.trim()) continue
          parseSSEEvent(event, state)
        }
      }

      // Process remaining buffer
      if (buffer.trim()) {
        parseSSEEvent(buffer, state)
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        // User cancelled — not an error
      } else {
        state.value.error = e.message || '连接中断'
      }
    } finally {
      state.value.isStreaming = false
      state.value.thinking = null
    }
  }

  function stop() {
    abortController?.abort()
    state.value.isStreaming = false
  }

  function parseSSEEvent(raw: string, state: any) {
    // Parse SSE lines: "event:xxx\ndata:yyy"
    let eventType = ''
    let data = ''

    for (const line of raw.split('\n')) {
      if (line.startsWith('event:')) eventType = line.slice(6).trim()
      if (line.startsWith('data:')) data = line.slice(5).trim()
    }

    try {
      const parsed = JSON.parse(data)
      switch (eventType) {
        case 'thinking':
          state.value.thinking = parsed.message
          break
        case 'sources':
          state.value.sources = parsed
          break
        case 'token':
          state.value.content += parsed.content
          break
        case 'done':
          state.value.messageId = parsed.message_id
          state.value.content = parsed.full_content  // 最终内容
          break
        case 'error':
          state.value.error = parsed.message
          break
      }
    } catch {
      // Invalid JSON — skip
    }
  }

  return { state, startStream, stop }
}
```

**⚠️ SSE 关键规则**：
- 使用 `fetch` + `ReadableStream`（不是 `EventSource`！因为需要 POST + Authorization header）
- Buffer + `split('\n\n')` 解析 SSE（标准 SSE 格式）
- 每个事件类型 `thinking / sources / token / done / error` 分别处理
- 实现 `stop()` 可随时中断（AbortController）
- `try/catch` 包住整个流读取过程，网络中断不会让页面崩溃

### 5.4 useCourse（当前课程上下文）

```typescript
// frontend/src/composables/useCourse.ts
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/course'

export function useCourse() {
  const route = useRoute()
  const courseStore = useCourseStore()

  const courseId = computed(() => route.params.courseId as string)
  const course = computed(() => courseStore.currentCourse)
  const isTeacher = computed(() => {
    // 从 course members 中判断当前用户角色（一期简化：用 authStore.userRole）
    return true // TODO: 从 course member 表查询
  })

  return { courseId, course, isTeacher }
}
```

### 5.5 useTheme（明暗主题切换）

```typescript
// frontend/src/composables/useTheme.ts
import { ref, watchEffect } from 'vue'

type Theme = 'light' | 'dark' | 'system'

const theme = ref<Theme>(
  (localStorage.getItem('theme') as Theme) || 'system'
)

function applyTheme(t: Theme) {
  const root = document.documentElement
  if (t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

watchEffect(() => {
  localStorage.setItem('theme', theme.value)
  applyTheme(theme.value)
})

// Listen system preference changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (theme.value === 'system') applyTheme('system')
})

export function useTheme() {
  function setTheme(t: Theme) { theme.value = t }
  return { theme, setTheme }
}
```

---

## Pattern 6: Vue Router（路由配置 + 导航守卫）

**文件：`frontend/src/router/index.ts`**

```typescript
// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ================================================================
    // Public
    // ================================================================
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { guest: true },
    },

    // ================================================================
    // Auth Required
    // ================================================================
    {
      path: '/home',
      name: 'Home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/courses',
      name: 'CourseList',
      component: () => import('@/views/course/CourseListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/courses/:courseId',
      component: () => import('@/views/course/CourseDetailView.vue'),
      meta: { requiresAuth: true, requiresCourseMember: true },
      children: [
        { path: '', redirect: (to) => ({ path: `${to.path}/qa` }) },
        { path: 'resources', component: () => import('@/views/course/CourseResourcesView.vue') },
        { path: 'qa',         component: () => import('@/views/course/CourseQAView.vue') },
        { path: 'tasks',      component: () => import('@/views/course/CourseTasksView.vue') },
        { path: 'tasks/:taskId',     component: () => import('@/views/course/CourseTaskDetailView.vue') },
        { path: 'reports',    component: () => import('@/views/course/CourseReportsView.vue') },
        { path: 'reports/:reportId', component: () => import('@/views/course/CourseReportDetailView.vue') },
        { path: 'settings',   component: () => import('@/views/course/CourseSettingsView.vue') },
      ],
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },

    // ================================================================
    // Admin Only
    // ================================================================
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('@/views/admin/AdminDashboardView.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },

    // ================================================================
    // Fallback
    // ================================================================
    { path: '/', redirect: '/home' },
    { path: '/:pathMatch(.*)*', redirect: '/home' },
  ],
})

// ================================================================
// Global Navigation Guard
// ================================================================
router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  // 1. 已登录访问 guest 页面（login/register）→ 重定向到 home
  if (to.meta.guest && auth.isAuthenticated) {
    return next('/home')
  }

  // 2. 需要认证但未登录 → 跳转登录
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }

  // 3. 角色检查
  if (to.meta.roles && !(to.meta.roles as string[]).includes(auth.userRole || '')) {
    return next('/home')  // 无权限 → 回首页
  }

  // 4. 课程成员检查（延迟到组件内做，避免路由守卫阻塞）
  // 在 CourseDetailView 的 onMounted 中调 GET /courses/:id/check-member

  next()
})

export default router
```

**⚠️ 导航守卫顺序不可乱**：

```
guest check → requiresAuth check → roles check → path param check
```

课程成员检查放在**组件内**（不在全局守卫），因为需要调 API，放在路由守卫中会阻塞页面。

---

## Pattern 7: Layout Components（布局组件）

### 7.1 AppLayout（主布局壳）

```vue
<!-- frontend/src/components/layout/AppLayout.vue -->
<script setup lang="ts">
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCoursePage = computed(() => route.matched.some(r => r.meta.layout === 'course'))
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <div class="flex flex-1">
      <!-- Sidebar: 仅课程详情页显示 -->
      <AppSidebar v-if="isCoursePage" />
      <main class="flex-1 p-4 md:p-6 lg:p-8 overflow-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>
```

### 7.2 AppHeader

```vue
<!-- frontend/src/components/layout/AppHeader.vue -->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'
import { BookOpen, User, LogOut, Sun, Moon } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const { theme, setTheme } = useTheme()
</script>

<template>
  <header class="h-14 border-b border-gray-200 bg-white flex items-center px-4 sticky top-0 z-40">
    <!-- Logo -->
    <router-link to="/home" class="flex items-center gap-2 mr-8">
      <BookOpen class="w-6 h-6 text-primary-600" />
      <span class="font-bold text-lg text-gray-900">EduAgent</span>
    </router-link>

    <!-- Breadcrumb (optional, computed from route) -->
    <nav class="hidden md:flex items-center text-sm text-gray-500">
      <!-- breadcrumb items -->
    </nav>

    <div class="ml-auto flex items-center gap-3">
      <!-- Theme Toggle -->
      <button @click="setTheme(theme === 'dark' ? 'light' : 'dark')" class="p-2 rounded-md hover:bg-gray-100">
        <Sun v-if="theme === 'dark'" class="w-5 h-5" />
        <Moon v-else class="w-5 h-5" />
      </button>

      <!-- Notifications (simplified) -->
      <button class="p-2 rounded-md hover:bg-gray-100 relative">
        <Bell class="w-5 h-5 text-gray-500" />
      </button>

      <!-- User Dropdown -->
      <div class="relative" v-if="auth.user">
        <button class="flex items-center gap-2 p-1 rounded-full hover:bg-gray-100">
          <img :src="auth.user.avatar_url || '/default-avatar.png'" class="w-8 h-8 rounded-full" />
          <span class="hidden md:inline text-sm font-medium">{{ auth.user.username }}</span>
        </button>
        <!-- Dropdown menu (on click) -->
      </div>
    </div>
  </header>
</template>
```

### 7.3 AppSidebar（课程 Tab 导航）

```vue
<!-- frontend/src/components/layout/AppSidebar.vue -->
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { BookOpen, MessageCircle, FileText, BarChart3, Settings } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const courseId = route.params.courseId as string

const tabs = [
  { path: 'resources', label: '资源', icon: BookOpen },
  { path: 'qa',         label: '问答', icon: MessageCircle },
  { path: 'tasks',      label: '任务', icon: FileText },
  { path: 'reports',    label: '报告', icon: BarChart3 },
  { path: 'settings',   label: '设置', icon: Settings },
]

const activeTab = computed(() => {
  return tabs.find(t => route.path.includes(`/${t.path}`))
})
</script>

<template>
  <aside class="w-16 lg:w-56 border-r border-gray-200 bg-white flex flex-col py-2 shrink-0">
    <nav class="flex flex-col gap-1 px-2">
      <router-link
        v-for="tab in tabs"
        :key="tab.path"
        :to="`/courses/${courseId}/${tab.path}`"
        class="flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors"
        :class="activeTab?.path === tab.path
          ? 'bg-primary-50 text-primary-700 font-medium'
          : 'text-gray-600 hover:bg-gray-100'"
      >
        <component :is="tab.icon" class="w-5 h-5 shrink-0" />
        <span class="hidden lg:inline">{{ tab.label }}</span>
      </router-link>
    </nav>

    <!-- 底部课程信息 -->
    <div class="mt-auto p-3 border-t border-gray-200 hidden lg:block">
      <p class="text-xs text-gray-400 truncate">{{ /* 课程名称 */ }}</p>
    </div>
  </aside>

  <!-- 移动端：底部 TabBar 替代侧边栏 -->
  <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex justify-around py-1 lg:hidden z-50">
    <button v-for="tab in tabs" :key="tab.path"
      @click="router.push(`/courses/${courseId}/${tab.path}`)"
      class="flex flex-col items-center p-2 text-xs"
      :class="activeTab?.path === tab.path ? 'text-primary-600' : 'text-gray-400'"
    >
      <component :is="tab.icon" class="w-5 h-5" />
      <span>{{ tab.label }}</span>
    </button>
  </nav>
</template>
```

---

## Pattern 8: Common Components（通用组件）

### 8.1 LoadingSpinner

```vue
<!-- frontend/src/components/common/LoadingSpinner.vue -->
<script setup lang="ts">
defineProps<{ fullscreen?: boolean; text?: string }>()
</script>

<template>
  <div :class="fullscreen ? 'fixed inset-0 z-50 flex items-center justify-center bg-white/80' : 'flex items-center justify-center py-12'">
    <div class="flex flex-col items-center gap-3">
      <div class="w-8 h-8 border-3 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      <p v-if="text" class="text-sm text-gray-500">{{ text }}</p>
    </div>
  </div>
</template>
```

### 8.2 EmptyState

```vue
<!-- frontend/src/components/common/EmptyState.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import { BookOpen, Upload, FileText, Inbox } from 'lucide-vue-next'

const props = defineProps<{
  icon?: 'book' | 'upload' | 'file' | 'inbox'
  title: string
  description?: string
  actionLabel?: string
  actionRoute?: string
}>()

const emit = defineEmits<{ action: [] }>()

const iconComponent = computed(() => {
  const map = { book: BookOpen, upload: Upload, file: FileText, inbox: Inbox }
  return map[props.icon || 'inbox']
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <component :is="iconComponent" class="w-16 h-16 text-gray-300 mb-4" />
    <h3 class="text-lg font-semibold text-gray-700 mb-2">{{ title }}</h3>
    <p v-if="description" class="text-sm text-gray-500 mb-6 max-w-sm">{{ description }}</p>
    <router-link v-if="actionLabel && actionRoute" :to="actionRoute"
      class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors text-sm"
    >
      {{ actionLabel }}
    </router-link>
    <button v-else-if="actionLabel" @click="emit('action')"
      class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors text-sm"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
```

### 8.3 ConfirmDialog

```vue
<!-- frontend/src/components/common/ConfirmDialog.vue -->
<script setup lang="ts">
defineProps<{
  visible: boolean
  title: string
  message: string
  confirmText?: string
  danger?: boolean
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="emit('cancel')">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
          <h3 class="text-lg font-semibold mb-2">{{ title }}</h3>
          <p class="text-sm text-gray-600 mb-6">{{ message }}</p>
          <div class="flex justify-end gap-3">
            <button @click="emit('cancel')" class="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors">
              取消
            </button>
            <button @click="emit('confirm')"
              :class="danger
                ? 'bg-danger text-white hover:bg-red-600'
                : 'bg-primary-600 text-white hover:bg-primary-700'"
              class="px-4 py-2 text-sm rounded-md transition-colors"
            >
              {{ confirmText || '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
```

### 8.4 MarkdownRenderer

```vue
<!-- frontend/src/components/common/MarkdownRenderer.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const props = defineProps<{ content: string }>()

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

const rendered = computed(() => md.render(props.content))
</script>

<template>
  <div class="prose prose-sm max-w-none dark:prose-invert" v-html="rendered" />
</template>
```

### 8.5 FileUploader

```vue
<!-- frontend/src/components/course/FileUploader.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { Upload as UploadIcon } from 'lucide-vue-next'

const props = defineProps<{
  courseId: string
  maxSize?: number  // MB
}>()
const emit = defineEmits<{ success: [fileNames: string[]] }>()

const isDragging = ref(false)
const uploading = ref(false)

async function handleFiles(files: FileList) {
  uploading.value = true
  const formData = new FormData()
  for (const file of files) {
    formData.append('files', file)
  }
  try {
    const res = await fetch(`/api/v1/courses/${props.courseId}/resources/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
      body: formData,
    })
    const result = await res.json()
    emit('success', result.data.map((r: any) => r.file_name))
  } catch (e) {
    // Error handled by parent
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
    :class="isDragging ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-300'"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="isDragging = false; handleFiles($event.dataTransfer!.files)"
  >
    <UploadIcon v-if="!uploading" class="w-10 h-10 text-gray-400 mx-auto mb-2" />
    <div v-else class="w-8 h-8 border-3 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-2" />
    <p class="text-sm text-gray-600 mb-1">
      拖拽文件到此处，或 <span class="text-primary-600">点击上传</span>
    </p>
    <p class="text-xs text-gray-400">
      支持 PDF / PPTX / DOCX / MD / TXT · 单文件 ≤ {{ maxSize || 50 }}MB
    </p>
    <input type="file" multiple accept=".pdf,.pptx,.docx,.md,.txt" class="hidden"
      @change="handleFiles(($event.target as HTMLInputElement).files!)"
    />
  </div>
</template>
```

### 8.6 StatusBadge

```vue
<!-- frontend/src/components/common/StatusBadge.vue -->
<script setup lang="ts">
import type { ResourceStatus, TaskStatus } from '@/types'
import { computed } from 'vue'

const props = defineProps<{
  status: ResourceStatus | TaskStatus
  type: 'resource' | 'task'
}>()

const config = computed(() => {
  const map = {
    resource: {
      uploading: { label: '上传中', color: 'bg-yellow-100 text-yellow-800' },
      parsing:   { label: '解析中', color: 'bg-blue-100 text-blue-800' },
      ready:     { label: '就绪',   color: 'bg-green-100 text-green-800' },
      failed:    { label: '失败',   color: 'bg-red-100 text-red-800' },
    },
    task: {
      draft:     { label: '草稿',   color: 'bg-gray-100 text-gray-800' },
      published: { label: '已发布', color: 'bg-green-100 text-green-800' },
      archived:  { label: '已归档', color: 'bg-yellow-100 text-yellow-800' },
    },
  }
  return map[props.type][props.status as keyof typeof map.resource] || { label: props.status, color: 'bg-gray-100 text-gray-800' }
})
</script>

<template>
  <span class="inline-flex px-2 py-0.5 text-xs font-medium rounded-full" :class="config.color">
    {{ config.label }}
  </span>
</template>
```

---

## Pattern 9: SSE Streaming Chat（QA 核心页面模式）

**这是本项目最重要的页面模式——展示了如何将 useSSE composable 与 UI 组件结合。**

```vue
<!-- frontend/src/views/course/CourseQAView.vue -->
<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSSE } from '@/composables/useSSE'
import { useToast } from '@/composables/useToast'
import type { Message, Source } from '@/types'
import { Send, Square } from 'lucide-vue-next'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'

const route = useRoute()
const { state, startStream, stop } = useSSE()
const toast = useToast()

// ================================================================
// State
// ================================================================
const messages = ref<Message[]>([])
const inputText = ref('')
const chatContainer = ref<HTMLDivElement>()
const showSources = ref<Source[]>([])

// ================================================================
// Send Message
// ================================================================
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || state.value.isStreaming) return

  // 1. 添加用户消息
  const userMsg: Message = {
    id: crypto.randomUUID(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputText.value = ''

  // 2. 创建助手消息占位
  const assistantMsg: Message = {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: '',
    created_at: new Date().toISOString(),
  }
  messages.value.push(assistantMsg)

  await nextTick()
  scrollToBottom()

  // 3. 启动 SSE 流
  await startStream(
    `/api/v1/qa/ask/stream`,
    {
      question: text,
      course_id: route.params.courseId,
      session_id: null, // 一期单次对话
    }
  )

  // 4. 流结束后更新最后一条消息
  if (!state.value.error) {
    assistantMsg.content = state.value.content
    assistantMsg.sources = state.value.sources
    assistantMsg.id = state.value.messageId || assistantMsg.id
  } else {
    assistantMsg.content = `❌ ${state.value.error}`
    toast.error(state.value.error)
  }

  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-56px)]">
    <!-- Messages -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div v-if="messages.length === 0" class="text-center py-16">
        <h3 class="text-lg font-semibold text-gray-700 mb-4">👋 有什么问题想问？</h3>
        <div class="flex flex-wrap justify-center gap-2">
          <button v-for="q in ['这门课主要讲什么？', 'XX概念怎么理解？', '出一道练习题']" :key="q"
            @click="inputText = q; sendMessage()"
            class="px-4 py-2 text-sm border border-gray-200 rounded-full hover:bg-gray-100 transition-colors"
          >
            {{ q }}
          </button>
        </div>
      </div>

      <div v-for="msg in messages" :key="msg.id" class="flex gap-3"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- AI Avatar -->
        <div v-if="msg.role === 'assistant'" class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
          <span class="text-xs text-primary-600 font-bold">AI</span>
        </div>

        <div class="max-w-[80%]" :class="msg.role === 'user' ? 'bg-primary-600 text-white rounded-lg rounded-tr-sm px-4 py-2' : ''">
          <!-- AI Message (Markdown) -->
          <div v-if="msg.role === 'assistant'" class="bg-white border border-gray-100 rounded-lg rounded-tl-sm px-4 py-3 shadow-sm">
            <MarkdownRenderer :content="msg.content || (state.isStreaming && messages[messages.length-1]?.id === msg.id ? state.value.content : '')" />
            <!-- Streaming cursor -->
            <span v-if="state.isStreaming && messages[messages.length-1]?.id === msg.id && state.value.content"
              class="streaming-cursor" />
            <!-- Sources -->
            <div v-if="msg.sources?.length && !state.isStreaming" class="mt-3 pt-3 border-t border-gray-100">
              <p class="text-xs text-gray-400 mb-1">📚 参考来源：</p>
              <div v-for="s in msg.sources" :key="s.chunk_id" class="text-xs text-gray-500">
                {{ s.resource_name }} · 相似度 {{ (s.score * 100).toFixed(0) }}%
              </div>
            </div>
          </div>
          <!-- User Message -->
          <p v-else class="text-sm">{{ msg.content }}</p>
        </div>

        <!-- User Avatar -->
        <div v-if="msg.role === 'user'" class="w-8 h-8 rounded-full bg-accent-100 flex items-center justify-center shrink-0">
          <span class="text-xs text-accent-600 font-bold">我</span>
        </div>
      </div>

      <!-- Thinking indicator -->
      <div v-if="state.isStreaming && !state.value.content" class="flex gap-3">
        <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
          <span class="text-xs text-primary-600 font-bold">AI</span>
        </div>
        <div class="bg-white border border-gray-100 rounded-lg rounded-tl-sm px-4 py-3 shadow-sm">
          <div class="flex gap-1.5">
            <span class="dot w-2 h-2 bg-primary-400 rounded-full" />
            <span class="dot w-2 h-2 bg-primary-400 rounded-full" />
            <span class="dot w-2 h-2 bg-primary-400 rounded-full" />
          </div>
        </div>
      </div>
    </div>

    <!-- Input Bar -->
    <div class="border-t border-gray-200 p-4 bg-white">
      <div class="flex gap-3 max-w-3xl mx-auto">
        <input v-model="inputText" @keydown.enter="sendMessage()"
          :disabled="state.isStreaming"
          placeholder="输入你的问题..."
          class="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:bg-gray-50"
        />
        <button @click="state.isStreaming ? stop() : sendMessage()"
          :disabled="!state.isStreaming && !inputText.trim()"
          :class="state.isStreaming
            ? 'bg-danger hover:bg-red-600'
            : 'bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300'"
          class="px-4 py-2.5 text-white rounded-lg transition-colors shrink-0"
        >
          <Square v-if="state.isStreaming" class="w-5 h-5" />
          <Send v-else class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 流式光标（来自 07 §10.2） */
.streaming-cursor::after {
  content: '▌';
  animation: cursor-blink 0.8s infinite;
  color: var(--color-primary-500);
}
@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
/* AI 思考跳动点（来自 07 §10.2） */
.dot { animation: typing-bounce 1.4s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}
</style>
```

### QA 页面状态覆盖规则

| 状态 | 表现 |
|------|------|
| **空（无对话）** | 显示 3 个建议问题快捷按钮 |
| **加载（发送中）** | 输入框禁用 + 发送按钮变停用秒表 + AI 消息区显示跳动点 |
| **流式输出中** | `streamingContent` 逐字追加 + `▌` 光标闪烁 + Markdown 实时渲染 |
| **流式完成** | 停止光标闪烁 + 显示来源列表 + 显示赞/踩按钮 |
| **流式出错** | AI 消息变为红色错误文本 + "重试" 按钮 |

---

## Pattern 10: Course List Page（课程列表页模式）

```vue
<!-- frontend/src/views/course/CourseListView.vue -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useApi } from '@/composables/useApi'
import { useCourseStore } from '@/stores/course'
import { useToast } from '@/composables/useToast'
import { coursesApi } from '@/api/courses'
import type { Course, PaginatedData } from '@/types'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import CourseCard from '@/components/course/CourseCard.vue'

const { data, loading, error, execute } = useApi<PaginatedData<Course>>()
const courseStore = useCourseStore()
const toast = useToast()

onMounted(() => {
  loadCourses()
})

async function loadCourses() {
  try {
    await execute(coursesApi.list())
    courseStore.courseList = data.value?.items || []
  } catch {
    toast.error('加载课程列表失败')
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">我的课程</h1>
      <button @click="/* open create/join dialog */"
        class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm">
        + 创建 / 加入课程
      </button>
    </div>

    <LoadingSpinner v-if="loading" text="加载课程中..." />
    <EmptyState v-else-if="error" icon="book" :title="error"
      action-label="重试" @action="loadCourses" />
    <EmptyState v-else-if="!data?.items?.length" icon="book"
      title="还没有课程" description="创建新课程或通过邀请码加入" />
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <CourseCard v-for="course in data.items" :key="course.id" :course="course" />
    </div>
  </div>
</template>
```

### 页面状态覆盖通用模式（每页必实现）

```typescript
// ⚠️ 每个数据驱动页面必须覆盖 4 种状态：
// 1. loading    → LoadingSpinner
// 2. empty      → EmptyState（含操作引导）
// 3. error      → 错误消息 + 重试按钮
// 4. normal     → 数据展示

// Vue 模板中的通用嵌套结构：
// <LoadingSpinner v-if="loading" />
// <EmptyState v-else-if="error" :title="error" action-label="重试" @action="fetchData" />
// <EmptyState v-else-if="!items.length" ... :action-label="..." />
// <div v-else> ...正常内容... </div>
```

---

## Pattern 11: Page View with State Matrix（数据驱动的页面模板）

**每页必须实现 4 态覆盖（Loading / Empty / Error / Normal）**：

| 状态 | 条件 | 渲染组件 |
|------|------|---------|
| Loading | `loading === true` | `<LoadingSpinner />` |
| Error | `error !== null` | `<EmptyState icon="inbox" :title="error" action-label="重试" @action="fetchData" />` |
| Empty | `items.length === 0` | `<EmptyState :icon="..." :title="..." :description="..." :action-label="..." />` |
| Normal | 以上皆不满足 | 正常数据展示 |

**对应 07_页面流程图.md §11.1 的完整状态矩阵：每页根据角色、数据量不同，EmptyState 的 title/description/action 都有所不同。**

---

## Pattern 12: Responsive Breakpoints（响应式 5 断点）

### Tailwind 默认断点 + 本项目适配策略

```css
/* ⚠️ 核心规则（来自 07 §9.2）： */

/* sm: 640px — 单列→可双列，表格→卡片列表 */
@screen sm { .course-grid { @apply grid-cols-1; } }

/* md: 768px — 侧边栏显示，课程列表 2 列 */
@screen md { .course-grid { @apply grid-cols-2; } .sidebar { @apply block; } }

/* lg: 1024px — 侧边栏展开文字 + 课程列表 3 列，QA 对话区居中 800px */
@screen lg {
  .course-grid { @apply grid-cols-3; }
  .qa-container { @apply max-w-[800px] mx-auto; }
  .sidebar-text { @apply inline; }
}

/* xl: 1280px — 更多列 */
@screen xl { .dashboard-grid { @apply grid-cols-3; } }

/* 2xl: 1536px — 内容最大宽度 1400px 居中 */
@screen 2xl { .page-container { @apply max-w-[1400px] mx-auto; } }
```

### 移动端底部 TabBar（替代侧边栏）

```vue
<!-- 仅在 lg:hidden（< 1024px）时显示 -->
<nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200
  flex justify-around py-1 lg:hidden z-50 safe-area-inset-bottom">
  <!-- Tab 图标列表，active 状态用 primary-600 -->
</nav>
```

**⚠️ 底部 TabBar 必须加 `safe-area-inset-bottom`**（iPhone 底部 Home Indicator 区域）。

---

## CSS Animations（交互动效）

### 全局 CSS 动画（来自 07 §10.2）

```css
/* frontend/src/assets/animations.css */

/* 按钮 hover 微交互 */
.btn { transition: all 150ms ease-out; }
.btn:hover { transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.07); }
.btn:active { transform: translateY(0); }

/* 路由过渡（Vue Router <RouterView> 包裹 <Transition>） */
.page-enter-active { transition: opacity 200ms ease-out, transform 200ms ease-out; }
.page-leave-active { transition: opacity 150ms ease-in, transform 150ms ease-in; }
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to { opacity: 0; transform: translateY(-8px); }

/* Modal 弹窗 */
.modal-enter-active { transition: all 300ms cubic-bezier(0.16,1,0.3,1); }
.modal-leave-active { transition: all 200ms ease-in; }
.modal-enter-from { opacity: 0; transform: scale(0.95); }
.modal-leave-to { opacity: 0; transform: scale(0.95); }

/* Toast 通知滑入/滑出 */
.toast-enter-active { transition: all 400ms ease-out; }
.toast-leave-active { transition: all 300ms ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(100%) translateY(-50%); }
.toast-leave-to { opacity: 0; transform: translateX(100%); }

/* 骨架屏呼吸动画 */
@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.skeleton { animation: skeleton-pulse 1.5s ease-in-out infinite; }

/* AI 跳动点 */
@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

/* 流式光标闪烁 */
@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
```

---

## Project-Specific Constraints（本项目特定约束）

### 1. 文件结构必须遵循 02 目录规范

```
frontend/src/
├── api/            ← Axios 请求封装（按模块分文件：auth.ts / courses.ts / qa.ts ...）
├── assets/         ← 静态资源 + CSS（main.css / animations.css）
├── components/
│   ├── common/     ← 通用组件（LoadingSpinner / EmptyState / ConfirmDialog / ToastNotification / MarkdownRenderer / StatusBadge / FileUploader）
│   ├── layout/     ← 布局组件（AppLayout / AppHeader / AppSidebar）
│   └── course/     ← 课程相关组件（CourseCard / ResourceList / QAChat / TaskCard）
├── composables/    ← 组合式函数（useApi / useToast / useSSE / useCourse / useTheme）
├── router/         ← Vue Router 配置
├── stores/         ← Pinia Store（auth / course / theme）
├── types/          ← TypeScript 接口定义
└── views/          ← 页面视图
    ├── auth/       ← Login / Register
    ├── course/     ← CourseList / CourseDetail / CourseQA / CourseTasks / CourseReports / ...
    └── admin/      ← AdminDashboard
```

### 2. 组件懒加载

所有页面视图必须用动态导入（`() => import(...)`），不用静态 import：

```typescript
// ✅ 正确
{ path: '/login', component: () => import('@/views/auth/LoginView.vue') }

// ❌ 错误（会全部打包到主 chunk）
import LoginView from '@/views/auth/LoginView.vue'
```

### 3. API 调用全部通过 Axios client

禁止在组件中直接 `fetch()`：必须通过 `frontend/src/api/*.ts` 模块调用。

```typescript
// ✅ 正确
import { coursesApi } from '@/api/courses'
const res = await coursesApi.list()

// ❌ 错误
const res = await fetch('/api/v1/courses')
```

### 4. SSE 流式问答只用于 QA 页面

其他页面（Resource 上传进度、Task 生成进度）暂不使用 SSE，使用普通轮询。

### 5. 暗色模式一期可选

暗色模式 CSS 变量已定义（07 §1.2），但一期不强制实现。通过 `useTheme()` composable 控制，默认跟随系统。

### 6. 移动端适配优先级

按 07 §9.2 表格实现，关键适配顺序：
1. 侧边栏 → 底部 TabBar（最重要）
2. 课程列表 → 响应式列数
3. 资源表格 → 卡片列表
4. Modal/Dialog → bottom sheet

---

## Anti-Patterns（常见错误 — Do NOT Do）

### ❌ 1. 用 Options API 而非 Composition API

```vue
<!-- ❌ 错误 -->
<script>
export default {
  data() { return { count: 0 } },
  methods: { increment() { this.count++ } }
}
</script>

<!-- ✅ 正确 -->
<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
function increment() { count.value++ }
</script>
```

**原因**：Composition API 是 Vue 3 推荐写法，本项目所有代码必须统一使用 `<script setup lang="ts">`。

### ❌ 2. 在组件中直接 fetch()

```typescript
// ❌ 错误：绕过 Axios interceptor（Token 注入、错误解包全失效）
const res = await fetch('/api/v1/courses')
const data = await res.json()
```

**原因**：绕过 `api/client.ts` 的 JWT 注入 + 统一错误处理，Token 过期不会触发刷新。

### ❌ 3. SSE 用 EventSource 而非 fetch

```typescript
// ❌ 错误：EventSource 不支持 POST + Authorization header
const es = new EventSource('/api/v1/qa/ask/stream')
```

**原因**：本项目 SSE 端点需要 POST + JSON body + JWT Token，EventSource 只支持 GET。

### ❌ 4. 忘记 loading / error / empty 三态

```vue
<!-- ❌ 错误：数据为空时白屏 -->
<div v-for="item in items">{{ item.name }}</div>

<!-- ✅ 正确 -->
<LoadingSpinner v-if="loading" />
<EmptyState v-else-if="error" ... />
<EmptyState v-else-if="!items.length" ... />
<div v-else v-for="item in items">...</div>
```

**原因**：用户体验——用户需要知道"正在加载"、"没有数据"还是"加载失败"。

### ❌ 5. TypeScript 类型定义与 API 响应不一致

```typescript
// ❌ 错误：自己定义 Course 类型，与 03 数据模型不一致
interface Course { id: string; title: string; ... }

// ✅ 正确：从 types/index.ts 导入，确保与后端表结构一致
import type { Course } from '@/types'
```

### ❌ 6. Pinia 用 Options Store 代替 Setup Store

```typescript
// ❌ 错误：Options Store（旧风格）
export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null }),
  actions: { login() { ... } }
})

// ✅ 正确：Setup Store（Composition API 风格）
export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  function login() { ... }
  return { user, login }
})
```

### ❌ 7. 布局组件中忘记 responsive class

```vue
<!-- ❌ 错误：侧边栏所有尺寸都显示 -->
<aside class="w-56">...</aside>

<!-- ✅ 正确：移动端隐藏，桌面端显示，中间尺寸折叠为图标 -->
<aside class="w-16 lg:w-56">...</aside>
<!-- 同时需要在模板底部添加移动端 TabBar -->
```

---

## Quick Reference（速查表）

### 要做某事 → 看哪个 Pattern → 产出哪个文件？

| 要做的事 | Pattern | 产出文件 |
|---------|:--:|------|
| 创建前端项目 | Pattern 1 | 完整 `frontend/` 目录 |
| 配置 Tailwind 颜色/圆角/阴影 | Pattern 1 | `tailwind.config.ts` + `main.css` |
| 定义 User/Course/Resource/Task 类型 | Pattern 2 | `types/index.ts` |
| 封装 Axios + JWT 刷新 | Pattern 3 | `api/client.ts` |
| 写登录/注册 API 调用 | Pattern 3 | `api/auth.ts` |
| 管理登录状态 | Pattern 4.1 | `stores/auth.ts` |
| 管理当前课程 | Pattern 4.2 | `stores/course.ts` |
| 通用 loading/error 封装 | Pattern 5.1 | `composables/useApi.ts` |
| Toast 通知 | Pattern 5.2 | `composables/useToast.ts` |
| SSE 流式问答 | Pattern 5.3 | `composables/useSSE.ts` |
| 获取当前 courseId + course | Pattern 5.4 | `composables/useCourse.ts` |
| 明暗主题切换 | Pattern 5.5 | `composables/useTheme.ts` |
| 路由 + 导航守卫 | Pattern 6 | `router/index.ts` |
| 主布局 + Header + Sidebar | Pattern 7 | `components/layout/*.vue` |
| Loading / Empty / Confirm / Markdown 通用组件 | Pattern 8 | `components/common/*.vue` |
| QA 聊天页面（含 SSE） | Pattern 9 | `views/course/CourseQAView.vue` |
| 课程列表页（含 4 态） | Pattern 10 | `views/course/CourseListView.vue` |
| 创建任意数据驱动页面 | Pattern 11 | `views/**/*.vue` |
| 响应式布局适配 | Pattern 12 | 所有组件 + Tailwind class |
| CSS 动画/过渡 | CSS Animations | `assets/animations.css` |

---

## References

本 Skill 基于以下项目文档编写，所有代码模板均与这些文档精确对齐：

| 文档 | 对齐内容 |
|------|---------|
| `docs/07_页面流程图.md` | 全部 15 页面布局、设计系统、组件清单、Composable 清单、状态矩阵、CSS 动画 |
| `docs/03_数据模型与数据库设计.md` | TypeScript 接口定义（User / Course / Resource / Task / Report 等） |
| `docs/04_API接口文档.md` | API 调用封装（Axios base URL、统一响应格式、SSE 事件类型） |
| `docs/02_技术架构文档.md` | 前端目录结构、技术栈选型（Vue 3 + Tailwind + Pinia） |
