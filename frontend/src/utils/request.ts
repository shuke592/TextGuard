/**
 * TextGuard Axios 请求封装
 * 统一处理：Token注入、错误提示、响应拦截
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：注入 Token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // Token 过期或无效，跳转登录
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          ElMessage.error('登录已过期，请重新登录')
          router.push({ name: 'Login' })
          break
        case 403:
          ElMessage.error(data?.detail || '无权执行此操作')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          ElMessage.error(data?.detail?.[0]?.msg || '请求参数错误')
          break
        case 429:
          ElMessage.warning('请求过于频繁，请稍后再试')
          break
        case 500:
          ElMessage.error('服务器内部错误，请稍后再试')
          break
        case 503:
          ElMessage.error(data?.detail || '服务暂时不可用，请稍后再试')
          break
        default:
          ElMessage.error(data?.detail || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络')
    } else {
      ElMessage.error('网络连接异常')
    }

    return Promise.reject(error)
  }
)

export default request
