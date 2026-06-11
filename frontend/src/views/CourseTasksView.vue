<script setup lang="ts">
/**
 * CourseTasksView.vue — 教学任务列表页 (T8.7)
 * 任务生成 + 列表 + 角色视图
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'
import { taskApi } from '@/api/tasks'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Task } from '@/types'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const authStore = useAuthStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId as string)
const canManageTasks = computed(() => courseStore.myRole === 'teacher' || authStore.isAdmin)

// ── State ──
const tasks = ref<Task[]>([])
const isLoading = ref(false)
const loadError = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// Task generation form
const showGenerateForm = ref(false)
const generateTopic = ref('')
const generateType = ref('class_exercise')
const generateDifficulty = ref('medium')
const generateInstructions = ref('')
const isGenerating = ref(false)

// Delete confirm
const showDeleteConfirm = ref(false)
const deleteTarget = ref<Task | null>(null)

// ── Methods ──
async function fetchTasks() {
  isLoading.value = true
  loadError.value = ''
  try {
    const params: Record<string, any> = { course_id: courseId.value }
    if (canManageTasks.value && statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value) params.task_type = typeFilter.value
    const res = await taskApi.list(params as any)
    tasks.value = res.data || []
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载任务列表失败'
  } finally {
    isLoading.value = false
  }
}

async function handleGenerate() {
  if (!generateTopic.value.trim()) {
    toast.warning('请输入任务主题')
    return
  }
  isGenerating.value = true
  try {
    await taskApi.generate(courseId.value, {
      topic: generateTopic.value,
      task_type: generateType.value,
      difficulty: generateDifficulty.value,
      additional_instructions: generateInstructions.value || undefined,
    })
    toast.success('任务生成成功！')
    showGenerateForm.value = false
    generateTopic.value = ''
    generateInstructions.value = ''
    await fetchTasks()
  } catch (e: any) {
    toast.error(`生成失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isGenerating.value = false
  }
}

async function handlePublish(task: Task) {
  try {
    await taskApi.publish(courseId.value, task.id)
    toast.success('任务已发布')
    await fetchTasks()
  } catch (e: any) {
    toast.error(`发布失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

async function handleArchive(task: Task) {
  try {
    await taskApi.archive(courseId.value, task.id)
    toast.success('任务已归档')
    await fetchTasks()
  } catch (e: any) {
    toast.error(`归档失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

async function handleRegenerate(task: Task) {
  try {
    await taskApi.regenerate(courseId.value, task.id)
    toast.success('任务重新生成中...')
    await fetchTasks()
  } catch (e: any) {
    toast.error(`重新生成失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

function confirmDelete(task: Task) {
  deleteTarget.value = task
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  try {
    await taskApi.delete(courseId.value, deleteTarget.value.id)
    toast.success('任务已删除')
    showDeleteConfirm.value = false
    deleteTarget.value = null
    await fetchTasks()
  } catch (e: any) {
    toast.error(`删除失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

function goToDetail(task: Task) {
  router.push(`/courses/${courseId.value}/tasks/${task.id}`)
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
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// ── Lifecycle ──
onMounted(async () => {
  if (!courseStore.currentCourse || courseStore.currentCourseId !== courseId.value) {
    await courseStore.fetchCourseDetail(courseId.value)
  }
  await fetchTasks()
})
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-800">📋 教学任务</h2>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ canManageTasks ? '生成和管理教学任务' : '查看已发布的学习任务' }}
        </p>
      </div>
      <button
        v-if="canManageTasks"
        @click="showGenerateForm = !showGenerateForm"
        class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
      >
        {{ showGenerateForm ? '取消' : '生成新任务' }}
      </button>
    </div>

    <!-- Generate Form -->
    <div v-if="showGenerateForm && canManageTasks" class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <h3 class="font-medium text-gray-700">✨ 生成新任务</h3>
      <div>
        <label class="block text-sm text-gray-600 mb-1">任务主题 <span class="text-red-400">*</span></label>
        <input
          v-model="generateTopic"
          placeholder="例如：Python 函数编程练习"
          class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm text-gray-600 mb-1">任务类型</label>
          <select v-model="generateType" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white">
            <option value="class_exercise">课堂练习</option>
            <option value="homework">课后作业</option>
            <option value="lab_guide">实验指导</option>
          </select>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">难度</label>
          <select v-model="generateDifficulty" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white">
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
          </select>
        </div>
      </div>
      <div>
        <label class="block text-sm text-gray-600 mb-1">额外指令（可选）</label>
        <textarea
          v-model="generateInstructions"
          rows="2"
          placeholder="额外要求，如：重点考察的题型、知识点范围..."
          class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40 resize-none"
        ></textarea>
      </div>
      <button
        @click="handleGenerate"
        :disabled="isGenerating || !generateTopic.trim()"
        class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <span v-if="isGenerating" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-1 align-middle"></span>
        {{ isGenerating ? '生成中...' : '开始生成' }}
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2">
      <select v-if="canManageTasks" v-model="statusFilter" @change="fetchTasks" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white">
        <option value="">全部状态</option>
        <option value="draft">草稿</option>
        <option value="published">已发布</option>
        <option value="archived">已归档</option>
      </select>
      <select v-model="typeFilter" @change="fetchTasks" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white">
        <option value="">全部类型</option>
        <option value="class_exercise">课堂练习</option>
        <option value="homework">课后作业</option>
        <option value="lab_guide">实验指导</option>
      </select>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载任务列表..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="fetchTasks" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="tasks.length === 0"
      icon="📋"
      :title="canManageTasks ? '还没有生成任务' : '暂无学习任务'"
      :description="canManageTasks ? '点击上方「生成新任务」按钮，AI 将根据课程资料自动生成教学任务' : '老师暂未发布学习任务'"
    />

    <!-- Task Cards Grid -->
    <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="task in tasks"
        :key="task.id"
        @click="goToDetail(task)"
        class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md hover:border-primary-200 transition-all cursor-pointer"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="font-semibold text-gray-800 text-sm line-clamp-2 flex-1 mr-2">{{ task.title }}</h3>
          <StatusBadge :type="'task'" :status="task.status" />
        </div>
        <div class="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <span class="px-1.5 py-0.5 bg-gray-100 rounded">{{ getTypeLabel(task.task_type) }}</span>
          <span class="px-1.5 py-0.5 bg-gray-100 rounded">{{ getDifficultyLabel(task.difficulty) }}</span>
          <span v-if="task.estimated_time" class="text-gray-400">⏱ {{ task.estimated_time }}</span>
        </div>
        <p class="text-xs text-gray-400">{{ formatDate(task.created_at) }}</p>

        <!-- Teacher Actions -->
        <div v-if="canManageTasks" class="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100" @click.stop>
          <template v-if="task.status === 'draft'">
            <button @click="handlePublish(task)" class="text-xs text-green-600 hover:text-green-800 font-medium">发布</button>
            <button @click="goToDetail(task)" class="text-xs text-primary-600 hover:text-primary-800 font-medium">编辑</button>
            <button @click="handleRegenerate(task)" class="text-xs text-orange-600 hover:text-orange-800 font-medium">重新生成</button>
            <button @click="confirmDelete(task)" class="text-xs text-red-500 hover:text-red-700 font-medium">删除</button>
          </template>
          <template v-else-if="task.status === 'published'">
            <button @click="handleArchive(task)" class="text-xs text-gray-600 hover:text-gray-800 font-medium">归档</button>
            <button @click="confirmDelete(task)" class="text-xs text-red-500 hover:text-red-700 font-medium">删除</button>
          </template>
          <template v-else-if="task.status === 'archived'">
            <button @click="confirmDelete(task)" class="text-xs text-red-500 hover:text-red-700 font-medium">删除</button>
          </template>
        </div>
      </div>
    </div>

    <!-- Delete Confirm -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="确认删除任务"
      :message="`确定要删除「${deleteTarget?.title}」吗？此操作不可撤销。`"
      danger
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false; deleteTarget = null"
    />
  </div>
</template>
