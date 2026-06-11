// frontend/src/api/resources.ts — 资源管理 API
import client from './client'
import type {
  ApiResponse,
  PaginationMeta,
  Resource,
  ResourceStatusPoll,
} from '@/types'

export interface ResourceListParams {
  course_id: string
  file_type?: string
  status?: string
  keyword?: string
  sort_by?: string
  order?: string
  page?: number
  page_size?: number
}

export interface ResourceUploadResponse {
  resources: Resource[]
  failed?: { file_name: string; error: string }[]
}

export const resourceApi = {
  /** 上传单个资源 */
  upload(courseId: string, file: File) {
    const form = new FormData()
    form.append('file', file)
    return client.post<any, ApiResponse<Resource>>(
      `/courses/${courseId}/resources/upload`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  /** 批量上传资源 */
  batchUpload(courseId: string, files: File[]) {
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    return client.post<any, ApiResponse<ResourceUploadResponse>>(
      `/courses/${courseId}/resources/upload-batch`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  /** 资源列表 */
  list(params: ResourceListParams) {
    return client.get<any, ApiResponse<Resource[]>>(
      `/courses/${params.course_id}/resources`,
      { params }
    )
  },

  /** 资源详情 */
  detail(courseId: string, resourceId: string) {
    return client.get<any, ApiResponse<Resource>>(
      `/courses/${courseId}/resources/${resourceId}`
    )
  },

  /** 搜索资源 */
  search(courseId: string, q: string, page?: number, page_size?: number) {
    return client.get<any, ApiResponse<Resource[]>>(
      `/courses/${courseId}/resources/search`,
      { params: { q, page, page_size } }
    )
  },

  /** 资源处理状态 */
  status(courseId: string, resourceId: string) {
    return client.get<any, ApiResponse<ResourceStatusPoll>>(
      `/courses/${courseId}/resources/${resourceId}/status`
    )
  },

  /** 重新处理资源 */
  reprocess(courseId: string, resourceId: string) {
    return client.post<any, ApiResponse<Resource>>(
      `/courses/${courseId}/resources/${resourceId}/reprocess`
    )
  },

  /** 删除资源 */
  delete(courseId: string, resourceId: string) {
    return client.delete<any, ApiResponse<null>>(
      `/courses/${courseId}/resources/${resourceId}`,
      { data: { confirm: true, confirm_text: resourceId } }
    )
  },
}
