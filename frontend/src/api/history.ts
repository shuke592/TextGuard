/**
 * TextGuard 校对历史 API
 */
import request from '@/utils/request'

export interface HistoryItem {
  id: number
  type: string
  domain: string
  total_issues: number
  text_preview: string
  source_filename?: string
  token_usage?: Record<string, number>
  created_at?: string
}

export interface HistoryListResponse {
  items: HistoryItem[]
  total: number
  page: number
  page_size: number
}

export interface HistoryDetail {
  id: number
  type: string
  domain: string
  original_text: string
  modified_text?: string
  check_types?: string
  result?: {
    issues: Array<{
      original: string
      type: string
      suggestion: string
      explanation: string
      severity: string
    }>
    [key: string]: any
  }
  total_issues: number
  source_filename?: string
  token_usage?: Record<string, number>
  created_at?: string
}

/** 获取历史列表 */
export function listHistoryApi(params?: {
  page?: number
  page_size?: number
  type?: string
  domain?: string
}): Promise<HistoryListResponse> {
  return request.get('/history', { params })
}

/** 获取历史详情 */
export function getHistoryDetailApi(id: number): Promise<HistoryDetail> {
  return request.get(`/history/${id}`)
}

/** 删除历史记录 */
export function deleteHistoryApi(id: number): Promise<void> {
  return request.delete(`/history/${id}`)
}
