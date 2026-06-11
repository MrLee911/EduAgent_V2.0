// frontend/src/router/index.ts — Vue Router 配置 + 4 级导航守卫
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  // ── 公开路由 ──
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true },
  },

  // ── 需认证路由 ──
  {
    path: '/home',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/courses',
    name: 'Courses',
    component: () => import('@/views/CoursesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/courses/:courseId',
    name: 'CourseDetail',
    component: () => import('@/views/CourseDetailView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: () => {
          // 默认重定向到资源页
          return { name: 'CourseResources' }
        },
      },
      {
        path: 'resources',
        name: 'CourseResources',
        component: () => import('@/views/CourseResourcesView.vue'),
      },
      {
        path: 'qa',
        name: 'CourseQA',
        component: () => import('@/views/CourseQAView.vue'),
      },
      {
        path: 'tasks',
        name: 'CourseTasks',
        component: () => import('@/views/CourseTasksView.vue'),
      },
      {
        path: 'reports',
        name: 'CourseReports',
        component: () => import('@/views/CourseReportsView.vue'),
        meta: { roles: ['teacher', 'admin'] },
      },
      {
        path: 'settings',
        name: 'CourseSettings',
        component: () => import('@/views/CourseSettingsView.vue'),
        meta: { roles: ['teacher', 'admin'] },
      },
    ],
  },
  {
    path: '/courses/:courseId/tasks/:taskId',
    name: 'TaskDetail',
    component: () => import('@/views/CourseDetailView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/TaskDetailView.vue'),
      },
    ],
  },
  {
    path: '/courses/:courseId/reports/:reportId',
    name: 'ReportDetail',
    component: () => import('@/views/CourseDetailView.vue'),
    meta: { requiresAuth: true, roles: ['teacher', 'admin'] },
    children: [
      {
        path: '',
        component: () => import('@/views/ReportDetailView.vue'),
      },
    ],
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },

  // ── 管理员路由 ──
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/admin/AdminUsersView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('@/views/admin/AdminSettingsView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },

  // ── 404 ──
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },

  // ── 默认重定向 ──
  {
    path: '/',
    redirect: '/home',
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// ── 4 级导航守卫：guest → requiresAuth → roles → fetchMe ──
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 1. 已登录用户访问 guest 页面 → 跳转到 home
  if (to.meta.guest && authStore.isLoggedIn) {
    return next('/home')
  }

  // 2. 需认证页面 → 检查是否登录
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    // 尝试用 localStorage 中的 token 恢复会话
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        await authStore.fetchMe()
        if (!authStore.isLoggedIn) {
          return next(`/login?redirect=${to.fullPath}`)
        }
      } catch {
        return next(`/login?redirect=${to.fullPath}`)
      }
    } else {
      return next(`/login?redirect=${to.fullPath}`)
    }
  }

  // 3. 角色检查
  if (to.meta.roles && Array.isArray(to.meta.roles)) {
    const userRole = authStore.user?.role
    if (!userRole || !(to.meta.roles as string[]).includes(userRole)) {
      return next('/home')
    }
  }

  next()
})

export default router
