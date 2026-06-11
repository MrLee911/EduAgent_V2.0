// frontend/src/types/index.ts — TypeScript 类型定义（与后端 API 响应一致）

// ── 通用 API 响应 ──
export interface PaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T | null
  meta?: PaginationMeta
  error?: {
    type: string
    details: { field?: string; message: string }[]
  }
}

// ── 用户 ──
export interface User {
  id: string
  username: string
  email: string
  role: 'teacher' | 'student' | 'admin'
  display_name: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  role: 'teacher' | 'student'
}

export interface TokenData {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// ── 课程 ──
export interface TeacherBrief {
  id: string
  display_name: string | null
  username: string
}

export interface CourseStats {
  member_count: number
  resource_count: number
  task_count: number
  qa_count: number
}

export interface Course {
  id: string
  name: string
  code: string
  description: string
  semester: string
  cover_image: string | null
  status: 'active' | 'archived'
  teacher?: TeacherBrief
  stats?: CourseStats
  my_role?: 'teacher' | 'student' | 'admin' | null
  member_count?: number
  created_at: string
  updated_at: string
}

export interface CourseMember {
  id: string
  user: { id: string; username: string; display_name: string | null; email?: string | null }
  role: 'teacher' | 'student'
  joined_at: string
}

// ── 资源 ──
export type ResourceStatus = 'uploading' | 'parsing' | 'chunking' | 'embedding' | 'ready' | 'failed'
export type ResourceFileType = 'pdf' | 'docx' | 'pptx' | 'md' | 'txt' | 'xlsx'

export interface Resource {
  id: string
  file_name: string
  file_type: ResourceFileType
  file_size: number
  status: ResourceStatus
  chunk_count: number
  summary: string
  file_url?: string
  error_message?: string | null
  uploaded_by?: { id: string; display_name: string | null }
  created_at: string
}

export interface ResourceStatusPoll {
  id: string
  status: ResourceStatus
  progress: {
    stage: string
    stage_index: number
    total_stages: number
    chunk_count_done: number
    chunk_count_total: number
  }
}

// ── 问答 ──
export interface QASource {
  resource_id: string
  resource_name: string
  chunk_id: string
  chunk_index: number
  score: number
  text_preview?: string
}

export interface QARecord {
  id: string
  conversation_id: string
  question: string
  answer: string
  sources: QASource[]
  feedback: 'none' | 'like' | 'dislike'
  created_at: string
}

export interface QAHistoryItem {
  id: string
  conversation_id: string
  question: string
  answer_excerpt: string
  feedback: 'none' | 'like' | 'dislike'
  created_at: string
}

export interface ConversationItem {
  conversation_id: string
  first_question: string
  message_count: number
  last_active_at: string | null
}

export interface QAAskRequest {
  question: string
  conversation_id?: string
}

export interface SSEMessage {
  type: 'thinking' | 'sources' | 'token' | 'done' | 'error'
  data: any
}

// ── 任务 ──
export type TaskType = 'class_exercise' | 'homework' | 'lab_guide'
export type TaskDifficulty = 'easy' | 'medium' | 'hard'
export type TaskStatus = 'draft' | 'published' | 'archived'

export interface TaskRefResource {
  resource_id: string
  resource_name: string
  chunk_id: string
}

export interface Task {
  id: string
  course_id?: string
  title: string
  task_type: TaskType
  topic: string
  content: string
  difficulty: TaskDifficulty
  estimated_time: string
  reference_resources: TaskRefResource[]
  status: TaskStatus
  created_by?: { id: string; display_name: string | null }
  created_at: string
  updated_at?: string
}

// ── 报告 ──
export type ReportType = 'weekly' | 'monthly' | 'semester'

export interface ReportStatistics {
  total_tasks: number
  published_tasks: number
  total_qa: number
  active_students: number
  top_questions: { question: string; count: number }[]
  total_resources: number
  new_resources: number
  suggestions: string[]
}

export interface Report {
  id: string
  course_id?: string
  report_type: ReportType
  title: string
  start_date: string
  end_date: string
  content: string
  statistics: ReportStatistics
  generated_by?: { id: string; display_name: string | null }
  created_at: string
}

// ── Toast ──
export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
}
