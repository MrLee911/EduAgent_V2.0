<script setup lang="ts">
/**
 * CourseReportsView.vue — 学情报告列表页 (T8.9)
 * 报告生成 + 列表
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { useAuthStore } from '@/stores/auth'
import { reportApi } from '@/api/reports'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Report } from '@/types'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const authStore = useAuthStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId as string)

// ── State ──
const reports = ref<Report[]>([])
const isLoading = ref(false)
const loadError = ref('')

// Generate form
const showGenerateForm = ref(false)
const generateType = ref('weekly')
const generateStartDate = ref('')
const generateEndDate = ref('')
const isGenerating = ref(false)

const showDeleteConfirm = ref(false)
const deleteTarget = ref<Report | null>(null)

// ── Methods ──
async function fetchReports() {
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await reportApi.list(courseId.value)
    reports.value = res.data || []
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载报告列表失败'
  } finally {
    isLoading.value = false
  }
}

async function handleGenerate() {
  isGenerating.value = true
  try {
    await reportApi.generate(courseId.value, {
      report_type: generateType.value,
      start_date: generateStartDate.value || undefined,
      end_date: generateEndDate.value || undefined,
    })
    toast.success('报告生成成功！')
    showGenerateForm.value = false
    await fetchReports()
  } catch (e: any) {
    toast.error(`生成失败: ${e?.response?.data?.message || '未知错误'}`)
  } finally {
    isGenerating.value = false
  }
}

async function handleExport(report: Report, format: 'md' | 'pdf') {
  try {
    const res = await reportApi.exportReport(courseId.value, report.id, format)
    const blob = res as any
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.title}.${format}`
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`报告已导出为 ${format.toUpperCase()}`)
  } catch {
    toast.error('导出失败')
  }
}

function confirmDelete(report: Report) {
  deleteTarget.value = report
  showDeleteConfirm.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  // Report deletion is via admin endpoint or course management
  // Using a simple approach - reports don't have a dedicated delete in the spec
  // We'll show a toast for now
  toast.info('报告删除功能将在后续版本中支持')
  showDeleteConfirm.value = false
  deleteTarget.value = null
}

function goToDetail(report: Report) {
  router.push(`/courses/${courseId.value}/reports/${report.id}`)
}

function getTypeLabel(type: string) {
  const map: Record<string, string> = { weekly: '周报', monthly: '月报', semester: '学期报告' }
  return map[type] || type
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  if (!courseStore.currentCourse) {
    await courseStore.fetchCourseDetail(courseId.value)
  }
  await fetchReports()
})
</script>

<template>
  <div class="p-4 space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-gray-800">📊 学情报告</h2>
        <p class="text-sm text-gray-500 mt-0.5">查看课程学情分析报告</p>
      </div>
      <button
        @click="showGenerateForm = !showGenerateForm"
        class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
      >
        {{ showGenerateForm ? '取消' : '生成报告' }}
      </button>
    </div>

    <!-- Generate Form -->
    <div v-if="showGenerateForm" class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <h3 class="font-medium text-gray-700">✨ 生成学情报告</h3>
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-sm text-gray-600 mb-1">报告类型</label>
          <select v-model="generateType" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white">
            <option value="weekly">周报</option>
            <option value="monthly">月报</option>
            <option value="semester">学期报告</option>
          </select>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">开始日期</label>
          <input v-model="generateStartDate" type="date" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg" />
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">结束日期</label>
          <input v-model="generateEndDate" type="date" class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg" />
        </div>
      </div>
      <button
        @click="handleGenerate"
        :disabled="isGenerating"
        class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 disabled:opacity-50 transition-colors"
      >
        <span v-if="isGenerating" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-1 align-middle"></span>
        {{ isGenerating ? '生成中...' : '开始生成' }}
      </button>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" text="加载报告列表..." />

    <!-- Error -->
    <div v-else-if="loadError" class="text-center py-12">
      <p class="text-red-500 text-sm mb-3">{{ loadError }}</p>
      <button @click="fetchReports" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="reports.length === 0"
      icon="📊"
      title="还没有生成报告"
      description="点击上方「生成报告」按钮，AI 将根据课程数据自动生成学情分析报告"
    />

    <!-- Report Cards -->
    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="report in reports"
        :key="report.id"
        class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md hover:border-primary-200 transition-all"
      >
        <h3
          @click="goToDetail(report)"
          class="font-semibold text-gray-800 text-sm mb-2 cursor-pointer hover:text-primary-600 line-clamp-2"
        >
          {{ report.title }}
        </h3>
        <div class="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <span class="px-1.5 py-0.5 bg-gray-100 rounded">{{ getTypeLabel(report.report_type) }}</span>
          <span>{{ report.start_date }} ~ {{ report.end_date }}</span>
        </div>

        <!-- Statistics Summary -->
        <div v-if="report.statistics" class="grid grid-cols-2 gap-1.5 mb-3 text-xs">
          <div class="px-2 py-1 bg-gray-50 rounded">
            <span class="text-gray-400">任务</span> <span class="font-medium text-gray-700">{{ report.statistics.total_tasks }}</span>
          </div>
          <div class="px-2 py-1 bg-gray-50 rounded">
            <span class="text-gray-400">问答</span> <span class="font-medium text-gray-700">{{ report.statistics.total_qa }}</span>
          </div>
          <div class="px-2 py-1 bg-gray-50 rounded">
            <span class="text-gray-400">资源</span> <span class="font-medium text-gray-700">{{ report.statistics.total_resources }}</span>
          </div>
          <div class="px-2 py-1 bg-gray-50 rounded">
            <span class="text-gray-400">活跃</span> <span class="font-medium text-gray-700">{{ report.statistics.active_students }}人</span>
          </div>
        </div>

        <p class="text-xs text-gray-400 mb-3">{{ formatDate(report.created_at) }}</p>

        <div class="flex items-center gap-2 pt-3 border-t border-gray-100">
          <button @click="goToDetail(report)" class="text-xs text-primary-600 hover:text-primary-800 font-medium">查看详情</button>
          <button @click="handleExport(report, 'md')" class="text-xs text-gray-500 hover:text-gray-700 font-medium">导出MD</button>
          <button @click="handleExport(report, 'pdf')" class="text-xs text-gray-500 hover:text-gray-700 font-medium">导出PDF</button>
          <button @click="confirmDelete(report)" class="text-xs text-red-500 hover:text-red-700 font-medium ml-auto">删除</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="确认删除报告"
      :message="`确定要删除「${deleteTarget?.title}」吗？此操作不可撤销。`"
      danger
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false; deleteTarget = null"
    />
  </div>
</template>
