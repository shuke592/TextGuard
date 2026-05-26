/**
 * TextGuard 文档校对相关 API
 */
import request from '@/utils/request'

export interface DocumentUploadResponse {
  file_id: string
  filename: string
  file_size: number
  file_ext: string
  text_length: number
  text_preview: string
  extracted_text: string
  extracted_html: string
}

export interface DocumentProofreadResponse {
  file_id: string
  filename: string
  issues: Array<{
    original: string
    type: string
    suggestion: string
    explanation: string
    severity: string
    chunk_index: number
  }>
  total_issues: number
  chunks_count: number
  usage: Record<string, number>
  domain: string
  record_id?: number
  corrected_download_url?: string
}

/**
 * 上传文档
 */
export function uploadDocumentApi(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/document/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

/**
 * 文档校对
 */
export function documentProofreadApi(data: {
  file_id: string
  check_types?: string[]
  domain?: string
}): Promise<DocumentProofreadResponse> {
  return request.post('/document/proofread', data)
}
