<script setup lang="ts">
/**
 * ReportDetailView.vue — 报告详情页 (T8.10)
 * Markdown 渲染 + 导出按钮 + 统计可视化
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/course'
import { reportApi } from '@/api/reports'
import { useToast } from '@/composables/useToast'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import type { Report } from '@/types'

const route = useRoute()
const router = useRouter()
const courseStore = useCourseStore()
const toast = useToast()

const courseId = computed(() => route.params.courseId as string)
const reportId = computed(() => route.params.reportId as string)

const report = ref<Report | null>(null)
const isLoading = ref(false)
const loadError = ref('')

function getTypeLabel(type: string) {
  const map: Record<string, string> = { weekly: '周报', monthly: '月报', semester: '学期报告' }
  return map[type] || type
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

async function fetchReport() {
  isLoading.value = true
  loadError.value = ''
  try {
    const res = await reportApi.detail(courseId.value, reportId.value)
    report.value = res.data
  } catch (e: any) {
    loadError.value = e?.response?.data?.message || '加载报告详情失败'
  } finally {
    isLoading.value = false
  }
}

async function handleExport(format: 'md' | 'pdf') {
  try {
    const res = await reportApi.exportReport(courseId.value, reportId.value, format)
    const blob = res as any
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.value?.title || 'report'}.${format}`
    a.click()
    URL.revokeObjectURL(url)
    toast.success(`报告已导出为 ${format.toUpperCase()}`)
  } catch {
    toast.error('导出失败')
  }
}

function goBack() {
  router.push(`/courses/${courseId.value}/reports`)
}

onMounted(fetchReport)
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Loading -->
    <LoadingSpinner v-if="isLoading" fullscreen text="加载报告详情..." />

    <!-- Error -->
    <div v-else-if="loadError" class="flex-1 flex flex-col items-center justify-center p-8">
      <p class="text-red-500 mb-3">{{ loadError }}</p>
      <div class="flex gap-2">
        <button @click="fetchReport" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600">重试</button>
        <button @click="goBack" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200">返回列表</button>
      </div>
    </div>

    <template v-else-if="report">
      <!-- Top Bar -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white sticky top-0 z-10">
        <button @click="goBack" class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          ← 返回列表
        </button>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">{{ getTypeLabel(report.report_type) }}</span>
          <button @click="handleExport('md')" class="px-3 py-1.5 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200">导出 MD</button>
          <button @click="handleExport('pdf')" class="px-3 py-1.5 text-xs bg-primary-50 text-primary-700 rounded hover:bg-primary-100">导出 PDF</button>
        </div>
      </div>

      <!-- Report Content -->
      <div class="flex-1 overflow-y-auto">
        <!-- Report Header -->
        <div class="px-4 py-6 border-b border-gray-100 bg-white">
          <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ report.title }}</h1>
          <div class="flex items-center gap-3 text-sm text-gray-500">
            <span>周期：{{ formatDate(report.start_date) }} — {{ formatDate(report.end_date) }}</span>
            <span v-if="report.generated_by">· 生成者：{{ report.generated_by.display_name || report.generated_by.id }}</span>
            <span>· {{ formatDate(report.created_at) }}</span>
          </div>
        </div>

        <!-- Statistics Section -->
        <div v-if="report.statistics" class="px-4 py-4 border-b border-gray-100 bg-gray-50/30">
          <h2 class="text-sm font-semibold text-gray-700 mb-3">📈 数据统计</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
              <div class="text-2xl font-bold text-primary-600">{{ report.statistics.total_tasks }}</div>
              <div class="text-xs text-gray-500 mt-1">总任务数</div>
            </div>
            <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
              <div class="text-2xl font-bold text-green-600">{{ report.statistics.published_tasks }}</div>
              <div class="text-xs text-gray-500 mt-1">已发布</div>
            </div>
            <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
              <div class="text-2xl font-bold text-orange-600">{{ report.statistics.total_qa }}</div>
              <div class="text-xs text-gray-500 mt-1">总问答数</div>
            </div>
            <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
              <div class="text-2xl font-bold text-purple-600">{{ report.statistics.active_students }}</div>
              <div class="text-xs text-gray-500 mt-1">活跃学生</div>
            </div>
          </div>

          <!-- Top Questions -->
          <div v-if="report.statistics.top_questions?.length" class="mt-4 bg-white rounded-lg border border-gray-200 p-3">
            <h3 class="text-xs font-semibold text-gray-600 mb-2">🔥 热门问题</h3>
            <div class="space-y-1">
              <div v-for="(q, i) in report.statistics.top_questions" :key="i" class="flex items-center justify-between text-sm">
                <span class="text-gray-700 truncate flex-1 mr-2">{{ q.question }}</span>
                <span class="text-xs text-gray-400">{{ q.count }}次</span>
              </div>
            </div>
          </div>

          <!-- Suggestions -->
          <div v-if="report.statistics.suggestions?.length" class="mt-3 bg-blue-50 rounded-lg border border-blue-100 p-3">
            <h3 class="text-xs font-semibold text-blue-700 mb-1.5">💡 教学建议</h3>
            <ul class="list-disc list-inside space-y-0.5">
              <li v-for="(s, i) in report.statistics.suggestions" :key="i" class="text-sm text-blue-800">{{ s }}</li>
            </ul>
          </div>
        </div>

        <!-- Markdown Content -->
        <div class="px-4 py-6 prose prose-sm max-w-none">
          <MarkdownRenderer :content="report.content" />
        </div>
      </div>
    </template>
  </div>
</template>
