/**
 * TextGuard 站点配置 API
 */
import request from '@/utils/request'

export interface SiteConfig {
  platform_name: string
  platform_subtitle: string
  favicon_url: string
}

/** 获取站点公开配置（无需登录） */
export function getSiteInfoApi(): Promise<SiteConfig> {
  return request.get('/site/info')
}

/** 管理员获取站点配置 */
export function getAdminSiteConfigApi(): Promise<SiteConfig> {
  return request.get('/admin/settings/site')
}

/** 管理员更新站点配置 */
export function updateAdminSiteConfigApi(data: Partial<SiteConfig>): Promise<SiteConfig> {
  return request.put('/admin/settings/site', data)
}

/** 管理员上传图标文件 */
export function uploadIconApi(file: File): Promise<{ url: string; filename: string }> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/admin/settings/upload-icon', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
