// frontend/src/api/tasks.ts — 教学任务 API
import client from './client'
import type {
  ApiResponse,
  Task,
} from '@/types'

export interface TaskListParams {
  course_id: string
  status?: string
  task_type?: string
  page?: number
  page_size?: number
}

export interface TaskGenerateParams {
  topic: string
  task_type: string
  difficulty: string
  additional_instructions?: string
}

export interface TaskUpdateParams {
  title?: string
  content?: string
  difficulty?: string
  estimated_time?: string
  topic?: string
}

export const taskApi = {
  /** 生成任务 */
  generate(courseId: string, data: TaskGenerateParams) {
    return client.post<any, ApiResponse<Task>>(
      `/courses/${courseId}/tasks/generate`,
      data
    )
  },

  /** 任务列表 */
  list(params: TaskListParams) {
    return client.get<any, ApiResponse<Task[]>>(
      `/courses/${params.course_id}/tasks`,
      { params }
    )
  },

  /** 任务详情 */
  detail(courseId: string, taskId: string) {
    return client.get<any, ApiResponse<Task>>(
      `/courses/${courseId}/tasks/${taskId}`
    )
  },

  /** 更新任务 */
  update(courseId: string, taskId: string, data: TaskUpdateParams) {
    return client.patch<any, ApiResponse<Task>>(
      `/courses/${courseId}/tasks/${taskId}`,
      data
    )
  },

  /** 重新生成 */
  regenerate(courseId: string, taskId: string) {
    return client.post<any, ApiResponse<Task>>(
      `/courses/${courseId}/tasks/${taskId}/regenerate`
    )
  },

  /** 发布任务 */
  publish(courseId: string, taskId: string) {
    return client.post<any, ApiResponse<Task>>(
      `/courses/${courseId}/tasks/${taskId}/publish`
    )
  },

  /** 归档任务 */
  archive(courseId: string, taskId: string) {
    return client.post<any, ApiResponse<Task>>(
      `/courses/${courseId}/tasks/${taskId}/archive`
    )
  },

  /** 删除任务 */
  delete(courseId: string, taskId: string) {
    return client.delete<any, ApiResponse<null>>(
      `/courses/${courseId}/tasks/${taskId}`,
      { data: { confirm: true, confirm_text: taskId } }
    )
  },
}
