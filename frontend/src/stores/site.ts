/**
 * TextGuard 站点配置状态管理
 * 管理平台名称、副标题、图标等全局配置
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSiteInfoApi, type SiteConfig } from '@/api/site'

// 默认图标（盾牌校验，主题色内嵌SVG）
const DEFAULT_FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%230056b3'%3E%3Cpath d='M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z'/%3E%3C/svg%3E"

export const useSiteStore = defineStore('site', () => {
  // 状态（带默认值）
  const platformName = ref('TextGuard')
  const platformSubtitle = ref('智能文档审校平台')
  const faviconUrl = ref(DEFAULT_FAVICON)
  const customFaviconSet = ref(false) // 是否管理员上传了自定义图标
  const loaded = ref(false)

  /** 是否使用自定义图标（用于登录页等需要按图标存在与否切换样式的场景） */
  const hasCustomFavicon = computed(() => customFaviconSet.value)

  /** 从后端加载站点配置 */
  async function loadSiteConfig() {
    try {
      const config: SiteConfig = await getSiteInfoApi()
      platformName.value = config.platform_name || 'TextGuard'
      platformSubtitle.value = config.platform_subtitle || '智能文档审校平台'
      customFaviconSet.value = !!config.favicon_url
      faviconUrl.value = config.favicon_url || DEFAULT_FAVICON
      loaded.value = true

      // 更新浏览器标题
      updateDocumentTitle()
      // 更新 favicon
      updateFavicon()
    } catch (e) {
      console.warn('[站点配置] 加载失败，使用默认值', e)
      loaded.value = true
    }
  }

  /** 更新配置（管理员保存后调用） */
  function applyConfig(config: SiteConfig) {
    platformName.value = config.platform_name || 'TextGuard'
    platformSubtitle.value = config.platform_subtitle || '智能文档审校平台'
    customFaviconSet.value = !!config.favicon_url
    faviconUrl.value = config.favicon_url || DEFAULT_FAVICON
    updateDocumentTitle()
    updateFavicon()
  }

  /** 更新页面标题 */
  function updateDocumentTitle(pageTitle?: string) {
    const base = `${platformName.value} - ${platformSubtitle.value}`
    document.title = pageTitle ? `${pageTitle} - ${platformName.value}` : base
  }

  /** 更新 favicon */
  function updateFavicon() {
    let link = document.querySelector("link[rel*='icon']") as HTMLLinkElement
    if (!link) {
      link = document.createElement('link')
      link.rel = 'icon'
      document.head.appendChild(link)
    }
    link.href = faviconUrl.value
  }

  return {
    platformName,
    platformSubtitle,
    faviconUrl,
    hasCustomFavicon,
    loaded,
    loadSiteConfig,
    applyConfig,
    updateDocumentTitle,
    updateFavicon,
  }
})
