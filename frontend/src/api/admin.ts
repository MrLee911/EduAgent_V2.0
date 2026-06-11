// frontend/src/api/admin.ts — 管理后台 API
import client from './client'
import type { ApiResponse, User } from '@/types'

export interface AdminUserListParams {
  role?: string
  is_active?: boolean
  keyword?: string
  page?: number
  page_size?: number
}

export interface AdminSettings {
  llm_model: string
  llm_api_key_masked: string
  llm_base_url: string
  llm_max_tokens: number
  llm_temperature: number
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
  top_k: number
  similarity_threshold: number
  max_upload_size_mb: number
  conversation_retention_days: number
  default_language: string
}

export const adminApi = {
  /** 用户列表 */
  listUsers(params?: AdminUserListParams) {
    return client.get<any, ApiResponse<User[]>>('/admin/users', { params })
  },

  /** 创建用户 */
  createUser(data: { username: string; email: string; password: string; role: string }) {
    return client.post<any, ApiResponse<User>>('/admin/users', data)
  },

  /** 更新用户 */
  updateUser(userId: string, data: { is_active?: boolean; role?: string; display_name?: string }) {
    return client.patch<any, ApiResponse<User>>(`/admin/users/${userId}`, data)
  },

  /** 获取系统设置 */
  getSettings() {
    return client.get<any, ApiResponse<AdminSettings>>('/admin/settings')
  },

  /** 更新系统设置 */
  updateSettings(data: Partial<AdminSettings>) {
    return client.put<any, ApiResponse<AdminSettings>>('/admin/settings', data)
  },
}
