<template>
  <el-container class="user-layout">
    <!-- 顶部导航栏 -->
    <el-header class="user-header">
      <div class="header-left">
        <!-- 移动端汉堡菜单按钮 -->
        <el-icon class="mobile-menu-btn" @click="mobileMenuVisible = true">
          <Operation />
        </el-icon>
        <div class="logo" @click="router.push('/')">
          <img :src="siteStore.faviconUrl" alt="" class="logo-icon" />
          <span class="logo-text">{{ siteStore.platformName }}</span>
          <span class="logo-sub">{{ siteStore.platformSubtitle }}</span>
        </div>
      </div>
      <!-- 桌面端导航菜单 -->
      <div class="header-nav desktop-only">
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          :ellipsis="false"
          router
        >
          <el-menu-item index="/polish">
            <el-icon><MagicStick /></el-icon>
            <span>AI润色</span>
          </el-menu-item>
          <el-menu-item index="/proofread/text">
            <el-icon><Edit /></el-icon>
            <span>文本校对</span>
          </el-menu-item>
          <el-menu-item index="/proofread/document">
            <el-icon><Document /></el-icon>
            <span>文档校对</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/dictionary">
            <el-icon><Collection /></el-icon>
            <span>个性化词库</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/whitelist">
            <el-icon><CircleCheck /></el-icon>
            <span>放行词管理</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isLoggedIn" index="/history">
            <el-icon><Clock /></el-icon>
            <span>校对历史</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="header-right">
        <template v-if="userStore.isLoggedIn">
          <el-dropdown trigger="click">
            <div class="user-info">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.userInfo?.username?.charAt(0) }}
              </el-avatar>
              <span class="user-name desktop-only">{{ userStore.userInfo?.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="userStore.isSuperAdmin || userStore.hasPermission('admin:access')"
                  @click="router.push('/admin')"
                >
                  <el-icon><Setting /></el-icon>管理后台
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click="router.push('/login')">登录</el-button>
        </template>
      </div>
    </el-header>

    <!-- 移动端侧边抽屉导航 -->
    <el-drawer
      v-model="mobileMenuVisible"
      direction="ltr"
      size="260px"
      :show-close="false"
      class="mobile-drawer"
    >
      <template #header>
        <div class="drawer-header">
          <span class="drawer-title">{{ siteStore.platformName }}</span>
        </div>
      </template>
      <el-menu
        :default-active="activeMenu"
        router
        @select="mobileMenuVisible = false"
        class="mobile-nav-menu"
      >
        <el-menu-item index="/polish">
          <el-icon><MagicStick /></el-icon>
          <span>AI润色</span>
        </el-menu-item>
        <el-menu-item index="/proofread/text">
          <el-icon><Edit /></el-icon>
          <span>文本校对</span>
        </el-menu-item>
        <el-menu-item index="/proofread/document">
          <el-icon><Document /></el-icon>
          <span>文档校对</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isLoggedIn" index="/dictionary">
          <el-icon><Collection /></el-icon>
          <span>个性化词库</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isLoggedIn" index="/whitelist">
          <el-icon><CircleCheck /></el-icon>
          <span>放行词管理</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isLoggedIn" index="/history">
          <el-icon><Clock /></el-icon>
          <span>校对历史</span>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <!-- 主内容区 -->
    <el-main class="user-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const siteStore = useSiteStore()

const activeMenu = computed(() => route.path)
const mobileMenuVisible = ref(false)

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.user-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.user-header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  padding: 0 var(--spacing-lg);
  height: 60px;
  z-index: 100;

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;

    .mobile-menu-btn {
      display: none;
      font-size: 22px;
      cursor: pointer;
      color: #333;
    }

    .logo {
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;

      .logo-icon {
        width: 28px;
        height: 28px;
        object-fit: contain;
        flex-shrink: 0;
      }

      .logo-text {
        font-size: 22px;
        font-weight: 700;
        color: var(--color-primary);
        white-space: nowrap;
      }

      .logo-sub {
        font-size: 12px;
        color: var(--color-text-secondary);
        white-space: nowrap;
      }
    }
  }

  .header-nav {
    flex: 1;
    margin-left: var(--spacing-xl);

    .el-menu {
      border-bottom: none;
      height: 60px;
    }
  }

  .header-right {
    margin-left: auto;

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;

      .user-name {
        font-size: 14px;
        color: var(--color-text);
      }
    }
  }
}

.user-main {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  background: var(--color-bg);
}

/* 移动端抽屉 */
.drawer-header {
  .drawer-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--color-primary);
  }
}

.mobile-nav-menu {
  border-right: none;
}

/* ===== 响应式 ===== */
.desktop-only {
  display: flex;
}

@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }

  .user-header {
    padding: 0 12px;

    .header-left .mobile-menu-btn {
      display: block;
    }

    .header-left .logo {
      .logo-sub {
        display: none;
      }
      .logo-text {
        font-size: 18px;
      }
      .logo-icon {
        width: 24px;
        height: 24px;
      }
    }
  }

  .user-main {
    padding: 12px;
  }
}
</style>
