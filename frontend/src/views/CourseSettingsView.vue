<script setup lang="ts">
/**
 * CourseSettingsView.vue — 课程设置页 (T8.11)
 * 基本信息 + 成员管理 + 危险操作
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { CourseMember } from '@/types'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId as string)

// ── State ──
const editName = ref('')
const editDescription = ref('')
const editSemester = ref('')
const isSaving = ref(false)

const members = ref<CourseMember[]>([])
const isLoadingMembers = ref(false)
const loadMemberError = ref('')
const newStudentIdentifier = ref('')
const isAddingStudent = ref(false)
const removingMemberId = ref('')

const showDeleteConfirm = ref(false)
const deleteConfirmText = ref('')

const isLoading = ref(false)
const loadError = ref('')

// ── Computed ──
const course = computed(() => courseStore.currentCourse)
const courseCode = computed(() => course.value?.code || '')

// ── Methods ──
async function loadData() {
  isLoading.value = true
  loadError.value = ''
  try {
    await courseStore.fetchCourseDetail(courseId.value)
    if (course.value) {
      editName.value = course.value.name
      editDescription.value = course.value.description
      editSemester.value = course.value.semester
    }
    await fetchMembers()
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载课程信息失败'
  } finally {
    isLoading.value = false
  }
}

async function fetchMembers() {
  isLoadingMembers.value = true
  loadMemberError.value = ''
  try {
    await courseStore.fetchMembers(courseId.value)
    members.value = courseStore.members || []
  } catch (e: any) {
    loadMemberError.value = e?.response?.data?.message || '加载成员列表失败'
  } finally {
    isLoadingMembers.value = false
  }
}

async function handleSaveInfo() {
  isSaving.value = true
  try {
    await courseStore.updateCourse(courseId.value, {
      name: editName.value,
      description: editDescription.value,
      semester: editSemester.value,
    })
    toast.success('课程信息已更新')
  } catch (e: any) {
    toast.error(`保存失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isSaving.value = false
  }
}

function copyCode() {
  navigator.clipboard.writeText(courseCode.value).then(() => {
    toast.success('课程码已复制到剪贴板')
  }).catch(() => {
    toast.error('复制失败')
  })
}

async function handleAddStudent() {
  const identifier = newStudentIdentifier.value.trim()
  if (!identifier) {
    toast.warning('请输入学生用户名或邮箱')
    return
  }

  isAddingStudent.value = true
  try {
    await courseStore.addStudent(courseId.value, identifier)
    newStudentIdentifier.value = ''
    await fetchMembers()
    await courseStore.fetchCourseDetail(courseId.value)
    toast.success('学生已加入课程')
  } catch (e: any) {
    toast.error(`添加失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isAddingStudent.value = false
  }
}

async function handleRemoveMember(member: CourseMember) {
  if (member.role !== 'student') return
  const name = member.user?.display_name || member.user?.username || '该学生'
  if (!window.confirm(`确定要将「${name}」移出本课程吗？`)) return

  removingMemberId.value = member.id
  try {
    await courseStore.removeMember(courseId.value, member.id)
    await fetchMembers()
    await courseStore.fetchCourseDetail(courseId.value)
    toast.success('学生已移出课程')
  } catch (e: any) {
    toast.error(`移出失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    removingMemberId.value = ''
  }
}

async function handleDeleteCourse() {
  if (deleteConfirmText.value !== course.value?.name) {
    toast.warning('请输入正确的课程名称确认删除')
    return
  }
  try {
    await courseStore.deleteCourse(courseId.value, deleteConfirmText.value)
    toast.success('课程已删除')
    router.push('/courses')
  } catch (e: any) {
    toast.error(`删除失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

function getRoleLabel(role: string) {
  const map: Record<string, string> = { teacher: '教师', student: '学生', admin: '管理员' }
  return map[role] || role
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(loadData)
</script>

<template>
  <div class="p-4 space-y-6">
    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载课程设置..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="loadData" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
    </div>

    <template v-else-if="course">
      <!-- Section 1: Basic Info -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <h3 class="font-semibold text-gray-800">📝 基本信息</h3>
        <div>
          <label class="block text-sm text-gray-600 mb-1">课程名称</label>
          <input v-model="editName" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">课程描述</label>
          <textarea v-model="editDescription" rows="3" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40 resize-none"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-600 mb-1">学期</label>
            <input v-model="editSemester" placeholder="例如：2026年春季" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">课程码</label>
            <div class="flex gap-2">
              <input :value="courseCode" readonly class="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-gray-50 font-mono tracking-wider" />
              <button @click="copyCode" class="px-3 py-2 text-sm bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">复制</button>
            </div>
          </div>
        </div>
        <div class="flex justify-end">
          <button
            @click="handleSaveInfo"
            :disabled="isSaving"
            class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            {{ isSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>

      <!-- Section 2: Members -->
      <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h3 class="font-semibold text-gray-800">👥 学生与班级管理</h3>
            <p class="text-xs text-gray-500 mt-1">学生可使用课程码 {{ courseCode }} 自行加入，教师也可以按用户名或邮箱添加学生。</p>
          </div>
          <span class="text-xs text-gray-500">成员 {{ members.length }}</span>
        </div>

        <form class="flex flex-col sm:flex-row gap-2" @submit.prevent="handleAddStudent">
          <input
            v-model="newStudentIdentifier"
            placeholder="输入学生用户名或邮箱"
            class="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40"
          />
          <button
            type="submit"
            :disabled="isAddingStudent"
            class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 transition-colors"
          >
            {{ isAddingStudent ? '添加中...' : '添加学生' }}
          </button>
        </form>

        <LoadingSpinner v-if="isLoadingMembers" text="加载成员..." />
        <p v-else-if="loadMemberError" class="text-sm text-red-500">{{ loadMemberError }}</p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="border-b border-gray-100">
              <tr>
                <th class="text-left py-2 font-medium text-gray-600">姓名</th>
                <th class="text-left py-2 font-medium text-gray-600">账号</th>
                <th class="text-left py-2 font-medium text-gray-600">角色</th>
                <th class="text-left py-2 font-medium text-gray-600">加入时间</th>
                <th class="text-right py-2 font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="m in members" :key="m.id" class="hover:bg-gray-50/50">
                <td class="py-2 text-gray-800">
                  {{ m.user?.display_name || m.user?.username }}
                </td>
                <td class="py-2 text-gray-500">
                  <div>@{{ m.user?.username }}</div>
                  <div v-if="m.user?.email" class="text-xs text-gray-400">{{ m.user.email }}</div>
                </td>
                <td class="py-2">
                  <span :class="[
                    'px-1.5 py-0.5 rounded text-xs',
                    m.role === 'teacher' ? 'bg-blue-50 text-blue-700' : 'bg-gray-100 text-gray-600'
                  ]">
                    {{ getRoleLabel(m.role) }}
                  </span>
                </td>
                <td class="py-2 text-gray-400 text-xs">{{ formatDate(m.joined_at) }}</td>
                <td class="py-2 text-right">
                  <button
                    v-if="m.role === 'student'"
                    @click="handleRemoveMember(m)"
                    :disabled="removingMemberId === m.id"
                    class="text-xs text-red-500 hover:text-red-700"
                  >
                    {{ removingMemberId === m.id ? '移出中...' : '移出' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <EmptyState v-if="members.length === 0" title="暂无成员" description="复制课程码给学生，或使用上方输入框添加学生。" />
        </div>
      </div>

      <!-- Section 3: Danger Zone -->
      <div class="bg-white rounded-lg border border-red-200 p-4 space-y-3">
        <h3 class="font-semibold text-red-600">⚠️ 危险操作</h3>
        <p class="text-sm text-gray-500">删除课程将同时删除所有关联的资源、问答记录、任务和报告，此操作不可撤销。</p>
        <button
          @click="showDeleteConfirm = true"
          class="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-colors"
        >
          删除课程
        </button>
      </div>

      <!-- Delete Confirm Dialog -->
      <ConfirmDialog
        v-if="showDeleteConfirm"
        title="删除课程"
        danger
        @confirm="handleDeleteCourse"
        @cancel="showDeleteConfirm = false; deleteConfirmText = ''"
      >
        <template #default>
          <p class="text-sm text-gray-600 mb-3">此操作将永久删除课程及所有关联数据。请键入课程名称确认：</p>
          <p class="text-sm font-bold text-red-600 mb-2">{{ course.name }}</p>
          <input
            v-model="deleteConfirmText"
            :placeholder="`输入 ${course.name} 确认`"
            class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500/40"
          />
        </template>
      </ConfirmDialog>
    </template>
  </div>
</template>
