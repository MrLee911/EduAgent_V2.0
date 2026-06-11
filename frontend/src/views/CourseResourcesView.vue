<script setup lang="ts">
/**
 * CourseResourcesView.vue — 课程资源管理页 (T8.5)
 * 文件上传 + 资源列表 + 状态轮询 + 删除
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'
import { resourceApi } from '@/api/resources'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Resource, ResourceStatus } from '@/types'

const route = useRoute()
const courseStore = useCourseStore()
const authStore = useAuthStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId as string)
const canManageResources = computed(() => courseStore.myRole === 'teacher' || authStore.isAdmin)

// ── State ──
const resources = ref<Resource[]>([])
const isLoading = ref(false)
const loadError = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const keyword = ref('')
const fileTypeFilter = ref('')
const statusFilter = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')

const showDeleteConfirm = ref(false)
const deleteTarget = ref<Resource | null>(null)

// Polling
const pollingTimers = new Map<string, number>()

// ── Methods ──
async function fetchResources() {
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await resourceApi.list({
      course_id: courseId.value,
      file_type: fileTypeFilter.value || undefined,
      status: statusFilter.value || undefined,
      keyword: keyword.value || undefined,
      sort_by: sortBy.value,
      order: sortOrder.value,
    })
    resources.value = res.data || []
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载资源列表失败'
  } finally {
    isLoading.value = false
  }
}

async function handleUpload(e: Event) {
  if (!canManageResources.value) {
    toast.warning('学生只能查看课程资源，不能上传资源')
    return
  }
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  isUploading.value = true
  uploadProgress.value = 0

  try {
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      // Validate file size (50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast.warning(`${file.name} 超过 50MB 限制，已跳过`)
        continue
      }
      // Validate file type
      const ext = file.name.split('.').pop()?.toLowerCase()
      const allowed = ['pdf', 'docx', 'pptx', 'md', 'txt', 'xlsx']
      if (!ext || !allowed.includes(ext)) {
        toast.warning(`${file.name} 不支持的文件类型，已跳过`)
        continue
      }

      try {
        await resourceApi.upload(courseId.value, file)
        toast.success(`${file.name} 上传成功，正在后台处理...`)
      } catch (e: any) {
        toast.error(`${file.name} 上传失败: ${e?.response?.data?.message || '未知错误'}`)
      }

      uploadProgress.value = Math.round(((i + 1) / files.length) * 100)
    }
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
    input.value = '' // Reset input
    await fetchResources()
  }
}

function startPolling(resource: Resource) {
  if (resource.status === 'ready' || resource.status === 'failed') return
  if (pollingTimers.has(resource.id)) return

  const timer = window.setInterval(async () => {
    try {
      const res = await resourceApi.status(courseId.value, resource.id)
      if (res.data) {
        const idx = resources.value.findIndex(r => r.id === resource.id)
        if (idx !== -1) {
          resources.value[idx].status = res.data.status
          resources.value[idx].chunk_count = res.data.progress?.chunk_count_done || 0
        }
        if (res.data.status === 'ready' || res.data.status === 'failed') {
          stopPolling(resource.id)
          await fetchResources()
        }
      }
    } catch {
      stopPolling(resource.id)
    }
  }, 2000)

  pollingTimers.set(resource.id, timer)
}

function stopPolling(resourceId: string) {
  const timer = pollingTimers.get(resourceId)
  if (timer) {
    clearInterval(timer)
    pollingTimers.delete(resourceId)
  }
}

function confirmDelete(resource: Resource) {
  if (!canManageResources.value) {
    toast.warning('学生只能查看课程资源，不能删除资源')
    return
  }
  deleteTarget.value = resource
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  try {
    await resourceApi.delete(courseId.value, deleteTarget.value.id)
    toast.success('资源已删除')
    showDeleteConfirm.value = false
    deleteTarget.value = null
    await fetchResources()
  } catch (e: any) {
    toast.error(`删除失败: ${e?.response?.data?.message || '未知错误'}`)
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// Poll pending resources
watch(resources, (list) => {
  list.forEach(r => {
    if (r.status !== 'ready' && r.status !== 'failed') {
      startPolling(r)
    }
  })
}, { deep: true })

// ── Lifecycle ──
onMounted(async () => {
  if (!courseStore.currentCourse || courseStore.currentCourseId !== courseId.value) {
    await courseStore.fetchCourseDetail(courseId.value)
  }
  await fetchResources()
  // Start initial polling
  resources.value.forEach(r => {
    if (r.status !== 'ready' && r.status !== 'failed') {
      startPolling(r)
    }
  })
})

onUnmounted(() => {
  pollingTimers.forEach(timer => clearInterval(timer))
  pollingTimers.clear()
})
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-800">📁 课程资源</h2>
        <p class="text-sm text-gray-500 mt-0.5">
          {{ canManageResources ? '上传和管理课程资料' : '浏览课程学习资料' }}
        </p>
      </div>
      <label
        v-if="canManageResources"
        class="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-primary-600 transition-colors"
        :class="{ 'opacity-50 pointer-events-none': isUploading }"
      >
        <span v-if="isUploading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        <span>{{ isUploading ? `上传中 ${uploadProgress}%` : '上传资源' }}</span>
        <input type="file" class="hidden" @change="handleUpload" multiple accept=".pdf,.docx,.pptx,.md,.txt,.xlsx" />
      </label>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2">
      <input
        v-model="keyword"
        @input="fetchResources"
        placeholder="搜索资源名称..."
        class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/40 w-48"
      />
      <select v-model="fileTypeFilter" @change="fetchResources" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white">
        <option value="">全部类型</option>
        <option value="pdf">PDF</option>
        <option value="docx">Word</option>
        <option value="pptx">PPT</option>
        <option value="md">Markdown</option>
        <option value="txt">文本</option>
        <option value="xlsx">Excel</option>
      </select>
      <select v-model="statusFilter" @change="fetchResources" class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white">
        <option value="">全部状态</option>
        <option value="ready">就绪</option>
        <option value="uploading">上传中</option>
        <option value="parsing">解析中</option>
        <option value="chunking">分块中</option>
        <option value="embedding">向量化</option>
        <option value="failed">失败</option>
      </select>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载资源列表..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="fetchResources" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">
        重试
      </button>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="resources.length === 0"
      :icon="canManageResources ? '📂' : '📭'"
      :title="canManageResources ? '还没有上传资源' : '暂无资源'"
      :description="canManageResources ? '上传课程资料，AI 将自动处理并为问答提供知识支持' : '老师还没有上传课程资料'"
    />

    <!-- Resource Table -->
    <div v-else class="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-600">文件名</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">类型</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">大小</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">状态</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">分块</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">上传者</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">时间</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="r in resources" :key="r.id" class="hover:bg-gray-50/50 transition-colors">
              <td class="px-4 py-3 font-medium text-gray-800 truncate max-w-[200px]" :title="r.file_name">
                <a
                  v-if="r.file_url"
                  :href="r.file_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-primary-600 hover:text-primary-700 hover:underline"
                >
                  {{ r.file_name }}
                </a>
                <span v-else>{{ r.file_name }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs uppercase">{{ r.file_type }}</span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ formatFileSize(r.file_size) }}</td>
              <td class="px-4 py-3">
                <StatusBadge :type="'resource'" :status="r.status" />
              </td>
              <td class="px-4 py-3 text-gray-500">{{ r.chunk_count || '-' }}</td>
              <td class="px-4 py-3 text-gray-500">{{ r.uploaded_by?.display_name || '-' }}</td>
              <td class="px-4 py-3 text-gray-400 text-xs">{{ formatDate(r.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <a
                  v-if="r.file_url"
                  :href="r.file_url"
                  :download="r.file_name"
                  class="text-primary-600 hover:text-primary-800 text-xs font-medium transition-colors"
                >
                  下载
                </a>
                <button
                  v-if="canManageResources"
                  @click="confirmDelete(r)"
                  class="ml-3 text-red-500 hover:text-red-700 text-xs font-medium transition-colors"
                >
                  删除
                </button>
                <span v-if="!r.file_url && !canManageResources" class="text-xs text-gray-400">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Delete Confirm Dialog -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="确认删除资源"
      :message="`确定要删除「${deleteTarget?.file_name}」吗？此操作不可撤销。`"
      danger
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false; deleteTarget = null"
    />
  </div>
</template>
