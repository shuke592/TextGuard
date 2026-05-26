/**
 * TextGuard 前端路由配置
 * 包含用户端和管理端两套布局
 */
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

// 静态路由（无需权限）
const staticRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', hidden: true },
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: { title: '无权限', hidden: true },
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面不存在', hidden: true },
  },
]

// 用户端路由
const userRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/UserLayout.vue'),
    redirect: '/polish',
    children: [
      {
        path: 'polish',
        name: 'AIPolish',
        component: () => import('@/views/user/polish/index.vue'),
        meta: { title: 'AI润色', icon: 'MagicStick' },
      },
      {
        path: 'proofread/text',
        name: 'TextProofread',
        component: () => import('@/views/user/proofread/TextProofread.vue'),
        meta: { title: '文本校对', icon: 'Edit' },
      },
      {
        path: 'proofread/document',
        name: 'DocumentProofread',
        component: () => import('@/views/user/proofread/DocumentProofread.vue'),
        meta: { title: '文档校对', icon: 'Document' },
      },
      {
        path: 'dictionary',
        name: 'Dictionary',
        component: () => import('@/views/user/dictionary/index.vue'),
        meta: { title: '个性化词库', icon: 'Collection', requireAuth: true },
      },
      {
        path: 'whitelist',
        name: 'Whitelist',
        component: () => import('@/views/user/whitelist/index.vue'),
        meta: { title: '放行词管理', icon: 'CircleCheck', requireAuth: true },
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/user/history/index.vue'),
        meta: { title: '校对历史', icon: 'Clock', requireAuth: true },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/user/profile/index.vue'),
        meta: { title: '个人中心', icon: 'User', requireAuth: true },
      },
    ],
  },
]

// 管理端路由
const adminRoutes: RouteRecordRaw[] = [
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: { title: '管理后台', requireAuth: true, requireAdmin: true },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'DataAnalysis' },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/users/index.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
      {
        path: 'roles',
        name: 'AdminRoles',
        component: () => import('@/views/admin/roles/index.vue'),
        meta: { title: '角色权限', icon: 'Lock' },
      },
      {
        path: 'policy',
        name: 'AdminPolicy',
        component: () => import('@/views/admin/policy/index.vue'),
        meta: { title: '策略管理', icon: 'Setting' },
      },
      {
        path: 'llm',
        name: 'AdminLLM',
        component: () => import('@/views/admin/llm/index.vue'),
        meta: { title: '大模型配置', icon: 'Cpu' },
      },
      {
        path: 'global-dict',
        name: 'AdminGlobalDict',
        component: () => import('@/views/admin/global-dict/index.vue'),
        meta: { title: '全局词库', icon: 'Notebook' },
      },
      {
        path: 'documents',
        name: 'AdminDocuments',
        component: () => import('@/views/admin/documents/index.vue'),
        meta: { title: '文档管理', icon: 'Folder' },
      },
      {
        path: 'audit',
        name: 'AdminAudit',
        component: () => import('@/views/admin/audit/index.vue'),
        meta: { title: '日志审查', icon: 'Document' },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/settings/index.vue'),
        meta: { title: '系统设置', icon: 'Tools' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes: [...staticRoutes, ...userRoutes, ...adminRoutes],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  // 动态设置页面标题（站点配置在 main.ts 中加载到 DOM title 上，此处做路由级覆盖）
  import('@/stores/site').then(({ useSiteStore }) => {
    try {
      const siteStore = useSiteStore()
      siteStore.updateDocumentTitle(to.meta.title as string || '')
    } catch { /* pinia 未就绪时忽略 */ }
  })

  const token = localStorage.getItem('access_token')

  // 需要登录的页面
  if (to.meta.requireAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 已登录不允许访问登录页（除非有飞书回调参数）
  if (to.name === 'Login' && token) {
    const hasFeishuParams = to.query.code || to.query.feishu_token
    if (!hasFeishuParams) {
      next({ path: '/' })
      return
    }
  }

  next()
})

export default router
