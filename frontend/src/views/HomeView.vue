<!-- frontend/src/views/HomeView.vue — 首页仪表盘 -->
<template>
  <div class="max-w-6xl mx-auto">
    <div class="bg-[var(--bg-surface)] rounded-xl border border-[var(--border-light)] p-6 mb-6">
      <h1 class="text-xl font-bold text-[var(--text-primary)]">欢迎回来，{{ userName }}！</h1>
      <p class="text-sm text-[var(--text-secondary)] mt-1">你参与了 {{ courses.length }} 门课程</p>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-4">
        <h2 class="text-lg font-semibold text-[var(--text-primary)]">📚 我的课程</h2>
        <div v-if="loading" class="space-y-3">
          <div v-for="i in 3" :key="i" class="h-24 skeleton rounded-lg" />
        </div>
        <EmptyState
          v-else-if="courses.length === 0"
          icon="📚"
          title="还没有课程"
          description="立即创建或加入一门课程开始使用"
          action-label="浏览课程"
          action-route="/courses"
        />
        <router-link
          v-for="course in courses"
          :key="course.id"
          :to="`/courses/${course.id}/resources`"
          class="block bg-[var(--bg-surface)] rounded-lg border border-[var(--border-light)] p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between">
            <div>
              <h3 class="font-semibold text-[var(--text-primary)]">{{ course.name }}</h3>
              <p class="text-xs text-[var(--text-muted)] mt-1">
                {{ course.stats?.resource_count ?? 0 }} 资源 · {{ course.stats?.qa_count ?? 0 }} 问答 · {{ course.stats?.task_count ?? 0 }} 任务
              </p>
            </div>
            <StatusBadge :status="course.status" type="course" />
          </div>
        </router-link>
      </div>
      <div class="space-y-4">
        <div class="bg-[var(--bg-surface)] rounded-lg border border-[var(--border-light)] p-4">
          <h3 class="font-semibold text-[var(--text-primary)] mb-3">快捷操作</h3>
          <div class="space-y-2">
            <router-link v-if="!authStore.isStudent" to="/courses" class="block w-full px-3 py-2 text-sm text-center bg-[var(--color-primary-50)] text-[var(--color-primary-700)] rounded-lg hover:bg-[var(--color-primary-100)] transition-colors">创建课程</router-link>
            <router-link to="/courses" class="block w-full px-3 py-2 text-sm text-center border border-[var(--border-default)] text-[var(--text-secondary)] rounded-lg hover:bg-[var(--bg-surface-alt)] transition-colors">{{ authStore.isStudent ? '浏览课程' : '加入课程' }}</router-link>
          </div>
        </div>
        <div class="bg-[var(--bg-surface)] rounded-lg border border-[var(--border-light)] p-4">
          <h3 class="font-semibold text-[var(--text-primary)] mb-3">最近活动</h3>
          <p class="text-sm text-[var(--text-muted)]">暂无最近活动</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCourseStore } from '@/stores/course'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const authStore = useAuthStore()
const courseStore = useCourseStore()
const loading = ref(true)

const userName = computed(() => authStore.user?.display_name || authStore.user?.username || '用户')
const courses = computed(() => courseStore.courses)

onMounted(async () => {
  try {
    await courseStore.fetchCourses(authStore.isStudent ? { role_filter: 'joined' } : undefined)
  } finally {
    loading.value = false
  }
})
</script>
