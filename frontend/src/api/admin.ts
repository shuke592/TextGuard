/**
 * TextGuard 管理后台 API
 */
import request from '@/utils/request'

// ========== 仪表盘 ==========
export interface DashboardStats {
  today_proofread_count: number
  total_proofread_count: number
  total_users: number
  active_users_today: number
  total_token_usage: number
  today_document_count: number
  total_document_count: number
}

export function getDashboardStatsApi(): Promise<DashboardStats> {
  return request.get('/admin/dashboard/stats')
}

// ========== 用户管理 ==========
export interface AdminUserItem {
  id: number
  employee_id: string
  username: string
  phone?: string
  gender?: string
  department?: string
  role_id?: number
  role_name?: string
  is_active: boolean
  daily_quota?: number
  remark?: string
  created_at?: string
}

export function listUsersApi(params?: {
  page?: number; page_size?: number; keyword?: string; role_id?: number; is_active?: boolean
}): Promise<{ items: AdminUserItem[]; total: number }> {
  return request.get('/admin/users', { params })
}

export function createUserApi(data: {
  employee_id: string; username: string; password: string; role_id: number;
  phone?: string; gender?: string; department?: string; daily_quota?: number; remark?: string
}): Promise<AdminUserItem> {
  return request.post('/admin/users', data)
}

export function updateUserApi(id: number, data: Record<string, any>): Promise<AdminUserItem> {
  return request.put(`/admin/users/${id}`, data)
}

export function deleteUserApi(id: number): Promise<void> {
  return request.delete(`/admin/users/${id}`)
}

// ========== 角色管理 ==========
export interface RoleItem {
  id: number; name: string; code: string; description?: string;
  is_system: boolean; is_active: boolean; sort_order: number; permission_ids: number[]
}

export interface PermissionItem {
  id: number; name: string; code: string; type: string;
  parent_id?: number; path?: string; icon?: string; sort_order: number;
  description?: string; children?: PermissionItem[]
}

export function listRolesApi(): Promise<RoleItem[]> {
  return request.get('/admin/roles')
}

export function createRoleApi(data: { name: string; code: string; description?: string; permission_ids: number[] }): Promise<RoleItem> {
  return request.post('/admin/roles', data)
}

export function updateRoleApi(id: number, data: Record<string, any>): Promise<RoleItem> {
  return request.put(`/admin/roles/${id}`, data)
}

export function deleteRoleApi(id: number): Promise<void> {
  return request.delete(`/admin/roles/${id}`)
}

export function getPermissionTreeApi(): Promise<PermissionItem[]> {
  return request.get('/admin/roles/permissions/tree')
}

// ========== 全局词库管理 ==========
export interface GlobalWordItem {
  id: number
  word: string
  type: string         // sensitive / banned / whitelist / correction
  replacement?: string // correction 类型的替换词
  category?: string
  severity: string
  remark?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface GlobalWordStats {
  total: number
  sensitive_count: number
  banned_count: number
  whitelist_count: number
  correction_count: number
}

export function getGlobalWordStatsApi(): Promise<GlobalWordStats> {
  return request.get('/admin/global-dict/stats')
}

export function listGlobalWordsApi(params?: {
  type?: string; keyword?: string; page?: number; page_size?: number
}): Promise<GlobalWordItem[]> {
  return request.get('/admin/global-dict', { params })
}

export function createGlobalWordApi(data: {
  word: string; type: string; replacement?: string; category?: string; severity?: string; remark?: string
}): Promise<GlobalWordItem> {
  return request.post('/admin/global-dict', data)
}

export function batchCreateGlobalWordsApi(data: {
  entries: Array<{ word: string; type: string; replacement?: string; category?: string; severity?: string; remark?: string }>
}): Promise<{ added: number; skipped: number }> {
  return request.post('/admin/global-dict/batch', data)
}

export function updateGlobalWordApi(id: number, data: Record<string, any>): Promise<GlobalWordItem> {
  return request.put(`/admin/global-dict/${id}`, data)
}

export function deleteGlobalWordApi(id: number): Promise<void> {
  return request.delete(`/admin/global-dict/${id}`)
}

// ========== 大模型配置管理 ==========
export interface LLMConfigItem {
  id: number
  name: string
  provider: string
  api_base: string
  api_key: string
  api_key_masked: string
  model: string
  temperature: number
  max_tokens?: number
  timeout: number
  max_retries: number
  is_active: boolean
  is_enabled: boolean
  remark?: string
  created_at?: string
  updated_at?: string
}

export interface LLMProviderOption {
  code: string
  name: string
  default_base: string
  default_model: string
}

export interface LLMTestResult {
  success: boolean
  model: string
  message: string
  usage: Record<string, number>
}

export function listLLMProvidersApi(): Promise<LLMProviderOption[]> {
  return request.get('/admin/llm-config/providers')
}

export function listLLMConfigsApi(): Promise<LLMConfigItem[]> {
  return request.get('/admin/llm-config')
}

export function createLLMConfigApi(data: {
  name: string; provider: string; api_base: string; api_key: string; model: string;
  temperature?: number; max_tokens?: number; timeout?: number; max_retries?: number; remark?: string
}): Promise<LLMConfigItem> {
  return request.post('/admin/llm-config', data)
}

export function updateLLMConfigApi(id: number, data: Record<string, any>): Promise<LLMConfigItem> {
  return request.put(`/admin/llm-config/${id}`, data)
}

export function deleteLLMConfigApi(id: number): Promise<void> {
  return request.delete(`/admin/llm-config/${id}`)
}

export function activateLLMConfigApi(id: number): Promise<LLMConfigItem> {
  return request.post(`/admin/llm-config/${id}/activate`)
}

export function testLLMConfigApi(id: number): Promise<LLMTestResult> {
  return request.post(`/admin/llm-config/${id}/test`)
}

export function getActiveLLMConfigApi(): Promise<LLMConfigItem> {
  return request.get('/admin/llm-config/active')
}

// ========== 文档管理 ==========
export interface AdminDocumentItem {
  id: number
  file_id: string
  filename: string
  file_ext: string
  file_size: number
  text_length: number
  username: string
  status: string
  download_url: string
  created_at?: string
}

export function listDocumentsApi(params?: {
  page?: number; page_size?: number; keyword?: string; file_ext?: string
}): Promise<{ items: AdminDocumentItem[]; total: number; page: number; page_size: number }> {
  return request.get('/admin/documents', { params })
}

export function deleteDocumentApi(id: number): Promise<void> {
  return request.delete(`/admin/documents/${id}`)
}

// ========== 策略管理 ==========
export interface GuestPolicyConfig {
  daily_limit: number
  max_text_length: number
  allow_upload: boolean
}

export interface UserPolicyConfig {
  daily_limit: number
  max_text_length: number
  allow_upload: boolean
  allow_export: boolean
  allow_dictionary: boolean
}

export function getGuestPolicyApi(): Promise<GuestPolicyConfig> {
  return request.get('/admin/policy/guest')
}

export function updateGuestPolicyApi(data: GuestPolicyConfig): Promise<GuestPolicyConfig> {
  return request.put('/admin/policy/guest', data)
}

export function getUserPolicyApi(): Promise<UserPolicyConfig> {
  return request.get('/admin/policy/user')
}

export function updateUserPolicyApi(data: UserPolicyConfig): Promise<UserPolicyConfig> {
  return request.put('/admin/policy/user', data)
}

// ========== 系统配置 ==========
export interface BasicSettingsConfig {
  version: string
  debug: boolean
  allow_register: boolean
  maintenance_mode: boolean
}

export interface FeishuSettingsConfig {
  enabled: boolean
  app_id: string
  app_secret: string
  redirect_uri: string
}

export interface SecuritySettingsConfig {
  default_password: string
}

export interface MaintenanceResult {
  success: boolean
  message: string
  deleted_count?: number
}

export function getBasicSettingsApi(): Promise<BasicSettingsConfig> {
  return request.get('/admin/system-config/basic')
}

export function updateBasicSettingsApi(data: BasicSettingsConfig): Promise<BasicSettingsConfig> {
  return request.put('/admin/system-config/basic', data)
}

export function getFeishuSettingsApi(): Promise<FeishuSettingsConfig> {
  return request.get('/admin/system-config/feishu')
}

export function updateFeishuSettingsApi(data: FeishuSettingsConfig): Promise<FeishuSettingsConfig> {
  return request.put('/admin/system-config/feishu', data)
}

export function getSecuritySettingsApi(): Promise<SecuritySettingsConfig> {
  return request.get('/admin/system-config/security')
}

export function updateSecuritySettingsApi(data: SecuritySettingsConfig): Promise<SecuritySettingsConfig> {
  return request.put('/admin/system-config/security', data)
}

export function cleanLogsApi(days?: number): Promise<MaintenanceResult> {
  return request.post('/admin/system-config/maintenance/clean-logs', null, { params: { days } })
}

export function cleanTempFilesApi(): Promise<MaintenanceResult> {
  return request.post('/admin/system-config/maintenance/clean-temp')
}

export function cleanCacheApi(): Promise<MaintenanceResult> {
  return request.post('/admin/system-config/maintenance/clean-cache')
}

export function cleanExpiredWhitelistApi(): Promise<MaintenanceResult> {
  return request.post('/admin/system-config/maintenance/clean-expired-whitelist')
}
