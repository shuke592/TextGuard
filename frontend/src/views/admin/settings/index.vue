<template>
  <div class="admin-settings">
    <!-- 平台品牌设置 -->
    <el-card>
      <template #header><span style="font-weight: 600;">平台品牌设置</span></template>
      <el-form label-width="160px" style="max-width: 680px;" :model="siteConfig">
        <el-form-item label="平台名称">
          <el-input v-model="siteConfig.platform_name" placeholder="请输入平台名称" maxlength="20" show-word-limit />
          <div class="form-tip">显示在导航栏、浏览器页签及各页面标题中</div>
        </el-form-item>
        <el-form-item label="平台副标题">
          <el-input v-model="siteConfig.platform_subtitle" placeholder="请输入平台副标题" maxlength="30" show-word-limit />
          <div class="form-tip">显示在导航栏平台名称右侧、浏览器页签中</div>
        </el-form-item>
        <el-form-item label="浏览器图标">
          <div class="favicon-config">
            <div class="favicon-preview">
              <img :src="siteConfig.favicon_url" alt="favicon" class="favicon-img" />
            </div>
            <div class="favicon-options">
              <!-- 本地上传 -->
              <div class="upload-row">
                <el-upload
                  :show-file-list="false"
                  :before-upload="handleIconUpload"
                  accept=".png,.jpg,.jpeg,.svg,.ico,.webp,.gif"
                  class="icon-upload"
                >
                  <el-button size="small" type="primary">
                    <el-icon><Upload /></el-icon>上传本地图标
                  </el-button>
                </el-upload>
                <span class="upload-tip">支持 PNG/JPG/SVG/ICO，不超过 500KB，建议 32x32 或 64x64</span>
              </div>
              <!-- 预设图标 -->
              <div class="favicon-presets">
                <span class="preset-label">或选择预设：</span>
                <div
                  v-for="icon in faviconPresets"
                  :key="icon.url"
                  class="preset-item"
                  :class="{ 'is-active': siteConfig.favicon_url === icon.url }"
                  @click="siteConfig.favicon_url = icon.url"
                  :title="icon.name"
                >
                  <img :src="icon.url" :alt="icon.name" />
                </div>
              </div>
            </div>
          </div>
          <div class="form-tip">上传后可在左侧预览效果，点击“保存品牌设置”后生效</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveSiteConfig">
            保存品牌设置
          </el-button>
          <el-button @click="resetSiteConfig">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 系统基本设置 -->
    <el-card style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">系统基本设置</span></template>
      <el-form label-width="160px" style="max-width: 600px;">
        <el-form-item label="版本号">
          <el-input v-model="settings.version" disabled />
        </el-form-item>
        <el-form-item label="调试模式">
          <el-switch v-model="settings.debug" />
        </el-form-item>
        <el-form-item label="允许注册">
          <el-switch v-model="settings.allow_register" />
        </el-form-item>
        <el-form-item label="维护模式">
          <el-switch v-model="settings.maintenance_mode" />
          <span style="font-size: 12px; color: #999; margin-left: 12px;">开启后仅管理员可访问</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveBasicSettings">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 飞书对接配置 -->
    <el-card style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">飞书对接配置</span></template>
      <el-form label-width="160px" style="max-width: 680px;" :model="feishuSettings">
        <el-form-item label="启用飞书登录">
          <el-switch v-model="feishuSettings.enabled" />
          <span style="font-size: 12px; color: #999; margin-left: 12px;">开启后登录页显示飞书扫码入口</span>
        </el-form-item>
        <el-form-item label="App ID">
          <el-input v-model="feishuSettings.app_id" placeholder="飞书自建应用的App ID" />
        </el-form-item>
        <el-form-item label="App Secret">
          <el-input v-model="feishuSettings.app_secret" type="password" show-password placeholder="飞书自建应用的App Secret" />
        </el-form-item>
        <el-form-item label="回调地址">
          <el-input v-model="feishuSettings.redirect_uri" placeholder="https://your-domain.com/login" />
          <div class="form-tip">飞书应用后台「安全设置」中配置的重定向URL，需与此一致</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveFeishuSettings">保存飞书配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户安全设置 -->
    <el-card style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">用户安全设置</span></template>
      <el-form label-width="160px" style="max-width: 600px;" :model="securitySettings">
        <el-form-item label="新用户初始密码">
          <el-input v-model="securitySettings.default_password" placeholder="admin123" />
          <div class="form-tip">飞书首次登录自动创建用户时使用此密码，管理员重置密码时也使用此值</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveSecuritySettings">保存安全设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据维护 -->
    <el-card style="margin-top: 16px;">
      <template #header><span style="font-weight: 600;">数据维护</span></template>
      <div style="display: flex; gap: 12px; flex-wrap: wrap;">
        <el-button @click="handleClean('logs')">清理日志</el-button>
        <el-button @click="handleClean('temp')">清理临时文件</el-button>
        <el-button @click="handleClean('cache')">清理缓存</el-button>
        <el-button type="danger" @click="handleClean('expired')">清理过期放行词</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadRawFile } from 'element-plus'
import {
  type BasicSettingsConfig, type FeishuSettingsConfig, type SecuritySettingsConfig,
  getBasicSettingsApi, updateBasicSettingsApi,
  getFeishuSettingsApi, updateFeishuSettingsApi,
  getSecuritySettingsApi, updateSecuritySettingsApi,
  cleanLogsApi, cleanTempFilesApi, cleanCacheApi, cleanExpiredWhitelistApi,
} from '@/api/admin'
import {
  type SiteConfig,
  getAdminSiteConfigApi, updateAdminSiteConfigApi, uploadIconApi,
} from '@/api/site'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()
const saving = ref(false)

// 预设图标（内嵌SVG，主题色 #0056b3，不依赖外部服务）
const faviconPresets = [
  {
    name: '盾牌校验',
    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230056b3'%3E%3Cpath d='M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z'/%3E%3C/svg%3E",
  },
  {
    name: '文档审校',
    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230056b3'%3E%3Cpath d='M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm-1 7V3.5L18.5 9H13zM9 13h6v2H9v-2zm6 4H9v2h6v-2zm-6-8h3v2H9V9z'/%3E%3C/svg%3E",
  },
  {
    name: '智能AI',
    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230056b3'%3E%3Cpath d='M21 10.5h-1V8c0-.55-.45-1-1-1h-2V5.5c0-.83-.67-1.5-1.5-1.5S14 4.67 14 5.5V7h-4V5.5C10 4.67 9.33 4 8.5 4S7 4.67 7 5.5V7H5c-.55 0-1 .45-1 1v2.5H3c-.83 0-1.5.67-1.5 1.5s.67 1.5 1.5 1.5h1V16c0 .55.45 1 1 1h2v1.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V17h4v1.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5V17h2c.55 0 1-.45 1-1v-2.5h1c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5zM9 14c-.83 0-1.5-.67-1.5-1.5S8.17 11 9 11s1.5.67 1.5 1.5S9.83 14 9 14zm6 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z'/%3E%3C/svg%3E",
  },
  {
    name: '笔尖编辑',
    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230056b3'%3E%3Cpath d='M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z'/%3E%3C/svg%3E",
  },
  {
    name: '校对勾选',
    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230056b3'%3E%3Cpath d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E",
  },
  {
    name: '品牌TG',
    url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230056b3'/%3E%3Ctext x='16' y='22' font-family='Arial,sans-serif' font-size='14' font-weight='bold' fill='white' text-anchor='middle'%3ETG%3C/text%3E%3C/svg%3E",
  },
]

// 站点品牌配置
const siteConfig = reactive<SiteConfig>({
  platform_name: 'TextGuard',
  platform_subtitle: '智能文档审校平台',
  favicon_url: faviconPresets[0].url,
})

// 原始值（用于重置）
let originalSiteConfig: SiteConfig = { ...siteConfig }

/** 上传图标文件 */
async function handleIconUpload(file: UploadRawFile) {
  if (file.size > 512 * 1024) {
    ElMessage.warning('图标文件不能超过 500KB')
    return false
  }
  try {
    const res = await uploadIconApi(file)
    siteConfig.favicon_url = res.url
    ElMessage.success('图标上传成功，请点击保存品牌设置生效')
  } catch {
    // 错误已在拦截器处理
  }
  return false // 阻止 el-upload 默认上传行为
}

// 基本设置
const settings = reactive<BasicSettingsConfig>({
  version: '1.0.0',
  debug: false,
  allow_register: false,
  maintenance_mode: false,
})

// 飞书对接设置
const feishuSettings = reactive<FeishuSettingsConfig>({
  enabled: false,
  app_id: '',
  app_secret: '',
  redirect_uri: '',
})

// 用户安全设置
const securitySettings = reactive<SecuritySettingsConfig>({
  default_password: 'admin123',
})

onMounted(async () => {
  try {
    const config = await getAdminSiteConfigApi()
    Object.assign(siteConfig, config)
    originalSiteConfig = { ...config }
  } catch {}
  
  try {
    const basic = await getBasicSettingsApi()
    Object.assign(settings, basic)
  } catch {}
  
  try {
    const feishu = await getFeishuSettingsApi()
    Object.assign(feishuSettings, feishu)
  } catch {}
  
  try {
    const security = await getSecuritySettingsApi()
    Object.assign(securitySettings, security)
  } catch {}
})

/** 保存品牌设置 */
async function saveSiteConfig() {
  if (!siteConfig.platform_name?.trim()) {
    ElMessage.warning('平台名称不能为空')
    return
  }
  saving.value = true
  try {
    const result = await updateAdminSiteConfigApi(siteConfig)
    siteStore.applyConfig(result)
    originalSiteConfig = { ...result }
    ElMessage.success('品牌设置已保存，全站已即时生效')
  } catch {
    // 错误已在拦截器处理
  } finally {
    saving.value = false
  }
}

/** 重置 */
function resetSiteConfig() {
  Object.assign(siteConfig, originalSiteConfig)
}

async function saveBasicSettings() {
  try {
    await updateBasicSettingsApi(settings)
    ElMessage.success('基本设置已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

/** 保存飞书配置 */
async function saveFeishuSettings() {
  try {
    await updateFeishuSettingsApi(feishuSettings)
    ElMessage.success('飞书配置已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

/** 保存安全设置 */
async function saveSecuritySettings() {
  try {
    await updateSecuritySettingsApi(securitySettings)
    ElMessage.success('用户安全设置已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function handleClean(type: string) {
  const labels: Record<string, string> = { logs: '日志', temp: '临时文件', cache: '缓存', expired: '过期放行词' }
  try {
    await ElMessageBox.confirm(`确定清理${labels[type]}？`, '确认操作', { type: 'warning' })
    let result
    if (type === 'logs') result = await cleanLogsApi(90)
    else if (type === 'temp') result = await cleanTempFilesApi()
    else if (type === 'cache') result = await cleanCacheApi()
    else if (type === 'expired') result = await cleanExpiredWhitelistApi()
    
    ElMessage.success(result?.message || `${labels[type]}清理完成`)
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('清理失败')
  }
}
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
  line-height: 1.4;
}

.favicon-config {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  width: 100%;
}

.favicon-preview {
  width: 48px;
  height: 48px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  flex-shrink: 0;

  .favicon-img {
    width: 32px;
    height: 32px;
    object-fit: contain;
  }
}

.favicon-options {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;

  .upload-tip {
    font-size: 12px;
    color: #9ca3af;
  }
}

.icon-upload {
  display: inline-block;
}

.favicon-presets {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;

  .preset-label {
    font-size: 13px;
    color: #6b7280;
    white-space: nowrap;
  }

  .preset-item {
    width: 36px;
    height: 36px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
    background: #fff;

    img {
      width: 24px;
      height: 24px;
    }

    &:hover {
      border-color: #93c5fd;
    }

    &.is-active {
      border-color: #0056b3;
      background: #eff6ff;
      box-shadow: 0 0 0 2px rgba(0, 86, 179, 0.1);
    }
  }
}
</style>
