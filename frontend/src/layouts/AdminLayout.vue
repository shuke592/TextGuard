<template>
  <el-container class="admin-layout">
    <!-- 左侧菜单 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="admin-aside">
      <div class="aside-header">
        <span v-if="!isCollapse" class="aside-title">{{ siteStore.platformName }} 管理</span>
        <span v-else class="aside-title-short">{{ siteStore.platformName.charAt(0) }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="admin-menu"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/roles">
          <el-icon><Lock /></el-icon>
          <template #title>角色权限</template>
        </el-menu-item>
        <el-menu-item index="/admin/policy">
          <el-icon><Setting /></el-icon>
          <template #title>策略管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/llm">
          <el-icon><Cpu /></el-icon>
          <template #title>大模型配置</template>
        </el-menu-item>
        <el-menu-item index="/admin/global-dict">
          <el-icon><Notebook /></el-icon>
          <template #title>全局词库</template>
        </el-menu-item>
        <el-menu-item index="/admin/documents">
          <el-icon><Folder /></el-icon>
          <template #title>文档管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/audit">
          <el-icon><List /></el-icon>
          <template #title>日志审查</template>
        </el-menu-item>
        <el-menu-item index="/admin/settings">
          <el-icon><Tools /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧内容区 -->
    <el-container class="admin-content-wrapper">
      <!-- 顶部栏 -->
      <el-header class="admin-header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
          >
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-button text @click="router.push('/')">
            <el-icon><Back /></el-icon>返回用户端
          </el-button>
          <el-dropdown trigger="click">
            <div class="user-info">
              <el-avatar :size="28" :src="userStore.userInfo?.avatar">
                {{ userStore.userInfo?.username?.charAt(0) }}
              </el-avatar>
              <span class="user-name">{{ userStore.userInfo?.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const siteStore = useSiteStore()

const isCollapse = ref(false)
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) isCollapse.value = true
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
const activeMenu = computed(() => route.path)

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped lang="scss">
.admin-layout {
  height: 100vh;
}

.admin-aside {
  background: #1d2b3a;
  transition: width 0.3s;
  overflow-x: hidden;
  overflow-y: auto;

  .aside-header {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .aside-title {
      color: #fff;
      font-size: 16px;
      font-weight: 600;
    }

    .aside-title-short {
      color: #fff;
      font-size: 18px;
      font-weight: 700;
    }
  }

  .admin-menu {
    border-right: none;
    background: transparent;

    :deep(.el-menu-item) {
      color: rgba(255, 255, 255, 0.75);

      &:hover {
        background: rgba(255, 255, 255, 0.08);
        color: #fff;
      }

      &.is-active {
        background: var(--color-primary);
        color: #fff;
      }
    }
  }
}

.admin-content-wrapper {
  display: flex;
  flex-direction: column;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  height: 60px;
  padding: 0 var(--spacing-lg);

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);

    .collapse-btn {
      font-size: 20px;
      cursor: pointer;
      color: var(--color-text);
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);

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

.admin-main {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  background: var(--color-bg);
}

/* ===== 移动端响应式 ===== */
@media (max-width: 768px) {
  .admin-aside {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 200;
    height: 100vh;
  }

  .admin-header {
    padding: 0 12px;
  }

  .admin-main {
    padding: 12px;
  }
}
</style>
