<!-- frontend/src/views/CoursesView.vue — 课程列表页 -->
<template>
  <div class="max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-[var(--text-primary)]">课程列表</h1>
      <div class="flex gap-2">
        <button v-if="canCreateCourse" @click="showCreateModal = true" class="px-4 py-2 text-sm bg-[var(--color-primary-500)] text-white rounded-lg hover:bg-[var(--color-primary-600)] transition-colors btn-hover">创建课程</button>
        <button @click="showJoinModal = true" class="px-4 py-2 text-sm border border-[var(--border-default)] text-[var(--text-secondary)] rounded-lg hover:bg-[var(--bg-surface-alt)] transition-colors">加入课程</button>
      </div>
    </div>

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="h-32 skeleton rounded-lg" />
    </div>

    <EmptyState
      v-else-if="courses.length === 0"
      icon="📚"
      title="还没有课程"
      :description="authStore.isStudent ? '暂无可学习课程' : '创建你的第一门课程或通过课程码加入课程'"
    />

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="course in courses"
        :key="course.id"
        class="bg-[var(--bg-surface)] rounded-lg border border-[var(--border-light)] p-5 hover:shadow-md transition-shadow"
      >
        <component
          :is="canEnterCourse(course) ? 'router-link' : 'div'"
          :to="canEnterCourse(course) ? `/courses/${course.id}/resources` : undefined"
          class="block"
        >
          <div class="flex items-start justify-between mb-3">
            <h3 class="font-semibold text-[var(--text-primary)]">{{ course.name }}</h3>
            <StatusBadge :status="course.status" type="course" :show-dot="false" />
          </div>
          <div class="text-xs text-[var(--text-muted)] space-y-1">
            <p>学期：{{ course.semester || '未设置' }}</p>
            <p>教师：{{ course.teacher?.display_name || course.teacher?.username || '未知' }}</p>
            <p>{{ course.member_count ?? 0 }} 名成员</p>
          </div>
          <p class="text-xs text-[var(--color-primary-500)] mt-2">课程码：{{ course.code }}</p>
        </component>
        <div class="mt-4 pt-3 border-t border-[var(--border-light)] flex justify-end gap-2">
          <router-link
            v-if="canEnterCourse(course)"
            :to="`/courses/${course.id}/resources`"
            class="px-3 py-1.5 text-xs font-medium text-[var(--color-primary-700)] bg-[var(--color-primary-50)] rounded-md hover:bg-[var(--color-primary-100)] transition-colors"
          >
            进入学习
          </router-link>
          <button
            v-else-if="authStore.isStudent"
            @click="handleJoinByCourse(course)"
            :disabled="joiningCourseId === course.id"
            class="px-3 py-1.5 text-xs font-medium text-white bg-[var(--color-primary-500)] rounded-md hover:bg-[var(--color-primary-600)] disabled:opacity-50 transition-colors"
          >
            {{ joiningCourseId === course.id ? '加入中...' : '加入课程' }}
          </button>
          <button
            v-if="authStore.isAdmin"
            @click="confirmDeleteCourse(course)"
            class="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition-colors"
          >
            删除课程
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/加入弹窗 -->
    <div v-if="showCreateModal && canCreateCourse" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showCreateModal = false">
      <div class="bg-[var(--bg-surface)] rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-semibold mb-4">创建课程</h3>
        <div class="space-y-3">
          <input v-model="newCourse.name" placeholder="课程名称 *" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm" />
          <input v-model="newCourse.semester" placeholder="学期（如 2026年春季）" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm" />
          <textarea v-model="newCourse.description" placeholder="课程描述" rows="3" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm" />
        </div>
        <div class="flex justify-end gap-3 mt-4">
          <button @click="showCreateModal = false" class="px-4 py-2 text-sm text-[var(--text-secondary)] bg-[var(--bg-surface-alt)] rounded-lg">取消</button>
          <button @click="handleCreateCourse" class="px-4 py-2 text-sm bg-[var(--color-primary-500)] text-white rounded-lg">创建</button>
        </div>
      </div>
    </div>

    <div v-if="showJoinModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showJoinModal = false">
      <div class="bg-[var(--bg-surface)] rounded-xl shadow-xl w-full max-w-sm p-6">
        <h3 class="text-lg font-semibold mb-4">加入课程</h3>
        <div class="space-y-3">
          <input v-model="joinCode" placeholder="输入6位课程码" maxlength="6" class="w-full px-3 py-2 border border-[var(--border-default)] rounded-lg text-sm text-center uppercase tracking-widest" @input="joinCode = joinCode.toUpperCase()" />
        </div>
        <div class="flex justify-end gap-3 mt-4">
          <button @click="showJoinModal = false" class="px-4 py-2 text-sm text-[var(--text-secondary)] bg-[var(--bg-surface-alt)] rounded-lg">取消</button>
          <button @click="handleJoinCourse" class="px-4 py-2 text-sm bg-[var(--color-primary-500)] text-white rounded-lg">加入</button>
        </div>
      </div>
    </div>

    <ConfirmDialog
      v-if="deleteTarget"
      title="删除课程"
      danger
      confirm-text="删除"
      @confirm="handleDeleteCourse"
      @cancel="deleteTarget = null"
    >
      <template #default>
        <p class="text-sm text-gray-600 mb-3">此操作将永久删除课程及所有关联数据。请确认删除：</p>
        <p class="text-sm font-bold text-red-600">{{ deleteTarget.name }}</p>
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Course } from '@/types'

const router = useRouter()
const courseStore = useCourseStore()
const authStore = useAuthStore()
const toast = useToast()

const loading = ref(true)
const showCreateModal = ref(false)
const showJoinModal = ref(false)
const deleteTarget = ref<Course | null>(null)
const joiningCourseId = ref('')
const joinCode = ref('')
const newCourse = reactive({ name: '', semester: '', description: '' })

const courses = computed(() => courseStore.courses)
const canCreateCourse = computed(() => authStore.isTeacher || authStore.isAdmin)

onMounted(async () => {
  try {
    await courseStore.fetchCourses()
  } finally {
    loading.value = false
  }
})

async function handleCreateCourse() {
  if (!canCreateCourse.value) {
    toast.warning('学生账号不能创建课程')
    showCreateModal.value = false
    return
  }
  if (!newCourse.name.trim()) return
  try {
    const course = await courseStore.createCourse(newCourse)
    showCreateModal.value = false
    newCourse.name = ''
    newCourse.semester = ''
    newCourse.description = ''
    toast.success('课程创建成功')
    router.push(`/courses/${course.id}/resources`)
  } catch {
    toast.error('创建课程失败')
  }
}

async function handleJoinCourse() {
  if (joinCode.value.length !== 6) return
  try {
    await courseStore.joinCourse(joinCode.value)
    showJoinModal.value = false
    joinCode.value = ''
    toast.success('成功加入课程')
    await courseStore.fetchCourses()
  } catch {
    toast.error('加入课程失败')
  }
}

async function handleJoinByCourse(course: Course) {
  joiningCourseId.value = course.id
  try {
    await courseStore.joinCourse(course.code)
    toast.success('成功加入课程')
    await courseStore.fetchCourses()
    router.push(`/courses/${course.id}/resources`)
  } catch (e: any) {
    toast.error(`加入课程失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    joiningCourseId.value = ''
  }
}

function canEnterCourse(course: Course) {
  return authStore.isAdmin || course.my_role === 'teacher' || course.my_role === 'student'
}

function confirmDeleteCourse(course: Course) {
  deleteTarget.value = course
}

async function handleDeleteCourse() {
  if (!deleteTarget.value) return
  try {
    await courseStore.deleteCourse(deleteTarget.value.id, deleteTarget.value.name)
    toast.success('课程已删除')
    deleteTarget.value = null
    await courseStore.fetchCourses()
  } catch (e: any) {
    toast.error(`删除课程失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}
</script>
