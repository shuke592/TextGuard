/**
 * TextGuard 异步任务 API
 */
import request from '@/utils/request'

export interface TaskStatus {
  task_id: string
  status: string
  progress: number
  message: string
  step?: string
  result?: any
  error?: string
}

/** 查询任务状态 */
export function getTaskStatusApi(taskId: string): Promise<TaskStatus> {
  return request.get(`/tasks/${taskId}`)
}

/** 提交异步文档校对 */
export function asyncDocumentProofreadApi(data: {
  file_id: string
  check_types?: string[]
  domain?: string
}): Promise<{ task_id: string; message: string }> {
  return request.post('/document/proofread/async', data)
}

/**
 * 轮询任务状态，直到完成或失败
 * @param taskId 任务ID
 * @param onProgress 进度回调
 * @param interval 轮询间隔（毫秒）
 */
export function pollTaskStatus(
  taskId: string,
  onProgress?: (status: TaskStatus) => void,
  interval = 2000,
): Promise<TaskStatus> {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const status = await getTaskStatusApi(taskId)
        onProgress?.(status)

        if (status.status === 'SUCCESS') {
          clearInterval(timer)
          resolve(status)
        } else if (status.status === 'FAILURE') {
          clearInterval(timer)
          reject(new Error(status.error || '任务执行失败'))
        }
      } catch (err) {
        clearInterval(timer)
        reject(err)
      }
    }, interval)
  })
}
