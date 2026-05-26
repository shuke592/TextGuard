/**
 * TextGuard 放行词 API
 */
import request from '@/utils/request'

export interface WhitelistItem {
  id: number
  word: string
  type: string
  remark?: string
  expire_at?: string
  created_at?: string
}

/** 获取放行词列表 */
export function listWhitelistApi(params?: { keyword?: string; page?: number; page_size?: number }): Promise<WhitelistItem[]> {
  return request.get('/whitelist', { params })
}

/** 添加放行词 */
export function createWhitelistApi(data: { word: string; type?: string; remark?: string; expire_at?: string }): Promise<WhitelistItem> {
  return request.post('/whitelist', data)
}

/** 更新放行词 */
export function updateWhitelistApi(id: number, data: { word?: string; type?: string; remark?: string; expire_at?: string }): Promise<WhitelistItem> {
  return request.put(`/whitelist/${id}`, data)
}

/** 删除放行词 */
export function deleteWhitelistApi(id: number): Promise<void> {
  return request.delete(`/whitelist/${id}`)
}

/** 批量添加放行词 */
export function batchCreateWhitelistApi(words: Array<{ word: string; type?: string; remark?: string }>): Promise<{ count: number }> {
  return request.post('/whitelist/batch', words)
}
