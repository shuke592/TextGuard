/**
 * TextGuard 校对相关 API
 */
import request from '@/utils/request'

export interface ProofreadIssue {
  original: string
  type: string
  suggestion: string
  explanation: string
  severity: string
  chunk_index: number
}

export interface TextProofreadResponse {
  issues: ProofreadIssue[]
  total_issues: number
  chunks_count: number
  usage: Record<string, number>
  domain: string
  check_types: string[]
  record_id?: number
}

/**
 * 文本校对
 */
export function textProofreadApi(data: {
  text: string
  check_types?: string[]
  domain?: string
}): Promise<TextProofreadResponse> {
  return request.post('/proofread/text', data, { timeout: 300000 })
}
