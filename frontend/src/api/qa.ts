// frontend/src/api/qa.ts — 智能问答 API
import client from './client'
import type {
  ApiResponse,
  QARecord,
  QAHistoryItem,
  QAAskRequest,
  PaginationMeta,
} from '@/types'

export interface QAHistoryParams {
  course_id: string
  conversation_id?: string
  page?: number
  page_size?: number
}

export const qaApi = {
  /** 非流式问答 */
  ask(courseId: string, data: QAAskRequest) {
    return client.post<any, ApiResponse<QARecord>>(
      `/courses/${courseId}/qa/ask`,
      data
    )
  },

  /** 流式问答 — 返回 URL，由调用方用 fetch + ReadableStream 消费 */
  askStreamUrl(courseId: string) {
    return `/api/v1/courses/${courseId}/qa/ask-stream`
  },

  /** 问答历史 */
  history(params: QAHistoryParams) {
    return client.get<any, ApiResponse<QAHistoryItem[]>>(
      `/courses/${params.course_id}/qa/history`,
      { params }
    )
  },

  /** 问答详情 */
  detail(courseId: string, qaId: string) {
    return client.get<any, ApiResponse<QARecord>>(
      `/courses/${courseId}/qa/history/${qaId}`
    )
  },

  /** 提交反馈 */
  feedback(courseId: string, qaId: string, feedback: 'like' | 'dislike') {
    return client.post<any, ApiResponse<null>>(
      `/courses/${courseId}/qa/history/${qaId}/feedback`,
      { feedback }
    )
  },

  /** 清除对话 */
  clearConversation(courseId: string, conversationId: string) {
    return client.delete<any, ApiResponse<null>>(
      `/courses/${courseId}/qa/conversation/${conversationId}`
    )
  },
}
