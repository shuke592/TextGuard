/**
 * TextGuard 认证相关 API
 */
import request from '@/utils/request'

/**
 * 用户登录
 */
export function loginApi(data: { employee_id: string; password: string }) {
  return request.post('/auth/login', data)
}

/**
 * 获取当前用户信息
 */
export function getMeApi() {
  return request.get('/auth/me')
}

/**
 * 修改密码
 */
export function changePasswordApi(data: { old_password: string; new_password: string }) {
  return request.put('/auth/password', data)
}

/**
 * 刷新 Token
 */
export function refreshTokenApi(data: { refresh_token: string }) {
  return request.post('/auth/refresh', data)
}
