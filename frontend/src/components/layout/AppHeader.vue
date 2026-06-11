<!-- frontend/src/components/layout/AppHeader.vue — 顶部导航栏 -->
<template>
  <header class="h-16 bg-[var(--bg-surface)] border-b border-[var(--border-light)] flex items-center justify-between px-6 shrink-0 shadow-sm z-20">
    <!-- 左侧：Logo + 面包屑 -->
    <div class="flex items-center gap-4">
      <router-link to="/home" class="flex items-center gap-2 no-underline">
        <span class="text-2xl">📚</span>
        <span class="text-lg font-bold text-[var(--text-primary)] hidden sm:inline">
          EduAgent
        </span>
      </router-link>

      <!-- 面包屑 -->
      <nav v-if="breadcrumbs.length > 0" class="hidden md:flex items-center gap-1 text-sm text-[var(--text-secondary)]">
        <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
          <span v-if="idx > 0" class="text-[var(--text-muted)] mx-1">/</span>
          <router-link
            v-if="crumb.to"
            :to="crumb.to"
            class="hover:text-[var(--color-primary-500)] transition-colors"
          >
            {{ crumb.label }}
          </router-link>
          <span v-else class="text-[var(--text-primary)] font-medium">{{ crumb.label }}</span>
        </template>
      </nav>
    </div>

    <!-- 右侧：通知 + 用户下拉 -->
    <div class="flex items-center gap-3">
      <!-- 通知图标 -->
      <button class="relative p-2 rounded-full hover:bg-[var(--bg-surface-alt)] transition-colors" title="通知">
        <Bell class="w-5 h-5 text-[var(--text-secondary)]" />
        <span v-if="hasNotifications" class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
      </button>

      <!-- 用户下拉 -->
      <div class="relative" ref="userMenuRef">
        <button
          @click="showUserMenu = !showUserMenu"
          class="flex items-center gap-2 p-2 rounded-lg hover:bg-[var(--bg-surface-alt)] transition-colors"
        >
          <div class="w-8 h-8 rounded-full bg-[var(--color-primary-500)] flex items-center justify-center text-white text-sm font-medium">
            {{ userInitial }}
          </div>
          <span class="text-sm text-[var(--text-secondary)] hidden sm:inline">
            {{ userName }}
          </span>
          <ChevronDown class="w-4 h-4 text-[var(--text-muted)] hidden sm:block" />
        </button>

        <!-- 下拉菜单 -->
        <transition name="fade">
          <div
            v-if="showUserMenu"
            class="absolute right-0 top-full mt-1 w-48 bg-[var(--bg-surface)] border border-[var(--border-light)] rounded-lg shadow-lg py-1 z-50"
            @click="showUserMenu = false"
          >
            <router-link to="/profile" class="block px-4 py-2 text-sm hover:bg-[var(--bg-surface-alt)] transition-colors">
              👤 个人中心
            </router-link>
            <router-link
              v-if="authStore.isAdmin"
              to="/admin/users"
              class="block px-4 py-2 text-sm hover:bg-[var(--bg-surface-alt)] transition-colors"
            >
              ⚙️ 管理后台
            </router-link>
            <div class="border-t border-[var(--border-light)] my-1"></div>
            <button
              @click="handleLogout"
              class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-[var(--bg-surface-alt)] transition-colors"
            >
              🚪 退出登录
            </button>
          </div>
        </transition>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, ChevronDown } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useCourseStore } from '@/stores/course'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const courseStore = useCourseStore()

const showUserMenu = ref(false)
const hasNotifications = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)

const userInitial = computed(() => {
  const name = authStore.user?.display_name || authStore.user?.username || 'U'
  return name.charAt(0).toUpperCase()
})
const userName = computed(() => authStore.user?.display_name || authStore.user?.username || '用户')

const breadcrumbs = computed(() => {
  const crumbs: { label: string; to?: string }[] = []
  const path = route.path

  if (path.startsWith('/home')) {
    crumbs.push({ label: '首页' })
  } else if (path.startsWith('/courses')) {
    crumbs.push({ label: '课程列表', to: '/courses' })
    if (route.params.courseId) {
      const courseName = courseStore.currentCourseName || route.params.courseId
      crumbs.push({ label: String(courseName), to: `/courses/${route.params.courseId}` })
    }
  } else if (path.startsWith('/profile')) {
    crumbs.push({ label: '个人中心' })
  } else if (path.startsWith('/admin')) {
    crumbs.push({ label: '管理后台' })
  }

  return crumbs
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

function handleClickOutside(e: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    showUserMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 150ms ease-out;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
