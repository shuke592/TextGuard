/**
 * TextGuard AI润色相关 API
 */
import request from '@/utils/request'

/** 润色风格项 */
export interface PolishStyle {
  key: string
  name: string
  description: string
}

/** 润色风格列表响应 */
export interface PolishStylesResponse {
  styles: PolishStyle[]
}

/** 单个润色版本 */
export interface PolishVersion {
  label: string
  level: string
  content: string
}

/** 润色响应 */
export interface PolishResponse {
  versions: PolishVersion[]
  style: string
  style_name: string
  usage: Record<string, number>
}

/**
 * 获取所有润色风格
 */
export function getPolishStylesApi(): Promise<PolishStylesResponse> {
  return request.get('/polish/styles')
}

/**
 * AI文本润色
 */
export function textPolishApi(data: {
  text: string
  style: string
}): Promise<PolishResponse> {
  return request.post('/polish/text', data, { timeout: 300000 })
}
