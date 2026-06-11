<script setup lang="ts">
/**
 * TaskDetailView.vue — 任务详情页 (T8.8)
 * Markdown 渲染 + 教师/学生视图 + 编辑模式
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'
import { taskApi } from '@/api/tasks'
import { useToast } from '@/composables/useToast'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Task } from '@/types'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const authStore = useAuthStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId as string)
const taskId = computed(() => route.params.taskId as string)
const isTeacher = computed(() => courseStore.isTeacherOfCourse || authStore.isAdmin)
const isStudent = computed(() => authStore.isStudent)

// ── State ──
const task = ref<Task | null>(null)
const isLoading = ref(false)
const loadError = ref('')
const isEditing = ref(false)
const editContent = ref('')
const isSaving = ref(false)
const showDeleteConfirm = ref(false)

// Student view: hide answer section
const displayContent = computed(() => {
  if (!task.value?.content) return ''
  if (isStudent.value && task.value.status === 'published') {
    const idx = task.value.content.indexOf('## 参考答案')
    if (idx !== -1) return task.value.content.slice(0, idx)
  }
  return task.value.content
})

// ── Methods ──
async function fetchTask() {
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await taskApi.detail(courseId.value, taskId.value)
    task.value = res.data
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载任务详情失败'
  } finally {
    isLoading.value = false
  }
}

function startEdit() {
  if (task.value) {
    editContent.value = task.value.content
    isEditing.value = true
  }
}

function cancelEdit() {
  isEditing.value = false
  editContent.value = ''
}

async function saveEdit() {
  if (!task.value) return
  isSaving.value = true
  try {
    const res = await taskApi.update(courseId.value, task.value.id, {
      content: editContent.value,
    })
    task.value = res.data || { ...task.value, content: editContent.value }
    isEditing.value = false
    toast.success('任务已更新')
  } catch (e: any) {
    toast.error(`保存失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isSaving.value = false
  }
}

async function handlePublish() {
  if (!task.value) return
  try {
    await taskApi.publish(courseId.value, task.value.id)
    toast.success('任务已发布')
    await fetchTask()
  } catch (e: any) {
    toast.error(`发布失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

async function handleRegenerate() {
  if (!task.value) return
  try {
    await taskApi.regenerate(courseId.value, task.value.id)
    toast.success('任务重新生成中...')
    await fetchTask()
  } catch (e: any) {
    toast.error(`重新生成失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

async function handleDelete() {
  if (!task.value) return
  try {
    await taskApi.delete(courseId.value, task.value.id)
    toast.success('任务已删除')
    router.push(`/courses/${courseId.value}/tasks`)
  } catch (e: any) {
    toast.error(`删除失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

function goBack() {
  router.push(`/courses/${courseId.value}/tasks`)
}

function getTypeLabel(type: string) {
  const map: Record<string, string> = { class_exercise: '课堂练习', homework: '课后作业', lab_guide: '实验指导' }
  return map[type] || type
}

function getDifficultyLabel(difficulty: string) {
  const map: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' }
  return map[difficulty] || difficulty
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(fetchTask)
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" fullscreen text="加载任务详情..." />

    <!-- Error -->
    <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center p-8">
      <p class="text-red-500 mb-3">{{ loadError }}</p>
      <div class="flex gap-2">
        <button @click="fetchTask" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
        <button @click="goBack" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200">返回列表</button>
      </div>
    </div>

    <!-- Content -->
    <template v-else-if="task">
      <!-- Top Bar -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white sticky top-0 z-10">
        <button @click="goBack" class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← 返回列表
        </button>
        <div class="flex items-center gap-2">
          <StatusBadge type="task" :status="task.status" />
          <div class="flex gap-1" v-if="isTeacher">
            <template v-if="task.status === 'draft'">
              <button v-if="!isEditing" @click="startEdit" class="px-3 py-1.5 text-xs bg-primary-50 text-primary-700 rounded hover:bg-primary-100">编辑</button>
              <button v-else @click="cancelEdit" class="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200">取消</button>
              <button @click="handlePublish" class="px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">发布</button>
              <button @click="handleRegenerate" class="px-3 py-1.5 text-xs bg-orange-50 text-orange-700 rounded hover:bg-orange-100">重新生成</button>
            </template>
            <button @click="showDeleteConfirm = true" class="px-3 py-1.5 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100">删除</button>
          </div>
        </div>
      </div>

      <!-- Task Info Header -->
      <div class="px-4 py-4 border-b border-gray-100 bg-white">
        <h1 class="text-xl font-bold text-gray-900 mb-2">{{ task.title }}</h1>
        <div class="flex items-center gap-3 text-sm text-gray-500">
          <span>{{ getTypeLabel(task.task_type) }}</span>
          <span>·</span>
          <span>难度：{{ getDifficultyLabel(task.difficulty) }}</span>
          <span v-if="task.estimated_time">·</span>
          <span v-if="task.estimated_time">⏱ {{ task.estimated_time }}</span>
          <span>·</span>
          <span>{{ formatDate(task.created_at) }}</span>
        </div>
        <div v-if="task.created_by" class="text-xs text-gray-400 mt-1">
          创建者：{{ task.created_by.display_name || task.created_by.id }}
        </div>
      </div>

      <!-- Task Content -->
      <div class="flex-1 overflow-y-auto p-4 bg-white">
        <!-- Edit Mode -->
        <div v-if="isEditing" class="grid grid-cols-2 gap-4 h-full">
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="px-3 py-2 bg-gray-50 border-b text-xs font-medium text-gray-600">编辑</div>
            <textarea
              v-model="editContent"
              class="w-full h-[calc(100%-36px)] p-4 text-sm font-mono resize-none focus:outline-none"
            ></textarea>
          </div>
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="px-3 py-2 bg-gray-50 border-b text-xs font-medium text-gray-600">预览</div>
            <div class="p-4 prose prose-sm max-w-none h-[calc(100%-36px)] overflow-y-auto">
              <MarkdownRenderer :content="editContent" />
            </div>
          </div>
          <div class="col-span-2 flex justify-end">
            <button
              @click="saveEdit"
              :disabled="isSaving"
              class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50"
            >
              {{ isSaving ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>

        <!-- View Mode -->
        <div v-else class="prose prose-sm max-w-none">
          <MarkdownRenderer :content="displayContent" />
        </div>
      </div>

      <!-- Reference Resources -->
      <div
        v-if="task.reference_resources && task.reference_resources.length > 0"
        class="px-4 py-3 border-t border-gray-200 bg-gray-50/50"
      >
        <p class="text-xs font-medium text-gray-600 mb-2">📚 引用资料</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="ref in task.reference_resources"
            :key="ref.resource_id"
            class="px-2 py-1 text-xs bg-white border border-gray-200 rounded text-primary-600 hover:bg-primary-50 cursor-pointer"
          >
            {{ ref.resource_name }}
          </span>
        </div>
      </div>
    </template>

    <!-- Delete Confirm -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="确认删除任务"
      :message="`确定要删除「${task?.title}」吗？此操作不可撤销。`"
      danger
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>
