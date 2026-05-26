/**
 * TextGuard 自定义词库 API
 */
import request from '@/utils/request'

export interface DictionaryItem {
  id: number
  name: string
  description?: string
  is_active: boolean
  entry_count: number
  created_at?: string
  updated_at?: string
}

export interface EntryItem {
  id: number
  dictionary_id: number
  wrong_word: string
  correct_word: string
  remark?: string
  created_at?: string
}

/** 获取词库列表 */
export function listDictionariesApi(): Promise<DictionaryItem[]> {
  return request.get('/dictionary')
}

/** 创建词库 */
export function createDictionaryApi(data: { name: string; description?: string }): Promise<DictionaryItem> {
  return request.post('/dictionary', data)
}

/** 更新词库 */
export function updateDictionaryApi(id: number, data: { name?: string; description?: string; is_active?: boolean }): Promise<DictionaryItem> {
  return request.put(`/dictionary/${id}`, data)
}

/** 删除词库 */
export function deleteDictionaryApi(id: number): Promise<void> {
  return request.delete(`/dictionary/${id}`)
}

/** 获取词条列表 */
export function listEntriesApi(dictId: number, params?: { keyword?: string; page?: number; page_size?: number }): Promise<EntryItem[]> {
  return request.get(`/dictionary/${dictId}/entries`, { params })
}

/** 添加词条 */
export function createEntryApi(dictId: number, data: { wrong_word: string; correct_word: string; remark?: string }): Promise<EntryItem> {
  return request.post(`/dictionary/${dictId}/entries`, data)
}

/** 批量添加词条 */
export function batchCreateEntriesApi(dictId: number, entries: Array<{ wrong_word: string; correct_word: string; remark?: string }>): Promise<{ count: number }> {
  return request.post(`/dictionary/${dictId}/entries/batch`, { entries })
}

/** 删除词条 */
export function deleteEntryApi(dictId: number, entryId: number): Promise<void> {
  return request.delete(`/dictionary/${dictId}/entries/${entryId}`)
}
