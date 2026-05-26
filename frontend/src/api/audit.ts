/**
 * TextGuard 审计日志 API
 */
import request from '@/utils/request'

/** 审计日志列表项 */
export interface AuditLogItem {
  id: number
  action_type: string
  user_id: number | null
  username: string | null
  employee_id: string | null
  is_guest: boolean
  client_ip: string
  device_type: string | null
  input_preview: string
  output_preview: string
  file_name: string | null
  status: string
  duration_ms: number | null
  created_at: string
}

/** 审计日志详情 */
export interface AuditLogDetail extends AuditLogItem {
  user_agent: string | null
  input_text: string | null
  input_length: number
  output_text: string | null
  output_length: number
  extra_params: Record<string, any> | null
  file_id: string | null
  file_path: string | null
  file_size: number | null
  error_message: string | null
  token_usage: Record<string, any> | null
}

/** 审计日志列表响应 */
export interface AuditLogListResponse {
  items: AuditLogItem[]
  total: number
  page: number
  page_size: number
}

/** 审计统计 */
export interface AuditStats {
  today_count: number
  today_guest_count: number
  today_failed_count: number
  total_count: number
  type_distribution: Record<string, number>
}

/** 查询审计日志列表 */
export function getAuditLogsApi(params: {
  page?: number
  page_size?: number
  action_type?: string
  user_type?: string
  keyword?: string
  ip?: string
  status?: string
  start_date?: string
  end_date?: string
}): Promise<AuditLogListResponse> {
  return request.get('/admin/audit/logs', { params })
}

/** 查看审计日志详情 */
export function getAuditLogDetailApi(id: number): Promise<AuditLogDetail> {
  return request.get(`/admin/audit/logs/${id}`)
}

/** 获取审计统计概览 */
export function getAuditStatsApi(): Promise<AuditStats> {
  return request.get('/admin/audit/stats')
}
