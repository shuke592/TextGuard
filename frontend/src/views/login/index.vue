<template>
  <div class="login-page">
    <!-- 左侧品牌区（PC端显示） -->
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-logo">
          <img
            v-if="siteStore.hasCustomFavicon"
            :src="siteStore.faviconUrl"
            class="logo-icon logo-img"
            alt="平台图标"
          />
          <svg v-else viewBox="0 0 24 24" fill="currentColor" class="logo-icon">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
          </svg>
        </div>
        <h1 class="brand-title">{{ siteStore.platformName }}</h1>
        <p class="brand-subtitle">{{ siteStore.platformSubtitle }}</p>
        <div class="brand-features">
          <div class="feature-item">
            <span class="feature-dot"></span>
            <span>AI智能文本校对与润色</span>
          </div>
          <div class="feature-item">
            <span class="feature-dot"></span>
            <span>多领域专业化审校能力</span>
          </div>
          <div class="feature-item">
            <span class="feature-dot"></span>
            <span>企业级安全与权限管控</span>
          </div>
        </div>
      </div>
      <div class="brand-footer">
        <span>&copy; {{ new Date().getFullYear() }} {{ siteStore.platformName }}</span>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-panel">
      <div class="login-card">
        <!-- 移动端Logo -->
        <div class="mobile-logo">
          <img
            v-if="siteStore.hasCustomFavicon"
            :src="siteStore.faviconUrl"
            class="logo-icon-sm logo-img-sm"
            alt="平台图标"
          />
          <svg v-else viewBox="0 0 24 24" fill="currentColor" class="logo-icon-sm">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
          </svg>
          <span class="mobile-title">{{ siteStore.platformName }}</span>
        </div>

        <h2 class="login-title">欢迎登录</h2>
        <p class="login-desc">请选择登录方式进入系统</p>

        <!-- 登录方式Tab -->
        <div class="login-tabs">
          <div
            class="tab-item"
            :class="{ active: activeTab === 'account' }"
            @click="activeTab = 'account'"
          >
            <el-icon><User /></el-icon>
            <span>账号登录</span>
          </div>
          <div
            v-if="feishuConfig.enabled"
            class="tab-item"
            :class="{ active: activeTab === 'feishu' }"
            @click="activeTab = 'feishu'"
          >
            <el-icon><Connection /></el-icon>
            <span>飞书登录</span>
          </div>
        </div>

        <!-- 账号密码登录 -->
        <div v-show="activeTab === 'account'" class="login-form-wrapper">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="employee_id">
              <el-input
                v-model="loginForm.employee_id"
                placeholder="请输入工号"
                size="large"
                clearable
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleLogin"
              >
                登 录
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 飞书扫码登录 -->
        <div v-show="activeTab === 'feishu'" class="feishu-login-wrapper">
          <div v-if="feishuConfig.enabled" class="feishu-qrcode-area">
            <div class="feishu-icon-wrapper">
              <svg viewBox="0 0 48 48" class="feishu-logo">
                <rect width="48" height="48" rx="10" fill="#3370FF"/>
                <path d="M14 14h8v8h-8z M26 14h8v8h-8z M14 26h8v8h-8z M26 26h8v4a4 4 0 01-4 4h-4v-8z" fill="white" opacity="0.95"/>
              </svg>
            </div>
            <p class="feishu-main-tip">使用飞书账号快速登录</p>
            <p class="feishu-sub-tip">点击下方按钮跳转到飞书进行授权</p>
            <el-button
              type="primary"
              size="large"
              class="feishu-login-btn"
              :loading="feishuLoading"
              @click="handleFeishuLogin"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" style="width:18px;height:18px;margin-right:8px;">
                <rect width="20" height="20" rx="4" fill="currentColor" opacity="0.15"/>
                <path d="M5 5h4v4H5z M11 5h4v4h-4z M5 11h4v4H5z M11 11h4v2a2 2 0 01-2 2h-2v-4z" fill="currentColor"/>
              </svg>
              飞书授权登录
            </el-button>
          </div>
          <div v-else class="feishu-disabled">
            <el-icon :size="48" color="#ccc"><WarningFilled /></el-icon>
            <p>飞书登录功能暂未启用</p>
            <p class="feishu-disabled-sub">请联系管理员开启飞书对接配置</p>
          </div>
        </div>

        <!-- 底部 -->
        <div class="login-footer">
          <el-button text type="info" @click="router.push('/')">
            游客模式体验
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { User, Lock, Connection, WarningFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const siteStore = useSiteStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const feishuLoading = ref(false)
const activeTab = ref<'account' | 'feishu'>('account')

// 飞书配置
const feishuConfig = reactive({
  app_id: '',
  redirect_uri: '',
  enabled: false,
})

const loginForm = reactive({
  employee_id: '',
  password: '',
})

const loginRules = {
  employee_id: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 加载飞书配置
async function loadFeishuConfig() {
  try {
    const res: any = await request.get('/auth/feishu/config')
    feishuConfig.app_id = res.app_id
    feishuConfig.redirect_uri = res.redirect_uri
    feishuConfig.enabled = res.enabled
  } catch (e) {
    console.warn('飞书配置加载失败', e)
  }
}

// 跳转到飞书授权页面进行登录
function handleFeishuLogin() {
  if (!feishuConfig.enabled || !feishuConfig.app_id) {
    ElMessage.warning('飞书登录未配置，请联系管理员')
    return
  }
  feishuLoading.value = true
  // 飞书官方OAuth2.0授权地址（最新版：域名accounts.feishu.cn，参数client_id，必须带response_type=code）
  const feishuAuthUrl = `https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id=${feishuConfig.app_id}&redirect_uri=${encodeURIComponent(feishuConfig.redirect_uri)}&response_type=code&state=feishu_login`
  window.location.href = feishuAuthUrl
}

// 处理飞书回调（URL中带code参数时）
async function handleFeishuCallback() {
  const code = route.query.code as string
  const state = route.query.state as string

  // 处理SSO token直接传递的情况
  const feishuToken = route.query.feishu_token as string
  const feishuRefresh = route.query.feishu_refresh as string

  if (feishuToken && feishuRefresh) {
    // SSO方式：直接使用token
    localStorage.setItem('access_token', feishuToken)
    localStorage.setItem('refresh_token', feishuRefresh)
    userStore.token = feishuToken
    await userStore.fetchUserInfo()
    ElMessage.success('飞书登录成功')
    router.replace('/polish')
    return
  }

  if (code) {
    // 飞书授权回调：用code换token
    loading.value = true
    try {
      const res: any = await request.post('/auth/feishu/callback', { code })
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
      userStore.token = res.access_token
      await userStore.fetchUserInfo()
      ElMessage.success(res.is_new_user ? '首次登录，已自动创建账号' : '飞书登录成功')
      router.replace('/polish')
    } catch (e: any) {
      // 错误已在 axios 拦截器中统一处理和提示
      console.error('[飞书callback失败]', e?.response?.data || e)
    } finally {
      loading.value = false
    }
    return
  }

  // 处理错误信息（来自SSO重定向或飞书拒绝授权）
  const error = route.query.error as string
  if (error) {
    const errorMap: Record<string, string> = {
      access_denied: '您已拒绝授权，请重新登录',
      feishu_disabled: '飞书登录功能未启用',
      feishu_auth_failed: '飞书授权失败，请重试',
      account_disabled: '账号已被停用，请联系管理员',
      system_error: '系统异常，请联系管理员',
    }
    ElMessage.error(errorMap[error] || '登录失败')
  }
}

// 账号密码登录
async function handleLogin() {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(loginForm.employee_id, loginForm.password)
      ElMessage.success('登录成功')
      const redirect = (route.query.redirect as string) || '/polish'
      router.push(redirect)
    } catch (e: any) {
      // 错误已在 axios 拦截器中处理
    } finally {
      loading.value = false
    }
  })
}

onMounted(async () => {
  await loadFeishuConfig()
  // 检查URL中是否有飞书回调参数
  await handleFeishuCallback()
})
</script>

<style scoped lang="scss">
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  overflow: hidden;
  background: #f7f8fa;
}

/* 左侧品牌区 */
.login-brand {
  flex: 0 0 480px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(180deg, #1a365d 0%, #1e40af 50%, #1a365d 100%);
  color: #fff;
  padding: 60px 40px;
  position: relative;
}

.brand-content {
  text-align: center;
}

.brand-logo {
  margin-bottom: 24px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  color: #fff;
  filter: drop-shadow(0 4px 12px rgba(255, 255, 255, 0.3));
}

.logo-img {
  object-fit: contain;
  background: #fff;
  padding: 8px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: 2px;
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.85;
  margin-bottom: 48px;
}

.brand-features {
  text-align: left;
  display: inline-block;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 15px;
  opacity: 0.9;
}

.feature-dot {
  width: 8px;
  height: 8px;
  background: #60a5fa;
  border-radius: 50%;
  flex-shrink: 0;
}

.brand-footer {
  position: absolute;
  bottom: 32px;
  font-size: 13px;
  opacity: 0.6;
}

/* 右侧登录区 */
.login-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
}

.mobile-logo {
  display: none;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
}

.logo-icon-sm {
  width: 28px;
  height: 28px;
  color: #1e40af;
}

.logo-img-sm {
  object-fit: contain;
  border-radius: 6px;
}

.mobile-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e40af;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 8px;
}

.login-desc {
  font-size: 14px;
  color: #718096;
  margin-bottom: 32px;
}

/* 登录方式Tab */
.login-tabs {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 28px;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 0;
  cursor: pointer;
  font-size: 14px;
  color: #718096;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;

  &:hover {
    color: #1e40af;
  }

  &.active {
    color: #1e40af;
    border-bottom-color: #1e40af;
    font-weight: 500;
  }
}

/* 账号密码表单 */
.login-form-wrapper {
  min-height: 200px;
}

.login-form {
  .el-input {
    --el-input-border-radius: 8px;
  }

  .login-btn {
    width: 100%;
    height: 44px;
    font-size: 16px;
    border-radius: 8px;
    background: #1e40af;
    border-color: #1e40af;
    margin-top: 8px;

    &:hover {
      background: #1d4ed8;
      border-color: #1d4ed8;
    }
  }
}

/* 飞书登录 */
.feishu-login-wrapper {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.feishu-qrcode-area {
  text-align: center;
  padding: 20px 0;
}

.feishu-icon-wrapper {
  margin-bottom: 20px;
}

.feishu-logo {
  width: 56px;
  height: 56px;
}

.feishu-main-tip {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.feishu-sub-tip {
  font-size: 13px;
  color: #999;
  margin-bottom: 28px;
}

.feishu-login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  border-radius: 8px;
  background: #3370FF;
  border-color: #3370FF;

  &:hover {
    background: #2860E0;
    border-color: #2860E0;
  }
}

.feishu-disabled {
  text-align: center;
  padding: 40px 0;

  p {
    margin-top: 12px;
    color: #999;
    font-size: 14px;
  }

  .feishu-disabled-sub {
    font-size: 12px;
    color: #bbb;
  }
}

/* 底部 */
.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* ===== 移动端适配 ===== */
@media (max-width: 960px) {
  .login-brand {
    display: none;
  }

  .login-page {
    background: #fff;
  }

  .login-panel {
    padding: 24px 16px;
  }

  .login-card {
    padding: 32px 24px;
    box-shadow: none;
    border-radius: 0;
  }

  .mobile-logo {
    display: flex;
  }

  .login-title {
    text-align: center;
  }

  .login-desc {
    text-align: center;
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 24px 16px;
  }

  .login-title {
    font-size: 20px;
  }

  .tab-item {
    font-size: 13px;
  }
}
</style>
