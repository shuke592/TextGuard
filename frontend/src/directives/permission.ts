/**
 * TextGuard 按钮级权限指令
 * 用法：v-permission="'proofread:export'"
 * 当用户不具备指定权限时，移除对应 DOM 元素
 */
import { Directive, DirectiveBinding } from 'vue'
import { useUserStore } from '@/stores/user'

const permissionDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding<string>) {
    const permissionCode = binding.value
    if (!permissionCode) return

    const userStore = useUserStore()

    // 未登录用户隐藏需要权限的按钮
    if (!userStore.isLoggedIn) {
      el.parentNode?.removeChild(el)
      return
    }

    // 检查用户是否有该权限
    if (!userStore.hasPermission(permissionCode)) {
      el.parentNode?.removeChild(el)
    }
  },
  updated(el: HTMLElement, binding: DirectiveBinding<string>) {
    const permissionCode = binding.value
    if (!permissionCode) return

    const userStore = useUserStore()

    if (!userStore.isLoggedIn || !userStore.hasPermission(permissionCode)) {
      el.style.display = 'none'
    } else {
      el.style.display = ''
    }
  },
}

export default permissionDirective
