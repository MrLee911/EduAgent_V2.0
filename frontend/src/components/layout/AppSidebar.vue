<!-- frontend/src/components/layout/AppSidebar.vue — 侧边栏导航（课程子页面专用） -->
<template>
  <!-- 桌面端侧边栏 -->
  <aside class="hidden md:flex flex-col w-60 bg-[var(--bg-surface)] border-r border-[var(--border-light)] shrink-0 overflow-y-auto">
    <!-- 课程信息卡片 -->
    <div class="p-4 border-b border-[var(--border-light)]">
      <h3 class="font-semibold text-[var(--text-primary)] truncate" :title="courseName">
        {{ courseName || '加载中...' }}
      </h3>
      <p v-if="courseDescription" class="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">
        {{ courseDescription }}
      </p>
      <span v-if="courseSemester" class="inline-block mt-2 px-2 py-0.5 text-xs font-medium bg-[var(--color-primary-50)] text-[var(--color-primary-700)] rounded-full">
        {{ courseSemester }}
      </span>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 py-2">
      <template v-for="item in navItems" :key="item.key">
        <router-link
          v-if="item.show"
          :to="item.to"
          class="flex items-center gap-3 px-4 py-3 text-sm transition-colors"
          :class="isActive(item.key) ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-700)] border-l-[3px] border-[var(--color-primary-500)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-alt)] border-l-[3px] border-transparent'"
        >
          <component :is="item.icon" class="w-5 h-5" />
          <span>{{ item.label }}</span>
        </router-link>
      </template>
    </nav>
  </aside>

  <!-- 移动端底部 TabBar -->
  <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-[var(--bg-surface)] border-t border-[var(--border-light)] flex justify-around py-2 z-40">
    <template v-for="item in navItems" :key="item.key">
      <router-link
        v-if="item.show"
        :to="item.to"
        class="flex flex-col items-center gap-0.5 px-2 py-1 text-xs transition-colors"
        :class="isActive(item.key) ? 'text-[var(--color-primary-500)]' : 'text-[var(--text-muted)]'"
      >
        <component :is="item.icon" class="w-5 h-5" />
        <span>{{ item.label }}</span>
      </router-link>
    </template>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  FolderOpen, MessageCircle, ClipboardList, BarChart3, Settings,
} from 'lucide-vue-next'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()

const courseId = computed(() => String(route.params.courseId || ''))
const courseName = computed(() => courseStore.currentCourseName)
const courseDescription = computed(() => courseStore.currentCourse?.description || '')
const courseSemester = computed(() => courseStore.currentCourse?.semester || '')
const canManageCourse = computed(() => courseStore.myRole === 'teacher' || authStore.isAdmin)

const navItems = computed(() => [
  {
    key: 'resources',
    label: canManageCourse.value ? '资源管理' : '课程资源',
    icon: FolderOpen,
    to: `/courses/${courseId.value}/resources`,
    show: true,
  },
  {
    key: 'qa',
    label: '智能问答',
    icon: MessageCircle,
    to: `/courses/${courseId.value}/qa`,
    show: true,
  },
  {
    key: 'tasks',
    label: '教学任务',
    icon: ClipboardList,
    to: `/courses/${courseId.value}/tasks`,
    show: true,
  },
  {
    key: 'reports',
    label: '教学报告',
    icon: BarChart3,
    to: `/courses/${courseId.value}/reports`,
    show: canManageCourse.value,
  },
  {
    key: 'settings',
    label: '课程设置',
    icon: Settings,
    to: `/courses/${courseId.value}/settings`,
    show: canManageCourse.value,
  },
])

function isActive(key: string): boolean {
  return route.path.includes(`/${key}`)
}
</script>
