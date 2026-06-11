// frontend/src/api/reports.ts — 学情报告 API
import client from './client'
import type {
  ApiResponse,
  Report,
} from '@/types'

export interface ReportGenerateParams {
  report_type: string
  start_date?: string
  end_date?: string
  title?: string
}

export const reportApi = {
  /** 生成报告 */
  generate(courseId: string, data: ReportGenerateParams) {
    return client.post<any, ApiResponse<Report>>(
      `/courses/${courseId}/reports/generate`,
      data
    )
  },

  /** 报告列表 */
  list(courseId: string, page?: number, page_size?: number) {
    return client.get<any, ApiResponse<Report[]>>(
      `/courses/${courseId}/reports`,
      { params: { page, page_size } }
    )
  },

  /** 报告详情 */
  detail(courseId: string, reportId: string) {
    return client.get<any, ApiResponse<Report>>(
      `/courses/${courseId}/reports/${reportId}`
    )
  },

  /** 导出报告 */
  exportReport(courseId: string, reportId: string, format: 'md' | 'pdf' = 'md') {
    return client.get(
      `/courses/${courseId}/reports/${reportId}/export`,
      { params: { format }, responseType: 'blob' }
    )
  },
}
